#!/usr/bin/env python3

from __future__ import annotations

import json
import math
import time
from typing import Any, Dict, List, Optional

import click
import requests
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable, SessionExpired
from sqlalchemy import text

from cardio_graph_core.extraction.clients import ip_dict, ollama_models, port_dict
from cardio_graph_core.snomedct.snomed_query import SnomedExplorer


def _resolve_model_name(model_name: str) -> str:
    return ollama_models.get(model_name, model_name)


def _format_seconds(seconds: float) -> str:
    seconds = int(max(seconds, 0))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _resolve_base_url(
    node: str, port: Optional[int], explicit_url: Optional[str]
) -> str:
    if explicit_url:
        return explicit_url.rstrip("/")
    if not node:
        raise click.ClickException("Either embedding-url or node must be provided")
    actual_port = port if port is not None else port_dict.get(node, 34)
    if actual_port >= 1000:
        return f"http://{ip_dict.get(node, node)}:{actual_port}"
    return f"http://{ip_dict.get(node, node)}:114{actual_port}"


def _embed_batch(
    embedding_url: str,
    embedding_model: str,
    texts: List[str],
    timeout_seconds: int,
) -> List[List[float]]:
    if not texts:
        return []

    base = embedding_url.rstrip("/")
    model = _resolve_model_name(embedding_model)

    try:
        response = requests.post(
            f"{base}/api/embed",
            json={"model": model, "input": texts},
            timeout=timeout_seconds,
        )
        if response.status_code == 200:
            body = response.json()
            embeddings = body.get("embeddings")
            if (
                isinstance(embeddings, list)
                and len(embeddings) == len(texts)
                and all(isinstance(item, list) for item in embeddings)
            ):
                return embeddings
    except Exception:
        pass

    out: List[List[float]] = []
    for item in texts:
        response = requests.post(
            f"{base}/api/embeddings",
            json={"model": model, "prompt": item},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        embedding = body.get("embedding")
        if not isinstance(embedding, list):
            raise RuntimeError("Invalid Ollama embedding payload")
        out.append(embedding)
    return out


def _drop_all_vector_indexes(session) -> None:
    rows = session.run(
        """
        SHOW INDEXES YIELD name, type
        WHERE type = 'VECTOR'
        RETURN name
        """
    )
    names = [row["name"] for row in rows]
    for name in names:
        session.run(f"DROP INDEX `{name}` IF EXISTS")


def _wipe_database_in_batches(
    driver,
    batch_size: int,
    max_attempts: int,
    retry_backoff_seconds: float,
) -> None:
    query = f"""
        MATCH (n)
        CALL {{
            WITH n
            DETACH DELETE n
        }} IN TRANSACTIONS OF {int(batch_size)} ROWS
        """

    def operation() -> None:
        with driver.session() as session:
            session.run(query).consume()

    _run_neo4j_with_retry(
        driver=driver,
        operation=operation,
        operation_name="wipe database in batches",
        max_attempts=max_attempts,
        retry_backoff_seconds=retry_backoff_seconds,
    )


def _create_vector_index(
    session,
    index_name: str,
    label: str,
    property_name: str,
    dimensions: int,
    similarity: str,
) -> None:
    similarity_upper = similarity.strip().upper()
    if similarity_upper not in {"COSINE", "EUCLIDEAN"}:
        raise click.ClickException(
            f"Unsupported similarity '{similarity}'. Use COSINE or EUCLIDEAN."
        )

    cypher = (
        f"CREATE VECTOR INDEX `{index_name}` IF NOT EXISTS "
        f"FOR (n:`{label}`) ON (n.`{property_name}`) "
        f"OPTIONS {{indexConfig: {{`vector.dimensions`: {int(dimensions)}, "
        f"`vector.similarity_function`: '{similarity_upper}'}}}}"
    )
    session.run(cypher)


def _run_neo4j_with_retry(
    driver,
    operation,
    operation_name: str,
    max_attempts: int,
    retry_backoff_seconds: float,
):
    attempt = 0
    while True:
        attempt += 1
        try:
            return operation()
        except (ServiceUnavailable, SessionExpired, OSError) as exc:
            if attempt >= max_attempts:
                raise
            sleep_seconds = retry_backoff_seconds * (2 ** (attempt - 1))
            click.echo(
                f"[vector-ingest] transient Neo4j error during {operation_name} "
                f"(attempt {attempt}/{max_attempts}): {exc}. "
                f"retrying in {sleep_seconds:.1f}s"
            )
            time.sleep(sleep_seconds)
        except Neo4jError:
            raise


def _filter_rows_needing_embedding(
    driver,
    label: str,
    property_name: str,
    rows: List[Dict[str, Any]],
    max_attempts: int,
    retry_backoff_seconds: float,
) -> List[Dict[str, Any]]:
    if not rows:
        return []

    query = f"""
        UNWIND $rows AS row
        OPTIONAL MATCH (n:`{label}` {{concept_id: toInteger(row.conceptid), term: row.term}})
        WITH row, n
        WHERE n IS NULL OR n.`{property_name}` IS NULL
        RETURN row.conceptid AS conceptid, row.term AS term
        """

    def operation():
        with driver.session() as session:
            result = session.run(query, rows=rows)
            return [{"conceptid": r["conceptid"], "term": r["term"]} for r in result]

    return _run_neo4j_with_retry(
        driver=driver,
        operation=operation,
        operation_name="resume filter",
        max_attempts=max_attempts,
        retry_backoff_seconds=retry_backoff_seconds,
    )


def _count_existing_embeddings(
    driver,
    label: str,
    property_name: str,
    max_attempts: int,
    retry_backoff_seconds: float,
) -> int:
    query = f"""
        MATCH (n:`{label}`)
        WHERE n.`{property_name}` IS NOT NULL
        RETURN count(n) AS cnt
        """

    def operation() -> int:
        with driver.session() as session:
            row = session.run(query).single()
            return int(row["cnt"] if row else 0)

    return _run_neo4j_with_retry(
        driver=driver,
        operation=operation,
        operation_name="count existing embeddings",
        max_attempts=max_attempts,
        retry_backoff_seconds=retry_backoff_seconds,
    )


@click.command()
@click.option(
    "--neo4j-uri", default="bolt://neo4j-dev3.internal:7687", show_default=True
)
@click.option("--neo4j-user", default="neo4j", show_default=True)
@click.option(
    "--neo4j-password", envvar="CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD", required=True
)
@click.option("--label", default="SnomedTerm", show_default=True)
@click.option("--property-name", default="embedding", show_default=True)
@click.option("--index-name", default="snomed_term_embeddings_4096", show_default=True)
@click.option("--dimensions", default=4096, type=int, show_default=True)
@click.option("--similarity", default="COSINE", show_default=True)
@click.option("--embedding-url", default=None, show_default=False)
@click.option("--node", default="g4", show_default=True)
@click.option("--port", default=None, type=int, show_default=False)
@click.option("--embedding-model", default="Qwen3embed", show_default=True)
@click.option("--embedding-timeout", default=120, type=int, show_default=True)
@click.option("--fetch-size", default=2000, type=int, show_default=True)
@click.option("--batch-size", default=24, type=int, show_default=True)
@click.option("--language-code", default="en", show_default=True)
@click.option("--max-rows", default=0, type=int, show_default=True)
@click.option(
    "--subset-concept-ids-path",
    default=None,
    show_default=False,
    help="Optional JSON file containing cardiology subset concept IDs under 'concept_ids'.",
)
@click.option("--log-every", default=5000, type=int, show_default=True)
@click.option("--wipe-db/--no-wipe-db", default=False, show_default=True)
@click.option("--resume-only/--no-resume-only", default=True, show_default=True)
@click.option(
    "--drop-existing-vector-indexes/--keep-existing-vector-indexes",
    default=True,
    show_default=True,
)
@click.option("--neo4j-max-attempts", default=5, type=int, show_default=True)
@click.option("--neo4j-retry-backoff", default=2.0, type=float, show_default=True)
@click.option(
    "--index-online-timeout",
    default=7200,
    type=int,
    show_default=True,
    help="Timeout in seconds to wait for vector index to become ONLINE (0 for no timeout)",
)
def main(
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    label: str,
    property_name: str,
    index_name: str,
    dimensions: int,
    similarity: str,
    embedding_url: Optional[str],
    node: str,
    port: Optional[int],
    embedding_model: str,
    embedding_timeout: int,
    fetch_size: int,
    batch_size: int,
    language_code: str,
    max_rows: int,
    subset_concept_ids_path: Optional[str],
    log_every: int,
    wipe_db: bool,
    resume_only: bool,
    drop_existing_vector_indexes: bool,
    neo4j_max_attempts: int,
    neo4j_retry_backoff: float,
    index_online_timeout: int,
) -> None:
    if batch_size <= 0:
        raise click.ClickException("batch_size must be > 0")

    click.echo("[vector-ingest] starting")
    click.echo(f"[vector-ingest] neo4j_uri={neo4j_uri}")
    base_url = _resolve_base_url(node=node, port=port, explicit_url=embedding_url)
    click.echo(f"[vector-ingest] embedding_url={base_url} (node={node}, port={port})")
    click.echo(
        f"[vector-ingest] embedding_model={embedding_model} -> {_resolve_model_name(embedding_model)}"
    )
    click.echo(f"[vector-ingest] index_name={index_name}, dimensions={dimensions}")
    click.echo(
        f"[vector-ingest] resume_only={resume_only}, neo4j_max_attempts={neo4j_max_attempts}, "
        f"neo4j_retry_backoff={neo4j_retry_backoff}"
    )

    snomed = SnomedExplorer()
    snomed.connect()

    language_filter = ""
    params: Dict[str, Any] = {}
    subset_filter = ""
    if language_code:
        language_filter = " AND languagecode = :language_code"
        params["language_code"] = language_code

    if subset_concept_ids_path:
        with open(subset_concept_ids_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        concept_ids = payload.get("concept_ids")
        if not isinstance(concept_ids, list) or not concept_ids:
            raise click.ClickException(
                f"Invalid subset file '{subset_concept_ids_path}': expected non-empty 'concept_ids' list"
            )
        try:
            concept_ids = [int(c) for c in concept_ids]
        except Exception as exc:
            raise click.ClickException(
                f"Invalid concept id value in subset file '{subset_concept_ids_path}': {exc}"
            )
        params["subset_concept_ids"] = concept_ids
        subset_filter = " AND conceptid = ANY(:subset_concept_ids)"
        click.echo(
            f"[vector-ingest] subset filtering enabled: {len(concept_ids)} concept ids from {subset_concept_ids_path}"
        )

    language_filter_aliased = language_filter.replace("languagecode", "d.languagecode")
    subset_filter_aliased = subset_filter.replace("conceptid", "d.conceptid")

    count_query = text(
        f"""
        SELECT COUNT(*) AS cnt
        FROM description d
        JOIN concept c ON d.conceptid = c.id
        WHERE d.active = true
          AND c.active = true
          AND d.term IS NOT NULL
                    {language_filter_aliased}
                    {subset_filter_aliased}
        """
    )

    with snomed.engine.connect() as conn:
        total_rows = int(conn.execute(count_query, params).scalar() or 0)

    if max_rows > 0:
        total_target = min(total_rows, max_rows)
    else:
        total_target = total_rows

    click.echo(f"[vector-ingest] source rows={total_rows}, target rows={total_target}")

    with GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password)) as driver:
        driver.verify_connectivity()

        if wipe_db:
            click.echo(
                "[vector-ingest] wiping Neo4j database (all nodes + rels) in batches"
            )
            _wipe_database_in_batches(
                driver=driver,
                batch_size=1000,
                max_attempts=neo4j_max_attempts,
                retry_backoff_seconds=neo4j_retry_backoff,
            )
            click.echo("[vector-ingest] wipe complete")

        with driver.session() as session:
            if drop_existing_vector_indexes:
                click.echo("[vector-ingest] dropping existing vector indexes")
                _drop_all_vector_indexes(session)

            session.run(
                f"CREATE INDEX `{label.lower()}_concept_term_idx` IF NOT EXISTS "
                f"FOR (n:`{label}`) ON (n.concept_id, n.term)"
            )

        pre_existing_embeddings = 0
        if resume_only and not wipe_db:
            pre_existing_embeddings = _count_existing_embeddings(
                driver=driver,
                label=label,
                property_name=property_name,
                max_attempts=neo4j_max_attempts,
                retry_backoff_seconds=neo4j_retry_backoff,
            )
            if max_rows > 0:
                pre_existing_embeddings = min(pre_existing_embeddings, total_target)
            click.echo(
                f"[vector-ingest] existing embedded rows before run={pre_existing_embeddings}"
            )

        query = text(
            f"""
            SELECT d.conceptid, d.term
            FROM description d
            JOIN concept c ON d.conceptid = c.id
            WHERE d.active = true
              AND c.active = true
              AND d.term IS NOT NULL
              {language_filter_aliased}
              {subset_filter_aliased}
            ORDER BY d.conceptid, d.id
            """
        )

        processed = 0
        start = time.time()
        last_log = start
        rows_buffer: List[Dict[str, Any]] = []

        with snomed.engine.connect().execution_options(stream_results=True) as conn:
            result = conn.execution_options(yield_per=fetch_size).execute(query, params)

            def flush_buffer() -> None:
                nonlocal processed, rows_buffer, last_log
                if not rows_buffer:
                    return

                rows_to_embed = rows_buffer
                if resume_only:
                    rows_to_embed = _filter_rows_needing_embedding(
                        driver=driver,
                        label=label,
                        property_name=property_name,
                        rows=rows_buffer,
                        max_attempts=neo4j_max_attempts,
                        retry_backoff_seconds=neo4j_retry_backoff,
                    )

                if not rows_to_embed:
                    rows_buffer = []
                    return

                texts = [row["term"] for row in rows_to_embed]
                embeddings = _embed_batch(
                    embedding_url=base_url,
                    embedding_model=embedding_model,
                    texts=texts,
                    timeout_seconds=embedding_timeout,
                )

                if len(embeddings) != len(rows_to_embed):
                    raise RuntimeError("Embedding count mismatch")

                bad_dim = next(
                    (len(vec) for vec in embeddings if len(vec) != dimensions), None
                )
                if bad_dim is not None:
                    raise RuntimeError(
                        f"Embedding dimension mismatch: expected {dimensions}, got {bad_dim}"
                    )

                payload = []
                for item, vector in zip(rows_to_embed, embeddings):
                    payload.append(
                        {
                            "concept_id": int(item["conceptid"]),
                            "term": str(item["term"]),
                            "embedding": vector,
                        }
                    )

                def write_operation():
                    with driver.session() as session:
                        session.run(
                            f"""
                            UNWIND $rows AS row
                            MERGE (n:`{label}` {{concept_id: row.concept_id, term: row.term}})
                            SET n.`{property_name}` = row.embedding,
                                n.updated_at = datetime()
                            """,
                            rows=payload,
                        )

                _run_neo4j_with_retry(
                    driver=driver,
                    operation=write_operation,
                    operation_name="batch write",
                    max_attempts=neo4j_max_attempts,
                    retry_backoff_seconds=neo4j_retry_backoff,
                )

                processed += len(payload)
                rows_buffer = []

                if processed % log_every == 0 or (time.time() - last_log) >= 60:
                    elapsed = time.time() - start
                    rate = processed / max(elapsed, 1e-9)
                    effective_done = min(
                        pre_existing_embeddings + processed, total_target
                    )
                    remaining = max(total_target - effective_done, 0)
                    eta = _format_seconds(remaining / rate) if rate > 0 else "--:--:--"
                    click.echo(
                        "[vector-ingest] processed="
                        f"{effective_done}/{total_target} "
                        f"({(effective_done / max(total_target, 1)) * 100:.2f}%), "
                        f"run_delta={processed}, pre_existing={pre_existing_embeddings}, "
                        f"rate={rate:.2f} rows/s, elapsed={_format_seconds(elapsed)}, eta={eta}"
                    )
                    last_log = time.time()

            for row in result.mappings():
                if max_rows > 0 and processed + len(rows_buffer) >= max_rows:
                    break
                rows_buffer.append(
                    {"conceptid": int(row["conceptid"]), "term": row["term"]}
                )
                if len(rows_buffer) >= batch_size:
                    flush_buffer()

            flush_buffer()

        with driver.session() as session:
            click.echo("[vector-ingest] creating vector index")
            _create_vector_index(
                session=session,
                index_name=index_name,
                label=label,
                property_name=property_name,
                dimensions=dimensions,
                similarity=similarity,
            )

            poll_start = time.time()
            while True:
                row = session.run(
                    """
                    SHOW INDEXES YIELD name, type, state
                    WHERE name = $name
                    RETURN state
                    """,
                    name=index_name,
                ).single()
                state = row["state"] if row else "MISSING"
                click.echo(
                    f"[vector-ingest] index_state={state} (elapsed={_format_seconds(time.time() - poll_start)})"
                )
                if state == "ONLINE":
                    break
                elif state == "FAILED":
                    raise RuntimeError(f"Vector index failed to populate: {state}")
                if (
                    index_online_timeout > 0
                    and time.time() - poll_start > index_online_timeout
                ):
                    raise RuntimeError("Timed out waiting for vector index ONLINE")
                time.sleep(10)

            # Final check
            row = session.run(
                """
                SHOW INDEXES YIELD name, type, state
                WHERE name = $name
                RETURN state
                """,
                name=index_name,
            ).single()
            final_state = row["state"] if row else "MISSING"
            if final_state != "ONLINE":
                raise RuntimeError(
                    f"Vector index did not reach ONLINE state: {final_state}"
                )
            click.echo("[vector-ingest] vector index is ONLINE")

    total_elapsed = time.time() - start
    final_effective_done = min(pre_existing_embeddings + processed, total_target)
    click.echo(
        "[vector-ingest] completed "
        f"effective_rows={final_effective_done}/{total_target}, "
        f"run_delta={processed}, elapsed={_format_seconds(total_elapsed)}"
    )


if __name__ == "__main__":
    main()

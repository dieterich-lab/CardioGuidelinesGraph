#!/usr/bin/env python3

import argparse
import json
import re
import socket
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from cardio_graph_core.snomedct.snomed_query import SnomedExplorer


def _extract_rows(payload: dict) -> List[dict]:
    if isinstance(payload, dict) and "tables" in payload:
        rows: List[dict] = []
        for table in payload.get("tables") or []:
            rows.extend(table.get("data") or [])
        return rows
    if isinstance(payload, dict) and "data" in payload:
        return payload.get("data") or []
    return []


def _iter_concept_candidates(concept: dict) -> Iterable[Tuple[str, str]]:
    standardized_list = concept.get("entity_standardized_list") or []
    if standardized_list:
        for entry in standardized_list:
            if not isinstance(entry, dict):
                continue
            standardized = (entry.get("entity_standardized_candidate") or "").strip()
            snomed_id = entry.get("snomed_id")
            if standardized:
                yield standardized, (str(snomed_id) if snomed_id is not None else "")
        return

    standardized = (
        concept.get("entity_standardized_candidate")
        or concept.get("entity_original")
        or ""
    ).strip()
    snomed_id = concept.get("snomed_id")
    if standardized:
        yield standardized, (str(snomed_id) if snomed_id is not None else "")


def _normalize_term(text: str) -> str:
    lowered = (text or "").strip().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", lowered)).strip()


def _parse_abbreviation_file(path: Path) -> Dict[str, List[str]]:
    text = path.read_text(encoding="utf-8")
    raw_entries = [entry.strip() for entry in text.replace("\n", " ").split(";")]
    expanded_to_abbrs: Dict[str, List[str]] = {}
    for entry in raw_entries:
        if not entry or "," not in entry:
            continue
        abbr, expanded = entry.split(",", 1)
        abbr_value = (abbr or "").strip()
        expanded_value = (expanded or "").strip().rstrip(".")
        if not abbr_value or not expanded_value:
            continue
        key = _normalize_term(expanded_value)
        if not key:
            continue
        bucket = expanded_to_abbrs.setdefault(key, [])
        if abbr_value not in bucket:
            bucket.append(abbr_value)
    return expanded_to_abbrs


def _resolve_abbreviation(
    term: str, expanded_to_abbrs: Dict[str, List[str]]
) -> Optional[str]:
    if not term:
        return None
    normalized_term = _normalize_term(term)
    if not normalized_term:
        return None

    exact = expanded_to_abbrs.get(normalized_term)
    if exact:
        return exact[0]

    for expanded, abbreviations in expanded_to_abbrs.items():
        if expanded in normalized_term or normalized_term in expanded:
            return abbreviations[0]
    return None


def _resolve_abbreviations(
    term: str, expanded_to_abbrs: Dict[str, List[str]]
) -> List[str]:
    if not term:
        return []
    normalized_term = _normalize_term(term)
    if not normalized_term:
        return []

    resolved: List[str] = []
    seen = set()

    def _append(values: List[str]) -> None:
        for value in values:
            cleaned = (value or "").strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            resolved.append(cleaned)

    exact = expanded_to_abbrs.get(normalized_term)
    if exact:
        _append(exact)

    for expanded, abbreviations in expanded_to_abbrs.items():
        if expanded in normalized_term or normalized_term in expanded:
            _append(abbreviations)

    return resolved


def _dedupe_synonyms(values: List[str], concept: str, max_items: int = 10) -> List[str]:
    normalized_concept = _normalize_term(concept)
    seen = set()
    cleaned: List[str] = []
    for value in values:
        candidate = (value or "").strip()
        if not candidate:
            continue
        key = _normalize_term(candidate)
        if not key or key == normalized_concept or key in seen:
            continue
        seen.add(key)
        cleaned.append(candidate)
        if len(cleaned) >= max_items:
            break
    return cleaned


def _synonym_cache_key(concept: str, role: str) -> str:
    return f"{_normalize_term(concept)}||{_normalize_term(role)}"


def _normalize_cache_entry(value: Any) -> Dict[str, List[str]]:
    if isinstance(value, list):
        legacy_synonyms = [str(v).strip() for v in value if str(v).strip()]
        merged = _dedupe_synonyms(legacy_synonyms, concept="", max_items=50)
        return {
            "llm_synonyms": [],
            "snomed_synonyms": [],
            "abbreviations": [],
            "synonyms": merged,
        }

    if isinstance(value, dict):
        llm_synonyms = [
            str(v).strip() for v in (value.get("llm_synonyms") or []) if str(v).strip()
        ]
        snomed_synonyms = [
            str(v).strip()
            for v in (value.get("snomed_synonyms") or [])
            if str(v).strip()
        ]
        abbreviations = [
            str(v).strip() for v in (value.get("abbreviations") or []) if str(v).strip()
        ]
        merged_source = (
            value.get("synonyms") or llm_synonyms + snomed_synonyms + abbreviations
        )
        merged = _dedupe_synonyms(
            [str(v).strip() for v in merged_source if str(v).strip()],
            concept="",
            max_items=50,
        )
        return {
            "llm_synonyms": _dedupe_synonyms(llm_synonyms, concept="", max_items=50),
            "snomed_synonyms": _dedupe_synonyms(
                snomed_synonyms, concept="", max_items=50
            ),
            "abbreviations": _dedupe_synonyms(abbreviations, concept="", max_items=20),
            "synonyms": merged,
        }

    return {
        "llm_synonyms": [],
        "snomed_synonyms": [],
        "abbreviations": [],
        "synonyms": [],
    }


def _normalize_synonym_channels(
    llm_synonyms: List[str], snomed_synonyms: List[str]
) -> Tuple[List[str], List[str]]:
    llm_clean = _dedupe_synonyms(llm_synonyms or [], concept="", max_items=50)
    snomed_clean = _dedupe_synonyms(snomed_synonyms or [], concept="", max_items=50)
    return llm_clean, snomed_clean


def _load_synonym_cache(path: Path) -> Dict[str, Dict[str, List[str]]]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"WARNING: failed to read synonym cache at {path}: {exc}")
        return {}
    if not isinstance(payload, dict):
        return {}

    cache: Dict[str, Dict[str, List[str]]] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            continue
        cache[key] = _normalize_cache_entry(value)
    return cache


def _save_synonym_cache(path: Path, cache: Dict[str, Dict[str, List[str]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")


def _ensure_ollama_reachable(
    node: str, port: Optional[int], timeout_s: float = 3.0
) -> None:
    from cardio_graph_core.extraction.clients import resolve_ollama_base_url

    base_url = resolve_ollama_base_url(node=node, port=port)
    host_port = base_url.split("//", 1)[-1].split("/", 1)[0]
    host, raw_port = host_port.rsplit(":", 1)
    target_port = int(raw_port)
    try:
        with socket.create_connection((host, target_port), timeout=timeout_s):
            return
    except Exception as exc:
        raise RuntimeError(
            f"Ollama endpoint unavailable at {base_url} for synonym generation. "
            "Start the server or disable --enable-llm-synonyms. "
            f"Underlying error: {exc}"
        ) from exc


def _build_snomed_synonyms_fetcher(
    enabled: bool,
    uri: Optional[str],
    user: Optional[str],
    password: Optional[str],
):
    if not enabled:
        return None, None

    explorer = SnomedExplorer()
    explorer.connect()
    cache: Dict[str, List[str]] = {}

    def _fetch(snomed_id: str, preferred_term: str) -> List[str]:
        key = str(snomed_id)
        if key in cache:
            return cache[key]

        collected: List[str] = []
        try:
            descriptions = explorer.get_descriptions_for_concept(int(key))
        except Exception:
            descriptions = []

        for row in descriptions:
            if not isinstance(row, dict):
                continue
            term = str(row.get("term") or "").strip()
            if not term:
                continue
            desc_type = str(row.get("type") or "").strip().lower()
            if desc_type == "fsn":
                continue
            collected.append(term)

        cleaned = _dedupe_synonyms(collected, concept=preferred_term, max_items=50)
        cache[key] = cleaned
        return cleaned

    return _fetch, explorer


def _build_synonyms_generator(
    enabled: bool,
    model: str,
    node: str,
    port: Optional[int],
    synonym_stats: Optional[Dict[str, int]] = None,
):
    if not enabled:
        return None

    from cardio_graph_core.extraction.baml_client.sync_client import b
    from cardio_graph_core.extraction.clients import create_client_registry

    _ensure_ollama_reachable(node=node, port=port)

    client_registry = create_client_registry(model, node=node, port=port)
    baml_options = {"client_registry": client_registry}

    def _generate(concept: str, role: str) -> List[str]:
        if synonym_stats is not None:
            synonym_stats["llm_calls"] = synonym_stats.get("llm_calls", 0) + 1
        try:
            result = b.GenerateConceptSynonyms(
                concept=concept,
                role=role,
                baml_options=baml_options,
            )
            synonyms = list(getattr(result, "synonyms", []) or [])
            cleaned = _dedupe_synonyms(synonyms, concept=concept, max_items=10)
            return cleaned
        except Exception as exc:
            raise RuntimeError(
                f"Synonym generation failed for concept '{concept}' (role '{role}'): {exc}"
            ) from exc

    return _generate


def _build_embedding_generator(
    enabled: bool,
    model: str,
    node: str,
    port: Optional[int],
    embedding_stats: Optional[Dict[str, int]] = None,
):
    if not enabled:
        return None

    from cardio_graph_core.extraction.clients import (
        resolve_ollama_base_url,
        resolve_ollama_model_name,
    )
    from cardio_graph_core.query.langchain_replacement import OllamaEmbeddings

    _ensure_ollama_reachable(node=node, port=port)

    model_id = resolve_ollama_model_name(model)
    base_url = resolve_ollama_base_url(node=node, port=port)
    ollama_base_url = base_url[:-3] if base_url.endswith("/v1") else base_url
    embedder = OllamaEmbeddings(model=model_id, base_url=ollama_base_url, timeout=60)
    cache: Dict[str, List[float]] = {}

    def _embed(text: str) -> List[float]:
        normalized = _normalize_term(text)
        if normalized in cache:
            if embedding_stats is not None:
                embedding_stats["cache_hits"] = embedding_stats.get("cache_hits", 0) + 1
            return cache[normalized]

        vector = embedder.embed_query(text)
        cache[normalized] = vector
        if embedding_stats is not None:
            embedding_stats["calls"] = embedding_stats.get("calls", 0) + 1
        return vector

    return _embed


def convert_manual_payloads(
    input_paths: List[Path],
    abbreviation_lookup: Optional[Dict[str, List[str]]] = None,
    synonym_generator=None,
    synonym_cache: Optional[Dict[str, Dict[str, List[str]]]] = None,
    snomed_synonym_fetcher=None,
    synonym_stats: Optional[Dict[str, int]] = None,
    embedding_generator=None,
    row_id_filters: Optional[List[str]] = None,
) -> Tuple[Dict[str, dict], List[dict], List[str]]:
    role_to_label = {
        "ClinicalCondition": "ClinicalCondition",
        "ClinicalParameter": "ClinicalParameter",
        "Medication": "Medication",
        "Procedure": "Procedure",
    }

    by_snomed_id: Dict[str, dict] = {}
    rules_rows: List[dict] = []
    used_sources: List[str] = []
    normalized_row_filters = {
        value.strip() for value in (row_id_filters or []) if value and value.strip()
    }

    for path in input_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = _extract_rows(payload)
        used_sources.append(str(path))
        table_tag = path.stem

        for row_idx, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                continue
            row_id = f"{table_tag}:row_{row_idx:02d}"
            if normalized_row_filters and row_id not in normalized_row_filters:
                continue
            recommendation_text = (
                row.get("recommendation")
                or row.get("Recommendations")
                or row.get("Recommendation")
                or ""
            ).strip()
            section = (row.get("Section Header") or row.get("Sub Header") or "").strip()
            table_header = (row.get("Table Header") or "").strip()
            source_context = (
                recommendation_text
                or section
                or table_header
                or f"{table_tag}:row_{row_idx:02d}"
            )

            for rule_idx, rule in enumerate((row.get("rules") or []), start=1):
                if not isinstance(rule, dict):
                    continue
                chunk_id = f"{table_tag}:row_{row_idx:02d}:rule_{rule_idx:02d}"

                for side, side_name in (
                    ("conditions", "condition"),
                    ("actions", "action"),
                ):
                    for concept in rule.get(side) or []:
                        if not isinstance(concept, dict):
                            continue

                        role = (concept.get("role") or "").strip()
                        if not role:
                            role = (
                                "ClinicalCondition"
                                if side == "conditions"
                                else "Procedure"
                            )
                        target_label = role_to_label.get(role, "Concept")

                        logic_structured = dict(concept.get("logic_structured") or {})
                        concept_context = (
                            concept.get("context")
                            or logic_structured.get("context")
                            or None
                        )
                        if isinstance(concept_context, str):
                            concept_context = concept_context.strip() or None
                        entity_original = (
                            concept.get("entity_original")
                            or concept.get("entity_standardized_candidate")
                            or ""
                        ).strip()

                        for standardized, snomed_id in _iter_concept_candidates(
                            concept
                        ):
                            rules_rows.append(
                                {
                                    "chunk_id": chunk_id,
                                    "source_context": source_context,
                                    "guideline_title": table_header or table_tag,
                                    "entity_original": entity_original or standardized,
                                    "entity_standardized_candidate": standardized,
                                    "role": role,
                                    "logic": side_name,
                                    "logic_structured": logic_structured,
                                    "concept_context": concept_context,
                                    "snomed_id": snomed_id or None,
                                    "target_label": target_label,
                                }
                            )

                            if snomed_id and snomed_id not in by_snomed_id:
                                abbreviations: List[str] = []
                                abbreviation = None
                                if abbreviation_lookup is not None:
                                    abbreviations = _resolve_abbreviations(
                                        standardized, abbreviation_lookup
                                    )
                                    abbreviation = (
                                        abbreviations[0] if abbreviations else None
                                    )

                                cache_entry = {
                                    "llm_synonyms": [],
                                    "snomed_synonyms": [],
                                    "abbreviations": abbreviations,
                                    "synonyms": [],
                                }
                                cache_key = _synonym_cache_key(standardized, role)
                                if (
                                    synonym_cache is not None
                                    and cache_key in synonym_cache
                                ):
                                    cache_entry = _normalize_cache_entry(
                                        synonym_cache.get(cache_key)
                                    )
                                    if synonym_stats is not None:
                                        synonym_stats["cache_hits"] = (
                                            synonym_stats.get("cache_hits", 0) + 1
                                        )

                                snomed_synonyms = (
                                    cache_entry.get("snomed_synonyms") or []
                                )
                                if snomed_synonym_fetcher is not None:
                                    snomed_synonyms = snomed_synonym_fetcher(
                                        snomed_id,
                                        standardized,
                                    )
                                    if synonym_stats is not None:
                                        synonym_stats["snomed_db_lookups"] = (
                                            synonym_stats.get("snomed_db_lookups", 0)
                                            + 1
                                        )

                                llm_synonyms = cache_entry.get("llm_synonyms") or []
                                if synonym_generator is not None and not llm_synonyms:
                                    llm_synonyms = synonym_generator(standardized, role)

                                llm_synonyms, snomed_synonyms = (
                                    _normalize_synonym_channels(
                                        llm_synonyms=llm_synonyms or [],
                                        snomed_synonyms=snomed_synonyms or [],
                                    )
                                )

                                merged_synonyms = _dedupe_synonyms(
                                    (llm_synonyms or [])
                                    + (snomed_synonyms or [])
                                    + (abbreviations or []),
                                    concept=standardized,
                                    max_items=50,
                                )

                                if synonym_cache is not None:
                                    synonym_cache[cache_key] = {
                                        "llm_synonyms": llm_synonyms or [],
                                        "snomed_synonyms": snomed_synonyms or [],
                                        "abbreviations": abbreviations or [],
                                        "synonyms": merged_synonyms,
                                    }

                                embedding_entity_standardized_4096 = None
                                if embedding_generator is not None:
                                    embedding_entity_standardized_4096 = (
                                        embedding_generator(standardized)
                                    )

                                by_snomed_id[snomed_id] = {
                                    "snomed_id": snomed_id,
                                    "preferred_term": standardized,
                                    "entity": standardized,
                                    "entity_original": entity_original or standardized,
                                    "entity_standardized_candidate": standardized,
                                    "target_label": target_label,
                                    "abbr": abbreviation,
                                    "abbreviations": abbreviations,
                                    "llm_synonyms": llm_synonyms or [],
                                    "snomed_synonyms": snomed_synonyms or [],
                                    "taxonomy_path": [],
                                    "embedding_entity_standardized_4096": embedding_entity_standardized_4096,
                                }

    return by_snomed_id, rules_rows, used_sources


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="Manual ground-truth JSON (can be passed multiple times)",
    )
    parser.add_argument(
        "--row-id-filter",
        action="append",
        default=None,
        help=(
            "Optional row id filter in format <table_stem>:row_XX "
            "(can be passed multiple times)."
        ),
    )
    parser.add_argument(
        "--out-index", required=True, help="Output grounding_index.json path"
    )
    parser.add_argument("--out-rules", required=True, help="Output rules.jsonl path")
    parser.add_argument(
        "--abbrv-path",
        default=str(
            Path(__file__).resolve().parents[1]
            / "config"
            / "cardio_graph_core"
            / "abbrv.txt"
        ),
        help="Path to abbreviation file",
    )
    parser.add_argument(
        "--enable-llm-synonyms",
        action="store_true",
        help="Generate synonyms with BAML LLM prompt",
    )
    parser.add_argument(
        "--enable-snomed-db-synonyms",
        action="store_true",
        help="Fetch synonyms from Neo4j concepts by snomed_id",
    )
    parser.add_argument(
        "--snomed-db-uri",
        default=None,
        help="Neo4j URI used to fetch SNOMED synonyms by concept id",
    )
    parser.add_argument(
        "--snomed-db-user",
        default=None,
        help="Neo4j user for SNOMED synonym lookup",
    )
    parser.add_argument(
        "--snomed-db-password",
        default=None,
        help="Neo4j password for SNOMED synonym lookup",
    )
    parser.add_argument(
        "--synonym-model",
        default="Qwen3next",
        help="Model alias used by create_client_registry",
    )
    parser.add_argument(
        "--synonym-node",
        default="g5",
        help="Node alias used by create_client_registry",
    )
    parser.add_argument(
        "--synonym-port",
        type=int,
        default=11436,
        help="Port for synonym generation model endpoint",
    )
    parser.add_argument(
        "--synonym-cache-path",
        default=None,
        help="Optional JSON cache path for concept+role -> synonyms",
    )
    parser.add_argument(
        "--out-concept-dict",
        default=None,
        help="Optional output path for reusable concept dictionary JSON",
    )
    parser.add_argument(
        "--enable-entity-standardized-embeddings",
        action="store_true",
        help="Generate embedding_entity_standardized_4096 using Ollama embeddings.",
    )
    parser.add_argument(
        "--embedding-model",
        default="Qwen3embed",
        help="Embedding model alias passed through resolve_ollama_model_name.",
    )
    parser.add_argument(
        "--embedding-node",
        default="127.0.0.1",
        help="Node/host used for embedding generation endpoint.",
    )
    parser.add_argument(
        "--embedding-port",
        type=int,
        default=11434,
        help="Port used for embedding generation endpoint.",
    )
    args = parser.parse_args()

    input_paths = [Path(p) for p in args.input]
    abbrv_path = Path(args.abbrv_path)
    abbreviation_lookup: Optional[Dict[str, List[str]]] = None
    if abbrv_path.is_file():
        abbreviation_lookup = _parse_abbreviation_file(abbrv_path)
    else:
        print(f"WARNING: abbreviation file not found at {abbrv_path}")

    synonym_cache: Optional[Dict[str, Dict[str, List[str]]]] = None
    synonym_cache_path: Optional[Path] = None
    synonym_stats: Dict[str, int] = {
        "cache_hits": 0,
        "llm_calls": 0,
        "snomed_db_lookups": 0,
    }
    if args.synonym_cache_path:
        synonym_cache_path = Path(args.synonym_cache_path)
        synonym_cache = _load_synonym_cache(synonym_cache_path)

    embedding_stats: Dict[str, int] = {
        "calls": 0,
        "cache_hits": 0,
    }

    snomed_synonym_fetcher = None
    snomed_resource = None
    try:
        snomed_synonym_fetcher, snomed_resource = _build_snomed_synonyms_fetcher(
            enabled=args.enable_snomed_db_synonyms,
            uri=args.snomed_db_uri,
            user=args.snomed_db_user,
            password=args.snomed_db_password,
        )

        synonym_generator = _build_synonyms_generator(
            enabled=args.enable_llm_synonyms,
            model=args.synonym_model,
            node=args.synonym_node,
            port=args.synonym_port,
            synonym_stats=synonym_stats,
        )

        embedding_generator = _build_embedding_generator(
            enabled=args.enable_entity_standardized_embeddings,
            model=args.embedding_model,
            node=args.embedding_node,
            port=args.embedding_port,
            embedding_stats=embedding_stats,
        )

        by_snomed_id, rules_rows, used_sources = convert_manual_payloads(
            input_paths,
            abbreviation_lookup=abbreviation_lookup,
            synonym_generator=synonym_generator,
            synonym_cache=synonym_cache,
            snomed_synonym_fetcher=snomed_synonym_fetcher,
            synonym_stats=synonym_stats,
            embedding_generator=embedding_generator,
            row_id_filters=args.row_id_filter,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 2
    finally:
        if snomed_resource is not None:
            if hasattr(snomed_resource, "disconnect"):
                snomed_resource.disconnect()
            elif hasattr(snomed_resource, "close"):
                snomed_resource.close()

    out_index = Path(args.out_index)
    out_rules = Path(args.out_rules)
    out_index.parent.mkdir(parents=True, exist_ok=True)
    out_rules.parent.mkdir(parents=True, exist_ok=True)

    out_index.write_text(
        json.dumps({"by_snomed_id": by_snomed_id}, indent=2) + "\n",
        encoding="utf-8",
    )

    if synonym_cache_path is not None and synonym_cache is not None:
        _save_synonym_cache(synonym_cache_path, synonym_cache)

    if args.out_concept_dict:
        out_concept_dict = Path(args.out_concept_dict)
        out_concept_dict.parent.mkdir(parents=True, exist_ok=True)
        out_concept_dict.write_text(
            json.dumps(
                {
                    "generated_from": used_sources,
                    "abbreviation_source": str(abbrv_path),
                    "llm_synonym_generation": args.enable_llm_synonyms,
                    "snomed_db_synonym_generation": args.enable_snomed_db_synonyms,
                    "synonym_model": (
                        args.synonym_model if args.enable_llm_synonyms else None
                    ),
                    "synonym_node": (
                        args.synonym_node if args.enable_llm_synonyms else None
                    ),
                    "synonym_port": (
                        args.synonym_port if args.enable_llm_synonyms else None
                    ),
                    "entity_standardized_embeddings_enabled": args.enable_entity_standardized_embeddings,
                    "embedding_model": (
                        args.embedding_model
                        if args.enable_entity_standardized_embeddings
                        else None
                    ),
                    "embedding_node": (
                        args.embedding_node
                        if args.enable_entity_standardized_embeddings
                        else None
                    ),
                    "embedding_port": (
                        args.embedding_port
                        if args.enable_entity_standardized_embeddings
                        else None
                    ),
                    "concepts_by_snomed_id": by_snomed_id,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    with out_rules.open("w", encoding="utf-8") as handle:
        for row in rules_rows:
            handle.write(json.dumps(row) + "\n")

    print("Used sources:")
    for source in used_sources:
        print(f" - {source}")
    print(f"Abbreviation source: {abbrv_path}")
    print(
        f"LLM synonym generation: {'enabled' if args.enable_llm_synonyms else 'disabled'}"
    )
    print(
        f"SNOMED DB synonym generation: {'enabled' if args.enable_snomed_db_synonyms else 'disabled'}"
    )
    print(
        "Entity standardized embeddings: "
        f"{'enabled' if args.enable_entity_standardized_embeddings else 'disabled'}"
    )
    print(f"Synonym cache hits: {synonym_stats.get('cache_hits', 0)}")
    if args.enable_llm_synonyms:
        print(f"Synonym LLM calls: {synonym_stats.get('llm_calls', 0)}")
    if args.enable_snomed_db_synonyms:
        print(f"SNOMED DB lookups: {synonym_stats.get('snomed_db_lookups', 0)}")
    if args.enable_entity_standardized_embeddings:
        print(f"Embedding calls: {embedding_stats.get('calls', 0)}")
        print(f"Embedding cache hits: {embedding_stats.get('cache_hits', 0)}")
    if synonym_cache_path is not None:
        print(f"Synonym cache path: {synonym_cache_path}")
    print(f"Rules rows: {len(rules_rows)}")
    print(f"Unique SNOMED concepts: {len(by_snomed_id)}")
    print(f"Index output: {out_index}")
    print(f"Rules output: {out_rules}")
    if args.out_concept_dict:
        print(f"Concept dictionary output: {args.out_concept_dict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

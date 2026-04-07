#!/usr/bin/env python3
"""Generate a cardiology-focused SNOMED subset with rich metadata for grounding."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import yaml
from sqlalchemy import text

from cardio_graph_core.snomedct.snomed_query import SnomedExplorer

IS_A_TYPE_ID = 116680003


def _default_config_path() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "config"
        / "cardio_graph_core"
        / "ontology_config.yaml"
    )


def _default_gold_paths() -> List[Path]:
    return [
        Path("/prj/doctoral_letters/guide/data/evaluation/table_22_manual_1.3.json"),
        Path("/prj/doctoral_letters/guide/data/evaluation/table_17_manual_1.3.json"),
        Path("/prj/doctoral_letters/guide/data/evaluation/table_8_manual_1.4.json"),
    ]


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _coerce_snomed_id(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        v = value.strip()
        if re.fullmatch(r"\d{5,18}", v):
            return int(v)
    return None


def _walk_extract_snomed_ids(obj: Any, out_ids: Set[int]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if "snomed" in str(key).lower():
                direct = _coerce_snomed_id(value)
                if direct is not None:
                    out_ids.add(direct)
                elif isinstance(value, list):
                    for item in value:
                        cid = _coerce_snomed_id(item)
                        if cid is not None:
                            out_ids.add(cid)
            _walk_extract_snomed_ids(value, out_ids)
    elif isinstance(obj, list):
        for item in obj:
            _walk_extract_snomed_ids(item, out_ids)


def _load_gold_ids(gold_paths: List[Path]) -> Set[int]:
    gold_ids: Set[int] = set()
    for gold_path in gold_paths:
        if not gold_path.is_file():
            continue
        payload = json.loads(gold_path.read_text(encoding="utf-8"))
        _walk_extract_snomed_ids(payload, gold_ids)
    return gold_ids


def _extract_term_seed_ids(
    explorer: SnomedExplorer,
    search_terms: List[str],
    limit_per_term: int,
    global_limit: int,
) -> tuple[Set[int], Dict[int, Set[str]]]:
    query = text(
        """
        SELECT DISTINCT d.conceptid
        FROM description d
        JOIN concept c ON d.conceptid = c.id
        WHERE d.term ILIKE :search_term
          AND d.active = true
          AND c.active = true
        LIMIT :limit_per_term
        """
    )

    concept_ids: Set[int] = set()
    matched_terms: Dict[int, Set[str]] = defaultdict(set)

    for term in search_terms:
        rows = explorer.session.execute(
            query, {"search_term": f"%{term}%", "limit_per_term": limit_per_term}
        )
        for (concept_id,) in rows:
            cid = int(concept_id)
            concept_ids.add(cid)
            matched_terms[cid].add(term)
            if global_limit > 0 and len(concept_ids) >= global_limit:
                return concept_ids, matched_terms

    return concept_ids, matched_terms


def _batch(iterable: Iterable[int], size: int) -> Iterable[List[int]]:
    chunk: List[int] = []
    for value in iterable:
        chunk.append(value)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def _fetch_isa_parents(
    explorer: SnomedExplorer, concept_ids: Set[int]
) -> Dict[int, Set[int]]:
    if not concept_ids:
        return {}
    query = text(
        """
        SELECT sourceid, destinationid
        FROM relationship
        WHERE active = true
          AND typeid = :isa
          AND sourceid = ANY(:source_ids)
        """
    )
    out: Dict[int, Set[int]] = defaultdict(set)
    for ids in _batch(sorted(concept_ids), 2000):
        rows = explorer.session.execute(query, {"isa": IS_A_TYPE_ID, "source_ids": ids})
        for source_id, destination_id in rows:
            out[int(source_id)].add(int(destination_id))
    return out


def _fetch_isa_children(
    explorer: SnomedExplorer, concept_ids: Set[int]
) -> Dict[int, Set[int]]:
    if not concept_ids:
        return {}
    query = text(
        """
        SELECT sourceid, destinationid
        FROM relationship
        WHERE active = true
          AND typeid = :isa
          AND destinationid = ANY(:destination_ids)
        """
    )
    out: Dict[int, Set[int]] = defaultdict(set)
    for ids in _batch(sorted(concept_ids), 2000):
        rows = explorer.session.execute(
            query, {"isa": IS_A_TYPE_ID, "destination_ids": ids}
        )
        for source_id, destination_id in rows:
            out[int(destination_id)].add(int(source_id))
    return out


def _expand_ids(
    explorer: SnomedExplorer,
    seed_ids: Set[int],
    parent_depth: int,
    child_depth: int,
) -> tuple[Set[int], Dict[int, Set[str]], Dict[int, Set[int]], Dict[int, Set[int]]]:
    all_ids: Set[int] = set(seed_ids)
    source_tags: Dict[int, Set[str]] = defaultdict(set)
    for cid in seed_ids:
        source_tags[cid].add("seed")

    isa_parents_index: Dict[int, Set[int]] = defaultdict(set)
    isa_children_index: Dict[int, Set[int]] = defaultdict(set)

    frontier = set(seed_ids)
    for depth in range(1, max(parent_depth, 0) + 1):
        parents_map = _fetch_isa_parents(explorer, frontier)
        next_frontier: Set[int] = set()
        for child, parents in parents_map.items():
            isa_parents_index[child].update(parents)
            for parent in parents:
                if parent not in all_ids:
                    next_frontier.add(parent)
                source_tags[parent].add(f"expand_parent_d{depth}")
        all_ids.update(next_frontier)
        frontier = next_frontier
        if not frontier:
            break

    frontier = set(seed_ids)
    for depth in range(1, max(child_depth, 0) + 1):
        children_map = _fetch_isa_children(explorer, frontier)
        next_frontier = set()
        for parent, children in children_map.items():
            isa_children_index[parent].update(children)
            for child in children:
                if child not in all_ids:
                    next_frontier.add(child)
                source_tags[child].add(f"expand_child_d{depth}")
        all_ids.update(next_frontier)
        frontier = next_frontier
        if not frontier:
            break

    # Enrich direct adjacency for all selected IDs.
    parent_map_all = _fetch_isa_parents(explorer, all_ids)
    child_map_all = _fetch_isa_children(explorer, all_ids)
    for child, parents in parent_map_all.items():
        isa_parents_index[child].update(parents)
    for parent, children in child_map_all.items():
        isa_children_index[parent].update(children)

    return all_ids, source_tags, isa_parents_index, isa_children_index


def _parse_semantic_tag(fsn: str | None) -> str | None:
    if not fsn:
        return None
    match = re.search(r"\(([^)]+)\)\s*$", fsn)
    if not match:
        return None
    return match.group(1).strip().lower()


def _build_metadata(
    explorer: SnomedExplorer,
    concept_ids: Set[int],
    matched_terms: Dict[int, Set[str]],
    source_tags: Dict[int, Set[str]],
    isa_parents_index: Dict[int, Set[int]],
    isa_children_index: Dict[int, Set[int]],
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    for cid in sorted(concept_ids):
        descriptions = explorer.get_descriptions_for_concept(cid)
        preferred = explorer.get_preferred_term(cid) or ""

        fsn = ""
        synonyms: List[str] = []
        all_terms: List[str] = []
        seen = set()

        normalized_preferred = preferred.strip().lower()
        for desc in descriptions:
            term = (desc.get("term") or "").strip()
            if not term:
                continue
            if term.lower() not in seen:
                seen.add(term.lower())
                all_terms.append(term)

            if desc.get("type") == "FSN" and not fsn:
                fsn = term
            if desc.get("type") == "Synonym":
                if term.lower() != normalized_preferred and term.lower() not in {
                    s.lower() for s in synonyms
                }:
                    synonyms.append(term)

        item = {
            "concept_id": cid,
            "snomed_id": cid,
            "preferred_term": preferred,
            "entity_standardized_candidate": preferred,
            "entity": preferred,
            "fsn": fsn,
            "semantic_tag": _parse_semantic_tag(fsn or preferred),
            "snomed_synonyms": synonyms,
            "synonyms": synonyms,
            "llm_synonyms": [],
            "all_descriptions": all_terms,
            "matched_search_terms": sorted(matched_terms.get(cid, set())),
            "source_tags": sorted(source_tags.get(cid, set())),
            "isa_parents": sorted(isa_parents_index.get(cid, set())),
            "isa_children": sorted(isa_children_index.get(cid, set())),
        }
        items.append(item)

    return items


def _gold_coverage(concept_ids: Set[int], gold_ids: Set[int]) -> Dict[str, Any]:
    covered = sorted(concept_ids & gold_ids)
    missing = sorted(gold_ids - concept_ids)
    return {
        "gold_total": len(gold_ids),
        "covered": len(covered),
        "missing": len(missing),
        "coverage": (len(covered) / len(gold_ids)) if gold_ids else 0.0,
        "missing_ids_sample": missing[:100],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate cardiology-focused SNOMED subset with rich metadata"
    )
    parser.add_argument(
        "--config-path",
        default=str(_default_config_path()),
        help="Path to ontology_config.yaml",
    )
    parser.add_argument(
        "--gold-path",
        dest="gold_paths",
        action="append",
        default=[],
        help="Optional gold annotation JSON path. Repeat for multiple files.",
    )
    parser.add_argument(
        "--seed-mode",
        choices=["terms", "gold", "both"],
        default="both",
        help="Seed subset from configured terms, gold annotations, or both.",
    )
    parser.add_argument("--host", default="snomed-ct2.internal")
    parser.add_argument("--port", default="5432")
    parser.add_argument("--user", default="readonly")
    parser.add_argument("--password", default="readonly")
    parser.add_argument("--database", default="snomed")
    parser.add_argument("--sslrootcert", default="/etc/ssl/certs/DieterichLab_CA.pem")
    parser.add_argument("--sslmode", default="verify-full")
    parser.add_argument("--limit-per-term", type=int, default=500)
    parser.add_argument("--global-limit", type=int, default=20000)
    parser.add_argument("--expand-parent-depth", type=int, default=2)
    parser.add_argument("--expand-child-depth", type=int, default=1)
    parser.add_argument(
        "--subset-concept-ids-out",
        default="/prj/doctoral_letters/guide/data/ontologies/cardio_subset_concept_ids.json",
        help="Output JSON containing subset concept_ids",
    )
    parser.add_argument(
        "--subset-candidates-out",
        default="/prj/doctoral_letters/guide/data/ontologies/cardio_subset_candidates.json",
        help="Output JSON containing rich concept metadata including snomed_synonyms",
    )
    args = parser.parse_args()

    config_path = Path(args.config_path)
    cfg = _load_yaml(config_path)
    search_terms: List[str] = cfg.get("cardiovascular_search_terms") or []
    if not search_terms and args.seed_mode in {"terms", "both"}:
        raise RuntimeError(
            f"No cardiovascular_search_terms found in config {config_path}"
        )

    config_gold_paths = [Path(p) for p in (cfg.get("gold_seed_paths") or [])]
    if args.gold_paths:
        gold_paths = [Path(p) for p in args.gold_paths]
    elif config_gold_paths:
        gold_paths = config_gold_paths
    else:
        gold_paths = _default_gold_paths()
    gold_ids = _load_gold_ids(gold_paths)

    explorer = SnomedExplorer(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        sslrootcert=args.sslrootcert,
        sslmode=args.sslmode,
    )
    explorer.connect()

    try:
        term_seed_ids: Set[int] = set()
        matched_terms: Dict[int, Set[str]] = defaultdict(set)
        if args.seed_mode in {"terms", "both"}:
            term_seed_ids, matched_terms = _extract_term_seed_ids(
                explorer=explorer,
                search_terms=search_terms,
                limit_per_term=args.limit_per_term,
                global_limit=args.global_limit,
            )

        seed_ids: Set[int] = set()
        source_tags: Dict[int, Set[str]] = defaultdict(set)

        if args.seed_mode in {"terms", "both"}:
            seed_ids.update(term_seed_ids)
            for cid in term_seed_ids:
                source_tags[cid].add("seed_terms")

        if args.seed_mode in {"gold", "both"}:
            seed_ids.update(gold_ids)
            for cid in gold_ids:
                source_tags[cid].add("seed_gold")

        (
            expanded_ids,
            expanded_tags,
            isa_parents_index,
            isa_children_index,
        ) = _expand_ids(
            explorer=explorer,
            seed_ids=seed_ids,
            parent_depth=args.expand_parent_depth,
            child_depth=args.expand_child_depth,
        )

        for cid, tags in expanded_tags.items():
            source_tags[cid].update(tags)

        metadata_items = _build_metadata(
            explorer=explorer,
            concept_ids=expanded_ids,
            matched_terms=matched_terms,
            source_tags=source_tags,
            isa_parents_index=isa_parents_index,
            isa_children_index=isa_children_index,
        )
    finally:
        explorer.disconnect()

    concept_ids_sorted = sorted(expanded_ids)
    generated_at = datetime.now(timezone.utc).isoformat()
    coverage = _gold_coverage(expanded_ids, gold_ids)

    subset_ids_payload = {
        "generated_at": generated_at,
        "config_path": str(config_path),
        "seed_mode": args.seed_mode,
        "seed_terms_count": len(term_seed_ids),
        "seed_gold_count": len(gold_ids),
        "expand_parent_depth": args.expand_parent_depth,
        "expand_child_depth": args.expand_child_depth,
        "count": len(concept_ids_sorted),
        "concept_ids": concept_ids_sorted,
        "gold_coverage": coverage,
        "gold_paths": [str(p) for p in gold_paths if p.is_file()],
    }

    candidates_payload = {
        "generated_at": generated_at,
        "config_path": str(config_path),
        "seed_mode": args.seed_mode,
        "count": len(metadata_items),
        "items": metadata_items,
        "notes": {
            "grounding_relevant_fields": [
                "concept_id",
                "snomed_id",
                "entity",
                "preferred_term",
                "entity_standardized_candidate",
                "snomed_synonyms",
                "synonyms",
                "llm_synonyms",
                "fsn",
                "semantic_tag",
                "isa_parents",
                "isa_children",
            ]
        },
    }

    out_ids = Path(args.subset_concept_ids_out)
    out_candidates = Path(args.subset_candidates_out)
    out_ids.parent.mkdir(parents=True, exist_ok=True)
    out_candidates.parent.mkdir(parents=True, exist_ok=True)

    out_ids.write_text(
        json.dumps(subset_ids_payload, indent=2) + "\n", encoding="utf-8"
    )
    out_candidates.write_text(
        json.dumps(candidates_payload, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Generated subset concept IDs: {len(concept_ids_sorted)}")
    print(f"Seed term IDs: {len(term_seed_ids)}")
    print(f"Seed gold IDs: {len(gold_ids)}")
    print(
        "Gold coverage: "
        f"{coverage['covered']}/{coverage['gold_total']} "
        f"({coverage['coverage'] * 100:.2f}%)"
    )
    print(f"Subset ID file: {out_ids}")
    print(f"Subset candidate file: {out_candidates}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

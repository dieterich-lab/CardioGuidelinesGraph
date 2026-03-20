#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


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


def _build_synonyms_generator(
    enabled: bool,
    model: str,
    node: str,
    port: Optional[int],
):
    if not enabled:
        return None

    from cardio_graph_core.extraction.baml_client.sync_client import b
    from cardio_graph_core.extraction.clients import create_client_registry

    client_registry = create_client_registry(model, node=node, port=port)
    baml_options = {"client_registry": client_registry}

    def _generate(concept: str, role: str) -> List[str]:
        try:
            result = b.GenerateConceptSynonyms(
                concept=concept,
                role=role,
                baml_options=baml_options,
            )
            synonyms = list(getattr(result, "synonyms", []) or [])
            return _dedupe_synonyms(synonyms, concept=concept, max_items=10)
        except Exception as exc:
            print(f"WARNING: synonym generation failed for '{concept}': {exc}")
            return []

    return _generate


def convert_manual_payloads(
    input_paths: List[Path],
    abbreviation_lookup: Optional[Dict[str, List[str]]] = None,
    synonym_generator=None,
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

    for path in input_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = _extract_rows(payload)
        used_sources.append(str(path))
        table_tag = path.stem

        for row_idx, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
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
                                abbreviation = None
                                if abbreviation_lookup is not None:
                                    abbreviation = _resolve_abbreviation(
                                        standardized, abbreviation_lookup
                                    )
                                synonyms = []
                                if synonym_generator is not None:
                                    synonyms = synonym_generator(standardized, role)
                                by_snomed_id[snomed_id] = {
                                    "snomed_id": snomed_id,
                                    "preferred_term": standardized,
                                    "entity": standardized,
                                    "entity_original": entity_original or standardized,
                                    "entity_standardized_candidate": standardized,
                                    "target_label": target_label,
                                    "abbr": abbreviation,
                                    "synonyms": synonyms,
                                    "taxonomy_path": [],
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
        "--synonym-model",
        default="Qwen32b",
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
    args = parser.parse_args()

    input_paths = [Path(p) for p in args.input]
    abbrv_path = Path(args.abbrv_path)
    abbreviation_lookup: Optional[Dict[str, List[str]]] = None
    if abbrv_path.is_file():
        abbreviation_lookup = _parse_abbreviation_file(abbrv_path)
    else:
        print(f"WARNING: abbreviation file not found at {abbrv_path}")

    synonym_generator = _build_synonyms_generator(
        enabled=args.enable_llm_synonyms,
        model=args.synonym_model,
        node=args.synonym_node,
        port=args.synonym_port,
    )

    by_snomed_id, rules_rows, used_sources = convert_manual_payloads(
        input_paths,
        abbreviation_lookup=abbreviation_lookup,
        synonym_generator=synonym_generator,
    )

    out_index = Path(args.out_index)
    out_rules = Path(args.out_rules)
    out_index.parent.mkdir(parents=True, exist_ok=True)
    out_rules.parent.mkdir(parents=True, exist_ok=True)

    out_index.write_text(
        json.dumps({"by_snomed_id": by_snomed_id}, indent=2) + "\n",
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
    print(f"Rules rows: {len(rules_rows)}")
    print(f"Unique SNOMED concepts: {len(by_snomed_id)}")
    print(f"Index output: {out_index}")
    print(f"Rules output: {out_rules}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

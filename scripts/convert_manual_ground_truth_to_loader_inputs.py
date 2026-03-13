#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


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


def convert_manual_payloads(
    input_paths: List[Path],
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
                                by_snomed_id[snomed_id] = {
                                    "snomed_id": snomed_id,
                                    "preferred_term": standardized,
                                    "entity": standardized,
                                    "entity_original": entity_original or standardized,
                                    "entity_standardized_candidate": standardized,
                                    "target_label": target_label,
                                    "synonyms": [],
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
    args = parser.parse_args()

    input_paths = [Path(p) for p in args.input]
    by_snomed_id, rules_rows, used_sources = convert_manual_payloads(input_paths)

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
    print(f"Rules rows: {len(rules_rows)}")
    print(f"Unique SNOMED concepts: {len(by_snomed_id)}")
    print(f"Index output: {out_index}")
    print(f"Rules output: {out_rules}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

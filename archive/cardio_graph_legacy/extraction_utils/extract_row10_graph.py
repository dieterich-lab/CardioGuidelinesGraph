#!/usr/bin/env python3
import json
import os
import re

from cardio_graph.extraction_utils.guideline_graph_builder import GuidelineGraphBuilder

DOC_TABLE_JSONS = [
    "/prj/doctoral_letters/guide/data/guidelines/docling/pdf_pages/_62/tables/table_000.json",
    "/prj/doctoral_letters/guide/data/guidelines/docling/pdf_pages/_63/tables/table_000.json",
]
TABLE_ID = "_62_63/table_000.json"
ROW_ID = "row_10"
FOOTNOTES = """CABG, coronary artery bypass grafting; CAD, coronary artery disease; CCS, chronic coronary syndrome; FFR, fractional flow reserve; iFR, instantaneous wave-free ratio; IVUS, intravascular
ultrasound; LAD, left anterior descending; LV, left ventricular; LVEF, left ventricular ejection fraction; MVD, multivessel disease; OCT, optical coherence tomography; PCI, percutaneous
coronary intervention; QFR, quantitative flow ratio; STS, Society of Thoracic Surgeons; SYNTAX, SYNergy Between PCI with TAXUS and Cardiac Surgery.
a Class of recommendation.
b Level of evidence.

c Age, frailty, cognitive status, diabetes, and any other comorbidities.
d Multivessel disease with/out left main stem involvement, high anatomical complexity, and likelihood of revascularization completeness.
e Local expertise and outcomes, surgical and interventional risk."""

GUIDELINE_TITLE = "2024 ESC Guidelines for the management of chronic coronary syndromes"
INDEX_PATH = "/prj/doctoral_letters/guide/data/graph/grounding_index_docling_table_000_row10.json"
RULES_OUT_PATH = "/prj/doctoral_letters/guide/data/graph/extracted_rules_docling_table_000_row10.jsonl"
HUMAN_READABLE_PATH = (
    "/prj/doctoral_letters/guide/data/graph/row_10_human_readable.json"
)

MODEL = "Qwen30b"
NODE = "g5"
MIN_MATCH_SCORE = 0.6


def _load_table_jsons():
    table_jsons = []
    for path in DOC_TABLE_JSONS:
        with open(path, "r", encoding="utf-8") as f:
            table_jsons.append(json.load(f))
    return table_jsons


def _parse_row_metadata(row_text: str):
    recommendation_text = None
    class_value = None
    level_value = None
    for line in (row_text or "").splitlines():
        if line.startswith("Recommendation:"):
            recommendation_text = line.split(":", 1)[1].strip()
        elif line.startswith("Class:"):
            class_value = line.split(":", 1)[1].strip()
        elif line.startswith("Level:"):
            level_value = line.split(":", 1)[1].strip()
    if recommendation_text and (class_value is None or level_value is None):
        match = re.search(
            r"\|\s*Class:\s*([IVX]+(?:a|b)?)\s*\|\s*Level:\s*([A-C])",
            recommendation_text,
            flags=re.IGNORECASE,
        )
        if match:
            class_value = class_value or match.group(1)
            level_value = level_value or match.group(2)
            recommendation_text = recommendation_text[: match.start()].strip()
    return recommendation_text, class_value, level_value


def _normalize_class(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if value.lower().startswith("class "):
        value = value[6:].strip()
    return value or None


def _normalize_strength(value: str | None) -> str | None:
    return _normalize_class(value)


def _normalize_entity(value: str | None) -> str | None:
    if not value:
        return None
    return " ".join(value.strip().split()).lower()


def _build_human_readable(row_id, row_text, extracted):
    recommendation_text, class_value, level_value = _parse_row_metadata(row_text)
    class_value = _normalize_class(class_value)

    rules = {}
    for concept in extracted:
        rule_id = concept.rule_id or 1
        rules.setdefault(rule_id, {"conditions": [], "actions": []})
        logic_structured = dict(concept.logic_structured or {})
        role = (concept.role or "").strip()
        if role in {"Condition", "ClinicalParameter"}:
            if not logic_structured.get("operator"):
                logic_structured["operator"] = "PRESENT"
            if not logic_structured.get("logic_type"):
                logic_structured["logic_type"] = "AND"
            if not logic_structured.get("logic_group"):
                logic_structured["logic_group"] = f"and_{rule_id}"

        if role in {"Condition", "ClinicalParameter"}:
            rules[rule_id]["conditions"].append(
                {
                    "entity_original": concept.entity_original,
                    "entity_standardized_candidate": _normalize_entity(
                        concept.entity_standardized_candidate
                    ),
                    "role": role,
                    "logic_structured": {
                        "operator": logic_structured.get("operator"),
                        "threshold": logic_structured.get("threshold"),
                        "unit": logic_structured.get("unit"),
                        "condition_context": logic_structured.get("condition_context"),
                        "logic_type": logic_structured.get("logic_type"),
                        "logic_group": logic_structured.get("logic_group"),
                    },
                }
            )
        elif role in {"Procedure", "Medication"}:
            strength = _normalize_strength(logic_structured.get("strength"))
            level = logic_structured.get("level") or level_value
            if not strength:
                strength = class_value
            rules[rule_id]["actions"].append(
                {
                    "entity_original": concept.entity_original,
                    "entity_standardized_candidate": _normalize_entity(
                        concept.entity_standardized_candidate
                    ),
                    "role": role,
                    "logic_structured": {
                        "strength": strength,
                        "level": level,
                        "direction": logic_structured.get("direction"),
                    },
                }
            )

    return {
        "row_id": row_id,
        "class": class_value,
        "level": level_value,
        "recommendation_text": recommendation_text,
        "rules": [
            {"rule_id": rule_id, **payload}
            for rule_id, payload in sorted(rules.items())
        ],
    }


def main() -> None:
    os.makedirs(os.path.dirname(RULES_OUT_PATH), exist_ok=True)
    builder = GuidelineGraphBuilder(
        model=MODEL,
        node=NODE,
        index_path=INDEX_PATH,
        min_match_score=MIN_MATCH_SCORE,
    )
    rows = builder._format_docling_table_rows(_load_table_jsons(), footnotes=FOOTNOTES)
    row_text = None
    for row_id, text in rows:
        if row_id == ROW_ID:
            row_text = text
            break
    if not row_text:
        raise RuntimeError(f"Row {ROW_ID} not found in docling table inputs")

    tagged_text = f"DOC_TABLE: {TABLE_ID}\nDOC_ROW: {ROW_ID}\n{row_text}"
    extracted, _ = builder.extract_and_ground(
        tagged_text, source_type="table", guideline_title=GUIDELINE_TITLE
    )

    chunk_label = f"{TABLE_ID}:{ROW_ID}"
    with open(RULES_OUT_PATH, "w", encoding="utf-8") as rules_file:
        builder._write_rules_entries_from_extracted(
            rules_file,
            extracted,
            chunk_id=chunk_label,
            source_context=";".join(DOC_TABLE_JSONS),
            source_type="table",
            guideline_title=GUIDELINE_TITLE,
        )

    human_readable = _build_human_readable(ROW_ID, row_text, extracted)
    with open(HUMAN_READABLE_PATH, "w", encoding="utf-8") as f:
        json.dump(human_readable, f, indent=2, ensure_ascii=False)

    print(f"Wrote row_10 rules to {RULES_OUT_PATH}")
    print(f"Wrote row_10 index to {INDEX_PATH}")
    print(f"Wrote row_10 human readable to {HUMAN_READABLE_PATH}")


if __name__ == "__main__":
    main()

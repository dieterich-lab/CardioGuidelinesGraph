import json
import os
import unittest

from cardio_graph.extraction_utils.guideline_graph_builder import GuidelineGraphBuilder

DOC_TABLE_JSONS = [
    "/prj/doctoral_letters/guide/data/guidelines/docling/pdf_pages/_62/tables/table_000.json",
    "/prj/doctoral_letters/guide/data/guidelines/docling/pdf_pages/_63/tables/table_000.json",
]
FOOTNOTES = """CABG, coronary artery bypass grafting; CAD, coronary artery disease; CCS, chronic coronary syndrome; FFR, fractional flow reserve; iFR, instantaneous wave-free ratio; IVUS, intravascular
ultrasound; LAD, left anterior descending; LV, left ventricular; LVEF, left ventricular ejection fraction; MVD, multivessel disease; OCT, optical coherence tomography; PCI, percutaneous
coronary intervention; QFR, quantitative flow ratio; STS, Society of Thoracic Surgeons; SYNTAX, SYNergy Between PCI with TAXUS and Cardiac Surgery.
a Class of recommendation.
b Level of evidence.

c Age, frailty, cognitive status, diabetes, and any other comorbidities.
d Multivessel disease with/out left main stem involvement, high anatomical complexity, and likelihood of revascularization completeness.
e Local expertise and outcomes, surgical and interventional risk."""

RULES_PATH = "/prj/doctoral_letters/guide/data/extracted_rules_docling_table_000.jsonl"
EXPECTED_DIR = "/home/pwiesenbach/CardioGuidelinesGraph/tests/expected_rows"


def _load_table_jsons():
    table_jsons = []
    for path in DOC_TABLE_JSONS:
        with open(path, "r", encoding="utf-8") as f:
            table_jsons.append(json.load(f))
    return table_jsons


def _parse_row_metadata(row_text):
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
    return recommendation_text, class_value, level_value


def _load_rules():
    rows = []
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _build_structure(rows_for_row, recommendation_text, class_value, level_value):
    rules = {}
    for concept in rows_for_row:
        rule_id = concept.get("rule_id") or 1
        rules.setdefault(rule_id, {"conditions": [], "actions": []})
        logic = concept.get("logic_structured") or {}
        entry = {
            "entity_original": concept.get("entity_original"),
            "entity_standardized_candidate": concept.get(
                "entity_standardized_candidate"
            ),
            "role": concept.get("role"),
            "logic_structured": {
                "operator": logic.get("operator"),
                "threshold": logic.get("threshold"),
                "unit": logic.get("unit"),
                "condition_context": logic.get("condition_context"),
                "logic_type": logic.get("logic_type"),
                "logic_group": logic.get("logic_group"),
                "strength": logic.get("strength"),
                "level": logic.get("level"),
                "direction": logic.get("direction"),
            },
        }
        role = concept.get("role")
        if role in {"Condition", "ClinicalParameter"}:
            rules[rule_id]["conditions"].append(entry)
        elif role in {"Procedure", "Medication"}:
            rules[rule_id]["actions"].append(entry)

    for payload in rules.values():
        payload["conditions"].sort(
            key=lambda x: (x.get("entity_standardized_candidate") or "")
        )
        payload["actions"].sort(
            key=lambda x: (x.get("entity_standardized_candidate") or "")
        )

    structure = {
        "row_id": None,
        "class": class_value,
        "level": level_value,
        "recommendation_text": recommendation_text,
        "rules": [],
    }
    for rule_id in sorted(rules.keys()):
        structure["rules"].append({"rule_id": rule_id, **rules[rule_id]})
    return structure


def _load_expected(row_id):
    path = os.path.join(EXPECTED_DIR, f"{row_id}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class AllRowsStructureExtractionTests(unittest.TestCase):
    def _assert_verbose(self, row_id, expected, actual):
        print(f"\nROW {row_id} EXPECTED:\n" + json.dumps(expected, indent=2))
        print(f"\nROW {row_id} ACTUAL:\n" + json.dumps(actual, indent=2))
        self.assertEqual(actual, expected)

    def test_all_rows_match_expected(self):
        builder = GuidelineGraphBuilder(model="Qwen30b", node="g5")
        rows = builder._format_docling_table_rows(
            _load_table_jsons(), footnotes=FOOTNOTES
        )
        rules = _load_rules()
        rules_by_row = {}
        for concept in rules:
            chunk_id = concept.get("chunk_id") or ""
            if "row_" not in chunk_id:
                continue
            row_id = chunk_id.split(":")[-1]
            rules_by_row.setdefault(row_id, []).append(concept)

        for row_id, row_text in rows:
            recommendation_text, class_value, level_value = _parse_row_metadata(
                row_text
            )
            row_rules = rules_by_row.get(row_id, [])
            actual = _build_structure(
                row_rules, recommendation_text, class_value, level_value
            )
            actual["row_id"] = row_id
            expected = _load_expected(row_id)
            self._assert_verbose(row_id, expected, actual)


if __name__ == "__main__":
    unittest.main()

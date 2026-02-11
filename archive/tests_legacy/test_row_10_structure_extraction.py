import json
import unittest

from cardio_graph.extraction_utils.guideline_graph_builder import GuidelineGraphBuilder

DOC_TABLE_JSONS = [
    "/prj/doctoral_letters/guide/data/guidelines/docling/pdf_pages/_62/tables/table_000.json",
    "/prj/doctoral_letters/guide/data/guidelines/docling/pdf_pages/_63/tables/table_000.json",
]

EXPECTED_JSON_PATH = (
    "/home/pwiesenbach/CardioGuidelinesGraph/tests/expected_row_10_structure.json"
)

FOOTNOTES = """CABG, coronary artery bypass grafting; CAD, coronary artery disease; CCS, chronic coronary syndrome; FFR, fractional flow reserve; iFR, instantaneous wave-free ratio; IVUS, intravascular
ultrasound; LAD, left anterior descending; LV, left ventricular; LVEF, left ventricular ejection fraction; MVD, multivessel disease; OCT, optical coherence tomography; PCI, percutaneous
coronary intervention; QFR, quantitative flow ratio; STS, Society of Thoracic Surgeons; SYNTAX, SYNergy Between PCI with TAXUS and Cardiac Surgery.
a Class of recommendation.
b Level of evidence.

c Age, frailty, cognitive status, diabetes, and any other comorbidities.
d Multivessel disease with/out left main stem involvement, high anatomical complexity, and likelihood of revascularization completeness.
e Local expertise and outcomes, surgical and interventional risk."""


def _load_table_jsons():
    table_jsons = []
    for path in DOC_TABLE_JSONS:
        with open(path, "r", encoding="utf-8") as f:
            table_jsons.append(json.load(f))
    return table_jsons


def _load_expected_summary():
    with open(EXPECTED_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class Row10StructureExtractionTests(unittest.TestCase):
    def setUp(self):
        self.builder = GuidelineGraphBuilder(model="Qwen30b", node="g5")

    def _assert_verbose(self, query, expected, actual, health_note):
        print("\nQUERY:\n" + query)
        print("EXPECTED:\n" + str(expected))
        print("ACTUAL:\n" + str(actual))
        print("HEALTH NOTE:\n" + health_note)
        self.assertEqual(actual, expected)

    def _get_row_10_text(self):
        rows = self.builder._format_docling_table_rows(
            _load_table_jsons(), footnotes=FOOTNOTES
        )
        for row_id, row_text in rows:
            if row_id == "row_10":
                return row_text
        return None

    def _extract_row_10_concepts(self, row_text):
        extracted_main = self.builder.extract_concepts(
            row_text,
            source_type="table",
            guideline_title="2024 ESC Guidelines for the management of chronic coronary syndromes",
            focus="MAIN",
        )
        extracted_population = self.builder.extract_concepts(
            row_text,
            source_type="table",
            guideline_title="2024 ESC Guidelines for the management of chronic coronary syndromes",
            focus="POPULATION",
        )
        if extracted_main and extracted_population:
            primary_rule_id = extracted_main[0].rule_id
            for concept in extracted_population:
                if concept.rule_id is None:
                    concept.rule_id = primary_rule_id
        merged = self.builder._merge_extracted_concepts(
            extracted_main, extracted_population
        )
        return self.builder._explode_or_conditions(merged)

    def _normalize_strength(self, strength):
        if not strength:
            return None
        normalized = str(strength).strip()
        if normalized.lower().startswith("class "):
            return normalized.split(" ", 1)[1].strip()
        return normalized

    def _build_actual_summary(self, row_text, concepts):
        recommendation_text = None
        for line in (row_text or "").splitlines():
            if line.startswith("Recommendation:"):
                recommendation_text = line.split(":", 1)[1].strip()
                break
        summary = {
            "row_id": "row_10",
            "class": None,
            "level": None,
            "recommendation_text": recommendation_text,
            "rules": [],
        }
        rules = {}
        for concept in concepts:
            rule_id = concept.rule_id or 1
            rules.setdefault(rule_id, {"conditions": [], "actions": []})
            logic = concept.logic_structured or {}
            entry = {
                "entity_original": concept.entity_original,
                "entity_standardized_candidate": concept.entity_standardized_candidate,
                "role": concept.role,
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
            if concept.role in {"Condition", "ClinicalParameter"}:
                rules[rule_id]["conditions"].append(entry)
            elif concept.role in {"Procedure", "Medication"}:
                rules[rule_id]["actions"].append(entry)
                if summary["class"] is None and logic.get("strength"):
                    summary["class"] = self._normalize_strength(logic.get("strength"))
                if summary["level"] is None and logic.get("level"):
                    summary["level"] = logic.get("level")
        for rule_id, payload in rules.items():
            summary["rules"].append({"rule_id": rule_id, **payload})
        return summary

    def test_row_10_text_present(self):
        row_text = self._get_row_10_text()
        self._assert_verbose(
            "_format_docling_table_rows(...): row_10",
            True,
            row_text is not None,
            "Row_10 text must be available for deterministic extraction.",
        )

    def test_row_10_structure_extraction(self):
        row_text = self._get_row_10_text()
        self.assertIsNotNone(row_text, "Row_10 text missing")
        concepts = self._extract_row_10_concepts(row_text)
        expected_summary = _load_expected_summary()
        actual_summary = self._build_actual_summary(row_text, concepts)
        print(
            "\nEXPECTED SUMMARY (structure reference):\n"
            + json.dumps(expected_summary, indent=2)
        )
        print("\nACTUAL SUMMARY (extracted):\n" + json.dumps(actual_summary, indent=2))
        print("\nNOTE: Grounding is not validated in this test suite.")

        roles = [c.role for c in concepts]
        standardized = [c.entity_standardized_candidate.lower() for c in concepts]
        rule_ids = {c.rule_id for c in concepts}

        self._assert_verbose(
            "Extract roles",
            True,
            all(r is not None for r in roles),
            "All concepts should have roles for rule construction.",
        )

        self._assert_verbose(
            "Rule IDs",
            1,
            len(rule_ids),
            "All row_10 concepts should share a single rule_id.",
        )

        self._assert_verbose(
            "Population condition present",
            True,
            any("chronic coronary syndrome" in s or s == "ccs" for s in standardized),
            "Row_10 population (CCS) must be captured as a condition.",
        )

        lvef = [
            c
            for c in concepts
            if "left ventricular ejection fraction"
            in c.entity_standardized_candidate.lower()
        ]
        self._assert_verbose(
            "LVEF present",
            True,
            len(lvef) >= 1,
            "Row_10 must include the LVEF clinical parameter.",
        )
        if lvef:
            lvef_logic = lvef[0].logic_structured or {}
            self._assert_verbose(
                "LVEF operator",
                ">",
                lvef_logic.get("operator"),
                "LVEF should carry a numeric operator.",
            )
            self._assert_verbose(
                "LVEF threshold",
                "35",
                lvef_logic.get("threshold"),
                "LVEF should capture the threshold value.",
            )
            self._assert_verbose(
                "LVEF unit",
                "%",
                lvef_logic.get("unit"),
                "LVEF should capture the unit.",
            )

        three_vessel = [
            c
            for c in concepts
            if "three-vessel" in c.entity_standardized_candidate.lower()
            or "three vessel" in c.entity_standardized_candidate.lower()
        ]
        self._assert_verbose(
            "Three-vessel disease present",
            True,
            len(three_vessel) >= 1,
            "Row_10 must include functionally significant three-vessel disease.",
        )

        action = [
            c
            for c in concepts
            if c.role == "Procedure"
            and "myocardial revascularization"
            in c.entity_standardized_candidate.lower()
        ]
        self._assert_verbose(
            "Action present",
            True,
            len(action) >= 1,
            "Row_10 must include myocardial revascularization as the action.",
        )

        if action:
            action_logic = action[0].logic_structured or {}
            self._assert_verbose(
                "Action strength",
                "I",
                self._normalize_strength(action_logic.get("strength")),
                "Row_10 action should include Class I strength.",
            )
            self._assert_verbose(
                "Action level",
                "A",
                action_logic.get("level"),
                "Row_10 action should include Level A evidence.",
            )


if __name__ == "__main__":
    unittest.main()

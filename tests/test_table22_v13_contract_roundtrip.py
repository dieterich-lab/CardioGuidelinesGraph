import json
import unittest
from pathlib import Path

import yaml

from cardio_graph_core.extraction.schema_contract_sync import (
    contract_vocabulary_from_schema,
    resolve_table22_v13_path,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    PROJECT_ROOT / "config" / "cardio_graph_core" / "guideline_graph_schema.yaml"
)


class TestTable22V13ContractRoundtrip(unittest.TestCase):
    def setUp(self):
        self.schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8")) or {}
        self.vocab = contract_vocabulary_from_schema(self.schema)

    def _load_golden_payload(self):
        data_path = resolve_table22_v13_path(PROJECT_ROOT)
        if data_path is None:
            raise unittest.SkipTest(
                "table_22_manual_1.3.json not found in expected locations"
            )
        return json.loads(data_path.read_text(encoding="utf-8"))

    def _first_row_with_rules(self, payload):
        for table in payload.get("tables", []) or []:
            for row in table.get("data", []) or []:
                if row.get("rules"):
                    return row
        return None

    def test_schema_uses_column_placeholder(self):
        output_schema = (
            self.schema.get("rule_output_format", {}).get("schema", {}) or {}
        )
        self.assertIn("Column_N", output_schema)
        self.assertNotIn("Column_1", output_schema)
        self.assertNotIn("Column_2", output_schema)
        self.assertNotIn("Column_n", output_schema)

    def test_golden_row_matches_rule_contract(self):
        payload = self._load_golden_payload()
        row = self._first_row_with_rules(payload)
        self.assertIsNotNone(
            row, "Expected at least one row with rules in golden payload"
        )

        self.assertIn("input", row)
        self.assertIn("recommendation", row)
        self.assertIsInstance(row.get("rules"), list)
        self.assertGreater(len(row["rules"]), 0)

        operator_allowed = set(self.vocab["operator"])
        logic_type_allowed = {v.upper() for v in self.vocab["logic_type"]}
        direction_allowed = set(self.vocab["direction"])
        strength_allowed = set(self.vocab["strength"])
        level_allowed = set(self.vocab["level"])
        role_allowed = {
            "ClinicalCondition",
            "ClinicalParameter",
            "Medication",
            "Procedure",
            "Qualifier Value",
        }

        for rule in row["rules"]:
            conditions = rule.get("conditions") or []
            actions = rule.get("actions") or []
            self.assertGreater(len(conditions), 0)
            self.assertGreater(len(actions), 0)

            for condition in conditions:
                self.assertIn(condition.get("role"), role_allowed)
                standardized = condition.get("entity_standardized_list") or []
                self.assertGreater(len(standardized), 0)
                for candidate in standardized:
                    self.assertTrue(
                        (candidate.get("entity_standardized_candidate") or "").strip()
                    )
                    self.assertTrue((candidate.get("snomed_id") or "").strip())

                logic = condition.get("logic_structured") or {}
                operator = (logic.get("operator") or "").strip()
                if operator:
                    self.assertIn(operator, operator_allowed)
                logic_type = (logic.get("logic_type") or "").strip()
                if logic_type:
                    self.assertIn(logic_type.upper(), logic_type_allowed)

            for action in actions:
                self.assertIn(action.get("role"), role_allowed)
                standardized = action.get("entity_standardized_list") or []
                self.assertGreater(len(standardized), 0)
                for candidate in standardized:
                    self.assertTrue(
                        (candidate.get("entity_standardized_candidate") or "").strip()
                    )
                    self.assertTrue((candidate.get("snomed_id") or "").strip())

                logic = action.get("logic_structured") or {}
                direction = (logic.get("direction") or "").strip()
                if direction:
                    self.assertIn(direction, direction_allowed)

                strength = (logic.get("strength") or "").strip()
                if strength:
                    normalized_strength = (
                        strength
                        if strength.startswith("Class ")
                        else f"Class {strength}"
                    )
                    self.assertIn(normalized_strength, strength_allowed)

                level = (logic.get("level") or "").strip()
                if level:
                    self.assertIn(level, level_allowed)


if __name__ == "__main__":
    unittest.main()

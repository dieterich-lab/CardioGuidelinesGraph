import re
import unittest
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    PROJECT_ROOT / "config" / "cardio_graph_core" / "guideline_graph_schema.yaml"
)
BAML_PATH = (
    PROJECT_ROOT
    / "src"
    / "cardio_graph_core"
    / "extraction"
    / "baml_src"
    / "extract_concepts.baml"
)
LOADER_PATH = (
    PROJECT_ROOT / "src" / "cardio_graph_core" / "neo4j" / "grounding_index_to_neo4j.py"
)


class TestSchemaContractAlignment(unittest.TestCase):
    def setUp(self):
        self.schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.baml_text = BAML_PATH.read_text(encoding="utf-8")
        self.loader_text = LOADER_PATH.read_text(encoding="utf-8")

    def test_no_extraction_profile_block(self):
        self.assertNotIn("schema_profiles", self.schema)

    def test_baml_contains_required_origin_fields(self):
        required_fields = ["entity_original", "entity_standardized_candidate"]
        for field in required_fields:
            self.assertRegex(self.baml_text, rf"\b{re.escape(field)}\b")

    def test_baml_contains_core_logic_fields(self):
        core_logic_fields = {
            "operator",
            "threshold",
            "unit",
            "context",
            "logic_type",
            "logic_group",
            "strength",
            "level",
            "direction",
        }
        for field in core_logic_fields:
            self.assertRegex(self.baml_text, rf"\b{re.escape(field)}\b")

    def test_node_level_enums_defined_for_logic(self):
        nodes = self.schema.get("nodes") or []

        def _get_attr(label, name):
            for node in nodes:
                if node.get("label") != label:
                    continue
                for attr in node.get("attributes", []) or []:
                    if attr.get("name") == name:
                        return attr
            return {}

        operator_attr = _get_attr("DecisionNode", "operator")
        logic_type_attr = _get_attr("DecisionNode", "logic_type")
        direction_attr = _get_attr("RecommendationNode", "direction")

        self.assertTrue(operator_attr.get("allowed"))
        self.assertIn("<=", operator_attr.get("allowed", []))
        self.assertIn(">=", operator_attr.get("allowed", []))
        self.assertTrue(logic_type_attr.get("allowed"))
        self.assertIn("SINGLE", logic_type_attr.get("allowed", []))
        self.assertTrue(direction_attr.get("allowed"))
        self.assertIn("POSITIVE", direction_attr.get("allowed", []))


if __name__ == "__main__":
    unittest.main()

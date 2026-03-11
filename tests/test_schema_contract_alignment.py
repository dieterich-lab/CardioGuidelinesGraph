import re
import unittest
from pathlib import Path

import yaml

from cardio_graph_core.extraction.schema_contract_sync import baml_snippets_from_schema

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
        self.assertEqual(
            set(operator_attr.get("allowed", [])),
            {"<", ">", "=", "PRESENT", "ABSENT"},
        )
        self.assertTrue(logic_type_attr.get("allowed"))
        self.assertIn("SINGLE", logic_type_attr.get("allowed", []))
        self.assertTrue(direction_attr.get("allowed"))
        self.assertEqual(
            set([v for v in direction_attr.get("allowed", []) if v is not None]),
            {"<", ">", "=", "POSITIVE", "NEGATIVE"},
        )
        self.assertIn("POSITIVE", direction_attr.get("allowed", []))

    def test_baml_operator_and_direction_vocab_aligned_with_v13(self):
        snippets = baml_snippets_from_schema(self.schema)
        self.assertIn(snippets["operator_prompt"], self.baml_text)
        self.assertIn(snippets["direction_prompt"], self.baml_text)
        self.assertNotIn("PRESENT, ABSENT, PLANNED", self.baml_text)
        self.assertNotIn("POSITIVE, NEGATIVE, UNKNOWN", self.baml_text)

    def test_schema_prompt_blocks_exist_for_non_coercible_enum_guidance(self):
        # BAML enforces shape via ctx.output_format; these blocks are reserved for enum/value guidance.
        required_markers = [
            "[BEGIN SCHEMA_OPERATOR_PROMPT]",
            "[END SCHEMA_OPERATOR_PROMPT]",
            "[BEGIN SCHEMA_DIRECTION_USE_PROMPT]",
            "[END SCHEMA_DIRECTION_USE_PROMPT]",
            "[BEGIN SCHEMA_OPERATOR_PROMPT_RULES]",
            "[END SCHEMA_OPERATOR_PROMPT_RULES]",
            "[BEGIN SCHEMA_DIRECTION_PROMPT_RULES]",
            "[END SCHEMA_DIRECTION_PROMPT_RULES]",
        ]
        for marker in required_markers:
            self.assertIn(marker, self.baml_text)


if __name__ == "__main__":
    unittest.main()

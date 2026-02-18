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

    def test_extraction_profile_exists(self):
        profile = (self.schema.get("schema_profiles") or {}).get("extraction")
        self.assertIsInstance(profile, dict)
        self.assertEqual(profile.get("source_of_truth"), "guideline_graph_schema.yaml")

    def test_rule_cardinality_constraints_exist(self):
        profile = self.schema["schema_profiles"]["extraction"]
        rule_structure = profile.get("rule_structure") or {}
        self.assertGreaterEqual((rule_structure.get("conditions") or {}).get("min_items", 0), 1)
        self.assertGreaterEqual(
            (rule_structure.get("actions") or {}).get("min_items_main_focus", 0),
            1,
        )

    def test_baml_contains_required_origin_fields(self):
        profile = self.schema["schema_profiles"]["extraction"]
        required_fields = (profile.get("origin_fields") or {}).get("required", [])
        for field in required_fields:
            self.assertRegex(self.baml_text, rf"\b{re.escape(field)}\b")

    def test_baml_contains_condition_logic_fields(self):
        profile = self.schema["schema_profiles"]["extraction"]
        logic_fields = set((profile.get("logic_fields") or {}).keys())
        for field in logic_fields:
            self.assertRegex(self.baml_text, rf"\b{re.escape(field)}\b")

    def test_baml_contains_recommendation_fields(self):
        profile = self.schema["schema_profiles"]["extraction"]
        rec_fields = set((profile.get("recommendation_fields") or {}).keys())
        for field in rec_fields:
            self.assertRegex(self.baml_text, rf"\b{re.escape(field)}\b")

    def test_loader_contains_contract_mappings(self):
        profile = self.schema["schema_profiles"]["extraction"]
        threshold_mapping = profile["logic_fields"]["threshold"][
            "maps_to_graph_attribute"
        ]
        strength_mapping = profile["recommendation_fields"]["strength"][
            "maps_to_graph_attribute"
        ]
        level_mapping = profile["recommendation_fields"]["level"][
            "maps_to_graph_attribute"
        ]
        self.assertIn(threshold_mapping, self.loader_text)
        self.assertIn(strength_mapping, self.loader_text)
        self.assertIn(level_mapping, self.loader_text)


if __name__ == "__main__":
    unittest.main()

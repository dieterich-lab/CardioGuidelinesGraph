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

    def test_extraction_contract_exists(self):
        contract = self.schema.get("extraction_contract")
        self.assertIsInstance(contract, dict)
        self.assertEqual(contract.get("source_of_truth"), "guideline_graph_schema.yaml")

    def test_baml_contains_required_origin_fields(self):
        contract = self.schema["extraction_contract"]
        required_fields = contract.get("required_origin_fields", [])
        for field in required_fields:
            self.assertRegex(self.baml_text, rf"\b{re.escape(field)}\b")

    def test_baml_contains_condition_logic_fields(self):
        contract = self.schema["extraction_contract"]
        logic_fields = set(contract.get("condition_logic_fields", {}).keys())
        for field in logic_fields:
            self.assertRegex(self.baml_text, rf"\b{re.escape(field)}\b")

    def test_baml_contains_recommendation_fields(self):
        contract = self.schema["extraction_contract"]
        rec_fields = set(contract.get("recommendation_fields", {}).keys())
        for field in rec_fields:
            self.assertRegex(self.baml_text, rf"\b{re.escape(field)}\b")

    def test_loader_contains_contract_mappings(self):
        contract = self.schema["extraction_contract"]
        threshold_mapping = contract["condition_logic_fields"]["threshold"][
            "maps_to_graph_attribute"
        ]
        strength_mapping = contract["recommendation_fields"]["strength"][
            "maps_to_graph_attribute"
        ]
        level_mapping = contract["recommendation_fields"]["level"][
            "maps_to_graph_attribute"
        ]
        self.assertIn(threshold_mapping, self.loader_text)
        self.assertIn(strength_mapping, self.loader_text)
        self.assertIn(level_mapping, self.loader_text)


if __name__ == "__main__":
    unittest.main()

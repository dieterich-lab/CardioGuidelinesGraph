import unittest
from pathlib import Path

from cardio_graph_core.extraction.schema_contract_sync import (
    expected_baml_type_contract_from_schema,
    extract_baml_class_field_names,
    load_schema,
)

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


class TestBamlTypeContractAlignment(unittest.TestCase):
    def test_baml_type_fields_match_expected_contract(self):
        schema = load_schema(SCHEMA_PATH)
        baml_text = BAML_PATH.read_text(encoding="utf-8")

        expected = expected_baml_type_contract_from_schema(schema)
        for class_name, expected_fields in expected.items():
            actual_fields = extract_baml_class_field_names(baml_text, class_name)
            self.assertEqual(
                actual_fields,
                expected_fields,
                f"BAML class {class_name} drifted from expected formal contract.",
            )

    def test_logic_structured_field_coverage(self):
        baml_text = BAML_PATH.read_text(encoding="utf-8")
        fields = set(extract_baml_class_field_names(baml_text, "LogicStructured"))
        self.assertTrue({"operator", "direction", "strength", "level"}.issubset(fields))


if __name__ == "__main__":
    unittest.main()

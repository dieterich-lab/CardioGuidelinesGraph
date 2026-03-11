import re
import unittest
from pathlib import Path

from cardio_graph_core.extraction.schema_contract_sync import (
    baml_managed_block_values_from_schema,
    extract_baml_managed_block_values,
    load_schema,
    sync_extract_concepts_baml_text,
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


class TestBamlSchemaFragmentSync(unittest.TestCase):
    def _normalize_ws(self, value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    def test_extract_concepts_baml_schema_fragments_are_synced(self):
        schema = load_schema(SCHEMA_PATH)
        current = BAML_PATH.read_text(encoding="utf-8")
        expected = sync_extract_concepts_baml_text(current, schema)
        self.assertEqual(
            current,
            expected,
            "extract_concepts.baml contains schema-bound prompt fragments out of sync with guideline_graph_schema.yaml. "
            "Run: /home/pwiesenbach/CardioGuidelinesGraph/.venv/bin/python scripts/sync_baml_schema_fragments.py",
        )

    def test_managed_blocks_match_schema_generated_values(self):
        schema = load_schema(SCHEMA_PATH)
        current = BAML_PATH.read_text(encoding="utf-8")
        expected_blocks = baml_managed_block_values_from_schema(schema)
        current_blocks = extract_baml_managed_block_values(current)
        normalized_current = {
            key: self._normalize_ws(value) for key, value in current_blocks.items()
        }
        normalized_expected = {
            key: self._normalize_ws(value) for key, value in expected_blocks.items()
        }
        self.assertEqual(normalized_current, normalized_expected)

    def test_manual_prompt_core_instructions_remain_present(self):
        current = BAML_PATH.read_text(encoding="utf-8")
        required_manual_lines = [
            "Core requirement: NEVER mix conditions and actions in the same list.",
            "If [FOCUS: MAIN], each rule must include at least one action.",
            "If [FOCUS: POPULATION], actions MUST be an empty array and output only eligibility/population conditions.",
            'For class strength, always output "Class I", "Class IIa", "Class IIb", or "Class III".',
        ]
        for line in required_manual_lines:
            self.assertIn(line, current)


if __name__ == "__main__":
    unittest.main()

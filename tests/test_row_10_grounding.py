import json
import os
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR = Path(os.environ.get("CARDIO_GRAPH_DATA_DIR", DEFAULT_DATA_DIR))
GRAPH_DIR = Path(os.environ.get("CARDIO_GRAPH_GRAPH_DIR", DATA_DIR / "graph"))
RULES_PATH = Path(
    os.environ.get(
        "CARDIO_GRAPH_RULES_ROW10_PATH",
        GRAPH_DIR / "extracted_rules_docling_table_000_row10.jsonl",
    )
)
GROUND_TRUTH_PATH = Path(
    os.environ.get("CARDIO_GRAPH_ROW10_GROUND_TRUTH_PATH", "")
)


def _load_rules():
    rows = []
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _load_ground_truth():
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@unittest.skipUnless(
    GROUND_TRUTH_PATH and GROUND_TRUTH_PATH.is_file(),
    "Row10 grounding truth not available. Set CARDIO_GRAPH_ROW10_GROUND_TRUTH_PATH.",
)
class Row10GroundingTests(unittest.TestCase):
    def setUp(self):
        if not RULES_PATH.is_file():
            self.skipTest(
                "Missing rules file: "
                + str(RULES_PATH)
                + ". Set CARDIO_GRAPH_RULES_ROW10_PATH."
            )

    def test_row_10_grounding_matches_truth(self):
        rules_rows = _load_rules()
        truth = _load_ground_truth()

        self.assertIsInstance(truth, dict, "Ground truth must be a JSON object.")
        self.assertIn("mappings", truth, "Ground truth missing 'mappings' key.")

        expected = truth.get("mappings", {})
        actual = {
            row.get("entity_standardized_candidate"): row.get("snomed_id")
            for row in rules_rows
            if row.get("entity_standardized_candidate")
        }

        self.assertEqual(
            expected,
            actual,
            "Row_10 grounding should match the curated ground truth mapping.",
        )


if __name__ == "__main__":
    unittest.main()

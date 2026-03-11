from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from cardio_graph_core.tuning.score_adapter import build_score_report_from_alignment


def _write_alignment(payload: dict) -> Path:
    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    with tmp:
        json.dump(payload, tmp)
    return Path(tmp.name)


class TestTuningScoreAdapterProfiles(unittest.TestCase):
    def test_tolerant_profile_downweights_extra_and_condition(self):
        payload = {
            "rows": [
                {
                    "row_id": "row_01",
                    "expected_entries": [
                        {
                            "role": "ClinicalCondition",
                            "entity": "myocardial infarction",
                            "logic_type": "AND",
                            "logic_group": "and_1",
                        }
                    ],
                    "actual_entries": [
                        {
                            "role": "ClinicalCondition",
                            "entity": "myocardial infarction",
                            "logic_type": "AND",
                            "logic_group": "and_1",
                        },
                        {
                            "role": "ClinicalCondition",
                            "entity": "prior myocardial infarction",
                            "logic_type": "AND",
                            "logic_group": "and_1",
                        },
                    ],
                    "concept_missing": [],
                    "concept_extra": ["prior myocardial infarction"],
                    "rule_missing": [],
                    "rule_extra": [],
                }
            ]
        }
        alignment = _write_alignment(payload)

        os.environ["CARDIO_GRAPH_TUNING_SCORE_PROFILE"] = "strict"
        strict = build_score_report_from_alignment(
            alignment,
            run_id="strict",
            split="dev",
            prompt_version="p0",
            run_success=True,
        )

        os.environ["CARDIO_GRAPH_TUNING_SCORE_PROFILE"] = "tolerant"
        os.environ["CARDIO_GRAPH_TUNING_EXTRA_CONCEPT_WEIGHT"] = "0.25"
        os.environ["CARDIO_GRAPH_TUNING_EXTRA_AND_CONCEPT_WEIGHT"] = "0.10"
        tolerant = build_score_report_from_alignment(
            alignment,
            run_id="tol",
            split="dev",
            prompt_version="p0",
            run_success=True,
        )

        self.assertGreater(
            tolerant.metrics.concept_precision, strict.metrics.concept_precision
        )

    def test_semantic_normalization_matches_aliases(self):
        payload = {
            "rows": [
                {
                    "row_id": "row_01",
                    "expected_entries": [
                        {
                            "role": "Procedure",
                            "entity": "percutaneous coronary intervention",
                        }
                    ],
                    "actual_entries": [
                        {
                            "role": "Procedure",
                            "entity": "PCI",
                        }
                    ],
                    "concept_missing": [],
                    "concept_extra": [],
                    "rule_missing": [],
                    "rule_extra": [],
                }
            ]
        }
        alignment = _write_alignment(payload)

        os.environ["CARDIO_GRAPH_TUNING_ENABLE_SEMANTIC_NORMALIZATION"] = "true"
        report = build_score_report_from_alignment(
            alignment,
            run_id="norm",
            split="dev",
            prompt_version="p0",
            run_success=True,
        )

        self.assertEqual(report.metrics.concept_recall, 1.0)

    def test_singleton_condition_ignores_logic_type_group(self):
        payload = {
            "rows": [
                {
                    "row_id": "row_01",
                    "expected_entries": [
                        {
                            "role": "ClinicalCondition",
                            "entity": "complex clinical cases",
                            "operator": "PRESENT",
                            "logic_type": "AND",
                            "logic_group": "and_1",
                        }
                    ],
                    "actual_entries": [
                        {
                            "role": "ClinicalCondition",
                            "entity": "complex clinical cases",
                            "operator": "PRESENT",
                            "logic_type": "SINGLE",
                            "logic_group": "single_1",
                        }
                    ],
                    "concept_missing": [],
                    "concept_extra": [],
                    "rule_missing": [],
                    "rule_extra": [],
                }
            ]
        }
        alignment = _write_alignment(payload)

        report = build_score_report_from_alignment(
            alignment,
            run_id="singleton_logic",
            split="dev",
            prompt_version="p0",
            run_success=True,
        )

        self.assertEqual(report.metrics.rule_exact_match, 1.0)
        self.assertEqual(report.metrics.logic_group_accuracy, 0.0)
        row_errors = report.rows[0].errors
        self.assertFalse(
            any(err.error_class == "C5_logic_type_wrong" for err in row_errors)
        )
        self.assertFalse(
            any(err.error_class == "C6_logic_group_wrong" for err in row_errors)
        )


if __name__ == "__main__":
    unittest.main()

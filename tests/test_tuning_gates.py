import unittest

from cardio_graph_core.tuning.contracts import Metrics
from cardio_graph_core.tuning.gates import GateThresholds, evaluate_locked_test_gate


def _metrics(
    rule_exact_match: float,
    operator_accuracy: float,
    logic_group_accuracy: float,
    concept_f1: float,
) -> Metrics:
    return Metrics(
        schema_valid_rate=1.0,
        rule_exact_match=rule_exact_match,
        operator_accuracy=operator_accuracy,
        logic_group_accuracy=logic_group_accuracy,
        concept_precision=0.8,
        concept_recall=0.4,
        concept_f1=concept_f1,
        grounding_hit_rate=0.0,
    )


class TestTuningGates(unittest.TestCase):
    def test_locked_gate_rejects_operator_regression_when_min_gain_zero(self):
        champion = _metrics(
            rule_exact_match=0.10,
            operator_accuracy=0.80,
            logic_group_accuracy=0.50,
            concept_f1=0.45,
        )
        challenger = _metrics(
            rule_exact_match=0.20,
            operator_accuracy=0.79,
            logic_group_accuracy=0.70,
            concept_f1=0.50,
        )

        decision = evaluate_locked_test_gate(
            champion, challenger, GateThresholds(min_locked_test_operator_gain=0.0)
        )

        self.assertFalse(decision.accepted)
        self.assertTrue(
            any(
                "locked-test operator_accuracy did not meet minimum gain" in reason
                for reason in decision.reasons
            )
        )

    def test_locked_gate_accepts_when_rule_and_operator_constraints_hold(self):
        champion = _metrics(
            rule_exact_match=0.10,
            operator_accuracy=0.80,
            logic_group_accuracy=0.50,
            concept_f1=0.45,
        )
        challenger = _metrics(
            rule_exact_match=0.12,
            operator_accuracy=0.80,
            logic_group_accuracy=0.70,
            concept_f1=0.50,
        )

        decision = evaluate_locked_test_gate(
            champion, challenger, GateThresholds(min_locked_test_operator_gain=0.0)
        )

        self.assertTrue(decision.accepted)
        self.assertEqual([], decision.reasons)


if __name__ == "__main__":
    unittest.main()

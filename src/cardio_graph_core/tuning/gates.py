from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from cardio_graph_core.tuning.contracts import GateDecision, Metrics


@dataclass
class GateThresholds:
    min_rule_exact_gain: float = 0.005
    max_secondary_drop: float = 0.01
    max_locked_test_drop: float = 0.01
    bootstrap_rule_exact_floor: float = 0.05
    bootstrap_min_concept_f1_gain: float = 0.03
    bootstrap_max_operator_drop: float = 0.005
    bootstrap_max_logic_drop: float = 0.005


def metric_deltas(champion: Metrics, challenger: Metrics) -> Dict[str, float]:
    return {
        "schema_valid_rate": challenger.schema_valid_rate - champion.schema_valid_rate,
        "rule_exact_match": challenger.rule_exact_match - champion.rule_exact_match,
        "operator_accuracy": challenger.operator_accuracy - champion.operator_accuracy,
        "logic_group_accuracy": (
            challenger.logic_group_accuracy - champion.logic_group_accuracy
        ),
        "concept_f1": challenger.concept_f1 - champion.concept_f1,
    }


def evaluate_dev_gates(
    champion: Metrics,
    challenger: Metrics,
    thresholds: GateThresholds,
) -> GateDecision:
    reasons: List[str] = []
    deltas = metric_deltas(champion, challenger)
    used_bootstrap = False

    if challenger.schema_valid_rate < 1.0:
        reasons.append("schema_valid_rate must be 1.0")

    rule_gain_ok = deltas["rule_exact_match"] >= thresholds.min_rule_exact_gain
    if not rule_gain_ok:
        if (
            champion.rule_exact_match < thresholds.bootstrap_rule_exact_floor
            and deltas["concept_f1"] >= thresholds.bootstrap_min_concept_f1_gain
            and deltas["operator_accuracy"] >= -thresholds.bootstrap_max_operator_drop
            and deltas["logic_group_accuracy"] >= -thresholds.bootstrap_max_logic_drop
            and challenger.schema_valid_rate >= 1.0
        ):
            used_bootstrap = True
        else:
            reasons.append(
                "rule_exact_match did not meet minimum gain "
                f"({deltas['rule_exact_match']:.4f} < {thresholds.min_rule_exact_gain:.4f})"
            )

    for metric_name in ("operator_accuracy", "logic_group_accuracy", "concept_f1"):
        if deltas[metric_name] < -thresholds.max_secondary_drop:
            reasons.append(
                f"{metric_name} regressed by {deltas[metric_name]:.4f} "
                f"(allowed {-thresholds.max_secondary_drop:.4f})"
            )

    accepted = (not reasons) or used_bootstrap
    if used_bootstrap and reasons:
        reasons = [reason for reason in reasons if not reason.startswith("rule_exact_match did not meet minimum gain")]

    return GateDecision(accepted=accepted, reasons=reasons, deltas=deltas)


def evaluate_locked_test_gate(
    champion_locked_test: Metrics,
    challenger_locked_test: Metrics,
    thresholds: GateThresholds,
) -> GateDecision:
    reasons: List[str] = []
    deltas = metric_deltas(champion_locked_test, challenger_locked_test)

    if deltas["rule_exact_match"] < -thresholds.max_locked_test_drop:
        reasons.append(
            "locked-test rule_exact_match regression exceeded threshold "
            f"({deltas['rule_exact_match']:.4f} < {-thresholds.max_locked_test_drop:.4f})"
        )

    return GateDecision(accepted=not reasons, reasons=reasons, deltas=deltas)

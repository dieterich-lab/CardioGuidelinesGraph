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
HUMAN_READABLE_PATH = Path(
    os.environ.get(
        "CARDIO_GRAPH_ROW10_HUMAN_READABLE_PATH",
        GRAPH_DIR / "row_10_human_readable.json",
    )
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


def _load_human_readable():
    with open(HUMAN_READABLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize(value):
    if value is None:
        return None
    return " ".join(str(value).strip().split()).lower()


def _normalize_logic(logic, role=None):
    operator = logic.get("operator")
    if operator is None and role in {"Condition", "ClinicalParameter"}:
        operator = "PRESENT"
    return {
        "operator": operator,
        "threshold": logic.get("threshold"),
        "unit": logic.get("unit"),
        "condition_context": logic.get("condition_context"),
        "logic_type": logic.get("logic_type"),
        "logic_group": logic.get("logic_group"),
    }


def _normalize_action_logic(logic):
    strength = logic.get("strength")
    if isinstance(strength, str) and strength.lower().startswith("class "):
        strength = strength.split(" ", 1)[1].strip()
    return {
        "strength": strength,
        "level": logic.get("level"),
        "direction": logic.get("direction"),
    }


def _summarize_rules(rules_rows):
    grouped = {}
    for row in rules_rows:
        rule_id = row.get("rule_id") or 1
        grouped.setdefault(rule_id, {"conditions": [], "actions": []})
        role = (row.get("role") or "").strip()
        if role in {"Condition", "ClinicalParameter"}:
            grouped[rule_id]["conditions"].append(
                {
                    "entity_original": row.get("entity_original"),
                    "entity_standardized_candidate": _normalize(
                        row.get("entity_standardized_candidate")
                    ),
                    "role": role,
                    "logic_structured": _normalize_logic(
                        row.get("logic_structured") or {},
                        role=role,
                    ),
                }
            )
        elif role in {"Procedure", "Medication"}:
            grouped[rule_id]["actions"].append(
                {
                    "entity_original": row.get("entity_original"),
                    "entity_standardized_candidate": _normalize(
                        row.get("entity_standardized_candidate")
                    ),
                    "role": role,
                    "logic_structured": _normalize_action_logic(
                        row.get("logic_structured") or {}
                    ),
                }
            )
    return grouped


def _summarize_human(human):
    grouped = {}
    for rule in human.get("rules", []):
        rule_id = rule.get("rule_id") or 1
        grouped.setdefault(rule_id, {"conditions": [], "actions": []})
        for condition in rule.get("conditions", []):
            role = condition.get("role")
            grouped[rule_id]["conditions"].append(
                {
                    "entity_original": condition.get("entity_original"),
                    "entity_standardized_candidate": _normalize(
                        condition.get("entity_standardized_candidate")
                    ),
                    "role": role,
                    "logic_structured": _normalize_logic(
                        condition.get("logic_structured") or {},
                        role=role,
                    ),
                }
            )
        for action in rule.get("actions", []):
            grouped[rule_id]["actions"].append(
                {
                    "entity_original": action.get("entity_original"),
                    "entity_standardized_candidate": _normalize(
                        action.get("entity_standardized_candidate")
                    ),
                    "role": action.get("role"),
                    "logic_structured": _normalize_action_logic(
                        action.get("logic_structured") or {}
                    ),
                }
            )
    return grouped


class Row10StructureRulesTests(unittest.TestCase):
    def setUp(self):
        if not RULES_PATH.is_file():
            self.skipTest(
                "Missing rules file: "
                + str(RULES_PATH)
                + ". Set CARDIO_GRAPH_RULES_ROW10_PATH."
            )
        if not HUMAN_READABLE_PATH.is_file():
            self.skipTest(
                "Missing human-readable file: "
                + str(HUMAN_READABLE_PATH)
                + ". Set CARDIO_GRAPH_ROW10_HUMAN_READABLE_PATH."
            )

    def _assert_verbose(self, label, expected, actual, note):
        print("\nCHECK: " + label)
        print("EXPECTED:\n" + json.dumps(expected, indent=2))
        print("ACTUAL:\n" + json.dumps(actual, indent=2))
        print("NOTE:\n" + note)
        self.assertEqual(actual, expected)

    def test_row_10_rules_match_human_readable(self):
        rules_rows = _load_rules()
        human = _load_human_readable()

        rules_summary = _summarize_rules(rules_rows)
        human_summary = _summarize_human(human)

        self._assert_verbose(
            "Rule IDs",
            sorted(human_summary.keys()),
            sorted(rules_summary.keys()),
            "Rule IDs should match between rules/index output and human-readable file.",
        )

        for rule_id, human_rule in human_summary.items():
            rules_rule = rules_summary.get(rule_id, {"conditions": [], "actions": []})
            self._assert_verbose(
                "Rule " + str(rule_id) + " conditions",
                sorted(human_rule["conditions"], key=lambda x: x["entity_original"]),
                sorted(rules_rule["conditions"], key=lambda x: x["entity_original"]),
                "Conditions should match between rules/index output and human-readable file (grounding ignored).",
            )
            self._assert_verbose(
                "Rule " + str(rule_id) + " actions",
                sorted(human_rule["actions"], key=lambda x: x["entity_original"]),
                sorted(rules_rule["actions"], key=lambda x: x["entity_original"]),
                "Actions should match between rules/index output and human-readable file (grounding ignored).",
            )


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Export row-wise ground-truth rule Mermaid graphs for Tables 22, 17, and 8."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from cardio_graph_core.common.paths import ground_truth_rule_graphs_root

DEFAULT_SOURCES = {
    "22": "/prj/doctoral_letters/guide/data/evaluation/table_22_manual_1.3.json",
    "17": "/prj/doctoral_letters/guide/data/evaluation/table_17_manual_1.3.json",
    "8": "/prj/doctoral_letters/guide/data/evaluation/table_8_manual_1.3.json",
}


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    return " ".join(str(value).strip().split()).lower()


def _normalize_role(role: Any) -> str | None:
    if role is None:
        return None
    return str(role).strip()


def _normalize_strength(strength: Any) -> str | None:
    if strength is None:
        return None
    return str(strength).strip()


def _normalize_level(level: Any) -> str | None:
    if level is None:
        return None
    return str(level).strip()


def _normalize_direction(direction: Any) -> str | None:
    if direction is None:
        return None
    return str(direction).strip()


def _normalize_logic(logic: Dict[str, Any]) -> Dict[str, Any]:
    operator = logic.get("operator")
    if operator is None and (logic.get("logic_type") or logic.get("logic_group")):
        operator = "PRESENT"
    return {
        "operator": operator,
        "threshold": logic.get("threshold"),
        "unit": logic.get("unit"),
        "context": _normalize_text(logic.get("context")),
        "logic_type": logic.get("logic_type"),
        "logic_group": logic.get("logic_group"),
        "strength": _normalize_strength(logic.get("strength")),
        "level": _normalize_level(logic.get("level")),
        "direction": _normalize_direction(logic.get("direction")),
    }


def _build_entry(
    entity: Any, entity_original: Any, role: Any, logic: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        "entity": _normalize_text(entity),
        "entity_original": _normalize_text(entity_original),
        "role": _normalize_role(role),
        **_normalize_logic(logic or {}),
    }


def _build_entry_with_side(
    entity: Any, entity_original: Any, role: Any, logic: Dict[str, Any], side: str
) -> Dict[str, Any]:
    entry = _build_entry(entity, entity_original, role, logic)
    entry["_side"] = side
    return entry


def _sanitize_label(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace('"', "'")


def _sanitize_id(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-zA-Z0-9_]", "_", str(value))


def _group_entries(entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for entry in entries:
        group = entry.get("logic_group") or "group_1"
        grouped.setdefault(str(group), []).append(entry)
    return grouped


def _group_type(group_name: str, entries: List[Dict[str, Any]]) -> str:
    if str(group_name).lower().startswith("or"):
        return "OR"
    for entry in entries:
        if str(entry.get("logic_type") or "").upper() == "OR":
            return "OR"
    return "AND"


def _build_mermaid(entries_or_rules: Any, title: str) -> str:
    def _flatten_entries_with_side(payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, dict) and isinstance(payload.get("rules"), list):
            payload = payload.get("rules")

        if (
            isinstance(payload, list)
            and payload
            and all(
                isinstance(item, dict)
                and {"conditions", "actions"}.issubset(item.keys())
                for item in payload
            )
        ):
            flattened: List[Dict[str, Any]] = []
            for rule in payload:
                for condition in rule.get("conditions", []):
                    item = dict(condition)
                    item["_side"] = "condition"
                    flattened.append(item)
                for action in rule.get("actions", []):
                    item = dict(action)
                    item["_side"] = "action"
                    flattened.append(item)
            return flattened

        if isinstance(payload, list):
            return payload
        return []

    entries = _flatten_entries_with_side(entries_or_rules)

    def is_condition(entry: Dict[str, Any]) -> bool:
        side = (entry.get("_side") or "").strip().lower()
        if side:
            return side == "condition"
        if entry.get("role") in {
            "ClinicalCondition",
            "ClinicalParameter",
            "Qualifier Value",
        }:
            return True
        return bool(entry.get("logic_type") or entry.get("logic_group"))

    def is_action(entry: Dict[str, Any]) -> bool:
        side = (entry.get("_side") or "").strip().lower()
        if side:
            return side == "action"
        if entry.get("role") in {"Procedure", "Medication", "ClinicalAction"}:
            return not (entry.get("logic_type") or entry.get("logic_group"))
        return False

    condition_entries_all = [entry for entry in entries if is_condition(entry)]
    groups = _group_entries(condition_entries_all)
    actions = [entry for entry in entries if is_action(entry)]

    ordered_groups: List[Dict[str, Any]] = []
    for group_name, group_entries in groups.items():
        ordered_groups.append(
            {
                "group_name": group_name,
                "group_entries": group_entries,
                "group_type": _group_type(group_name, group_entries),
            }
        )

    lines = ["graph LR", "  REC[RecommendationNode]"]

    if actions:
        for idx, action in enumerate(actions, start=1):
            action_id = f"ACT{idx}"
            label = _sanitize_label(action.get("entity"))
            role = action.get("role") or "Action"
            direction = str(action.get("direction") or "").strip().upper()
            if direction in {"NEGATIVE", "CONTRAINDICATED", "DO_NOT_USE"}:
                relation = "CONTRAINDICATES"
            elif role == "Procedure":
                relation = "RECOMMENDS_PROCEDURE"
            else:
                relation = "RECOMMENDS_USAGE"
            lines.append(f"  {action_id}[{role}: {label}]")
            lines.append(f"  REC -->|{relation}| {action_id}")

    previous_decisions: List[str] = []
    for group in ordered_groups:
        group_name = group["group_name"]
        group_entries = group["group_entries"]
        group_type = group["group_type"]
        group_id = _sanitize_id(group_name)
        lines.append(f"  subgraph {title}_{group_id}_{group_type}")

        decision_ids: List[str] = []
        for idx, entry in enumerate(group_entries, start=1):
            decision_id = f"D_{group_id}_{idx}"
            concept_id = f"C_{group_id}_{idx}"
            decision_ids.append(decision_id)
            role = entry.get("role") or "Concept"
            label = _sanitize_label(entry.get("entity"))
            relation = "EVALUATES" if role == "ClinicalParameter" else "CHECKS_FOR"
            lines.append(f"    {decision_id}[DecisionNode {group_id} s{idx}]")
            lines.append(f"    {concept_id}[{role}: {label}]")
            lines.append(f"    {decision_id} -->|{relation}| {concept_id}")

        if previous_decisions and decision_ids:
            if group_type == "OR":
                for prev_id in previous_decisions:
                    for curr_id in decision_ids:
                        lines.append(
                            f"    {prev_id} -->|LEADS_TO condition_met=true| {curr_id}"
                        )
            else:
                first_id = decision_ids[0]
                for prev_id in previous_decisions:
                    lines.append(
                        f"    {prev_id} -->|LEADS_TO condition_met=true| {first_id}"
                    )

        if group_type == "AND" and len(decision_ids) > 1:
            for idx in range(1, len(decision_ids)):
                lines.append(
                    f"    {decision_ids[idx - 1]} -->|LEADS_TO condition_met=true| {decision_ids[idx]}"
                )

        if not group_entries:
            lines.append("    REC")

        lines.append("  end")

        if decision_ids:
            previous_decisions = (
                decision_ids if group_type == "OR" else [decision_ids[-1]]
            )

    if previous_decisions:
        for prev_id in previous_decisions:
            lines.append(f"  {prev_id} -->|RESULTS_IN condition_met=true| REC")

    return "\n".join(lines)


def _iter_rows(
    payload: Dict[str, Any], allowed_table_ids: set[int] | None = None
) -> Iterable[Tuple[int, Dict[str, Any]]]:
    if isinstance(payload, dict) and isinstance(payload.get("tables"), list):
        for table in payload.get("tables", []):
            table_id = table.get("table_id")
            if allowed_table_ids is not None and table_id not in allowed_table_ids:
                continue
            rows = table.get("data", []) or []
            for index, row in enumerate(rows, start=1):
                yield index, row
        return

    rows = payload.get("data", []) if isinstance(payload, dict) else []
    for index, row in enumerate(rows, start=1):
        yield index, row


def _row_entries_and_rules(
    row: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    entries: List[Dict[str, Any]] = []
    rules_payload: List[Dict[str, Any]] = []

    for rule in row.get("rules", []) or []:
        conditions: List[Dict[str, Any]] = []
        actions: List[Dict[str, Any]] = []

        for condition in rule.get("conditions", []) or []:
            entity = condition.get("entity_standardized_candidate") or condition.get(
                "entity_original"
            )
            if _normalize_text(entity) == "string":
                continue
            entry = _build_entry_with_side(
                entity,
                condition.get("entity_original"),
                condition.get("role"),
                condition.get("logic_structured") or {},
                "condition",
            )
            entries.append(entry)
            conditions.append(dict(entry))

        for action in rule.get("actions", []) or []:
            entity = action.get("entity_standardized_candidate") or action.get(
                "entity_original"
            )
            if _normalize_text(entity) == "string":
                continue
            entry = _build_entry_with_side(
                entity,
                action.get("entity_original"),
                action.get("role"),
                action.get("logic_structured") or {},
                "action",
            )
            entries.append(entry)
            actions.append(dict(entry))

        if conditions or actions:
            rules_payload.append({"conditions": conditions, "actions": actions})

    return entries, rules_payload


def _row_markdown(
    table_name: str,
    row_index: int,
    row: Dict[str, Any],
    rules_payload: List[Dict[str, Any]],
) -> str:
    title = f"Ground Truth Rules - Table {table_name} Row {row_index:02d}"
    recommendation = row.get("recommendation") or row.get("Recommendations") or ""
    mermaid = _build_mermaid(rules_payload, f"Table{table_name}Row{row_index:02d}")

    lines = [
        f"# {title}",
        "",
        f"- table: {table_name}",
        f"- row: row_{row_index:02d}",
        "",
        "Recommendation text:",
        "",
        "```text",
        str(recommendation).strip(),
        "```",
        "",
        "Ground-truth rules:",
        "",
        "```json",
        json.dumps(rules_payload, indent=2),
        "```",
        "",
        "Mermaid graph:",
        "",
        "```mermaid",
        mermaid,
        "```",
        "",
    ]
    return "\n".join(lines)


def _load_payload(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected dict JSON payload in {path}")
    return payload


def export_table_graphs(
    table_name: str,
    source_path: Path,
    out_root: Path,
    allowed_table_ids: set[int] | None = None,
) -> int:
    payload = _load_payload(source_path)
    table_dir = out_root / f"table_{table_name}"
    table_dir.mkdir(parents=True, exist_ok=True)

    for stale in table_dir.glob("row_*_graph.md"):
        stale.unlink()

    written = 0
    for row_index, row in _iter_rows(payload, allowed_table_ids=allowed_table_ids):
        entries, rules_payload = _row_entries_and_rules(row)
        if not entries:
            continue
        row_path = table_dir / f"row_{row_index:02d}_graph.md"
        row_path.write_text(
            _row_markdown(table_name, row_index, row, rules_payload),
            encoding="utf-8",
        )
        written += 1

    return written


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export row-wise Mermaid graphs from ground-truth rule files"
    )
    parser.add_argument(
        "--table22-path",
        default=DEFAULT_SOURCES["22"],
        help="Path to Emre Table 22 ground-truth JSON",
    )
    parser.add_argument(
        "--table17-path",
        default=DEFAULT_SOURCES["17"],
        help="Path to Emre Table 17 ground-truth JSON",
    )
    parser.add_argument(
        "--table8-path",
        default=DEFAULT_SOURCES["8"],
        help="Path to Emre Table 8 ground-truth JSON",
    )
    parser.add_argument(
        "--out-dir",
        default=str(ground_truth_rule_graphs_root()),
        help="Output directory root",
    )
    parser.add_argument(
        "--allow-table-id",
        action="append",
        type=int,
        default=None,
        help=(
            "Optional table_id filter inside source JSON (repeatable). "
            "Default keeps table_id=0 only."
        ),
    )
    args = parser.parse_args()

    sources = {
        "22": Path(args.table22_path),
        "17": Path(args.table17_path),
        "8": Path(args.table8_path),
    }
    for table_name, src in sources.items():
        if not src.is_file():
            raise FileNotFoundError(
                f"Missing ground-truth file for table {table_name}: {src}"
            )

    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    allowed_table_ids = set(args.allow_table_id) if args.allow_table_id else {0}

    totals = {}
    for table_name, src in sources.items():
        totals[table_name] = export_table_graphs(
            table_name,
            src,
            out_root,
            allowed_table_ids=allowed_table_ids,
        )

    print("Wrote ground-truth row graphs:")
    for table_name in ("22", "17", "8"):
        print(f"table_{table_name}: {totals[table_name]} rows")
    print(f"output_root: {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import json
import re
from pathlib import Path


def _sanitize_label(value):
    if value is None:
        return ""
    return str(value).replace('"', "'")


def _sanitize_id(value):
    if value is None:
        return ""
    return re.sub(r"[^a-zA-Z0-9_]", "_", str(value))


def _group_entries(entries):
    grouped = {}
    for entry in entries:
        group = entry.get("logic_group") or "group_1"
        grouped.setdefault(group, []).append(entry)
    return grouped


def _group_type(group_name, entries):
    if str(group_name).lower().startswith("or"):
        return "OR"
    for entry in entries:
        if str(entry.get("logic_type") or "").upper() == "OR":
            return "OR"
    return "AND"


def _flatten_entries_with_side(payload):
    if isinstance(payload, dict) and isinstance(payload.get("rules"), list):
        payload = payload.get("rules")

    if (
        isinstance(payload, list)
        and payload
        and all(
            isinstance(item, dict) and {"conditions", "actions"}.issubset(item.keys())
            for item in payload
        )
    ):
        flattened = []
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


def _build_mermaid(entries, title):
    entries = _flatten_entries_with_side(entries)

    def is_condition(entry):
        side = (entry.get("_side") or "").strip().lower()
        if side:
            return side == "condition"
        if entry.get("role") in {"ClinicalCondition", "ClinicalParameter"}:
            return True
        return bool(entry.get("logic_type") or entry.get("logic_group"))

    def is_action(entry):
        side = (entry.get("_side") or "").strip().lower()
        if side:
            return side == "action"
        if entry.get("role") in {"Procedure", "Medication", "ClinicalAction"}:
            return not (entry.get("logic_type") or entry.get("logic_group"))
        return False

    condition_entries_all = [entry for entry in entries if is_condition(entry)]
    groups = _group_entries(condition_entries_all)
    actions = [entry for entry in entries if is_action(entry)]
    ordered_groups = []
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

    previous_decisions = []
    for group in ordered_groups:
        group_name = group["group_name"]
        group_entries = group["group_entries"]
        group_type = group["group_type"]
        group_id = _sanitize_id(group_name)
        lines.append(f"  subgraph {title}_{group_id}_{group_type}")

        condition_entries = list(group_entries)
        decision_ids = []
        for idx, entry in enumerate(condition_entries, start=1):
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

        lines.append("  end")

        if decision_ids:
            if group_type == "OR":
                previous_decisions = decision_ids
            else:
                previous_decisions = [decision_ids[-1]]

    if previous_decisions:
        for prev_id in previous_decisions:
            lines.append(f"  {prev_id} -->|RESULTS_IN condition_met=true| REC")

    return "\n".join(lines)


def _format_concept(key):
    role, entity = key
    return f"{role}: {entity}"


def _format_rule(key):
    (
        role,
        entity,
        operator,
        threshold,
        unit,
        context,
        logic_type,
        logic_group,
        strength,
        level,
        direction,
    ) = key
    parts = [f"{role}: {entity}"]
    if operator is not None:
        parts.append(f"op={operator}")
    if threshold is not None:
        parts.append(f"thr={threshold}")
    if unit is not None:
        parts.append(f"unit={unit}")
    if context is not None:
        parts.append(f"ctx={context}")
    if logic_type is not None:
        parts.append(f"logic={logic_type}")
    if logic_group is not None:
        parts.append(f"grp={logic_group}")
    if strength is not None:
        parts.append(f"class={strength}")
    if level is not None:
        parts.append(f"level={level}")
    if direction is not None:
        parts.append(f"dir={direction}")
    return " | ".join(parts)


def _display_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except Exception:
        return str(path)


def _is_empty_grouped_payload(payload):
    if not isinstance(payload, dict):
        return False
    rules = payload.get("rules")
    if not isinstance(rules, list) or not rules:
        return False
    for rule in rules:
        if not isinstance(rule, dict):
            return False
        if rule.get("conditions") or rule.get("actions"):
            return False
    return True


def _infer_side(entry):
    role = entry.get("role")
    if role in {"ClinicalCondition", "ClinicalParameter", "Condition"}:
        return "condition"
    if role in {"Procedure", "Medication", "ClinicalAction"}:
        if entry.get("logic_type") or entry.get("logic_group"):
            return "condition"
        return "action"
    if entry.get("logic_type") or entry.get("logic_group"):
        return "condition"
    return "action"


def _group_from_flat_entries(entries):
    grouped = {"rules": [{"conditions": [], "actions": []}]}
    for raw in entries or []:
        entry = dict(raw)
        side = (entry.get("_side") or "").strip().lower() or _infer_side(entry)
        if side == "condition":
            grouped["rules"][0]["conditions"].append(entry)
        else:
            grouped["rules"][0]["actions"].append(entry)
    return grouped


def render_reports(alignment_path: Path):
    payload = json.loads(alignment_path.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    out_dir = alignment_path.parent
    project_root = Path(__file__).resolve().parents[1]

    summary_csv = out_dir / "table22_rowwise_summary.csv"
    report_md = out_dir / "table22_rowwise_comparison.md"

    summary_csv.write_text(
        "row_id,mapped_actual_row,match_score,expected_concepts,actual_concepts,concept_matches,concept_missing,concept_extra,expected_rules,actual_rules,rule_matches,rule_missing,rule_extra\n",
        encoding="utf-8",
    )
    with summary_csv.open("a", encoding="utf-8") as f:
        for row in rows:
            cs = row["concept_summary"]
            rs = row["rule_summary"]
            f.write(
                f"{row['row_id']},{row['mapped_actual_row']},{row['match_score']:.3f},"
                f"{cs['expected']},{cs['actual']},{cs['matches']},{cs['missing']},{cs['extra']},"
                f"{rs['expected']},{rs['actual']},{rs['matches']},{rs['missing']},{rs['extra']}\n"
            )

    with report_md.open("w", encoding="utf-8") as f:
        f.write("# Table 22 row-wise comparison (concepts and rules)\n\n")
        f.write(f"Ground truth: {payload.get('ground_truth')}\n")
        f.write(f"Extracted rules: {payload.get('extracted_rules')}\n")
        f.write(f"{payload.get('mapping')}\n\n")
        f.write(
            f"Ground after extraction: {payload.get('ground_after_extraction', False)}\n\n"
        )
        f.write(f"Summary CSV: {_display_path(summary_csv, project_root)}\n")
        f.write(f"Aligned JSON: {_display_path(alignment_path, project_root)}\n\n")
        f.write("Per-row reports:\n\n")
        for row in rows:
            row_file = out_dir / f"{row['row_id']}.md"
            f.write(
                f"- {row['row_id']} -> {_display_path(row_file, project_root)} "
                f"(match_score={row['match_score']:.3f})\n"
            )

    for row in rows:
        row_file = out_dir / f"{row['row_id']}.md"
        with row_file.open("w", encoding="utf-8") as f:
            f.write(f"# {row['row_id']} (mapped to {row['mapped_actual_row']})\n\n")
            f.write("Original table row text (ground truth):\n\n")
            f.write("```json\n")
            f.write(json.dumps(row.get("ground_truth_text", {}), indent=2))
            f.write("\n```\n\n")

            f.write("Aligned JSON (expected vs actual):\n\n")
            f.write("<table>\n")
            f.write("  <tr>\n")
            f.write('    <th align="left">Human Annotation</th>\n')
            f.write('    <th align="left">LLM Generated</th>\n')
            f.write("  </tr>\n")
            f.write("  <tr>\n")
            f.write('    <td valign="top"><pre>\n')
            f.write(json.dumps(row.get("expected_entries_display"), indent=2))
            f.write("\n</pre></td>\n")
            f.write('    <td valign="top"><pre>\n')
            actual_display = row.get("actual_entries_display")
            if _is_empty_grouped_payload(actual_display):
                actual_display = _group_from_flat_entries(row.get("actual_entries", []))
            f.write(json.dumps(actual_display, indent=2))
            f.write("\n</pre></td>\n")
            f.write("  </tr>\n")
            f.write("</table>\n\n")

            f.write("Mermaid (Human Annotation):\n\n")
            f.write("```mermaid\n")
            f.write(_build_mermaid(row.get("expected_entries_display"), "Human"))
            f.write("\n```\n\n")

            f.write("Mermaid (LLM Generated):\n\n")
            f.write("```mermaid\n")
            actual_display = row.get("actual_entries_display")
            if _is_empty_grouped_payload(actual_display):
                actual_display = _group_from_flat_entries(row.get("actual_entries", []))
            f.write(_build_mermaid(actual_display, "LLM"))
            f.write("\n```\n\n")

            if row.get("grounding_summary"):
                f.write("Grounding summary (optional):\n\n")
                f.write("```json\n")
                f.write(json.dumps(row.get("grounding_summary"), indent=2))
                f.write("\n```\n\n")

            cs = row["concept_summary"]
            f.write("Concepts:\n")
            f.write(f"- expected: {cs['expected']}\n")
            f.write(f"- actual: {cs['actual']}\n")
            f.write(f"- matches: {cs['matches']}\n")
            f.write(f"- missing: {cs['missing']}\n")
            f.write(f"- extra: {cs['extra']}\n\n")

            if row.get("concept_missing"):
                f.write("Missing concepts:\n")
                for item in sorted(tuple(x) for x in row["concept_missing"]):
                    f.write("- " + _format_concept(item) + "\n")
                f.write("\n")

            if row.get("concept_extra"):
                f.write("Extra concepts:\n")
                for item in sorted(tuple(x) for x in row["concept_extra"]):
                    f.write("- " + _format_concept(item) + "\n")
                f.write("\n")

            rs = row["rule_summary"]
            f.write("Rules (concept + logic fields):\n")
            f.write(f"- expected: {rs['expected']}\n")
            f.write(f"- actual: {rs['actual']}\n")
            f.write(f"- matches: {rs['matches']}\n")
            f.write(f"- missing: {rs['missing']}\n")
            f.write(f"- extra: {rs['extra']}\n\n")

            if row.get("rule_missing"):
                f.write("Missing rules:\n")
                for item in sorted(
                    (tuple(x) for x in row["rule_missing"]),
                    key=lambda x: json.dumps(x),
                ):
                    f.write("- " + _format_rule(item) + "\n")
                f.write("\n")

            if row.get("rule_extra"):
                f.write("Extra rules:\n")
                for item in sorted(
                    (tuple(x) for x in row["rule_extra"]),
                    key=lambda x: json.dumps(x),
                ):
                    f.write("- " + _format_rule(item) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Render table22 markdown reports from existing alignment JSON."
    )
    parser.add_argument(
        "--alignment",
        default="docs/table22_rows_comparison/table22_rowwise_alignment.json",
        help="Path to table22 alignment JSON",
    )
    args = parser.parse_args()
    render_reports(Path(args.alignment))


if __name__ == "__main__":
    main()

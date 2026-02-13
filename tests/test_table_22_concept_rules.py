import json
import os
import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR = Path(os.environ.get("CARDIO_GRAPH_DATA_DIR", DEFAULT_DATA_DIR))
GRAPH_DIR = Path(os.environ.get("CARDIO_GRAPH_GRAPH_DIR", DATA_DIR / "graph"))
DOCS_DIR = Path(os.environ.get("CARDIO_GRAPH_DOCS_DIR", PROJECT_ROOT / "docs"))
ROWS_DIR = Path(
    os.environ.get("CARDIO_GRAPH_TABLE22_ROWS_DIR", DOCS_DIR / "table22_rows")
)
RULES_PATH = Path(
    os.environ.get(
        "CARDIO_GRAPH_TABLE22_RULES_PATH",
        GRAPH_DIR
        / "extracted_rules_docling_table_000_whole_grid_score0.6_df1_tag0_off0.jsonl",
    )
)
GROUND_TRUTH_PATH = Path(
    os.environ.get(
        "CARDIO_GRAPH_TABLE22_GROUND_TRUTH_PATH",
        DATA_DIR / "evaluation" / "table_22_manual_full_graph.json",
    )
)
DOCLING_TABLE_62_PATH = Path(
    os.environ.get(
        "CARDIO_GRAPH_TABLE22_DOCLING_62",
        "/prj/doctoral_letters/guide/data/guidelines/docling/pdf_pages/_62/tables/table_000.json",
    )
)
DOCLING_TABLE_63_PATH = Path(
    os.environ.get(
        "CARDIO_GRAPH_TABLE22_DOCLING_63",
        "/prj/doctoral_letters/guide/data/guidelines/docling/pdf_pages/_63/tables/table_000.json",
    )
)
DOCLING_TABLE_PATHS = [DOCLING_TABLE_62_PATH, DOCLING_TABLE_63_PATH]
TABLE_IDS_RAW = os.environ.get("CARDIO_GRAPH_TABLE22_TABLE_IDS", "0")
TABLE_IDS = {int(value.strip()) for value in TABLE_IDS_RAW.split(",") if value.strip()}
SKIP_ROWS_RAW = os.environ.get("CARDIO_GRAPH_TABLE22_SKIP_ROWS", "row_01")
SKIP_ROWS = {value.strip() for value in SKIP_ROWS_RAW.split(",") if value.strip()}
MIN_ROW_MATCH = float(os.environ.get("CARDIO_GRAPH_TABLE22_MIN_ROW_MATCH", "0.2"))
ENTRY_MATCH_THRESHOLD = float(
    os.environ.get("CARDIO_GRAPH_TABLE22_ENTRY_MATCH_THRESHOLD", "0.6")
)
REPORT_MD_PATH = Path(
    os.environ.get(
        "CARDIO_GRAPH_TABLE22_REPORT_MD",
        DOCS_DIR / "table22_rowwise_comparison.md",
    )
)
REPORT_JSON_PATH = Path(
    os.environ.get(
        "CARDIO_GRAPH_TABLE22_REPORT_JSON",
        DOCS_DIR / "table22_rowwise_alignment.json",
    )
)
REPORT_CSV_PATH = Path(
    os.environ.get(
        "CARDIO_GRAPH_TABLE22_REPORT_CSV",
        DOCS_DIR / "table22_rowwise_summary.csv",
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


def _load_ground_truth():
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_docling_rows():
    rows = []
    for path in DOCLING_TABLE_PATHS:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        rows.extend(payload.get("data", []))
    return rows


def _normalize_text(value):
    if value is None:
        return None
    return " ".join(str(value).strip().split()).lower()


def _docling_row_values(row):
    values = []
    for value in row.values():
        if isinstance(value, str):
            normalized = _normalize_text(value)
            if normalized:
                values.append(normalized)
    return values


def _normalize_role(role):
    if role is None:
        return None
    role_text = str(role).strip()
    lowered = role_text.lower()
    if lowered == "clinicalcondition":
        return "Condition"
    if lowered == "clinicalparameter":
        return "ClinicalParameter"
    if lowered == "clinicalaction":
        return "Procedure"
    return role_text


def _normalize_strength(strength):
    if strength is None:
        return None
    value = str(strength).strip()
    if value.lower().startswith("class "):
        value = value.split(" ", 1)[1].strip()
    return value


def _normalize_level(level):
    if level is None:
        return None
    value = str(level).strip()
    if value.lower().startswith("level "):
        value = value.split(" ", 1)[1].strip()
    return value


def _normalize_direction(direction):
    if direction is None:
        return None
    return str(direction).strip().upper()


def _normalize_logic(logic):
    operator = logic.get("operator")
    if operator is None and (logic.get("logic_type") or logic.get("logic_group")):
        operator = "PRESENT"
    return {
        "operator": operator,
        "threshold": logic.get("threshold"),
        "unit": logic.get("unit"),
        "condition_context": _normalize_text(logic.get("condition_context")),
        "logic_type": logic.get("logic_type"),
        "logic_group": logic.get("logic_group"),
        "strength": _normalize_strength(logic.get("strength")),
        "level": _normalize_level(logic.get("level")),
        "direction": _normalize_direction(logic.get("direction")),
    }


def _build_entry(entity, entity_original, role, logic):
    normalized_logic = _normalize_logic(logic or {})
    return {
        "entity": _normalize_text(entity),
        "entity_original": _normalize_text(entity_original),
        "role": _normalize_role(role),
        **normalized_logic,
    }


def _summarize_rules(rules_rows):
    grouped = {}
    for index, row in enumerate(rules_rows):
        chunk_id = row.get("chunk_id") or ""
        row_id = chunk_id.split(":")[-1] if ":" in chunk_id else None
        if not row_id or row_id in SKIP_ROWS:
            continue
        entity = row.get("entity_standardized_candidate") or row.get("entity_original")
        entry = _build_entry(
            entity,
            row.get("entity_original"),
            row.get("role"),
            row.get("logic_structured") or {},
        )
        entry["_source_index"] = index
        grouped.setdefault(row_id, []).append(entry)
    return grouped


def _summarize_ground_truth(truth):
    grouped = {}
    for table in truth.get("tables", []):
        table_id = table.get("table_id")
        if TABLE_IDS and table_id not in TABLE_IDS:
            continue
        for index, row in enumerate(table.get("data", []), start=1):
            row_id = f"row_{index:02d}"
            row_entries = []
            for rule in row.get("rules", []):
                rule_id = rule.get("rule_id")
                for condition in rule.get("conditions", []):
                    entity = condition.get(
                        "entity_standardized_candidate"
                    ) or condition.get("entity_original")
                    if _normalize_text(entity) == "string":
                        continue
                    entry = _build_entry(
                        entity,
                        condition.get("entity_original"),
                        condition.get("role"),
                        condition.get("logic_structured") or {},
                    )
                    entry["side"] = "condition"
                    entry["rule_id"] = rule_id
                    row_entries.append(entry)
                for action in rule.get("actions", []):
                    entity = action.get("entity_standardized_candidate") or action.get(
                        "entity_original"
                    )
                    if _normalize_text(entity) == "string":
                        continue
                    entry = _build_entry(
                        entity,
                        action.get("entity_original"),
                        action.get("role"),
                        action.get("logic_structured") or {},
                    )
                    entry["side"] = "action"
                    entry["rule_id"] = rule_id
                    row_entries.append(entry)
            if row_entries:
                grouped[row_id] = row_entries
    return grouped


def _summarize_ground_truth_grouped(truth):
    grouped = {}
    for table in truth.get("tables", []):
        table_id = table.get("table_id")
        if TABLE_IDS and table_id not in TABLE_IDS:
            continue
        for index, row in enumerate(table.get("data", []), start=1):
            row_id = f"row_{index:02d}"
            rules_payload = []
            for rule in row.get("rules", []):
                rule_id = rule.get("rule_id")
                conditions = []
                actions = []

                for condition in rule.get("conditions", []):
                    entity = condition.get(
                        "entity_standardized_candidate"
                    ) or condition.get("entity_original")
                    if _normalize_text(entity) == "string":
                        continue
                    conditions.append(
                        _build_entry(
                            entity,
                            condition.get("entity_original"),
                            condition.get("role"),
                            condition.get("logic_structured") or {},
                        )
                    )

                for action in rule.get("actions", []):
                    entity = action.get("entity_standardized_candidate") or action.get(
                        "entity_original"
                    )
                    if _normalize_text(entity) == "string":
                        continue
                    actions.append(
                        _build_entry(
                            entity,
                            action.get("entity_original"),
                            action.get("role"),
                            action.get("logic_structured") or {},
                        )
                    )

                if conditions or actions:
                    rules_payload.append(
                        {
                            "rule_id": rule_id,
                            "conditions": conditions,
                            "actions": actions,
                        }
                    )

            if rules_payload:
                grouped[row_id] = rules_payload
    return grouped


def _ordered_rows(grouped):
    return [
        (row_id, entries)
        for row_id, entries in sorted(
            grouped.items(), key=lambda item: int(item[0].split("_")[-1])
        )
    ]


def _tokenize(text):
    if not text:
        return set()
    cleaned = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return {token for token in cleaned.split() if token}


def _entry_match(expected, actual):
    if expected.get("role") != actual.get("role"):
        return False
    expected_tokens = _tokenize(expected.get("entity"))
    actual_tokens = _tokenize(actual.get("entity"))
    if not expected_tokens or not actual_tokens:
        return False
    overlap = expected_tokens.intersection(actual_tokens)
    return (len(overlap) / len(expected_tokens)) >= ENTRY_MATCH_THRESHOLD


def _row_match_score(expected_entries, actual_entries):
    if not expected_entries:
        return 1.0
    matched = 0
    for expected in expected_entries:
        if any(_entry_match(expected, actual) for actual in actual_entries):
            matched += 1
    return matched / len(expected_entries)


def _sorted_entries(entries):
    return sorted(
        entries,
        key=lambda entry: (
            entry.get("entity") or "",
            entry.get("role") or "",
            json.dumps(entry, sort_keys=True),
        ),
    )


def _strip_internal_keys(entries):
    cleaned = []
    for entry in entries:
        cleaned.append(
            {key: value for key, value in entry.items() if not key.startswith("_")}
        )
    return cleaned


def _concept_key(entry):
    return (entry.get("role"), entry.get("entity"))


def _rule_key(entry):
    return (
        entry.get("role"),
        entry.get("entity"),
        entry.get("operator"),
        entry.get("threshold"),
        entry.get("unit"),
        entry.get("condition_context"),
        entry.get("logic_type"),
        entry.get("logic_group"),
        entry.get("strength"),
        entry.get("level"),
        entry.get("direction"),
    )


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
    if operator:
        parts.append(f"op={operator}")
    if threshold is not None:
        parts.append(f"thr={threshold}")
    if unit:
        parts.append(f"unit={unit}")
    if context:
        parts.append(f"ctx={context}")
    if logic_type:
        parts.append(f"logic={logic_type}")
    if logic_group:
        parts.append(f"grp={logic_group}")
    if strength:
        parts.append(f"class={strength}")
    if level:
        parts.append(f"level={level}")
    if direction:
        parts.append(f"dir={direction}")
    return " | ".join(parts)


def _ground_truth_row_text(row):
    keys = [
        "Table Header",
        "Section Header",
        "Sub Header",
        "Recommendations",
        "Recommendation",
        "input",
        "recommendation",
        "Class a",
        "Level b",
    ]
    payload = {}
    for key in keys:
        value = row.get(key)
        if value:
            payload[key] = value
    return payload


def _ground_truth_match_text(row):
    for key in ("Recommendations", "recommendation", "Recommendation"):
        value = row.get(key)
        normalized = _normalize_text(value)
        if normalized:
            return normalized
    return None


def _collect_ground_truth_rows(truth):
    rows = {}
    for table in truth.get("tables", []):
        table_id = table.get("table_id")
        if TABLE_IDS and table_id not in TABLE_IDS:
            continue
        for index, row in enumerate(table.get("data", []), start=1):
            row_id = f"row_{index:02d}"
            rows[row_id] = _ground_truth_row_text(row)
    return rows


def _collect_docling_rows(truth):
    docling_rows = _load_docling_rows()
    docling_values = [set(_docling_row_values(row)) for row in docling_rows]
    result = {}
    cursor = 0

    for table in truth.get("tables", []):
        table_id = table.get("table_id")
        if TABLE_IDS and table_id not in TABLE_IDS:
            continue
        for index, row in enumerate(table.get("data", []), start=1):
            row_id = f"row_{index:02d}"
            match_text = _ground_truth_match_text(row)
            matched_row = None
            if match_text:
                for doc_index in range(cursor, len(docling_rows)):
                    if match_text in docling_values[doc_index]:
                        matched_row = docling_rows[doc_index]
                        cursor = doc_index + 1
                        break
            result[row_id] = matched_row or {}
    return result


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


def _build_mermaid(entries, title):
    def is_condition(entry):
        side = (entry.get("side") or "").strip().lower()
        if side:
            return side == "condition"
        return entry.get("role") in {"Condition", "ClinicalParameter"}

    def is_action(entry):
        side = (entry.get("side") or "").strip().lower()
        if side:
            return side == "action"
        return entry.get("role") in {"Procedure", "Medication"}

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

        if not condition_entries:
            lines.append("    REC")

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


class Table22ConceptRulesTests(unittest.TestCase):
    def setUp(self):
        if not RULES_PATH.is_file():
            self.skipTest(
                "Missing rules file: "
                + str(RULES_PATH)
                + ". Set CARDIO_GRAPH_TABLE22_RULES_PATH."
            )
        if not GROUND_TRUTH_PATH.is_file():
            self.skipTest(
                "Missing ground-truth file: "
                + str(GROUND_TRUTH_PATH)
                + ". Set CARDIO_GRAPH_TABLE22_GROUND_TRUTH_PATH."
            )
        missing_docling = [path for path in DOCLING_TABLE_PATHS if not path.is_file()]
        if missing_docling:
            self.skipTest(
                "Missing docling table(s): "
                + ", ".join(str(path) for path in missing_docling)
                + ". Set CARDIO_GRAPH_TABLE22_DOCLING_62/63."
            )

    def _assert_verbose(self, label, expected, actual, note):
        print("\nCHECK: " + label)
        print("EXPECTED:\n" + json.dumps(expected, indent=2))
        print("ACTUAL:\n" + json.dumps(actual, indent=2))
        print("NOTE:\n" + note)
        self.assertEqual(actual, expected)

    def test_table_22_rules_match_ground_truth(self):
        rules_rows = _load_rules()
        truth = _load_ground_truth()

        truth_rows = _collect_docling_rows(truth)
        expected_rows = _ordered_rows(_summarize_ground_truth(truth))
        expected_rows_grouped = _summarize_ground_truth_grouped(truth)
        actual_rows = _ordered_rows(_summarize_rules(rules_rows))

        if len(actual_rows) < len(expected_rows):
            self.fail(
                "Extracted rows are fewer than expected. "
                + str(len(actual_rows))
                + " < "
                + str(len(expected_rows))
            )

        report_rows = []
        for expected_row_id, expected_entries in expected_rows:
            expected_index = int(expected_row_id.split("_")[-1])
            actual_row_id = f"row_{expected_index + 1:02d}"
            actual_entries_raw = dict(actual_rows).get(actual_row_id, [])
            actual_entries_ordered = _strip_internal_keys(
                sorted(
                    actual_entries_raw, key=lambda entry: entry.get("_source_index", 0)
                )
            )

            expected_sorted = _sorted_entries(expected_entries)
            actual_sorted = _sorted_entries(actual_entries_ordered)

            expected_concepts = {_concept_key(entry) for entry in expected_sorted}
            actual_concepts = {_concept_key(entry) for entry in actual_sorted}
            concept_matches = expected_concepts & actual_concepts
            concept_missing = expected_concepts - actual_concepts
            concept_extra = actual_concepts - expected_concepts

            expected_rules = {_rule_key(entry) for entry in expected_sorted}
            actual_rules = {_rule_key(entry) for entry in actual_sorted}
            rule_matches = expected_rules & actual_rules
            rule_missing = expected_rules - actual_rules
            rule_extra = actual_rules - expected_rules

            score = _row_match_score(expected_entries, actual_entries_ordered)
            report_rows.append(
                {
                    "row_id": expected_row_id,
                    "mapped_actual_row": actual_row_id,
                    "match_score": score,
                    "ground_truth_text": truth_rows.get(expected_row_id, {}),
                    "expected_entries": expected_entries,
                    "expected_entries_display": expected_rows_grouped.get(
                        expected_row_id, expected_entries
                    ),
                    "actual_entries": actual_entries_ordered,
                    "concept_summary": {
                        "expected": len(expected_concepts),
                        "actual": len(actual_concepts),
                        "matches": len(concept_matches),
                        "missing": len(concept_missing),
                        "extra": len(concept_extra),
                    },
                    "rule_summary": {
                        "expected": len(expected_rules),
                        "actual": len(actual_rules),
                        "matches": len(rule_matches),
                        "missing": len(rule_missing),
                        "extra": len(rule_extra),
                    },
                    "concept_missing": sorted(concept_missing),
                    "concept_extra": sorted(concept_extra),
                    "rule_missing": sorted(
                        rule_missing, key=lambda x: json.dumps(x, sort_keys=True)
                    ),
                    "rule_extra": sorted(
                        rule_extra, key=lambda x: json.dumps(x, sort_keys=True)
                    ),
                }
            )

        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_JSON_PATH.write_text(
            json.dumps(
                {
                    "ground_truth": str(GROUND_TRUTH_PATH),
                    "extracted_rules": str(RULES_PATH),
                    "mapping": "truth row_N -> extracted row_{N+1} (skip extracted row_01 header)",
                    "rows": report_rows,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        REPORT_CSV_PATH.write_text(
            "row_id,mapped_actual_row,match_score,expected_concepts,actual_concepts,concept_matches,concept_missing,concept_extra,expected_rules,actual_rules,rule_matches,rule_missing,rule_extra\n",
            encoding="utf-8",
        )
        with REPORT_CSV_PATH.open("a", encoding="utf-8") as f:
            for row in report_rows:
                f.write(
                    f"{row['row_id']},{row['mapped_actual_row']},{row['match_score']:.3f},"
                    f"{row['concept_summary']['expected']},{row['concept_summary']['actual']},"
                    f"{row['concept_summary']['matches']},{row['concept_summary']['missing']},"
                    f"{row['concept_summary']['extra']},{row['rule_summary']['expected']},"
                    f"{row['rule_summary']['actual']},{row['rule_summary']['matches']},"
                    f"{row['rule_summary']['missing']},{row['rule_summary']['extra']}\n"
                )

        with REPORT_MD_PATH.open("w", encoding="utf-8") as f:
            f.write("# Table 22 row-wise comparison (concepts and rules)\n\n")
            f.write(f"Ground truth: {GROUND_TRUTH_PATH}\n")
            f.write(f"Extracted rules: {RULES_PATH}\n")
            f.write(
                "Mapping: truth row_N -> extracted row_{N+1} (skip extracted row_01 header)\n\n"
            )
            f.write(f"Summary CSV: {REPORT_CSV_PATH.relative_to(PROJECT_ROOT)}\n")
            f.write(f"Aligned JSON: {REPORT_JSON_PATH.relative_to(PROJECT_ROOT)}\n\n")
            f.write("Per-row reports:\n\n")
            for row in report_rows:
                row_file = ROWS_DIR / f"{row['row_id']}.md"
                f.write(
                    f"- {row['row_id']} -> {row_file.relative_to(PROJECT_ROOT)} "
                    f"(match_score={row['match_score']:.3f})\n"
                )

        ROWS_DIR.mkdir(parents=True, exist_ok=True)
        for row in report_rows:
            row_file = ROWS_DIR / f"{row['row_id']}.md"
            with row_file.open("w", encoding="utf-8") as f:
                f.write(f"# {row['row_id']} (mapped to {row['mapped_actual_row']})\n\n")
                f.write("Original table row text (ground truth):\n\n")
                f.write("```json\n")
                f.write(json.dumps(row["ground_truth_text"], indent=2))
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
                f.write(json.dumps(row["actual_entries"], indent=2))
                f.write("\n</pre></td>\n")
                f.write("  </tr>\n")
                f.write("</table>\n\n")

                f.write("Mermaid (Human Annotation):\n\n")
                f.write("```mermaid\n")
                f.write(_build_mermaid(row["expected_entries"], "Human"))
                f.write("\n```\n\n")

                f.write("Mermaid (LLM Generated):\n\n")
                f.write("```mermaid\n")
                f.write(_build_mermaid(row["actual_entries"], "LLM"))
                f.write("\n```\n\n")

                f.write("Concepts:\n")
                f.write(f"- expected: {row['concept_summary']['expected']}\n")
                f.write(f"- actual: {row['concept_summary']['actual']}\n")
                f.write(f"- matches: {row['concept_summary']['matches']}\n")
                f.write(f"- missing: {row['concept_summary']['missing']}\n")
                f.write(f"- extra: {row['concept_summary']['extra']}\n\n")

                if row["concept_missing"]:
                    f.write("Missing concepts:\n")
                    for item in sorted(row["concept_missing"]):
                        f.write("- " + _format_concept(item) + "\n")
                    f.write("\n")

                if row["concept_extra"]:
                    f.write("Extra concepts:\n")
                    for item in sorted(row["concept_extra"]):
                        f.write("- " + _format_concept(item) + "\n")
                    f.write("\n")

                f.write("Rules (concept + logic fields):\n")
                f.write(f"- expected: {row['rule_summary']['expected']}\n")
                f.write(f"- actual: {row['rule_summary']['actual']}\n")
                f.write(f"- matches: {row['rule_summary']['matches']}\n")
                f.write(f"- missing: {row['rule_summary']['missing']}\n")
                f.write(f"- extra: {row['rule_summary']['extra']}\n\n")

                if row["rule_missing"]:
                    f.write("Missing rules:\n")
                    for item in sorted(
                        row["rule_missing"], key=lambda x: json.dumps(x, sort_keys=True)
                    ):
                        f.write("- " + _format_rule(item) + "\n")
                    f.write("\n")

                if row["rule_extra"]:
                    f.write("Extra rules:\n")
                    for item in sorted(
                        row["rule_extra"], key=lambda x: json.dumps(x, sort_keys=True)
                    ):
                        f.write("- " + _format_rule(item) + "\n")
                    f.write("\n")

        self.assertTrue(REPORT_MD_PATH.is_file(), "Markdown report was not written.")
        self.assertTrue(REPORT_JSON_PATH.is_file(), "JSON report was not written.")
        self.assertTrue(REPORT_CSV_PATH.is_file(), "CSV report was not written.")


if __name__ == "__main__":
    unittest.main()

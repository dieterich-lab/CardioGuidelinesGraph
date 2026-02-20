import json
import os
import re
import unittest
from pathlib import Path

from cardio_graph_core.extraction.guideline_graph_builder import GuidelineGraphBuilder

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
        "/prj/doctoral_letters/guide/data/graph/extracted_rules_docling_table_000_whole_grid_score0.6_df1_tag0_off0.jsonl",
    )
)
GROUND_TRUTH_PATH = Path(
    os.environ.get(
        "CARDIO_GRAPH_TABLE22_GROUND_TRUTH_PATH",
        "/prj/doctoral_letters/guide/data/evaluation/table_22_manual_snomed.json",
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
ENTRY_MATCH_THRESHOLD = float(
    os.environ.get("CARDIO_GRAPH_TABLE22_ENTRY_MATCH_THRESHOLD", "0.6")
)
MIN_ROW_MATCH = float(os.environ.get("CARDIO_GRAPH_TABLE22_MIN_ROW_MATCH", "0.2"))


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


def _normalize_text(value):
    if value is None:
        return None
    return " ".join(str(value).strip().split()).lower()


def _normalize_role(role):
    if role is None:
        return None
    return str(role).strip()


def _normalize_strength(strength):
    if strength is None:
        return None
    return str(strength).strip()


def _normalize_level(level):
    if level is None:
        return None
    return str(level).strip()


def _normalize_direction(direction):
    if direction is None:
        return None
    return str(direction).strip()


def _normalize_logic(logic):
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


def _build_entry(entity, entity_original, role, logic, side):
    normalized_logic = _normalize_logic(logic or {})
    return {
        "entity": _normalize_text(entity),
        "entity_original": _normalize_text(entity_original),
        "role": _normalize_role(role),
        "side": side,
        **normalized_logic,
    }


def _get_ground_truth_for_row(truth, row_id):
    for table in truth.get("tables", []):
        table_id = table.get("table_id")
        if TABLE_IDS and table_id not in TABLE_IDS:
            continue
        for index, row in enumerate(table.get("data", []), start=1):
            current_row_id = f"row_{index:02d}"
            if current_row_id == row_id:
                entries = []
                for rule in row.get("rules", []):
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
                            "condition",
                        )
                        entries.append(entry)
                    for action in rule.get("actions", []):
                        entity = action.get(
                            "entity_standardized_candidate"
                        ) or action.get("entity_original")
                        if _normalize_text(entity) == "string":
                            continue
                        entry = _build_entry(
                            entity,
                            action.get("entity_original"),
                            action.get("role"),
                            action.get("logic_structured") or {},
                            "action",
                        )
                        entries.append(entry)
                return entries, row
    return [], None


def _get_extracted_for_row(rules_rows, row_id):
    entries = []
    for row in rules_rows:
        chunk_id = row.get("chunk_id") or ""
        current_row_id = chunk_id.split(":")[-1] if ":" in chunk_id else None
        if current_row_id == row_id:
            entity = row.get("entity_standardized_candidate") or row.get(
                "entity_original"
            )
            logic_structured = row.get("logic_structured") or {}
            side = "condition" if row.get("logic") == "condition" else "action"
            entry = _build_entry(
                entity,
                row.get("entity_original"),
                row.get("role"),
                logic_structured,
                side,
            )
            entries.append(entry)
    return entries


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


def _build_mermaid(expected_entries, actual_entries):
    lines = ["graph TD"]
    node_id = 0
    entity_to_id = {}
    conditions = [
        e for e in expected_entries + actual_entries if e.get("side") == "condition"
    ]
    actions = [
        e for e in expected_entries + actual_entries if e.get("side") == "action"
    ]

    condition_nodes = []
    for cond in conditions:
        entity = cond.get("entity")
        if entity not in entity_to_id:
            entity_to_id[entity] = f"C{node_id}"
            node_id += 1
        condition_nodes.append(entity_to_id[entity])
        lines.append(f'{entity_to_id[entity]}["{entity}"]')

    action_nodes = []
    for act in actions:
        entity = act.get("entity")
        if entity not in entity_to_id:
            entity_to_id[entity] = f"A{node_id}"
            node_id += 1
        action_nodes.append(entity_to_id[entity])
        lines.append(f'{entity_to_id[entity]}["{entity}"]')

    for cond_node in condition_nodes:
        for act_node in action_nodes:
            lines.append(f"{cond_node} --> {act_node}")

    return "\n".join(lines)


def _summarize_ground_truth_grouped(truth, row_id):
    entries, row = _get_ground_truth_for_row(truth, row_id)
    if not entries:
        return {}
    grouped = {"rules": [{"conditions": [], "actions": []}]}
    for entry in entries:
        if entry.get("side") == "condition":
            grouped["rules"][0]["conditions"].append(entry)
        elif entry.get("side") == "action":
            grouped["rules"][0]["actions"].append(entry)
    return grouped


class TestTable22Row(unittest.TestCase):
    def setUp(self):
        self.ground_truth = _load_ground_truth()
        self.rules_rows = _load_rules()
        self.builder = GuidelineGraphBuilder(model="Qwen30b", node="g5", port=11435)

    def _test_row(self, row_id):
        expected_entries, row_data = _get_ground_truth_for_row(
            self.ground_truth, row_id
        )
        # Live extraction
        if row_data:
            text = " | ".join(
                str(v).strip()
                for v in row_data.values()
                if isinstance(v, str) and v.strip()
            )
            extracted_concepts = self.builder.extract_concepts(
                text, source_type="table_row", guideline_title="ESC Guidelines"
            )
            actual_entries = []
            for concept in extracted_concepts:
                side = (
                    "condition"
                    if getattr(concept, "logic", None) == "condition"
                    else "action"
                )
                entry = _build_entry(
                    getattr(concept, "entity_standardized_candidate", None)
                    or getattr(concept, "entity_original", ""),
                    getattr(concept, "entity_original", ""),
                    getattr(concept, "role", None),
                    getattr(concept, "logic_structured", None) or {},
                    side,
                )
                actual_entries.append(entry)
        else:
            actual_entries = []

        match_score = _row_match_score(expected_entries, actual_entries)
        self.assertGreaterEqual(
            match_score,
            MIN_ROW_MATCH,
            f"Row {row_id} match score {match_score:.2f} is too low. "
            f"Expected {len(expected_entries)} entries, got {len(actual_entries)}.",
        )

        # Generate reports
        ROWS_DIR.mkdir(parents=True, exist_ok=True)
        row_md_path = ROWS_DIR / f"{row_id}.md"

        expected_grouped = _summarize_ground_truth_grouped(self.ground_truth, row_id)
        actual_grouped = {"rules": [{"conditions": [], "actions": []}]}
        for entry in actual_entries:
            if entry.get("side") == "condition":
                actual_grouped["rules"][0]["conditions"].append(entry)
            elif entry.get("side") == "action":
                actual_grouped["rules"][0]["actions"].append(entry)

        mermaid = _build_mermaid(expected_entries, actual_entries)

        with open(row_md_path, "w", encoding="utf-8") as f:
            f.write(f"# {row_id}\n\n")
            f.write("## Ground Truth\n\n")
            f.write("```json\n")
            json.dump(expected_grouped, f, indent=2)
            f.write("\n```\n\n")
            f.write("## Extracted\n\n")
            f.write("```json\n")
            json.dump(actual_grouped, f, indent=2)
            f.write("\n```\n\n")
            f.write("## Mermaid\n\n")
            f.write("```mermaid\n")
            f.write(mermaid)
            f.write("\n```\n\n")
            f.write(f"Match Score: {match_score:.2f}\n")

    def test_row_01(self):
        self._test_row("row_01")


if __name__ == "__main__":
    unittest.main()

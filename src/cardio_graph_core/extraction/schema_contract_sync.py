from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml


def _unique_preserve_order(values: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _node_attr(schema: Dict, label: str, attr_name: str) -> Dict:
    for node in schema.get("nodes") or []:
        if node.get("label") != label:
            continue
        for attr in node.get("attributes") or []:
            if attr.get("name") == attr_name:
                return attr
    return {}


def allowed_values(schema: Dict, label: str, attr_name: str) -> List[str]:
    attr = _node_attr(schema, label, attr_name)
    raw_allowed = attr.get("allowed") or []
    values = [str(v).strip() for v in raw_allowed if v is not None and str(v).strip()]
    return _unique_preserve_order(values)


def contract_vocabulary_from_schema(schema: Dict) -> Dict[str, List[str]]:
    return {
        "operator": allowed_values(schema, "DecisionNode", "operator"),
        "logic_type": allowed_values(schema, "DecisionNode", "logic_type"),
        "direction": allowed_values(schema, "RecommendationNode", "direction"),
        "strength": allowed_values(schema, "RecommendationNode", "strength"),
        "level": allowed_values(schema, "RecommendationNode", "level"),
    }


def baml_snippets_from_schema(schema: Dict) -> Dict[str, str]:
    vocab = contract_vocabulary_from_schema(schema)
    operator_csv = ", ".join(vocab["operator"])
    direction_csv = ", ".join(vocab["direction"])
    return {
        "operator_values_csv": operator_csv,
        "direction_values_csv": direction_csv,
        "operator_prompt": f"Use operator values from: {operator_csv}.",
        "direction_use_prompt": f"Use one of {direction_csv}.",
        "direction_prompt": f"Direction must be one of {direction_csv}.",
    }


def baml_managed_block_values_from_schema(schema: Dict) -> Dict[str, str]:
    snippets = baml_snippets_from_schema(schema)
    type_block = render_baml_type_contract_block(schema)
    return {
        "SCHEMA_BAML_TYPE_CONTRACT": type_block,
        "SCHEMA_OPERATOR_PROMPT": snippets["operator_prompt"],
        "SCHEMA_OPERATOR_PROMPT_RULES": snippets["operator_prompt"],
        "SCHEMA_DIRECTION_USE_PROMPT": snippets["direction_use_prompt"],
        "SCHEMA_DIRECTION_PROMPT_RULES": snippets["direction_prompt"],
    }


def load_schema(schema_path: Path) -> Dict:
    return yaml.safe_load(schema_path.read_text(encoding="utf-8")) or {}


def resolve_table22_v13_path(project_root: Path) -> Optional[Path]:
    candidates = [
        Path("/prj/doctoral_letters/guide/data/evaluation/table_22_manual_1.3.json"),
        project_root / "data" / "evaluation" / "table_22_manual_1.3.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _indent_block(content: str, indent: str) -> str:
    return "\n".join(
        f"{indent}{line}" if line else indent for line in content.splitlines()
    )


def _replace_managed_block(text: str, block_name: str, content: str) -> str:
    pattern = re.compile(
        rf"(?P<indent>[ \t]*)(?P<prefix>//[ \t]*)?\[BEGIN {re.escape(block_name)}\]\n"
        rf"(?P<body>.*?)"
        rf"(?P=indent)(?P=prefix)?\[END {re.escape(block_name)}\]",
        flags=re.DOTALL,
    )

    def _repl(match: re.Match) -> str:
        indent = match.group("indent")
        prefix = match.group("prefix") or ""
        indented_content = _indent_block(content, indent)
        return (
            f"{indent}{prefix}[BEGIN {block_name}]\n"
            f"{indented_content}\n"
            f"{indent}{prefix}[END {block_name}]"
        )

    updated, count = pattern.subn(_repl, text)
    if count == 0:
        raise ValueError(
            f"Managed block {block_name} not found in BAML file. "
            "Expected [BEGIN ...]/[END ...] markers."
        )
    return updated


def extract_baml_managed_block_values(baml_text: str) -> Dict[str, str]:
    block_names = (
        "SCHEMA_BAML_TYPE_CONTRACT",
        "SCHEMA_OPERATOR_PROMPT",
        "SCHEMA_OPERATOR_PROMPT_RULES",
        "SCHEMA_DIRECTION_USE_PROMPT",
        "SCHEMA_DIRECTION_PROMPT_RULES",
    )
    values: Dict[str, str] = {}
    for block_name in block_names:
        pattern = re.compile(
            rf"^[ \t]*(?://[ \t]*)?\[BEGIN {re.escape(block_name)}\]\n"
            rf"(?P<body>.*?)"
            rf"^[ \t]*(?://[ \t]*)?\[END {re.escape(block_name)}\][ \t]*$",
            flags=re.DOTALL | re.MULTILINE,
        )
        match = pattern.search(baml_text)
        if not match:
            raise ValueError(f"Managed block {block_name} not found in BAML content.")
        body = match.group("body")
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        values[block_name] = " ".join(lines).strip()
    return values


def sync_extract_concepts_baml_text(baml_text: str, schema: Dict) -> str:
    managed_values = baml_managed_block_values_from_schema(schema)
    synced = baml_text
    for block_name, value in managed_values.items():
        synced = _replace_managed_block(synced, block_name, value)
    return synced


def sync_extract_concepts_baml_file(schema_path: Path, baml_path: Path) -> bool:
    schema = load_schema(schema_path)
    current = baml_path.read_text(encoding="utf-8")
    updated = sync_extract_concepts_baml_text(current, schema)
    if updated == current:
        return False
    baml_path.write_text(updated, encoding="utf-8")
    return True


def extract_baml_class_field_names(baml_text: str, class_name: str) -> List[str]:
    class_pattern = re.compile(
        rf"class\s+{re.escape(class_name)}\s*\{{(?P<body>.*?)\n\}}",
        flags=re.DOTALL,
    )
    match = class_pattern.search(baml_text)
    if not match:
        raise ValueError(f"Class {class_name} not found in BAML content.")
    body = match.group("body")

    field_names: List[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        # BAML field lines look like: field_name type ...
        token = stripped.split()[0]
        if token and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", token):
            field_names.append(token)
    return field_names


def expected_baml_type_contract_from_schema(schema: Dict) -> Dict[str, List[str]]:
    vocab = contract_vocabulary_from_schema(schema)
    logic_structured_fields = [
        "strength",
        "level",
        "direction",
        "operator",
        "threshold",
        "unit",
        "context",
    ]

    # Keep logic_type/logic_group in rule-side structures, matching current design.
    rule_logic_fields = [
        "operator",
        "threshold",
        "unit",
        "context",
        "logic_type",
        "logic_group",
    ]
    rule_recommendation_fields = ["strength", "level", "direction"]

    # Ensure schema still exposes the same core vocab used by BAML types.
    _ = vocab["operator"]
    _ = vocab["direction"]
    _ = vocab["logic_type"]
    _ = vocab["strength"]
    _ = vocab["level"]

    return {
        "LogicStructured": logic_structured_fields,
        "RuleLogicV2": rule_logic_fields,
        "RuleRecommendationV2": rule_recommendation_fields,
        "ExtractedConcept": [
            "entity_original",
            "entity_standardized_candidate",
            "role",
            "logic",
            "logic_structured",
        ],
        "ExtractConceptsResult": ["concepts"],
        "RuleConditionV2": [
            "entity_original",
            "entity_standardized_candidate",
            "role",
            "logic",
        ],
        "RuleActionV2": [
            "entity_original",
            "entity_standardized_candidate",
            "role",
            "context",
            "recommendation",
        ],
        "ExtractedRuleV2": ["conditions", "actions"],
        "ExtractRulesResultV2": ["rules"],
    }


def render_baml_type_contract_block(schema: Dict) -> str:
    vocab = contract_vocabulary_from_schema(schema)
    operator_csv = ", ".join(vocab["operator"])
    direction_csv = ", ".join(vocab["direction"])

    # Keep field layout in one place, schema-coupled through contract + vocab text.
    return (
        "// Auto-generated from guideline_graph_schema.yaml via schema_contract_sync.py\n"
        "// Do not edit manually.\n"
        "class LogicStructured {\n"
        "  // Recommendation details\n"
        '  strength string? @description("Recommendation strength (e.g., Strong, Weak, Class I)")\n'
        '  level string? @description("Level of evidence (e.g., A, B, C)")\n'
        f'  direction string @description("Recommendation direction ({direction_csv})")\n'
        "\n"
        "  // Decision details (fuer Bedingungen/Checks)\n"
        f'  operator string? @description("Comparison/presence operator (e.g., {operator_csv})")\n'
        '  threshold string? @description("Numeric threshold value (e.g., 40, 120/80)")\n'
        '  unit string? @description("Unit of measurement (e.g., %, mmHg, mg)")\n'
        "\n"
        "  // Temporal/Conditional context\n"
        "  context string? @description(\"Additional context (e.g., 'history of', 'acute', 'chronic')\")\n"
        "}\n"
        "\n"
        "class ExtractedConcept {\n"
        "  entity_original string\n"
        "  entity_standardized_candidate string\n"
        "  role string\n"
        "  logic string\n"
        "  logic_structured LogicStructured\n"
        "}\n"
        "\n"
        "class ExtractConceptsResult {\n"
        "  concepts ExtractedConcept[]\n"
        "}\n"
        "\n"
        "// Draft v2: explicit input/output separation to remove ambiguity.\n"
        "class RuleLogicV2 {\n"
        f'  operator string? @description("Operator for input conditions (e.g., {operator_csv})")\n'
        '  threshold string? @description("Numeric threshold value (e.g., 40, 120/80)")\n'
        '  unit string? @description("Unit of measurement (e.g., %, mmHg, mg)")\n'
        "  context string? @description(\"Additional context (e.g., 'history of', 'acute', 'chronic')\")\n"
        '  logic_type string? @description("AND, OR, or SINGLE within a group")\n'
        '  logic_group string? @description("Group name for inputs that are evaluated together (e.g., and_1, or_1)")\n'
        "}\n"
        "\n"
        "class RuleConditionV2 {\n"
        "  entity_original string\n"
        "  entity_standardized_candidate string\n"
        '  role string @description("ClinicalCondition, ClinicalParameter, Procedure, Qualifier Value")\n'
        "  logic RuleLogicV2\n"
        "}\n"
        "\n"
        "class RuleRecommendationV2 {\n"
        '  strength string? @description("Recommendation strength (e.g., Class I, Class IIa)")\n'
        '  level string? @description("Level of evidence (e.g., A, B, C)")\n'
        f'  direction string @description("Recommendation direction ({direction_csv})")\n'
        "}\n"
        "\n"
        "class RuleActionV2 {\n"
        "  entity_original string\n"
        "  entity_standardized_candidate string\n"
        '  role string @description("Medication or Procedure")\n'
        '  context string? @description("Short action context span (e.g., indication, temporal clause, qualifier)")\n'
        "  recommendation RuleRecommendationV2\n"
        "}\n"
        "\n"
        "class ExtractedRuleV2 {\n"
        "  conditions RuleConditionV2[]\n"
        "  actions RuleActionV2[]\n"
        "}\n"
        "\n"
        "class ExtractRulesResultV2 {\n"
        "  rules ExtractedRuleV2[]\n"
        "}"
    )

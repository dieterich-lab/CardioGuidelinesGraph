from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Metrics:
    schema_valid_rate: float
    rule_exact_match: float
    operator_accuracy: float
    logic_group_accuracy: float
    concept_precision: float
    concept_recall: float
    concept_f1: float
    grounding_hit_rate: float

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class ErrorItem:
    error_class: str
    severity: str
    expected: Optional[str] = None
    actual: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        payload = {
            "class": self.error_class,
            "severity": self.severity,
            "expected": self.expected,
            "actual": self.actual,
        }
        return payload


@dataclass
class RowErrors:
    row_id: str
    errors: List[ErrorItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row_id": self.row_id,
            "errors": [error.to_dict() for error in self.errors],
        }


@dataclass
class ScoreReport:
    run_id: str
    split: str
    prompt_version: str
    metrics: Metrics
    rows: List[RowErrors] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "split": self.split,
            "prompt_version": self.prompt_version,
            "metrics": self.metrics.to_dict(),
            "rows": [row.to_dict() for row in self.rows],
        }


@dataclass
class ErrorClassSummary:
    error_class: str
    count: int
    confidence: float
    root_cause_hypothesis: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class": self.error_class,
            "count": self.count,
            "confidence": self.confidence,
            "root_cause_hypothesis": self.root_cause_hypothesis,
        }


@dataclass
class ErrorAnalysis:
    run_id: str
    top_classes: List[ErrorClassSummary]
    selected_targets: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "top_classes": [top_class.to_dict() for top_class in self.top_classes],
            "selected_targets": self.selected_targets,
        }


@dataclass
class PromptEdit:
    zone: str
    change_type: str
    old: str
    new: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class PromptPatch:
    base_prompt_version: str
    candidate_prompt_version: str
    target_classes: List[str]
    edits: List[PromptEdit]
    max_edit_lines: int
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_prompt_version": self.base_prompt_version,
            "candidate_prompt_version": self.candidate_prompt_version,
            "target_classes": self.target_classes,
            "edits": [edit.to_dict() for edit in self.edits],
            "max_edit_lines": self.max_edit_lines,
            "rationale": self.rationale,
        }


@dataclass
class GateDecision:
    accepted: bool
    reasons: List[str]
    deltas: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SplitManifest:
    split_version: str
    table_id: int
    dev_rows: List[str]
    locked_test_rows: List[str]

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "SplitManifest":
        return cls(
            split_version=str(payload.get("split_version", "unknown")),
            table_id=int(payload.get("table_id", 0)),
            dev_rows=list(payload.get("dev_rows", [])),
            locked_test_rows=list(payload.get("locked_test_rows", [])),
        )

from __future__ import annotations

import json
import logging
import statistics
import sys
import time
import unittest
from pathlib import Path


def _summarize_alignment(alignment_path: Path) -> str:
    if not alignment_path.is_file():
        return "rows=0 mean_match=0.000 low_rows=0"

    payload = json.loads(alignment_path.read_text(encoding="utf-8"))
    rows = payload.get("rows", []) or []
    if not rows:
        return "rows=0 mean_match=0.000 low_rows=0"

    scores = [float(r.get("match_score", 0.0) or 0.0) for r in rows]
    mean_score = statistics.fmean(scores)
    low_rows = sum(1 for s in scores if s < 0.2)
    return f"rows={len(rows)} mean_match={mean_score:.3f} low_rows={low_rows}"


def main() -> int:
    # Keep eval logs compact in SLURM output; full details remain in artifacts.
    logging.getLogger("GuidelineGraphBuilder").setLevel(logging.WARNING)

    from tests.test_table_22_concept_rules import (
        REPORT_CSV_PATH,
        REPORT_JSON_PATH,
        REPORT_MD_PATH,
        Table22ConceptRulesTests,
    )

    case = Table22ConceptRulesTests(methodName="test_table_22_rules_match_ground_truth")
    start = time.time()

    print("[table22-dev-eval] start")
    try:
        case.setUp()
        case.test_table_22_rules_match_ground_truth()
    except unittest.SkipTest as exc:
        print(f"[table22-dev-eval] skipped reason={exc}")
        return 2
    except Exception as exc:
        print(f"[table22-dev-eval] failed error={exc}")
        return 1

    elapsed = time.time() - start
    summary = _summarize_alignment(REPORT_JSON_PATH)
    print(f"[table22-dev-eval] done elapsed_seconds={elapsed:.1f} {summary}")
    print(
        "[table22-dev-eval] artifacts "
        f"md={REPORT_MD_PATH} json={REPORT_JSON_PATH} csv={REPORT_CSV_PATH}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import json
import logging
import statistics
import sys
import time
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

    from cardio_graph_core.evaluation.table22_rule_alignment_eval import (
        REPORT_CSV_PATH,
        REPORT_JSON_PATH,
        REPORT_MD_PATH,
        run_table22_rule_alignment_eval,
    )

    start = time.time()

    print("[table22-dev-eval] start")
    try:
        run_table22_rule_alignment_eval()
    except Exception as exc:
        # SkipTest can be raised by the evaluation module when inputs are unavailable.
        if exc.__class__.__name__ == "SkipTest":
            print(f"[table22-dev-eval] skipped reason={exc}")
            return 2
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

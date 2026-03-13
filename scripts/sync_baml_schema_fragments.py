#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from cardio_graph_core.extraction.schema_contract_sync import (
    sync_extract_concepts_baml_file,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    PROJECT_ROOT / "config" / "cardio_graph_core" / "guideline_graph_schema.yaml"
)
BAML_PATH = (
    PROJECT_ROOT
    / "src"
    / "cardio_graph_core"
    / "extraction"
    / "baml_src"
    / "extract_concepts.baml"
)


def main() -> int:
    changed = sync_extract_concepts_baml_file(SCHEMA_PATH, BAML_PATH)
    if changed:
        print(f"Updated schema-bound BAML fragments in {BAML_PATH}")
    else:
        print("No schema-bound BAML fragment changes needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

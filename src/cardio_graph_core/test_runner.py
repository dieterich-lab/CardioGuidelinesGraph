import sys
from typing import List

import pytest


def row10() -> int:
    args: List[str] = [
        "-q",
        "tests/test_row_10_structure_extraction.py",
        "tests/test_row_10_structure_rules.py",
        "tests/test_row_10_graph.py",
        "tests/test_row_10_grounding.py",
    ]
    return pytest.main(args)


if __name__ == "__main__":
    sys.exit(row10())

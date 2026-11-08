"""Verify a synthetic run against a known, hand-authored nine-move oracle.

Unlike cross-engine parity, this fails if BOTH engines agree on an incorrect result.
The input sequence is defined in python/tools/make_demo.py (owned demo only).
"""
import csv
import json
from pathlib import Path
import sys

EXPECTED = [
    ("Black", "E8"), ("White", "E9"), ("Black", "F8"),
    ("White", "F9"), ("Black", "G8"), ("White", "G9"),
    ("Black", "H8"), ("White", "H9"), ("Black", "I8"),
]


def check(folder: Path) -> None:
    with (folder / "moves.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    actual = [(row["Color"], row["Position"]) for row in rows]
    if actual != EXPECTED:
        raise AssertionError(f"SYNTHETIC_ORACLE_FAIL: expected {EXPECTED}, got {actual}")
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8-sig"))
    if summary.get("moves") != 9 or summary.get("winner") != "Black":
        raise AssertionError(f"SYNTHETIC_ORACLE_FAIL: expected nine moves and Black winner, got {summary.get('moves')}, {summary.get('winner')}")
    if summary.get("canceled", False):
        raise AssertionError("SYNTHETIC_ORACLE_FAIL: run unexpectedly canceled")
    print(f"SYNTHETIC_ORACLE_PASS: 9/9 moves, Black winner, engine={summary.get('engine','unknown')}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python verify_synthetic_expected.py <result-folder>")
    check(Path(sys.argv[1]))

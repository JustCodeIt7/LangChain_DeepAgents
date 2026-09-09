"""
Diff line counter for the DeepCoder series
==========================================
Counts ADDED code lines between consecutive part folders so every part stays
under the series' 150-line budget.

Counted: the app itself (.py, .tcss, .toml, .json).
Not counted: READMEs, caches, and test_*.py -- tests are verification
infrastructure for the repo, not code the video walks through.

Run:  python _tools/diff_lines.py
"""

import difflib
import sys
from pathlib import Path

SERIES_DIR = Path(__file__).resolve().parent.parent
BUDGET = 150
CODE_SUFFIXES = {".py", ".tcss", ".toml", ".json"}
SKIP_DIRS = {"__pycache__", "workspace", ".deepcoder", "_tools", ".pytest_cache"}


def code_files(part: Path) -> dict[str, list[str]]:
    """Map relative path -> lines, for every code file in a part folder."""
    files = {}
    for path in sorted(part.rglob("*")):
        if not path.is_file() or path.suffix not in CODE_SUFFIXES:
            continue
        if path.name.startswith("test_"):
            continue
        if any(part_name in SKIP_DIRS for part_name in path.relative_to(part).parts):
            continue
        files[str(path.relative_to(part))] = path.read_text().splitlines()
    return files


def added_lines(prev: Path | None, curr: Path) -> int:
    """Count lines added in `curr` relative to `prev` (all lines if prev is None)."""
    curr_files = code_files(curr)
    if prev is None:
        return sum(len(lines) for lines in curr_files.values())

    prev_files = code_files(prev)
    total = 0
    for name, lines in curr_files.items():
        old = prev_files.get(name, [])
        diff = difflib.unified_diff(old, lines, n=0, lineterm="")
        total += sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    return total


def main() -> int:
    parts = sorted(
        p for p in SERIES_DIR.iterdir() if p.is_dir() and p.name[:2].isdigit()
    )
    if not parts:
        print("No part folders found.")
        return 1

    over_budget = []
    print(f"{'part':<24}{'added':>7}{'total':>8}  status")
    print("-" * 52)
    for index, part in enumerate(parts):
        prev = parts[index - 1] if index else None
        added = added_lines(prev, part)
        total = sum(len(lines) for lines in code_files(part).values())
        ok = added <= BUDGET
        if not ok:
            over_budget.append(part.name)
        print(f"{part.name:<24}{added:>7}{total:>8}  {'ok' if ok else 'OVER BUDGET'}")

    if over_budget:
        names = ", ".join(over_budget)
        print(f"\n{len(over_budget)} part(s) over the {BUDGET}-line budget: {names}")
        return 1
    print(f"\nAll {len(parts)} parts within the {BUDGET}-line budget.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""milestone.py — XP-free milestone leveling marker. Writes the fork's
`⚠ LEVEL UP PENDING (Level N)` marker onto a character sheet's **XP:** line from a
target level, with no XP threshold. The /dm:dnd level up procedure then applies it.

Do NOT confuse with the fork's unrelated display `milestone_counter`."""
from __future__ import annotations

import pathlib
import re

# Matches the XP line, capturing the numbers, dropping any prior pending marker.
_XP_LINE = re.compile(
    r"(\*\*XP:\*\*\s*\d+\s*/\s*\d+)(?:\s*⚠ LEVEL UP PENDING \(Level \d+\))?"
)


def set_pending_level(sheet_text: str, target_level: int) -> str:
    if not _XP_LINE.search(sheet_text):
        raise ValueError("no **XP:** line found in character sheet")
    marker = f" ⚠ LEVEL UP PENDING (Level {target_level})"
    return _XP_LINE.sub(lambda m: m.group(1) + marker, sheet_text, count=1)


def apply_to_file(path: pathlib.Path, target_level: int) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(set_pending_level(text, target_level), encoding="utf-8")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Mark a milestone level-up as pending.")
    p.add_argument("--sheet", required=True, help="path to the character sheet .md")
    p.add_argument("--level", type=int, required=True, help="target level")
    args = p.parse_args()
    apply_to_file(pathlib.Path(args.sheet), args.level)
    print(f"Marked pending level-up to Level {args.level} on {args.sheet}")

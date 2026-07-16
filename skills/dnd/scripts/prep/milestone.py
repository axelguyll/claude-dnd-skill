"""milestone.py — XP-free milestone leveling marker. Writes the fork's
`⚠ LEVEL UP PENDING (Level N)` marker onto a character sheet from a target level,
with no XP threshold. The /dm:dnd level up procedure then applies it.

Anchor: a numeric **XP:** line when the sheet has one (legacy sheets), else the
**Level:** line — milestone-fork sheets legitimately carry no XP numbers, and the
template ships the XP field blank (2026-07-16 re-probe finding).

Do NOT confuse with the fork's unrelated display `milestone_counter`."""
from __future__ import annotations

import pathlib
import re

# Each pattern captures its anchor line, dropping any prior pending marker.
_XP_LINE = re.compile(
    r"(\*\*XP:\*\*\s*\d+\s*/\s*\d+)(?:\s*⚠ LEVEL UP PENDING \(Level \d+\))?"
)
_LEVEL_LINE = re.compile(
    r"(\*\*Level:\*\*\s*\d+)(?:\s*⚠ LEVEL UP PENDING \(Level \d+\))?"
)


def _anchor(sheet_text: str) -> re.Pattern | None:
    if _XP_LINE.search(sheet_text):
        return _XP_LINE
    if _LEVEL_LINE.search(sheet_text):
        return _LEVEL_LINE
    return None


def set_pending_level(sheet_text: str, target_level: int) -> str:
    pattern = _anchor(sheet_text)
    if pattern is None:
        raise ValueError("no numeric **XP:** or **Level:** line found in character sheet")
    marker = f" ⚠ LEVEL UP PENDING (Level {target_level})"
    return pattern.sub(lambda m: m.group(1) + marker, sheet_text, count=1)


def clear_pending(sheet_text: str) -> str:
    """Remove a `⚠ LEVEL UP PENDING (Level N)` marker from whichever anchor line
    carries it, leaving the line itself intact. No-op if there is no marker."""
    text = _XP_LINE.sub(lambda m: m.group(1), sheet_text, count=1)
    return _LEVEL_LINE.sub(lambda m: m.group(1), text, count=1)


def apply_to_file(path: pathlib.Path, target_level: int) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(set_pending_level(text, target_level), encoding="utf-8")


def clear_to_file(path: pathlib.Path) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(clear_pending(text), encoding="utf-8")


if __name__ == "__main__":
    import argparse
    import sys

    p = argparse.ArgumentParser(description="Mark or clear a milestone level-up marker.")
    p.add_argument("--sheet", required=True, help="path to the character sheet .md")
    p.add_argument("--level", type=int, help="target level")
    p.add_argument("--clear", action="store_true", help="clear the pending marker instead of setting one")
    args = p.parse_args()
    if args.clear:
        clear_to_file(pathlib.Path(args.sheet))
        print(f"Cleared pending level-up marker on {args.sheet}")
    else:
        if args.level is None:
            p.error("--level is required unless --clear is set")
        try:
            apply_to_file(pathlib.Path(args.sheet), args.level)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            raise SystemExit(1)
        print(f"Marked pending level-up to Level {args.level} on {args.sheet}")

#!/usr/bin/env python3
"""
session_log_archive.py — deterministic session-log archival for /dm:dnd save.

The save procedure keeps only the 2 newest `## Session N` entries live in
`session-log.md`; older entries move to `session-log-archive.md` (append,
never delete). That cut-and-append is pure file surgery and used to be done
by the model with Edit calls on every save past session 3. The model still
writes the 3-5 bullet continuity summary per archived session — this script
only moves text.

Only numeric `## Session N` headers count as entries; the template blocks
(`## Session Template`, `## Session X — <date>`) stay in the preamble.
Idempotent: archived entries leave the live log, so a re-run is a no-op.

CLI:
  python3 session_log_archive.py --campaign NAME [--keep 2]
      Prints the archived session numbers, or "nothing to archive".
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402

LOG_NAME = "session-log.md"
ARCHIVE_NAME = "session-log-archive.md"

_ENTRY_HEADER = re.compile(r"^## Session (\d+)\b", re.M)


def split_entries(text: str) -> tuple[str, list[tuple[int, str]]]:
    """Split a session log into (preamble, [(session_number, block), ...]).

    A block runs from its `## Session N` header to the next numeric session
    header (or EOF). Non-numeric `## Session …` headers (Template, X) belong
    to the preamble.
    """
    matches = list(_ENTRY_HEADER.finditer(text))
    if not matches:
        return text, []
    preamble = text[:matches[0].start()]
    entries = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        entries.append((int(m.group(1)), text[m.start():end]))
    return preamble, entries


def archive_old_entries(camp_dir: pathlib.Path, keep: int = 2) -> list[int]:
    """Move all but the `keep` highest-numbered entries to the archive.

    Returns the archived session numbers (oldest first). Appends to the
    archive file (created with a header if absent); never rewrites or
    deletes archived content.
    """
    log = camp_dir / LOG_NAME
    if not log.exists():
        return []
    text = log.read_text(encoding="utf-8")
    preamble, entries = split_entries(text)
    if len(entries) <= keep:
        return []
    keep_nums = {n for n, _ in sorted(entries, key=lambda e: e[0])[-keep:]}
    to_archive = [(n, block) for n, block in entries if n not in keep_nums]
    kept = [block for n, block in entries if n in keep_nums]

    archive = camp_dir / ARCHIVE_NAME
    with open(archive, "a", encoding="utf-8") as f:
        if f.tell() == 0:
            f.write("# Session Log Archive\n\nFull entries moved out of "
                    "session-log.md at save; the continuity summaries live "
                    "in state.md → ## Continuity Archive.\n\n")
        for _, block in to_archive:
            f.write(block.rstrip("\n") + "\n\n")

    log.write_text(preamble + "".join(kept), encoding="utf-8")
    return [n for n, _ in to_archive]


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Archive old session-log entries.")
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--keep", type=int, default=2,
                    help="How many newest entries stay live (default 2).")
    args = ap.parse_args()

    camp_dir = paths.find_campaign(args.campaign)
    if not camp_dir.exists():
        print(f"campaign not found: {args.campaign}", file=sys.stderr)
        return 1
    archived = archive_old_entries(camp_dir, keep=max(args.keep, 0))
    if archived:
        nums = ", ".join(str(n) for n in archived)
        print(f"archived session(s) {nums} -> {ARCHIVE_NAME}")
    else:
        print("nothing to archive")
    return 0


if __name__ == "__main__":
    sys.exit(main())

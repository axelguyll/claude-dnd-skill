"""mirror_check.py — compare spine.json against the authored-arc mirror in state.md.

The spine is the heavy source of truth; state.md carries a light beats mirror
(id/status) plus current_beat, dual-written at `/dm:dnd beat complete` and the
authored branch of `/dm:dnd arc revise`. This makes drift between the two
deterministic to detect instead of prose-discipline. Run as step 0 of
`/dm:dnd beat complete`; on mismatch, stop and reconcile with the host — never
silently pick a winner.

Exit codes: 0 = in sync, 1 = mismatch, 2 = missing/unreadable inputs.
"""
from __future__ import annotations

import json
import re

import pathlib as _pathlib
import sys as _sys

_scripts_dir = str(_pathlib.Path(__file__).resolve().parent.parent)
if _scripts_dir not in _sys.path:
    _sys.path.insert(0, _scripts_dir)

import yaml  # noqa: E402

import paths  # noqa: E402


def load_mirror(state_text: str) -> dict | None:
    """Extract the live ## Campaign Arc yaml block from state.md text."""
    m = re.search(r"## Campaign Arc.*?```yaml\s*(.*?)```", state_text, re.DOTALL)
    if not m:
        return None
    # drop full-line comments (template remnants of the other arc formats)
    live = "\n".join(
        line for line in m.group(1).splitlines() if not line.lstrip().startswith("#")
    )
    try:
        parsed = yaml.safe_load(live)
    except yaml.YAMLError:
        return None
    return parsed if isinstance(parsed, dict) else None


def compare(spine: dict, mirror: dict | None) -> list[str]:
    """Return mismatch strings (empty == in sync)."""
    if not isinstance(mirror, dict) or mirror.get("type") != "authored":
        return ["state.md ## Campaign Arc has no live `type: authored` block"]
    errs: list[str] = []
    spine_status = {b.get("id"): b.get("status") for b in spine.get("beats", [])}
    mirror_status = {b.get("id"): b.get("status") for b in (mirror.get("beats") or [])}
    for bid, st in spine_status.items():
        if bid not in mirror_status:
            errs.append(f"beat {bid}: in spine.json but missing from state.md mirror")
        elif mirror_status[bid] != st:
            errs.append(
                f"beat {bid}: status differs — spine.json {st!r} "
                f"vs state.md {mirror_status[bid]!r}"
            )
    for bid in mirror_status:
        if bid not in spine_status:
            errs.append(f"beat {bid}: in state.md mirror but not in spine.json")
    current = [bid for bid, st in spine_status.items() if st == "current"]
    expected = current[0] if current else None
    if mirror.get("current_beat") != expected:
        errs.append(
            f"current_beat differs — spine.json implies {expected!r}, "
            f"state.md has {mirror.get('current_beat')!r}"
        )
    return errs


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(
        description="Check spine.json vs the state.md authored-arc mirror."
    )
    p.add_argument("--campaign", required=True, help="campaign name")
    args = p.parse_args()

    camp = paths.find_campaign(args.campaign)
    spine_path, state_path = camp / "spine.json", camp / "state.md"
    if not spine_path.is_file() or not state_path.is_file():
        print(f"MISSING: {spine_path if not spine_path.is_file() else state_path}")
        _sys.exit(2)
    try:
        spine = json.loads(spine_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"UNREADABLE spine.json: {e}")
        _sys.exit(2)
    mismatches = compare(spine, load_mirror(state_path.read_text(encoding="utf-8")))
    if mismatches:
        print("MISMATCH:")
        for m in mismatches:
            print(f"  - {m}")
        _sys.exit(1)
    print("MIRROR OK")

#!/usr/bin/env python3
"""
session_audit.py — between-session audit checks over a finished transcript.

Pass B Cluster A (2026-07-20): the cheap, exact, zero-per-turn-cost end of
the enforcement budget. Five post-hoc checks, all reading the transcript
and campaign files after a session; the report is reviewed by a human
between sessions. Not wired into any hook, and never run mid-play.

Checks (finding `check` ids):
  dice_provenance     a narrated resolved roll line with no dice.py/combat.py
                      tool call in the same turn (A4 — the only mechanical
                      no-fudge audit that exists)
  no_xp               an `xp.py award` call, or an XP-award block in output
                      (A3 — this fork never awards XP)
  microsave_liveness  state.md / session-tail.md untouched across a long
                      session while `autosave: on` (A7 — staleness is
                      deterministic even when flush content is not)
  state_divergence    the STATE_JSON last passed to render_tracker.py vs the
                      `## Active Combat` block in state.md (A8 — mid-combat
                      compaction recovers from that block)
  lint_log_privacy    a mid-session Read/Bash touching `.lint-log.jsonl`
                      (A5 — the lint log is an instrument, not a play surface)

Like the turn lint, a clean report means "nothing matched", never "the
session was clean" — the checks are exact but narrow.

CLI:
  python3 session_audit.py --campaign NAME --transcript SESSION.jsonl
      [--jsonl OUT] [--min-turns N]
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402
import turn_lint  # noqa: E402  (transcript turn-boundary contract)

# A resolved die roll of any size, e.g. "d20+4 = 17", "1d6+2 -> 5".
_RESOLVED_ROLL = re.compile(
    r"\b\d{0,2}d\d+\s*(?:[+-]\s*\d+)?\s*(?:=|→|->)\s*\**\d+", re.I)
_DICE_TOOL = re.compile(r"\b(?:dice|combat)\.py\b")
_XP_TOOL = re.compile(r"\bxp\.py\b.*\baward\b")
_XP_TEXT = re.compile(
    r"\+\s*\d+\s*XP\b|\bawarded?\s+\d+\s*XP\b|\bXP\s+award(?:ed)?\b|"
    r"\bgain(?:s|ed)?\s+\d+\s*XP\b", re.I)
_LINT_LOG_TOUCH = re.compile(r"\.lint-log\.jsonl")
_LINT_TAIL = re.compile(r"turn_lint\.py\b.*--tail")
_RENDER_STATE = re.compile(
    r"render_tracker\.py.*?--state\s+(?:'(.*?)'(?=\s+--|\s*$)|\"(.*?)\"(?=\s+--|\s*$))",
    re.S)


def parse_turns(transcript_path: str | pathlib.Path) -> list[dict]:
    """DM turns with tool context, oldest first.

    Each turn: {"texts": [...], "commands": [Bash command strings],
    "read_paths": [Read file_path strings], "ts": first ISO timestamp seen}.
    Same turn-boundary contract as turn_lint (a genuine user message starts
    a new turn; tool_results do not).
    """
    p = pathlib.Path(transcript_path)
    try:
        raw_lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    turns: list[dict] = []
    current: dict | None = None

    def flush():
        nonlocal current
        if current and (current["texts"] or current["commands"]
                        or current["read_paths"]):
            turns.append(current)
        current = None

    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except ValueError:
            continue
        if turn_lint._is_turn_boundary(obj):
            flush()
            current = {"texts": [], "commands": [], "read_paths": [],
                       "ts": obj.get("timestamp")}
            continue
        if obj.get("type") != "assistant":
            continue
        if current is None:
            current = {"texts": [], "commands": [], "read_paths": [],
                       "ts": obj.get("timestamp")}
        for block in (obj.get("message") or {}).get("content") or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                current["texts"].append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                inp = block.get("input") or {}
                if isinstance(inp.get("command"), str):
                    current["commands"].append(inp["command"])
                if isinstance(inp.get("file_path"), str):
                    current["read_paths"].append(inp["file_path"])
    flush()
    return turns


def _finding(check: str, turn_idx: int, detail: str, excerpt: str = "") -> dict:
    return {"check": check, "turn": turn_idx, "detail": detail,
            "excerpt": excerpt[:160]}


# ── Checks ────────────────────────────────────────────────────────────────

def check_dice_provenance(turns: list[dict]) -> list[dict]:
    out = []
    for i, turn in enumerate(turns, 1):
        has_dice_call = any(_DICE_TOOL.search(c) for c in turn["commands"])
        if has_dice_call:
            continue
        for text in turn["texts"]:
            for line in text.splitlines():
                m = _RESOLVED_ROLL.search(line)
                if m:
                    out.append(_finding(
                        "dice_provenance", i,
                        "resolved roll line with no dice.py/combat.py call "
                        "in the same turn", line.strip()))
    return out


def check_no_xp(turns: list[dict]) -> list[dict]:
    out = []
    for i, turn in enumerate(turns, 1):
        for cmd in turn["commands"]:
            if _XP_TOOL.search(cmd):
                out.append(_finding("no_xp", i, "xp.py award call", cmd))
        for text in turn["texts"]:
            m = _XP_TEXT.search(text)
            if m:
                out.append(_finding(
                    "no_xp", i, "XP-award block in narration",
                    text[max(0, m.start() - 40):m.end() + 40]))
    return out


def check_lint_log_privacy(turns: list[dict]) -> list[dict]:
    out = []
    for i, turn in enumerate(turns, 1):
        for path in turn["read_paths"]:
            if _LINT_LOG_TOUCH.search(path):
                out.append(_finding("lint_log_privacy", i,
                                    "Read of the lint log mid-session", path))
        for cmd in turn["commands"]:
            if _LINT_LOG_TOUCH.search(cmd) or _LINT_TAIL.search(cmd):
                out.append(_finding("lint_log_privacy", i,
                                    "Bash touching the lint log mid-session",
                                    cmd))
    return out


def _parse_ts(raw) -> float | None:
    if not isinstance(raw, str):
        return None
    try:
        return datetime.datetime.fromisoformat(
            raw.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def check_microsave_liveness(turns: list[dict], camp_dir: pathlib.Path,
                             min_turns: int = 8) -> list[dict]:
    """Anchor files untouched across a long autosave:on session.

    Judged only when the session is long enough to owe flushes and the
    transcript carries timestamps; the content of a flush stays human-judged.
    """
    if len(turns) < min_turns:
        return []
    flags = turn_lint.session_flags(camp_dir)
    if flags.get("autosave", "on").lower() in ("off", "false", "disabled"):
        return []
    starts = [t for t in (_parse_ts(turn.get("ts")) for turn in turns)
              if t is not None]
    if not starts:
        return []
    session_start = min(starts)
    stale = []
    for name in ("state.md", "session-tail.md"):
        f = camp_dir / name
        try:
            if not f.exists() or f.stat().st_mtime < session_start:
                stale.append(name)
        except OSError:
            stale.append(name)
    if not stale:
        return []
    return [_finding(
        "microsave_liveness", len(turns),
        f"{' and '.join(stale)} untouched across {len(turns)} turns with "
        f"autosave: on")]


def check_state_divergence(turns: list[dict], camp_dir: pathlib.Path) -> list[dict]:
    """Last STATE_JSON passed to render_tracker.py vs `## Active Combat`.

    Order-insensitive by combatant name — per-turn renders rotate the active
    actor to the front, which is not divergence. A block with no parseable
    JSON is not flagged (combat may have ended and been cleared); a block
    whose combatants or facts differ is.
    """
    last_state = None
    for turn in turns:
        for cmd in turn["commands"]:
            m = _RENDER_STATE.search(cmd)
            if m:
                raw = m.group(1) if m.group(1) is not None else m.group(2)
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        last_state = parsed
                except ValueError:
                    pass
    if last_state is None:
        return []
    state_md = camp_dir / "state.md"
    if not state_md.exists():
        return []
    text = state_md.read_text(encoding="utf-8", errors="replace")
    section = _section(text, "## Active Combat")
    if section is None:
        return []
    m = re.search(r"\[[\s\S]*\]", section)
    if not m:
        return []
    try:
        block = json.loads(m.group(0))
    except ValueError:
        return []
    if not isinstance(block, list):
        return []

    rendered = {str(c.get("name")): c for c in last_state if isinstance(c, dict)}
    durable = {str(c.get("name")): c for c in block if isinstance(c, dict)}
    problems = []
    for name in rendered.keys() - durable.keys():
        problems.append(f"{name} rendered but missing from the block")
    for name in durable.keys() - rendered.keys():
        problems.append(f"{name} in the block but not in the last render")
    for name in rendered.keys() & durable.keys():
        if rendered[name] != durable[name]:
            problems.append(f"{name} differs between render and block")
    if not problems:
        return []
    return [_finding("state_divergence", len(turns), "; ".join(problems))]


def _section(text: str, header: str) -> str | None:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == header:
            start = i + 1
            break
    if start is None:
        return None
    body = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body)


# ── CLI ───────────────────────────────────────────────────────────────────

def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="Between-session audit over a finished transcript.")
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--jsonl", help="Also append findings to this file.")
    ap.add_argument("--min-turns", type=int, default=8,
                    help="Turns before microsave liveness is judged (default 8).")
    args = ap.parse_args()

    camp_dir = paths.find_campaign(args.campaign)
    if not camp_dir.exists():
        print(f"campaign not found: {args.campaign}", file=sys.stderr)
        return 1
    turns = parse_turns(args.transcript)
    if not turns:
        print("(no turns found in transcript)")
        return 0

    findings = []
    findings += check_dice_provenance(turns)
    findings += check_no_xp(turns)
    findings += check_microsave_liveness(turns, camp_dir, args.min_turns)
    findings += check_state_divergence(turns, camp_dir)
    findings += check_lint_log_privacy(turns)

    print(f"{len(turns)} turns audited — {len(findings)} finding(s)")
    for f in findings:
        print(f"  turn {f['turn']:>3}  {f['check']}: {f['detail']}")
        if f["excerpt"]:
            print(f"            {f['excerpt']}")
    if args.jsonl and findings:
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat(
            timespec="seconds")
        with open(args.jsonl, "a", encoding="utf-8") as fh:
            for f in findings:
                fh.write(json.dumps({"ts": ts, "campaign": args.campaign,
                                     **f}, ensure_ascii=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

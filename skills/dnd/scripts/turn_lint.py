#!/usr/bin/env python3
"""turn_lint.py — log-only adherence lint for DM turns.

Invoked from the autosave Stop hook (`autosave_checkpoint.py`) after every DM
turn. Scans the just-finished assistant turn for machine-detectable rule
violations and appends findings to `<campaign>/.lint-log.jsonl`. **Log-only:**
it never blocks and never prints in hook mode — the log is reviewed between
sessions to measure adherence and detector precision before any blocking is
enabled (design: docs/reviews/2026-07-17-fable-solutions.md §5.1).

Detectors (rule anchor in SKILL.md):
  rote_closer     stock "what do you do?" closer at turn end (Narration principles)
  dc_leak         DC number in player-facing text ("Never state the DC";
                  tutor lines and the PC's own spell save DC are exempt)
  roll_not_final  roll request followed by substantive narration
                  ("The roll request ends the turn" — roll_mode: players only)
  pc_auto_roll    visible resolved check/save roll line under roll_mode: players
                  (the "never fall back to dice.py for a PC" hard constraint;
                  heuristic — NPC skill rolls formatted the same way will also
                  land in the log, the excerpt lets the reviewer judge)
  unknown_cue     sound/map cue handle not on the campaign's lists
                  ("never invent a cue" / "never invent a map")

Per-campaign opt-out: `turn_lint: off` in `state.md → ## Session Flags`.

Manual usage:
  python3 turn_lint.py --campaign <name> --transcript <session.jsonl>  # lint last turn, print findings
  python3 turn_lint.py --campaign <name> --tail 10                     # show last N log entries
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
from render_assets import parse_asset_list  # noqa: E402

LOG_NAME = ".lint-log.jsonl"
EXCERPT_LEN = 160

# Words of trailing narration tolerated after a roll request (allows a short
# "…or something else?" style option tail without flagging).
ROLL_TAIL_ALLOWANCE = 40

_SKILLS = (
    "Acrobatics|Animal Handling|Arcana|Athletics|Deception|History|Insight|"
    "Intimidation|Investigation|Medicine|Nature|Perception|Performance|"
    "Persuasion|Religion|Sleight of Hand|Stealth|Survival"
)

_ROTE_CLOSER = re.compile(
    r"what (?:do|will) you do|what'?s your (?:move|play|next)|"
    r"what do you (?:want|wanna)(?: to)? do",
    re.I,
)
_DC_NUMBER = re.compile(r"\bDC\s*\d+")
_SPELL_SAVE_DC = re.compile(r"spell save DC", re.I)
_ROLL_REQUEST = re.compile(
    r"(?:\broll\b|\bmake\b|\bgive me\b)[^.\n!?]{0,80}?"
    r"(?:\bcheck\b|\bsave\b|saving throw|\bd20\b|attack roll)",
    re.I,
)
_RESOLVED_ROLL_LINE = re.compile(
    r"\*\*Roll:?\*\*.*\bd20\b.*(?:→|->)", re.I)
_SKILL_PAREN = re.compile(r"\((?:%s)\)" % _SKILLS, re.I)
_SOUND_CUE = re.compile(r"🔊 \*\*Cue:\*\* \*(.+?)\*")
_MAP_CUE = re.compile(r"🗺 \*\*Map:\*\* \*(.+?)\*")


def _excerpt(text: str, start: int = 0) -> str:
    return text[start:start + EXCERPT_LEN].strip()


# ── Detectors (pure functions: text in, violation dicts out) ──────────────

def check_rote_closer(text: str) -> list[dict]:
    tail = text[-200:]
    m = _ROTE_CLOSER.search(tail)
    if not m:
        return []
    return [{"detector": "rote_closer",
             "detail": "stock closer at turn end",
             "excerpt": _excerpt(tail, max(0, m.start() - 40))}]


def check_dc_leak(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        if "◈ Tutor" in line or _SPELL_SAVE_DC.search(line):
            continue
        m = _DC_NUMBER.search(line)
        if m:
            out.append({"detector": "dc_leak",
                        "detail": f"DC number in player-facing text ({m.group(0)})",
                        "excerpt": _excerpt(line)})
    return out


def check_roll_not_final(text: str, roll_mode: str) -> list[dict]:
    if roll_mode != "players":
        return []
    last = None
    for m in _ROLL_REQUEST.finditer(text):
        last = m
    if last is None:
        return []
    trailing = text[last.end():]
    n_words = len(trailing.split())
    if n_words <= ROLL_TAIL_ALLOWANCE:
        return []
    return [{"detector": "roll_not_final",
             "detail": f"roll request followed by {n_words} words of narration",
             "excerpt": _excerpt(text, last.start())}]


def check_pc_auto_roll(text: str, roll_mode: str) -> list[dict]:
    if roll_mode != "players":
        return []
    out = []
    for line in text.splitlines():
        if not _RESOLVED_ROLL_LINE.search(line):
            continue
        kind = ("skill check" if _SKILL_PAREN.search(line)
                else "save" if re.search(r"\bsave\b|saving throw", line, re.I)
                else None)
        if kind is None:
            continue
        out.append({"detector": "pc_auto_roll",
                    "detail": f"resolved {kind} roll line under roll_mode: players",
                    "excerpt": _excerpt(line)})
    return out


def check_unknown_cue(text: str, ambient_handles: set[str],
                      map_handles: set[str]) -> list[dict]:
    out = []
    for m in _SOUND_CUE.finditer(text):
        handle = m.group(1).strip()
        if handle.lower() not in ambient_handles:
            out.append({"detector": "unknown_cue",
                        "detail": f"sound cue not on ambient-list: {handle!r}",
                        "excerpt": _excerpt(m.group(0))})
    for m in _MAP_CUE.finditer(text):
        handle = m.group(1).strip()
        if handle.lower().startswith("down"):  # "down — theater of the mind"
            continue
        if handle.lower() not in map_handles:
            out.append({"detector": "unknown_cue",
                        "detail": f"map cue not on map-list: {handle!r}",
                        "excerpt": _excerpt(m.group(0))})
    return out


def lint_turn(text: str, flags: dict, ambient_handles: set[str],
              map_handles: set[str]) -> list[dict]:
    roll_mode = flags.get("roll_mode", "players")
    findings = []
    findings += check_rote_closer(text)
    findings += check_dc_leak(text)
    findings += check_roll_not_final(text, roll_mode)
    findings += check_pc_auto_roll(text, roll_mode)
    findings += check_unknown_cue(text, ambient_handles, map_handles)
    return findings


# ── Campaign ground truth ─────────────────────────────────────────────────

def session_flags(camp_dir: pathlib.Path) -> dict:
    """Parse `state.md → ## Session Flags` into a {key: value} dict."""
    state = camp_dir / "state.md"
    if not state.exists():
        return {}
    try:
        lines = state.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    flags, inside = {}, False
    for line in lines:
        if line.strip() == "## Session Flags":
            inside = True
            continue
        if inside and line.startswith("## "):
            break
        if inside:
            m = re.match(r"^(\w+):\s*(.+?)\s*$", line.strip())
            if m:
                flags[m.group(1)] = m.group(2)
    return flags


def asset_handles(camp_dir: pathlib.Path) -> tuple[set[str], set[str]]:
    """Lowercased cue handles from the campaign's ambient/map lists."""
    handles = []
    for name in ("ambient-list.md", "map-list.md"):
        f = camp_dir / name
        if not f.exists():
            handles.append(set())
            continue
        try:
            items = parse_asset_list(f.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            items = []
        handles.append({i["handle"].lower() for i in items})
    return handles[0], handles[1]


# ── Transcript parsing ────────────────────────────────────────────────────

def last_turn(transcript_path: str | pathlib.Path) -> str:
    """Player-facing text of the final assistant turn: every assistant text
    block emitted since the last genuine user message (tool_results are not
    turn boundaries). Empty string when the transcript is missing/unreadable."""
    p = pathlib.Path(transcript_path)
    try:
        raw_lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    texts: list[str] = []
    for raw in reversed(raw_lines):
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except ValueError:
            continue
        kind = obj.get("type")
        msg = obj.get("message") or {}
        if kind == "assistant":
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text", ""))
        elif kind == "user":
            content = msg.get("content")
            if isinstance(content, str):
                break  # genuine user prompt — turn boundary
            if isinstance(content, list):
                if not any(isinstance(b, dict) and b.get("type") == "tool_result"
                           for b in content):
                    break  # genuine user prompt — turn boundary
                # tool_result feedback — same turn, keep walking
    return "\n\n".join(reversed(texts))


# ── Hook entry point ──────────────────────────────────────────────────────

def run_and_log(stdin_obj: dict, campaign: str) -> int:
    """Lint the turn in `transcript_path` and append findings to the campaign
    log. Returns the number of findings. Never raises, never prints."""
    try:
        transcript = stdin_obj.get("transcript_path")
        if not transcript:
            return 0
        camp_dir = paths.find_campaign(campaign)
        if not camp_dir.exists():
            return 0
        flags = session_flags(camp_dir)
        if flags.get("turn_lint", "on").lower() in ("off", "false", "disabled"):
            return 0
        text = last_turn(transcript)
        if not text.strip():
            return 0
        ambient, maps = asset_handles(camp_dir)
        findings = lint_turn(text, flags, ambient, maps)
        if not findings:
            return 0
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        sid = stdin_obj.get("session_id")
        with open(camp_dir / LOG_NAME, "a", encoding="utf-8") as f:
            for v in findings:
                f.write(json.dumps({"ts": ts, "session_id": sid,
                                    "campaign": campaign, **v},
                                   ensure_ascii=True) + "\n")
        return len(findings)
    except Exception:
        return 0  # a lint failure must never break the Stop hook


# ── CLI (manual review / dev) ─────────────────────────────────────────────

def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Log-only DM turn lint.")
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--transcript", help="Session .jsonl — lint its last turn and print findings.")
    ap.add_argument("--tail", type=int, help="Print the last N lint-log entries.")
    args = ap.parse_args()

    camp_dir = paths.find_campaign(args.campaign)
    if not camp_dir.exists():
        print(f"campaign not found: {args.campaign}", file=sys.stderr)
        return 1

    if args.tail:
        log = camp_dir / LOG_NAME
        if not log.exists():
            print("(lint log empty)")
            return 0
        lines = log.read_text(encoding="utf-8").splitlines()[-args.tail:]
        for line in lines:
            print(line)
        return 0

    if not args.transcript:
        ap.error("--transcript or --tail required")
    text = last_turn(args.transcript)
    if not text.strip():
        print("(no assistant turn found in transcript)")
        return 0
    ambient, maps = asset_handles(camp_dir)
    findings = lint_turn(text, session_flags(camp_dir), ambient, maps)
    if not findings:
        print("clean: no findings")
        return 0
    for v in findings:
        print(f"{v['detector']}: {v['detail']}\n    {v['excerpt']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

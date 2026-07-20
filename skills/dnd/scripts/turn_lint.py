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
  roll_not_final  roll request preceded by odds/outcome-hedging lead-in
                  narration, or followed by substantive narration
                  ("The roll request ends the turn" — roll_mode: players only;
                  the lead-in half is recall-biased by design — see
                  check_roll_not_final)
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
# Lead-in narration that pre-judges the roll — states or implies the outcome,
# the odds, or how hard the attempt looks (SKILL.md: "the canonical
# violation" is "this isn't going to win on skill"). Four general categories,
# each a named regex so a reviewer can see which one fired (the `detail`
# string reports the category name) — deliberately NOT one opaque alternation
# curve-fit to known fixtures. Recall-biased: this detector is log-only, so a
# false positive costs a log line while a false negative costs a session of
# believing the rules held when they didn't.

# 1. Negated-ease: the DM hedges that the attempt won't be simple/quick,
#    without naming odds or a target trait directly.
_NEGATED_EASE = re.compile(
    r"\bnot\s+exactly\s+\w+\b|"
    r"\b(?:isn'?t|aren'?t|wasn'?t|weren'?t|is\s+not|are\s+not|was\s+not|were\s+not)"
    r"\s+(?:going\s+to\s+be\s+)?(?:easy|simple|quick|straightforward)\b|"
    r"\bnot\s+going\s+to\s+be\s+(?:easy|simple|quick|straightforward)\b|"
    r"\b(?:won'?t|wouldn'?t)\s+be\s+(?:easy|simple|quick|straightforward)\b|"
    r"\b(?:doesn'?t|don'?t|didn'?t)\s+just\s+\w+\b|"
    r"\bno\s+easy\s+(?:thing|task|feat|matter)\b",
    re.I,
)
# 2. REMOVED — bare difficulty/odds vocabulary (hard|tough|tricky|odds|chance|
#    easy|simple, unfiltered by sentence role). It assumed the tight lead-in
#    window made a structural check unnecessary. Measured against legitimate
#    pre-roll narration it produced a false positive on 6 of 6 samples, because
#    the lead-in window is exactly where the *permitted* attempt description
#    lives and it shares this vocabulary: "you push hard against the door",
#    "you keep it simple", "you go easy on the latch", "the rain is coming down
#    hard". SKILL.md explicitly allows all of those. A detector that fires on
#    the behaviour a rule permits trains the reader to ignore it.
#    Cost of removal: real violations carried only by a bare adjective
#    ("Garrick is a hard man to like") are no longer caught. Accepted — see
#    check_roll_not_final's docstring on what this detector does not cover.
# 2b. Difficulty *predication* — the replacement for the removed lexicon.
#    Bare adjectives are ambiguous ("push hard" describes the attempt, which is
#    allowed; "looks hard" rates the difficulty, which is not). What separates
#    them is grammatical role, so match the constructions where the adjective is
#    predicated of the task or the target rather than modifying the PC's action:
#    a copular/perception verb ("looks tricky"), "the odds" as a subject, or an
#    attributive "a hard man to read". Verified against the six legitimate
#    phrasings that broke the lexicon — none of them match these.
_DIFFICULTY_PREDICATION = re.compile(
    r"\b(?:look|looks|looked|seem|seems|seemed|sound|sounds|sounded|"
    r"feel|feels|felt)\s+(?:like\s+)?(?:a\s+)?"
    r"(?:tricky|hard|tough|difficult|dicey|risky|rough|steep|easy|simple)\b|"
    r"\bthe\s+odds\b|"
    r"\ba\s+(?:hard|tough|tricky|difficult)\s+\w+\s+to\s+\w+\b",
    re.I,
)
# 3. Outcome pre-judgment: the DM states how the roll will land before it's
#    made.
_OUTCOME_PREJUDGMENT = re.compile(
    r"\b(?:isn'?t|aren'?t|wasn'?t)\s+going\s+to\s+\w+\b|"
    r"\bwon'?t\s+work\b|"
    r"\bno\s+way\s+(?:he|she|they|it|you)\b|"
    r"\bgood\s+luck\s+with\b|"
    r"\bif\s+you\s+can\s+even\b",
    re.I,
)
# 4. Target-resistance framing: the DM pre-rates the opposition (how alert,
#    guarded, or hard-to-fool the target is) rather than letting the roll
#    decide it.
_TARGET_RESISTANCE = re.compile(
    r"\bguarded\b|\bwary\b|\bcareful\b|\bsharp(?:-eyed)?\b|\bsuspicious\b|"
    r"\bnot\s+(?:stupid|foolish|gullible|slow|careless|easily\s+fooled)\b|"
    r"\bhard\s+to\s+(?:read|fool|convince|persuade)\b|"
    r"\bquick[- ]witted\b|\bon\s+(?:her|his|their|your)\s+guard\b|\bno\s+fool\b",
    re.I,
)
_ODDS_HEDGE_CATEGORIES = (
    ("negated-ease", _NEGATED_EASE),
    ("difficulty predication", _DIFFICULTY_PREDICATION),
    ("outcome pre-judgment", _OUTCOME_PREJUDGMENT),
    ("target-resistance framing", _TARGET_RESISTANCE),
)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
# Lead-in lookback is bounded to the current paragraph (never crosses a
# blank-line break) and further capped to this many trailing characters, so
# an odds-hedge several paragraphs up (an earlier, resolved beat) is never
# in scope.
LEAD_IN_CHAR_CAP = 300
LEAD_IN_SENTENCES = 2
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


def _roll_lead_in_window(text: str, request_start: int) -> str:
    """The one-or-two-sentence lead-in immediately before a roll request.

    Bounded to the current paragraph (never crosses a blank-line break), so
    narration from an earlier, already-resolved beat is out of scope.
    LEAD_IN_CHAR_CAP applies only when there is no paragraph break at all —
    the two bounds are alternatives, not additive. Either way the result is
    trimmed to the last LEAD_IN_SENTENCES sentences, which is the real bound.
    """
    before = text[:request_start]
    para_break = before.rfind("\n\n")
    window = before[para_break + 2:] if para_break != -1 else before[-LEAD_IN_CHAR_CAP:]
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(window) if s.strip()]
    return " ".join(sentences[-LEAD_IN_SENTENCES:])


def _odds_hedge_category(lead_in: str) -> str | None:
    """First odds/outcome-hedge category that matches, or None.

    Checked in a fixed order (negated-ease, difficulty predication, outcome
    pre-judgment, target-resistance framing); the first hit names the
    category reported in the finding's `detail`.

    Typographic apostrophes are folded to ASCII first. Three of the four
    categories lean on contractions ("isn't", "won't", "doesn't"), so a U+2019
    would silently disable most of the detector while "not exactly" kept
    matching — a partial failure is harder to notice than a total one. Current
    narration uses ASCII throughout (183 to 0 across a full session), so this
    guards a latent gap rather than an observed one.
    """
    lead_in = lead_in.replace("’", "'")
    for category, pattern in _ODDS_HEDGE_CATEGORIES:
        if pattern.search(lead_in):
            return category
    return None


def check_roll_not_final(text: str, roll_mode: str) -> list[dict]:
    """Both halves of "the roll request ends the turn": lead-in hedging
    before the request, and substantive narration after it.

    The lead-in half matches the one-or-two-sentence window immediately
    before the request against four hedge categories (see
    _ODDS_HEDGE_CATEGORIES) selected for grammatical shape rather than
    vocabulary, because the rule turns on grammatical role: "you push hard
    against the door" describes the attempt and is allowed; "the door looks
    hard to force" rates the difficulty and is not. Both contain "hard". An
    earlier bare-lexicon version fired on 6 of 6 permitted phrasings.

    Known blind spots, measured rather than assumed: violations carried by
    implication rather than construction pass clean — "That's not the kind
    of man who talks easily", "She's already got your measure", "This could
    go sideways fast". Recall against arbitrary phrasing is poor and does
    not improve by extending the lists; the signal is semantic, not lexical.
    Read a clean result as "nothing matched", never as "the turn was clean".
    SKILL.md:306 is wider than anything checkable here, and hand-review
    remains the instrument of record for it.

    Consequently this is NOT a blocking-mode candidate: it would pass most
    real violations while occasionally stopping a legal turn.
    """
    if roll_mode != "players":
        return []
    last = None
    for m in _ROLL_REQUEST.finditer(text):
        last = m
    if last is None:
        return []
    out = []
    lead_in = _roll_lead_in_window(text, last.start())
    category = _odds_hedge_category(lead_in) if lead_in else None
    if category:
        out.append({"detector": "roll_not_final",
                    "detail": f"lead-in narration implies the odds/outcome "
                              f"before the roll request ({category})",
                    "excerpt": _excerpt(lead_in)})
    trailing = text[last.end():]
    n_words = len(trailing.split())
    if n_words > ROLL_TAIL_ALLOWANCE:
        out.append({"detector": "roll_not_final",
                    "detail": f"roll request followed by {n_words} words of narration",
                    "excerpt": _excerpt(text, last.start())})
    return out


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


def _is_turn_boundary(obj: dict) -> bool:
    """True for a genuine user prompt. Tool results are not boundaries — they
    are feedback inside the DM's own turn."""
    if obj.get("type") != "user":
        return False
    content = (obj.get("message") or {}).get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return not any(isinstance(b, dict) and b.get("type") == "tool_result"
                       for b in content)
    return False


def all_turns(transcript_path: str | pathlib.Path) -> list[str]:
    """Every player-facing DM turn in the transcript, oldest first.

    `last_turn` is the live-hook path and only ever needs the final turn. This
    walks the whole session so a backfill can recover turns played while the
    hook was broken or not yet installed.
    """
    p = pathlib.Path(transcript_path)
    try:
        raw_lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    turns: list[str] = []
    current: list[str] = []

    def flush():
        if current:
            joined = "\n\n".join(current).strip()
            if joined:
                turns.append(joined)
            current.clear()

    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except ValueError:
            continue
        if _is_turn_boundary(obj):
            flush()
        elif obj.get("type") == "assistant":
            for block in (obj.get("message") or {}).get("content") or []:
                if isinstance(block, dict) and block.get("type") == "text":
                    current.append(block.get("text", ""))
    flush()
    return turns


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
    ap.add_argument("--backfill", action="store_true",
                    help="With --transcript: lint every turn in the session and "
                         "report per-turn, instead of only the last one.")
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

    if args.backfill:
        flags = session_flags(camp_dir)
        ambient, maps = asset_handles(camp_dir)
        turns = all_turns(args.transcript)
        total = 0
        for i, text in enumerate(turns, 1):
            findings = lint_turn(text, flags, ambient, maps)
            total += len(findings)
            for v in findings:
                print(f"turn {i:>3}  {v['detector']}: {v['detail']}")
                print(f"          {v['excerpt']}")
        rate = (total / len(turns)) if turns else 0.0
        print(f"\n{len(turns)} turns · {total} findings · {rate:.2f} per turn")
        return 0

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

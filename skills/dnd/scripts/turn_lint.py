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
  first_use_gloss campaign proper noun first-used in narration without a
                  same-sentence gloss ("naming and glossing are one act,
                  not a name plus a tax" — SKILL.md). Inventory is drawn
                  mechanically from the campaign's own world.md/npcs.md
                  (build_name_inventory) — no AI-judgment step, deliberately
                  (anti-pattern 10: a model that has read world.md already
                  knows the jargon and cannot feel the player's confusion).
                  First use is tracked per campaign in
                  `<campaign>/.lint-seen-names.json`, written alongside the
                  lint log — see check_first_use_gloss.
  narration_band  session-opening narration over its heat band's word cap,
                  or introducing more than three new names ("Length
                  follows the scene's heat" — SKILL.md Standard 4). Fires
                  ONLY on the session's first turn (is_first_turn) — heat
                  is not mechanically decidable on any other turn, and the
                  Breathe band is unbounded by design. See
                  check_narration_band.

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
SEEN_NAMES_LOG = ".lint-seen-names.json"
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
# Deterministic format triggers, not a hedge lexicon: the imperative verbs
# ("roll/make/give me"), the "I need a / let's see a" request idioms (article
# required, so "I need you to check on the horses" stays narration), and the
# bare house format "<Ability> (<Skill>) check". A trigger miss silences BOTH
# halves of roll_not_final, so coverage here is coverage of the whole rule.
_ABILITIES = "Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma"
_ROLL_REQUEST = re.compile(
    r"(?:\broll\b|\bmake\b|\bgive me\b)[^.\n!?]{0,80}?"
    r"(?:\bcheck\b|\bsave\b|saving throw|\bd20\b|attack roll)"
    r"|\b(?:I\s+need|let'?s\s+see)\s+(?:a|an|another|one\s+more)"
    r"[^.\n!?]{0,60}?(?:\bcheck\b|\bsave\b|saving throw|\bd20\b)"
    r"|\b(?:%s)\s*\((?:%s)\)\s+(?:check|save)\b" % (_ABILITIES, _SKILLS),
    re.I,
)
_RESOLVED_ROLL_LINE = re.compile(
    r"\*\*Roll:?\*\*.*\bd20\b.*(?:→|->)", re.I)
# The skill's own canonical inline roll format (SKILL.md: "Piper —
# Perception: d20+5 = 18"): a resolved d20 with `=` or an arrow. Which lines
# are violations is decided by PC-name attribution against campaign data
# (characters/*.md), not by format-guessing — the earlier detector matched
# only the session-1 violation's bold-prefix shape.
_RESOLVED_D20 = re.compile(r"\bd20\s*(?:[+-]\s*\d+)?\s*(?:=|→|->)\s*\**\d+", re.I)
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
#    The "doesn't just <anything>" arm matched plain intensifiers ("the rain
#    doesn't just fall — it hammers", permitted restatement), so it is
#    constrained to yield-class verbs: things a task or target does when it
#    gives way without a contest (probe-verified both directions 2026-07-20).
#    Cost: hedges via other verbs ("he doesn't just talk to strangers") are
#    no longer caught. Accepted — precision first.
_NEGATED_EASE = re.compile(
    r"\bnot\s+exactly\s+\w+\b|"
    r"\b(?:isn'?t|aren'?t|wasn'?t|weren'?t|is\s+not|are\s+not|was\s+not|were\s+not)"
    r"\s+(?:going\s+to\s+be\s+)?(?:easy|simple|quick|straightforward)\b|"
    r"\bnot\s+going\s+to\s+be\s+(?:easy|simple|quick|straightforward)\b|"
    r"\b(?:won'?t|wouldn'?t)\s+be\s+(?:easy|simple|quick|straightforward)\b|"
    r"\b(?:doesn'?t|don'?t|didn'?t)\s+just\s+"
    r"(?:open|give|yield|budge|break|fold|hand|let|step\s+aside|"
    r"back\s+down|roll\s+over)\b|"
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
#    `rough` and `steep` are excluded from the perception-verb arm: their
#    literal physical senses dominate pre-roll narration ("the rope feels
#    rough" is texture, "the trail looks steep" is terrain — both permitted
#    scene description, probe-verified 2026-07-20). Cost: a difficulty rating
#    carried only by those two adjectives ("this climb looks steep") is no
#    longer caught. Accepted — same tradeoff as the category-2 removal above.
_DIFFICULTY_PREDICATION = re.compile(
    r"\b(?:look|looks|looked|seem|seems|seemed|sound|sounds|sounded|"
    r"feel|feels|felt)\s+(?:like\s+)?(?:a\s+)?"
    r"(?:tricky|hard|tough|difficult|dicey|risky|easy|simple)\b|"
    r"\bthe\s+odds\b|"
    r"\ba\s+(?:hard|tough|tricky|difficult)\s+\w+\s+to\s+\w+\b",
    re.I,
)
# 3. Outcome pre-judgment: the DM states how the roll will land before it's
#    made. The "isn't going to <anything>" arm matched every negated future
#    ("the storm isn't going to break" — weather, permitted), so it is
#    constrained to success-class verbs, or refusal-class verbs with a
#    personal subject (probe-verified both directions 2026-07-20). Cost: a
#    pre-judgment carried by a verb outside these classes ("this isn't going
#    to impress her") is no longer caught. Accepted — precision first.
_OUTCOME_PREJUDGMENT = re.compile(
    r"\b(?:isn'?t|aren'?t|wasn'?t|weren'?t)\s+going\s+to\s+"
    r"(?:work|succeed|help|matter|win|land|cut\s+it|be\s+enough|"
    r"get\s+you\s+(?:anywhere|far|in|past)|go\s+(?:well|your\s+way))\b|"
    r"\b(?:he|she|they)\s+(?:isn'?t|aren'?t|wasn'?t|weren'?t)\s+going\s+to\s+"
    r"(?:listen|budge|buy|believe|bend|crack|talk|yield|give)\b|"
    r"\bwon'?t\s+work\b|"
    r"\bno\s+way\s+(?:he|she|they|it|you)\b|"
    r"\bgood\s+luck\s+with\b|"
    r"\bif\s+you\s+can\s+even\b",
    re.I,
)
# 4. Target-resistance framing: the DM pre-rates the opposition (how alert,
#    guarded, or hard-to-fool the target is) rather than letting the roll
#    decide it. The bare single-word arms (guarded|wary|careful|sharp|
#    suspicious) were the removed category-2 defect with different words —
#    probed 2026-07-20, they fired on 6 of 6 permitted phrasings ("careful of
#    the loose stones", "a sharp crack", "the guarded gate"), because the
#    permitted and forbidden senses share the vocabulary and only grammatical
#    role separates them. Only constructions predicated of the target remain.
#    Cost: a pre-rating carried by a bare adjective ("Marska is wary") is no
#    longer caught. Accepted — same measurement, same conclusion as the
#    category-2 removal above.
_TARGET_RESISTANCE = re.compile(
    r"\bnot\s+(?:stupid|foolish|gullible|slow|careless|easily\s+fooled)\b|"
    r"\bhard\s+to\s+(?:read|fool|convince|persuade)\b|"
    r"\bsharp-eyed\b|\bquick[- ]witted\b|"
    r"\bon\s+(?:her|his|their|your)\s+guard\b|\bno\s+fool\b",
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
# The genuine down-cue (SKILL.md: "down — theater of the mind"), exempt from
# map-list membership. Anchored at the start so a real map handle that merely
# starts with "down" (downfall-ruins, downtown-docks) is NOT exempted —
# `handle.lower().startswith("down")` used to swallow those. Tolerates an
# ASCII hyphen in place of the em-dash, and allows trailing free text after
# "theater of the mind" (the documented variant), but the literal phrase
# itself must be present.
_DOWN_CUE = re.compile(r"^down\s*[-—]\s*theater of the mind\b", re.I)

# ── first_use_gloss support data ───────────────────────────────────────────
# A maximal run of consecutive Title-Case words, joined by a single literal
# space (not `\s`) so a run never crosses a newline — two capitalized words
# on adjacent lines must not accidentally merge into one bogus phrase.
# Apostrophes are deliberately excluded from the word class: "Vane's" and
# "King's" tokenize as "Vane"/"King", which both strips possessives for free
# and avoids inventory keys keyed on a raw possessive form.
_TITLE_WORD = r"[A-Z][a-zA-Z]*"
_TITLE_RUN = re.compile(r"%s(?:[ ]%s)*" % (_TITLE_WORD, _TITLE_WORD))

# A single leading determiner/possessive is stripped from a candidate phrase
# before it enters the inventory or is matched against it — this is the
# mechanism (not a stopword lexicon on the narration side) that keeps
# ordinary sentence-initial capitals ("The rain falls...") out of the
# inventory: "The Grey King" reduces to "Grey King", but "The" alone reduces
# to nothing and is discarded.
_LEADING_DETERMINERS = frozenset({
    "The", "A", "An", "This", "That", "These", "Those",
    "His", "Her", "Their", "Its", "My", "Your", "Our",
})
# Common English words that are still capitalized when sentence-initial and
# would otherwise cross the single-word frequency threshold in ordinary
# campaign prose (a stopword list is a fixed, deterministic exclusion — not
# a judgment call — so it stays mechanical per anti-pattern 10).
_COMMON_CAPITALIZED_STOPWORDS = _LEADING_DETERMINERS | frozenset({
    "He", "She", "They", "You", "We", "I", "It",
    "But", "And", "So", "If", "When", "While", "Where", "What",
    "Why", "How", "There", "Then", "Yes", "No", "Well", "Now",
    "Not", "Or", "As", "At", "By", "For", "From", "In", "Of",
    "On", "To", "With",
})
# Bold markdown field labels ("**Location:**", "**Notable abilities:**") and
# markdown section headers are template scaffolding, not campaign prose —
# stripped before candidate extraction so words like "Location" or "World
# Foundations" never enter the inventory.
_BOLD_LABEL = re.compile(r"\*\*[A-Za-z][A-Za-z /'\-]*?:\*\*")
_HEADER_LINE = re.compile(r"(?m)^#{1,6}\s+.*$")
# The three fixed per-NPC profile subsection headers (templates/npcs.md) —
# excluded from the "### <Name>" structural-name pass.
_NPC_SUBSECTION_HEADERS = frozenset({"personality", "relationships", "notes"})
# The two mechanical gloss signals (design-fixed, deliberately not extended):
# an indefinite-article noun phrase ("a sign reading...", "a grey-cloaked
# officer") or explicit naming vocabulary ("called X", "known as X").
_GLOSS_NAMING_VOCAB = re.compile(r"\b(?:called|named|known\s+as)\b", re.I)
_GLOSS_INDEFINITE_NOUN = re.compile(r"\b(?:a|an)\s+([a-z]+)", re.I)
# "a/an" immediately followed by one of these is almost always an idiom
# ("without a word", "in a moment"), not the start of a descriptive
# apposition — excluded so the indefinite-article signal doesn't fire on
# every sentence containing ordinary filler and defeat the detector
# entirely. A fixed, enumerated list, not a judgment call.
_GLOSS_FILLER_NOUNS = frozenset({
    "word", "moment", "bit", "while", "second", "chance", "beat", "breath",
    "look", "glance", "step", "point", "sound", "sight", "thing", "little",
    "few", "couple", "way", "turn",
})


def _has_gloss_signal(sentence: str) -> bool:
    """Either mechanical gloss signal, present anywhere in `sentence`."""
    if _GLOSS_NAMING_VOCAB.search(sentence):
        return True
    for m in _GLOSS_INDEFINITE_NOUN.finditer(sentence):
        if m.group(1).lower() not in _GLOSS_FILLER_NOUNS:
            return True
    return False


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


def check_pc_auto_roll(text: str, roll_mode: str,
                       pc_names: set[str] | frozenset[str] = frozenset()) -> list[dict]:
    """Resolved PC roll lines under roll_mode: players.

    Two shapes: the legacy bold `**Roll:** … d20 … →` line (kept — NPC rolls
    in that format also land in the log, the excerpt lets the reviewer
    judge), and the house format `<Name> — <Skill>: d20+N = M`, attributed
    by PC name at line start against `pc_names` (lowercased, from
    campaign_pc_names). A resolved line starting with an NPC name passes.
    """
    if roll_mode != "players":
        return []
    pc_line = None
    if pc_names:
        pc_line = re.compile(
            r"^\s*\**(?P<who>%s)\b\**\s*[—–:,-]"
            % "|".join(re.escape(n) for n in sorted(pc_names)),
            re.I)
    out = []
    for line in text.splitlines():
        if _RESOLVED_ROLL_LINE.search(line):
            kind = ("skill check" if _SKILL_PAREN.search(line)
                    else "save" if re.search(r"\bsave\b|saving throw", line, re.I)
                    else None)
            if kind is not None:
                out.append({"detector": "pc_auto_roll",
                            "detail": f"resolved {kind} roll line under roll_mode: players",
                            "excerpt": _excerpt(line)})
                continue
        if pc_line and _RESOLVED_D20.search(line):
            m = pc_line.match(line)
            if m:
                out.append({"detector": "pc_auto_roll",
                            "detail": f"resolved roll line attributed to PC "
                                      f"{m.group('who').strip('* ')} under "
                                      f"roll_mode: players",
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
        if _DOWN_CUE.match(handle):
            continue
        if handle.lower() not in map_handles:
            out.append({"detector": "unknown_cue",
                        "detail": f"map cue not on map-list: {handle!r}",
                        "excerpt": _excerpt(m.group(0))})
    return out


def _line_kind(line: str) -> str:
    """Classify a line for first_use_gloss purposes: the canonical cue-block
    lines (🔊/🗺) are exempt outright; NPC dialogue (blockquoted per
    SKILL.md's `> **Name:** "..."` format) introduces a name without needing
    a gloss (SKILL.md: "once an NPC says the name out loud, it's the
    character's too"); everything else is ordinary narration."""
    if _SOUND_CUE.search(line) or _MAP_CUE.search(line):
        return "cue"
    if line.lstrip().startswith(">"):
        return "dialogue"
    return "narration"


def _sentence_window(text: str, start: int, end: int) -> str:
    """The sentence containing text[start:end), bounded to the current
    paragraph (mirrors _roll_lead_in_window's paragraph bound) — "the SAME
    SENTENCE (or the immediately adjacent clause)" that a gloss must land
    in. A dash- or comma-set-off appositive clause is still part of the same
    sentence, so this covers both gloss-before-name and gloss-after-name
    shapes without extra machinery (anti-pattern 1)."""
    para_start = text.rfind("\n\n", 0, start)
    para_start = 0 if para_start == -1 else para_start + 2
    para_end = text.find("\n\n", end)
    para_end = len(text) if para_end == -1 else para_end
    para = text[para_start:para_end]
    rel_start, rel_end = start - para_start, end - para_start
    sent_start = 0
    for m in re.finditer(r"[.!?]\s+", para):
        if m.end() <= rel_start:
            sent_start = m.end()
        else:
            break
    sent_end = len(para)
    for m in re.finditer(r"[.!?](?=\s|$)", para):
        if m.start() >= rel_end:
            sent_end = m.start() + 1
            break
    return para[sent_start:sent_end].strip()


def _match_inventory(phrase: str, inventory: dict[str, str]):
    """Longest contiguous sub-phrase of `phrase` (a maximal Title-Case run)
    that matches the inventory, case-insensitively — tried longest-to-
    shortest so "The Grey King" matches the inventory's "Grey King" rather
    than missing entirely or matching a shorter accidental substring.
    Returns (lowercase_key, canonical_display) or (None, None)."""
    words = phrase.split(" ")
    n = len(words)
    for length in range(n, 0, -1):
        for start in range(0, n - length + 1):
            key = " ".join(words[start:start + length]).lower()
            if key in inventory:
                return key, inventory[key]
    return None, None


def check_first_use_gloss(text: str, inventory: dict[str, str],
                          seen_names: set[str] | frozenset[str] = frozenset(),
                          pc_names: set[str] | frozenset[str] = frozenset()
                          ) -> tuple[list[dict], set[str]]:
    """Every campaign name's first use in narration must be glossed in the
    same breath (SKILL.md: "naming and glossing are one act, not a name plus
    a tax"). Mechanical throughout — no AI-judgment step (anti-pattern 10):
    `inventory` is pre-built by build_name_inventory from the campaign's own
    world.md/npcs.md, and the two gloss signals (_GLOSS_SIGNAL) are fixed,
    enumerated regexes, not a hedge lexicon that grows to fit fixtures.

    Returns (findings, encountered) where `encountered` is every inventory
    name matched in this turn (lowercase keys) — first use or not, dialogue
    or narration — for the caller to fold into the per-campaign ledger
    (`seen_names` is read-only here; the ledger write itself is the
    caller's job, run_and_log/main). Empty inventory means the detector is
    silently inert (no world.md/npcs.md to check against) and both return
    values are empty — the caller records that distinctly from "checked and
    clean" (see save_seen_names' has_inventory flag).

    Exclusions: a name already in `seen_names` (or already claimed earlier
    in this same turn) never re-fires — the rule fires once per name. A
    name in `pc_names` is skipped outright (not even added to the ledger) —
    PCs are never subject to this NPC/place/faction rule. So is a bare
    single word matching one *token* of a PC's full name (`campaign_pc_names`
    only returns full names, e.g. "talla vane", but narration naturally uses
    the bare first name, "Talla") — this only exempts a single-token
    inventory match ("talla"), never a multi-word one ("ash hollow" is not
    exempted just because a PC is "Ash Meridan"), so an unrelated inventory
    name that happens to share a PC's first/last name still counts normally.
    Cue-block lines (🔊/🗺) are not scanned. A name whose first occurrence in
    the turn falls inside an NPC dialogue block (a line starting with `>`)
    is registered as introduced but never gloss-checked — an NPC saying the
    name aloud is itself the in-fiction introduction.
    """
    if not inventory:
        return [], set()
    pc_tokens = {tok for name in pc_names for tok in name.split()}
    findings: list[dict] = []
    newly_seen: set[str] = set()
    for m in _TITLE_RUN.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        line_end = len(text) if line_end == -1 else line_end
        kind = _line_kind(text[line_start:line_end])
        if kind == "cue":
            continue
        key, canonical = _match_inventory(m.group(0), inventory)
        if not key or key in pc_names or (" " not in key and key in pc_tokens):
            continue
        if key in seen_names or key in newly_seen:
            continue
        newly_seen.add(key)
        if kind == "dialogue":
            continue  # said aloud by an NPC — introduced, no gloss required
        sentence = _sentence_window(text, m.start(), m.end())
        if not (sentence and _has_gloss_signal(sentence)):
            findings.append({
                "detector": "first_use_gloss",
                "detail": f"first use of campaign name {canonical!r} "
                          f"without a gloss in the same sentence",
                "excerpt": _excerpt(sentence) if sentence
                           else _excerpt(text, m.start()),
            })
    return findings, newly_seen


# ── narration_band support ─────────────────────────────────────────────────
# SKILL.md Standard 4 ("Length follows the scene's heat"): Hot ~40-60 words
# with at most one new name, Normal ~80-100 words with two or three new names
# (three is the cap), Breathe unbounded. Heat/scene-transition is not
# mechanically decidable from arbitrary mid-session text, and Breathe has no
# upper bound, so a hard word-cap finding on an ordinary turn would false-fire
# on a legitimate Breathe scene. This fires ONLY on the session-opening turn
# (see is_first_turn) — the one place the arithmetic is unambiguous: a
# session always opens hot or normal, never mid-Breathe.
_NARRATION_BAND_TOLERANCE_DENOM = 20  # 5% — see check_narration_band's docstring


def _narration_word_count(text: str) -> int:
    """Narration words in `text`, excluding NPC dialogue/tutor lines
    (blockquoted, `_line_kind` == "dialogue" — SKILL.md formats both
    `> **Name:** "..."` and `> ◈ Tutor: ...` this way), cue-block lines
    (`_line_kind` == "cue"), and resolved roll/mechanics lines (the bold
    `**Roll:** … d20 … →` shape and the house `d20+N = M` shape — the same
    two shapes check_pc_auto_roll already matches). A roll *request*
    ("Make a Perception check") is left in — it's narration prose asking
    for a roll, not the resolved mechanics themselves."""
    words = 0
    for line in text.splitlines():
        if _line_kind(line) != "narration":
            continue
        if _RESOLVED_ROLL_LINE.search(line) or _RESOLVED_D20.search(line):
            continue
        words += len(line.split())
    return words


def check_narration_band(word_count: int, is_opening_turn: bool,
                         new_name_count: int | None) -> list[dict]:
    """Mechanized SKILL.md Standard 4, session-opening turn only.

    `new_name_count` is the count of inventory names newly introduced this
    turn (see check_first_use_gloss's `encountered` return) — None when no
    campaign name inventory exists, in which case the name-count is unknown
    and the most permissive cap (100, Normal) applies rather than silently
    skipping the check.

    Bands (SKILL.md): <=1 new name -> Hot, 60-word cap; 2-3 new names ->
    Normal, 100-word cap; more than 3 -> its own finding ("three is the
    cap" — SKILL.md's explicit ceiling on an opener's names), independent
    of word count, since the prose defines no length band for that case at
    all.

    Tolerance: SKILL.md says "roughly" 40-60 / 80-100, so a small overage is
    permitted — 5% of the cap (60 -> 63, 100 -> 105), not the 10% a first
    read of "roughly" might suggest: 10% would not have caught the real
    observed failure shape (a 109-word opener against the 100-word cap;
    109 <= 110), so the tolerance was tightened until it did.
    """
    if not is_opening_turn:
        return []
    if new_name_count is not None and new_name_count > 3:
        return [{
            "detector": "narration_band",
            "detail": f"session-opening turn introduces {new_name_count} "
                      f"new names — three is the cap (SKILL.md Standard 4)",
            "excerpt": "",
        }]
    if new_name_count is None:
        cap, basis = 100, "no name inventory — most permissive cap applied"
    elif new_name_count <= 1:
        cap, basis = 60, f"{new_name_count} new name(s), Hot band"
    else:
        cap, basis = 100, f"{new_name_count} new names, Normal band"
    threshold = cap + cap // _NARRATION_BAND_TOLERANCE_DENOM
    if word_count > threshold:
        return [{
            "detector": "narration_band",
            "detail": f"session-opening narration measured {word_count} "
                      f"words against a {cap}-word cap ({basis}; 5% "
                      f"tolerance applied)",
            "excerpt": "",
        }]
    return []


def lint_turn(text: str, flags: dict, ambient_handles: set[str],
              map_handles: set[str],
              pc_names: set[str] | frozenset[str] = frozenset(),
              name_inventory: dict[str, str] | None = None,
              seen_names: set[str] | frozenset[str] = frozenset(),
              gloss_seen_out: set[str] | None = None,
              is_opening_turn: bool = False,
              narration_words_out: list[int] | None = None) -> list[dict]:
    roll_mode = flags.get("roll_mode", "players")
    findings = []
    # rote_closer disabled 2026-07-21: 75% false-positive rate (9/12) in
    # empirical re-validation against freshly invented permitted prose — the
    # regex is register-blind, so an NPC closing a scene with a direct
    # question (a form SKILL.md recommends at a genuine decision point)
    # trips it (validation report). Function and unit tests kept.
    # findings += check_rote_closer(text)
    findings += check_dc_leak(text)
    findings += check_roll_not_final(text, roll_mode)
    # pc_auto_roll disabled 2026-07-21: false-fired (3/12) in empirical
    # re-validation, including an undocumented in-genre case — a house-format
    # PC initiative line ("Kestrel -- Initiative: d20+2 = 14") fires it even
    # though SKILL.md exempts initiative from roll_mode; the house-format
    # branch lacks a `kind` filter to exclude it (validation report).
    # Function and unit tests kept.
    # findings += check_pc_auto_roll(text, roll_mode, pc_names)
    findings += check_unknown_cue(text, ambient_handles, map_handles)
    new_name_count = None
    if name_inventory:
        gloss_findings, encountered = check_first_use_gloss(
            text, name_inventory, seen_names, pc_names)
        findings += gloss_findings
        if gloss_seen_out is not None:
            gloss_seen_out.update(encountered)
        new_name_count = len(encountered)
    # Word count is measured every pass, opener or not — Task 2's
    # proof-of-measurement for the health record (see run_and_log). Only
    # the finding itself is gated on is_opening_turn.
    word_count = _narration_word_count(text)
    if narration_words_out is not None:
        narration_words_out.append(word_count)
    findings += check_narration_band(word_count, is_opening_turn, new_name_count)
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


def campaign_pc_names(camp_dir: pathlib.Path) -> set[str]:
    """Lowercased PC names from `<campaign>/characters/*.md` filenames and
    `# ` headers. The ground truth for pc_auto_roll attribution."""
    names: set[str] = set()
    chars = camp_dir / "characters"
    if not chars.is_dir():
        return names
    for f in chars.glob("*.md"):
        stem = f.stem.replace("_", " ").replace("-", " ").strip()
        if stem:
            names.add(stem.lower())
        try:
            for line in f.read_text(encoding="utf-8",
                                    errors="replace").splitlines():
                line = line.strip()
                if not line.startswith("# "):
                    continue
                head = re.split(r"[—–(,:]|\s-\s", line[2:], maxsplit=1)[0]
                head = head.strip(" *")
                if head and len(head.split()) <= 4:
                    names.add(head.lower())
                break
        except OSError:
            pass
    return names


def _strip_structural_noise(text: str) -> str:
    """Remove markdown scaffolding (bold field labels, section headers) that
    would otherwise pollute the name inventory with template vocabulary
    ("Location", "Notable abilities", "World Foundations") rather than the
    campaign's own proper nouns."""
    text = _BOLD_LABEL.sub(" ", text)
    text = _HEADER_LINE.sub("", text)
    return text


def _npc_structural_names(npcs_text: str) -> set[str]:
    """Explicit NPC names from the index table's Name column and the
    `### <Name>` profile headers — structural ground truth, so no frequency
    threshold applies (a single-mention NPC is still a real name)."""
    names: set[str] = set()
    for raw in npcs_text.splitlines():
        line = raw.strip()
        m = re.match(r"^###\s+(.+)$", line)
        if m:
            head = m.group(1).strip(" *")
            if head and head.lower() not in _NPC_SUBSECTION_HEADERS:
                names.add(head)
            continue
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not cells or not cells[0]:
                continue
            first = cells[0]
            if first.lower() == "name" or set(first) <= set("-: "):
                continue
            names.add(first)
    return names


def _title_run_candidates(text: str) -> list[str]:
    """Every maximal capitalized-word run in `text`, each reduced by
    stripping a single leading determiner/possessive (see
    _LEADING_DETERMINERS) — the mechanism that keeps "The Grey King" mapped
    to "Grey King" and "The" alone discarded."""
    out = []
    for m in _TITLE_RUN.finditer(text):
        words = m.group(0).split(" ")
        if words[0] in _LEADING_DETERMINERS and len(words) > 1:
            words = words[1:]
        if words:
            out.append(" ".join(words))
    return out


def build_name_inventory(camp_dir: pathlib.Path) -> dict[str, str]:
    """Campaign name inventory for first_use_gloss: {lowercase phrase: the
    canonical (first-seen) display form}, drawn from the campaign's own
    world.md / npcs.md / npcs-full.md — never from AI judgment
    (anti-pattern 10).

    Two sources, combined:
    - Structural (npcs.md, npcs-full.md): index-table Name column and
      `### <Name>` profile headers — included unconditionally.
    - Prose frequency (both files, bold labels and headers stripped first):
      any capitalized *multi*-word phrase is included unconditionally (two
      Title-Case words in a row is already a strong proper-noun signal); a
      bare single capitalized word is included only if it recurs at least
      twice across the source files and isn't a common English function
      word (_COMMON_CAPITALIZED_STOPWORDS) — this is what filters out
      incidental sentence-initial capitals mechanically, without needing
      any judgment about what's "really" a name.

    Returns {} when world.md and npcs.md are both absent/unreadable — the
    detector goes silently inert in that case (see check_first_use_gloss
    and save_seen_names' has_inventory flag).
    """
    structural: set[str] = set()
    prose_parts: list[str] = []
    found_any_file = False

    world = camp_dir / "world.md"
    if world.exists():
        try:
            prose_parts.append(world.read_text(encoding="utf-8", errors="replace"))
            found_any_file = True
        except OSError:
            pass

    for fname in ("npcs.md", "npcs-full.md"):
        f = camp_dir / fname
        if not f.exists():
            continue
        try:
            raw = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        found_any_file = True
        structural |= _npc_structural_names(raw)
        prose_parts.append(raw)

    if not found_any_file:
        return {}

    inventory: dict[str, str] = {}
    for name in structural:
        inventory.setdefault(name.lower(), name)

    prose = _strip_structural_noise("\n\n".join(prose_parts))
    single_word_counts: dict[str, int] = {}
    for phrase in _title_run_candidates(prose):
        words = phrase.split(" ")
        if len(words) > 1:
            inventory.setdefault(phrase.lower(), phrase)
        else:
            single_word_counts[phrase] = single_word_counts.get(phrase, 0) + 1

    for word, count in single_word_counts.items():
        if count >= 2 and word not in _COMMON_CAPITALIZED_STOPWORDS:
            inventory.setdefault(word.lower(), word)

    return inventory


def load_seen_names(camp_dir: pathlib.Path) -> set[str]:
    """Lowercased names already recorded as introduced, from the per-campaign
    first_use_gloss ledger. Missing/corrupt ledger reads as empty — a fresh
    campaign or a lint-log wiped between sessions must not be treated as
    every name having already fired once (that would silently disable the
    detector, not fail safe toward it)."""
    f = camp_dir / SEEN_NAMES_LOG
    if not f.exists():
        return set()
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    seen = data.get("seen") if isinstance(data, dict) else None
    if not isinstance(seen, list):
        return set()
    return {str(s).lower() for s in seen}


def save_seen_names(camp_dir: pathlib.Path, seen: set[str],
                    has_inventory: bool) -> None:
    """Overwrite the per-campaign first-use ledger. `has_inventory` records
    whether this run had a name inventory to check narration against at
    all — so a reviewer reading the ledger can tell "no findings, inventory
    present, narration was clean" apart from "no inventory — the detector
    was inert this whole run" (the health/liveness distinction called for
    in the design; `.lint-health.jsonl` itself is owned by
    autosave_checkpoint.py, outside this script, so this ledger is the
    in-scope place to carry it). Best-effort: must not raise when the
    campaign dir is otherwise missing world.md/npcs.md."""
    f = camp_dir / SEEN_NAMES_LOG
    try:
        f.write_text(
            json.dumps({"seen": sorted(seen), "has_inventory": has_inventory}),
            encoding="utf-8")
    except OSError:
        pass


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


def is_first_turn(transcript_path: str | pathlib.Path) -> bool:
    """True when the turn just linted is the session's first — the anchor
    check_narration_band's hard findings need (see its docstring for why
    heat can't be decided from arbitrary text, but the opener always can).

    Anchor chosen: turn-boundary count in the transcript itself, reusing
    the same genuine-user-prompt test (_is_turn_boundary) all_turns already
    uses, rather than "first lint of this session_id" read from
    `.lint-health.jsonl`. That file is owned and appended-to by
    autosave_checkpoint.py (a sibling script, elsewhere in the hook
    pipeline) — coupling this detector's core arithmetic to it would make
    the anchor only as reliable as that file's completeness (a gap,
    rotation, or a session that never got a health record would silently
    mis-anchor). The transcript is the actual session record and is
    already what run_and_log/main are handed, so this needs no session_id
    at all and works identically for the CLI (--transcript, --backfill)
    and the hook path.

    Cost stays bounded on long sessions: scanning stops the moment a
    second boundary is found, so a turn deep into a session (long since
    past two boundaries) returns False in the time it takes to reach the
    second user message near the top of the file — not a re-read of the
    whole transcript. A missing/unreadable transcript reads as False (not
    the opening turn), the fail-safe direction: it costs a missed hard
    finding, never a false one on a turn that isn't actually the opener.
    """
    try:
        raw_lines = pathlib.Path(transcript_path).read_text(
            encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False
    boundaries = 0
    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except ValueError:
            continue
        if _is_turn_boundary(obj):
            boundaries += 1
            if boundaries >= 2:
                return False
    return True


# ── Hook entry point ──────────────────────────────────────────────────────

def run_and_log(stdin_obj: dict, campaign: str,
                health_out: dict | None = None) -> int:
    """Lint the turn in `transcript_path` and append findings to the campaign
    log. Returns the number of findings. Never raises, never prints.

    `health_out`, when given, is populated with `gloss_inventory` (bool) and
    `narration_words` (int) once they're actually measured — left untouched
    on any early return or exception, so the caller (autosave_checkpoint.py's
    `.lint-health.jsonl` heartbeat) can tell "measured, value X" apart from
    "never got far enough to measure" (anti-pattern 2)."""
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
        pc_names = campaign_pc_names(camp_dir)
        inventory = build_name_inventory(camp_dir)
        seen_names = load_seen_names(camp_dir)
        gloss_seen: set[str] = set()
        narration_words: list[int] = []
        is_opening = is_first_turn(transcript)
        findings = lint_turn(text, flags, ambient, maps, pc_names,
                             inventory, seen_names, gloss_seen,
                             is_opening_turn=is_opening,
                             narration_words_out=narration_words)
        save_seen_names(camp_dir, seen_names | gloss_seen, bool(inventory))
        if health_out is not None:
            health_out["gloss_inventory"] = bool(inventory)
            if narration_words:
                health_out["narration_words"] = narration_words[0]
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
    except Exception as exc:
        # A lint failure must never break the Stop hook — but a mid-body
        # crash must be distinguishable from a clean turn in the file the
        # reviewer already reads. Best-effort; the caller's heartbeat in
        # autosave_checkpoint covers the import-death case this can't.
        try:
            camp_dir = paths.find_campaign(campaign)
            ts = datetime.datetime.now(datetime.timezone.utc).isoformat(
                timespec="seconds")
            with open(camp_dir / LOG_NAME, "a", encoding="utf-8") as f:
                f.write(json.dumps(
                    {"ts": ts, "session_id": stdin_obj.get("session_id"),
                     "campaign": campaign, "detector": "lint_error",
                     "detail": f"{type(exc).__name__}: {exc}"[:200]},
                    ensure_ascii=True) + "\n")
        except Exception:
            pass
        return 0


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
        pcs = campaign_pc_names(camp_dir)
        inventory = build_name_inventory(camp_dir)
        seen_names = load_seen_names(camp_dir)
        turns = all_turns(args.transcript)
        total = 0
        for i, text in enumerate(turns, 1):
            gloss_seen: set[str] = set()
            # Turn 1 of the (whole-session) backfill list is, by
            # construction, the session's opening turn.
            findings = lint_turn(text, flags, ambient, maps, pcs,
                                 inventory, seen_names, gloss_seen,
                                 is_opening_turn=(i == 1))
            seen_names = seen_names | gloss_seen
            total += len(findings)
            for v in findings:
                print(f"turn {i:>3}  {v['detector']}: {v['detail']}")
                print(f"          {v['excerpt']}")
        save_seen_names(camp_dir, seen_names, bool(inventory))
        rate = (total / len(turns)) if turns else 0.0
        print(f"\n{len(turns)} turns · {total} findings · {rate:.2f} per turn")
        return 0

    text = last_turn(args.transcript)
    if not text.strip():
        print("(no assistant turn found in transcript)")
        return 0
    ambient, maps = asset_handles(camp_dir)
    pcs = campaign_pc_names(camp_dir)
    inventory = build_name_inventory(camp_dir)
    seen_names = load_seen_names(camp_dir)
    gloss_seen: set[str] = set()
    findings = lint_turn(text, session_flags(camp_dir), ambient, maps, pcs,
                         inventory, seen_names, gloss_seen,
                         is_opening_turn=is_first_turn(args.transcript))
    save_seen_names(camp_dir, seen_names | gloss_seen, bool(inventory))
    if not findings:
        print("clean: no findings")
        return 0
    for v in findings:
        print(f"{v['detector']}: {v['detail']}\n    {v['excerpt']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

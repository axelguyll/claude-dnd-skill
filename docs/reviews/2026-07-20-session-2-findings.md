# Session 2 — hook postmortem + play findings

Date: 2026-07-20 · Campaign: the-honest-map · Transcript: `8900c3ea` (17 DM turns)
Fix commit: `03ca0d7`

---

## Part 1 — Postmortem: the hook never ran

**Repro command** (the one-liner everything below was answerable from):

```powershell
python3 --version   # CommandNotFoundException in PowerShell; works in Git Bash
```

**Root cause.** `install_autosave_hook.py:38` hardcoded `python3` as the hook
interpreter. Claude Code executes Stop hooks in the Windows shell, where `python3`
does not resolve — Git Bash ships a shim, PowerShell does not. The hook exited
CommandNotFound on every turn of a full playthrough.

**Why it stayed invisible.** Three independent maskings, all of which have to be
understood or this recurs:

1. The hook is silent by design. A non-zero exit produces no user-facing output.
2. `state.md` kept updating, because the DM skill saves in-turn. The one artifact
   a human would glance at to confirm "the hook is working" is written by a
   different code path entirely.
3. `turn_lint.run_and_log` wraps its body in `except Exception: return 0`. Correct
   for a lint that must never break play, but it erases the distinction between
   "clean turn" and "crashed" — during diagnosis this had to be bypassed manually.

**Earlier signal — what would have caught it.** `install_autosave_hook.py` had
**zero tests**. Not thin coverage; none. The 377 tests that passed at wave 2 all
call `turn_lint` in-process, so they exercised the module and never the installed
command string. The new `tests/test_install_autosave_hook.py` asserts the emitted
interpreter is an existing absolute executable — that assertion fails against the
old code.

**Architecture flag.** Real, and worth naming: the project verifies through the
Bash tool but ships to a PowerShell harness. Every command string this repo writes
into a config file for something *else* to execute is exposed to the same class of
bug, and no test covers that seam generally. `sys.executable` fixes this instance;
it does not fix the category.

**Process failure, separate from the code.** Wave 2 was reported as "verified
end-to-end" on the strength of an in-process import test. That claim was not
warranted. The end-to-end check that mattered — pipe realistic Stop-hook JSON into
the exact installed command, in the harness's own shell — took one command and was
not run until today.

---

## Part 2 — The detectors found nothing. The player found four things.

Backfill over the full session:

```
17 turns · 0 findings · 0.00 per turn
```

Verified as a true negative, not a broken pipeline: injecting a known-bad string
into real turn text fires `rote_closer` and `dc_leak` as expected.

Meanwhile the player, reading the same 17 turns by hand, logged four defects. The
five detectors caught **none** of them, because none of the five were aimed at
these failure modes.

| # | Defect | Turn | Detector? |
|---|--------|------|-----------|
| 1 | Disadvantage declared *after* the roll came back | 4→5 | none |
| 2 | Voice register — "chain mail doesn't do quiet" | 6 | none (deliberately) |
| 3 | Knowledge leak — Warden's identity, "the drift the ledger's been hinting at" | 6, 16 | none |
| 4 | Intra-turn contradiction — Ostley "doesn't move to stop him", then offered "push past Ostley" | 6 | none |

### 1. Late disadvantage (rules gap, mechanically significant)

Turn 4 called for a Dexterity (Stealth) check. The player rolled 4. Turn 5 *then*
introduced disadvantage from chain mail and asked for a second d20.

The roll request correctly ended the turn, so `roll_not_final` is silent — the
existing rule is satisfied. The defect is upstream: the DM did not check the
character's own equipment before setting the terms of the roll. Adjusting terms
after seeing a number is the same class of failure as the roll-order rule
(SKILL.md:298) even though the prose doesn't reach it.

Chain mail's Stealth disadvantage is a static property of the equipped armor —
knowable before any roll, from the character sheet. SKILL.md:221 covers voicing an
*active condition's* mechanical effect, but equipment is not a condition, so
nothing in the prose requires the pre-check.

Mitigating and worth recording: by turn 9 the DM pre-declared it correctly
("disadvantage still applies from the armor: two d20s, lower one counts"). The
failure was first-instance, not persistent.

**Fix:** prose — before calling for any PC roll, check equipped armor for the
Stealth disadvantage property and state advantage/disadvantage *in the same breath
as the roll request*. Cheap, deterministic, and detectable later.

### 2. Voice register (adherence, third occurrence)

"Chain mail doesn't do quiet" and "easy smile a beat too careful" are the
novelistic register the voice rule was written against — the same failure as
session 1, now with the rule in place and caveman off. This is the third
independent confirmation that prose alone does not hold this one.

Still recommend **not** building a "too literary" blocking detector; false-positive
risk on good prose is high and the failure is aesthetic, not mechanical.

### 3. Knowledge leak — the significant new finding

Two instances, one self-caught:

- Turn 6: "the Warden's cloak is already rounding the corner" — Holg had no way to
  identify her as the Warden at that point.
- Turn 16: "the drift the ledger's been hinting at" — Holg has never seen the
  ledger. When challenged, the DM conceded immediately and correctly, citing the
  only thing Holg actually has (Tomas Wick's line).

This is the highest-value gap found. Reasons:

- It corrupts play state, not just tone. A player acting on knowledge the character
  shouldn't have makes decisions the fiction can't justify.
- The DM **can** detect it — turn 17 is a clean unprompted diagnosis once asked.
  A failure the model self-diagnoses on demand is one a rule can plausibly hold.
- It is invisible to the player exactly when it matters most; they cannot audit
  what their own character is supposed to know.

**Fix:** prose first — before naming any person, place, or fact in narration, check
it against what the PC has actually witnessed or been told this campaign; refer to
the unknown by description ("a cloaked figure"), never by name. A detector is
plausible later (proper nouns in DM narration cross-checked against the campaign
graph's PC-known set) but should not be attempted before the prose rule has a
session or two to prove itself.

### 4. Intra-turn contradiction

Turn 6 states Ostley "doesn't move to stop him", then closes by offering "push past
Ostley, or deal with the man" — an option the same paragraph established as
unnecessary. Low severity, but it is a distinct category: the turn contradicting
itself between narration and the closing options.

---

## What this changes

The measurement plan assumed the lint would be the evidence base and the player's
impressions would corroborate it. That is backwards. This session the lint scored
0.00/turn while the session contained four real defects — a decision made on lint
data alone would have concluded "rules are holding, skip the wrapper," which is
precisely wrong.

The five detectors are not useless; they cover the session-1 failure modes, and
those modes did not recur. But detector silence is not evidence of a clean session.

**Revised sequence:**

0. ~~Fix the hook~~ — done (`03ca0d7`). Live data collection starts next session.
1. Prose patches for #1 (equipment-before-roll) and #3 (PC knowledge boundary).
   Both are cheap, and #3 is the one that corrupts play.
2. Keep hand-notes as the primary signal for at least two more sessions. They
   outperformed the instrumentation on its first real trial.
3. Consider a `knowledge_leak` detector only after the prose rule has been tested.
4. Wrapper decision stays deferred, and the criterion changes: hand-logged defect
   rate, not lint-logged.

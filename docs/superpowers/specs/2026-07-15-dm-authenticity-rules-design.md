# DM Authenticity Rules — Design

**Date:** 2026-07-15
**Status:** Approved, pre-implementation
**Scope:** Six adjudication rules that make play *feel* like a real 5e table. Five are
prose edits to `skills/dnd/SKILL.md`. One (rule 4a) also carries a small `dice.py`
change, because the mislabel it fixes lives in the script, not the prompt. Kept as a
**separate spec from the voice overhaul** (`2026-07-15-dm-voice-overhaul-design.md`) so
the two review cleanly apart: voice governs *how the DM writes*; this governs *how the
DM adjudicates*.

## Motivation

The voice overhaul made narration read cleanly aloud. It did not touch *rulings*. Six
places where the DM currently plays looser than a competent human DM would:

1. **Yes-botting phantom fiction.** A player references an item they don't have or
   attacks an enemy who isn't present, and the DM invents it into being rather than
   treating the inventory/roster as ground truth.
2. **Stating DCs.** Nothing forbids narrating "that's a DC 15" — which no human DM says
   aloud; the number lives behind the screen.
3. **Reflexive rolls.** A check gets called because the player used a skill verb, not
   because failure has a stake. Real DMs let no-stakes actions just happen.
4. **Nat 1/20 mishandled + flat dead-ends.** Two problems bundled: (a) `dice.py` asserts
   `*** CRITICAL HIT ***` / `*** FUMBLE ***` on *every* nat 20/1 including ability
   checks and saves, where RAW gives no auto-success/fail; and (b) a failed check often
   dead-ends the scene instead of complicating it forward.
5. **Silent conditions.** Poisoned/frightened/prone are tracked but never voiced, and
   when they are, the DM describes the effect without naming the dice the player must
   actually roll.

Governing test, same as the voice spec: **would this ruling read as authentic to
someone who has played 5e at a real table?**

## Design

Six rules (1, 2, 3, 4a, 4b, 5). Homes verified against post-teardown SKILL.md line
numbers (SKILL.md was re-flowed by both the voice overhaul and the display teardown —
old refs are stale).

### Rule 1 — Refuse phantom items/enemies (Narration principles, `SKILL.md:195`)

Inventory (`characters/<PC>.md → sheet`) and the live encounter roster are ground truth.
When a player invokes an item they don't have or acts on an enemy who isn't present, the
DM does not conjure it — it redirects *in fiction*, never as a rules-lawyer aside.

> **Inventory and the enemy roster are ground truth — don't yes-bot fiction that
> contradicts them.** If the player invokes an item they don't have, or acts on an enemy
> who isn't present, don't invent it into being. Check the PC sheet / the encounter
> roster first, then redirect in fiction: *"You reach for a torch — but your pack's been
> empty since the crossing."* Never break frame to explain the inventory; just play the
> world honestly.

### Rule 2 — Hidden DCs (Standard 7 "Be Fair and Consistent", `SKILL.md:112`)

The player hears the world, not the math. The old `--dc` display-leak concern is **moot**
— the teardown deleted the phone that could have surfaced a number. This is now purely a
"never say the number aloud" prose rule.

> **Never state the DC.** The player doesn't hear a target number — they hear the world.
> Call for the roll, take the result, and narrate success or failure in fiction (*"the
> lock gives"* / *"it won't budge"*). The DC stays behind the screen, always — before
> the roll and after it.

### Rule 3 — Context-driven roll necessity (Dice convention, `SKILL.md:261`)

Stakes and opposition decide whether dice come out — not the player's phrasing.

> **Stakes decide whether a roll happens — not the player's wording.** No meaningful
> failure state and nothing actively opposing them → no roll; narrate it done (glancing
> around a safe tavern, recalling common lore). Call for a check only when failure costs
> something or a force actively resists. Don't reflexively roll because the player used a
> skill verb.

### Rule 4a — Nat 1/20 by roll type + `dice.py` fix (Dice convention, `SKILL.md:261`; `dice.py`)

RAW, confirmed (Crawford / SRD): nat 1/20 are automatic **only on attack rolls**. On
ability checks and saving throws they are merely the die's extremes — modifier applies,
compare to DC, no auto-result. A non-natural 20 (e.g. 14+6) is mechanically identical to
a nat 20 on a check; there is no auto-success either way.

**Prose (SKILL.md):**

> **Natural 1 and 20 are automatic only on attack rolls.** On an attack, nat 20 auto-hits
> and crits (double the damage dice), nat 1 auto-misses — ignoring modifiers and AC. On
> **ability checks and saving throws, a nat 20 or nat 1 is just the die's high or low
> end**: apply the modifier, compare to the DC, no automatic success or failure. You may
> still *narrate* a nat 20 as stylish or a nat 1 as clumsy, but the DC math stands.

**Script change (`dice.py`):** today `run()` unconditionally prints
`*** CRITICAL HIT (nat 20)! ***` / `*** FUMBLE (nat 1)! ***` on any single d20
(`dice.py:96-99`). Since attacks route through `combat.py` (which rolls its own d20 and
owns its own crit flag at `combat.py:106`), dice.py's d20s are almost always checks and
saves — exactly where those labels are wrong. Change: **dice.py defaults to a neutral
`(nat 20)` / `(nat 1)` note with no crit/fumble claim; add an `--attack` flag that
restores the `CRITICAL HIT` / `FUMBLE` wording** for the rare ad-hoc NPC attack rolled
straight through dice.py. combat.py is unchanged (its crit handling is already
attack-context-correct — verify at implementation that its flag is nat-20-gated, not
total-gated).

### Rule 4b — Fail-forward, with a puzzle carve-out (Standard 7, `SKILL.md:112`)

A failed *check* complicates forward. But this explicitly does **not** extend to puzzles
or player-reasoning challenges — a wrong attempt at a puzzle simply doesn't work, and the
DM offers no consolation hint. Some things are meant to be figured out.

> **A failed roll complicates — it doesn't dead-end — but never hand a hint to a problem
> meant to be solved.** For checks with a stake (a lock, a climb, a persuasion), failure
> moves the scene sideways: partial success at a cost, the goal at a price, or a fresh
> problem — not "nothing happens." **But this does not apply to puzzles or reasoning
> challenges:** an action that doesn't solve the puzzle simply doesn't solve it, with no
> consolation clue and no nudge. Working it out is the game. Use degree of failure as the
> lever — a nat 1 that also misses the DC earns the harsher complication; a near-miss
> earns the softer cost.

### Rule 5 — Voice conditions and name the dice (Narration principles, `SKILL.md:195`; per-turn combat step d, `SKILL.md:281`)

A condition that alters a roll must be *voiced with its exact dice instruction*, not just
flavored. `dice.py` already implements advantage/disadvantage correctly (`dice.py:63-75`:
roll twice, take higher/lower; a single boolean, so no stacking). The DM's job is to
**net the sources out before speaking** (advantage and disadvantage don't stack; one of
each cancels to a single flat d20) and then say the cause and the instruction in one
plain line.

> **Voice an active condition's mechanical effect and name the dice — don't just flavor
> it.** When a condition changes an actor's roll, say the cause and the exact instruction
> together. `roll_mode: players`: *"The venom still burns — roll two d20 for the attack
> and take the lower. That's disadvantage."* `roll_mode: auto`: resolve it yourself via
> `dice.py "d20+X dis"` and show the math. Net the sources first: advantage and
> disadvantage never stack, and one of each cancels to a single flat d20. Voice it the
> first turn the condition applies and again whenever it changes the current roll — not
> every turn (that drones across long combats).

## What does not change

- combat.py, tracker.py, calendar.py, character.py, the turn loop — untouched. The only
  script edit is dice.py's crit/fumble labeling (rule 4a).
- Advantage/disadvantage *math* is already correct in dice.py; rule 5 adds no code.
- Voice-overhaul prose (persona, beat-cap, diction, speaker separation) is a separate
  spec and is not re-opened here.
- Per-campaign `## DM Style Notes` overrides still layer on top.

## Testing

Same content-assertion approach as `tests/test_prep_skill_prose.py::DMVoiceTests`. Add a
new guard class (e.g. `DMAuthenticityTests`) with one assertion per rule — each pins the
rule's presence against silent regression:

- Rule 1: `assertIn` the phantom-item/roster-ground-truth rule text.
- Rule 2: `assertIn` "Never state the DC"; `assertNotIn` any instruction to announce a DC.
- Rule 3: `assertIn` the stakes-decide-rolls text.
- Rule 4a: `assertIn` the nat-1/20-only-on-attacks rule.
- Rule 4b: `assertIn` both the fail-forward text and the puzzle carve-out.
- Rule 5: `assertIn` the name-the-dice / net-out-adv-dis text.

Plus a **dice.py behavioral unit test** (this rule has real code): assert a plain
`d20` roll that lands on 20/1 does **not** emit `CRITICAL HIT` / `FUMBLE`, and that the
same roll with `--attack` does. (Seed `random` or assert on the label branch.)

Then the real acceptance check — a **live read-through** across a few turns: a no-stakes
action (rule 3 → no roll), a failed lock check (rule 4b → complication), a failed puzzle
attempt (rule 4b carve-out → no hint), a poisoned attack (rule 5 → dice named), a
phantom-item reference (rule 1 → in-fiction refusal), and a nat-20 Perception check (rule
4a → no auto-success). This cannot be driven headless; flag it to the user as the human
sign-off.

## Out of scope

Table Cards and First-Timer/teaching framing (vault backlog, Bucket C) — deferred and
re-scoped post-teardown. The narration/NPC terminal-block *rendering* design (Bucket B)
is a separate open design decision, brainstormed and specced on its own.

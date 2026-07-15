# DM Voice Overhaul — Design

**Date:** 2026-07-15
**Status:** Approved, pre-implementation
**Scope:** Prose edits to `skills/dnd/SKILL.md` that change how the DM *writes and
speaks* narration at the table. No script/code-path changes. Play-time narration
only — prep-phase spine prose (authored `situation`/`what_changes` fields) is untouched.

## Motivation

A live playthrough surfaced that the DM narration reads like a novel, not like a
person running a game aloud. Concretely:

- **Too wordy per turn.** One pre-choice narration stacked six separate pressure
  points (house atmosphere + NPC state + a hanging quote + arrivals outside + a
  second NPC warning + a supernatural tell + a compound question) before the player
  could act.
- **Extreme vocabulary.** Words like *tallow*, *cadence*, *sexton*, *lintel* — novel
  words, not table words. A human reading them aloud stumbles and the player loses
  the thread. This is the single biggest readability problem.
- **Book-register sentences.** Noun fragments and dropped subjects (*"Outside: boots
  on the frozen mud, slowing"*) look sharp on a page but sound like a telegram aloud.
- **Monotone.** The persona hardcodes a "dark" tone, so every scene reads ominous
  regardless of what's happening.
- **Dialogue buried in prose.** NPC speech is inlined into the narration wall instead
  of standing on its own line.
- **Rote "What do you do?"** tagged onto the end of every turn — not how D&D is played;
  an open situation invites the player's response without a prompt.

This fork is read aloud by a human at the table (TTS is retired), so the governing
test throughout is: **would this read cleanly aloud to friends?**

## Design

Seven changes (A–G). Most hook into structure that already exists (the DM Standards,
the `## DM Style Notes` per-campaign override, the `send.py` typed-block model), so
this is prose, not plumbing.

### A. Rewrite the persona voice (`SKILL.md:24`)

Replace *"Your tone is dark, immersive, and descriptive — paint scenes with sensory
detail"* with a plain-spoken, friend-at-the-table voice. Relocate where "dark" comes
from: **the campaign theme sets what's at stake; the DM does not narrate in a fixed
mood.** This one line drives both the wordiness and the monotone today, so it is the
largest single lever.

### B. Beat-cap and dynamic length (Standard 4, `SKILL.md:89`; Standard 6, `SKILL.md:97`)

Standard 4 already preaches economy but has no enforcement. Add two rules:

- **Beat-cap:** a pre-choice narration delivers **at most ~3 moments** (a moment = one
  image, one event, or one line of dialogue that moves things). When more is happening,
  hold the rest back — they become the *next* beat after the player reacts. The scene
  does not fire every barrel at once.
- **Dynamic length by scene tempo** (anchored to Standard 6, "Control the Pace"):

  | Tempo | When | Target |
  |-------|------|--------|
  | **Hot** | combat, chase, a threat at the door, any "bang" | 1–2 moments, ~40–60 words, clipped |
  | **Normal** | conversation, investigation, travel | 2–3 moments, ~80–100 words |
  | **Breathe** | arriving somewhere new, a big reveal, downtime | up to 3 moments, longer OK |

  Length is not one fixed number; it follows the heat of the scene.

### C. Tone variety (folds into A; stated as its own rule)

The theme drives the arc's problems and stakes; **individual scenes vary freely in
mood** — warm, funny, mundane, tense. Ominous is a spike the DM *earns* at genuine
high-stakes beats, then relaxes back. NPCs have distinct personalities, not uniform
dread. Example: theme "a dying mining town" means the *problems* are grim (the mine is
cursed, people vanish) — but a scene can still be a bad-flirting tavern keeper, a kid
selling wrong directions, a warm fire and a card game, before the floor drops out.

### D. Plain spoken diction — the unslop layer (Standard 4)

Not just plain *words* — plain *sentences*:

- **Full subject–verb sentences**, said the way you'd say them aloud. No book-style
  noun fragments, colon-dumps, or dropped subjects.
- **Character-POV grounding:** narrate through what a character perceives —
  *"Tomm hears footsteps slowing as they come toward the gate,"* not a detached
  *"Outside: boots on the frozen mud."*
- **The read-aloud test:** if the human reading it would stumble on a word, or it
  sounds like a novel, swap for the plain version. *tallow → pale and grey;
  cadence → the same three slow knocks; sexton → the churchman.*

Implementation note: draw the concrete "AI/literary tell" list from the `unslop-text`
skill so the ban-guidance is grounded, not ad-hoc.

### E. Speaker separation (`SKILL.md:314`, `SKILL.md:320`, block order `SKILL.md:382`)

Narration and NPC speech go in **separate labeled blocks**. The `send.py --npc <name>`
block already exists and renders NPC dialogue distinctly; the block order already
places it after plain narration. The blocker is the current rule at `SKILL.md:320`:

> "Brief NPC interjections within narration don't need a separate block."

**Flip it:** NPC speech always gets its own `--npc` block, never inlined into narration
prose. (The old dm-app hit the exact failure this prevents: a trailing meta-line
inherited the last NPC's voice because it wasn't in a narrator segment.)

### F. No rote "What do you do?" (Standard 13 principle, `SKILL.md:126`; extends it to every turn-close)

Standard 13 already forbids "what do you do?" as dead air at scene *opens*. Extend that
to every turn-close:

- End on the **situation itself** — the NPC's line, the event, the pressure — and let
  the player respond naturally. No reflexive tag.
- Prompt explicitly **only at a genuine decision point**, and then with real options
  (*"Fight, or find another way out?"*), always leaving room (*"…or something else?"*).
  Vary the wording; never a rote question.
- **The steer is always narrator-voiced** — it goes in the plain narration block, never
  the `--npc` block. (This is the dm-app fix, `69cab6d`, verified 0/4 rote questions in
  live play.)

### G. Phonetic respelling of invented names (read-aloud aid)

When narration first introduces a hard-to-pronounce invented name, include a short
pronunciation hint the first time: *"Xanathar (zan-a-thar)."* Directly serves the
read-aloud premise and pairs with D. First-use only, not every mention.

## Worked example

The failing playthrough turn, rewritten under A–G (Hot tempo, plain diction, speakers
split, no rote prompt):

> **Narrator:** Tomm sits on the kitchen stool. He hasn't eaten in two days and his
> face has gone pale — but when he looks up at Sel, his eyes are his own again. Wet,
> scared, awake.
>
> **Tomm:** "You have to put me back. I'm not paid anymore."
>
> **Narrator:** Then Tomm hears footsteps outside, slowing down as they come toward the
> gate. Three slow knocks. He grabs Sel's sleeve.
>
> **Tomm:** "Don't let them take me back down. Not yet."
>
> **Narrator:** The latch starts to lift.

~75 words, no word to decode, dialogue on its own line, POV-grounded, ends on the
situation with no "What do you do?" The sexton-through-the-shutter, the aunt's warning,
and the voice-glitch tell are held for the *next* beats.

## What does not change

- No script/code-path changes. `send.py`, `combat.py`, `tracker.py`, the turn loop, and
  all `--stat-*` bundling are untouched.
- The per-campaign `## DM Style Notes` override still layers on top (a specific table
  can still ask for more atmosphere). No conflict.
- Prep-phase spine prose is out of scope.
- Authenticity rules (hidden DCs, context-driven rolls, fail-forward, phantom-item
  discipline, voicing conditions) are a **separate spec**, not this one. See the vault
  backlog note dated 2026-07-15.

## Testing

Prompt prose can't be unit-tested behaviorally, but it can be pinned against silent
regression, matching the existing `tests/test_prep_skill_prose.py` content-assertion
style. Add tests asserting:

- The persona no longer contains "dark, immersive" (Change A landed).
- The beat-cap / dynamic-length rule text is present (Change B).
- The plain-diction / read-aloud-test rule is present (Change D).
- The `--npc`-always rule is present and the old "don't need a separate block" line is
  gone (Change E).
- The steer-only-at-decisions / steer-is-narrator rule is present (Change F).
- The phonetic-hint rule is present (Change G).

Then a **live read-through**: run 2–3 narration turns across different tempos (a tense
scene, a warm conversation) and confirm they read aloud clean, dialogue is split, and
no rote prompt appears. This is the real acceptance check; the unit tests only prevent
silent reversion.

## Out of scope

Authenticity/adjudication rules, Table Cards, First-Timer framing, and proactive
condition-voicing are all logged in the vault backlog and handled in a later spec.

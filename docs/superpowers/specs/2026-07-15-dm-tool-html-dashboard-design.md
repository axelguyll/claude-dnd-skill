# DM-Tool HTML Dashboard — Design

**Date:** 2026-07-15
**Status:** Approved, pre-implementation
**Scope:** A host-facing (DM-side) HTML dashboard for `claude-dnd-skill`, delivered as
two self-contained local files with **no server**. Adds a live combat tracker, an
interactive asset hub (maps + ambient loops + SFX buttons), a third narration block type
(sound cue) that bridges chat to the hub, and a prep-phase pass that generates the asset
shopping lists from the sealed story spine. This is the concrete realization of the
deferred "Bucket B" (narration/NPC block rendering) plus the new asset-hub direction.

## Motivation

The display-companion teardown (2026-07-15) left the skill **terminal-only** on purpose —
it removed a ~14,200-line server/phone/network/audio stack that was too heavy and too
coupled. But it removed the *good idea* along with the apparatus: a place for the host to
see volatile combat state at a glance and to reach curated maps/sounds instantly.

Terminal chat is the source of truth and stays that way. Its weakness is combat: HP,
conditions, concentration, initiative, and death saves scroll away, and mid-fight the host
loses track of "whose turn, who's poisoned, how much HP the ogre has left." A DM screen
fixes exactly that — the way Roll20/Foundry give the GM an at-a-glance operator view.

**Audience is the host, not the players.** In this skill *Claude* is the DM; the human
host facilitates the physical table (places maps, plays sounds, reads the sealed map
list). This screen is the host's operator dashboard. It stays **operational, never
omniscient** — see the sealed-campaign constraint below.

**Governing test:** does the dashboard reduce table friction (state that scrolls away,
fumbling for the right sound) without leaking anything the host is meant to discover in
play?

## Hard constraints

1. **No server.** The old design died on a network layer. Everything here is a local file
   opened over `file://`.
   - `<audio>` and `<img>` **work** over `file://` with local relative paths — click-to-play
     SFX and looped ambient are fine.
   - `fetch()`/XHR of local files is **blocked** over `file://` (CORS). This is *why* the
     combat tracker uses whole-file regeneration instead of polling a JSON feed, and why
     chat→hub coupling is loose (below), not a live data channel.
   - Browser autoplay policy blocks sound without a user gesture — a non-issue here because
     every sound is triggered by a host **click**.
2. **Sealed campaign preserved.** The campaign (`spine.json`/`world.md`/`state.md`) is
   sealed from the host; the map list is currently the *only* prep artifact they read. The
   dashboard may show **combat operational state** (a facilitator sees HP/conditions) but
   must **never** surface plot, upcoming beats, secret DCs, or *why* an asset matters. The
   asset lists inherit the map list's rule: *describe the asset only, never the plot.*
3. **Manual out-of-combat tracking stays manual.** Gold and inventory are deliberately
   **out** — they change almost entirely out of combat and are a normal, wanted part of
   the tabletop experience. The dashboard tracks combat-volatile state only.
4. **Lean, script-driven, testable.** HTML is emitted by small deterministic render
   scripts (matching the existing `dice.py`/`combat.py`/`tracker.py` pattern), not
   hand-written by Claude each turn. Deterministic, unit-testable, token-cheap, drift-free.
   These are new *render* scripts — small templates, not a revival of the deleted stack.

## Architecture

Two files under the campaign directory (`~/.claude/dnd/campaigns/<name>/`), each opened in
its own browser tab:

| File | Nature | Generated | Holds | Regenerated |
|------|--------|-----------|-------|-------------|
| `assets.html` | **Static** | once at prep (+ when host adds files) | maps, ambient loops, SFX buttons | never during play |
| `tracker.html` | **Live** | each combat turn | initiative order, HP, conditions, concentration, death saves | every combat turn |

**Why two files, not one:** the tracker regenerates mid-combat. If audio lived in the same
file, each regen reload would **kill any playing ambient loop**. Splitting keeps the audio
file stable so loops survive; only the disposable tracker file churns.

Both files are optional augmentation. If the host never opens them, chat remains fully
playable — the dashboard mirrors state, it is not a dependency.

## Components

### 1. Combat tracker — `tracker.html`

Rendered by `render_tracker.py` from the **existing** combat state model in `combat.py`
(combatants carry `name`, `initiative`, `hp`/`max_hp`, `ac`, `conditions`, plus `round`
and the active-turn marker — this model already backs the terminal `print_tracker`). No
new state is introduced; the script reads live state and character files
(`characters/<PC>.md` for PC HP) and renders.

Contents:
- Initiative order, **active combatant row highlighted**, round counter (Foundry/Roll20
  parity — both are free byproducts of the existing model).
- Per combatant: HP `cur/max` (bar), AC, conditions, concentration flag, death-save
  pips when dying.
- **Inline condition effects** — each condition tag shows its rules effect pulled from the
  shipped SRD (`data/dnd5e_srd.json`), e.g. *"Poisoned — disadvantage on attack rolls and
  ability checks."* Saves the host asking what a condition does.

Update mechanism: at the end of each combat turn Claude invokes `render_tracker.py` (the
same way it already invokes `combat.py`/`tracker.py`), which overwrites `tracker.html`. The
file carries a `<meta http-equiv="refresh">` so the browser reloads itself. **Only during
combat.** Out of combat the file is left at its last state (or a neutral "no active
encounter" view); no per-turn regeneration happens during calm play.

### 2. Asset hub — `assets.html`

Rendered by `render_assets.py` at prep time from the three asset lists (below). Static
after generation. Three sections, all pre-wired to canonical filenames so the host just
drops files into `maps/` and `sounds/` and the controls go live:

- **Maps** — `<img src="maps/<file>">` thumbnails, click to enlarge. Encounter scenes only.
- **Ambient loops** — one **play/stop toggle** per location (`<audio loop>`), e.g.
  *Town Square*, *Crypt*, *Cave*.
- **SFX** — one **play button** per scripted sound (`<audio>` one-shot), e.g.
  *Collapse ▶*, *Beast roar ▶*.

A button/toggle whose file is not yet present renders in a visible "missing" state and
simply does nothing on click — the host knows to acquire it, and the page never errors.

### 3. Narration sound-cue block (bridge, loose coupling)

This is the chat→hub link, and it completes the original Bucket B. Narration principles in
`SKILL.md` gain a **third block type** alongside narrator and NPC speech:

> **Narrator:** The support beam splinters overhead.
> 🔊 **Cue:** *Collapse*
> **Nix:** "RUN—"

The host reads `🔊 Cue: Collapse` in chat and clicks **Collapse ▶** in `assets.html`.
**Loose coupling** — no live data channel between chat and hub (impossible over `file://`
anyway). The host does the eye-match; that is the whole mechanism.

This turn also **formalizes the NPC block** (Bucket B proper): NPC speech renders as a
blockquoted, bold speaker-labeled block — `> **Nix:** "..."` — the strongest visual break
that every markdown renderer honors, reusing the blockquote-with-prefix vocabulary the
skill already uses for Tutor hints. The existing prose rule at `SKILL.md:203` ("put NPC
speech in its own block") is made concrete; it currently states the *what* but never the
*how*.

Both rules live in Narration principles and get guard tests mirroring the existing
`DMAuthenticityTests`/`DMVoiceTests` content-assertion pattern.

### 4. Prep-phase asset lists (generated from the spine)

The prep flow (`SKILL-commands.md` step 4, currently "Map shopping list") extends to a
single asset pass producing three lists, each a filtered walk over the sealed
`spine.json`. All three obey the sealed-campaign discipline — **describe the asset only,
never the plot/why** — and each entry assigns a **canonical filename** so `render_assets.py`
can pre-wire the HTML.

| List | Template | Spine filter | Entry shape |
|------|----------|--------------|-------------|
| Maps | `templates/map-list.md` (exists) | scenes flagged **tactical encounter** only — *not* social/exploration scenes | handle · look-only description · `Acquire:` archetype · `File: maps/<name>` |
| Ambient | `templates/ambient-list.md` (new) | distinct **notable locations** (town square, crypt, cave) | handle · atmosphere description · `Find:` search hint · `File: sounds/<name>` |
| SFX | `templates/sfx-list.md` (new) | **spine-guaranteed events only** — named monster set-pieces, fixed plot gates; *not* player-improvised actions | handle · **neutral sound** description · `Find:` search hint · `File: sounds/<name>` |

**Restricting maps to encounter scenes** is a real simplification — social scenes are
theater of the mind and need no map.

**SFX must not spoil the host.** A guaranteed *event* ("the cave collapses and traps the
party") is a plot beat the host is meant to discover in play. The SFX list therefore
describes the **sound, stripped of its trigger** — *"heavy stone-on-stone collapse
rumble,"* not *"the cave that traps you."* The host gathers the sound; only learns *when*
it fires from the live `🔊 Cue` at the table. Same discipline the map list already applies
to locations ("look only, never why").

**Downloads, not links.** The host acquires local audio files rather than pasting URLs.
This is the technically-correct path, not just a preference: local files are what make
`<audio>` play over `file://`; external links frequently *cannot* be embedded (YouTube is
not `<audio>`-able, CORS/mixed-content, link rot, buffering, ads) — fatal when clicking at
a dramatic beat. The list supplies search hints; the host saves files under the canonical
names; the pre-wired HTML lights up as files appear.

## Data flow

```
PREP (once):
  spine.json ──render──> map-list.md / ambient-list.md / sfx-list.md   (Claude, 3 filters)
  host reads the 3 lists, acquires files → maps/*, sounds/*            (manual)
  render_assets.py(lists) ──> assets.html                              (pre-wired buttons)

PLAY — combat turn:
  combat.py / tracker.py / characters.md  ──render_tracker.py──> tracker.html  (meta-refresh)

PLAY — narration:
  Claude emits 🔊 Cue: <name> in chat ──(host eye-match)──> host clicks button in assets.html
```

## Error handling / edge cases

- **Missing asset file** — control renders in a "missing" state, click is a no-op, no error.
- **Ambient loop survival** — guaranteed by the two-file split; tracker regen never touches
  `assets.html`.
- **No combat active** — `tracker.html` shows a neutral "no active encounter" view; no
  per-turn writes during calm play.
- **Host never opens the tabs** — fully supported; chat is source of truth, dashboard is
  mirror-only.
- **Autoplay blocked** — non-issue; all audio is click-triggered (a user gesture).
- **Malformed HTML risk** — avoided by generating from render scripts, not free-written
  markup.

## Testing

- **Prose guards** (`tests/test_prep_skill_prose.py`, mirroring `DMAuthenticityTests`):
  assert `SKILL.md` contains the formalized NPC-block rule and the sound-cue block rule.
- **Template presence:** assert `templates/ambient-list.md` and `templates/sfx-list.md`
  exist and carry the "describe the asset only, never the plot" discipline text; assert
  the SFX template carries the neutral-sound / no-trigger instruction.
- **`render_tracker.py`:** unit test with a sample combatant set → assert output HTML
  contains each name, `cur/max` HP, the active-row highlight, and a condition rendered
  *with* its SRD effect text; assert `<meta refresh>` present.
- **`render_assets.py`:** unit test with sample lists → assert `<img>`/`<audio>` elements
  wired to the canonical filenames, one control per entry, missing-file state for absent
  files.

## Out of scope / rejected

- **Gold / inventory tracking** — manual by design (constraint 3).
- **Plot notes / secret reveal / monster stat math** — violates the sealed campaign
  (constraint 2); Claude already adjudicates.
- **Tight chat→hub coupling** (HTML auto-highlights the cued button) — would force HTML
  regeneration on *every* narration turn, dragging per-turn writes into calm play. Loose
  coupling gets ~90% of the value; revisit only if the eye-match proves clumsy in practice.
- **Fog of war, multi-encounter tracking, macros** — complex, player-facing, or redundant
  with Claude-as-DM.
- **Reviving any server / network / phone / TTS** — the teardown's whole point.

## Open questions (resolve in the plan, not blocking)

- Exact wiring of persisted combat state that `render_tracker.py` reads (does `combat.py`
  persist combatants between turns, or are they passed each call?) — confirm during
  implementation.
- Whether `assets.html` also shows a static resting-party HP reference out of combat, or
  strictly maps+sounds — minor, decide when building `render_assets.py`.
- Canonical filename scheme (`sfx_collapse.mp3` vs `collapse.mp3`) — pick one convention in
  the plan and use it in both the list templates and the render script.

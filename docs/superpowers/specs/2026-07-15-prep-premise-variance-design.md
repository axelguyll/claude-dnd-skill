# Prep premise/theme variance fix — design

**Date:** 2026-07-15
**Status:** approved, pre-implementation
**Repo:** claude-dnd-skill (`skills/dnd`)

## Problem

The `/dm:dnd prep` phase produces low premise variety. A blank / "surprise-me"
premise collapses into the same trope basin — *frontier town + sealed mine +
disappearances + sealed evil waking* — reproduced three times, most recently on an
unassisted **classic-tone** roll (not even grim). Root cause, confirmed against the
code:

- The prep premise/tone picker is **improvised by the model at runtime** — not a
  catalog, not hardcoded. Nothing forces orthogonal random choices, so "generic
  fantasy threat" free-associates to one lowest-energy cliché every time.
- Prep's tone axis **regressed** vs `/dm:dnd new`: prep offers 3 moods
  (grim/classic/lighthearted); `new` offers 7 genres
  (grimdark/dark-fantasy/heroic/horror/political/swashbuckling/cosmic). Different
  vocabularies, and prep is the coarser one.

There is a **second, related defect** at the narration layer. The existing
"Tone follows the scene, not the theme" rule (`SKILL.md:26`) is written
grim-biased ("save *dread*", "don't narrate everything *ominous*"). It stops a grim
campaign from over-saturating, but says nothing to the other tones. With prep now
producing 7 distinct tones, each can fall into its own saturation trap
(swashbuckling = nonstop banter, cosmic = eldritch dread in every tavern).

## Goal

Give prep a mechanism that forces **orthogonal** random premise axes so tone no
longer collapses to one trope, unify the tone vocabulary across prep and `new` so
they can't drift, and generalize the anti-saturation narration rule to all tones.

## Approach (chosen: Hybrid C + shared tone catalog)

Divergent approaches considered and rejected are recorded in the ideation note
(`Vault/projects/claude-dnd-skill.md`). Summary of the fork:

- **A — flat curated hook list:** rejected. Doesn't structurally break clustering;
  a short list of one-tone hooks still clusters. Variety capped at list length.
- **B — pure combinatorial axes:** rejected as sole mechanism. Best variety but
  ships incoherent combos with no coherence anchor.
- **C — hybrid (chosen):** combinatorial axes (the variety engine) + per-tone
  exemplars (the quality bar) + a composer that emits a labeled scaffold with an
  explicit reconcile/discard instruction (bounds the nonsense).

## Components

### 1. Tone catalog — `skills/dnd/data/tones.yaml` (new)

Single source of truth for tone, consumed by the composer script **and** recited by
both prep and `/dm:dnd new` prose. Reconciles prep's 3 moods + new's 7 genres into
one 7-tone set:

| id | descriptor | absorbs |
|---|---|---|
| `heroic` | bright high fantasy, clear stakes | new:heroic, prep:classic |
| `mythic` | classic D&D middle register | prep:classic |
| `grimdark` | harsh, morally grey, costly | new:grimdark + dark-fantasy, prep:grim |
| `horror` | dread, survival, the wrong-shaped | new:horror |
| `intrigue` | courts, leverage, betrayal | new:political |
| `swashbuckling` | fast, funny, daring | new:swashbuckling, prep:lighthearted |
| `cosmic` | eldritch, unknowable, mystery | new:cosmic |

Each entry: `id`, `descriptor`, `mood_note` (one-line steer for the reconciliation
pass — e.g. grimdark: "the cost is real; let victories bleed").

### 2. Premise seed file — `skills/dnd/data/premise-seeds.yaml` (new)

- `axes:` — four **tone-agnostic** lists: `setting`, `conflict`, `antagonist`,
  `twist` (~6–8 entries each). Tone-agnostic on purpose: "something sealed away"
  can be grim *or* played for laughs; tone colors it at reconcile time, so one axis
  set serves all 7 tones. ~6×6×6×6 ≈ 1300 combinations from ~28 curated lines.
- `exemplars:` — 2–3 complete premises per tone, reference-only (not rolled), to
  anchor the quality bar.

### 3. Composer — `skills/dnd/scripts/prep/premise.py` (new)

CLI `--tone <id> [--seed N]`, mirroring `bestiary.py` / `milestone.py` structure
(module functions + `argparse` `__main__`). Behavior:

1. Load `tones.yaml`; validate `--tone` against it (unknown tone → stderr + exit 1).
2. Load `premise-seeds.yaml`; roll each of the four axes independently (stdlib
   `random`; `--seed` for deterministic tests).
3. Print a **labeled scaffold**: the four rolled axes, the tone's `mood_note`, the
   tone's exemplars, and a fixed instruction block:
   > *Raw spark. Reconcile into ONE coherent premise in the chosen tone. Discard any
   > axis that fights the others — orthogonality is the point, coherence is your job.
   > Do not default to the nearest cliché.*

Reachable two ways: called by prep when premise is blank, **and** standalone so the
host can re-roll manually.

### 4. Prep prose — `SKILL-commands.md` (`/dm:dnd prep`, `:276`+)

- Signature `tone:` enum → the 7 catalog ids (replacing grim|classic|lighthearted).
- New step between resolve-dir and world-layer: *if premise is blank, run
  `premise.py --tone <t>`, reconcile the scaffold into the premise, log the rolled
  axes* (mirrors the Tone Wizard's `dice.py` blank-field logging).
- `/dm:dnd new` step 6 tone line → point at the catalog (`data/tones.yaml`) instead
  of an inline list. `new`'s flow is otherwise unchanged.

### 5. Generalized saturation rule — `SKILL.md:26` (edit)

Rewrite tone-agnostic. The campaign's tone belongs to the **focused beats** (main
storyline events, the antagonist, genuine high-stakes turns), not every scene. Name
the failure mode across registers, not just grim:
> …Whatever the campaign's tone, it belongs to the beats that carry the story — the
> antagonist, the high-stakes turns — not to every conversation and errand. A grim
> campaign isn't uniformly bleak; a swashbuckling one isn't nonstop banter; a cosmic
> one doesn't drown a market-day in dread…

Keeps the pinned phrase "Tone follows the scene, not the theme" (existing test still
passes).

## Testing (TDD, vertical slices)

- `tests/test_prep_premise.py` (new) — composer: seeded determinism (same seed →
  same roll), tone validation (bad tone exits nonzero), all four axes present in
  output, reconcile-instruction present, mood_note + exemplars for the tone present.
- `tests/test_tones_catalog.py` (new) — `tones.yaml` parses; 7 expected ids present;
  each entry has `descriptor` + `mood_note`.
- `tests/test_prep_skill_prose.py` (edit) — prep signature lists the catalog tones;
  prep references `premise.py`; both prep and `new` reference `data/tones.yaml`; the
  saturation rule names more than one register (anti-revert pin).

## Blast radius

New: `data/tones.yaml`, `data/premise-seeds.yaml`, `scripts/prep/premise.py`,
`tests/test_prep_premise.py`, `tests/test_tones_catalog.py`.
Edited: `SKILL-commands.md` (prep + new), `SKILL.md:26`, `tests/test_prep_skill_prose.py`.
`/dm:dnd new` behavior unchanged except the tone list now lives in `tones.yaml`.

## Out of scope (parked)

- Wiring easy/standard/deadly difficulty into real band math (separate concern; not
  the user's complaint).
- Reworking `/dm:dnd new`'s interview flow beyond the tone-list pointer.

## Acceptance

Live prep read-through: blank-premise rolls across several tones produce visibly
distinct premises that do **not** collapse to frontier/sealed-mine/disappearances.
Prose pins guard against silent reversion; the real check is the read-through.

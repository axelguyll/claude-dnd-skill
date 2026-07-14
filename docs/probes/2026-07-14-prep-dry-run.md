# Prep Phase — First Dry-Run Probe (2026-07-14)

Manual Probe of the authored-campaign **prep** flow end to end (per CONTEXT.md *Probe* —
automated tests can't judge prose quality or spoiler-safety). Driven on branch `prep-phase`.

## Premise driven

`/dm:dnd prep premise:"a mining town's children are vanishing" tone:classic difficulty:standard`
with 2 imported party sheets. Generated: world intent → 6-beat spine → hard validate → map list.

## Step 1 — automated suite

`python -m unittest discover -s tests -p "test_prep_*.py"` → **31/31 pass** (after the
CLI fix below). (`tests/test_display_robustness.py` has 8 pre-existing, unrelated cp1252
failures on this Windows box — not part of the prep suite, not touched by this work.)

## Bug found and fixed by this Probe

The Probe immediately hit a real shipped bug that every unit test had masked:

- `python skills/dnd/scripts/prep/schema.py --bible <path>` — the exact call the
  `/dm:dnd prep` procedure makes — crashed with `ModuleNotFoundError: No module named 'prep'`.
- **Root cause:** run as a script, `sys.path[0]` is the `prep/` dir itself, so
  `importlib.import_module("prep.bestiary")` couldn't find the `prep` package (parent
  `skills/dnd/scripts` absent from path). Unit tests never saw it because they
  `sys.path.insert(0, ".../scripts")` before importing.
- **Fix:** schema.py now adds `scripts/` to `sys.path` before the import (commit `b519237`).
  Added `tests/test_prep_cli.py` — subprocess tests that invoke all three prep CLIs by
  file path (the real invocation), so this class of regression is caught going forward.

This is exactly what the manual Probe exists to catch: the CLIs are invoked as scripts at
runtime, and no unit test exercised that path.

## Step 2–3 — spine + hard gate + spoiler-safety

**Validation gate:** `schema.py --bible probe-bible.json` → `VALID` (exit 0), **first try**
after the CLI fix. The whole spine below was authored using `bestiary.py --level <L>` to pull
the legal in-band candidate list at each beat's party level, then picking what was *dramatic*
from that list only.

**Spine (6 beats, acts 2/2/2, milestone L1→8):**

| Beat | Act | Party level (during) | Threat | CR | Band ceiling | In band |
|------|-----|----------------------|--------|----|--------------|---------|
| 1 Inciting Incident | 1 | 1 | Ghoul | 1 | 3 | ✓ |
| 2 Complication | 1 | 2 | Ghast | 2 | 4 | ✓ |
| 3 Rising Action | 2 | 3 | Wraith | 5 | 5 | ✓ (at ceiling) |
| 4 Midpoint | 2 | 4 | Night Hag | 5 | 6 | ✓ |
| 5 All Is Lost | 3 | 6 | Young Green Dragon | 8 | 8 | ✓ (at ceiling) |
| 6 Final Confrontation | 3 | 7 | Fire Giant | 9 | 9 | ✓ (at ceiling) |

`level_up_to` = [2,3,4,6,7,8] — monotonic, final non-null, arc ends at L8. Beats are
situations (a bricked adit, a foreman who lies, a bound wraith, a broker's bargain, a
hostage larder, a slave-forge) with ≥3 hooks each; a single missing child causally chains
foreman → hag → dragon → fire-giant tyrant. Confirms the validator agrees with the design's
during-beat band rule on a real, hand-authored campaign — not just the fixtures.

**Map shopping list — spoiler-safety audit.** Generated in a SEPARATE pass instructed
"describe the look only, never why the party goes there or what happens." Result (the one
artifact the host is meant to read):

- **Town at the mine-mouth** — muddy switchback streets under timber headframes, slag heaps,
  a rickety chapel. *Acquire:* frontier mining-village battlemap.
- **Bricked adit** — a timbered tunnel mouth in a hillside, half-collapsed, cold air. *Acquire:* cave/mine-entrance tile.
- **Flooded gallery** — knee-deep black water between support pillars, side drifts vanishing into dark. *Acquire:* flooded-cavern map.
- **Broken shaft** — a snapped timber lift over a rubble-ramped pit dropping into black. *Acquire:* vertical mine-shaft map.
- **Candle-lit warren** — cramped twisting passages, low alcoves, damp stone. *Acquire:* tight-tunnel dungeon tiles.
- **Hazed deep cavern** — a vast green-lit gulf, mineral columns, a broad ledge over a drop. *Acquire:* large cavern map.
- **Underground forge-hall** — lava channels, anvils, hanging chains, iron catwalks. *Acquire:* lava foundry map.

Audit: **no entry states why the party goes there or what happens** — descriptions are
terrain/look only. Deliberately kept the *Acquire* hints creature-neutral ("large cavern",
"lava foundry") rather than "dragon cave" / "fire-giant forge", which would leak the encounter.

## Findings / recommendations

1. **[fixed]** schema.py CLI standalone-import bug — commit `b519237`, regression test added.
2. **[minor, for final review]** The `/dm:dnd prep` map-pass prose already forbids plot in the
   *description*. Recommend it also state explicitly that *Acquire* hints name terrain
   archetypes, not creatures — otherwise a well-meaning author writes "dragon lair map" and
   leaks the finale to the one artifact the host reads. I kept hints neutral by hand here.

## Verdict

Prep flow works end to end on a real premise: world intent → in-band spine → **VALID** hard
gate (first try, post-fix) → spoiler-safe map list. One real bug surfaced and fixed; one minor
prose-tightening logged. Milestone leveling (XP-free) and the level-up gate bypass are wired;
the deed ledger + cite rule are in place. Ready for whole-branch review.

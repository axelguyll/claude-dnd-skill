# Prep Premise/Theme Variance Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `/dm:dnd prep` a combinatorial premise seed-bank + shared tone catalog so blank-premise campaigns stop collapsing to one trope, and generalize the tone-saturation narration rule to all 7 tones.

**Architecture:** Two new YAML data files (`tones.yaml`, `premise-seeds.yaml`) are the curated source of truth. A new `premise.py` composer rolls four orthogonal axes independently and prints a labeled scaffold with a reconcile/discard instruction. Prep prose calls it when premise is blank; both prep and `/dm:dnd new` recite tone from the catalog so the lists can't drift. A prose edit to `SKILL.md` makes the "tone marks focus beats, not every scene" rule tone-agnostic.

**Tech Stack:** Python 3 stdlib (`random`, `argparse`, `pathlib`) + PyYAML 6.0.3 (already a repo dependency — `build_srd.py` imports it; no install). `unittest` for tests, matching existing `tests/`.

## Global Constraints

- Scripts mirror existing prep-script structure (`bestiary.py`, `milestone.py`): module-level functions + `if __name__ == "__main__"` argparse CLI. Tests import the module functions directly.
- Data path resolution mirrors `bestiary.py`: `pathlib.Path(__file__).resolve().parents[2] / "data" / "<file>.yaml"`.
- YAML loaded via `yaml.safe_load` only (never `yaml.load`).
- No new pip dependencies. No auto-install.
- Tone id set is exactly: `heroic, mythic, grimdark, horror, intrigue, swashbuckling, cosmic`.
- Determinism: any randomness goes through a `random.Random(seed)` instance passed in, never module-global `random`, so tests seed it.
- Run tests from repo root: `python3 -m unittest tests.<module> -v`.
- Every task ends with a commit. Co-author trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

---

### Task 1: Tone catalog data file

**Files:**
- Create: `skills/dnd/data/tones.yaml`
- Test: `tests/test_tones_catalog.py`

**Interfaces:**
- Produces: `tones.yaml` with top-level key `tones:` → list of `{id, descriptor, mood_note}`. The 7 ids above. Consumed by Task 3 (`premise.py`) and referenced by prose in Task 4.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tones_catalog.py
"""test_tones_catalog.py — the shared tone catalog is well-formed and complete."""
import pathlib
import unittest

import yaml

DATA = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "data"
EXPECTED_IDS = {"heroic", "mythic", "grimdark", "horror", "intrigue", "swashbuckling", "cosmic"}


class ToneCatalogTests(unittest.TestCase):
    def setUp(self):
        self.doc = yaml.safe_load((DATA / "tones.yaml").read_text(encoding="utf-8"))

    def test_has_tones_list(self):
        self.assertIn("tones", self.doc)
        self.assertIsInstance(self.doc["tones"], list)

    def test_exactly_seven_expected_ids(self):
        ids = {t["id"] for t in self.doc["tones"]}
        self.assertEqual(ids, EXPECTED_IDS)

    def test_every_entry_has_descriptor_and_mood_note(self):
        for t in self.doc["tones"]:
            self.assertTrue(t.get("descriptor", "").strip(), f"{t['id']} missing descriptor")
            self.assertTrue(t.get("mood_note", "").strip(), f"{t['id']} missing mood_note")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_tones_catalog -v`
Expected: FAIL — `FileNotFoundError` (tones.yaml does not exist yet).

- [ ] **Step 3: Create the data file**

```yaml
# skills/dnd/data/tones.yaml
# Shared tone catalog. Single source of truth for BOTH /dm:dnd prep and
# /dm:dnd new. Edit here, never inline in SKILL-commands.md.
tones:
  - id: heroic
    descriptor: "bright high fantasy, clear stakes, beatable villains"
    mood_note: "courage pays off; let clean wins feel earned, not naive"
  - id: mythic
    descriptor: "classic D&D middle register — wonder and danger in balance"
    mood_note: "the world is old and strange; treat legends as literally real"
  - id: grimdark
    descriptor: "harsh, morally grey, every victory costs something"
    mood_note: "let wins bleed a little; no clean hands"
  - id: horror
    descriptor: "dread, survival, the wrong-shaped thing"
    mood_note: "safety is temporary and the threat is patient — but only when it counts"
  - id: intrigue
    descriptor: "courts, leverage, quiet betrayal"
    mood_note: "everyone wants something; trust is spendable currency"
  - id: swashbuckling
    descriptor: "fast, funny, daring"
    mood_note: "keep it moving, let them look cool, banter over dread"
  - id: cosmic
    descriptor: "eldritch, unknowable, mystery at scale"
    mood_note: "understanding is dangerous and the scale dwarfs the party"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_tones_catalog -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add skills/dnd/data/tones.yaml tests/test_tones_catalog.py
git commit -m "feat(prep): add shared 7-tone catalog data file"
```

---

### Task 2: Premise seed data file

**Files:**
- Create: `skills/dnd/data/premise-seeds.yaml`
- Test: `tests/test_premise_seeds.py`

**Interfaces:**
- Produces: `premise-seeds.yaml` with `axes:` (keys `setting`, `conflict`, `antagonist`, `twist`, each a list of ≥6 strings) and `exemplars:` (one key per tone id, each a list of ≥2 strings). Consumed by Task 3.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_premise_seeds.py
"""test_premise_seeds.py — the premise seed bank is well-formed and deep enough
to actually produce variety."""
import pathlib
import unittest

import yaml

DATA = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "data"
AXES = ("setting", "conflict", "antagonist", "twist")
TONE_IDS = {"heroic", "mythic", "grimdark", "horror", "intrigue", "swashbuckling", "cosmic"}


class PremiseSeedTests(unittest.TestCase):
    def setUp(self):
        self.doc = yaml.safe_load((DATA / "premise-seeds.yaml").read_text(encoding="utf-8"))

    def test_all_four_axes_present_and_deep(self):
        for axis in AXES:
            entries = self.doc["axes"][axis]
            self.assertGreaterEqual(len(entries), 6, f"{axis} needs >=6 entries for variety")
            self.assertTrue(all(isinstance(e, str) and e.strip() for e in entries))

    def test_exemplars_cover_every_tone(self):
        for tone in TONE_IDS:
            self.assertIn(tone, self.doc["exemplars"])
            self.assertGreaterEqual(len(self.doc["exemplars"][tone]), 2, f"{tone} needs >=2 exemplars")

    def test_axes_are_tone_agnostic_no_tone_keys(self):
        # axes must be flat lists, not tone-keyed dicts — orthogonality depends on it
        for axis in AXES:
            self.assertIsInstance(self.doc["axes"][axis], list)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_premise_seeds -v`
Expected: FAIL — `FileNotFoundError`.

- [ ] **Step 3: Create the data file**

Fill each axis to 6–8 entries and each tone to 2–3 exemplars. Entries are deliberately spread across register and setting so no single combination reads as the default. Starter content (expand during this step to meet the ≥6 / ≥2 minimums):

```yaml
# skills/dnd/data/premise-seeds.yaml
# Combinatorial premise seed bank for /dm:dnd prep. Axes are TONE-AGNOSTIC:
# tone colors a rolled combination at reconcile time, so one axis set serves
# all 7 tones. premise.py rolls one entry per axis independently.
axes:
  setting:
    - "a trade-city built across a canyon on chained bridges"
    - "a monastery on a tidal island, cut off from the mainland at high water"
    - "a caravan road through salt flats where the wells are failing one by one"
    - "a river-delta port where three rivers and three laws meet"
    - "a mountain observatory that has stopped answering its couriers"
    - "a floating market-barge town that never docks in the same place twice"
    - "a border fort repurposed into a refugee town after the war moved on"
    - "an old-growth forest the maps insist is smaller than it is"
  conflict:
    - "a succession no living claimant can prove cleanly"
    - "a resource everyone needs that has started running out this season"
    - "a treaty coming due that half the signatories no longer honor"
    - "a debt called in all at once across an entire region"
    - "a migration arriving faster than anyone planned for"
    - "a discovery that makes an old crime suddenly provable"
    - "a quarantine no one can agree is still necessary"
  antagonist:
    - "a guild that has quietly bought every debt in the region"
    - "a reformer whose fix is worse than the problem"
    - "an heir raised in exile who has come home to collect"
    - "a bureaucracy following a rule past the point of sense"
    - "a folk hero whose legend requires a war to stay true"
    - "a cartel of experts who profit from the problem staying unsolved"
    - "a well-meaning zealot certain the ends justify anything"
  twist:
    - "the obvious victim is orchestrating the whole thing"
    - "the thing everyone fears is the only thing holding worse at bay"
    - "the party's employer is on the wrong side and doesn't know it"
    - "the solution everyone wants would doom a group no one is counting"
    - "the crisis already happened; this is the cover-up"
    - "two factions are the same faction wearing two faces"
    - "the map is right and the territory is lying"
exemplars:
  heroic:
    - "A failing mountain observatory begs for aid; the storms it tracked were the only warning against a rival kingdom's march, and the party can restore the watch before the first banners crest."
    - "A river-delta port drowns in a called-in debt; a folk-hero magistrate rallies the three river-guilds, and the party carries the alliance that saves the season."
  mythic:
    - "An old-growth forest larger than any map admits hides a sleeping arbiter; a treaty coming due wakes it, and the party must answer for both sides of a bargain older than the kingdom."
  grimdark:
    - "A quarantine no one will lift is the only thing keeping a cartel's profit alive; lifting it saves thousands and buries the party's employer, who is on the wrong side and doesn't know it."
  horror:
    - "A tidal-island monastery goes silent between high waters; the thing the monks feared is the only thing holding something worse at bay, and the tide is coming in."
  intrigue:
    - "A canyon trade-city faces a succession no claimant can prove; a guild that bought every debt in the city means to pick the winner, and the party holds the one ledger that decides it."
  swashbuckling:
    - "A market-barge town that never docks twice is running from an heir come home to collect; the party has one festival's worth of chaos to swap the debt-ledgers before the barge is boarded."
  cosmic:
    - "A salt-flat caravan road loses its wells one by one along a line no cartographer will admit is a shape; the discovery that maps it makes an old crime provable and an older presence aware of being seen."
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_premise_seeds -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add skills/dnd/data/premise-seeds.yaml tests/test_premise_seeds.py
git commit -m "feat(prep): add combinatorial premise seed bank"
```

---

### Task 3: Premise composer script

**Files:**
- Create: `skills/dnd/scripts/prep/premise.py`
- Test: `tests/test_prep_premise.py`

**Interfaces:**
- Consumes: `tones.yaml` (Task 1), `premise-seeds.yaml` (Task 2).
- Produces:
  - `load_tones(path=None) -> list[dict]`
  - `load_seeds(path=None) -> dict`
  - `tone_by_id(tone_id, tones) -> dict | None`
  - `roll_premise(tone_id, tones, seeds, rng) -> dict` — returns `{"tone", "descriptor", "mood_note", "setting", "conflict", "antagonist", "twist", "exemplars"}`. If `tone_id` is `None`, rolls a tone from the catalog via `rng` (surprise-me / seal-and-walk-away path). Raises `KeyError` only if a non-None `tone_id` is unknown.
  - `format_scaffold(rolled) -> str` — human-readable block including all four axis values, the resolved tone (so the caller knows what to stamp into `world.md`), the mood_note, exemplars, and the fixed reconcile instruction.
  - CLI: `python3 premise.py [--tone <id>] [--seed N]` → prints scaffold; `--tone` optional (omitted → rolled from catalog); unknown non-None tone → stderr + exit 1.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_prep_premise.py
"""test_prep_premise.py — the premise composer rolls orthogonal axes and emits
a reconcile-instruction scaffold. Determinism is seeded so the roll is testable."""
import pathlib
import random
import subprocess
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "skills" / "dnd" / "scripts" / "prep"))

import premise  # noqa: E402

SCRIPT = REPO / "skills" / "dnd" / "scripts" / "prep" / "premise.py"


class RollTests(unittest.TestCase):
    def setUp(self):
        self.tones = premise.load_tones()
        self.seeds = premise.load_seeds()

    def test_seeded_roll_is_deterministic(self):
        a = premise.roll_premise("grimdark", self.tones, self.seeds, random.Random(42))
        b = premise.roll_premise("grimdark", self.tones, self.seeds, random.Random(42))
        self.assertEqual(a, b)

    def test_roll_has_all_four_axes(self):
        r = premise.roll_premise("heroic", self.tones, self.seeds, random.Random(1))
        for axis in ("setting", "conflict", "antagonist", "twist"):
            self.assertTrue(r[axis].strip())

    def test_roll_carries_tone_mood_note(self):
        r = premise.roll_premise("cosmic", self.tones, self.seeds, random.Random(1))
        self.assertEqual(r["tone"], "cosmic")
        self.assertTrue(r["mood_note"].strip())

    def test_unknown_tone_raises(self):
        with self.assertRaises(KeyError):
            premise.roll_premise("nope", self.tones, self.seeds, random.Random(1))

    def test_blank_tone_rolls_from_catalog(self):
        ids = {t["id"] for t in self.tones}
        r = premise.roll_premise(None, self.tones, self.seeds, random.Random(9))
        self.assertIn(r["tone"], ids)
        self.assertTrue(r["mood_note"].strip())

    def test_scaffold_contains_axes_and_instruction(self):
        r = premise.roll_premise("intrigue", self.tones, self.seeds, random.Random(7))
        out = premise.format_scaffold(r)
        self.assertIn(r["setting"], out)
        self.assertIn(r["antagonist"], out)
        self.assertIn(r["tone"], out)  # resolved tone reported for world.md
        self.assertIn("Reconcile into ONE coherent premise", out)
        self.assertIn("Do not default to the nearest cliché", out)

    def test_scaffold_names_the_target_trope(self):
        r = premise.roll_premise("grimdark", self.tones, self.seeds, random.Random(2))
        self.assertIn("sealed-mine", premise.format_scaffold(r))


class CliTests(unittest.TestCase):
    def test_cli_good_tone_exit_zero(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--tone", "horror", "--seed", "3"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Reconcile into ONE coherent premise", p.stdout)

    def test_cli_no_tone_rolls_and_exits_zero(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--seed", "5"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Reconcile into ONE coherent premise", p.stdout)

    def test_cli_bad_tone_exit_nonzero(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--tone", "bogus"],
                           capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_prep_premise -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'premise'`.

- [ ] **Step 3: Write the implementation**

```python
# skills/dnd/scripts/prep/premise.py
"""premise.py — combinatorial premise composer for /dm:dnd prep.

Rolls one entry from each of four orthogonal axes (setting × conflict ×
antagonist × twist) from data/premise-seeds.yaml, colored by a tone drawn from
data/tones.yaml, and prints a labeled scaffold with an explicit reconcile
instruction. The axes are tone-agnostic on purpose: forcing independent random
choices is what stops 'grim' collapsing to one trope. The model turns the
scaffold into a coherent premise; discarding a clashing axis is expected.
"""
from __future__ import annotations

import pathlib
import random

import yaml

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"
AXES = ("setting", "conflict", "antagonist", "twist")

_INSTRUCTION = (
    "Reconcile into ONE coherent premise in the chosen tone. Discard any axis "
    "that fights the others — orthogonality is the point, coherence is your job. "
    "Do not default to the nearest cliché — especially avoid the frontier-town / "
    "sealed-mine / missing-people default that this tool exists to break."
)


def load_tones(path: pathlib.Path | None = None) -> list[dict]:
    p = path or DATA / "tones.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8"))["tones"]


def load_seeds(path: pathlib.Path | None = None) -> dict:
    p = path or DATA / "premise-seeds.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def tone_by_id(tone_id: str, tones: list[dict]) -> dict | None:
    for t in tones:
        if t["id"] == tone_id:
            return t
    return None


def roll_premise(tone_id, tones: list[dict], seeds: dict, rng: random.Random) -> dict:
    if tone_id is None:
        # surprise-me: roll the tone too, so prep has a concrete tone to author
        # the whole bible in. Roll tone BEFORE axes so a given seed is stable.
        tone = rng.choice(tones)
        tone_id = tone["id"]
    else:
        tone = tone_by_id(tone_id, tones)
        if tone is None:
            raise KeyError(f"unknown tone: {tone_id!r}")
    rolled = {axis: rng.choice(seeds["axes"][axis]) for axis in AXES}
    rolled.update(
        tone=tone_id,
        descriptor=tone["descriptor"],
        mood_note=tone["mood_note"],
        exemplars=seeds["exemplars"].get(tone_id, []),
    )
    return rolled


def format_scaffold(rolled: dict) -> str:
    lines = [
        f"PREMISE SCAFFOLD — tone: {rolled['tone']} ({rolled['descriptor']})",
        f"  mood: {rolled['mood_note']}",
        "",
        "Rolled axes (independent — reconcile, don't concatenate):",
        f"  setting    : {rolled['setting']}",
        f"  conflict   : {rolled['conflict']}",
        f"  antagonist : {rolled['antagonist']}",
        f"  twist      : {rolled['twist']}",
        "",
        "Exemplars for this tone (quality bar, not to be reused verbatim):",
    ]
    lines += [f"  - {ex}" for ex in rolled["exemplars"]]
    lines += ["", _INSTRUCTION]
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="Roll a combinatorial premise scaffold for prep.")
    ap.add_argument("--tone", default=None, help="tone id from data/tones.yaml (omit to roll one)")
    ap.add_argument("--seed", type=int, default=None, help="seed the roll (for reproducibility/tests)")
    args = ap.parse_args()

    tones = load_tones()
    seeds = load_seeds()
    rng = random.Random(args.seed)
    try:
        rolled = roll_premise(args.tone, tones, seeds, rng)
    except KeyError as e:
        valid = ", ".join(t["id"] for t in tones)
        print(f"error: {e}. valid tones: {valid}", file=sys.stderr)
        raise SystemExit(1)
    print(format_scaffold(rolled))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_prep_premise -v`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add skills/dnd/scripts/prep/premise.py tests/test_prep_premise.py
git commit -m "feat(prep): add premise composer that rolls orthogonal axes"
```

---

### Task 4: Wire prep + new prose to catalog and composer

**Files:**
- Modify: `skills/dnd/SKILL-commands.md` (prep signature/flow `:276`+; `/dm:dnd new` tone line `:27`)
- Modify: `skills/dnd/SKILL-scripts.md` (add `premise.py` reference entry)
- Modify: `skills/dnd/templates/world.md:5` (tone placeholder → catalog pointer)
- Modify: `tests/test_prep_skill_prose.py` (add prose pins)

**Interfaces:**
- Consumes: `premise.py` CLI + `tones.yaml` from Tasks 1–3.
- Produces: prose pins that guard the wiring against silent reversion.

- [ ] **Step 1: Write the failing prose pins**

Append to the existing `SkillProseTests` class in `tests/test_prep_skill_prose.py`:

```python
    # --- prep premise-variance wiring (2026-07-15) ---

    def test_prep_signature_uses_catalog_tones(self):
        idx = CMDS.find("/dm:dnd prep")
        sig = CMDS[idx: idx + 200]
        # widened away from the old 3-mood enum
        self.assertNotIn("tone:grim|classic|lighthearted", sig)
        self.assertIn("swashbuckling", sig)
        self.assertIn("cosmic", sig)

    def test_prep_references_premise_composer(self):
        self.assertIn("premise.py", CMDS)

    def test_premise_script_documented(self):
        # discoverability: the composer appears in the script reference doc
        self.assertIn("premise.py", SCRIPTS)

    def test_both_flows_reference_tone_catalog(self):
        # prep AND /dm:dnd new recite tone from the shared file, not inline lists
        self.assertGreaterEqual(CMDS.count("data/tones.yaml"), 2)
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m unittest tests.test_prep_skill_prose.SkillProseTests -v`
Expected: FAIL on the three new tests (old enum still present, no `premise.py`, no `data/tones.yaml`).

- [ ] **Step 3: Edit the prep signature + flow**

In `SKILL-commands.md`, change the prep heading line (`:276`) from:

```
## `/dm:dnd prep [premise:"..."] [tone:grim|classic|lighthearted] [difficulty:easy|standard|deadly]`
```
to:
```
## `/dm:dnd prep [premise:"..."] [tone:heroic|mythic|grimdark|horror|intrigue|swashbuckling|cosmic] [difficulty:easy|standard|deadly]`
```

In the sentence right below it, replace the tone note with a catalog pointer:

```
Generate the authored campaign **bible** before session one. Inputs: premise (optional —
blank = surprise-me), tone (from the shared Tone Catalog, `data/tones.yaml`), difficulty,
and the imported party sheets.
```

Add a new numbered step between step 0 (resolve dir) and step 1 (World layer):

```
0.5 **Resolve tone + premise (do this BEFORE authoring any bible content).** Tone drives
   the entire bible — world, spine encounters, arc — so it must be locked first, then
   carried through every step. Do NOT free-associate the tone OR the premise; free
   association is exactly what collapses every campaign into the same trope. Instead:
   - Run `python3 ${CLAUDE_SKILL_DIR}/scripts/prep/premise.py [--tone <tone>]`.
     Pass `--tone` if the host supplied one; omit it to roll a tone from the catalog.
   - The scaffold reports the resolved tone. Write it to `world.md → ## Campaign Tone &
     Genre` — it is now THE campaign tone; steps 1–6 all author in it.
   - Reconcile the printed scaffold into ONE coherent premise in that tone, discarding any
     rolled axis that fights the others. Log the resolved tone + rolled axes in `world.md`
     (mirror the Tone Wizard's `dice.py` blank-field logging).
   - If the host supplied a premise verbatim, still run the script for tone resolution but
     use the supplied premise instead of the rolled axes.
```

- [ ] **Step 4: Edit the `/dm:dnd new` tone line to point at the catalog**

In `SKILL-commands.md` step 6 (`:27`), change:

```
   - Tone: `grimdark / dark fantasy / heroic / horror / political / swashbuckling / cosmic`
```
to:
```
   - Tone: present the ids from the shared Tone Catalog (`data/tones.yaml`) — heroic /
     mythic / grimdark / horror / intrigue / swashbuckling / cosmic (descriptor per entry)
```

- [ ] **Step 5: Document `premise.py` in `SKILL-scripts.md`**

Add an entry alongside the other prep scripts (match the existing `bestiary.py` /
`milestone.py` format):

```
### premise.py — combinatorial premise scaffold (prep)
`python3 ${CLAUDE_SKILL_DIR}/scripts/prep/premise.py [--tone <id>] [--seed N]`
Rolls one entry from each of four orthogonal axes (setting × conflict × antagonist ×
twist) from `data/premise-seeds.yaml`, colored by a tone from `data/tones.yaml` (omit
`--tone` to roll one). Prints a labeled scaffold for the DM to reconcile into a coherent
premise. Used by `/dm:dnd prep` step 0.5 when premise is blank; also runnable standalone
to re-roll. `--seed` makes the roll reproducible.
```

- [ ] **Step 6: Update the `world.md` template tone placeholder**

In `skills/dnd/templates/world.md:5`, change:
```
- **Tone:** <grimdark / dark fantasy / heroic / horror / political / swashbuckling / cosmic>
```
to:
```
- **Tone:** <one tone id from data/tones.yaml — heroic / mythic / grimdark / horror / intrigue / swashbuckling / cosmic>
```

- [ ] **Step 7: Run the prose pins to verify pass**

Run: `python3 -m unittest tests.test_prep_skill_prose.SkillProseTests -v`
Expected: PASS (existing + 4 new).

- [ ] **Step 8: Commit**

```bash
git add skills/dnd/SKILL-commands.md skills/dnd/SKILL-scripts.md skills/dnd/templates/world.md tests/test_prep_skill_prose.py
git commit -m "feat(prep): wire prep + new tone to shared catalog, roll premise when blank"
```

---

### Task 5: Generalize the tone-saturation narration rule

**Files:**
- Modify: `skills/dnd/SKILL.md:26`
- Modify: `tests/test_prep_skill_prose.py` (add anti-revert pin to `DMVoiceTests`)

**Interfaces:**
- Produces: a tone-agnostic saturation rule; anti-revert pin naming ≥2 registers.

- [ ] **Step 1: Write the failing pin**

Append to `DMVoiceTests` in `tests/test_prep_skill_prose.py`:

```python
    def test_c_tone_saturation_rule_is_tone_agnostic(self):
        # the rule must name more than one register, not just grim/ominous
        idx = SKILL.find("Tone follows the scene, not the theme")
        window = SKILL[idx: idx + 700]
        self.assertIn("swashbuckling", window)
        self.assertIn("the beats that carry the story", window)
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m unittest tests.test_prep_skill_prose.DMVoiceTests -v`
Expected: FAIL on the new test (current prose is grim-only).

- [ ] **Step 3: Edit the rule at `SKILL.md:26`**

Replace the paragraph:

```
**Tone follows the scene, not the theme.** The campaign's theme sets what's at stake — the world's problems, the arc, the danger underneath — but it does not lock you into one mood. A scene can be warm, funny, or mundane before it turns; save dread for genuine high-stakes beats, then ease off. NPCs are people with their own personalities, not vessels for atmosphere. Don't narrate everything as ominous.
```
with:
```
**Tone follows the scene, not the theme.** The campaign's theme sets what's at stake — the world's problems, the arc, the danger underneath — but it does not lock you into one mood. Whatever the tone, it belongs to the beats that carry the story — the antagonist, the high-stakes turns, the focused storyline moments — not to every conversation and errand. A grim campaign isn't uniformly bleak; a swashbuckling one isn't nonstop banter; a horror one doesn't drown market-day in dread; a cosmic one doesn't make every tavern eldritch. A scene can be warm, funny, or mundane before it turns; save the tone's intensity for when it counts, then ease off. NPCs are people with their own personalities, not vessels for atmosphere.
```

- [ ] **Step 4: Run the full prose suite to verify pass + no regression**

Run: `python3 -m unittest tests.test_prep_skill_prose -v`
Expected: PASS — new pin passes; existing `test_c_tone_follows_scene_not_theme` (pins the unchanged headline phrase) still passes.

- [ ] **Step 5: Commit**

```bash
git add skills/dnd/SKILL.md tests/test_prep_skill_prose.py
git commit -m "feat(dm): generalize tone-saturation rule to all 7 tones"
```

---

### Task 6: Full-suite regression gate

**Files:** none (verification only)

- [ ] **Step 1: Run the entire test suite**

Run: `python3 -m unittest discover -s tests -v`
Expected: PASS — all prior tests plus the 5 new/edited modules. No regressions in `test_prep_*`, `test_dice_*`, `test_render_*`.

- [ ] **Step 2: Live acceptance (manual, per spec)**

Drive `/dm:dnd prep` with a blank premise across 3–4 different tones. Confirm the reconciled premises are visibly distinct and none collapse to frontier / sealed-mine / disappearances. This is the real acceptance check; the prose pins only guard against reversion.

---

## Self-Review

**Spec coverage:**
- Tone catalog (`tones.yaml`) → Task 1. ✓
- Premise seed file (`premise-seeds.yaml`) → Task 2. ✓
- Composer (`premise.py`, standalone + prep-called, `--seed`) → Task 3. ✓
- Prep prose (signature 7 tones, blank-premise roll step) + `new` pointer → Task 4. ✓
- Generalized saturation rule (SKILL.md:26) → Task 5. ✓
- Tests (test_prep_premise, test_tones_catalog, prose pins) → Tasks 1–5; note spec named `test_tones_catalog.py` (Task 1) and this plan adds `test_premise_seeds.py` (Task 2) — a superset, intentional. ✓
- Out-of-scope (difficulty wiring, new-flow rework) → untouched. ✓

**Placeholder scan:** No TBD/TODO. Task 2 step 3 says "expand to meet minimums" but ships concrete starter content meeting ≥6/≥2 already; the test enforces the floor. Acceptable — content curation is the task's deliverable, not a placeholder.

**Type consistency:** `roll_premise(tone_id, tones, seeds, rng)` signature identical across Task 3 impl, test, and interface block. `format_scaffold(rolled)` consistent. Axis tuple `("setting","conflict","antagonist","twist")` identical in premise.py, both data tests, and the seed file keys. Instruction string `"Reconcile into ONE coherent premise"` / `"Do not default to the nearest cliché"` matches between impl and test.

No gaps found.

## Grill resolutions (2026-07-15)

- **Blank tone:** `--tone` optional; omitted → `premise.py` rolls a tone from the catalog
  so prep always has a concrete tone to author the whole bible in. Tone is resolved at
  step 0.5, written to `world.md → ## Campaign Tone & Genre`, and carried through steps 1–6.
- **Tone-agnostic axes:** kept — one axis pool serves all 7 tones; orthogonality breaks
  the basin, tone colors at reconcile.
- **Anti-trope line:** composer instruction explicitly names the frontier/sealed-mine/
  missing-people default it exists to break.
- **Discoverability:** `premise.py` documented in `SKILL-scripts.md` (pinned).
- **Third tone copy:** `templates/world.md:5` placeholder repointed at the catalog.
- **No-free-associate rule** extended to cover tone as well as premise.
- **Parked:** difficulty→band-math wiring stays out of scope.

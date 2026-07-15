# DM-Tool HTML Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a host-facing (DM-side) HTML dashboard to `claude-dnd-skill` — a live combat tracker plus a static maps/ambient/SFX asset hub — with no server, driven by two small deterministic render scripts, and a third narration block type that cues sounds.

**Architecture:** Two self-contained local HTML files under the campaign dir, opened over `file://`. `tracker.html` (regenerated each combat turn by `render_tracker.py`, meta-refresh reloads it) merges combat.py's ephemeral `STATE_JSON` with tracker.py's persisted `tracker.json` and the bundled SRD condition text. `assets.html` (generated once at prep by `render_assets.py`) holds maps + click-to-play SFX + looped ambient, pre-wired to canonical filenames the host drops into `maps/`/`sounds/`. Splitting the files keeps the audio file stable so tracker regens never interrupt a playing loop. Chat→hub is loose coupling: Claude emits a `🔊 Cue: <handle>` block, the host clicks the matching button.

**Tech Stack:** Python 3.9+ stdlib only (`argparse`, `json`, `html`, `re`, `pathlib`); `unittest`; plain HTML/CSS + minimal inline JS. No new dependencies. No network.

## Global Constraints

- **Stdlib only.** No new dependencies. Match existing script style: `from __future__ import annotations` header (PEP 604 on 3.9).
- **Scripts live in `skills/dnd/scripts/`** and import siblings via bare import (`from paths import ...`) — Python puts the script's own dir on `sys.path[0]`, exactly as `tracker.py`/`combat.py` do.
- **No server.** `<audio>`/`<img>` load local relative paths over `file://`; never use `fetch()`/XHR. `tracker.html` carries `<meta http-equiv="refresh" content="4">`; `assets.html` must **never** carry a refresh (it would kill playing loops).
- **Filled per-campaign lists** live in the campaign dir: `<campaign>/map-list.md`, `<campaign>/ambient-list.md`, `<campaign>/sfx-list.md`. HTML output: `<campaign>/tracker.html`, `<campaign>/assets.html`. Assets referenced relative: `maps/<file>`, `sounds/<file>`.
- **Asset-list entry grammar** (one markdown bullet, parsed by `render_assets.py`):
  `- **<handle>** — <description>. *<Acquire|Find>:* <hint>. File: <maps/…|sounds/…>`
- **Sealed campaign.** All three lists describe the asset only, never plot/why. The SFX list describes the **sound stripped of its trigger** (`heavy stone-on-stone collapse rumble`, never `the cave that traps the party`).
- **Out of scope:** gold/inventory tracking, plot notes/secret reveal, tight chat→hub coupling, any server/network/phone/TTS.
- **Campaign path + SRD** come from `paths.py`: `find_campaign(name)`, `srd_path(campaign_ruleset(name))`, with fallback to `srd_path(None)` (the 2014 default, `data/dnd5e_srd.json`) if the ruleset file is absent.
- **Run tests** from repo root: `python3 -m unittest tests.<module> -v`. Full suite must stay green (190 tests pre-existing).

---

### Task 1: Narration prose — formalize NPC block + add sound-cue block

Completes the deferred "Bucket B": makes the existing "NPC speech in its own block" rule concrete, and adds the sound-cue block that bridges chat to `assets.html`. Prose-only edit to `SKILL.md` plus guard tests.

**Files:**
- Modify: `skills/dnd/SKILL.md` (Narration principles, the bullet at `SKILL.md:203`)
- Test: `tests/test_prep_skill_prose.py` (add a new `DMDashboardProseTests` class)

**Interfaces:**
- Consumes: nothing.
- Produces: two stable prose substrings later tasks and tests depend on — `🔊 **Cue:**` and `assets.html` in `SKILL.md`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_prep_skill_prose.py`:

```python
class DMDashboardProseTests(unittest.TestCase):
    """Bucket B: NPC speech renders as a concrete blockquoted, bold-labeled
    block, and a sound-cue block type bridges narration to the asset hub."""

    def test_npc_block_format_is_concrete(self):
        # The rule must say HOW, not just "in its own block".
        self.assertIn("bold speaker-labeled", SKILL)

    def test_sound_cue_block_exists(self):
        self.assertIn("🔊 **Cue:**", SKILL)

    def test_sound_cue_points_at_asset_hub(self):
        self.assertIn("assets.html", SKILL)

    def test_sound_cue_forbids_inventing_cues(self):
        idx = SKILL.find("🔊 **Cue:**")
        self.assertNotEqual(idx, -1)
        window = SKILL[idx - 400: idx + 400]
        self.assertIn("never invent a cue", window)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_prep_skill_prose.DMDashboardProseTests -v`
Expected: FAIL — `AssertionError` (substrings not present yet).

- [ ] **Step 3: Edit the NPC-block rule to be concrete**

In `skills/dnd/SKILL.md`, replace the bullet at line 203. Find:

```
- **Always put NPC speech in its own block, visually separated from DM narration** — even a one-line interjection; never inline dialogue into the narration paragraph. Dialogue stays visually split from narration and never gets voiced in the narrator's register (or the narrator's aside voiced as the NPC). This is also why the end-of-turn steer must be narration, never trailing an NPC's line.
```

Replace with (adds the concrete format sentence):

```
- **Always put NPC speech in its own block, visually separated from DM narration** — even a one-line interjection; never inline dialogue into the narration paragraph. Render it as a blockquoted, **bold speaker-labeled** line — `> **Nix:** "You're late."` — the strongest visual break chat markdown offers. Dialogue stays visually split from narration and never gets voiced in the narrator's register (or the narrator's aside voiced as the NPC). This is also why the end-of-turn steer must be narration, never trailing an NPC's line.
```

- [ ] **Step 4: Add the sound-cue block bullet**

In `skills/dnd/SKILL.md`, immediately after the (now-edited) line 203 NPC-block bullet, insert a new bullet:

```
- **When a scripted sound should fire, drop a sound-cue block** — on its own line, `🔊 **Cue:** *<handle>*`, where `<handle>` matches a button in the host's asset hub (`assets.html`). It is a standalone block like NPC speech — never bury it inside a narration paragraph or an NPC's dialogue line, so the host can spot it and click. Cue only sounds that appear on the campaign's ambient/SFX list — **never invent a cue** for a sound the host doesn't have.
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m unittest tests.test_prep_skill_prose.DMDashboardProseTests -v`
Expected: PASS (4 tests).

- [ ] **Step 6: Commit**

```bash
git add skills/dnd/SKILL.md tests/test_prep_skill_prose.py
git commit -m "feat(dnd): formalize NPC block + add sound-cue narration block"
```

---

### Task 2: `render_tracker.py` — live combat-tracker HTML

Deterministic render of the combat tracker from combat.py's `STATE_JSON`, tracker.py's `tracker.json`, and SRD condition text. Pure functions are unit-tested; the CLI wires paths and writes the file.

**Files:**
- Create: `skills/dnd/scripts/render_tracker.py`
- Test: `tests/test_render_tracker.py`

**Interfaces:**
- Consumes: `paths.find_campaign`, `paths.srd_path`, `paths.campaign_ruleset`; combatant dicts shaped like combat.py `STATE_JSON` (`{name, hp, max_hp, ac, initiative, conditions[]}`); `tracker.json` entities (`{<name-lower>: {conditions[], concentration, death_saves}}`).
- Produces: `condition_effects(srd: dict) -> dict[str,str]`; `render_tracker_html(combatants: list[dict], round_num: int, tracker_state: dict, cond_effects: dict[str,str]) -> str`; `main(argv=None)`. Later tasks invoke it as `python3 render_tracker.py --campaign <name> --state '<json>' [--round N]`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_render_tracker.py`:

```python
"""test_render_tracker.py — render_tracker.py builds combat-tracker HTML from
combatant STATE_JSON + tracker.json + SRD condition text. Pure-function tests,
no filesystem. Spec: docs/superpowers/specs/2026-07-15-dm-tool-html-dashboard-design.md
"""
import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import render_tracker  # noqa: E402

SRD = {"conditions": [
    {"name": "Poisoned", "index": "poisoned",
     "description": "- A poisoned creature has disadvantage on attack rolls and ability checks."},
    {"name": "Frightened", "index": "frightened",
     "description": "- A frightened creature has disadvantage on ability checks and attack rolls while the source of its fear is within line of sight."},
]}


class ConditionEffectsTests(unittest.TestCase):
    def test_collapses_srd_bullets_to_one_line(self):
        eff = render_tracker.condition_effects(SRD)
        self.assertEqual(
            eff["poisoned"],
            "A poisoned creature has disadvantage on attack rolls and ability checks.")


class RenderTrackerTests(unittest.TestCase):
    def setUp(self):
        self.eff = render_tracker.condition_effects(SRD)
        self.combatants = [
            {"name": "Ogre", "hp": 20, "max_hp": 59, "ac": 11,
             "initiative": 8, "conditions": ["poisoned"]},
            {"name": "Piper", "hp": 18, "max_hp": 24, "ac": 15,
             "initiative": 14, "conditions": []},
        ]

    def test_header_and_hp_render(self):
        out = render_tracker.render_tracker_html(self.combatants, 2, {}, self.eff)
        self.assertIn("Round 2", out)
        self.assertIn("Ogre", out)
        self.assertIn("20/59", out)

    def test_condition_effect_text_is_inline(self):
        out = render_tracker.render_tracker_html(self.combatants, 2, {}, self.eff)
        self.assertIn("disadvantage on attack rolls and ability checks", out)

    def test_first_row_is_active(self):
        out = render_tracker.render_tracker_html(self.combatants, 2, {}, self.eff)
        self.assertIn('class="row active"', out)

    def test_meta_refresh_present(self):
        out = render_tracker.render_tracker_html(self.combatants, 2, {}, self.eff)
        self.assertIn('http-equiv="refresh"', out)

    def test_tracker_json_merges_conditions_conc_and_death_saves(self):
        ts = {"piper": {"conditions": ["frightened"], "concentration": "Bless",
                        "death_saves": {"successes": 1, "failures": 2, "stable": False}}}
        out = render_tracker.render_tracker_html(
            [{"name": "Piper", "hp": 0, "max_hp": 24, "ac": 15,
              "initiative": 14, "conditions": []}], 3, ts, self.eff)
        self.assertIn("frightened", out)
        self.assertIn("Bless", out)
        self.assertIn("✔1", out)
        self.assertIn("✘2", out)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_render_tracker -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'render_tracker'`.

- [ ] **Step 3: Write `render_tracker.py`**

Create `skills/dnd/scripts/render_tracker.py`:

```python
#!/usr/bin/env python3
"""
render_tracker.py — emit a live combat-tracker HTML file (DM-side dashboard).

Merges the ephemeral combat STATE_JSON from combat.py with the persisted
tracker.json (conditions / concentration / death saves) and the bundled SRD
condition text, and writes <campaign>/tracker.html. The file carries a
meta-refresh so the DM's browser tab reloads itself each combat turn.

No server — a self-contained local page opened over file://.

Usage:
    python3 render_tracker.py --campaign <name> --state '<combatants_json>' [--round N]
        combatants_json: the STATE_JSON array printed by `combat.py init`.
        Writes <campaign_dir>/tracker.html and prints its path.
"""
from __future__ import annotations

import argparse
import html
import json
import sys

from paths import find_campaign, srd_path, campaign_ruleset


def condition_effects(srd: dict) -> dict:
    """Map condition index -> one-line effect text drawn from the SRD."""
    out = {}
    for c in srd.get("conditions", []):
        idx = str(c.get("index", c.get("name", ""))).lower()
        line = " ".join(
            part.lstrip("-• ").strip()
            for part in str(c.get("description", "")).splitlines()
            if part.strip()
        )
        out[idx] = line
    return out


def _merge_conditions(combatant: dict, tracker_state: dict) -> list:
    key = str(combatant["name"]).lower()
    persisted = tracker_state.get(key, {})
    return list(dict.fromkeys(
        [str(x).lower() for x in combatant.get("conditions", [])]
        + [str(x).lower() for x in persisted.get("conditions", [])]
    ))


def _extras(name: str, tracker_state: dict) -> dict:
    e = tracker_state.get(str(name).lower(), {})
    return {
        "concentration": e.get("concentration"),
        "death_saves": e.get("death_saves", {"successes": 0, "failures": 0, "stable": False}),
    }


def render_tracker_html(combatants: list, round_num: int,
                        tracker_state: dict, cond_effects: dict) -> str:
    rows = []
    for i, c in enumerate(combatants):
        name = html.escape(str(c["name"]))
        hp = c.get("hp", 0)
        max_hp = c.get("max_hp", hp) or 1
        pct = max(0, min(100, round(100 * hp / max_hp)))
        ac = html.escape(str(c.get("ac", "—")))
        init = html.escape(str(c.get("initiative", "—")))
        active = " active" if i == 0 else ""

        conds = _merge_conditions(c, tracker_state)
        if conds:
            cond_html = "".join(
                f'<span class="cond">{html.escape(cn)}'
                f'<em>{html.escape(cond_effects.get(cn, ""))}</em></span>'
                for cn in conds)
        else:
            cond_html = '<span class="none">—</span>'

        ex = _extras(c["name"], tracker_state)
        conc = (f'<div class="conc">◆ concentrating: '
                f'{html.escape(str(ex["concentration"]))}</div>'
                if ex["concentration"] else "")
        ds = ex["death_saves"]
        ds_html = ""
        if ds.get("successes") or ds.get("failures"):
            ds_html = (f'<div class="ds">death saves — ✔{ds.get("successes", 0)} '
                       f'✘{ds.get("failures", 0)}'
                       f'{" (stable)" if ds.get("stable") else ""}</div>')

        rows.append(
            f'<div class="row{active}">'
            f'<div class="init">{init}</div>'
            f'<div class="main"><div class="name">{name}</div>'
            f'<div class="conds">{cond_html}</div>{conc}{ds_html}</div>'
            f'<div class="hpbox"><div class="hpbar"><span style="width:{pct}%"></span></div>'
            f'<div class="hptext">{hp}/{max_hp} HP · AC {ac}</div></div>'
            f'</div>')

    body = "\n".join(rows)
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="4">
<title>Combat — Round {round_num}</title>
<style>
 body{{background:#14110e;color:#e8dcc8;font:15px/1.4 system-ui,sans-serif;margin:0;padding:16px}}
 h1{{font-size:18px;letter-spacing:.08em;text-transform:uppercase;color:#c9a86a;margin:0 0 12px}}
 .row{{display:flex;gap:12px;align-items:center;padding:10px 12px;border:1px solid #2c2620;border-radius:8px;margin-bottom:8px;background:#1c1813}}
 .row.active{{border-color:#c9a86a;box-shadow:inset 0 0 0 1px #c9a86a;background:#241d14}}
 .init{{font-size:20px;font-weight:700;color:#c9a86a;width:34px;text-align:center}}
 .main{{flex:1}} .name{{font-weight:600;font-size:16px}} .conds{{margin-top:3px}}
 .cond{{display:inline-block;background:#3a2c1c;color:#f0c987;border-radius:4px;padding:1px 7px;margin:2px 4px 0 0;font-size:12px}}
 .cond em{{display:block;font-style:normal;color:#b7a488;font-size:11px}}
 .none{{color:#6b6155}} .conc{{color:#8fb7d6;font-size:12px;margin-top:3px}}
 .ds{{color:#d68f8f;font-size:12px;margin-top:3px}}
 .hpbox{{width:150px}} .hpbar{{height:8px;background:#2c2620;border-radius:4px;overflow:hidden}}
 .hpbar span{{display:block;height:100%;background:#7fae5f}}
 .hptext{{font-size:12px;color:#b7a488;margin-top:3px;text-align:right}}
</style></head><body>
<h1>Combat — Round {round_num}</h1>
{body}
</body></html>'''


def main(argv=None):
    p = argparse.ArgumentParser(description="Render combat-tracker HTML.")
    p.add_argument("--campaign", required=True)
    p.add_argument("--state", required=True, help="STATE_JSON array from combat.py init")
    p.add_argument("--round", type=int, default=1)
    args = p.parse_args(argv)

    combatants = json.loads(args.state)
    camp = find_campaign(args.campaign)
    camp.mkdir(parents=True, exist_ok=True)

    tracker_state = {}
    tj = camp / "tracker.json"
    if tj.exists():
        try:
            tracker_state = json.loads(tj.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            tracker_state = {}

    try:
        path = srd_path(campaign_ruleset(args.campaign))
        srd = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        try:
            srd = json.loads(srd_path(None).read_text(encoding="utf-8"))
        except Exception:
            srd = {"conditions": []}
    effects = condition_effects(srd)

    out = camp / "tracker.html"
    out.write_text(render_tracker_html(combatants, args.round, tracker_state, effects),
                   encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_render_tracker -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add skills/dnd/scripts/render_tracker.py tests/test_render_tracker.py
git commit -m "feat(dnd): render_tracker.py — live combat-tracker HTML"
```

---

### Task 3: Prep asset lists — templates + prep-flow prose

Restrict maps to encounters, add the ambient + SFX list templates with sealed-campaign discipline, and wire the prep flow (`SKILL-commands.md` step 4) to generate all three into the campaign dir and build `assets.html`.

**Files:**
- Modify: `skills/dnd/templates/map-list.md`
- Create: `skills/dnd/templates/ambient-list.md`
- Create: `skills/dnd/templates/sfx-list.md`
- Modify: `skills/dnd/SKILL-commands.md` (prep step 4, near `SKILL-commands.md:299`)
- Test: `tests/test_asset_lists.py`

**Interfaces:**
- Consumes: nothing.
- Produces: template files following the Global-Constraints entry grammar; `SKILL-commands.md` prose referencing `ambient-list.md`, `sfx-list.md`, and `render_assets.py`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_asset_lists.py`:

```python
"""test_asset_lists.py — the three prep asset-list templates exist and carry the
sealed-campaign discipline; prep step 4 generates them and builds the asset hub.
"""
import pathlib
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
DND = REPO / "skills" / "dnd"
TPL = DND / "templates"
CMDS = (DND / "SKILL-commands.md").read_text(encoding="utf-8")


class AssetListTemplateTests(unittest.TestCase):
    def test_map_list_restricted_to_encounters(self):
        text = (TPL / "map-list.md").read_text(encoding="utf-8")
        self.assertIn("Encounter scenes only", text)
        self.assertIn("File: maps/", text)

    def test_ambient_list_exists_and_is_atmosphere_only(self):
        text = (TPL / "ambient-list.md").read_text(encoding="utf-8")
        self.assertIn("atmosphere only", text)
        self.assertIn("File: sounds/", text)

    def test_sfx_list_exists_and_forbids_leaking_the_trigger(self):
        text = (TPL / "sfx-list.md").read_text(encoding="utf-8")
        self.assertIn("sound only", text)
        self.assertIn("spine-guaranteed", text)
        self.assertIn("File: sounds/", text)


class PrepFlowTests(unittest.TestCase):
    def test_prep_generates_all_three_lists(self):
        self.assertIn("ambient-list.md", CMDS)
        self.assertIn("sfx-list.md", CMDS)

    def test_prep_builds_the_asset_hub(self):
        self.assertIn("render_assets.py", CMDS)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_asset_lists -v`
Expected: FAIL — `FileNotFoundError` (ambient/sfx templates absent) / `AssertionError`.

- [ ] **Step 3: Rewrite `map-list.md` (restrict to encounters, add `File:`)**

Overwrite `skills/dnd/templates/map-list.md`:

```markdown
# Map Shopping List — <Campaign>
*The maps the host places by hand. **Encounter scenes only** — tactical fights where
position matters; skip taverns, roads, and social scenes (those are theater of the mind).
Each entry describes a map's **look only** — never why the party goes there or what
happens. Bias to common, acquirable archetypes you can find or print.*

- **<short handle>** — <visual description: terrain, scale, notable features>. *Acquire:* <archetype to search/print>. File: maps/<handle>.png
```

- [ ] **Step 4: Create `ambient-list.md`**

Create `skills/dnd/templates/ambient-list.md`:

```markdown
# Ambient Soundscape List — <Campaign>
*Background loops the host plays per location. Main places only — a busy town square, a
crypt, a cave, and the like. Describe the **atmosphere only**, never the plot or why the
party is there. Downloads, not links: the host saves each as a local file under `sounds/`.*

- **<short handle>** — <atmosphere: the ambient bed, e.g. "warm crowd murmur, distant lute, hearth crackle">. *Find:* <search hint, e.g. "medieval tavern ambience" on Tabletop Audio / YouTube>. File: sounds/<handle>.mp3
```

- [ ] **Step 5: Create `sfx-list.md`**

Create `skills/dnd/templates/sfx-list.md`:

```markdown
# SFX Shopping List — <Campaign>
*One-shot sound effects for **spine-guaranteed events only** — named monster set-pieces
and fixed story beats certain to happen. NOT player-improvised actions (you can't
shopping-list a fireball a player might cast).*

*CRITICAL — describe the **sound only, stripped of its trigger**. Write "heavy
stone-on-stone collapse rumble", never "the cave that traps the party". The host must not
learn the plot from this list; they learn *when* to play it from the live `🔊 Cue` at the
table. Downloads, not links: the host saves each under `sounds/`.*

- **<short handle>** — <neutral sound description>. *Find:* <search hint>. File: sounds/<handle>.mp3
```

- [ ] **Step 6: Wire prep step 4 in `SKILL-commands.md`**

In `skills/dnd/SKILL-commands.md`, find step 4 (`SKILL-commands.md:299`):

```
4. **Map shopping list.** In a SEPARATE pass told "describe the look only, never why the
   party goes there or what happens," fill `templates/map-list.md`. Bias to common,
   acquirable archetypes. Keep the *Acquire* hint a terrain archetype ("large cavern map",
   "lava foundry map"), never a creature or plot label — the hint ships in the one artifact
```

Replace that step-4 heading line and add the two new lists + the hub build. Replace the line beginning `4. **Map shopping list.**` with:

```
4. **Asset shopping lists.** In a SEPARATE pass told "describe the asset only, never why
   the party goes there or what happens," generate three lists into the campaign dir by
   copying and filling the templates:
   - `map-list.md` from `templates/map-list.md` — **encounter scenes only** (tactical
     fights); skip social/exploration scenes. *Acquire* hint is a terrain archetype
     ("large cavern map"), never a creature or plot label.
   - `ambient-list.md` from `templates/ambient-list.md` — one loop per distinct notable
     location (town square, crypt, cave). Describe the atmosphere only.
   - `sfx-list.md` from `templates/sfx-list.md` — **spine-guaranteed events only** (named
     monster set-pieces, fixed story beats). Describe the **sound stripped of its
     trigger** so the list never spoils the host.
   Then build the host's asset hub:
   `python3 ${CLAUDE_SKILL_DIR}/scripts/render_assets.py --campaign <name>`
   These lists ship in the artifacts the host reads. Keep every hint acquirable and every
```

(This preserves the original sentence tail "…the hint ships in the one artifact" → now "…the artifacts the host reads. Keep every hint acquirable and every" — verify the following original lines still read coherently and adjust the connecting words only if needed; do not change step 5+.)

- [ ] **Step 7: Run test to verify it passes**

Run: `python3 -m unittest tests.test_asset_lists -v`
Expected: PASS (5 tests).

- [ ] **Step 8: Commit**

```bash
git add skills/dnd/templates/map-list.md skills/dnd/templates/ambient-list.md skills/dnd/templates/sfx-list.md skills/dnd/SKILL-commands.md tests/test_asset_lists.py
git commit -m "feat(dnd): ambient + SFX shopping lists, maps limited to encounters"
```

---

### Task 4: `render_assets.py` — asset-hub HTML

Parse the three campaign lists and render `assets.html`: map images, looped ambient toggles, one-shot SFX buttons. Pure functions unit-tested; CLI wires paths.

**Files:**
- Create: `skills/dnd/scripts/render_assets.py`
- Test: `tests/test_render_assets.py`

**Interfaces:**
- Consumes: `paths.find_campaign`; the entry grammar from Global Constraints; filled lists at `<campaign>/{map-list,ambient-list,sfx-list}.md`.
- Produces: `parse_asset_list(text: str) -> list[dict]` (each `{handle, desc, file}`); `render_assets_html(maps: list, ambient: list, sfx: list) -> str`; `main(argv=None)`. Invoked as `python3 render_assets.py --campaign <name>`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_render_assets.py`:

```python
"""test_render_assets.py — render_assets.py parses the three asset lists and
renders the asset-hub HTML. Pure-function tests, no filesystem.
"""
import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import render_assets  # noqa: E402


class ParseTests(unittest.TestCase):
    def test_parses_handle_desc_and_file_dropping_hint(self):
        text = ('# heading\n\n'
                '- **Collapse** — heavy stone-on-stone collapse rumble. '
                '*Find:* "cave collapse" on Tabletop Audio. File: sounds/sfx_collapse.mp3\n')
        self.assertEqual(render_assets.parse_asset_list(text), [
            {"handle": "Collapse",
             "desc": "heavy stone-on-stone collapse rumble",
             "file": "sounds/sfx_collapse.mp3"}])

    def test_ignores_non_entry_lines(self):
        self.assertEqual(render_assets.parse_asset_list("just prose\n- not an entry\n"), [])


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.html = render_assets.render_assets_html(
            maps=[{"handle": "Cavern", "desc": "big cave", "file": "maps/cavern.png"}],
            ambient=[{"handle": "Cave", "desc": "drips", "file": "sounds/cave.mp3"}],
            sfx=[{"handle": "Collapse", "desc": "rumble", "file": "sounds/sfx_collapse.mp3"}])

    def test_map_image_wired(self):
        self.assertIn('src="maps/cavern.png"', self.html)

    def test_ambient_is_looped_audio(self):
        self.assertIn('src="sounds/cave.mp3"', self.html)
        self.assertIn("loop", self.html)

    def test_sfx_button_wired(self):
        self.assertIn('src="sounds/sfx_collapse.mp3"', self.html)

    def test_assets_never_auto_refresh(self):
        # A refresh would reload the page and kill any playing ambient loop.
        self.assertNotIn('http-equiv="refresh"', self.html)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_render_assets -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'render_assets'`.

- [ ] **Step 3: Write `render_assets.py`**

Create `skills/dnd/scripts/render_assets.py`:

```python
#!/usr/bin/env python3
"""
render_assets.py — emit the DM-side asset-hub HTML (maps + ambient + SFX).

Parses the three filled shopping lists in the campaign dir and writes
<campaign>/assets.html, pre-wired to canonical filenames the host drops into
maps/ and sounds/. Static: it is NOT regenerated during play and carries no
meta-refresh, so playing ambient loops are never interrupted by a tracker regen.

No server — a self-contained local page opened over file://.

Usage:
    python3 render_assets.py --campaign <name>
        Reads <campaign>/{map-list,ambient-list,sfx-list}.md (any missing list is
        treated as empty), writes <campaign>/assets.html, ensures maps/ and
        sounds/ exist, and prints the html path.
"""
from __future__ import annotations

import argparse
import html
import re

from paths import find_campaign

_ENTRY = re.compile(
    r'^-\s+\*\*(?P<handle>.+?)\*\*\s*[—–-]+\s*(?P<body>.*?)\s*File:\s*(?P<file>\S+)\s*$')
_HINT = re.compile(r'\*(?:Acquire|Find):\*.*$')


def parse_asset_list(text: str) -> list:
    """Parse an asset-list markdown file into [{handle, desc, file}]."""
    items = []
    for raw in text.splitlines():
        m = _ENTRY.match(raw.strip())
        if not m:
            continue
        desc = _HINT.sub("", m.group("body")).strip().rstrip(".").strip()
        items.append({"handle": m.group("handle").strip(),
                      "desc": desc,
                      "file": m.group("file").strip()})
    return items


def _section_maps(maps: list) -> str:
    if not maps:
        return '<p class="none">No maps.</p>'
    return "".join(
        f'<figure><img src="{html.escape(m["file"])}" alt="{html.escape(m["handle"])}" '
        f'loading="lazy"><figcaption>{html.escape(m["handle"])}</figcaption></figure>'
        for m in maps)


def _section_audio(items: list, prefix: str, loop: bool) -> str:
    if not items:
        return '<p class="none">None.</p>'
    out = []
    for i, a in enumerate(items):
        aid = f"{prefix}{i}"
        loop_attr = " loop" if loop else ""
        icon = "▶" if loop else "🔊"
        onclick = f"tog('{aid}',this)" if loop else f"one('{aid}')"
        out.append(
            f'<div class="asset">'
            f'<audio id="{aid}"{loop_attr} src="{html.escape(a["file"])}"></audio>'
            f'<button onclick="{onclick}">{icon} {html.escape(a["handle"])}</button>'
            f'<span class="desc">{html.escape(a["desc"])}</span></div>')
    return "".join(out)


def render_assets_html(maps: list, ambient: list, sfx: list) -> str:
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>Asset Hub</title>
<style>
 body{{background:#14110e;color:#e8dcc8;font:15px/1.5 system-ui,sans-serif;margin:0;padding:16px}}
 h2{{font-size:15px;letter-spacing:.08em;text-transform:uppercase;color:#c9a86a;margin:20px 0 8px;border-bottom:1px solid #2c2620;padding-bottom:4px}}
 .maps{{display:flex;flex-wrap:wrap;gap:12px}}
 figure{{margin:0}} figure img{{max-width:220px;border-radius:6px;display:block}}
 figcaption{{font-size:12px;color:#b7a488;margin-top:4px}}
 .asset{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
 button{{background:#3a2c1c;color:#f0c987;border:1px solid #5a4426;border-radius:6px;padding:6px 12px;font-size:14px;cursor:pointer}}
 button.on{{background:#5a4426;color:#ffe4a8}}
 .desc{{font-size:12px;color:#b7a488}} .none{{color:#6b6155}}
</style></head><body>
<h2>Maps</h2>
<div class="maps">{_section_maps(maps)}</div>
<h2>Ambient</h2>
{_section_audio(ambient, "amb", True)}
<h2>SFX</h2>
{_section_audio(sfx, "sfx", False)}
<script>
 function one(id){{var a=document.getElementById(id);a.currentTime=0;a.play();}}
 function tog(id,btn){{var a=document.getElementById(id);
  if(a.paused){{a.play();btn.classList.add("on");}}
  else{{a.pause();btn.classList.remove("on");}}}}
</script>
</body></html>'''


def _read(camp, name: str) -> str:
    p = camp / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def main(argv=None):
    p = argparse.ArgumentParser(description="Render the asset-hub HTML.")
    p.add_argument("--campaign", required=True)
    args = p.parse_args(argv)

    camp = find_campaign(args.campaign)
    camp.mkdir(parents=True, exist_ok=True)
    (camp / "maps").mkdir(exist_ok=True)
    (camp / "sounds").mkdir(exist_ok=True)

    maps = parse_asset_list(_read(camp, "map-list.md"))
    ambient = parse_asset_list(_read(camp, "ambient-list.md"))
    sfx = parse_asset_list(_read(camp, "sfx-list.md"))

    out = camp / "assets.html"
    out.write_text(render_assets_html(maps, ambient, sfx), encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_render_assets -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add skills/dnd/scripts/render_assets.py tests/test_render_assets.py
git commit -m "feat(dnd): render_assets.py — maps/ambient/SFX asset-hub HTML"
```

---

### Task 5: Wire tracker into the combat loop + document both scripts

Make the turn loop refresh `tracker.html` each combat turn, and document both render scripts in `SKILL-scripts.md`. Guard tests confirm the wiring prose is present.

**Files:**
- Modify: `skills/dnd/SKILL.md` (combat sequence, `SKILL.md:291-296`)
- Modify: `skills/dnd/SKILL-scripts.md` (add two script sections)
- Test: `tests/test_prep_skill_prose.py` (extend `DMDashboardProseTests`)

**Interfaces:**
- Consumes: `render_tracker.py` (Task 2), `render_assets.py` (Task 4).
- Produces: `SKILL.md` combat prose naming `render_tracker.py`; `SKILL-scripts.md` sections naming both scripts.

- [ ] **Step 1: Write the failing test**

Add these methods to the existing `DMDashboardProseTests` class in `tests/test_prep_skill_prose.py`:

```python
    def test_combat_loop_refreshes_tracker_html(self):
        self.assertIn("render_tracker.py", SKILL)

    def test_scripts_doc_covers_both_render_scripts(self):
        self.assertIn("render_tracker.py", SCRIPTS)
        self.assertIn("render_assets.py", SCRIPTS)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_prep_skill_prose.DMDashboardProseTests -v`
Expected: FAIL — the two new assertions fail (existing four still pass).

- [ ] **Step 3: Wire the combat sequence in `SKILL.md`**

In `skills/dnd/SKILL.md`, find the combat sequence step (`SKILL.md:293-294`):

```
d. Write the full narration for this turn as chat prose. Put any NPC speech in its own
   visually distinct block, separate from DM narration (see "Narration principles").
```

Insert a new step immediately after it (before step `e.` "Persist stat changes"):

```
d2. Refresh the host's combat tracker from the current turn's state:
    `python3 ${CLAUDE_SKILL_DIR}/scripts/render_tracker.py --campaign <name> --state '<STATE_JSON>' --round <n>`
    Pass the same combatant STATE_JSON you pipe through `combat.py` (ordered so the current
    turn's actor is first — it renders as the highlighted active row). Only during combat;
    out of combat, leave `tracker.html` untouched.
```

- [ ] **Step 4: Document both scripts in `SKILL-scripts.md`**

In `skills/dnd/SKILL-scripts.md`, append a new section at the end of the file:

```markdown
---

## Combat-Tracker Render — `scripts/render_tracker.py`

Writes the host-side `tracker.html` (DM dashboard) from the live combat state. Call it at
the end of **each combat turn**, passing the same combatant `STATE_JSON` you pipe through
`combat.py`, ordered so the current actor is first (it becomes the highlighted active row).
Merges persisted conditions/concentration/death-saves from `tracker.json` and shows each
condition's SRD effect inline. The file carries a meta-refresh so the browser tab reloads
itself. No server.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_tracker.py \
  --campaign <name> --state '<STATE_JSON from combat.py>' --round <n>
```

Out of combat, do not call it — leave the last tracker in place.

## Asset-Hub Render — `scripts/render_assets.py`

Writes the host-side `assets.html` (maps + ambient loops + SFX buttons) from the three
prep shopping lists in the campaign dir (`map-list.md`, `ambient-list.md`, `sfx-list.md`).
Run once at the end of prep, and again any time the host adds or renames sound/map files.
Buttons are pre-wired to the canonical filenames; a button whose file is not yet in
`maps/`/`sounds/` simply plays nothing until the file exists. This file is **static** — it
carries no meta-refresh, so a combat-tracker regen never interrupts a playing ambient loop.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_assets.py --campaign <name>
```
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m unittest tests.test_prep_skill_prose.DMDashboardProseTests -v`
Expected: PASS (6 tests).

- [ ] **Step 6: Run the full suite**

Run: `python3 -m unittest discover -s tests -v`
Expected: PASS — all pre-existing tests plus the new `test_render_tracker`, `test_render_assets`, `test_asset_lists`, and `DMDashboardProseTests`.

- [ ] **Step 7: Commit**

```bash
git add skills/dnd/SKILL.md skills/dnd/SKILL-scripts.md tests/test_prep_skill_prose.py
git commit -m "feat(dnd): refresh tracker.html each combat turn + document render scripts"
```

---

## End-to-end smoke check (after all tasks)

Not a unit test — a manual confirmation the two files render and open:

```bash
# From skills/dnd/scripts, with a throwaway campaign:
python3 render_tracker.py --campaign smoke --state '[{"name":"Ogre","hp":20,"max_hp":59,"ac":11,"initiative":8,"conditions":["poisoned"]},{"name":"Piper","hp":18,"max_hp":24,"ac":15,"initiative":14,"conditions":[]}]' --round 2
python3 render_assets.py --campaign smoke
```

Open the printed `tracker.html` and `assets.html` paths in a browser. Confirm: the active
row is highlighted, poisoned shows its effect inline, the HP bars render; the asset hub
shows the three section headers and any list entries as buttons/images. (With no lists
filled, the hub shows "No maps." / "None." — expected.)

## Finish

Complete per `superpowers:finishing-a-development-branch` (branch `dm-html-dashboard`).

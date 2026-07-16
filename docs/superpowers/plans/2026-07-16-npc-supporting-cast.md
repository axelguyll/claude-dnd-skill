# NPC Supporting-Cast Tier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Seed 6–8 index-only "supporting cast" NPCs at campaign creation (both `/dm:dnd new` and `/dm:dnd prep`), promoted to full npcs-full.md entries on demand during play.

**Architecture:** Prose-only feature — no script changes. Two seeding-site additions in SKILL-commands.md, one promotion rule in SKILL.md, a template note, glossary + architecture doc updates. Contracts are locked in by a deterministic prose test (regex over the md files), following the existing `tests/test_prep_skill_prose.py` pattern.

**Tech Stack:** Markdown prose docs; Python unittest for prose-contract tests.

**Spec:** `docs/superpowers/specs/2026-07-16-npc-supporting-cast-design.md`

## Global Constraints

- Supporting-cast seed count: **6–8**, at both sites.
- Supporting row fields: Name / Role / Faction or "independent" / Location / Attitude / Notes = **exactly one distinct playable trait**.
- No npcs-full.md entry, no relationship-web requirement for supporting cast.
- Name-registry uniqueness check applies to supporting cast (same as core NPCs).
- Tier membership convention: an NPC is core **iff** a section for them exists in npcs-full.md. No tier column, no marker in the index.
- Never touch `~/.claude/dnd/campaigns/` (live campaign data).
- Repo prose docs live in `skills/dnd/`; the installed plugin cache is stale — never read or edit it.

---

### Task 1: Prose contracts — seeding steps, promotion rule, template note

**Files:**
- Test: `tests/test_supporting_cast_prose.py` (create)
- Modify: `skills/dnd/SKILL-commands.md` (after step 11 at line ~37; inside prep step 1.5 at line ~331)
- Modify: `skills/dnd/SKILL.md` (read-before-dialogue bullet, line ~221)
- Modify: `skills/dnd/templates/npcs.md` (note after the index table)

**Interfaces:**
- Consumes: nothing (first task).
- Produces: the phrase "supporting cast" as a defined term in all three prose docs; step number `11.5` in SKILL-commands.md (Task 2's ARCHITECTURE/CONTEXT text refers to it).

- [ ] **Step 1: Write the failing prose test**

Create `tests/test_supporting_cast_prose.py`:

```python
"""test_supporting_cast_prose.py — prose contracts for the supporting-cast NPC
tier: seeding steps in SKILL-commands.md (new 11.5, prep 1.5), the promotion
rule in SKILL.md, and the template note. Spec:
docs/superpowers/specs/2026-07-16-npc-supporting-cast-design.md
"""
import pathlib
import re
import unittest

DND = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd"
COMMANDS = (DND / "SKILL-commands.md").read_text(encoding="utf-8")
SKILL = (DND / "SKILL.md").read_text(encoding="utf-8")
NPCS_TEMPLATE = (DND / "templates" / "npcs.md").read_text(encoding="utf-8")


class NewCommandSeedingTests(unittest.TestCase):
    def test_new_has_step_11_5_supporting_cast(self):
        m = re.search(r"^11\.5 \*\*Supporting cast\.\*\*", COMMANDS, re.M)
        self.assertIsNotNone(m, "new needs step 11.5 'Supporting cast.'")

    def test_step_11_5_seeds_6_to_8_index_only(self):
        step = re.search(r"^11\.5 .*?(?=^\d+\.)", COMMANDS, re.M | re.S).group(0)
        self.assertIn("6–8", step)
        self.assertIn("npcs.md", step)
        self.assertIn("one distinct", step)
        self.assertIn("name-registry", step.lower())
        self.assertNotIn("npcs-full.md entry is required", step)

    def test_step_11_5_excludes_full_entries(self):
        step = re.search(r"^11\.5 .*?(?=^\d+\.)", COMMANDS, re.M | re.S).group(0)
        self.assertIn("No npcs-full.md entry", step)


class PrepSeedingTests(unittest.TestCase):
    def _step_1_5(self):
        return re.search(r"^1\.5 \*\*NPC layer\.\*\*.*?(?=^2\. )",
                         COMMANDS, re.M | re.S).group(0)

    def test_prep_1_5_has_supporting_cast_pass(self):
        self.assertIn("supporting cast", self._step_1_5())

    def test_prep_supporting_pass_is_new_names_only(self):
        self.assertIn("new names only", self._step_1_5())

    def test_prep_supporting_pass_counts_match_new(self):
        self.assertIn("6–8", self._step_1_5())


class PromotionRuleTests(unittest.TestCase):
    def test_skill_md_defines_promotion(self):
        self.assertIn("supporting cast", SKILL)
        self.assertRegex(SKILL, r"author(?:ing)? their full entry")

    def test_promotion_is_before_dialogue(self):
        idx = SKILL.find("supporting cast")
        window = SKILL[idx:idx + 600]
        self.assertIn("before writing the dialogue", window)


class TemplateNoteTests(unittest.TestCase):
    def test_npcs_template_names_the_tier(self):
        self.assertIn("supporting cast", NPCS_TEMPLATE.lower())
        self.assertIn("npcs-full.md", NPCS_TEMPLATE)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_supporting_cast_prose.py -v`
Expected: FAIL — every test (none of the phrases exist yet).

- [ ] **Step 3: Add step 11.5 to `/dm:dnd new` in SKILL-commands.md**

Insert between step 11 (line ~37, "3 NPCs with relationship web") and step 12 ("3–5 Quest Seeds"):

```markdown
11.5 **Supporting cast.** Seed 6–8 index-only NPCs anchored to the settlement and the
   Three Truths locations — the places the party will actually walk (innkeeper, gate
   sergeant, fence, ferryman, market fixture). One row each in the npcs.md index table
   (Name / Role / Faction or "independent" / Location / Attitude / Notes); the Notes
   field carries exactly one distinct, playable trait (a verbal tic, a visible
   contradiction, a small motivation — *"counts coins twice, hums when lying"*). No
   npcs-full.md entry and no relationship-web requirement. Run the name-registry
   uniqueness check on each name (as step 11 does). They are promoted to full entries
   on demand during play — see the promotion rule in SKILL.md (Active DM Mode).
```

- [ ] **Step 4: Append the supporting-cast pass to prep step 1.5**

In SKILL-commands.md step 1.5 (line ~331, ends "...must name one of these NPCs or factions."), append to the step:

```markdown
   Then the supporting cast: seed 6–8 additional index-only NPCs anchored to the
   settlement and Adventure Nodes — **new names only** (anyone already named in
   world.md got a full entry above; this pass adds breadth, not duplicates). Same row
   format, same one-distinct-trait Notes rule, and same name-registry check as `new`
   step 11.5. No npcs-full.md entry, no relationship web.
```

- [ ] **Step 5: Add the promotion rule to SKILL.md**

In the Active DM Mode bullet at line ~221 ("**Before writing substantive dialogue or decisions for any named NPC**, read their full entry in `npcs-full.md` if one exists. ..."), append these sentences to the same bullet:

```markdown
An index row with no npcs-full.md section is **supporting cast**: when a scene centers
on them, or before their first substantive dialogue, author their full entry (all
fields — stats, personality axes, secret, ≥2 relationships, schedule) *then*, before
writing the dialogue. Promotion is one-way. NPCs you improvise and name mid-scene enter
the roster as supporting-cast index rows by default and follow the same rule.
```

- [ ] **Step 6: Add the tier note to templates/npcs.md**

After the index table (line 5), before the `---`, insert:

```markdown
*Index rows without a matching section in npcs-full.md are **supporting cast** —
promote to a full entry before their first substantive dialogue (see SKILL.md,
Active DM Mode).*
```

- [ ] **Step 7: Run test to verify it passes**

Run: `python -m pytest tests/test_supporting_cast_prose.py -v`
Expected: PASS (all tests).

Also run the existing prose/regression suite to catch collateral breakage:
`python -m pytest tests/test_prep_skill_prose.py tests/test_no_display_refs.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add tests/test_supporting_cast_prose.py skills/dnd/SKILL-commands.md skills/dnd/SKILL.md skills/dnd/templates/npcs.md
git commit -m "feat: supporting-cast NPC tier — index-only seeding + promotion rule"
```

---

### Task 2: Glossary + architecture docs

**Files:**
- Modify: `CONTEXT.md` (add glossary entry in the NPC/roster vocabulary area — place near existing NPC-related terms; if none, append to the most fitting `## Language` section)
- Modify: `docs/ARCHITECTURE.md` (NPC-layer descriptions)

**Interfaces:**
- Consumes: term *supporting cast* and step number 11.5 as defined in Task 1.
- Produces: canonical glossary definition later docs can cite.

- [ ] **Step 1: Add CONTEXT.md glossary entry**

Follow the existing entry format (bold term, definition paragraph, `_Avoid_:` line). Add:

```markdown
**Supporting cast**:
The cheap NPC tier: an index-only row in npcs.md (Name/Role/Faction/Location/Attitude/
Notes with exactly one distinct playable trait) and **no npcs-full.md section** — that
absence *is* the tier marker; there is no tier column. Seeded 6–8 at creation by both
`/dm:dnd new` (step 11.5) and `/dm:dnd prep` (step 1.5 supporting pass), and by default
for NPCs improvised mid-scene. Promoted one-way to a full entry before their first
substantive dialogue (SKILL.md, Active DM Mode).
_Avoid_: "minor NPC", "background NPC" (undefined); calling a promoted NPC "supporting"
after their full entry exists.
```

- [ ] **Step 2: Update docs/ARCHITECTURE.md**

Its header requires an update on any lifecycle-step change. Find the sections describing `/dm:dnd new` NPC seeding and prep's NPC layer (search for "NPC layer" and "step 11"), and update them to mention: two-tier seeding (3 full + 6–8 supporting at `new`; coverage-driven full + 6–8 supporting at prep), and the membership convention (core iff npcs-full.md section exists). Keep each mention to 1–2 sentences in the file's existing style. If no prose describes NPC seeding in detail, add one line to the lifecycle/prep description rather than a new section.

- [ ] **Step 3: Run the full test suite**

Run: `python -m pytest tests/ -v --timeout=120`
Expected: PASS (docs changes can't break code tests; this is the pre-commit gate).
If `--timeout` is not installed, run without it.

- [ ] **Step 4: Commit**

```bash
git add CONTEXT.md docs/ARCHITECTURE.md
git commit -m "docs: glossary + architecture entries for supporting-cast tier"
```

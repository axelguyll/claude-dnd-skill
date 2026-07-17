# D&D Skill — Command Procedures

Full step-by-step procedures for all `/dm:dnd` slash commands. Load this file at `/dm:dnd load` or before executing any slash command.

> **Path note:** commands below use `${CLAUDE_SKILL_DIR}` for the skill directory. This file is read verbatim, so that token is **not** auto-expanded here — substitute the absolute skill-dir path (from `SKILL.md`) before running any command, or it will fail with a broken `/scripts/…` path.

---

## `/dm:dnd new <campaign-name> [tone]`

> **Legacy mode (no leveling).** This milestone-only fork levels via authored beats; dynamic/sandbox campaigns started here have no leveling path. For a levelable campaign use `/dm:dnd prep`.

1. **Session setup — call `AskUserQuestion`**:

   ***"Dice rolls?"*** — set how PC d20s are handled (see SKILL.md "Dice convention"):
   - `Players roll their own` (default) → write `roll_mode: players` to `state.md → ## Session Flags`. You will call for each PC roll and wait — never auto-roll a PC.
   - `DM rolls everything openly` → write `roll_mode: auto`. You resolve PC rolls yourself with full math shown.

   Default to `roll_mode: players` if the question is dismissed.
2. **Ruleset selection (added 2026-05-08).** Ask: *"D&D 5e ruleset for this campaign? **2014** (SRD 5.1, default — full mechanics, classic Player's Handbook structure) or **2024** (SRD 5.2, weapon mastery + origin feats + background ASIs + revised exhaustion)?"* Default to `2014` if no answer or ambiguous. Write the chosen value to `state.md` header line as `**Ruleset:** 2014` or `**Ruleset:** 2024`.

   If 2024 was chosen: verify the dataset exists with `ls ${CLAUDE_SKILL_DIR}/data/dnd5e_srd_2024.json`. If missing, run `python3 ${CLAUDE_SKILL_DIR}/scripts/build_srd.py --ruleset 2024` (one-time, ~3 min). Until the dataset exists, lookup-based features will fall back to 2014.
3. `mkdir -p ~/.claude/dnd/campaigns/<name>/characters`
4. Copy and populate templates from `${CLAUDE_SKILL_DIR}/templates/` — state.md, world.md, npcs.md, session-log.md. The state.md header keeps the `**Ruleset:**` field set in step 2.
5. Ask: **party size** and **starting level**
6. **Tone/Genre Wizard** — present all four in one message:
   - Tone: present the ids from the shared Tone Catalog (`data/tones.yaml`) — heroic /
     mythic / grimdark / horror / intrigue / swashbuckling / cosmic (descriptor per entry)
   - Magic level: `none / low / medium / high`
   - Setting type: `medieval / renaissance / ancient / nautical / underground`
   - Danger level: `lethal / gritty / standard / heroic`
   *(If `[tone]` supplied, pre-fill Tone and ask remaining three. Randomise any blank via dice.py and log `"d6=N → [result]"` in world.md.)*
7. **World Foundations** — geography/biome/climate, magic system, pantheon (2–3 active deities), calendar. Write to `## World Foundations` in world.md. Seed `state.md → ## World State → In-world date`.
8. **Three Truths** — one settlement, one nearby threat, one mystery (with clue trail). Write to respective sections in world.md.
9. **Threat Escalation Arc** — fill the five-stage table in world.md immediately after threat generation. Set current stage to 1. Write `Threat arc stage: 1 — Now` to `state.md → ## World State`.
10. **2 Factions** — archetype, all fields including current activity. Write to `## Factions` in world.md. Write one-line faction-activity entries to `state.md → ## World State → Faction activity`.
11. **3 NPCs with relationship web** — full entries (role, stats, demeanor, motivation, secret, speech quirk, faction, current goal, schedule, personality axes). Generate all three first, then fill Relationships (every NPC needs ≥2 links to others). Update index table.
11.5 **Supporting cast.** Seed 6–8 index-only NPCs anchored to the settlement and the
   Three Truths locations — the places the party will actually walk (innkeeper, gate
   sergeant, fence, ferryman, market fixture). One row each in the npcs.md index table
   (Name / Role / Faction or "independent" / Location / Attitude / Notes); the Notes
   field carries exactly one distinct, playable trait (a verbal tic, a visible
   contradiction, a small motivation — *"counts coins twice, hums when lying"*).
   No npcs-full.md entry and no relationship-web requirement. Run the name-registry
   uniqueness check on each name (as step 11 does). They are promoted to full entries
   on demand during play — see the promotion rule in SKILL.md (Active DM Mode).
12. **3–5 Quest Seeds** from threat, factions, mystery, NPC motivations. Write to `## Quest Seed Bank` in world.md.
13. **Dynamic Campaign Arc** — auto-generate the arc from all world data just created. Use Opus for this step. Ask: *"Generate a committed narrative arc? [y/n — recommended]"*

   **If yes:** Drawing from theme, threat arc stages, factions, Three Truths, NPC motivations, and quest seeds, derive:
   - **`theme`** — one sentence: what is this story ultimately about? Not the threat — its meaning.
   - **`resolution`** — the committed endpoint shape: if the party succeeds, what's the emotional truth? Keep specific events open; commit to the shape.
   - **Acts 1–3**, each with 2 beats. Each beat has:
     - `label` — a dramatic name
     - `what_changes` — before/after: what's fundamentally different once this lands? **CRITICAL: write this as a CONSEQUENCE, not an event.** A consequence is a state-of-the-world after the beat. An event is one specific thing that happens. Consequences survive when players pre-empt the obvious event delivery; events break and the beat goes stale. Example contrast for a 2b "All Is Lost" beat:
       - ❌ Event-shaped (fragile): *"Vedra's nomination succeeds and she takes the third seat."* If the party flips the clerk, this can't land — beat goes stale.
       - ✅ Consequence-shaped (robust): *"The party experiences a concrete cost from the Kept's escalation that they cannot reverse — a cover blown, an ally compromised, or a position they relied on no longer available."* This survives multiple delivery paths.
     - `world_pressure` — the specific faction or NPC move (naming actual entities from this world) that makes the beat feel inevitable. This MAY be event-shaped — but if the players pre-empt it, you're expected to revise per SKILL.md rule 8 (pre-emption is a revision trigger).
   - **`steering_notes`** — how to reach the first beat without forcing it

   Beat layout:
   - Act 1: **1a Inciting Incident** (the threat becomes personal for the party), **1b Complication** (the problem is bigger or stranger than it first appeared)
   - Act 2: **2a Midpoint Shift** (what the party *thought* they were doing changes), **2b All Is Lost** (a genuine setback — something fails, is lost, or collapses)
   - Act 3: **3a Final Confrontation** (the decisive moment the campaign turns on), **3b Resolution** (what's different about the world and the characters after)

   Write to `state.md → ## Campaign Arc` with `type: dynamic`. Deliver a one-paragraph arc summary to the DM.

   **If no:** Write `type: sandbox` to `## Campaign Arc`. The story remains open-ended with no arc tracking.

14. Write state.md with session count 0, starting location.
15. Confirm creation, offer `/dm:dnd character new`.

---

## `/dm:dnd load <campaign-name>`
0. **Pick the campaign if none was named.** If `<campaign-name>` was supplied (or the player clearly named one), use it. Otherwise `ls` the campaigns dir (`~/.claude/dnd/campaigns/` or `$DND_CAMPAIGN_ROOT/campaigns/`) and **call `AskUserQuestion`**: *"Which campaign?"* with the existing campaign names as options (most-recently-played first — sort by `state.md` mtime). The player can pick "Other" to type a name. If there are no campaigns, tell them and offer `/dm:dnd new`.
1. **Session setup — call `AskUserQuestion`** (not a typed y/n prompt):

   ***"Dice rolls?"*** — confirm how PC d20s are handled this session (see SKILL.md "Dice convention"). Pre-fill the recommended option from the existing `roll_mode` in `state.md` if present, else `players`:
   - `Players roll their own` → write `roll_mode: players`. Call for each PC roll and wait — never auto-roll a PC.
   - `DM rolls everything openly` → write `roll_mode: auto`. Resolve PC rolls yourself with full math shown.

   (Default if the player dismisses: `roll_mode: players` — or the existing saved value.)

   In the same `AskUserQuestion` call, add a second question: ***"How long are you playing today?"*** → `Short` / `Standard` / `Open-ended`. Write the answer as `session_length` to `state.md → ## Session Flags` (default `standard` if dismissed). This paces the session shape — see SKILL.md Standard 6 (pressure point by scene 2 for short, scene 3–4 for standard, re-raised every 3–4 scenes for open-ended).

2. **Backwards-compat: ruleset migration check.** Before reading state.md, run:

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/migrate_ruleset.py <campaign-name> --check
   ```

   - Exit code `0` (`migrated`) → proceed to step 3.
   - Exit code `1` (`needs-migration`) → this is a legacy campaign predating the ruleset field. Surface to DM exactly once: *"Campaign predates ruleset versioning. Stamp as **2014** (recommended for legacy campaigns) or **2024**? state.md will be backed up to `state.md.backup-pre-ruleset-<timestamp>` before any write. [2014/2024/skip]"*. On answer, run:

     ```bash
     python3 ${CLAUDE_SKILL_DIR}/scripts/migrate_ruleset.py <campaign-name> --ruleset 2014 --yes
     # or --ruleset 2024
     ```

     Migrator is idempotent and creates a timestamped backup. On `skip`, do not migrate; `paths.campaign_ruleset()` will return `2014` as the safety default at read time, but the field stays unstamped (DM will be re-prompted next load).
   - Exit code `2` (`missing`) → state.md not found; do not proceed with /dm:dnd load. Surface error to DM.

   Future migrations (e.g. when 2026 ruleset arrives) follow the same pattern: a small migrator script under `scripts/migrate_<topic>.py` invoked here as a `--check` then `--yes` pair.

3. **Read campaign ruleset** for this session: `python3 ${CLAUDE_SKILL_DIR}/scripts/paths.py campaign-ruleset <name>` (or import `campaign_ruleset` directly). Stash the result; pass `--ruleset <value>` to `lookup.py`, `build_supplemental.py`, and `combat.py` mastery calls so they route to the correct dataset.

4. Read SKILL-scripts.md (for script syntax this session)
5. **Mark this campaign active** (for the autosave hook): write `{"name": "<campaign-name>", "skill_dir": "<absolute skill-dir path>"}` to `$(python3 ${CLAUDE_SKILL_DIR}/scripts/paths.py runtime-dir)/active-campaign.json`. This is what `autosave_checkpoint.py` reads to know which campaign to checkpoint (it reads only the `name` key and tolerates extras); a stale marker is harmless. The `skill_dir` key is the post-compaction recovery anchor for the skill's own path — the runtime dir is derivable cold, the skill dir is not. Then read state.md, world.md, npcs.md (index only), session-tail.md (5–8 bullets — last session's final stretch, for the recap), and all characters/*.md
   - **If any character sheet carries `⚠ LEVEL UP PENDING (Level N)`:** surface it and run `/dm:dnd level up` before play begins — the marker means a beat completed but its level-up passes never ran, and the spine's banding math assumes the level was applied.
   - **state.md contains `## DM Style Notes`** — read and internalize before narrating anything. These are table-specific calibration patterns that override default DM instincts.
   - **world.md:** Load in full — World Foundations, Three Truths, and factions inform narration and faction moves. Do NOT read `world-seeds.md` at load (generation artifact, not live reference).
   - **world-nodes.md (imported campaigns only):** Do **NOT** load at session start. It holds the full Quest Seed Bank and Adventure Nodes for the whole module; read only the current act's nodes on demand when a scene needs them. If the file is absent (dynamic/sandbox, or an older import), there is nothing to lazy-load — `world.md` already carries the nodes, unchanged from prior behavior.
   - **arc.md (imported campaigns only):** Do **NOT** load at session start. `state.md → ## Campaign Arc` already carries the current + next chapter window. Read `arc.md` only when advancing chapters or when a player asks about the broader arc. If absent, the arc lives inline in `state.md` (dynamic/sandbox) — read it there as before.
   - **spine.json (authored campaigns only):** Do **NOT** load at session start. For a
     `type: authored` arc, `state.md → ## Campaign Arc` already carries theme/resolution and
     the current beat window (`current_beat`, `beats`, `steering_notes`) — read the arc there,
     exactly as for dynamic. Read `spine.json` only when a beat completes, if advancing it needs
     its `level_up_to`/`gear`/`threats`. This keeps the heavy spine off the hot path.
   - **source/<chapter-id>.md (imported campaigns only):** the full module text, one file per chapter. Never loaded at session start. Before running a scene in a chapter, read that chapter's `source/<id>.md` (the `source_ref` in the arc) — and only that chapter. This is the predefined-story equivalent of reading a single NPC's full entry on demand.
   - **npcs.md:** Index row only at load. **Before writing substantive dialogue or decisions for any named NPC, read their full entry in `npcs-full.md`.** Do not wait for an explicit `/dm:dnd npc [name]` call — do it proactively when a scene centers on that character. Index rows carry surface traits only; personality axes, relationships, and hidden goals are in the full entry.
   - **Do NOT read session-log.md at load** — recent events are already in `state.md → ## Recent Events`. Only read session-log.md if the player explicitly requests a recap, or if DM Calibration from the last 1-2 sessions is needed and not already internalized.
6. **Pull scene-context from the campaign graph.** Always run, even if you suspect `graph.json` doesn't exist — the script exits cleanly with a notice when uninitialized.
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/campaign_graph.py scene-context \
     --campaign <campaign-name> \
     --place "<current-location-name-or-id>" \
     --present "<comma-separated-NPC-names-likely-present>" \
     --hops 2 \
     --at-session <current-session-N>
   ```
   Identify `<current-location>` from `state.md → ## World State → location` (or the most recent location in `## Recent Events`). Identify `<present>` from the NPCs likely on-scene per `state.md` / `session-log.md`. `<current-session-N>` is `state.md → ## Session Count`.

   Output is a focused subgraph (nodes by type + relationships block). **Internalize this subgraph before delivering the recap** — it is the authoritative source for who-relates-to-whom in the current scene. Do not re-read `npcs-full.md` for relationships you can answer from the subgraph.

   If output reads `# graph not initialized` — graph hasn't been seeded for this campaign yet. **Graph init is a hard requirement, not deferrable.** The continuity-archive compression rule (see `/dm:dnd save`) assumes graph.json is present and canonical for relational state; deferring init creates state-archive drift that compounds session-over-session. Run the init flow before delivering the recap:

   1. **Detect legacy.** A campaign is "legacy" if any of: `Session count > 1` in state.md header, OR `## Continuity Archive` has at least one `### Session N` entry, OR session-log.md is > 100 lines. A freshly-created campaign at `/dm:dnd new` time fails all three signals — do NOT classify it as legacy.

   2. **Backup the campaign directory** (always — both fresh and legacy):
      ```bash
      cp -R ~/.claude/dnd/campaigns/<name> \
            ~/.claude/dnd/campaigns/<name>.backup-$(date +%Y%m%d-%H%M%S)
      ```
      Tell the DM the backup path explicitly so they can revert if needed.

   3. **Run `/dm:dnd graph init <name>`** — propose seed nodes/edges from `npcs.md`, `world.md`, and `state.md` (Live State Flags + Active Quests + recent NPC dispositions). Show the DM a single approval block (counts by type + named entries) and ask for one go/no-go. After approval, batch-execute the `add-node` and `add-edge` calls. Use `--since N` matching when each node/edge first became canon (use `1` for foundational; the actual session number for newer NPCs/edges).

   4. **Validate** with a `scene-context` query at the current location to confirm the subgraph is reachable.

   5. **(Legacy only)** Offer the one-time Continuity Archive compression pass:

      > "This campaign is legacy ({session_count} sessions, {archive_count} archive entries). Now that `graph.json` is the canonical source for faction memberships, NPC dispositions, and typed-edge relationships, I can do a one-time pass to trim the existing `## Continuity Archive` entries of relational restatements that the graph now answers. Mechanical changes, plot beats, atmospheric/decision moments, and disclosed information stay in full. Estimated reduction: 5–30% of archive bytes (varies by how relational vs. content-heavy your existing entries are). Backup is already at `<backup-path>`. Proceed? [y/n]"

      - `y` → trim each archive entry surgically; keep the bullet structure; remove ONLY pure-relational restatements (e.g. "X is allied with Y", "Z saw the party's faces", "W is a member of faction F") that have a corresponding edge in the just-initialized graph. Preserve: XP/level/items/HP, plot beats ("Beat 2a sealed"), atmospheric moments, disclosed content, calibration material, off-screen world events. Add a one-line note at the top of `## Continuity Archive`: *"Compressed YYYY-MM-DD (graph init pass). Relational state is canonical in graph.json — entries below preserve mechanical changes, plot beats, disclosed content, atmospheric/decision moments, and calibration material."*
      - `n` → leave the archive untouched. The going-forward compression rule (per `/dm:dnd save`) still applies to NEW entries from this session forward.

      For fresh (non-legacy) campaigns: skip the offer entirely — there's nothing to compress yet, and the going-forward rule covers all future entries.

   6. Re-run scene-context (now populated). Then proceed to step 6.5.

6.5 **Mechanical recap diff.** Run `python3 ${CLAUDE_SKILL_DIR}/scripts/session_recap.py diff --campaign <name>` and inject the output line as the mechanical half of the step-7 recap (HP deltas, conditions, slots — computed from data so the narration never hallucinates them). `diff` auto-advances the baseline, so this one call both reports last session's changes and re-baselines for the next one. First-ever load (no baseline yet — diff reports it): run `session_recap.py snapshot --campaign <name>` instead and skip the mechanical half this once.

7. Deliver one in-character paragraph recapping current situation — where the party is, what's at stake, what was last happening. Fold in the step-6.5 mechanical line and, from session-tail.md, the final stretch of last session.
8. Enter active DM mode — no `/dm:dnd` prefix needed from this point.

---

## `/dm:dnd import <filepath> [campaign-name]`

> **Legacy mode.** Imported structured campaigns predate the milestone build and have no milestone leveling. Retained for compatibility; new campaigns should use `/dm:dnd prep`.

Import a pre-written campaign from a source file (PDF, MD, TXT, DOCX) and create a playable campaign from it.

**Supported file types:** `.pdf` `.md` `.txt` `.markdown` `.docx`

### Step 1 — Extract source text
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/import_campaign.py "<filepath>" --info
```
**PDF sources:** extraction uses PyMuPDF (column-aware) so multi-column modules de-column into reading order and segment into chapters correctly — without it, two-column books collapse into one chapter. If the script prints a `pip3 install pymupdf` notice on its stderr, tell the DM to install it and re-run; it falls back to `pdftotext` otherwise but segmentation is less reliable.

Print file info. If word count is over 4000, chunk the source:
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/import_campaign.py "<filepath>" --chunks  # total chunks
python3 ${CLAUDE_SKILL_DIR}/scripts/import_campaign.py "<filepath>" --chunk 0  # first chunk
```
For short sources (under 4000 words), read in full:
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/import_campaign.py "<filepath>"
```

### Step 2 — Analyse structure
Read the extracted text and identify:
- **Campaign title and system**
- **Structure type:** `linear` (scene chain A→B→C) | `hub-and-spoke` (central hub + spoke locations, player-driven order) | `faction-web` (multi-faction city/complex, overlapping arcs)
- **Acts and chapters** — numbered sections, chapter headings, or named scenes
- **Key beats** — required story events the DM must deliver (boss reveals, faction turns, mandatory encounters)
- **Locations** — distinct named places with descriptions
- **NPCs** — names, roles, motivations, relationships, stat blocks if present
- **Factions** — groups with agendas, relationships to party
- **Quest hooks and seeds** — explicit adventure hooks, side quests, optional encounters
- **Starting conditions** — where does the party begin, what level, what's the inciting event

For large sources, read all chunks before proceeding.

### Step 3 — Confirm campaign name
If `[campaign-name]` not supplied, suggest one from the title and ask to confirm.

### Step 4 — Display summary and confirm
Show a structured summary before writing any files:

```
Title:    <source title>
Type:     structured / <structure type>
Acts:     N  |  Chapters: N  |  Key beats: N
NPCs:     N named  |  Factions: N
Locations: N distinct

Campaign name: <name>
Campaign dir:  ~/.claude/dnd/campaigns/<name>/

Proceed? [y/n]
```

### Step 5 — Create campaign files
On confirmation:

1. `mkdir -p ~/.claude/dnd/campaigns/<name>/characters`
2. Copy templates from `${CLAUDE_SKILL_DIR}/templates/`
3. Write **world.md** (load-time core — kept small so it can be read in full every load):
   - `## World Foundations` — setting, geography, tone, magic level, calendar if present
   - `## Three Truths` — one settlement, one threat, one mystery (drawn from source)
   - `## Threat Escalation Arc` — map source acts to the 5-stage table; set stage 1
   - `## Factions` — all factions with archetype, current activity, relationship to party

3a. Write **world-nodes.md** (lazy reference — NOT read at load, pulled per current act):
   - `## Quest Seed Bank` — all explicit hooks + 2–3 implied side threads
   - `## Adventure Nodes` — named locations with one-line descriptions, grouped by act/chapter

   For a small module the split is optional, but for any published adventure it is the
   single biggest load-time saving — the whole quest/location bank no longer sits in
   context every session. If you write `world-nodes.md`, do **not** duplicate its
   sections into `world.md`.

4. Write **npcs.md** index table (one row per NPC: name, role, location, one-line demeanor)

5. Write **npcs-full.md** — full entry for each named NPC:
   - Role, motivation, secret, speech quirk, faction affiliation
   - Relationships to other NPCs (min 2 per NPC)
   - Stat block summary if present in source

6. Write **arc.md** from `${CLAUDE_SKILL_DIR}/templates/arc.md` — the **full** act/chapter tree: every chapter's `id`, `title`, `location`, `source_ref` (its file in the lazy corpus, see step 6b), `key_beats`, `telegraph_scene`, `branching_notes`, plus `outstanding_beats` and `steering_notes`. This is the heavy structure; it lives here so it is read on demand, not at every load.

6a. Write **state.md** from template:
   - Populate `## Current Situation` — starting location and party placeholder
   - Populate `## World State` — in-world date if given, factions, threat arc stage 1
   - Populate `## Campaign Arc` with the **STRUCTURED ARC POINTER only** (see template): `type: structured`, `source`, `structure`, `arc_file: arc.md`, `current_act`, `current_chapter`, the `current_chapter_detail` block, `next_chapter`, `outstanding_beats`, `steering_notes`. **Delete the entire DYNAMIC ARC yaml block** from the template — do not leave both arc forms in the file. The full tree is in arc.md; state.md carries only the current + next chapter window.
   - Leave `## Active Quests`, `## Session Flags` (autosave defaults on), `## DM Style Notes` as template defaults

6b. Write the **lazy corpus** — the full source text, kept available but out of the hot path:
   - `mkdir -p ~/.claude/dnd/campaigns/<name>/source`
   - For each chapter in arc.md, write `source/<chapter-id>.md` (e.g. `source/1.1.md`) containing that chapter's source text from the extracted chunks. Use the same chapter ids as arc.md.
   - Write `source-index.md` — a table mapping `chapter-id → source/<id>.md → one-line scope`, plus source title and import date.
   - Validate the layout: `python3 ${CLAUDE_SKILL_DIR}/scripts/corpus_check.py --campaign <name>` (expects "lazy-corpus layout OK"). Fix any orphan/missing-file warnings before finishing.

7. Write **session-log.md** with Session 0 import record:
   ```
   ## Session 0 — Import — <date>
   Source: <filepath>
   Imported: <N> acts, <N> chapters, <N> NPCs, <N> locations
   ```

### Step 6 — Gap-fill wizard
After writing files, identify anything the source left ambiguous:
- If starting level not specified → ask
- If party size not specified → ask
- If calendar/in-world date absent → offer to generate or leave blank
- If tone not clear from source → offer Tone/Genre Wizard

### Step 7 — Confirm and offer next step
Print summary of files written. Offer:
```
Campaign "<name>" created from <source title>.
→ /dm:dnd character new      — create your character
→ /dm:dnd load <name>        — start playing immediately
```

---

## `/dm:dnd prep [premise:"..."] [tone:heroic|mythic|grimdark|horror|intrigue|swashbuckling|cosmic] [difficulty:easy|standard|deadly]`

Generate the authored campaign **bible** before session one. Inputs: premise (optional —
blank = surprise-me), tone (from the shared Tone Catalog, `data/tones.yaml`), difficulty,
and the imported party sheets.

0. **Resolve campaign + dir.** If `<name>` was not supplied, ask for it. Create the
   campaign dir: `mkdir -p ~/.claude/dnd/campaigns/<name>/characters`. Ruleset defaults
   to **2014**; if the host passed `ruleset:2024`, use 2024 (and, as in `/dm:dnd new`
   step 2, verify/build the 2024 dataset). Do not interrupt with a ruleset question —
   prep is a seal-and-walk-away flow.
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
     (log it the way the Tone Wizard logs a randomized blank field — the `d6=N → result`
     format; premise.py does its own rolling, so you are mirroring the log format, not calling dice.py).
   - If the host supplied a premise verbatim, still run the script for tone resolution but
     use the supplied premise instead of the rolled axes.
0.7 **Read the party (before authoring anything).** Read every sheet in
   `~/.claude/dnd/campaigns/<name>/characters/` — and confirm with the host if the dir is
   empty (prep binds the bible to the party, so the party comes first). For each PC,
   extract: level, class/subclass, key equipment, the `## Character Pillar` (raw sentence
   + derived pillar), and `## Backstory & Notes`. Record `party.size` and
   `party.start_level` for the spine (step 2) — never assume a level-1 start; if any PC
   is above level 1, the spine's leveling and banding run from the real `start_level`.
   Then bind the bible to them:
   - **World:** at least one faction, node, or mystery element must connect to each PC's
     pillar or backstory (a place they're from, a person they owe, an order that wants
     what they have). Log the binding in `world.md → ## Party Hooks` (one line per PC:
     pillar → which world element carries it).
   - **Spine:** at least one beat's `situation` or `secret` must engage each PC's pillar;
     `gear` rewards must be usable by the actual party's classes.
   - **Quest seeds:** derive at least one seed per PC from their pillar, alongside the
     threat/faction/mystery seeds.
   If a PC has no pillar (player skipped), bind to class/background instead — never
   invent a pillar (matches `character new` step 2).
1. **World layer.** Fill `templates/world.md` (Factions with Goals/Methods/Resources/
   Opposition/Secret/Current-activity/Attitude; Adventure Nodes as *situations, not plots*;
   Three Truths per element; `## Party Hooks` per step 0.7). Fill the remaining Tone &
   Genre knobs (magic level / setting type / danger level) coherently with the premise
   scaffold's setting axis, and log any you randomize in the `d6=N → result` format.
   Write to the campaign's `world.md`.
1.5 **NPC layer.** For every NPC named anywhere in `world.md` (factions' leaders, the
   mystery's actors, node stakeholders) — minimum 3 — write a full entry to `npcs-full.md`
   (same fields as `/dm:dnd new` step 11: role, stats, demeanor, motivation, secret,
   speech quirk, faction, current goal, schedule, personality axes, ≥2 relationships) and
   an index row to `npcs.md`. Run the name-registry uniqueness check on each (as `new`
   does). Every spine `world_pressure` that names an actor must name one of these NPCs
   or factions.

   Then the supporting cast: seed 6–8 additional index-only NPCs anchored to the
   settlement and Adventure Nodes — **new names only** (anyone already named in
   world.md got a full entry above; this pass adds breadth, not duplicates). Same row
   format, same one-distinct-trait Notes rule, and same name-registry check as `new`
   step 11.5. No npcs-full.md entry, no relationship web.
2. **Spine.** Choose a beat count (6–8), split across the fixed 3 acts. Write the
   required `party` block from step 0.7 (`{"size": N, "start_level": N}`) — the schema
   rejects a spine without it. For each beat, get the legal monster candidates:
   `python3 ${CLAUDE_SKILL_DIR}/scripts/prep/bestiary.py --level <party-level-at-beat>`
   — where the party's level *during* each beat runs from `party.start_level` (not 1),
   raised by prior beats' `level_up_to`. Pick what is *dramatic* from the in-band list
   only; prefer creatures whose type and flavor fit the tone and premise — the band is a
   legality gate, not a menu order. Author each beat per the schema in
   `templates/spine.md`: situations-not-objectives, ≥3 hooks (rule of three — defined in
   `templates/spine.md`), causal first-domino chain, absolute `level_up_to` (monotonic,
   every value above `start_level`, final non-null, arc ends ≈ L8), `gear` (usable by the
   actual party's classes), `threats` (exact MM names with counts — `"3x Goblin"`; shape
   each fight deliberately for `party.size`: one at-ceiling solo, a banded pair, or a mob
   of low-CR minions — the schema bands the species, you band the action economy),
   `secret` (prose or null), `status` — **beat 1 `current`, the rest `pending`** (the
   spine carries the playhead from prep onward; the state.md mirror at step 6 must match
   it or the `beat complete` mirror check trips on a fresh campaign).
   **Difficulty** (from the command arg, default `standard`) shifts the authoring, not
   the band: `easy` → pick from the lower half of each band, solos below ceiling;
   `standard` → mixed picks across the band; `deadly` → ceiling picks and paired
   at-band threats are fair game.
   **Bind the spine to the world layer:** every beat's `world_pressure` must name a
   faction or NPC that exists in `world.md` / `npcs-full.md` (step 1.5). Anchor each
   beat's `situation` at or adjacent to an Adventure Node or named world.md location —
   the spine is the story that moves *through* the world layer, not a second world.
   Write the bible to the canonical path `~/.claude/dnd/campaigns/<name>/spine.json`.
3. **Validate — hard gate.** `python3 ${CLAUDE_SKILL_DIR}/scripts/prep/schema.py --bible ~/.claude/dnd/campaigns/<name>/spine.json`
   If it prints `INVALID`, fix every listed error and re-run. Never proceed on an invalid spine.
4. **Asset shopping lists.** In a SEPARATE pass told "describe the asset only, never why
   the party goes there or what happens," generate two lists into the campaign dir by
   copying and filling the templates:
   - `map-list.md` from `templates/map-list.md` — **encounter scenes only** (tactical
     fights); skip social/exploration scenes. *Acquire* hint is a terrain archetype
     ("large cavern map"), never a creature or plot label.
   - `ambient-list.md` from `templates/ambient-list.md` — one loop per distinct notable
     location (town square, crypt, cave). Describe the atmosphere only.
   For every map-list entry, also author its **grid spec** to
   `~/.claude/dnd/campaigns/<name>/maps/<handle>.grid.json` — dims (`cols` ≤ 26 →
   letters, `rows` → numbers; tiles are 5 ft; non-square fine) plus terrain regions
   (`tiles` as `F1` or `C3-D5`; flags `difficult` / `impassable` / `blocks_los`; free-prose
   `notes`). Same spoiler discipline as the lists: **terrain only**, never why the party
   goes there or what happens. Then hard-gate each spec:
   `python3 ${CLAUDE_SKILL_DIR}/scripts/grid.py validate <spec.json>`
   If it prints `INVALID`, fix every listed error and re-run — never proceed on an
   invalid spec (same rule as the spine gate at step 3).
   Then build the host's asset hub:
   `python3 ${CLAUDE_SKILL_DIR}/scripts/render_assets.py --campaign <name>`
   These lists ship in the artifacts the host reads. Keep every hint acquirable and every
   description spoiler-free.
5. **Scaffold campaign files.** Copy `session-log.md` from `${CLAUDE_SKILL_DIR}/templates/`
   into the campaign dir (empty). (`npcs.md` / `npcs-full.md` were written at step 1.5.)
   Write `state.md` from the template: header `Session count: 0` and `**Ruleset:**` from
   step 0; `## Current Situation → Location` = the setting of spine beat 1's `situation`;
   seed `## World State` (in-world date, `Threat arc stage: 1 — Now`, one-line faction
   activity) exactly as `/dm:dnd new` steps 7–10 produce.
6. **Seed the authored arc.** In `state.md → ## Campaign Arc`, write the **AUTHORED ARC** block
   as **active, uncommented YAML** (strip all leading `#` comment markers from the template;
   the seeded arc must be live, not commented-out). Populate: `type: authored`, `spine_file: spine.json`,
   `generated: <today's date>`, `theme`/`resolution` verbatim from the spine, `current_beat: 1`,
   `outstanding_beats` = every beat id, a `beats:` mirror (one entry per spine beat carrying
   `id`/`act`/`label`/`what_changes`/`world_pressure`/`status` — beat 1 `status: current`,
   the rest `pending`), and `steering_notes` authored for beat 1. The seeded
   `steering_notes` must carry the current-beat payload (same contract as `beat complete`
   step 2): (a) beat 1's `situation` in one sentence, (b) its `threats` list verbatim,
   (c) its `secret` on the **last line** (or `secret: none`). state.md is DM-side and
   sealed from the host (step 7), so this leaks nothing. **Delete the DYNAMIC and
   STRUCTURED blocks** from the template so only the authored block remains (mirrors the
   structured-import deletion at the `import` command).
6.5. **Seed the campaign graph — silently, no approval prompt.** Everything the graph needs
   was authored seconds ago in this same pass (npcs/world/spine), so there is nothing for the
   host to review — asking would only leak structure. Batch-run
   `python3 ${CLAUDE_SKILL_DIR}/scripts/campaign_graph.py add-node` / `add-edge` for the
   NPCs, factions, places, and relationships just written (all `--since 1`), then validate
   with a `scene-context` query at beat 1's location. Do not narrate this step to the host
   beyond a one-line "campaign graph seeded." (The interactive `graph init` approval flow at
   `/dm:dnd load` is for **legacy** campaigns with player-facing history to protect — a
   freshly-prepped campaign has none, and after this step the load-time init never triggers.)
7. **Seal.** Tell the host: `world.md` / `spine.json` / `state.md` are sealed ("don't read your
   own campaign"); the map and ambient shopping lists are the artifacts they should read. The campaign now
   appears in `/dm:dnd load` at session 0.

## `/dm:dnd beat complete [<beat id>]`

Advance the spine when the host signals the current beat is done.

0. **Mirror check (deterministic).** Run
   `python3 ${CLAUDE_SKILL_DIR}/scripts/prep/mirror_check.py --campaign <name>`.
   On `MISMATCH`, stop, show both sides, and reconcile with the host — do not silently
   pick a winner. This is the only moment both files are open anyway; drift caught here
   is drift that never reaches steering or leveling.
1. **Advance the spine.** In `spine.json`, mark the beat `status: complete`; set the next
   beat `status: current` (if any).
2. **Sync state.md.** In `state.md → ## Campaign Arc`: set `current_beat` to the next beat's
   id, sync `beats[].status`, drop the completed id from `outstanding_beats`, regenerate
   `steering_notes`. While `spine.json` is open, read the **new current beat's** full
   entry and load the mirror's `steering_notes` with the current-beat payload: (a) the
   beat's `situation` in one sentence, (b) its `threats` list verbatim, (c) its `secret`
   on the **last line** (or `secret: none`). The current beat's spine entry is
   table-state; the rest of the spine is cold storage. state.md is DM-side and sealed
   from the host, so this leaks nothing.
   Final beat → set `current_beat: null`, append a one-line completion note (arc name,
   date, closing beat id) to the existing `## Arc History` section of state.md, then ask:
   *"The arc is complete. Continue with a new arc? [y/n]"* — **yes** → run
   `/dm:dnd arc new` (the successor arc is generated in **dynamic** format from the
   resolved world; the spine was a one-arc artifact); **no** → set `type: sandbox`.
3. **Milestone leveling.** If `level_up_to` is non-null, per party sheet: mark pending with
   `python3 ${CLAUDE_SKILL_DIR}/scripts/prep/milestone.py --sheet <sheet> --level <level_up_to>`,
   then run `/dm:dnd level up` **once per level** to `level_up_to` (spine may jump >1 level,
   e.g. 4 → 6 — one levelup pass per level). **No XP.** Clear:
   `python3 ${CLAUDE_SKILL_DIR}/scripts/prep/milestone.py --sheet <sheet> --clear`.
4. Apply the beat's `gear` (from `spine.json`) to inventory. Narrate the growth.

---

## `/dm:dnd save`

**Session boundary — define it once, here.** If this save is creating a new `## Session N`
entry in session-log.md (i.e. the **first save since load**), set N = header
`Session count` + 1, write the entry under that N, and update the state.md header:
`Session count: N`, `Last session: <today>`. Later saves in the same sitting update the
existing `## Session N` entry and do **not** bump the header. Every time-stamped
mechanism — graph `--since`, log archival, legacy detection, registry stamps — keys off
this counter.

Write session events to session-log.md, update state.md (location, active quests, party HP/resources, recent events), update any characters/*.md that changed. Mirror each updated character to global roster (`~/.claude/dnd/characters/<name>.md`).

**Inspiration tracking:** On every save, record each PC's Inspiration state in `state.md → ## Current Situation → Party status`. Use explicit text: `Inspiration ✓` if held, omit or `No Inspiration` if not. Inspiration persists across sessions and is NOT cleared by long rests. Example: `Mara: HP 24/24. Inspiration ✓. Theo: HP 24/24.`

**Update `## Live State Flags` in state.md on every save.** This section is the compaction-resistant anchor — it holds facts that prose summaries flatten. After each session, review and update:
- **Cover:** each PC's active cover, its status (INTACT / BLOWN / PARTIAL), and the one-line reason. Remove covers that are no longer active.
- **Faction stances:** each faction with non-neutral standing toward the party. Format: `[Faction]: [Allied/Friendly/Neutral/Suspicious/Hostile] — [one-line reason]`. Remove factions that have returned to neutral.
- **NPC dispositions:** each NPC with changed or notable standing. Format: `[Name]: [disposition] — [one-line reason]`. When an NPC returns to baseline, **don't delete the line — collapse it to memory**: `[Name]: baseline — remembers: [what they remember of the party, 1 line]`. The memory line is append-only (cap ~3 remembered items per NPC, oldest dropped); an NPC whose grudge cooled still remembers who caused it, and this line is what keeps that true across compactions. Only drop an NPC entirely if the party never meaningfully registered to them.

If nothing changed in a category this session, leave it as-is. If a fact was wrong in the previous save, correct it.

**Pillar hooks:** for each PC whose Character Pillar was touched this session (a scene,
NPC, or complication aimed at it — see SKILL.md Standard 9), update the `Active hooks`
line in their sheet's `## Character Pillar` (one line: how it's currently in play).

**NPC goals:** for NPCs who acted or were acted on this session, refresh the
`Current goal` line in their npcs-full.md entry — an NPC can't pursue a goal nobody
updates.

**Structured (imported) campaigns — keep the arc window and arc.md in sync.** When a chapter advances this session: mark the completed chapter `status: complete` in `arc.md`, set the new chapter `status: current`, and update `state.md → ## Campaign Arc` so its `current_chapter`, `current_chapter_detail`, `next_chapter`, and `outstanding_beats` reflect the new window. The full tree stays in `arc.md`; `state.md` carries only the current + next chapter so the load stays light. If no chapter advanced, only update `outstanding_beats`/`steering_notes` inline in `state.md` — no need to touch `arc.md`. (Dynamic/sandbox campaigns have no `arc.md`; update the inline arc in `state.md` as before.)

Then update `## Faction Moves` in state.md: for each active faction, answer *"what did they do while the party was occupied?"* One line per faction — even if nothing visible yet. Confirm what was written.

**Deed rule:** never change a faction's stance without recording the cause. Every shift in
**Faction stances** must **cite a deed** appended to the `## Deeds` ledger in state.md
(`<beat id or session number> — <faction> — <what the party did> — <+/−/neutral>`).

**Session tail archive:** at save time, write the tail files to the campaign dir — they are the compaction-survival record of the session's final stretch:

1. Write `~/.claude/dnd/campaigns/<name>/session-tail.md` — this session's 5–8 most important narrative beats, human-readable. **This is the primary tail record**: it is what `/dm:dnd load` step 5 and the post-compaction re-read ladder actually read.
2. Also write `~/.claude/dnd/campaigns/<name>/session_tail.json` — the same beats as a JSON list of `{"text": "...", "_camp": "<name>"}` entries (structured companion for tooling; nothing in the live loop reads it).

**Campaign-graph relationship-shift sweep (runs BEFORE log archival — the compression
rule below assumes this session's edges are already in the graph):** scan this session's
narration for relationship shifts that weren't captured live via `/dm:dnd graph add-edge`
/ `close-edge`. Look for moments matching these patterns:

- New alliance, betrayal, or rivalry between named NPCs / factions ("Velkyn now serves the Pale Court")
- An NPC moving into / out of a location ("Mira fled the Citadel for the Lowmarket")
- A faction taking control of (or losing) a place ("House Tarn lost the silver mine")
- A character learning a secret ("the party now knows Velkyn was the spy")
- A quest / thread ending or being blocked

For each candidate, draft an `add-edge` or `close-edge` call. Then **present the batch to the DM as a numbered list** and ask: *"Apply all? [y / pick / skip]"*

- `y` → run all proposed calls via `python3 ${CLAUDE_SKILL_DIR}/scripts/campaign_graph.py ...`
- `pick` → DM names the numbers to apply (e.g. `1, 3, 5`); skip the rest
- `skip` → don't apply any

Always supply `--since <current-session-N>` from state.md. Never write proposed edges
silently. (The micro-save's live `add-edge` discipline is the one exception, and it is
scoped: only edges explicitly narrated on-screen this scene; anything inferential waits
for this sweep.)

If `graph.json` doesn't exist yet for this campaign, skip the sweep entirely (no proposal block) — graph isn't seeded.

**Session log archival (run on every save after session count > 3):**
session-log.md keeps only the **2 most recent full session entries**. Older entries move to `session-log-archive.md` (append, never delete). Before archiving each entry, extract a 3–5 bullet continuity summary and write it to `## Continuity Archive` in state.md. Format:

```markdown
### Session N — [date] — [one-line location/event label]
- [Key fact that may resurface as a callback]
- [NPC revelation, exact wording of something important, decision that has consequences]
- [Roll outcome that changed the fiction]
- [Item acquired with story significance, plot beat, atmospheric/decision moment]
```

**Going-forward Continuity Archive compression rule (from 2026-05-07; applies when `graph.json` exists for the campaign):** When `graph.json` is present, the Continuity Archive bullets must NOT restate relational state that the graph holds canonically. Drop a relational bullet **only when its edge is confirmed present** — it appeared in the just-approved sweep batch above or in an earlier session's graph; a `skip`ped proposal means the bullet stays. If in doubt, keep the bullet. Specifically, **omit** bullets/clauses that say:
- "X is allied with Y" / "X is hostile to Y" / "X is friendly with Y" — already a typed edge with `--since N` and source-anchor
- "X is a member of faction F" / "X works for Y" / "X reports to Y" — already a `member_of` / `works_for` / `reports_on` edge
- "Z saw the party's faces" / "K is now in the Kept profile" — already a `hostile_to` / `surveils` edge with `--since`
- Faction memberships and NPC dispositions that haven't changed this session
- Restated NPC profiles (job title, age, location) that already live as node tags + summary

**Keep** in archive bullets:
- Mechanical changes (beat advanced / milestone level-ups, items gained/spent, slots burned, HP deltas at session end)
- Plot beats (arc beat completions, "Beat 2a sealed", "Beat 2b LANDED")
- Atmospheric / decision moments that have no graph edge ("Mira ate the bread — first food in 800 years", "Mara squeezed her hand")
- Disclosed content (the WHAT was learned — "fragment / anchor / host", "three acceleration factors") even when the relational fact is in graph
- Off-screen world events / faction moves
- Calibration / DM Notes
- Cliffhangers and pause-points

Treat each bullet as one sentence with one job. If the only job is "restate a graph edge", drop it. If it carries content + edge, keep the content half. The graph is queried at `/dm:dnd load` step 5; the archive is queried for chronological narrative + mechanical state — they should not overlap.

The continuity summary is what stays hot in context. The full verbose log is in the archive, readable on `/dm:dnd recap` or explicit request. When a past detail surfaces mid-scene, check `## Continuity Archive` first, then `/dm:dnd graph scene-context` for relational context, then read session-log-archive.md if more depth is needed.

---

## `/dm:dnd end`
1. Run `/dm:dnd save`, then:
   a. Append **Session Recap** block to session-log.md with key events and open threads.
   b. Ask: *"Quick calibration — what worked this session, and what would you adjust next time?"* Write answers to `### DM Calibration`. If skipped, leave blank.
   c. Update `## World State` in state.md: check whether events advanced the threat arc stage, shifted faction activity, or changed the in-world date. Update all three.
   d. If the calibration response reveals a new pattern (or confirms/contradicts an existing one), update `## DM Style Notes` in state.md. Add new bullets; refine existing ones if the pattern has sharpened. Do not log every session — only update when something genuinely new or changed is observed.
   e. **Arc check** (dynamic **and authored** arcs — skip for sandbox/structured): If `## Campaign Arc` has `type: dynamic` or `type: authored`, do all of:

      i. Ask: *"Did any arc beats land this session? [beat id(s) like '1b 2a', or 'none']"*
      ii. If beats landed: run `/dm:dnd arc advance <beat-id>` for each (authored: run `/dm:dnd beat complete <id>` instead of `arc advance`).
      iii. **Pre-emption check (critical — added 2026-05-01):** for each remaining outstanding beat whose `world_pressure` was visibly delivered this session (the world event named in the beat actually appeared in narration or Faction Moves), evaluate whether the beat's `what_changes` consequence ALSO landed. Three possible states:
        - **Landed cleanly** → mark beat complete (step ii).
        - **Did not land — pressure absorbed without consequence** → the beat is overdue and its current shape no longer fits. **Run `/dm:dnd arc revise` immediately**; do not just update `steering_notes`. The beat's `what_changes` was event-shaped (something specific happens) when it should be consequence-shaped (something fundamentally different is true) — revise both `what_changes` and `world_pressure` to fit a path that DOES land. The committed shape bends; it does not break.
        - **Pressure not yet delivered** → leave beat alone; expected to deliver next session.
      iv. Update `steering_notes` for the next outstanding beat with the *consequence shape* expected, not the specific event.
   f. **Tail verification:** confirm the campaign-side `session_tail.json` was written at save (non-empty, valid JSON list). If missing or corrupt, write it now from session context (5–8 entries, each `{"text": "...", "_camp": "<name>"}`).

---

## `/dm:dnd abandon`

Exit the current session **without saving any state changes**. Use this when an error occurred and you want to discard everything since the last `/dm:dnd save` (or since load, if the session was never saved).

1. Confirm: *"Abandon session? All unsaved state changes will be lost. Type 'yes' to confirm."* — do not proceed until confirmed.
2. Do **NOT** write to state.md, world.md, npcs.md, session-log.md, or any character files.
3. Confirm: *"Session abandoned. No files were written. Run `/dm:dnd load <campaign>` to reload from the last saved state."*

---

## `/dm:dnd data [sync|status]`
- `sync` → `python3 ${CLAUDE_SKILL_DIR}/scripts/sync_srd.py` — checks upstream SHAs (5e-bits + FoundryVTT) and rebuilds `dnd5e_srd.json` only if either source has new commits
- `sync --force` → `python3 ${CLAUDE_SKILL_DIR}/scripts/sync_srd.py --force` — rebuild regardless
- `sync --check` → check upstream without rebuilding
- `status` → `python3 ${CLAUDE_SKILL_DIR}/scripts/build_srd.py --status` — show current dataset metadata

Dataset is bundled at `${CLAUDE_SKILL_DIR}/data/dnd5e_srd.json` (1453 records: spells, equipment, magic items, conditions, monsters, class features). No download required at runtime. Run `sync` only when you want to pull new upstream content.

---

## `/dm:dnd path [<new-path> | reset]`

View or configure where campaign and character data is stored. Wraps the
`DND_CAMPAIGN_ROOT` env var.

- No args → `python3 ${CLAUDE_SKILL_DIR}/scripts/path_config.py` and show output.
- New path → `python3 ${CLAUDE_SKILL_DIR}/scripts/path_config.py set <path>`. Confirm to user, then remind them the change only takes effect in new shells (or after they `source` their rc on macOS/Linux).
- `reset` → `python3 ${CLAUDE_SKILL_DIR}/scripts/path_config.py reset`.

Persistence is via shell rc on macOS/Linux and via `setx` on Windows. Existing campaigns are not auto-migrated; `paths.find_campaign()` handles legacy fallback + copy-on-access.

---

## `/dm:dnd update [--check]`

Pull the latest skill changes from `origin/main`.

- No args → `python3 ${CLAUDE_SKILL_DIR}/scripts/update_skill.py` and stream output (script prompts before pulling).
- `--check` → `python3 ${CLAUDE_SKILL_DIR}/scripts/update_skill.py --check` — report status without pulling.
- The script refuses to update if the working tree is dirty and uses `--ff-only` so it never silently merges divergent history.
- After a successful pull, remind the user to restart Claude Code so the new `SKILL.md` and `SKILL-commands.md` are reloaded.

---

## `/dm:dnd list`
Read `~/.claude/dnd/campaigns/*/state.md`, print summary table: campaign name | last session date | session count.

---

## `/dm:dnd character new [campaign-name]`

**Read the campaign's ruleset first** — `paths.py` is a CLI (same call as load step 3):

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/paths.py campaign-ruleset <campaign>
```

The result drives branching at steps 1 (ASI source), 4 (origin feat), and 5 (subclass timing). The default `2014` applies for legacy campaigns predating the ruleset field.

1. Ask: name, **species** (2024) or **race** (2014), class, background.

   **Name uniqueness check:** run `python3 ${CLAUDE_SKILL_DIR}/scripts/name_registry.py check "<name>"`. Exit 1 (duplicate) → surface prior use; player confirms or changes. Record after step 9.

   **2014 (race-as-ASI):** the species/race grants ability score increases (e.g. Wood Elf: +2 DEX, +1 WIS). Apply to abilities at step 4.
   **2024 (background-as-ASI):** the **background** grants the +2/+1 ability score increase OR three +1s, AND a free **Origin Feat** (e.g. Magic Initiate, Lucky, Tough). Species grants traits but no ability scores. Players in 2024 must pick background BEFORE rolling abilities — the background's ASI pattern dictates which scores benefit.
2. Ask: *"In a sentence, what should the DM know about [Name]?"*
   - If answered: derive ONE pillar — **Bond**, **Flaw**, **Ideal**, or **Goal** (whichever fits best). Store both the raw sentence and derived pillar in `## Character Pillar`.
   - If skipped: leave `## Character Pillar` blank. Do not invent one. Do not re-prompt.
3. Ask: roll or point buy
   - Roll → `ability-scores.py roll`, present 3 arrays, player assigns
   - Point buy → `ability-scores.py pointbuy --check <scores>` to validate
4. Apply racial bonuses. Run `character.py calc` to derive all secondary stats.
5. Ask: Fighting Style (Fighter/Paladin/Ranger), spells (if caster)
6. Assign starting equipment per class + background
7. Write to `characters/<name>.md` using `templates/character-sheet.md`; set `## Campaign History → Origin campaign`
8. Add to `state.md` party line
9. Mirror to global roster: `cp characters/<name>.md ~/.claude/dnd/characters/<name>.md`
10. Run supplemental builder to fetch any non-SRD spells/features the character uses:
    ```bash
    python3 ${CLAUDE_SKILL_DIR}/scripts/build_supplemental.py --character ~/.claude/dnd/campaigns/<name>/characters/<charname>.md
    ```
    This scans the character file for spells and features not in the SRD and fetches descriptions from dnd5e.wikidot.com into `dnd5e_supplemental.json`. Skips any entries already present. Safe to re-run.

---

## `/dm:dnd character sheet [name]`
Read `characters/<name>.md`, display cleanly. If name omitted and one character exists, show that one.

---

## `/dm:dnd character import <name> [from:<campaign>]`
1. Find character sheet: `from:<campaign>` specified → that campaign's characters/; otherwise check global roster `~/.claude/dnd/characters/<name>.md`; if neither → search all campaigns, list matches, ask.
2. Show summary (level, XP, HP, key inventory) and ask: *"Import at current level [X], or level up before starting?"*
   - As-is → copy directly; Level up first → run `/dm:dnd level up` on source sheet
3. Copy to current campaign's `characters/<name>.md`. Update: Campaign, Last Updated, Previous campaigns, Death Saves (reset).
4. Optionally ask about equipment adjustment for new setting.
5. Add to `state.md` party line. Update global roster.
6. Run supplemental builder for any non-SRD entries:
    ```bash
    python3 ${CLAUDE_SKILL_DIR}/scripts/build_supplemental.py --character ~/.claude/dnd/campaigns/<name>/characters/<charname>.md
    ```
7. Deliver one-paragraph in-character aside — how does it feel to step into a new world?

---

## `/dm:dnd level up [name]`
1. **XP gate — check first:**

   | Level | XP required | Level | XP required |
   |-------|-------------|-------|-------------|
   | 2 | 300 | 11 | 85,000 |
   | 3 | 900 | 12 | 100,000 |
   | 4 | 2,700 | 13 | 120,000 |
   | 5 | 6,500 | 14 | 140,000 |
   | 6 | 14,000 | 15 | 165,000 |
   | 7 | 23,000 | 16 | 195,000 |
   | 8 | 34,000 | 17 | 225,000 |
   | 9 | 48,000 | 18 | 265,000 |
   | 10 | 64,000 | 19 | 305,000 |
   |    |         | 20 | 355,000 |

   Insufficient XP → report deficit and stop. Only continue on explicit DM override.

   **Milestone campaigns bypass this gate.** If the party sheet carries a `⚠ LEVEL UP PENDING (Level N)` marker (set by `/dm:dnd beat complete` via `prep/milestone.py`, with no XP counter in play), skip the XP-threshold check entirely and level to N — the pending marker **is** the authorization. See `## Milestone Leveling` in SKILL.md.
2. Read sheet. Run `character.py levelup`. Apply class features. Ask for HP roll or average. Update sheet + global roster. Narrate the growth.

   **Ruleset-aware subclass timing (added 2026-05-08):** read campaign ruleset via `paths.campaign_ruleset(<campaign>)`.
   - **2014:** Subclass selection happens at the class's specified level (Cleric/Sorcerer/Warlock at 1; Druid/Wizard at 2; most others at 3).
   - **2024:** Subclass selection unifies at **level 3** for ALL classes. If the player is hitting level 3 in a 2024 campaign and hasn't picked a subclass yet, prompt for it. Class features that 2014 placed at level 1 (e.g. Cleric Domain) shift to level 3 in 2024.

   **Weapon Mastery (2024 only):** Fighter/Barbarian/Paladin/Ranger gain Weapon Mastery at level 1 (Fighter knows 3 mastery properties; others know 2). Track which properties the character knows on the sheet under `## Class Features → Weapon Mastery: <list>`. Properties are picked from the eight in `data/dnd5e_srd_2024.json → weapon_mastery_properties`. The character can use mastery only with weapons that have the matching property (look up on `data/dnd5e_srd_2024.json → equipment[…].mastery`).

---

## `/dm:dnd npc [name]`
- Existing → read full entry from npcs-full.md (search by name), portray in character with voice/quirk
- New → generate full entry: role, CR-appropriate stats, demeanor, motivation, secret, speech quirk, faction (or "independent"), current goal, schedule, all four personality axes, ≥2 relationships to existing NPCs. Default attitude neutral. Append full entry to npcs-full.md; add one-line summary row to npcs.md index.

  **Name uniqueness check (added 2026-05-07):** before generating, run `python3 ${CLAUDE_SKILL_DIR}/scripts/name_registry.py check "<proposed-name>"`. If duplicate (exit 1), surface the prior use to the DM and offer either: (a) proceed with the duplicate (some scenarios want recurring names — a Voss reference can be deliberate); or (b) regenerate with a different name. Whichever path is chosen, after the NPC is added to npcs.md / npcs-full.md, call `name_registry.py add --name "<name>" --type npc --campaign <name> --session <current>` to record the entry.

  When **/dm:dnd new** generates a batch of NPCs during world-gen, run the check on each generated name in the same loop: if duplicate, regenerate that name (re-prompt the LLM with the prior name added to a "do-not-pick" exclusion list). After world-gen completes, batch-call `name_registry.py add` for every accepted NPC.

## `/dm:dnd npc attitude <name> <shift>`
Find NPC in npcs.md, shift attitude one step (hostile → suspicious → neutral → friendly → allied — the same five-word scale as Faction stances), log reason and date.

## `/dm:dnd npc rename "Old Name" <"New Name" | random> [flags]`
Rename a character across an entire campaign — `npcs.md`, `npcs-full.md`, `state.md` (every section), `session-log.md`, `graph.json` (node + edges preserved), and `characters/<slug>.md` if `--type pc`. Backs up the campaign first.

Maps to: `python3 ${CLAUDE_SKILL_DIR}/scripts/npc_rename.py --campaign <current> --old "..." --new "..." [flags]`. Use the currently loaded campaign by default; for explicit-campaign use, pass `--campaign <name>` directly.

Flags:
- `--random` — pick a name from the bundled fantasy-name corpus (~4800 unique combinations) that isn't already in `~/.claude/dnd/.name_registry.json`. Mutually exclusive with explicit "New Name".
- `--type npc | pc` (default `npc`) — `pc` also moves the character file and updates the global roster.
- `--dry-run` — show all hits across files without writing. Always run first for sanity.
- `--yes` — skip the confirmation prompt.
- `--include-archive` — also rename in `session-log-archive.md`. **Default is to leave the archive untouched** for historical accuracy and add a one-line audit note at the top: *"`<old>` renamed to `<new>` at S<N>; historical entries below preserve the original name."*

The script always backs up the campaign to `<name>.backup-rename-<old-slug>-YYYYMMDD-HHMMSS/` before any writes. Revert command is printed at the end.

After rename, the name registry is updated: old name marked `retired_from` this campaign with `replaced_by` pointing at the new slug; new name added with this campaign's current session as `first_session`.

## `/dm:dnd registry <subcommand>`
View and manage the cross-campaign name registry at `~/.claude/dnd/.name_registry.json`. Used by `/dm:dnd npc rename --random` to never reuse a name and (in a follow-up) by `/dm:dnd new` / `/dm:dnd character new` / `/dm:dnd npc <new>` to flag duplicates at creation time.

Maps to: `python3 ${CLAUDE_SKILL_DIR}/scripts/name_registry.py <subcommand> [args]`.

- `/dm:dnd registry rebuild [--include-prose]` — scan every campaign's `npcs.md`, `npcs-full.md`, `characters/*.md`, and `graph.json` (node names); rebuild the registry from canonical sources. Preserves any existing `retired_from` history. Run once on install, then ad hoc when desired.

  **`--include-prose` (added 2026-05-07, opt-in):** also scan `session-log.md` and `session-log-archive.md` for capitalized 2–3-word sequences (likely-name patterns). Filtered against a stopword list (places, factions, mechanic words like "Theo Stealth", sentence starts) but **regex-based extraction is inherently noisy** — typically 5–15× more entries than canonical, with maybe 10–20% real catches. Tagged `source: prose` to distinguish; query with `/dm:dnd registry list --source prose` to manually review and prune. For high-quality prose extraction, the future move is LLM-backed (similar to `/dm:dnd graph extract`).

- `/dm:dnd registry list [--campaign C] [--type npc|pc] [--source canonical|prose]` — print all registry entries; filter by campaign-currently-active, type, or source.
- `/dm:dnd registry lookup <name>` — case-insensitive lookup; prints the full entry as JSON.
- `/dm:dnd registry check <name> [--json]` — check whether a proposed name collides with the registry. Exit 0 if unique, 1 if duplicate. Severity (`warn` default, `strict` opt-in via `<DND_CAMPAIGN_ROOT>/.name_registry_config.json`) controls whether duplicates are reported as warnings or hard refusals. Used by `/dm:dnd new`, `/dm:dnd character new`, `/dm:dnd npc <new>` procedures.
- `/dm:dnd registry add --name N --type npc|pc --campaign C --session N` — record a new entry manually (auto-called by `/dm:dnd npc rename` and the creation-time uniqueness hooks).
- `/dm:dnd registry retire --name N --campaign C [--replaced-by NEW]` — mark a name as no longer active in a campaign (auto-called by `/dm:dnd npc rename`).

The registry by default captures **canonical** characters (those in `npcs.md` / `npcs-full.md` / `characters/` / graph.json node names). Names that appear only in session-log prose (one-off mentions, throwaway NPCs, skill-check labels) are NOT registered by default — that's deliberate, to avoid banning common names because of incidental use. The `--include-prose` flag is opt-in for users who want the broader (noisier) view.

**Severity config:** create `~/.claude/dnd/.name_registry_config.json` with `{"severity": "strict"}` to make all duplicate detections refuse-by-default rather than warn-and-allow. Set to `"none"` to disable checks entirely (registry rebuild and rename still work).

---

## `/dm:dnd characters`
List all characters in global roster (`~/.claude/dnd/characters/`). Display: name, race/class/level, origin campaign, previous campaigns, last updated.

---

## `/dm:dnd roll <notation>`
Run `scripts/dice.py <notation>`. Display output verbatim. Examples: `d20`, `2d6+3`, `d20 adv`, `4d6kh3`.

---

## `/dm:dnd combat start`
1. Identify combatants; collect name, DEX mod, HP, AC, type (pc/npc) for each.
1.5 **Mapped combat?** If the scene sits at a location matching a `map-list.md` handle
   (or the host names a listed map to use), this fight is on the grid:
   - Emit the map cue on its own line: `🗺 **Map:** *<handle>*`.
   - Load `maps/<handle>.grid.json`. **First use of this handle** (spec lacks
     `"confirmed": true`): ask the host one line — *"spec says <cols>×<rows> — match
     your map? give real dims if not."* On override, rewrite `cols`/`rows` (re-fit
     terrain regions proportionally if the shape changed a lot), then add
     `"confirmed": true` and re-run `grid.py validate`. **No spec file at all** (older
     prep): author one now through the same exchange — dims from the host, terrain from
     the scene as narrated so far — validate, save, continue.
   - Place everyone: NPCs per the fiction; players state their tiles (default them to a
     sensible entry edge if they don't care). Add `"pos": "<tile>"` to each combatant's
     JSON. An unrevealed enemy either stays out of the JSON until it appears or carries
     `"hidden": true` — hidden combatants never render on the player page.
   A fight anywhere else is theater of the mind: no cue, no grid, no `pos` fields —
   skip this step entirely.
2. Run `combat.py init '<JSON>'` — auto-roll initiative for every combatant including PCs. Show the tracker and per-combatant roll breakdown in chat:
   ```
   ⚔️ Initiative — Round 1
   [Name]: d20(N) + DEX = total
   Turn order: [Name] → [Name] → ...
   ```
3. Save STATE_JSON to `state.md` under `## Active Combat`. Mapped combat: also run the
   first projector render —
   `python3 ${CLAUDE_SKILL_DIR}/scripts/render_map.py --campaign <name> --handle <handle> --state '<STATE_JSON>' --round 1`
4. Step through turns using the per-turn sequence (in SKILL.md Active DM Mode).
5. On combat end: update HP in character sheets, clear `## Active Combat`, narrate aftermath, run `tracker.py -c <campaign> clear`, and re-run `render_tracker.py` once with the final state and a "combat ended" marker (or clear tracker.html) — the meta-refresh dashboard otherwise keeps showing a live fight that's over. Mapped combat: also emit the down-cue on its own line — `🗺 **Map:** *down — theater of the mind*` — and clear the projector page:
   `python3 ${CLAUDE_SKILL_DIR}/scripts/render_map.py --campaign <name> --clear`

**No XP.** This is a milestone-leveling fork — combat end awards no XP. Leveling happens only at
`/dm:dnd beat complete`. Narrate loot/consequences in the aftermath send; do not send an XP block.

---

## `/dm:dnd rest <short|long>`
**Short (1 hour):**
1. Ask how many Hit Dice the player spends. Roll `d[hit-die] + CON mod` per die via `dice.py`. Update HP in the character sheet.
2. Note class features that recharge (e.g. Second Wind).
3. Advance time: `calendar.py -c <campaign> rest short`
4. Clear encounter conditions: `tracker.py -c <campaign> clear` (concentration may persist — ask)

**Long (8 hours):**
1. Restore all HP, half max Hit Dice (round up), all spell slots, most class features. Update sheet.
2. Advance time: `calendar.py -c <campaign> rest long`
3. Clear all tracker state: `tracker.py -c <campaign> clear --all`
4. Update `state.md` in-world date to match calendar output.

---

## `/dm:dnd recap`
Read session-log.md. Deliver 3–5 sentence in-character narrator recap of the most recent session entry.

## `/dm:dnd world`
Read and display world.md.

## `/dm:dnd quests`
Read `state.md` → display Active Quests and Open Threads sections.

---

## `/dm:dnd arc [status|advance|revise|view]`

Manage the dynamic campaign arc. The `advance` and `new` subcommands are active only when `state.md → ## Campaign Arc` has `type: dynamic`; `revise` is active for `type: dynamic` **and `type: authored`** (authored branch below) — all are no-ops for sandbox campaigns. Authored beat completion goes through `/dm:dnd beat complete`, and a completed authored arc offers `arc new` from there (the successor arc is generated in dynamic format). For **structured (imported)** campaigns, `status` and `view` read from `arc.md` (chapter advancement happens at `/dm:dnd save`, not here); `advance`/`revise`/`new` are no-ops.

- **`/dm:dnd arc`** or **`/dm:dnd arc status`** — print current act, current beat label, `what_changes` for the current beat, and `steering_notes`. Quick reference, one screen. (Authored: **omit the `secret` line when printing `steering_notes`** — in solo play the host is the player, and the secret exists purely to be discovered in play.) (Structured: print `current_act`, `current_chapter`, current chapter's `key_beats`, and `outstanding_beats` from `state.md`; read `arc.md` only if more detail is asked for.)
- **`/dm:dnd arc advance [beat-id]`** — mark the named beat complete (current beat if omitted). Remove from `outstanding_beats`. Advance `current_beat` to the next pending beat. If all beats in an act are complete, advance `current_act`. Update `steering_notes` to describe how to reach the newly current beat without forcing it.

  **When the final beat (3b) is marked complete — arc continuation:**
  `outstanding_beats` is now empty. Ask: *"The arc is complete. Continue the campaign with a new arc? [y/n]"*
  - **Yes** → run `/dm:dnd arc new` (see below).
  - **No** → set `type: sandbox` and clear `outstanding_beats`. The campaign continues open-ended from the resolution state.

- **`/dm:dnd arc new`** — generate a new arc for a campaign that has completed its previous arc. Use Opus for this step.

  The new arc must be **intentionally distinct** — not a continuation of the same conflict, but a new chapter that grows from the changed world. The resolution of arc N is the status quo of arc N+1.

  Procedure:
  1. Read the completed arc's `resolution` field — this is now the world's baseline.
  2. Read `## DM Notes`, `## World State`, `## Faction Moves`, and any `## Continuity Archive` entries to understand what the world looks like post-resolution.
  3. Derive the new arc from **the consequences** of what just resolved. Ask: *what problem did solving the last arc create? What power vacuum formed? What did the party's victory cost that now has to be reckoned with? What was ignored because the last arc demanded all attention?*
  4. Generate a new full arc (theme, resolution, acts 1–3, 6 beats) using the same format as the initial arc. The new theme must be meaningfully different from the previous one — same world, new lens.
  5. Archive the completed arc: move the current `acts` block, `theme`, and `resolution` into a new `## Arc History` section in state.md under `arc_N` (numbered), with a one-line summary of how it resolved.
  6. Write the new arc to `## Campaign Arc`, incrementing `arc_number`. Set `current_act: 1`, `current_beat: "1a"`, `outstanding_beats` to all 6 beat ids.
  7. Append to `revision_log`: `"<date>: Arc N complete. New arc N+1 generated. [one-line premise of the new arc]"`
  8. Deliver a one-paragraph summary of the new arc's premise and how it differs from the previous one.

- **`/dm:dnd arc view`** — show full arc: theme, resolution, all acts and beats with completion status (current / complete / pending). If `## Arc History` exists, show a one-line summary of each completed arc above the current one.
- **`/dm:dnd arc revise`** — open revision flow for when the story has taken a major unexpected turn OR when the auto-trigger from /dm:dnd end's pre-emption check fires (most common case):
  1. Show all outstanding beats with their current `what_changes` and `world_pressure`.
  2. Ask: *"What's changed in the story that the arc doesn't reflect?"* — or, when auto-triggered by pre-emption, name the pre-empted beat directly: *"Beat 2b's pressure delivered but the consequence didn't land. Picking a revision path…"*
  3. **Apply one of three landing-path templates** (per SKILL.md rule 8) to the affected outstanding beat:
     - **Cost path** — `what_changes` becomes "the party paid a concrete cost for moving fast"; `world_pressure` becomes the specific cost (cover blown, ally compromised, position lost). Best when the party pre-empted cleanly.
     - **Secondary consequence path** — `what_changes` becomes "the world responded to being pre-empted in a way the party didn't anticipate"; `world_pressure` becomes the new escalation (the antagonist reads the disruption as a signal and does something WORSE). Best when the antagonist is intelligent and adaptive.
     - **Deferred path** — keep the original `what_changes` shape; rewrite `world_pressure` to a NEW pressure pointing at the same consequence, scheduled for the next 1–2 sessions. Best when the original consequence is still narratively essential and only the timing slipped.
  4. Rewrite `what_changes` (consequence-shaped per the rule in /dm:dnd new step 12) and `world_pressure` (event-shaped is fine) for the affected beat. Do NOT modify completed beats.

     **Authored arcs — write-back ordering contract (the sync is always spine→state, one
     direction; the spine stays the sole prose authority):**
     1. Write the revised `what_changes`/`world_pressure` to the matching beat in
        **`spine.json` first**.
     2. Re-run the schema gate:
        `python3 ${CLAUDE_SKILL_DIR}/scripts/prep/schema.py --bible ~/.claude/dnd/campaigns/<name>/spine.json`
        (revise only touches two prose fields, so this always passes unless the edit
        broke structure — which is exactly when you want to know).
     3. Regenerate the state.md mirror entry **from the just-written spine**, not from
        context — including the `steering_notes` current-beat payload if the revised
        beat is the current one.
     4. `revision_log` is appended in state.md only (spine.json gets no new fields).
  5. Append to `revision_log`: `"<date>: <beat-id> — <path: cost/secondary/deferred> — <what changed and why — one sentence>"`
  6. Update `steering_notes` to describe the next session's expected delivery.
  6.5 **If the revision relocates a scene or changes which NPC/faction drives it**, also:
     update the affected `world.md → ## Adventure Nodes` entries, propose the matching
     graph `add-edge`/`close-edge` calls in the same confirmation, and append matching
     entries to `map-list.md` / `ambient-list.md` (same spoiler rules as prep step 4)
     then re-run `python3 ${CLAUDE_SKILL_DIR}/scripts/render_assets.py --campaign <name>`
     so the host's hub stays current — a relocated beat with no legal ambient cue plays
     silent otherwise, and stale graph edges would reassert the pre-revision world after
     a compaction.
  7. Confirm what was revised. Show before/after for `what_changes` and `world_pressure`.

---

## `/dm:dnd graph <subcommand>` — campaign relationship graph

Local-only typed-edge relationship graph supplementing markdown. Stored at `~/.claude/dnd/campaigns/<name>/graph.json`. Supplements `npcs-full.md` / `session-log.md` — does not replace them. Edges are time-stamped (`since_session` / `until_session`), so historical state is recoverable.

**Auto-pulled at `/dm:dnd load` step 5** (scene-context) and **swept at `/dm:dnd save`** (relationship-shift extraction). The DM also uses `/dm:dnd graph scene-context` on demand mid-session, especially before heavy social or political scenes.

For background reading on the design and the A/B replay study that motivated it, see `docs/research/graph/`.

All subcommands invoke `python3 ${CLAUDE_SKILL_DIR}/scripts/campaign_graph.py <subcommand> --campaign <name> [args]`.

### `/dm:dnd graph init [campaign-name]`
First-time bootstrap. Read existing `npcs.md` / `world.md` / `state.md` for the campaign. Propose a node list (NPCs as `npc_*`, factions as `faction_*`, key locations as `place_*`) and a starter edge list (faction membership from npcs.md tables, NPC location from "Lives in / Based at" fields, faction relationships from world.md). Display the proposed list to the DM and **ask for approval** before writing — do not silently extract. After approval, run `add-node` and `add-edge` for each. Use `--since` matching state.md's current session count.

For existing campaigns being initialized for the first time, the `/dm:dnd load` flow offers to back the campaign directory up first; honour that flow rather than running init from a cold prompt.

### `/dm:dnd graph add-node --type T --name N [--tags ...] [--summary ...]`
Add a single node. Type is open vocab; suggested: `npc`, `faction`, `place`, `item`, `thread`. Default id is `<type>_<name-slug>`.

### `/dm:dnd graph add-edge --from <id> --to <id> --type T [--since N] [--note ...]`
Add a typed edge between two existing nodes. Edge type is open vocab; common: `loyal_to`, `opposes`, `allied_with`, `member_of`, `lives_in`, `controls`, `knows_about`, `friends_with`, `lover_of`, `owes`, `rules`, `related_by_blood`, `advances_thread`, `blocks_thread`. Always supply `--since` (the current session number from state.md) so historical replay works.

### `/dm:dnd graph close-edge --id <edge-id> --at-session N`
Mark an edge as ended at session N (e.g. when an alliance breaks). Original edge is preserved with `until_session` set; it remains visible in historical queries but is excluded from "active at session ≥ N" results.

### `/dm:dnd graph supersede-edge --id <edge-id> [--by <edge-id>] [--reason "..."]`
Hard retcon: mark an edge as **wrong from the start** (a mis-extracted or mis-narrated
relationship), optionally pointing at the corrected edge. Distinct from `close-edge`:
close-edge ends a state cleanly (it *was* true, then stopped); supersede-edge says the
original edge never was true. The superseded edge is preserved for the audit trail but
excluded from active queries at every session.

### `/dm:dnd graph list [--type T] [--at-session N]`
Print a compact node table grouped by type. With `--at-session`, also reports active edge count at that session.

### `/dm:dnd graph show --id <node-id>`
Print one node with all incoming and outgoing edges.

### `/dm:dnd graph scene-context --place <id> [--present id1,id2] [--threads id1,id2] [--hops H] [--at-session N]`
**Primary query for in-session use.** Returns a focused subgraph from the current scene (place + present NPCs + active threads) bounded by hop count, optionally filtered to edges active at a given session. Output is grouped: nodes by type, then a relationships block. Default `--hops 2`. Use this when you need to recall who-relates-to-whom in the current scene without re-reading `npcs-full.md` or session-log archives.

### `/dm:dnd graph subgraph --seed <id> [--seed <id>] [--hops H] [--at-session N]`
Lower-level traversal — same as `scene-context` but with arbitrary seed nodes. Use when the scene framing doesn't fit (e.g. tracing faction politics independent of any specific place).

### `/dm:dnd graph extract [campaign-name] [--last-session-only]`
Run a Haiku pass over the campaign's session-log to propose new edges with verbatim source-anchors. Outputs a proposal JSON to `~/.claude/dnd/campaigns/<name>/graph-proposals-<date>.json` for human review. Does **not** write to graph.json — that's the apply step.

### `/dm:dnd graph extract --deterministic [--last-session-only] [--write FILE]`
**Zero-LLM alternative.** Pattern-matches session-log sentences against the bundled verb-table seed (`data/graph/verb_table_seed.yaml`) and emits the same proposal shape as the Haiku pass — no Claude API call, no cost, fully portable. Trades recall (~50%, clean subject-verb-object only) for precision (~95%) and determinism. Prints proposals to stdout, or writes them with `--write`.

### `/dm:dnd graph extract --deterministic --apply [--min-confidence low|medium|high] [--no-auto-nodes]`
One-shot auto-apply: run deterministic extraction and write proposals at/above `--min-confidence` (default `high`) straight into `graph.json` — deduped against existing edges and **idempotent** (re-running adds nothing new). Missing nodes are auto-created as `npc_*` placeholders unless `--no-auto-nodes` is set. Use this for a hands-off relationship sweep at `/dm:dnd save`; use the review path below when you want a human in the loop.

### `/dm:dnd graph extract-apply --proposals <file> [--pick N1,N2,...] [--review]`
Apply previously-extracted proposals (from either the Haiku or deterministic pass). Without `--pick`/`--review`, applies all. With `--pick`, applies only the listed proposal indices. With `--review`, walks proposals one at a time with y/n/q prompts.

### Suggested DM workflow

1. **First session after install:** `/dm:dnd load` will offer to initialize the graph (with a backup-first prompt). Accept; review the proposed seed; approve.
2. **During session:** when a relationship shifts in narration, run `/dm:dnd graph add-edge` (or `close-edge`) with `--since` set to the current session number. Don't batch this — record at the moment of the narrative change so you don't forget.
3. **Before a heavy social/political scene:** run `/dm:dnd graph scene-context --place <current-place> --present <key-NPCs>` to refresh which relationships matter right now.
4. **At `/dm:dnd save`:** review the session log and add any edges you missed during play (the save flow runs an automatic sweep and presents proposals for approval).

---

## `/dm:dnd oracle <subcommand>` — solo/improv oracle tools

Dice-driven oracles for improvised play — they keep pacing transparent and rollable instead of letting the DM invent every beat. All subcommands invoke `python3 ${CLAUDE_SKILL_DIR}/scripts/oracle.py <subcommand>`. Rolls are stdlib-random and seedable (`--seed N`) for reproducibility. Zero LLM calls.

### `/dm:dnd oracle chaos [--campaign N]`
Show the campaign's current **chaos factor** (Mythic-style, 1–9). 1 = the PCs are firmly in control; 9 = the world is spinning out from under them. Stored in `state.md → ## Session Flags` as `chaos_factor: N` (default 5).

### `/dm:dnd oracle chaos set --campaign N --value V`
Set the chaos factor to V (clamped 1–9) and persist it to `state.md`.

### `/dm:dnd oracle chaos adjust --campaign N (--pc-won | --pc-lost)`
Move the factor one step the standard Mythic direction: `--pc-won` (PC achieved the scene goal) → −1; `--pc-lost` (PC was reactive or failed) → +1. Adjust once per scene.

### `/dm:dnd oracle ask [--likelihood L] [--campaign N | --chaos C] [--seed S]`
Ironsworn-shaped **yes/no** oracle. Likelihood ∈ {`sure-thing`, `likely`, `50/50`, `unlikely`, `no-way`} (default `50/50`); the chaos factor (read from the campaign, or `--chaos`) shifts the odds. Returns a verdict — `yes`/`no` optionally suffixed `-and` (extreme, on doubles) or `-but` (qualified, near the threshold) — plus the d100. Use when the fiction poses a question the prep doesn't answer.

### `/dm:dnd oracle event [--seed S]`
Mythic **Random Event Focus** (d100). Returns a direction label (`new NPC`, `NPC action`, `move toward thread`, `PC negative`, etc.) — interpret it against the campaign's current threads, NPCs, and locations. Use when a scene needs an unexpected turn.

### `/dm:dnd oracle scene [--seed S]`
Two-word **scene-meaning** generator (action verb + subject noun, One Page Solo Engine). Use as a spark when narration runs dry or an event focus rolls. Interpret loosely.

---

## `recap snapshot` / `recap diff` — precomputed party state-diff (load machinery)

Deterministic state-diff between two character snapshots — `python3 ${CLAUDE_SKILL_DIR}/scripts/session_recap.py`. Recaps are the #1 thing an LLM hallucinates (wrong HP, dropped facts); this computes the change set from data so narration never has to. Reads the character sheets at `~/.claude/dnd/campaigns/<name>/characters/*.md` and merges live `tracker.json` conditions/concentration. Zero LLM calls.

These subcommands are **load machinery, wired at `/dm:dnd load` step 6.5** — the
narrative `/dm:dnd recap` command above is unrelated. `diff` auto-advances the baseline,
so one call at load prints last session's mechanical changes AND re-baselines for the
next session, self-chaining forever. Do **not** snapshot at `/dm:dnd end` — an
end-of-session baseline diffed at next load reports nothing.

### `/dm:dnd recap snapshot --campaign N`
Snapshot the party's current state (HP/temp/level/hit dice/death saves/conditions/concentration/exhaustion/inspiration/spell slots) to `~/.claude/dnd/campaigns/<name>/.recap/`. Rolls the previous `last.json` to `prev.json`. Needed only at the **first-ever load** (no baseline exists yet); after that, `diff` maintains the chain itself.

### `/dm:dnd recap diff --campaign N [--before FILE] [--after FILE]`
Diff the prior snapshot against the current state and print a one-paragraph plain-English summary (e.g. *"Aldric: took 18 damage (30→12 HP); gained Poisoned; spent 2 level 1 slots."*), then advance the baseline to "now". With no `--before`, uses the stored `prev`/`last` snapshot; with no `--after`, snapshots live state on the fly. Run at every `/dm:dnd load` (step 6.5) as the mechanical half of the recap. `--json` emits the structured change list.

---

## `/dm:dnd tutor on` / `/dm:dnd tutor off`
Toggle tutor/learning mode. Write `tutor_mode: true/false` to `state.md` under `## Session Flags`. Session-scoped — does not persist to next `/dm:dnd load` unless explicitly set again. (Full tutor mode behavior is in SKILL.md.)

---

## `/dm:dnd autosave on` / `/dm:dnd autosave off`

Toggle the behind-the-scenes continuity checkpoint. Writes `autosave: on|off` to `state.md → ## Session Flags`. **Default is on.** Applies to every campaign type (structured, dynamic, sandbox) — it only ever writes the same continuity anchors a normal save writes, just more often, and never changes narration.

**What autosave does when on:**
1. **In-model micro-saves** (always available, no setup): the DM silently flushes continuity at scene boundaries and on a turn cadence — see the *Continuity micro-save* rule in SKILL.md. This keeps unsaved state near zero so a context compaction costs nothing.
2. **Deterministic Stop-hook checkpoint** (optional, opt-in): if the user has installed the hook, `autosave_checkpoint.py` snapshots `state.md` every turn and prompts a micro-save every N turns. Install once with:
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/install_autosave_hook.py        # enable
   python3 ${CLAUDE_SKILL_DIR}/scripts/install_autosave_hook.py --uninstall
   ```
   The hook reads this same `autosave` flag, so `/dm:dnd autosave off` silences it without uninstalling.

**On:** write `autosave: on`. Confirm: *"Autosave on — I'll checkpoint continuity behind the scenes so a context compaction never loses your place."*

**Off:** write `autosave: off`. Confirm: *"Autosave off — I'll only persist on /dm:dnd save and /dm:dnd end."*

**Why turn-count, not a context percentage:** the model cannot see its own context-usage level, so there is no reliable "save at 80% full" trigger from inside the skill. The cadence is keyed on turns instead, tuned to fire well before auto-compaction.

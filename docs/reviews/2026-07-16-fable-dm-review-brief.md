# Fable review brief — claude-dnd-skill DM & architecture

**You are Fable 5.** This file is the master brief for a **multi-session** review of this
D&D skill. Mission: an honest, deep review along the axes the owner cares about most —
**how well it plays like real D&D** and **how human the DM feels** — plus the architecture
underneath, so nothing falls apart mid-playthrough. You also leave behind durable reference
notes so every session (and future work) starts with full context instead of re-deriving it.

Repo: `C:\Users\axelg_p6dxxyr\Projects\experimental\claude-dnd-skill`
Owner: non-technical intern building this as a personal project; talks plainly, wants
substance over ceremony. You are Fable — run deep.

## The review is split across sessions (read this)

The work is broken into the sessions in the **ledger** at the bottom. **Run ONE session
per chat** to keep each context lean and focused — the owner launches them in order. The
durable artifacts you create (ARCHITECTURE.md, CONTEXT.md, the vault compass) are the
**bridge between sessions**: every session after A begins by reading them, so you never
re-derive the codebase from scratch. At the end of each session: update the artifacts,
tick the ledger, and hand back to the owner. Do not try to do the whole review in one run.

## Standing instruction — the dimensions are lenses, NOT a checklist

Every list of sub-questions below is a **starting seed, not a boundary.** Review the whole
tool through each lens **and beyond it.** If you find something that materially affects play
quality, DM realism, correctness, or the tool in general and it fits none of the named
dimensions — **report it anyway.** You are explicitly *not* constrained to the bullets
listed. When in doubt, surface it. The owner would rather see too much than have you
self-censor a real issue because it wasn't on the list.

## What this skill is (so you read it right)

It is a **prose-instruction-driven** DM. The "program" is mostly the three
`skills/dnd/SKILL*.md` documents that a model *executes* at the table; the ~30 Python
scripts are deterministic helpers (dice, HP, initiative, data lookup, rendering, prep bible
generation). So reviewing "how the DM behaves" is reviewing **prose as much as code** — the
instructions in SKILL.md *are* the behavior. Treat the prose as the primary artifact.

Recent work (merged to `main`, 236 tests green): a prep **premise-variance fix** — a
combinatorial premise seed-bank (`data/premise-seeds.yaml`) + a shared 7-tone catalog
(`data/tones.yaml`) + `scripts/prep/premise.py`, and a generalized tone-saturation rule.
Spec/plan under `docs/superpowers/`. That work is done; it is context, not your target.

## The problem this review also fixes: drift

There is **no `CONTEXT.md`, no ADRs, no architecture map.** The only "how it links" record
is a *chronological* vault log (`C:\Users\axelg_p6dxxyr\Vault\projects\claude-dnd-skill.md`,
~500 lines of dated entries) — the worst shape for "where is X / how does Y connect to Z."
Session A's output fixes this and becomes the anti-drift anchor for every later session.

## Ground rules (all sessions)

- **Propose, don't apply.** Write findings + concrete prose-rephrasing suggestions (with
  `file:line` and before/after prose). Do **not** edit the skill's prose or scripts — the
  owner approves changes later. The only files you create are the reference/findings docs
  named in each session.
- **Cite `file:line` for every claim.** No vague "the prep phase seems…". Point at it.
- **Never touch** `~/.claude/dnd/campaigns/` (live campaign data) or run destructive
  commands. Read freely; write only the reference/findings docs.
- Invoke skills via the Skill tool; read the current skill text, don't work from memory.
- End every session by updating artifacts + the ledger, then reporting to the owner.

## Orientation read-order (Session A does this fully; later sessions skim as needed)

1. `skills/dnd/SKILL.md` (346 ln) — the DM's core behavior contract.
2. `skills/dnd/SKILL-commands.md` (852 ln) — every `/dm:dnd` command procedure.
3. `skills/dnd/SKILL-scripts.md` (384 ln) — script syntax the prose calls.
4. Skim `skills/dnd/scripts/` (~30 files) + `scripts/prep/`, `data/`, `templates/`,
   `display/`, `scripts/graph/` — inventory, not line-by-line.
5. `docs/probes/2026-07-14-prep-dry-run.md` — an existing end-to-end prep probe.

---

# SESSION A — Orient & map (anti-drift foundation)

Produce two files:

**A1. `docs/ARCHITECTURE.md` (in-repo — versioned with the code so it can't silently rot):**
- **Subsystem inventory:** one line per script — what it does, what reads/writes it.
- **The three prose docs:** what each governs, where they overlap.
- **Data-flow / lifecycle:** the `/dm:dnd load → play → save → compaction` loop. Which
  command invokes which script; how `state.md`, `world.md`, `spine.json`, `npcs.md` /
  `npcs-full.md`, `session_tail.json` / `session-tail.md`, the campaign graph, and the
  `display/` + tracker/asset HTML flow into and out of each other.
- **The arc systems:** `authored` vs `dynamic` vs `structured` vs `sandbox` — how they
  differ and where each is handled.
- **Prose↔script contract:** places where prose tells the model to run a script — are the
  names/paths/flags consistent with the actual scripts?

**A2. Vault compass — `C:\Users\axelg_p6dxxyr\Vault\projects\claude-dnd-skill-compass.md`**
(a NEW, *stable* note — do NOT append to the chronological log). Contents:
- Pointers to `docs/ARCHITECTURE.md` and (after Session B) `CONTEXT.md`.
- **The orientation read-order** (so any session rebuilds context in minutes).
- **Known-fragile-links register** — drift/breakage hotspots (spine.json↔state.md arc-beat
  sync, compaction-survival reads, autosave cadence, session_tail regeneration, live-state-
  flags freshness). One line each; grows across every later session.
- **Open architectural questions** — seed it; later sessions drain it.
- **Session ledger mirror** (optional) — or just rely on this brief's ledger.

**End of Session A:** report the map + compass, tick the ledger, hand back.

---

# SESSION B — Domain modeling (clear the fuzzy terms)

**Bootstrap:** read `docs/ARCHITECTURE.md` + the vault compass first.

Many features landed since terms were last sharpened. Run `setup-engineering-skills`
**once** (configures where glossary/ADRs live), then `domain-modeling`. Sharpen the
overloaded vocabulary into `CONTEXT.md` + ADRs. Known-fuzzy seeds (not exhaustive — add
any you hit):
- **beat / spine / node / situation** — structural units; consistent meanings across prose?
- **arc type** — authored vs dynamic vs structured vs sandbox.
- **tone vs theme vs premise** — recently reworked; is the prose clean now?
- **cover / deed / faction-stance / live-state-flags / faction-move** — state vocabulary.
- **milestone vs XP** (XP deprecated) — any lingering contradiction?

Record hard-to-reverse decisions as ADRs.

**End of Session B:** report the glossary + any contradictions found; update compass; tick ledger.

---

# SESSIONS C–E — The review (one dimension per session)

**Bootstrap for each:** read `docs/ARCHITECTURE.md` + `CONTEXT.md` + the vault compass
first. Each session writes its own findings file
`docs/reviews/2026-07-16-findings-<dim>.md`, appends new fragile-links / open-questions to
the compass, and ticks the ledger.

**Remember the standing instruction: these bullets are lenses, not limits. Review the whole
tool through the dimension and report anything material beyond the listed items.**

### SESSION C — D1: Prep-phase story tailoring (and prep quality in general)
Does prep produce a *unique story bound to the settings chosen at prep time*, or generic
content with the settings pasted on? Starting seeds:
- **Character incorporation:** prep imports 5e sheets carrying level, class/subclass,
  weapons, spells, attributes, **personality traits, quirks, bonds, flaws**. Does the bible
  — world, spine beats, NPCs, quest seeds — actually *use* that? Are hooks tied to specific
  PCs' backstories/flaws? Does the spine's leveling/encounter design respect the party's
  real level path, gear, and subclass capabilities (`scripts/prep/bestiary.py`, `spine.json`
  `level_up_to`/`threats`/`gear`)?
- **Tone & world-type fidelity:** does the bible honor the tone (`data/tones.yaml`) and
  world/setting chosen at prep, or drift to a default register?
- **Shopping lists:** map-list + ambient-list (`templates/`, `render_assets.py`) — hints
  spoiler-free, acquirable, matched to the scenes the spine runs?
- **…and anything else** about whether prep sets up a good, playable, tailored campaign:
  pacing of the spine, node/situation design, quest-seed quality, what a real DM prepping
  a campaign would want that this doesn't produce.

### SESSION D — D2: DM humanness / dynamism (and table-feel in general)
Does the DM behave like a real person running a table? Starting seeds:
- **Steering & adaptation:** improv over script, "yes-and", reincorporation, reading
  engagement, pacing/bangs, reacting to PC *and* NPC choices, world-moves-without-player.
  Where does the prose enable this; where does it fall to rote?
- **Translating DM instinct into instructions** (the hard part the owner flagged): how do
  you turn a human DM's judgment / emotion / decision into concrete prose directions or
  script support? Do a **bounded** research pass (don't rabbit-hole) on established DM
  craft — situation-not-plot, PbtA "moves" as a model for codifying DM reactions, Sly
  Flourish "Lazy DM" prep, improv "yes-and" — and translate findings into **specific prose
  rewrites** for SKILL.md. Concrete diffs, not a reading list.
- **Rote tells:** over-narration, everything-ominous, "what do you do?" padding, NPCs as
  atmosphere-vessels — do existing guards actually prevent them?
- **…and anything else** about whether a player would feel a real, responsive DM across a
  session: consequence, memory, voice distinctness, fairness, surprise.

### SESSION E — D3: Architecture coherence (do fragments hold across a playthrough?)
Starting seeds:
- Trace a full session: `load → several scenes → combat → save → (context compaction) →
  reload`. Where can state be lost, double-counted, or contradicted?
- Compaction-survival: the prose leans on re-reading source-of-truth sections after
  compaction — are those anchors (`Live State Flags`, `session_tail`, continuity archive)
  actually kept current by the save/autosave paths?
- Arc-beat sync, milestone leveling, faction/deed ledger integrity, the HTML dashboard
  refresh loop — do the pieces stay consistent, or drift apart?
- **…and anything else** where the architecture could betray the player mid-play: race
  conditions between prose and scripts, silent data loss, contradictory state.

---

# SESSION F — Synthesis (light)

**Bootstrap:** read the three findings files + the compass.
- Merge into `docs/reviews/2026-07-16-fable-dm-review-summary.md`: grouped by dimension,
  each finding with `file:line`, severity, concrete fix (before/after prose diff for prose
  issues), plus an **"if you do three things"** priority list at the top.
- Finalize the compass (fragile-links register + open questions).
- **Batch fix-wave (owner pre-approved 2026-07-16, after Session B):** apply ALL accumulated
  prose/template contradiction fixes in ONE wave here — the Session A prose↔script drift
  items (ARCHITECTURE.md §7.1-7.5), the Session B contradictions (CONTEXT.md "⚠ Drift"
  flags + compass [B] entries: `[theme]`→`[tone]` arg, "Faction states"→"Faction activity"
  rename, XP mentions at SKILL.md:183-184/301, premise/theme wording, deeds format), and
  any C-E prose fixes the owner approves from the summary. Present the consolidated diff
  list first, apply on the owner's go, run the test suite. Then **refresh every stale
  `file:line` citation** in ARCHITECTURE.md, CONTEXT.md, and the compass — the fixes shift
  line numbers, and those cites are the anti-drift anchors. This ordering (fix-wave last,
  single citation refresh) was chosen deliberately: do not apply prose fixes in C-E.
- Tick the ledger complete.

---

## Deliverables recap
1. `docs/ARCHITECTURE.md` — linkage map (Session A).
2. `CONTEXT.md` + ADRs — domain-modeling (Session B).
3. `Vault\projects\claude-dnd-skill-compass.md` — stable pointer/fragile-links/read-order note.
4. `docs/reviews/2026-07-16-findings-{d1,d2,d3}.md` — per-dimension findings (C–E).
5. `docs/reviews/2026-07-16-fable-dm-review-summary.md` — merged summary + priorities (F).

Nothing else gets edited without owner approval.

## Session ledger (update at the end of each session)
- [x] **A** — Orient & map → `docs/ARCHITECTURE.md` + compass (done 2026-07-16)
- [x] **B** — Domain-modeling → `CONTEXT.md` + ADRs 0001-0005 + `docs/adr/README.md` lineage note (done 2026-07-16)
- [x] **C** — D1 prep-phase review → findings-d1 (done 2026-07-16; 11 findings, 3 HIGH — party sheets unread, L1 hardcode, zero prep NPCs)
- [x] **D** — D2 DM-humanness review (+ research) → findings-d2 (done 2026-07-16; 12 findings, 3 HIGH — authored arcs orphaned from steering/pre-emption gates, spine situation/threats/secret never read in play, Character Pillar unconsumed at table)
- [ ] **E** — D3 architecture-coherence review → findings-d3
- [ ] **F** — Synthesis → summary + priorities

**To launch a session:** tell Fable which session letter to run and point it at this file —
e.g. *"Read `docs/reviews/2026-07-16-fable-dm-review-brief.md` and run Session A."*

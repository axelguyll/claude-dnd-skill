# claude-dnd-skill

A prose-instruction-driven D&D 5e Dungeon Master skill. The three `skills/dnd/SKILL*.md`
documents are the program a model executes at the table; ~35 Python scripts are
deterministic helpers. This glossary is the canonical vocabulary for the whole fork —
prose, templates, scripts, and reviews. Written Session B of the 2026-07-16 Fable review;
prior art: `dm-app/CONTEXT.md` (the planning repo whose prep-phase vocabulary this fork
absorbed — see `docs/adr/README.md` for the ADR lineage).

Contradictions found while writing this glossary are flagged inline with **⚠ Drift**.
The Session F fix wave (2026-07-16) resolved most of them — resolved flags are marked
**✓ Fixed** and kept one line each so they aren't re-derived; the surviving ⚠ Drift
flags are still live. Citations refreshed post-wave.

## Language — story structure

**Arc**:
The campaign-level story structure stored in `state.md → ## Campaign Arc`, in exactly one
of four formats (see Arc type). "Arc" alone always means this campaign arc; the succession
counter is `arc_number` (a completed arc is followed by arc N+1 via `/dm:dnd arc new`).
_Avoid_: "arc" for the Threat Escalation Arc (call those **threat stages**), for the spine
(the spine lives *inside* the authored arc), or for `arc.md` unqualified (say "the
structured arc tree").
**⚠ Drift**: `world.md → ## Threat Escalation Arc` and `state.md → Threat arc stage`
(templates/state.md:13) reuse "arc" for an unrelated five-stage escalation table.

**Arc type**:
Which of the four arc systems a campaign runs: `sandbox` (no arc tracking), `dynamic`
(auto-generated 3-act/6-beat arc, revisable, from legacy `/dm:dnd new`), `structured`
(imported published module; pointer window + `arc.md` tree + lazy `source/` corpus), or
`authored` (the flagship `/dm:dnd prep` path; `spine.json` + state.md mirror; the only
type with leveling). Declared as `type:` in `## Campaign Arc`.
_Avoid_: "campaign type", "mode".

**Act**:
The fixed three-part frame of dynamic and authored arcs (Setup / Confrontation /
Resolution; `act: 1|2|3` on every beat). Structured arcs also group chapters by act.
Campaign length scales by beat count, never act count ("more beats, not more arcs").
_Avoid_: "act" for a session or a scene.

**Chapter**:
The structured-arc unit (imported modules only): one entry in `arc.md` carrying
`key_beats`, a `telegraph_scene`, and a `source_ref` to its lazy corpus file
`source/<id>.md`. Dynamic/authored arcs have no chapters — only acts and beats.
_Avoid_: "chapter" for an act or a beat in non-imported campaigns.

**Beat**:
One unit of an arc or spine: a *situation with a committed consequence* — fields
`what_changes` (the consequence, never an event), `world_pressure`, `label`, `status`.
Dynamic beat ids are strings (`"1a"`–`"3b"`, fixed dramatic roles); authored/spine beat
ids are sequential ints. Beats are the unit of steering, completion
(`/dm:dnd beat complete`, `arc advance`), the Deeds ledger, and milestone leveling.
_Avoid_: "beat" for a narration unit (that is a **moment**), "quest", "objective",
"encounter" — a beat is a situation, may contain an encounter, is not one.
**⚠ Drift**: prose reuses "beat" for narrative moments — session tail "narrative beats"
(SKILL-commands.md:471), "plot beats" (SKILL-commands.md:146), "closing beat" /
"first beat of every new scene" (SKILL.md:112,149). Same word, different unit; the
session-tail sense is *narrative*, not arc-beat. (Documented, not renamed.)
**⚠ Drift**: `current_beat` is a string in dynamic arcs (templates/state.md:113) and an
int in authored arcs (templates/state.md:160) — same field name, two types.

**Moment**:
The narration pacing unit: one image, one event, or one line of dialogue that moves
things (SKILL.md:97). Pre-choice narration caps at about three moments, scaled by scene
heat. This is the canonical word for a unit of *prose*; reserve "beat" for arc structure.
_Avoid_: "beat" (arc unit), "paragraph".

**Spine**:
The mechanical half of the authored Bible: a schema-validated sequence of 6–8 beats in 3
acts plus a required `party` block (`size` + `start_level`, from the actual imported
sheets — `spine.json`), each beat carrying `situation` / `what_changes` /
`world_pressure` / `level_up_to` / `gear` / `threats` / `secret` / `status`. Heavy
source of truth, opened only at `/dm:dnd beat complete` (after a `mirror_check.py` step-0
drift check) and the authored `arc revise` write-back; the **current** beat's
situation/threats/secret ride hot in the mirror's `steering_notes` — the rest of the
spine is cold storage.
_Avoid_: "arc" as a synonym — the spine is the beat structure *inside* the authored arc;
"plot" — beats are situations, not scripted scenes.

**Situation**:
A prep unit with a goal at stake and multiple ways in — it doesn't care how the player
approaches it (SKILL.md:138). The spine's per-beat `situation` field ("what the party
walks into", templates/spine.md:43 — must embed ≥3 hooks, the rule of three defined at
spine.md:52) and Adventure Nodes are both situations.
_Avoid_: "plot", "scene" (a scene is what actually happens at the table; a situation is
what was prepped). Note: `state.md → ## Current Situation` is an unrelated status header
(where the party is right now), not a prep situation — accepted name collision.

**Adventure node**:
One situation in the world's loose 3–5 node web (`world.md → ## Adventure Nodes`;
imported campaigns keep the full set in `world-nodes.md`, pulled per current act). Nodes
connect in multiple directions and *move* rather than disappear when skipped; each
records what happens if the party never arrives — that feeds Faction Moves.
_Avoid_: bare "node" — always qualify, because **graph node** (an entity record in
`graph.json`: npc/faction/place/item/thread) is a different thing entirely.

**World pressure**:
A beat's built-in faction/NPC move that creates the conditions for the beat — run as a
visible world event *before* the beat lands ("never deliver a beat cold"). May be
event-shaped; if players pre-empt it, that triggers revision, not failure.
_Avoid_: "foreshadowing" (pressure is the world acting, not hinting), "railroading".

**Telegraph**:
The structured-arc equivalent: a chapter's `telegraph_scene`, a setup scene giving 2–3
apparent paths that converge on the required beat so it feels earned (SKILL.md:242).
_Avoid_: conflating with world pressure — telegraph is a *scene you run*, pressure is a
*move the world makes*; structured arcs use telegraphs, dynamic/authored use pressure.

**Pre-emption**:
The state where a beat's world pressure was visibly delivered but its `what_changes`
consequence did not land (usually because players acted faster than the world). Checked
at every `/dm:dnd end` for dynamic AND authored arcs; automatic input to `/dm:dnd arc
revise` with three landing paths: cost / secondary consequence / deferred
(SKILL.md:274-278, SKILL-commands.md:541-544).
_Avoid_: "beat skipped" — the consequence is still owed; only its shape changes.

**Steering**:
Guiding play toward the current beat with world pressure, not walls — the per-arc-type
rule sets in SKILL.md:238-279 plus the live `steering_notes` field. Authored arcs reuse
the dynamic steering rules — the gate itself says so (SKILL.md:256 matches `type:
dynamic` or `type: authored`; decision recorded in docs/adr/0003).
_Avoid_: "railroading" (steering is pressure + telegraphs; walls are last-resort and
disguised as fiction).

## Language — prep

**Prep** / **Bible**:
`/dm:dnd prep` generates the authored campaign **Bible** before session one: the world
layer (`world.md` + NPCs), the spine (`spine.json`), the seeded `state.md`, and the
shopping lists. The Bible is spoiler-sealed by discipline — the host reads only the
shopping lists.
_Avoid_: "campaign setup" (that is legacy `/dm:dnd new`), "the docs".

**Premise**:
The campaign's ground situation in one sentence — *what it is fundamentally about* at the
level of setting, conflict, and antagonist (`world.md → Premise`). A prep input (host may
supply verbatim) or rolled via the premise scaffold.
_Avoid_: "theme" — the premise is the situation; the theme is its meaning.
**✓ Fixed (F wave)**: the two template definitions now diverge hard — world.md:9
"what is HAPPENING, never what it means" vs state.md:63 "what this story MEANS, never
what happens".

**Premise scaffold**:
The output of `scripts/prep/premise.py`: one rolled entry per orthogonal axis (setting /
conflict / antagonist / twist, from `data/premise-seeds.yaml`) colored by a tone, which
the DM *reconciles* into one coherent premise — discarding any axis that fights the
others. Rolled, not free-associated, to force variance.
_Avoid_: treating the scaffold as the premise — reconciliation is mandatory.

**Tone**:
One of the seven catalog ids in `data/tones.yaml` (heroic / mythic / grimdark / horror /
intrigue / swashbuckling / cosmic) — the single source of truth for both `prep` and
`new`. Written to `world.md → ## Campaign Tone & Genre`. Governed at the table by the
saturation rule: tone belongs to the beats that carry the story, not every scene
(SKILL.md:26).
_Avoid_: "theme", "genre" unqualified, "mood" (the catalog's `mood_note` is a field, not
the term).
**✓ Fixed (F wave)**: the `/dm:dnd new` argument is now `[tone]` (SKILL-commands.md:9,32)
— it pre-fills Tone; the `theme` arc field (derived at step 13) no longer shares a name
with it.

**Theme**:
The dynamic/authored arc field: one sentence stating what the story *means* — "not what
happens but what it means" (templates/state.md:63; spine `theme`, carried verbatim into
the arc mirror). Paired with `resolution` (the committed endpoint shape).
_Avoid_: "tone" (register), "premise" (situation), "moral".

**Quest seed**:
One of the 3–5 hook sketches in `world.md → ## Quest Seed Bank`, derived from threat /
factions / mystery / NPC motivations at world generation.
_Avoid_: bare "seed" — see **Seed** disambiguation below.

**Threats** / **CR band**:
A beat's monsters, by exact SRD name with an optional `Nx ` count prefix (`"3x Goblin"`;
bare name = 1), each with CR inside the band `bestiary.band_for_level()` computes for
the party's level *during* that beat (level before the beat's own `level_up_to` applies
— `schema.party_levels`, seeded from `party.start_level`). Empty list = pure-social
beat. Validation rejects unknown names, out-of-band CRs, and zero counts. The count is
the action-economy half the band math doesn't cover — shaped to `party.size`.
_Avoid_: "monsters" unqualified; "difficulty" (a prep *input* that shifts authoring
guidance within the band — easy/standard/deadly, SKILL-commands.md:352; the band itself
is derived).

**level_up_to**:
A beat's *absolute* target party level (int 2–8 or null), strictly monotonic across the
spine and always above `party.start_level`; the final beat's is never null — the arc
must end leveled. Absolutes self-heal; deltas compound errors.
_Avoid_: "levels_gained", any delta phrasing.

**Milestone leveling**:
Leveling driven by beat completion: `/dm:dnd beat complete` reads the beat's
`level_up_to`, stamps `⚠ LEVEL UP PENDING (Level N)` on each sheet via
`prep/milestone.py`, and the pending marker *is* the authorization at `/dm:dnd level up`
(XP gate bypassed, SKILL-commands.md:673). Authored campaigns only — the legacy paths
(`new`, `import`) have **no leveling path at all** in this fork. A stranded pending
marker is surfaced at load (SKILL-commands.md:101).
_Avoid_: "XP", "leveling by kills".
**✓ Fixed (F wave)**: the Milestone opener is now authored-scoped (SKILL.md:325), and XP
is gone from live prose — tier rows (SKILL.md:190-191) and the per-turn persist step
(SKILL.md:314) no longer mention it; consistent with "combat end awards no XP"
(SKILL-commands.md:754).

**XP** (deprecated):
Retained only so legacy campaigns' sheets stay readable (`xp.py`, `character.py xp`).
Never called in the live flow; never awarded at combat end.
_Avoid_: writing new prose that mentions XP outside the deprecation notices.

**Shopping list**:
The host-readable prep artifacts: `map-list.md` (spoiler-scrubbed, acquirable map
descriptions) and `ambient-list.md` (ambient sound handles). Rendered into `assets.html`
by `render_assets.py`; sound cues at the table may only reference handles on the ambient
list.
_Avoid_: "catalog", "asset pipeline" — these are lists the host shops from by hand.

**Supporting cast**:
The cheap NPC tier: an index-only row in npcs.md (Name/Role/Faction/Location/Attitude/
Notes with exactly one distinct playable trait) and **no npcs-full.md section** — that
absence *is* the tier marker; there is no tier column. Seeded 6–8 at creation by both
`/dm:dnd new` (step 11.5) and `/dm:dnd prep` (step 1.5 supporting pass), and by default
for NPCs improvised mid-scene. Promoted one-way to a full entry before their first
substantive dialogue (SKILL.md, Active DM Mode).
_Avoid_: "minor NPC", "background NPC" (undefined); calling a promoted NPC "supporting"
after their full entry exists.

## Language — state

**Live State Flags**:
The compaction-resistant anchor section of state.md: Cover, Faction stances, and NPC
dispositions as compact key-value facts. First stop of the re-read ladder; updated at
every save and micro-save.
_Avoid_: "flags" unqualified (Session Flags is a different section), "state" unqualified.

**Cover**:
A PC's assumed identity or false pretense, tracked per-PC in Live State Flags with status
INTACT / BLOWN / PARTIAL and a one-line reason.
_Avoid_: using bare "cover" in combat narration for the 5e AC mechanic — say "half cover"
/ "three-quarters cover" so the two never collide in a recap.

**Faction stance**:
The authoritative party-relative standing scalar: `[Faction]: Allied / Friendly / Neutral
/ Suspicious / Hostile — reason`, in Live State Flags (only non-neutral factions listed).
The single reputation scalar — nothing else duplicates it. Every stance shift must cite a
deed.
_Avoid_: "reputation score", "standing" as a field name (fine as prose), and especially
"faction states" — the old name of the World State line.
**✓ Fixed (F wave)**: the World State line is now **"Faction activity"**
(templates/state.md:14, with an inline pointer to the authoritative scalar) — the
two-letter "states"/"stances" conflation trap is gone. `Live State Flags → Faction
stances` (templates/state.md:45) remains the single reputation scalar.

**Deed** / **Deeds ledger**:
An append-only state.md log of *party* actions that move faction reputation:
`<beat id or session number> — <faction> — <what the party did> — <+/−/neutral>`. The
party-side provenance that the world-side Faction Moves log does not capture; every
Faction-stance shift must cite one (dm-app ADR-0016 decision B) — including shifts made
at a micro-save flush (SKILL.md:236).
_Avoid_: "reputation system" — the ledger is the audit trail, not the scalar.
**✓ Fixed (F wave)**: the template format key now matches the save procedure —
`<beat id or session number>` in both (templates/state.md:29, SKILL-commands.md:467).

**Faction Move**:
The world-side answer to "what did this faction do while the party was occupied?" — one
line per active faction, written at every save/end into `state.md → ## Faction Moves`. A
move the party didn't prevent should surface as a visible world change; faction moves are
the raw material for bangs.
_Avoid_: conflating with deeds (deeds are party actions; moves are faction actions).

**Continuity Archive**:
Per-session 3–5 bullet summaries in state.md for sessions archived out of
`session-log.md` (only the 2 newest log entries stay live). Compressed against the graph:
relational restatements dropped, mechanical/plot/atmospheric kept.
_Avoid_: "session summary" unqualified.

**Session tail**:
The final-stretch narrative record written at save and refreshed at every micro-save:
`session_tail.json` (5–8 most important narrative beats as JSON) + `session-tail.md`.
Compaction-survival artifact; verified at `/dm:dnd end`, read at load step 5 and by the
re-read ladder's "what just happened this session" stop (SKILL.md:224) — the freshest
narrative record post-compaction.
_Avoid_: "recap" — the tail is written state, a recap is delivered narration.

**Micro-save**:
The silent continuity flush at scene boundaries / every few turns when `autosave: on`
(default): update Live State Flags (+ the Deeds line for any stance shift), append
graph relationships narrated on-screen (inferential edges wait for the save sweep),
refresh the session tail, and ask the off-screen faction-move question once. Not a full
`/dm:dnd save` — no session-log rewrite, no narration, no interruption (SKILL.md:236).
The optional Stop hook is a backstop, not the mechanism.
_Avoid_: "autosave" for the full save; "checkpoint" (the hook's snapshot is a different
artifact).

**Campaign graph**:
The typed-edge relationship store `graph.json` (`campaign_graph.py`): **graph nodes**
(npc / faction / place / item / thread) joined by time-stamped edges
(`since_session` / `until_session`), so historical state is recoverable. Supplements —
never replaces — `npcs-full.md` and the session log. `scene-context` is the primary
in-play query.
_Avoid_: bare "node" (see Adventure node), "knowledge base".

**roll_mode**:
Session flag deciding who rolls PC d20s: `players` (default — call for the roll and
*wait*; never auto-roll a PC) or `auto` (DM rolls openly with shown math). NPC dice and
initiative are always DM-rolled.
_Avoid_: "dice mode", "manual mode".

**Seed** (disambiguation — always qualify):
Four unrelated senses in this repo: **quest seed** (world.md hook sketch), **premise
seed bank** (`data/premise-seeds.yaml` axes), **graph seed nodes** (`graph init`
proposals), and `--seed` (RNG determinism flag on `premise.py` / `dice.py`).
_Avoid_: bare "seed" in prose or findings.

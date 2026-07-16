# Fable DM review — merged summary (Session F, 2026-07-16)

*Synthesis of the three per-dimension findings files (D1 prep tailoring, D2 DM humanness,
D3 architecture coherence). Full argumentation, corroborating evidence, and complete fix
text live in `2026-07-16-findings-{d1,d2,d3}.md` — this file is the merged view plus the
fix-wave manifest. 38 findings total: 9 HIGH, 18 MEDIUM, 11 LOW.*

**Line-number note:** citations are against the files *before* the Session F fix wave
(same baseline as the findings files). ARCHITECTURE.md, CONTEXT.md, and the vault compass
carry post-wave refreshed citations; this file and the findings are historical records.

---

## If you do three things

1. **Wire the flagship authored path into its own dynamism machinery** (D2-1 + D2-2 + E8,
   with riders E4/E5). `type: authored` matches no steering gate, no end-of-session
   pre-emption check, no revision path, and no end-of-campaign path — and the table never
   reads the spine's `situation`/`threats`/`secret` while a beat is in play. The best
   design in the tool (steering, pre-emption, prep) is fully built and fully disconnected
   on the path new campaigns actually use.

2. **Bind prep to the party** (C1 + C2 + C3). Prep names the imported party sheets as an
   input and never reads them — not for hooks, not level, not size, not class. It also
   ships a bible with zero NPCs while the spine and the table-time NPC-voicing gate assume
   they exist. New prep steps 0.7 (read the party, Party Hooks) and 1.5 (NPC layer), plus
   the owner-decided required `party` block in spine.json.

3. **Fix the three unplugged compaction/lifecycle wires** (E1 + E2 + E3). The session
   counter is seeded 0 and never incremented (kills graph history, log archival, legacy
   detection); the session tail — the only anchor micro-save keeps fresh — has no reader;
   `## Active Combat` is written once at combat start, so mid-combat compaction loses the
   fight. All three are cheap prose fixes.

---

## D1 — Prep-phase story tailoring (Session C, findings-d1)

**Verdict:** strong on premise variance, tone threading, spoiler discipline, and the
schema validation gate; weak on exactly the asked-about axis — the party. A bible prepped
for *this* party and one prepped for *any* party are currently the same bible.

### HIGH

**C1 — Prep never reads the party sheets it declares as input** · SKILL-commands.md:279-281, 283-344
- Before: inputs list "premise …, tone …, difficulty, and the imported party sheets"; no
  step of the procedure reads `characters/*.md` or any PC fact; the Character Pillar
  (built at `character new` step 2 as a hook anchor) is never consumed at prep; world.md
  has no party-facing section.
- After: new **step 0.7** — read every sheet before authoring; extract level, class,
  equipment, Pillar, backstory; bind world (≥1 faction/node/mystery element per PC,
  logged in new `world.md → ## Party Hooks`), spine (≥1 beat's situation/secret per PC;
  class-usable gear), and quest seeds (≥1 per PC). Template gains `## Party Hooks`.

**C2 — Spine validation hardcodes a level-1 start; party level and size ignored** · schema.py:27, templates/spine.md:48-49, SKILL-commands.md:310
- Before: `party_levels()` starts at `current = 1`; an imported L3 party gets a
  green-validated misbanded spine; no schema field, prep step, or bestiary flag knows
  party size.
- After (**owner decision 2026-07-16 — required, not optional**): `spine.json` gains a
  required `party` block (`size`, `start_level`) populated at step 0.7 from the actual
  sheets; `schema.party_levels` reads `start_level`; prep step 2's authoring guidance
  references `party.size` for encounter shape and quest design; step 0.7 warns the host
  when the party is above L1.

**C3 — Flagship prep produces a bible with zero NPCs** · SKILL-commands.md:327-328
- Before: prep step 5 copies `npcs.md` empty; `npcs-full.md` never created; spine
  `world_pressure` and the NPC-voicing gate (SKILL.md:212) assume named NPCs exist;
  legacy `new` makes 3 full NPCs — inverted quality.
- After: new **step 1.5** — full `npcs-full.md` entry (same fields as `new` step 11) +
  index row for every NPC named in world.md, minimum 3, name-registry-checked; every
  spine `world_pressure` actor must be one of them. Step 5 amended accordingly.

### MEDIUM

**C4 — `difficulty:` argument is a dead input** · SKILL-commands.md:277,280, bestiary.py:15-29
- Before: accepted in the signature and the input list, consumed by nothing.
- After (recommended: wire, owner may strike): difficulty shifts step-2 authoring
  guidance (easy → lower half of band / solos below ceiling; deadly → ceiling picks and
  paired threats). Alternative: cut from lines 277/280.

**C5 — Spine threats carry no counts, no encounter budget** · templates/spine.md:41, SKILL-commands.md:305-312
- Before: `threats` is a flat name list — "Goblin" could mean one or eight; banding
  governs species, not encounters.
- After: allow `"3x Goblin"` count prefixes (schema parses `Nx ` prefix, ~10 lines, bare
  names stay valid); step 2 gains one sentence on shaping action economy deliberately.

**C6 — "≥3 hooks (rule of three)" undefined and homeless** · SKILL-commands.md:309, templates/spine.md
- Before: required per "the schema in templates/spine.md", which never defines a hooks
  field or uses the word.
- After: definition block in spine.md (three genuinely different entry points into the
  fiction, written into `situation` prose; authoring standard, not validated);
  SKILL-commands.md:309 points at it.

**C7 — Spine and world layer are not bound to each other** · SKILL-commands.md:305-312, world.md:133-153
- Before: no requirement that `world_pressure` names world.md entities; Adventure Nodes
  and spine beats are two parallel situation inventories with no stated relationship.
- After: two sentences in step 2 — every `world_pressure` names a faction/NPC that
  exists in world.md (post-C3: npcs-full.md); every beat's `situation` anchors at or
  adjacent to a node or named location.

**C8 — Shopping lists are prep-frozen; arc revision strands them** · SKILL-commands.md:315-326, SKILL.md:204
- Before: lists generated once at prep step 4; `arc revise` can relocate scenes; the
  cue whitelist makes a moved location legally silent; nothing refreshes the lists.
- After: merged with **E9** into one consolidated revise step — update Adventure Nodes,
  propose graph edge updates, append list entries, re-run `render_assets.py`.

### LOW

**C9 — Bestiary tone-blind; world knobs unrolled in prep** · bestiary.py:45-52, world.md:6-8
- After: one sentence each in prep steps 1-2 (prefer tone-fitting creature types; fill
  the remaining Tone & Genre knobs coherently).

**C10 — No post-catalog end-to-end probe** · docs/probes/2026-07-14-prep-dry-run.md
- Not a wave fix — **follow-up backlog**: re-probe after the wave (party-binding audit,
  one full `beat complete` with the E4 round-trip, simulated mid-combat compaction,
  session-count bump check).

**C11 — spine.md header calls the seeded block "dynamic arc format"** · templates/spine.md:7
- After: "(the authored block — dynamic-format mirror, see CONTEXT.md 'Arc type')".

---

## D2 — DM humanness / dynamism (Session D, findings-d2)

**Verdict:** unusually strong on rote-tell suppression and narration discipline; the
dynamism failures are almost all one shape — *a mechanism was designed and the wiring
that fires it at the table was never written*, with the flagship authored path the
biggest victim.

### HIGH

**D2-1 — `type: authored` matches no steering gate, no end-of-session arc check, no revision path** · SKILL.md:225,243,245; SKILL-commands.md:448,698,723-733
- Before: steering sections gate literally on `type: structured` / `type: dynamic`;
  `end`'s arc + pre-emption check is dynamic-only; `arc advance/revise/new` are
  dynamic-only. ADR-0003's reuse decision exists only in the ADR and a template comment —
  a literal read gives the flagship path no steering, no pre-emption, no revision.
- After: dynamic steering gate widened to `type: dynamic` **or `type: authored`** (with
  the three stated differences); dynamic preamble mentions prep origin; `end` arc check
  covers authored (`beat complete` instead of `arc advance`); `revise` extended to
  authored **with the E4 ordering contract baked in**: write spine.json first → re-run
  `schema.py` gate → regenerate the state.md mirror *from the spine* → append
  `revision_log`; plus `beat complete` gains a step-0 mirror-vs-spine check (stop and
  reconcile with the host on mismatch — never silently pick a winner).

**D2-2 — The prep bible's creative core is sealed from the table** · SKILL-commands.md:103-107, 337-338, 346-363
- Before: the state.md mirror carries only id/act/label/what_changes/world_pressure/
  status; load forbids opening the spine; `beat complete` reads it only for
  `level_up_to`/`gear` — so a beat's `situation`, `threats`, and `secret` are never read
  *while the party plays that beat*.
- After: the current beat is hot, the rest of the spine cold — `beat complete` step 2
  regenerates `steering_notes` with the new current beat's situation (one sentence),
  threats (verbatim), and secret; prep step 6 seeds beat 1's `steering_notes` with the
  same three items; **E5 rider**: secret goes on the last line and `arc status`
  (authored) omits the secret line when printing.

**D2-3 — Character Pillar planted at creation, never consumed at the table** · templates/character-sheet.md:8-13, SKILL.md:121-127
- Before: "Active hooks: … update each session" is addressed to nobody — no save/end
  step touches it; "pillar" appears nowhere in Active DM Mode or the 13 standards.
- After: Standard 9 gains a "Play the pillars" paragraph (re-read at session open, aim
  ≥1 scene at a pillar before the pressure point, note it in Active hooks); save gains a
  pillar-hooks step; Standard 6's pressure point "preferably aimed at a Character
  Pillar".

### MEDIUM

**D2-4 — Failure never advances the world's agenda** · SKILL.md:117
- After: append the ordered complication palette drawn from the world in motion
  (faction advances a goal → telegraphed danger steps closer → concrete cost →
  situation worsens; ignored telegraphed danger arrives full-force; never name the
  machinery).

**D2-5 — Session shape has no clock in chat** · SKILL.md:110, SKILL-commands.md:68-74
- After: load asks "How long are you playing today?" (`session_length` in Session
  Flags); SKILL.md:110 counts scenes instead of wall-clock ("pressure point by scene
  2/3-4; open-ended re-raises every 3-4 scenes; wrap-up signal → engineer the closing
  beat now").

**D2-6 — Engagement signals are table-body signals** · SKILL.md:76,85
- After: chat-medium translation inserted (flagging = shrinking replies / first-option
  picks / "what else is here?" / going meta; engaged = in-character dialogue, unprompted
  plans; two-three shrinking turns → pick a re-engagement tool now).

**D2-7 — Nothing re-anchors the behavior contract or `roll_mode` after compaction** · SKILL.md:213-221,223,276
- Before: the ladder covers campaign facts only; Session Flags absent from every anchor.
- After: ladder first stop also re-reads `## Session Flags`; micro-save rule gains a
  post-compaction behavior-contract re-read (Narration principles + Dice convention);
  **E6 rider**: load step 5 writes `skill_dir` into `active-campaign.json` so the path
  survives compaction (runtime dir is derivable; autosave_checkpoint.py tolerates the
  extra key), with the caveat that a disk re-read returns `${CLAUDE_SKILL_DIR}`
  unexpanded — behavior rules only, not runnable paths.

**D2-8 — The world only moves at `/dm:dnd end`** · SKILL.md:135,223; SKILL-commands.md:380
- After: micro-save flush gains "did any active faction take a step just now,
  off-screen?" — if yes, one `## Faction Moves` line immediately, surfaced as a sight or
  rumour within a scene or two; the end sweep becomes a catch-up pass.

**D2-9 — Oracle toolkit orphaned from Active DM Mode** · SKILL-commands.md:794-815, SKILL.md:209
- After: one narration-principles bullet pointing at `oracle ask` / `oracle event` when
  the fiction poses a question prep doesn't answer, plus chaos-factor adjustment at
  scene ends.

### LOW

**D2-10 — Two five-step attitude scales that don't match** · SKILL-commands.md:604, templates/npcs.md:14, templates/state.md:45
- After: one scale everywhere, faction wording wins ("Suspicious" replaces
  "unfriendly"); three one-line edits.

**D2-11 — NPC `Current goal` says "update each session"; nothing updates it** · templates/npcs.md:16, SKILL-commands.md:374
- After: save's disposition step also refreshes `Current goal` in npcs-full.md for NPCs
  who acted or were acted on.

**D2-12 — Solo-frame prose; no spotlight rule for multi-PC parties** · SKILL.md:23,85,122
- After: one line in Standard 9 — rotate the pillar/pressure target across PCs; note
  the last target in `## DM Style Notes`.

---

## D3 — Architecture coherence (Session E, findings-d3)

**Verdict:** the compaction-survival design is genuinely good; three load-bearing wires
are unplugged (counter, tail, mid-combat state). All four C/D handoff checks resolved —
D2's fixes are safe **with the riders** (E4/E5/E6), which are folded into the D2 entries
above.

### HIGH

**E1 — Nothing ever increments `Session count` (or `Last session`)** · SKILL-commands.md:61,329,366-438,442-457
- Before: seeded 0 by `new`/`prep`; no save/end step touches the header. Blast radius:
  graph `--since` stamps, log-archival trigger (>3 never fires), legacy detection,
  name-registry/npc-rename stamps, `scene-context --at-session`. Session boundary itself
  undefined (double-bump risk).
- After: save step 1 defines the boundary once — first save since load creates
  `## Session N` with N = header + 1 and updates `Session count` / `Last session`;
  later saves in the same sitting update the existing entry, no bump. **Lands first in
  the wave** — other fixes cite "current session N".

**E2 — The session tail is the only anchor micro-save keeps fresh, and nothing reads it** · SKILL.md:213-223; SKILL-commands.md:98-110,386-389,457
- Before: ladder sends recap claims to save-time artifacts; the tail — refreshed every
  scene boundary — has no reader anywhere (its reader was the torn-down display replay,
  CHANGELOG.md:336).
- After: ladder gains a "what just happened this session" stop reading
  `session-tail.md`; load step 5 reads it (5-8 bullets) so the opening recap can name
  last session's final stretch.

**E3 — Mid-combat compaction loses the fight** · SKILL-commands.md:661, SKILL.md:288-303
- Before: `## Active Combat` written once at combat start; evolving STATE_JSON lives
  only in context; the ladder has no combat entry.
- After: per-turn step d2 writes the STATE_JSON back to `## Active Combat` after each
  render; ladder gains a mid-combat stop (re-read the block + `tracker.py list`; never
  reconstruct a fight from compacted memory).

### MEDIUM

**E4 — Authored `arc revise` spine write-back: required, with ordering contract** — folded into D2-1 above.

**E5 — `steering_notes` payload safe; secret-omission rider** — folded into D2-2 above.

**E6 — SKILL.md re-read feasible only with a durable skill-dir anchor** — folded into D2-7 above.

**E7 — Continuity Archive compression runs before the graph sweep it depends on** · SKILL-commands.md:391-420 vs :422-438, SKILL.md:223
- Before: compression drops relational bullets assuming the graph holds them — but the
  approval-gated sweep hasn't run yet; `skip` = fact lost from both stores. Adjacent
  contradiction: micro-save appends edges silently vs ":436 never write proposed edges
  silently".
- After: sweep reordered before archival; drop-rule hardened (drop only when the edge is
  confirmed present; in doubt, keep); micro-save appends only edges explicitly narrated
  on-screen — inferential edges wait for the sweep.

**E8 — An authored campaign that finishes its spine has nowhere to go** · SKILL-commands.md:352-356,698,703-706
- Before: final `beat complete` sets `current_beat: null` and stops; continuation/
  sandbox conversion is dynamic-only.
- After: final-beat branch mirrors :703-706 — offer `arc new` (successor arc in dynamic
  format from the resolved world) or convert to sandbox.

**E9 — Revise relocation also strands world.md nodes and the graph** · SKILL-commands.md:723-733, SKILL.md:132
- After: one consolidated revise step (merged with C8): update affected Adventure
  Nodes, propose matching graph edge calls in the same confirmation, refresh shopping
  lists + re-run `render_assets.py`. (`world-nodes.md` is safe — structured-only.)

**E10 — Micro-save moves faction stances without their deeds** · SKILL.md:223, SKILL-commands.md:382-384
- After: one clause in the flush list — a stance change appends its Deeds line in the
  same flush.

### LOW

**E11 — Recap loop wiring: diff-at-load wins** · SKILL-commands.md:818-826, SKILL-scripts.md:210-218
- Before: snapshot/diff documented but wired into neither load nor end; load-vs-end
  timing contradiction; duplicate `/dm:dnd recap` semantics (:685 vs :818).
- After: load step 6.5 runs `session_recap.py diff` (first-ever load: `snapshot`) and
  injects the output as the mechanical half of the recap; :822-826 rewritten;
  snapshot-at-end deleted. Dissolves ARCHITECTURE §7.3 and §7.4 in one move.

**E12 — autosave_checkpoint.py docstring promises a tail check the code never performs** · autosave_checkpoint.py:10,166-176
- After: cut the docstring sentence (comment-only edit); SKILL-scripts.md autosave
  section gains the missing recovery line (autocheckpoint.md → copy back over state.md).

**E13 — tracker.html keeps refreshing a dead combat** · SKILL-commands.md:663
- After: combat-end re-runs `render_tracker.py` with a "combat ended" marker (or clears
  tracker.html).

**E14 — `supersede-edge` intended but undocumented** · campaign_graph.py:236-245, SKILL-commands.md:758-759
- After: doc block after close-edge carrying the close-vs-supersede distinction
  (ended-truth vs never-was-truth). Closes ARCHITECTURE §7.5.

**E15 — A pending level-up marker can strand across sessions** · SKILL-commands.md:357-361,98
- After: load step 5 one-liner — surface any `⚠ LEVEL UP PENDING` marker and run
  `/dm:dnd level up` before play begins.

---

## Session A/B carried items (fixed in the same wave)

- **A-1** `tracker.py effect-start` wrong syntax (SKILL.md:44) → `tracker.py -c <camp>
  effect start <actor> <name> <dur>`. [ARCHITECTURE §7.2]
- **A-2** paths.py "is not a CLI" contradiction (SKILL-commands.md:512) → correct to the
  real CLI. [§7.1]
- **A-3/A-4** recap wiring + duplicate `/dm:dnd recap` → resolved by E11. [§7.3-7.4]
- **A-5** supersede-edge undocumented → resolved by E14. [§7.5]
- **B-1** `/dm:dnd new <name> [theme]` arg actually pre-fills Tone
  (SKILL-commands.md:9,32) → renamed `[tone]` (**owner decision**).
- **B-2** `## World State → Faction states` vs `Live State Flags → Faction stances`
  two-letter conflation trap (templates/state.md:14) → World State line renamed
  **"Faction activity"** (**owner decision**).
- **B-3** XP mentions in live prose (SKILL.md:183-184 tier rows, :301 per-turn persist)
  contradict milestone-only (SKILL.md:309, SKILL-commands.md:665) → reworded.
- **B-4** premise vs theme template definitions nearly identical (world.md:9 vs
  state.md:63) → phrasing diverges harder ("the ground situation" vs "not what happens
  but what it means").
- **B-5** Deeds format `<beat id>` (templates/state.md:29) vs `<beat id or session
  number>` (SKILL-commands.md:384) → template aligned to the fuller form.

## What already works (do not regress)

Premise variance, tone lock + saturation, spoiler discipline, the schema hard gate
(D1); rote-tell guards, specifics-over-abstraction, the calibration loop, the
pre-emption *design* (D2); schema status-coherence, the autosave hook engineering,
lazy-load layering, code/data root separation, close-vs-supersede semantics, tail
write-side (D3). Full lists at the bottom of each findings file.

## Follow-up backlog (post-wave)

- **C10 re-probe:** end-to-end prep probe on the current flow (premise scaffold →
  reconcile → bible), auditing party-binding (C1), plus one full `beat complete` with
  the E4 round-trip, a simulated mid-combat compaction (E3), and a session-count bump
  check (E1).
- Legacy trio (`new`/`import`/xp) vs flagship `prep` — keep, gate, or fold (owner).
- Session boundary is prose-defined post-E1 — should a small script own the counter?
- Spine `threats` party-size-aware encounter *budget* (C5 shipped counts only).
- Model-id pins in SKILL.md:181-186 → "latest sonnet/opus" policy wording.

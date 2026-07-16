# Prep Phase — Post-Fix-Wave Re-Probe (C10, 2026-07-16)

Manual probe of the authored-campaign flow **after the Session F fix wave** (commit
`bf34fd2`), per the C10 backlog item: end-to-end prep on the *current* flow (premise
scaffold → reconcile → bible), party-binding audit, one full `beat complete` with the
mirror-check + write-back round-trip, a simulated mid-combat compaction, and a
session-count bump check. Run in a sandboxed data root (`DND_CAMPAIGN_ROOT` override) —
live campaign data untouched. All fixes below verified by the suite: **263 tests green**
(was 257).

## Probe campaign

`/dm:dnd prep` driven manually as the DM-model would execute it, **no premise supplied**
(scaffold-rolled), with **2 imported level-3 party sheets** — deliberately not the L1
default, to exercise the new `party` block end to end. One PC with a Character Pillar
(Mara Venn — Bond: missing sister), one with it skipped (Theo Quill — bound via
scrivener background per step 0.7's fallback).

- `premise.py --seed 42` → tone **swashbuckling**; axes: tidal-island monastery /
  unprovable succession / cartel profiting from deadlock / employer on wrong side. All
  four reconciled into "Brinecliff charters" premise — the scaffold genuinely prevented
  the frontier-town default (the 07-14 probe's mining-town premise was exactly that).
- World layer + **step 1.5 NPC layer**: 4 full `npcs-full.md` entries + index, all
  name-registry-checked (exit 0; registry file created in the sandbox root, not live).
- **Step 0.7 party binding**: `world.md → ## Party Hooks` populated (one line per PC);
  per-PC quest seeds (Seed 3 Mara, Seed 4 Theo); spine secrets carry Mara's thread at
  beats 2 and 5; Theo's document-craft carries beat 4.
- Spine: 6 beats, acts 2/2/2, `party: {size: 2, start_level: 3}`,
  `level_up_to` = [4,5,6,null,7,8]; during-levels [3,4,5,6,6,7]; every threat picked
  from `bestiary.py --level <during-level>` output; counts via `Nx ` prefixes
  (`"3x Bandit"`); encounter shapes sized to a duo (screen-fight, banded pair,
  near-ceiling solo, social, pair+support, solo dragon). `schema.py` → **VALID first try**.
- Negative gates verified: party block removed → INVALID (`party block required`);
  drift injected into the state.md mirror → `mirror_check.py` MISMATCH exit 1.

## Bugs found and fixed by this probe (5)

1. **Fresh prep failed its own mirror check** — prep step 2 authored spine.json
   all-`pending` while step 6 seeded the mirror with beat 1 `current`/`current_beat: 1`
   → `beat complete` step 0 tripped MISMATCH on every freshly-prepped campaign. The two
   prep steps contradicted each other; nobody reconciled them when mirror_check landed
   in the F wave. **Fix:** the spine carries the playhead from prep — beat 1 authored
   `status: current` (SKILL-commands.md prep step 2, templates/spine.md status row +
   worked example, new `test_example_carries_the_playhead`).
2. **`milestone.py` crashed on milestone-fork sheets** — the pending-marker anchored
   ONLY on a numeric `**XP:** N / N` line, but the fork's own template ships XP blank
   and the fork forbids writing XP; `beat complete` step 3 exited 1 on any XP-less
   sheet, and `--clear` silently "succeeded" on them. **Fix:** fall back to the
   `**Level:** N` line (numeric XP still wins for legacy sheets); 6 new tests.
3. **`combat.py` crashed on Windows consoles** — cp1252 stdout cannot encode the
   tracker's `►` active-row marker → `UnicodeEncodeError` at `combat init`, mid-fight
   critical path. **Fix:** utf-8 stdio reconfigure guard (same pattern premise.py
   already used). ~20 other scripts print non-cp1252 chars — swept to backlog (below).
4. **`tracker.py` error paths exited 0** — bad duration / missing args printed
   `error:` and returned success. **Fix:** `SystemExit(1)` on all four error branches.
5. **Two F-wave wordings were wrong** (introduced by the wave itself, caught running
   them verbatim): SKILL.md's weapon-mastery line said `effect start <actor> <property>
   <rounds>` — a bare number is rejected (real format `1r/10r/60m/8h/indef`); and the
   new mid-combat ladder stop said `tracker.py list` — no such subcommand (real:
   `status`). Both corrected (SKILL.md + ARCHITECTURE.md mirrors).

## Round-trips verified clean (after fixes)

- **`beat complete` (beat 1 → 2):** mirror check OK → spine status flip → mirror sync
  (`current_beat`, statuses, `outstanding_beats`) → `steering_notes` regenerated with
  the beat-2 payload (situation sentence, threats verbatim, **secret on the last line**
  — the E5 `arc status` omission stays a one-line drop) → milestone stamp `⚠ LEVEL UP
  PENDING (Level 4)` on both XP-less sheets → level-up applied → markers cleared →
  `schema.py` VALID on the mid-play spine (status-coherence gate) → mirror check OK.
- **Session-count bump (E1):** first save since load bumped header 0→1 + `## Session 1`
  log entry; the "later saves in the same sitting do not bump" rule reads unambiguously
  at the moment of execution.
- **Mid-combat compaction (E3):** `combat init` (post-fix) → STATE_JSON to `## Active
  Combat` → round-3 write-back per the new per-turn d2 step → **recovery from durable
  sources only** reproduced round number, turn order, live HP (`Bandit Captain 42/65
  frightened`, `Mara 19/28`) from the state.md block + `tracker.py status`. The ladder's
  mid-combat stop works as written (post-`status` fix). Combat end: block cleared,
  `tracker clear --all`, tracker.html cleared (E13's alternative path — render_tracker
  has no "ended" flag; the prose's either/or is honest).
- **Difficulty wiring:** `standard` guidance applied at authoring (mixed picks across
  the band, one near-ceiling solo) — the arg now observably shapes the spine.

## Party-binding audit (the C1 acceptance check)

- `## Party Hooks` non-empty, one line per PC, each naming the world element that
  carries it — the "empty = defect" tripwire is auditable exactly as intended.
- `party.size: 2` visibly shaped encounters (no 6-mob fights; parley/sneak outs written
  into situations) and quest seeds (infiltration/leverage shapes, per C2's rationale).
- `start_level: 3` drove bestiary calls and the `level_up_to` chain; the schema rejects
  the old L1-hardcode failure by construction (`level_up_to 2/3` would fail
  "must exceed party.start_level").
- Gear per class: Cloak of Protection (either PC), the abbot's cutlass → +1 Longsword
  (fighter), instruments/keys (plot). No greatsword-to-casters failure mode.
- Pillar-blank fallback exercised: Theo bound via background, no pillar invented.

## Residual gaps (logged, not fixed)

- **Declared `start_level` is not cross-checked against the sheets** — a spine claiming
  `start_level: 1` over L3 sheets validates green; schema has no sheet access. Prose
  step 0.7 owns the truth. Candidate: `--sheets-dir` cross-check flag on schema.py, or
  fold into mirror_check. (Same prose-discipline class as the session counter.)
- **Windows cp1252 stdout sweep** — ~20 scripts print chars cp1252 can't encode
  (`⚠ → ✓ ►`); only combat.py (confirmed crash) was fixed. Adopt premise.py's
  reconfigure pattern repo-wide. → compass fragile-links.
- **Beats 4–6 anchor to named locations (conclave grounds, the hulk, the Tide-Vault)
  that are not Adventure Nodes** — C7's rule ("at or adjacent to a node or named
  world.md location") is satisfied on the letter, but the Tide-Vault exists only in a
  node's Connections line. Prep guidance could ask that act-3 ground get at least a
  named world.md mention beyond a connection. LOW.

## Verdict

The F-wave surface holds under an end-to-end run: prep now binds to the party it's
given, the authored path's table-time machinery (mirror check, hot beat payload,
milestone stamps, session counter, combat write-back) round-trips cleanly, and the
validation gates catch the failure modes they were built for. The probe caught five
real defects — three shipped (two of them F-wave-introduced wordings, one pre-existing
milestone/XP dependency), one crash environmental (Windows console), one exit-code bug
— all fixed and test-covered in this pass. 263 tests green.

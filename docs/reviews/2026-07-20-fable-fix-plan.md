# Fix plan — implementing the 2026-07-20 Pass A / Pass B findings

Written 2026-07-20, for execution in a fresh session. Source findings:

- `docs/reviews/2026-07-20-fable-pass-a-findings.md` — diff review of
  `7e2cb23..01d5179`: concrete defects, cited by question number below (Q1, Q4a…).
- `docs/reviews/2026-07-20-fable-pass-b-findings.md` — whole-skill enforceability
  audit: cited by item id below (A4, M2, M15…).

Read both before starting. The findings are the source of truth; this plan is the
execution order. The host has approved every phase in this document, including
Phase 8 (held last because it needs a play-test to validate).

## Global constraints — binding for every phase

1. **Protected, do not touch:** the roll-order rule (SKILL.md:318, "The roll request
   ends the turn") and the voice/prose rules (register, tone-follows-the-scene,
   length-follows-heat). Nothing in this plan requires editing them.
2. **No word-list extensions to improve detector recall.** Settled by measurement
   (6/6 false positives on permitted phrasings — see the removal comment at
   turn_lint.py:94-105). Detector work in this plan is *precision*-restoring or
   *structural*; where a trigger is broadened (Phase 3, `_ROLL_REQUEST`), it is a
   deterministic format trigger, and every change must be probe-tested against
   permitted narration before it lands.
3. **Probe-first methodology for all detector changes** (Pass A finding 4c): execute
   the changed regex against freshly invented permitted narration AND freshly
   invented violations — do not trust the existing fixture suite, which pins
   history, not the property. New probes become tests. Name tests for what they
   assert, not the property they gesture at.
4. **Never touch `~/.claude/dnd/campaigns/`** — live player data. Tests use temp
   dirs (existing tests show the `DND_CAMPAIGN_ROOT` pattern).
5. Windows: `python`, not `python3`, for anything run in this session. (The
   `python3` strings inside the model-facing SKILL files are fine — settled context,
   they run through the Bash tool.)
6. Tests: `python -m unittest discover -s tests -q` — 441 passing at plan time.
   Run after every phase; never leave a phase with a red suite.
7. TDD, vertical slices: one failing test → minimal change → green → next.
8. One commit per phase, conventional-commit style matching the repo log.
9. Live install is a symlink into this working tree; edits go live at the next
   session start. No `/plugin update dm`.

## Phase 1 — remove the ghost safety net from the docs

**Why:** Pass A Q1.1/Q4a. Three model-facing sites still promise the removed
cadence-block backstop; the DM is told a safety net exists that doesn't, which
undercuts the in-turn micro-save habit that now carries all continuity.

**What:** Fix the stale text at:
- `SKILL.md:262` — drop/replace the "it will also prompt this flush on a turn
  cadence as a backstop" sentence; the scene-boundary habit is the only mechanism.
- `SKILL-scripts.md:360` — remove the "emits a Stop-hook `block` decision" sentence;
  correct the `DND_AUTOSAVE_EVERY` description (it now only sets the telemetry
  counter period). While here, trim the dev-history prose per Pass B M8 (the
  2026-07-20 lint-false-positive story belongs in review docs, not the hot file).
- `SKILL-commands.md:1018` — the hook "snapshots state.md every turn" only; no
  prompting.

**Acceptance:** `grep -n "prompt" `on the three files shows no claim that the hook
prompts anything; existing prose guard tests still green.

## Phase 2 — autosave hook: claim race + `--status` counter fix

**Why:** Pass A Q4a. (a) A dev session's Stop event can claim the campaign right
after `/dm:dnd load`, silently killing snapshot+lint for the play session. (b)
`--status` reads a campaign-keyed counter file while the hook writes a
session-keyed one — the counter's only consumer sees 0.

**What (autosave_checkpoint.py + tests):**
- Claim guard: before claiming, verify this session's transcript actually contains
  a `/dm:dnd load` of the active campaign (the transcript path arrives in the hook
  stdin; a user-message scan is deterministic). A session that never loaded the
  campaign must not claim it. Document the residual risk (a dev session that
  literally ran the load command) in the docstring.
- `--status`: read the counter the hook actually writes. Simplest correct shape:
  key the counter by campaign always (binding already guarantees one owning
  session), or have `--status` resolve the bound session id from the marker and
  read that file. Pick one, delete the other path.
- Strengthen `test_status_still_reports` to assert the *count round-trips through
  the hook path*, not just that a label prints (Pass A Q4c-1).

**Acceptance:** new tests — dev-session-cannot-claim, status-sees-hook-counter —
plus the existing binding suite green.

## Phase 3 — turn_lint: precision, coverage, and liveness

**Why:** Pass A Q4b/Q4c/Q2. The adherence log is the instrument every future
enforcement decision depends on; right now one category flags innocent narration
6/6, two detectors miss violations written in the skill's own house format, and a
dead lint is indistinguishable from a clean session.

**What (turn_lint.py, autosave_checkpoint.py, tests):**
1. `_TARGET_RESISTANCE`: remove the bare single-word arms (`guarded`, `wary`,
   `careful`, `sharp`, `suspicious`) — they are the removed category-2 defect with
   different words. Keep/convert only constructions predicated of the target
   ("on his/her/their guard", "no fool", "not easily fooled", "hard to
   read/fool/convince", "sharp-eyed"). Accept the recall loss and record it in the
   docstring, exactly as the category-2 removal comment does.
2. `_DIFFICULTY_PREDICATION`: exclude the literal-physical-sense probes — "feels
   rough" (texture), "looks steep" (terrain) must not fire. Options: drop
   `rough`/`steep` from the perception-verb arm, or require an infinitive/task
   complement. Probe-verify both directions.
3. `_OUTCOME_PREJUDGMENT`: the `isn't/wasn't going to <word>` arm fires on any
   negated future ("the storm isn't going to break"). Constrain it (e.g. require a
   success/work/win-class verb or a second-person/roll-adjacent subject) — verified
   by probes, not by intuition.
4. `_NEGATED_EASE`: the `doesn't just <verb>` arm fires on intensifiers ("the rain
   doesn't just fall — it hammers"). Same treatment.
5. `_ROLL_REQUEST` trigger: cover "I need a … check", "let's see a … check", and
   the bare "<Ability> (<Skill>) check" form — a miss here silences *both* halves
   of `roll_not_final`. Deterministic format trigger, not a hedge lexicon; still
   probe against permitted text ("that was a close check" must not match).
6. `check_pc_auto_roll`: detect the skill's own documented resolved-roll format.
   Ground truth: PC names from `<campaign>/characters/*.md` filenames/headers — a
   resolved d20 line attributed to a PC name is a violation; NPC lines pass. This
   replaces format-guessing with campaign data (Pass A: "the detector matches the
   session-1 shape only").
7. Liveness (Pass A Q2 conclusion): caller-owned heartbeat in
   `autosave_checkpoint.py` — after the `turn_lint` call returns (or raises),
   append a one-line health record (ts, session, invoked/raised, findings count)
   to a `.lint-health.jsonl` beside the lint log; `run_and_log` additionally
   writes a best-effort `lint_error` record into `.lint-log.jsonl` when its own
   body fails. No hook output, no exit-code changes — the never-break-a-turn
   constraint stands.
8. Tests: rename `test_permitted_attempt_narration_never_fires` to what it asserts
   (old-lexicon regression guard) and add a genuine permitted-narration probe
   suite from the Pass A probe list; make the apostrophe test assert the category.

**Acceptance:** all Pass A 4b probe strings added as tests and passing in the
correct direction; heartbeat present after a hook run; suite green.

## Phase 4 — faster, safer `/dm:dnd save`

**Why:** Pass A Q1.3/Q1.4. The save procedure hands the model two jobs a script
already (or trivially) does.

**What:**
- `SKILL-commands.md` save procedure: run `campaign_graph.py extract
  --deterministic` FIRST and present its proposals alongside; the model's hand
  scan covers only what the extractor missed. (The script exists and is already
  recommended at SKILL-commands.md:951 for exactly this moment.)
- New small script (or `session_recap.py`-style addition): session-log archival —
  keep the 2 newest `## Session N` entries in `session-log.md`, append older ones
  to `session-log-archive.md`. Model still writes the 3–5 continuity bullets; the
  file surgery is scripted. Wire it into the save procedure text.

**Acceptance:** archival script has temp-dir tests (entry counting, append-only,
idempotent on re-run); save procedure text references both scripts.

## Phase 5 — faster, sturdier `/dm:dnd load`

**Why:** Pass A Q1.7/Q1.8/Q1.9. The campaign list, the mtime sort, and the
active-marker write are deterministic; the marker is load-bearing for three
subsystems and currently hand-written by the model.

**What:**
- `paths.py` CLI: add `list-campaigns` (name, last-played mtime, session count —
  sorted, machine-readable) and `set-active <name> --skill-dir <path>` (writes
  `active-campaign.json` correctly, preserving the marker contract).
- Wire both into `SKILL-commands.md` load step 0 (picker options) and step 5
  (marker write), and into `/dm:dnd list`.

**Acceptance:** CLI tests for both subcommands; commands doc points to them; a
malformed-marker scenario is no longer reachable from the documented flow.

## Phase 6 — between-session audit checkers

**Why:** Pass B Cluster A — cheap, exact, zero per-turn cost; this is where Pass B
says the enforcement budget should go. Five checks, all post-hoc, all reading the
transcript and campaign files after a session.

**What:** one new script (suggested `session_audit.py`, reusing `turn_lint.py`'s
transcript parsing) with one check per finding:
- **Dice provenance** (B A4): every narrated roll line must trace to a
  `dice.py`/`combat.py` tool call in the same turn — the only mechanical
  no-fudge audit that exists.
- **No-XP** (B A3): flag any `xp.py award` call or XP-award block.
- **Micro-save liveness** (B A7): `state.md`/`session-tail.md` mtimes vs turn
  count while `autosave: on`.
- **State divergence** (B A8): the STATE_JSON passed to `render_tracker.py` vs the
  `## Active Combat` block written back.
- **Lint-log privacy** (B A5): any mid-session Read/Bash touching
  `.lint-log.jsonl`.

Output: a per-session report to stdout (and optionally a jsonl), reviewed by a
human between sessions. Not wired into any hook.

**Acceptance:** each check has fixture-transcript tests in both directions
(violation caught, clean session passes).

## Phase 7 — doc dedup, safe subset only

**Why:** Pass B M2, M3, M8, M9 — redundancy whose consolidation loses ~nothing;
every always-hot line is per-turn deliberation cost.

**What:**
- M2: pre-emption landing-path templates stay in `arc revise`
  (SKILL-commands.md:869-872) only; SKILL.md:300-303 and the `/end` flow get
  one-line pointers.
- M3: SKILL.md's Milestone Leveling section reduces to the per-turn-relevant core
  (no XP, ever + pointer); procedures already live in commands.
- M8: scripts/commands autosave copies trimmed to mechanism-only (partly done in
  Phase 1).
- M9: dedup the behind-the-screen clause between SKILL.md:143 and :311 (keep both
  rules, cut the restatement — these are near the protected dice-convention block;
  touch only the duplicated clause, nothing else).

**Explicitly out of scope:** M1 (auto-roll repetition — possible compaction armor),
M5/M6/M12 (placement may be load-bearing), M16/M17 — all flagged "decide with
care" in Pass B and not approved for this pass.

**Acceptance:** prose guard tests updated where anchors moved; no rule deleted,
only duplicate statements; suite green.

## Phase 8 — lazy-load SKILL-commands.md (LAST; needs a play-test)

**Why:** Pass B M15 — the single largest per-turn-cost item found: 1029 always-hot
lines for procedures that fire at most once per session. The skill already
lazy-loads all campaign data; its own biggest file is the exception.

**What:**
- Replace "load this file at `/dm:dnd load`" with: a compact command index
  (command → one-line purpose → section anchor) that IS loaded at session start,
  plus an instruction to Read the specific command's section on invocation.
- Exceptions that stay hot: whatever the per-turn loop genuinely needs
  (the save/micro-save contract summary; check what SKILL.md already carries).
- Design the section anchors so a targeted Read is cheap (stable `## /dm:dnd x`
  headers already exist).

**Validation gate:** after implementation, run a real play session and check the
lint/health logs and command behavior before calling it done. If a command
misfires from a stale context, the mitigation is a mandatory section-read step in
the index text — verify it held.

**Acceptance:** load procedure no longer instructs a full-file read; index exists;
a play session confirms commands still execute their full procedures.

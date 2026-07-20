# Pass A — diff review, 7e2cb23..01d5179

Date: 2026-07-20.

Scope: the nine commits in `7e2cb23..01d5179` (wave-1 prose patches, the log-only turn
lint, the hook-interpreter fix, session-2 prose patches, session binding, the 2024 SRD
dataset, and the three commits from today: `bd4fc69` autosave block removal, `2364869`
prose rules, `01d5179` roll lead-in detection). `b4afa1f` (the prompt file itself) is out
of scope. Diagnose-only: findings and reasoning, no patches. The roll-order rule
(currently `SKILL.md:318`; the prompt's `:306` anchor predates today's commits) and the
voice/prose rules are protected. The do-not-re-derive block is honored throughout — in
particular, nothing below proposes extending word lists to improve recall; several
findings run in the opposite direction.

Verification state: full suite run at review time — 441 tests, all passing. Every regex
claim below was confirmed by executing the detector against the quoted probe text, not by
reading the pattern.

---

## Question 1 — what else hands work back to the model?

The category, from the prompt: a hook, command, or procedure whose output is an
instruction rather than a result. The autosave cadence block was one instance; each
remaining instance is a model turn (or in-turn model work) spent on something Python
does in milliseconds. Ranked by cost.

**1.1 The removed instruction-emitter still exists in the documentation — three
model-facing orphans.** `bd4fc69` removed the block decision from the code but not from
the program (the SKILL files are the program):

- `SKILL-scripts.md:360` still says the hook "emits a Stop-hook `block` decision that
  prompts the DM to flush continuity before yielding" every N turns, and still documents
  `DND_AUTOSAVE_EVERY` as controlling that cadence. The env var now controls only the
  wrap point of a telemetry counter.
- `SKILL.md:262` still tells the DM the installed hook "will also prompt this flush on a
  turn cadence as a backstop — but do not wait for it."
- `SKILL-commands.md:1018` still says the hook "prompts a micro-save every N turns."

This is worse than a stale comment: the DM is told a safety net exists that does not.
The micro-save rule survives on the scene-boundary habit alone now, and the text
actively invites the DM to weight that habit against a backstop that will never fire.
(Also filed under Question 4a, since these are orphans of the `decide()` →
`count_turn()` change.)

**1.2 Load-time graph init (SKILL-commands.md:136-160).** The `scene-context` output
`# graph not initialized` triggers a mandatory mid-load model flow: legacy detection,
backup, model-generated seed proposals, an approval round, then the model batch-executes
`add-node`/`add-edge` calls one at a time. The proposal-generation step is
deterministic-shaped work — it reads the npcs.md index table, "Lives in / Based at"
fields, and world.md faction lists, which are exactly the structured sources a parser
handles. The repo already owns a deterministic extractor for the *hard* case
(`graph_extract_deterministic.py`, free-prose session logs at ~95% precision); nothing
scripted parses the *easy* case, the structured tables. One-time per campaign, but it is
the single largest load stall, and it sits between the player and the recap.

**1.3 The save-time relationship sweep (SKILL-commands.md:509-529).** The save procedure
instructs the model to "scan this session's narration for relationship shifts," draft
`add-edge` calls, and present the batch. Meanwhile `campaign_graph.py extract
--deterministic --apply` exists, and SKILL-commands.md:951 itself recommends it "for a
hands-off relationship sweep at `/dm:dnd save`." The save procedure never invokes it —
the model performs the scan by hand on every save. This is the cleanest instance of the
category in the repo: the script exists, is documented for this exact moment, and the
procedure routes the work to the model anyway. (A hybrid would still want the model for
what the extractor's ~50% recall misses; the point is the procedure doesn't even start
from the deterministic pass.)

**1.4 Session-log archival at save (SKILL-commands.md:533-541).** "Keep the 2 most
recent session entries, move older ones to `session-log-archive.md` (append, never
delete)" is deterministic file surgery the model performs with Edit calls on every save
once the campaign passes session 3. The 3–5 bullet continuity summary genuinely needs
the model; the cut-and-append does not.

**1.5 The continuity-archive compression check (SKILL-commands.md:544).** "Drop a
relational bullet **only when its edge is confirmed present**" — a per-bullet graph
membership test the model is instructed to perform mentally against the just-approved
sweep batch. A membership lookup against `graph.json` is a script's job; the model's
judgment is only needed for the keep/drop call on mixed bullets.

**1.6 `/dm:dnd end` tail verification (SKILL-commands.md:581).** "Confirm the
campaign-side `session_tail.json` was written at save (non-empty, valid JSON list)" —
the model is instructed to perform a file validation. Only the repair branch (rewriting
the tail from session context) needs the model.

**1.7 `/dm:dnd list` (SKILL-commands.md:629-630).** The model reads every campaign's
`state.md` and formats a table of three header fields. Fully deterministic, and every
invocation costs N file reads in context.

**1.8 Load step 0 campaign picker (SKILL-commands.md:76).** `ls` plus an mtime sort,
performed by the model, to build the AskUserQuestion option list. `paths.py` is already
a CLI; a `list-campaigns` subcommand shape of work.

**1.9 Load step 5 marker write (SKILL-commands.md:109).** The model hand-writes
`active-campaign.json`. Small — but this file is load-bearing for three subsystems
(session binding, turn lint, snapshot), and `claim_session()` silently gives up on a
parse error (autosave_checkpoint.py:95-100), so a malformed hand-write disables all
three with no symptom. The most fragile writer in the stack produces the file the
deterministic layer depends on.

**1.10 `beat complete` step 2 payload copy (SKILL-commands.md:445-452).** The beat's
`threats` list and `secret` are copied verbatim from `spine.json` into the state.md
mirror by the model. `mirror_check.py` exists precisely because this hand-copy drifts —
the gate catches at step 0 the drift that step 2's hand-copy creates. The verbatim
halves are scriptable; only the one-sentence situation summary is model work.

**Calibration — the pattern done right, for contrast:** `session_recap.py diff` (the
commit message class of "recaps are the #1 thing an LLM hallucinates, so compute the
change set"), `oracle.py`, `dice.py`/`combat.py`/`tracker.py`/`grid.py`, and the three
renderers all put the work in the script and hand the model a result. The sites above
are the residue where the flow is still inverted.

---

## Question 2 — should `turn_lint`'s blanket `except Exception: return 0` distinguish crash from clean?

**The current shape.** `run_and_log` wraps its entire body in `except Exception:
return 0` (turn_lint.py:487-488). The caller wraps the import *and* the call in a second
blanket (autosave_checkpoint.py:259-263). Every failure mode — import error, campaign
resolution failure, transcript parse crash, log-write failure — is indistinguishable
from a clean turn. The lint's only output is the findings log, and an absent or
silent log means both "no violations" and "never ran." That ambiguity already cost a
full session of false confidence (the 0.00 violations/turn reading while the hook was
dead — session-2 findings doc), and the constraint that created it is legitimate: the
lint must never break a turn.

**Assessment of the options the prompt names:**

- **A distinct exit path** conflicts with the constraint that motivated the blanket.
  Stop hooks are not a neutral channel: a nonzero exit is at minimum surfaced, and
  specific codes carry harness semantics. Any "crash exits differently" design re-opens
  the possibility of a lint failure touching play, which is the one hard prohibition.
  Also, an exit code reports to the harness, not to the reviewer — the between-sessions
  reader of the log would still see nothing. Wrong instrument for the audience.

- **A liveness marker written on success** fits the constraint structure. The core
  defect is that *silence is ambiguous*; a success-side artifact (a per-session
  heartbeat — e.g. a counter or timestamp recording "linted turn N, 0 findings")
  converts silence into evidence. The between-sessions reviewer checks the heartbeat
  before trusting the zero. It costs one small write on the path that already writes
  findings, and it cannot affect play because it produces no hook output.

- **Something else worth naming: the two blankets fail differently, and the marker must
  live in the right one.** `run_and_log` never raises by contract, so the caller's
  blanket only ever catches *import* failure — which is exactly the observed 2026-07-20
  failure class (interpreter/path regressions). A liveness marker written inside
  `run_and_log` would not cover the import-death case; a marker owned by the caller
  (`autosave_checkpoint`, recording "lint invoked and returned" vs "lint import/call
  raised") covers both layers. Additionally, `run_and_log` could write a `lint_error`
  record into the same `.lint-log.jsonl` when its own body fails — best-effort, inside
  the blanket — so a mid-body crash is distinguishable from clean in the same file the
  reviewer already reads.

Conclusion: the blanket catch is correct and should stay; the fix-shape that respects
both constraints is success-side liveness evidence (caller-owned, plus best-effort
in-log error records), not a distinct exit path. This is the same design conclusion as
the A7 finding in Pass B (staleness checks are deterministic even when content checks
are not), applied to the lint itself.

---

## Question 3 — is the PC knowledge-boundary rule's "two tests" checkable by the model mid-turn?

Plainly: **test 1 is not realistically enforceable in-turn. Test 2 is partially
checkable early in a session and unenforceable after compaction — which is the case the
rule exists for.**

**Test 1 — "does the character know it?"** The ground truth is the set of things this PC
has witnessed on-screen or been told out loud across the whole campaign. No artifact
stores that set. The campaign graph's `knows_about` edges and the save-sweep's
"character learned a secret" pattern are a partial substrate, but the live add-edge
discipline deliberately restricts itself to relationships explicitly narrated on-screen
in the current scene — the recorded set is a sparse, correct-direction sample of the
real one, not the ledger the test needs. The audit surface for one proper noun is the
full transcript and log history; a per-noun mid-turn traversal of that is not a bounded
check. What the model actually does is check the noun against its *impression* of the
history, and the impression — a lossy summary of summaries, as SKILL.md:248 itself
says — is precisely where leaks come from. In-turn, this test is aspirational. Post-hoc,
a first-occurrence scan can queue candidates for a human reviewer, which is the grade of
enforcement actually available.

**Test 2 — "can the player follow it?"** This one has a genuinely checkable core: "has
this name appeared in narration before?" is a question the model can answer from its own
context early in a session, and the required action (one appositive clause on first use)
is an own-output check. The hole is durability: first-mention state lives nowhere but
context. After a compaction the model cannot distinguish "the player has seen this name"
from "my summary mentions this name" — and long sessions, the ones that compact, are
where unglossed-noun pileups happen (the Thornwake failure that motivated the rule was a
session-1 pileup; the compaction case is strictly worse). No file tracks player-facing
first mentions — `name_registry.py` tracks cross-campaign name *uniqueness*, a different
question. So: checkable while context holds, unenforceable exactly when the risk peaks.

Neither test should be counted as enforced. The rule still earns its place as
instruction — the four failure examples do real disambiguation work, and that is the
mechanism this rule actually runs on — but its enforcement story is post-hoc review, not
mid-turn verification.

---

## Question 4 — correctness of the three commits from today

### 4a. Orphans of the `decide()` → `count_turn()` change (bd4fc69)

**Three model-facing documentation orphans** — SKILL-scripts.md:360, SKILL.md:262,
SKILL-commands.md:1018 — detailed under finding 1.1. All three still describe the
removed block/prompt behavior; two of them promise the DM a backstop that no longer
exists, and one documents `DND_AUTOSAVE_EVERY` as a cadence control when it now only
wraps a telemetry counter.

**The surviving counter's only consumer cannot see it.** The commit message says
`decide()` becomes `count_turn()`, "a pure counter feeding --status." In hook mode the
counter file is keyed by session id (`_counter_path(stdin_obj.get("session_id"),
campaign)`, autosave_checkpoint.py:275); in `--status` mode stdin is deliberately not
read (`stdin_obj = {} if (args.campaign or args.status)`, line 233), so the path is
keyed by campaign name. Hook writes `autosave-counter-<session>.json`; `--status` reads
`autosave-counter-<campaign>.json`. Whenever the harness supplies a session id — the
normal case — `--status` reports 0 or a stale value from a file the hook never touches.
The one purpose the counter was kept for is broken in the common path.
`test_status_still_reports` (test_autosave_no_block.py:70) passes because it only
asserts the label prints, and because the test drives the hook via `--campaign`, the
one path where the two keys coincide. Cosmetic corollary: the `--status` label is still
`turns_since_checkpoint`, and there is no checkpoint.

**A design gap in the adjacent session-binding commit (3e91e1d, in range): the claim
race.** The binding contract is "the first Stop hook to run after a load claims the
campaign." A concurrently open dev session emits Stop events too. If the dev session's
Stop lands between `/dm:dnd load` (which strips the session id) and the play session's
first turn-end, the *dev* session claims the campaign, and the play session no-ops
silently — no snapshot, no lint — until the next `/dm:dnd load` rewrites the marker.
Every no-op in this design is deliberately quiet, so the failure is invisible; the
scenario (dev session and play session open simultaneously) is exactly the one that
motivated the binding. `test_session_binding.py` covers ordering-correct cases only.
Same family: `claim_session` returns silently on a marker parse error
(autosave_checkpoint.py:95-100), leaving the campaign unbound so every session is
admitted — multiple sessions can then interleave writes into one lint log.

### 4b. Regex behaviour of the four `_ODDS_HEDGE_CATEGORIES` (01d5179)

All claims below were verified by running the detector; every probe sits inside the
lead-in window (final two sentences before the request), so the window bound does not
save any of them.

**The fourth category is a bare lexicon — the same defect class the second category was
removed for, with different words.** `_TARGET_RESISTANCE` (turn_lint.py:135-140)
matches `\bguarded\b`, `\bwary\b`, `\bcareful\b`, `\bsharp\b`, `\bsuspicious\b` with no
grammatical-role filter. The removal comment for category 2 (turn_lint.py:94-105)
records the settled measurement: bare difficulty vocabulary fired on 6 of 6 permitted
phrasings because permitted and forbidden narration share words, and the fix was
predication structure. Category 4 reintroduces exactly that shape one screen further
down. Probed against permitted narration, it fired on 6 of 6:

- *"You pick your way along the ledge, careful of the loose stones."* — the PC's own
  care, not the target's resistance → fires (`careful`).
- *"You keep a wary eye on the door while you work."* — PC action → fires (`wary`).
- *"A sharp crack comes from the rafters above you."* — a noise → fires (`sharp`).
- *"The blade is sharp and freshly oiled."* — an object property → fires (`sharp`).
- *"Two men stand at the guarded gate ahead."* — a literally guarded place, legal scene
  description → fires (`guarded`).
- *"You slip the suspicious package under your coat."* — an object → fires
  (`suspicious`).

To be explicit about the do-not-re-derive boundary: this is a **precision** finding, not
a recall proposal. It is the settled fact ("lexical detection of this rule does not
work") reasserting itself inside the commit that documented it. The six permanent
permitted-phrasing tests pin only the *old* lexicon's vocabulary (hard / easy / simple /
chance), so all of the above passes the suite green.

**The other three categories have narrower versions of the same precision gap**, each
verified:

- `_DIFFICULTY_PREDICATION`'s perception-verb pattern includes adjectives with literal
  physical senses: *"The rope feels rough against your palms"* and *"The trail looks
  steep past the treeline"* both fire, and both are texture/terrain description, not
  difficulty rating.
- `_OUTCOME_PREJUDGMENT`'s `isn't/wasn't going to <word>` arm fires on any negated
  future: *"The storm isn't going to break before nightfall"*, *"He wasn't going to
  wait forever, and you both knew it."*
- `_NEGATED_EASE`'s `doesn't just <word>` arm fires on plain intensifiers: *"The rain
  doesn't just fall here — it hammers."*

Impact calibration: the lint is log-only, so each false positive costs a log line — but
the log's declared purpose is to measure adherence and detector precision *before any
blocking is enabled* (turn_lint.py:6-9). A category with this false-positive surface
inflates measured violation rates and trains the between-sessions reviewer to discount
the detector, which is the exact failure the category-2 removal comment warns about.

**A recall gap in the shared trigger, distinct from the accepted semantic one.** The
docstring honestly scopes the hedge categories' recall ("the signal is semantic").
Separately, though, `_ROLL_REQUEST` (turn_lint.py:66-70) only matches requests
introduced by *roll*, *make*, or *give me*. Probed: *"I need a Charisma (Persuasion)
check from you"*, *"Let's see a Dexterity (Sleight of Hand) check"*, and a bare
*"Charisma (Persuasion) check, whenever you're ready"* — none match, and when the
trigger misses, **both halves** of `roll_not_final` go silent for the turn, including
the deterministic trailing-narration check. This is a gap in the deterministic trigger,
not in hedge semantics — fixing it is not "extending word lists to improve detector
recall" in the settled sense, but it is recorded here as a finding, not a proposal.
Related, minor: only the *last* request in a turn is inspected (`finditer` keeps the
final match), so a hedged earlier request in a two-request turn escapes.

**`pc_auto_roll` misses the skill's own documented roll format.** (Detector shipped in
`fefd249`, in range.) `_RESOLVED_ROLL_LINE` requires a bold `**Roll:**` prefix and an
arrow. SKILL.md:321's canonical inline format is `Piper — Perception: d20+5 = 18` — no
bold prefix, `=` not an arrow. Probed: that exact shape, and an unbolded
`Roll: Wisdom (Insight), d20+1 -> 14`, both produce zero findings under
`roll_mode: players`. The detector matches the one formatting shape observed in the
session-1 violation; a DM violating the rule in the house style the skill itself
teaches is invisible to it.

### 4c. Tests asserting something weaker than their names claim

The prompt's prior — one already found, assume more — holds. Found:

1. **`test_status_still_reports`** (test_autosave_no_block.py:70) — the name promises
   `--status` still reports; the body asserts only that the string `active_campaign`
   appears in stdout. It does not check the turn count, and it drives the script via
   `--campaign`, the one path where the hook's counter key and `--status`'s counter key
   coincide — so it passes while `--status` reads the wrong counter file in the real
   hook path (finding 4a).

2. **`test_permitted_attempt_narration_never_fires`** (test_turn_lint.py:199) — the name
   claims permitted attempt narration never fires; the body pins exactly the six
   phrasings that broke the *removed* lexicon. As 4b shows, permitted narration fires
   readily through the surviving categories ("careful of the loose stones", "the rope
   feels rough", "the storm isn't going to break"). The docstring scopes itself honestly
   to the old lexicon regression; the name asserts the general property. A reader
   trusting the name would conclude the false-positive problem is solved; it moved.

3. **`test_typographic_apostrophe_still_matches`** (test_turn_lint.py:181) — asserts
   `len(out) == 1` for both apostrophe forms but never which category (or which half of
   the detector) produced the finding. The fixture ("This isn't going to be easy")
   matches two categories today (negated-ease and outcome pre-judgment); the test would
   keep passing if the apostrophe fold silently broke for one of them. Low-risk, but the
   name claims fold-correctness that the assertion doesn't isolate.

4. Cosmetic: `test_session3_prose.py`'s `window()` helper uses a bare `assert` for its
   anchor check, which vanishes under `python -O` — a missing anchor would then surface
   as confusing empty-window assertion failures rather than the intended message.

Verified sound, for the record: the previously-flagged misnamed target-resistance test
is now correctly named and documented (`test_flags_attributive_difficulty_hard_man_to_like`
names the category that actually claims the string, and
`test_flags_target_resistance_on_its_own_category` genuinely fails if that regex is
deleted); the known-miss fixture (`test_known_miss_different_reasons_not_flagged`)
documents an accepted gap instead of overfitting to it; and `2364869`'s superset claim
checks out — all six deleted session-2 guards have session-3 equivalents (rule
existence, describe-don't-name default, both original failure examples, the
witnessed-or-told wording, the world-may-supply-knowledge allowance, and the placement
invariant).

---

## Summary of findings by severity

1. **Three model-facing doc orphans promise a removed backstop** (SKILL.md:262,
   SKILL-scripts.md:360, SKILL-commands.md:1018) — the DM is told a continuity safety
   net exists that doesn't. (Q1.1 / Q4a)
2. **`_TARGET_RESISTANCE` is a bare lexicon** — 6/6 verified false positives on
   permitted narration; the same defect class whose removal the file documents, guarded
   by tests that only pin the old lexicon's words. (Q4b)
3. **`--status` reads a counter the hook never writes** in the session-id path; the
   counter's sole surviving purpose is broken, and its guard test is too weak to see
   it. (Q4a / Q4c)
4. **The session-binding claim race** — a dev session's Stop can claim the campaign
   after a load, silently disabling snapshot and lint for the play session. (Q4a)
5. **`_ROLL_REQUEST`'s verb trigger silences both halves of `roll_not_final`** on
   common request phrasings; `pc_auto_roll` cannot see the skill's own documented roll
   format. (Q4b)
6. **Ten sites still hand deterministic work to the model** — the save-time
   relationship sweep (a script exists and is documented for exactly that moment),
   load-time graph init proposals, session-log archival, `/dm:dnd list`, the tail
   verification, the marker hand-write, and the beat-payload copy chief among them.
   (Q1)
7. **The lint's crash/clean ambiguity** should be resolved with caller-owned
   success-side liveness evidence plus best-effort in-log error records — not a
   distinct exit path, which conflicts with the never-break-a-turn constraint. (Q2)
8. **The knowledge-boundary rule's two tests**: test 1 is not enforceable in-turn
   (unbounded audit, no ledger exists); test 2 is checkable only until compaction,
   which is when it matters. Neither should be counted as enforced. (Q3)

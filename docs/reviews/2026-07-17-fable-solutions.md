# Fable Solutions Doc — Binding Mechanisms for DM-Behavior Rules — 2026-07-17

Second Fable pass (claude-fable-5), solution-focused, against the brief
`2026-07-17-dm-gap-analysis-and-fable-brief.md`. All citations fresh-verified against the live
tree at `49f4ae6` (v2.4.0). Answers §9 items 1–6 and the History lens H1–H3.

**TL;DR.** Every Tier-1/2 gap verifies (with corrections below). The enforcement ceiling is
real, but the archaeology reframes it: the roll gate used to be *structural* (the display-era
blocking dice flow) and was torn out with the display; the prose that remains was written
against a different failure mode than the one that fired. The highest-leverage move is not a
new architecture — it is (1) two cheap prose patches that close genuine rule-scope gaps,
(2) a turn-gate lint grafted onto the existing autosave Stop hook, run log-only first so it
doubles as the project's first continuous adherence-measurement instrument, and (3) deferring
the thin wrapper until that telemetry says detection isn't enough — noting honestly that the
wrapper is also the already-planned "bucket 2" terminal UI and the caveman firewall, so if it
gets built it should be justified by all three at once.

---

## 1. Gap verification (brief §4) — verdicts

| # | Brief claim | Verdict | Live evidence |
|---|---|---|---|
| T1-1 | Narration-vs-quote craft absent; only rule pushes toward verbatim | **CONFIRMED** | `SKILL.md:211` is purely a *formatting* rule (block + bold label). No rule anywhere maps information state (clear/muffled/secondhand) to narration mode. Transcript `session-1-transcript.md:132` renders an *eavesdrop through a door* as a full verbatim quote block — the exact failure. |
| T1-2 | No death/handoff protocol | **CONFIRMED** | Death saves are mechanics-only (`tracker.py:25-29`, `SKILL-scripts.md:168-181`). `SKILL.md:24` promises "death is possible"; nothing says what happens after 3 failures. Grep for death/dying across all three prose docs: zero campaign-level protocol. |
| T1-3 | No reusable asset library | **CONFIRMED** | `render_assets.py:25-26` is the 3-field parser (handle/desc/file), per-campaign only. Prep (`SKILL-commands.md:381-401`) generates fresh lists every campaign; no cross-campaign index, tags, or manifest exists anywhere under `scripts/` or `templates/`. |
| T2-4 | No DC-setting ladder | **CONFIRMED** | Hidden-DC (`SKILL.md:119`) and fail-forward (`SKILL.md:121`) exist; a search for any DC-number guidance returns nothing. The DM invents target numbers with no consistency anchor. |
| T2-5 | `npc_rename.py:94` session-tail bug | **CONFIRMED, recharacterized** | `npc_rename.py:94-96`: `_TEXT_FILES_ALWAYS` includes `session_tail.json`, omits `session-tail.md`. But the brief's framing "maintains a dead file" is wrong — see H2 below. The actionable bug stands: the file the load recap actually reads (`SKILL-commands.md:109`, `:164`; `SKILL.md:225`) keeps the stale name after a rename. |
| T2-6 | Dispositions deleted at baseline | **CONFIRMED** | `SKILL-commands.md:475`: "Remove NPCs who have returned to baseline." No residue of what the NPC remembers. |

**Corrections to the brief while verifying:**

- **Line drift:** the rote-closer ban is at `SKILL.md:210`, not `:189` (`:189` is now the Model
  Routing table). The brief's `:189` came from the vault entry for commit `d915dde`, where it
  was true at the time. `:104`, `:211`, `:290` still resolve correctly.
- **`session_tail.json` is not dead.** It is written at every save (`SKILL-commands.md:497`)
  and verified at `/dm:dnd end` (`SKILL-commands.md:572`). What it *lacks* is a reader: no
  script and no prose step reads it. Meanwhile `SKILL-commands.md:498` calls `session-tail.md`
  the "fallback if the JSON read fails" — backwards from reality, since the .md is the only one
  ever read. Doc contradiction to fix alongside the rename bug.
- **The transcript shows a third violation the brief missed.** `state.md → Session Flags` has
  `roll_mode: players`, yet transcript line 22 resolves Holg's Animal Handling inline
  (`d20+0 → 19`) with no player-supplied number anywhere in the file. That is the *original*
  hard constraint of `SKILL.md:290` — silent PC auto-roll — firing in addition to the
  narrate-before-roll ordering issue (line 20: "Holg's Animal Handling isn't going to win this
  on skill" *before* any die). Two distinct failure modes in one beat.

---

## 2. H1 — Rule archaeology (why the rules took their shape, and what that changes)

**Roll-before-narrate (`SKILL.md:290`).**
- Born 2026-06-04 (v2.1.1, "Enforced roll handling") against one specific bug: *the DM silently
  auto-rolling a PC when the physical-dice server was down.* The STOP language has always meant
  "stop after requesting, wait for the number" — it has **never contained a clause about what
  may be narrated before the request.** The playthrough's ordering failure (outcome/likelihood
  narrated pre-roll) is outside the rule's written scope. Part of the "enforcement ceiling" here
  is actually a **rule-scope gap**, which is much cheaper to fix than an adherence ceiling.
- Through v2.3.0 (commit `21969bd`, 06-28) the rule co-existed with a **structural gate**: the
  display's dice flow (`--wait` "blocks until the player rolls and then prints their result for
  you to resolve") and an autorun loop that explicitly would not proceed while "a dice roll is
  pending a player's response" (v2.3.0 `SKILL.md:270`). The teardown (`54244fb`, 07-15, 62 files
  / ~16k lines) removed the gate; `7ef85b5` reworded the prose terminal-native the same day.
  **The (B) wrapper's dice-gate is therefore a restoration, not an invention** — the project has
  already operated with hard roll enforcement and chose (reasonably) to trade it away for
  leanness, without re-deriving what enforcement remained.
- Live-tested in terminal-only form exactly once before 07-17: never. The 07-17 session was the
  acceptance test, and it failed both ways (auto-roll + pre-roll narration).

**Rote-closer ban (`SKILL.md:210`) and spoken-voice rule (`SKILL.md:104`).**
- Both born `d915dde` (07-15, voice overhaul), **written in reaction to a real playthrough that
  "read like a novel"** (vault, 07-15 session). So for the voice register, the sequence is:
  observed failure → strong rule → re-observed identical failure two days later with the rule
  loaded and caveman off (§8 replay). This is the strongest possible confirmation that the voice
  register is adherence-bound, not rule-scope-bound.
- The project *already knew* the guard tests don't bind behavior: `test_prep_skill_prose.py:112-160`
  asserts the rule **text exists in SKILL.md** — and the vault entry says so in plain words:
  "unit guards only prevent silent reversion. The true voice acceptance is a live read-through
  at the table." Shipped-and-assumed was a documented, accepted risk — not an oversight.
- Poetic detail worth keeping as the canonical worked example: `SKILL.md:104` names *tallow* as
  its exemplar trip-word to swap out; the playthrough's **opening line** is "Underwatch smells
  like tallow smoke" (`session-1-transcript.md:7`). The rule's own example word appeared,
  unmodified, in the first sentence of live play.

**NPC-block-always (`SKILL.md:211`).**
- `c58aa65` (07-15) formalized the deliberate flip from "brief interjections don't need a block"
  (vault, spec item E). Confirmed intentional; the fix for T1-1 must be a **new
  narration-mode rule layered above the formatting rule**, not a revert. The formatting rule is
  also a survivor of the teardown by design ("Approach B — keep block discipline as a prose
  convention… a deliberate **stopgap** until bucket 2" — vault, teardown decision). It was never
  meant to be the final word on dialogue rendering.

---

## 3. H2 — Teardown residue / orphans

Hunted the whole live tree (scripts + prose + config) for display-era wiring. The teardown was
unusually clean — the file-literal inventory across all scripts maps to live artifacts with
these exceptions:

1. **`npc_rename.py:94-96`** — the confirmed exemplar, recharacterized (§1): not dead-file
   maintenance but a **missing live file**. Fix is one line (add `"session-tail.md"` to
   `_TEXT_FILES_ALWAYS`) plus the doc fix at `SKILL-commands.md:498` (the .md is the primary,
   the JSON currently has no reader — either give the JSON a reader or demote it in prose).
2. **`skills/dnd/display/`** still exists as an empty shell containing only stale `__pycache__`
   (compiled remnants of deleted display modules). Delete the directory; also drop
   `.gitignore:13` (`**/display/session_tail.json`).
3. **`update_skill.py:29-31`** — not display residue but a sync question the brief asked about.
   **CORRECTION (wave-0 execution, same day):** the brief's "frozen copy" characterization was
   wrong — `~/.claude/plugins/cache/neural-initiative/dm/2.3.0/skills/dnd` is a **symlink to
   this repo's working tree** (created 07-14, the F1 fix), so fork edits reach live play at the
   next session start with no manual sync. The parent cache dir (CHANGELOG etc.) *is* a stale
   copy, which is what misled the diagnostic. Remaining real risks, now documented in
   `CLAUDE.md`: `/plugin update dm` would replace the cache dir and sever the symlink, and
   `update_skill.py`'s default VERSION check still points at upstream — treat its output as
   non-authoritative for this install.

No other orphans: `session_tail.json` writers/verifiers are prose-live (see §1 correction),
`tracker.html`/`map.html`/`assets.html` all have live render scripts, and no script or doc
references `send.py`, `check_input.py`, `autorun`, phone, or `_display_running` anymore.

---

## 4. H3 — Story-vs-code cross-check

- **CHANGELOG 2.4.0 teardown entry vs code: accurate**, including the claim that the session
  tail "survives as a continuity file written at save" — true, though the entry (like the brief)
  doesn't notice the JSON half lost its last reader.
- **Vault teardown rationale vs code: accurate and load-bearing.** Approach B's two explicit
  IOUs are both still open: (a) narration/NPC rendering as a "prose stopgap until bucket 2" —
  bucket 2 is unstarted, and issue #6 (leave the chat window) plus the (B) wrapper are the same
  work item wearing different hats; (b) hidden-DC became "just a narration-discipline rule"
  after the phone (which *displayed* the DC) died — i.e. hidden-DC also silently degraded from
  structural to prose in the teardown, same as the dice gate.
- **Drift found:** `SKILL-commands.md:498`'s fallback-direction claim (§3 above). Also the
  brief/vault cite `:189` for the closer ban (drifted to `:210`) — cosmetic, but worth noting
  that **all** file:line cites in review docs rot within days on this codebase; future briefs
  should cite rule *names* plus a quoted phrase, not line numbers.

---

## 5. Rule classification and binding mechanisms (§9 item 2 — the core)

### 5.1 Machine-detectable (regex/state against data that already exists)

All four detectors read the same two ground-truth sources: **the turn transcript** (Stop-hook
stdin JSON carries `transcript_path`; the last assistant message's text blocks are the
player-facing prose, its `tool_use` blocks are the dice calls) and **campaign state** (active
campaign via `<runtime-dir>/active-campaign.json` — the exact mechanism `autosave_checkpoint.py:70-79`
already uses — then `state.md → ## Session Flags` for `roll_mode`/`tutor_mode`, `ambient-list.md`
/ `map-list.md` for cue handles, `characters/*.md` for PC names).

| Detector | Signal scanned | Ground truth | Crispness |
|---|---|---|---|
| **Rote closer** (`SKILL.md:210`) | Final ~200 chars match `what (do\|will) you do`, `what's your (move\|play)`, etc. | none needed | Crisp — near-zero false positives; the rule's own allowed forms ("Fight, or find another way out?") don't match |
| **Hidden-DC leak** (`SKILL.md:119`) | `\bDC\s*\d+` in player-facing text | `tutor_mode` flag — tutor hints legitimately state the DC after a failed roll (`SKILL.md:359`), so exempt lines carrying `◈ Tutor:` | Crisp with the tutor exemption |
| **Roll-order / roll-final** (`SKILL.md:290` + new clause, §5.3) | Under `roll_mode: players`: a roll-request phrase (`(roll\|make\|give me)…(check\|save\|saving throw\|d20)`) followed by > ~40 words of narration in the same turn → violation ("the roll request must end the turn") | `roll_mode` from Session Flags | Crisp once the turn-shape clause exists in prose (§5.3) |
| **PC auto-roll** (`SKILL.md:290` original scope) | Under `players`: a `dice.py` d20 `tool_use` in a turn whose prose resolves a *named PC's* check/save (PC names from `characters/*.md`), excluding hidden-roll skills invoked with `--silent` (`SKILL.md:215`) | PC roster + tool calls | Heuristic — attribution needs the PC name near the roll line; expect occasional misses, near-zero false alarms |
| **Cue validity** (`SKILL.md:212-213`) | `🔊 **Cue:**` / `🗺 **Map:**` handle not in the campaign's list files | parse lists with `render_assets._ENTRY` (reuse `render_assets.py:25`) | Crisp |

**Mechanism: extend the existing Stop hook, don't add a new surface.** `autosave_checkpoint.py`
already implements the full pattern — stdin JSON parse (`:54`), active-campaign resolution
(`:70`), flag reading, the `block`-decision-with-reason emission, and the `stop_hook_active`
loop guard (`:21-22`, which naturally caps enforcement at **one redo per turn**). Add a
`turn_lint` module invoked from the same hook (one hook, one combined decision — avoids
two-hook reason-collision) and extend `install_autosave_hook.py` trivially. On violation the
reason reads e.g.: *"Turn lint: rote closer detected ('what do you do'). Rewrite the closing
steer per SKILL.md Narration principles, keep everything else, then end your turn."*

**Run it log-only first.** Before enabling `block`, have the lint append one JSON line per
violation to `<campaign>/.lint-log.jsonl`. Two effects: (1) it measures the real violation rate
per session — the **continuous performance signal the History lens correctly says this project
has never had**; every future "did the fix work?" question becomes answerable from data instead
of single-playthrough anecdotes; (2) it de-risks false-positive annoyance before any behavior
changes. Enable blocking per-detector once a detector shows precision in the log.

**The honest limit (detection ≠ prevention, made concrete):** in-chat, the flawed text has
already streamed to the player's screen before Stop fires; a redo means the player sees both
versions. For the closer and DC leak that's cosmetic double-render. For roll-order it still
*rescues the game* — the outcome hasn't been acted on, and a corrected turn re-establishes the
ask-roll-resolve rhythm. Invisible correction requires an output interceptor, which only the
wrapper provides (§6).

**Windows notes (task item 6):** follow the `combat.py:36-38` / `grid.py:57-58` house pattern —
`stream.reconfigure(encoding="utf-8")` guarded by `hasattr` — in any script that prints; the
lint reason strings contain no emoji (the cue *detector* reads emoji from the transcript file,
which is read as UTF-8 with `errors="replace"` like `autosave_checkpoint.py:90`); hook JSON
output uses `json.dumps(..., ensure_ascii=True)`. The installer already writes
`python3 "<abs path>"` (`install_autosave_hook.py:34-37`) — verify once via `--status` plus a
manual echo-hook that the Stop hook actually fires on this machine before trusting it (the
autosave hook is opt-in and may never have been installed here; that check is step 0 of the
lint work, not an afterthought).

### 5.2 Judgment-only (no reliable signature — prose + examples are the ceiling, in-skill)

- **Narration voice/register (`SKILL.md:104`).** "Too literary" has no regex. Proxy signals
  exist (mean sentence length, em-dash density, `like a`-simile counts — and the transcript
  would have tripped all three) but they are **advisory-grade only**; wire them into the
  log-only lint as a drift *thermometer* if desired, never as a blocking gate (false positives
  on legitimate Breathe-tier scenes are certain). The in-skill ceiling: add two compact
  worked BAD→GOOD passages to `SKILL.md:104` (one from the actual transcript — the "tallow
  smoke" opener rewritten spoken; one combat beat), because a model matches examples more
  reliably than adjectives. Expectations honest: this is the same class of fix that already
  failed once; treat it as marginal-improvement, and let the log-only thermometer measure
  whether it moved anything.
- **Quote-vs-summarize (T1-1).** Judgment at run time, but the *rule itself is genuinely
  missing* — this is not an adherence problem yet. Add a *narration-mode ladder* to Narration
  principles, above the `:211` formatting rule: **clear + present** → direct quote block;
  **muffled / partial / distant** → narrator summary + at most one sparse verbatim fragment;
  **secondhand / reported** → narrator summary only, no quote block; and **never let narration
  assert an identification the source didn't contain** (the smuggled "Vigil" deduction —
  narration may present evidence, the player makes the inference). Use the transcript's
  eavesdrop scene (`session-1-transcript.md:124-132`) as the in-rule worked example: as played
  (full verbatim block through a door) vs as it should read (fragments inside summary).
- **DC value choice (T2-4).** Judgment, anchored by a ladder. Add the standard 5e ladder to the
  Dice convention (Very Easy 5 / Easy 10 / Moderate 13 / Hard 15 / Very Hard 20 / Nearly
  Impossible 25) plus one line — "when torn, 13; reserve 18+ for stakes the fiction has visibly
  earned" — and keep `SKILL.md:119` (never say the number). No enforcement; the hidden-DC
  detector already polices the leak side.
- **Phantom item/enemy (`SKILL.md:217`).** Out of combat, referencing ground truth requires
  entity extraction — judgment; skip (over-engineering). *In combat* the enemy-roster half is
  machine-checkable against the Active Combat STATE_JSON if wanted later; not first-wave.

### 5.3 Roll-before-narrate — the turn-reshape (prose patch that makes the detector crisp)

Patch `SKILL.md:290` (2 sentences, not a rewrite): under `roll_mode: players`, when a check is
called, **the roll request is the final content of the turn** — nothing after it; before it,
you may describe the *attempt* (what the PC is physically doing) but **never the outcome, the
odds, or how hard it looks** ("isn't going to win this on skill" is the canonical violation —
cite the transcript). Resolution happens only in the *next* turn, after the player's number.
This closes the H1 scope gap, gives the detector a structural signature (request-must-be-final),
and costs nothing. The same clause under `roll_mode: auto` becomes: the roll line comes first
in the resolution, before any outcome prose.

---

## 6. Option (B) — thin Python turn-loop wrapper, assessed concretely (§9 item 3)

**What it is:** a small terminal client owning the player-facing I/O loop; Claude (same Pro
auth, via the Claude Agent SDK) still runs the whole existing skill unchanged.

**Chokepoints it mediates (exactly four, plus rendering):**
1. **Input gate** — player text enters through the wrapper; it stamps turn boundaries (kills
   the need for the autorun-style hacks the display era used).
2. **Dice gate** — the restoration of the torn-out `--wait` flow: when the model's output
   contains a roll-request marker (the `**Roll:**` convention already exists in live play —
   transcript lines 22/128 — it needs only to be specified in SKILL.md as *the* marker), the
   wrapper withholds any post-marker content, prompts the player for the number, and feeds it
   back as the next user message. Hard prevention: pre-roll outcome text physically cannot
   reach the screen.
3. **Redaction pass** — strip `DC \d+` (and any future DM-only annotations) from the rendered
   stream while logging them to a DM-side file. Hidden-DC returns to structural, as it was
   pre-teardown.
4. **Reference validation** — cue handles vs list files, PC-roll attribution vs roster: same
   detectors as §5.1, but running *before* render, so a violation triggers a silent
   regeneration request instead of a visible redo.
5. **Rendering (= bucket 2)** — narration vs NPC block vs cue lines vs tutor hints as visually
   distinct terminal elements. This is precisely the deferred "narration/NPC terminal-UI
   redesign" from the teardown decision, and it satisfies felt-problem #6 (out of the Claude
   chat window) and #8 (the wrapper session simply doesn't load the caveman hook — total
   narration firewall for free).

**What stays in the skill: everything.** All prose rules, commands, scripts, templates, state
files. The wrapper is a client of the skill, not a fork of it — the model still narrates, runs
`/dm:dnd` procedures, and writes campaign files through its own tools.

**Scope estimate:** ~800–1500 lines of Python for a serviceable v1 (SDK session + streaming,
block parser, dice-gate state machine, redaction, plain-but-structured rendering — `rich` is
enough, no TUI framework needed), plus ~20 lines of SKILL.md marker-formalization. The real
cost is not lines — it's a new operational surface (SDK auth/session lifecycle, stream-parse
drift when the model varies its block formatting, Windows console quirks) and the loss of
chat-native conveniences (scrollback, /compact, image display).

**Verdict:** genuinely attractive — but **sequence it after the lint tier**, for three reasons.
(1) The two Tier-1 failures that hurt most are addressable cheaper (one is a missing rule, one
is a scope-gap + detector). (2) The lint's log-only telemetry converts the wrapper decision
from instinct to data: if violation rates stay high *after* the prose patches and visible
redos, the wrapper is earned; if they collapse, it wasn't enforcement that was missing. (3) The
lint work *hardens the exact marker discipline* (`**Roll:**`, cue blocks, NPC blocks) the
wrapper's parser will depend on — nothing is wasted on the path through detection. When built,
justify it as enforcement + bucket-2 UI + caveman firewall together; as enforcement alone it
over-serves.

**(C) full app stays rejected** — the brief's model-downgrade argument holds and nothing found
here weakens it.

---

## 7. Solution ranking — leverage per effort (§9 item 5)

Effort: S = minutes-to-an-hour, M = half-day, L = multi-day.

| Rank | Fix | Effort | Leverage | Notes |
|---|---|---|---|---|
| 1 | `npc_rename.py` add `session-tail.md` (+ fix `SKILL-commands.md:498` fallback direction; decide JSON's fate) | S | High — silent continuity corruption | 1-line + doc line |
| 2 | Roll-turn reshape clause in `SKILL.md:290` (attempt-ok / outcome-never / request-is-final) | S | High — closes the H1 scope gap behind playthrough issue #5 | Prereq for detector crispness |
| 3 | Narration-mode ladder + no-smuggled-deduction rule (with transcript worked example) | S | High — T1-1 is a missing rule, not an adherence failure; cheapest Tier-1 close | |
| 4 | Sync-step check | S | ~~High~~ **Resolved in wave 0**: live install is already a symlink to the working tree (see §3 correction); residual = documented `/plugin update` warning in CLAUDE.md | Was mischaracterized by the brief |
| 5 | Turn-gate lint in the autosave Stop hook, **log-only first**, then per-detector blocking (closer, DC-leak, roll-final, PC-auto-roll, cue validity) | M | High — flips silent→loud AND creates the first adherence metric | Step 0: verify Stop hook fires on this Windows box |
| 6 | Death/handoff protocol (0 HP → dying → on death: canon-NPC promotion / new PC woven in / world remembers; SKILL.md rule + short command procedure) | S–M | High — uncapped campaign-ending risk, 2 independent readers flagged it | Port Sstobo's concept, adapt solo |
| 7 | DC ladder in Dice convention | S | Medium | |
| 8 | Prep-time silent graph seeding (drop the approval prompt for freshly-prepped campaigns; keep it for legacy init at load) | S | Medium — felt-problem #4 | Model authored the data minutes earlier; approval is theater |
| 9 | NPC memory micro-log (append-only 2-3 bullets in Live State Flags; stop deleting at baseline — patch `SKILL-commands.md:475`) | S | Medium | Explicitly NOT numeric vectors |
| 10 | Asset library (`~/.claude/dnd/library/{maps,sounds}/<category>/` + tags manifest; prep does library-first lookup, acquires-on-miss with *generic* names; `render_assets.py` reads both) | M | Medium-high — felt-problem #2; spoiler problem decays as library grows | The one genuinely new subsystem worth building now |
| 11 | Voice worked examples in `SKILL.md:104` (BAD = transcript opener, GOOD = spoken recast) | S | Uncertain — same fix class already failed once; do it cheap, measure via lint log | |
| 12 | Caveman narration firewall (out-of-repo: exempt DM-narration sessions/blocks in the caveman config) | S | Low-medium — §8 proved it secondary | Config change, not repo code |
| 13 | Residue cleanup (`display/` dir, `.gitignore:13`) | S | Hygiene | |
| 14 | **(B) thin wrapper** (dice gate, redaction, validation, bucket-2 rendering, caveman-free) | L | High *if* lint telemetry shows detection insufficient — decision point after 2–3 lint-instrumented sessions | Restoration of the pre-teardown gate + the planned bucket 2, in one artifact |

**Over-engineering flags (do NOT build now):**
- A standing **post-turn recast pass** (second model call rewriting every narration into spoken
  register) — per-turn latency + token cost on every turn to fix a some-turns problem, and
  mechanical recasting flattens the voice it's protecting. If the voice register stays bad
  after #11 + lint-visible feedback, fold the fix into the wrapper decision instead.
- A **blocking literary-prose detector** — no reliable signature; advisory thermometer only.
- **Out-of-combat phantom-reference validation** — entity extraction against sheets is a
  research project wearing a lint's clothes.
- **Any new hook surface beyond the existing Stop hook** (PreToolUse dice interception etc.) —
  the Stop hook covers every detector listed; added surfaces are added failure modes.

---

## 8. Recommended sequence

1. **Wave 0 — make fixes reach the table (same day):** #4 sync step (resolved — symlink
   already live; warning documented) ; verify Stop hook fires (#5 step 0).
2. **Wave 1 — prose + trivial code (one sitting):** #1, #2, #3, #6, #7, #8, #9, #11, #13.
   All S-effort; re-sync the plugin copy after.
3. **Wave 2 — the instrument:** #5 lint, log-only. Play 2–3 short sessions normally (caveman
   config per #12 first). Read `.lint-log.jsonl` after each.
4. **Wave 3 — enable blocking** per-detector where the log shows precision; build #10 (asset
   library) in parallel — it's independent of the enforcement question.
5. **Decision point — wrapper (B):** with 2–3 sessions of violation-rate data: rates collapsed
   → stay pure-skill, wrapper only if the bucket-2 UI itch is worth it on its own; rates
   persistent → build the wrapper as enforcement + UI + firewall combined, reusing the lint
   detectors as its validation pass and the hardened `**Roll:**`/cue markers as its parse
   anchors.

The through-line from the archaeology: this project already ran with hard enforcement once,
traded it away deliberately for leanness, and left IOUs it wrote down. The path above pays the
IOUs in order of interest rate — scope-gap prose first (free), detection with measurement
second (cheap), and the structural gate last, only when the data says the prose ceiling is
real for the rules that remain.

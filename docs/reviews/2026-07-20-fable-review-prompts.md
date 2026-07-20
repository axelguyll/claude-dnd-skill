# Fable review prompts — 2026-07-20

Two passes, diagnose-only. Pass A is scoped to the diff; Pass B needs whole-file
scope and cannot be answered from a diff.

**Protected in both passes — do not propose changes to these:**
- the roll-order rule (`SKILL.md:306`, "the roll request ends the turn")
- the voice/prose rules (register, tone-follows-the-scene, length-follows-heat)

Both have survived several rounds of review and play. They may be *cited* as
evidence, and their enforceability may be assessed, but they are not up for
rewriting or deletion.

---

## Pass A — diff review, `7e2cb23..01d5179`

Repo: `claude-dnd-skill`, a D&D 5e DM skill. The three `skills/dnd/SKILL*.md`
files are the program; the Python scripts are deterministic helpers. Review the
range `7e2cb23..01d5179` — everything before it was covered by the 07-17 sweep.

**Diagnose only. Do not propose rewrites or patches. Return findings and
reasoning; implementation decisions stay with us.**

### What this range contains

Six commits: wave-1 prose patches, a log-only turn lint wired to a Stop hook, a
hook-interpreter fix, session-2 prose patches, session binding for the hook, the
2024 SRD dataset, and three commits from today (autosave block removal, prose
rules, roll lead-in detection).

### Context you should not re-derive

These were established by measurement today. Treat them as settled and do not
propose reversing them without new evidence:

1. **The autosave Stop hook's cadence `block` was removed deliberately.** It
   emitted a decision whose reason instructed the DM to flush continuity, which
   spawned a full model turn (measured: 27.8–38.0s each, returning 36–155
   characters, against a 12.7s median narration turn). It was also redundant with
   in-turn saves — turn 34 wrote `state.md` and `session-tail.md`, turn 35 was a
   checkpoint that rewrote both. Do not propose restoring it.
2. **Lexical detection of the roll-order rule does not work.** The rule permits
   and forbids the same vocabulary ("you push hard against the door" describes the
   attempt and is legal; "looks hard to force" rates the difficulty and is not).
   A bare difficulty lexicon fired on 6 of 6 permitted phrasings. Do not propose
   extending word lists as a fix for recall.
3. **`python3` in the model-facing `SKILL-scripts.md` is fine** — those run
   through the Bash tool where it resolves. Zero failures across a full session.
   The earlier `python3` bug was specific to the hook running under PowerShell.
4. **Per-turn latency is dominated by reasoning volume, not tool calls,** on
   normal narration turns. Turns emitting zero thinking answered in 3.4–5.6s;
   a turn emitting 1603 thinking characters took 22.7s.

### Questions, in priority order

1. **What else in this skill hands work back to the model that could execute
   itself?** The autosave hook was one instance; the category is "a hook, command,
   or procedure whose output is an instruction rather than a result". Every such
   site is a full turn of latency disguised as automation. Enumerate them.
2. **Should `turn_lint`'s blanket `except Exception: return 0` distinguish crash
   from clean?** It concealed a dead hook for an entire session — the lint
   reported 0.00 violations/turn while the hook had never run. Assess: is the
   correct fix a distinct exit path, a liveness marker written on success, or
   something else? Note the competing constraint: the lint must never break a
   turn, which is why the blanket catch exists.
3. **Is the PC knowledge-boundary rule (`SKILL.md`, "two tests") actually
   checkable by the model mid-turn, or is it aspirational?** Be specific about
   which of the two tests is checkable. The character-knowledge test requires
   auditing campaign state; the player-comprehension test requires tracking first
   mentions. Say plainly if either is not realistically enforceable in-turn.
4. **Correctness of the three commits from today.** Particularly: anything
   orphaned by the `decide()` → `count_turn()` change; regex behaviour in the four
   `_ODDS_HEDGE_CATEGORIES`; and whether any test asserts something weaker than
   its name claims. (A prior review already found one of these — a test named for
   target-resistance that actually fired via difficulty predication — so this
   class of defect is present in the file, not hypothetical.)

---

## Pass B — whole-skill enforceability and deliberation audit

Scope: **all of** `skills/dnd/SKILL.md`, `SKILL-scripts.md`, `SKILL-commands.md`,
plus every detector in `skills/dnd/scripts/turn_lint.py`. Not a diff review — this
question cannot be answered from a diff.

**Diagnose only. Two deliverables, both inventories. Do not rewrite anything.**

### Why this pass exists

Response latency is the top complaint (10–15s typical, worse on some turns).
Measurement showed the dominant cost on a normal turn is deliberation volume, not
tool calls — which means the size and redundancy of the rule set the DM weighs on
every single turn is a direct latency cost, paid forever.

At the same time, today's session *added* four rules. That cuts against the goal,
and it is the reason this pass is scoped to the whole file rather than the diff.

### Deliverable 1 — rule inventory tagged by enforceability

Every behavioural rule in the three SKILL files, tagged:

- **script-checkable** — a deterministic checker could enforce it with acceptable
  precision *and* recall
- **model-checkable mid-turn** — the DM can realistically verify it about its own
  output before yielding the turn
- **human-only** — detectable in practice only by a person reading the transcript

Be adversarial about the first two tags. Today established that the roll-order
rule — which had a detector, and was the leading candidate to become the first
*blocking* detector — is human-only in practice: three separate mechanisation
attempts failed, and the working version still misses violations carried by
implication ("She's already got your measure" passes clean). A rule having a
detector is not evidence that it is script-checkable. Ask what the detector
actually catches, and what fraction of real violations that represents.

This inventory is the deliverable that matters most. It tells us which rules we
are actually enforcing and which we are only hoping for.

### Deliverable 2 — merge-and-cut list

Candidates for removal or consolidation, with per-turn deliberation cost as the
criterion — not correctness. A rule can be entirely correct and still not worth
what it costs on every turn. Look for:

- rules that overlap or restate each other and could be one rule
- rules whose failure mode is cosmetic rather than state-corrupting
- rules that fire so rarely they could move to a command procedure or a
  session-start check instead of the per-turn instruction set
- rules that have never demonstrably changed DM behaviour in play

For each candidate, state what is lost by cutting it. We would rather keep a rule
and know its cost than cut one and rediscover why it existed.

### What is off-limits

The roll-order rule and the voice/prose rules are protected — assess their
enforceability, do not propose cutting or rewriting them.

### One honest question to close on

Is this skill's rule set past the point where adding prose rules improves play?
If the answer is yes, say so directly, and say what the alternative mechanism
should be.

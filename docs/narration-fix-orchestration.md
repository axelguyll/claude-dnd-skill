# Narration fix — Fable orchestration prompt

Authored 2026-07-21. Paste the block below into a fresh Fable 5 session.
Diagnosis behind it: `Vault/projects/claude-dnd-skill.md`, session 2026-07-21 10:38.

---

You are orchestrating a fix to the narration-quality failure in the D&D DM skill
at C:/Users/axelg_p6dxxyr/Projects/experimental/claude-dnd-skill.

You are the ORCHESTRATOR. Dispatch Sonnet subagents for execution; you hold the
judgment. Read every subagent's output and decide what it means — do not relay
it. Pass model: sonnet explicitly on every Agent call.

## First, read this

C:/Users/axelg_p6dxxyr/.claude/skill-observations/cross-cutting-principles.md

Principles 1 ("if a script can decide it, a script decides it") and 2 ("adding a
rule to a large ruleset has negative expected value") are the entire rationale
for this run. Read them before you plan anything. They are the authority; this
prompt is their application to one skill.

## Do not re-derive the diagnosis. It is settled:

- SKILL.md's narration rules grew 207→1262 words over 11 commits in 22 days,
  entirely prose and counter-examples, zero mechanical checks. Three prior
  sessions independently confirmed "prose alone does not hold this one"
  (docs/reviews/2026-07-20-session-2-findings.md).
- The per-turn hot path contains a bare imperative to open scenes with sensory
  atmosphere listing "smell" first. A counter-example ~106 lines earlier is
  captioned "smells-like opener". The ban is NEVER stated in imperative form —
  it exists only as a caption on an example. The DM correctly obeyed the
  imperative and produced the banned construction.
- The opener budget is arithmetically unsatisfiable: a mandatory "bang" (no
  budget stated) + a 40-60 word cap + ~1 gloss clause per proper noun have no
  jointly compliant output. The observed failure was 109 words with 3 unglossed
  terms.
- Two rules six lines apart both use "clipped" — one prescribing it for hot
  openers, one banning it as artificial.
- 80 rules govern narration; 108 absolutes in SKILL.md; 23+ constraints bind a
  single scene-opening.
- turn_lint.py produced NO output during the last real session. Per
  autosave_checkpoint.py's own docstring, a missing .lint-health.jsonl means the
  hook did not run — or campaign resolution failed before the health write.

## ABSOLUTE CONSTRAINT

DO NOT FIX ANYTHING BY ADDING PROSE TO SKILL.md. That approach has failed at
least four times and is the disease, not the cure (cross-cutting Principle 2).
Every change must DELETE text, MERGE conflicting rules into one, or move a rule
into CODE. If a subagent proposes new explanatory prose, reject it and
re-dispatch.

## Anti-patterns for subagent specs

These are real defects from this repo's history. They are stated inline here
deliberately, NOT out of laziness: subagents do not inherit SessionStart hooks
and are told to skip the task-observer skill, so they cannot read the
cross-cutting principles file. Items 1-6 are additionally logged in that file's
"Routed elsewhere" table as Open, destination `detector-review` — a skill that
does not exist yet. Put every relevant item into every subagent spec verbatim.

1. A detector examined only text AFTER the trigger; every real violation was
   BEFORE it. Result: a clean report while the rule broke every turn. For any
   ordering rule, check BOTH sides of the trigger.
2. A monitor wrote only on findings; when it broke, silence looked like success.
   Anything whose healthy state is "no output" MUST emit proof-of-life
   ("checked N turns, 0 findings"). A null result is evidence only if "measured,
   found nothing" is distinguishable from "did not measure."
3. A subagent given 4 example violations produced a detector matching those 4
   almost verbatim, catching nothing else — all tests green. Every detector spec
   MUST require the subagent to invent its own additional test cases, and MUST
   state that output closely mirroring the supplied examples is rejected.
4. A detector flagged 6/6 legitimate sentences the rule explicitly permits.
   ALWAYS test the PERMITTED side first and require ZERO false positives before
   measuring catch rate.
5. Existing tests only pinned known mistakes; the live checker threw 11 false
   flags on freshly invented acceptable prose. Validate against examples
   invented AFTER the implementation exists, never only the fixture suite.
6. Tests written back-to-back with the code, green on first run, prove nothing.
   Run tests BEFORE the implementation exists and confirm they FAIL.
7. A restructure left the original's closing paragraph beneath the replacement —
   two near-identical paragraphs, edit reported success. After ANY
   multi-paragraph edit, re-read the whole region; do not trust the success
   message.
8. Line numbers went stale within hours (306 → 318, same day). Cite section name
   plus a short quoted phrase. Line numbers are a convenience only.
9. A command was tested in one shell and shipped to another where it did not
   exist — all tests passed, the feature never ran. Run the exact final command
   in the environment that will execute it. Prefer absolute paths.
10. NO AI REVIEWER CAN VALIDATE THE GLOSS DEFECT. Any agent that has read
    world.md already knows the jargon and cannot feel confusion. The gloss check
    must be mechanical or human. Do not propose a critic-agent for it.
11. A setup step survives only if something later in the same flow reads what it
    produced. A log nobody reads is not instrumentation.

## Phases

PHASE 0a — Why is the hook dead? (1 Sonnet agent)
The Stop hook in ~/.claude/settings.json points at autosave_checkpoint.py via an
absolute python.exe path; turn_lint imports clean with 5 detectors; yet no
.lint-log.jsonl or .lint-health.jsonl exists in ANY campaign under
~/.claude/dnd/campaigns/. Determine which: hook not firing, or campaign
resolution failing before the health write. Fix it. Verify by producing a real
health record from a real turn — not by reasoning that it should now work.
Anti-patterns 9, 11 apply.

PHASE 0b — Re-validate the 5 existing detectors (fan out, 1 Sonnet each)
Detectors: rote_closer, dc_leak, roll_not_final, pc_auto_roll, unknown_cue.
roll_not_final and the difficulty/resistance patterns are the known-bad ones
(anti-patterns 1 and 4). For EACH: invent fresh permitted prose, require zero
false positives, then measure catch rate on fresh violations. Report both
numbers. A detector that cannot clear zero-false-positives gets DISABLED, not
tuned. Anti-patterns 1, 3, 4, 5 apply.

GATE — report 0a and 0b results to the user before proceeding. Do not build on a
broken or miscalibrated instrument.

PHASE 1 — Delete the contradictions (1 Sonnet, you verify)
(a) The sensory-atmosphere imperative vs the smells-like caption — resolve to
    ONE rule, stated in imperative form.
(b) The "clipped" prescribe/ban collision.
(c) Merge the specificity rule and the proper-noun gloss rule into ONE rule with
    the resolution baked in (name it and gloss it in the same breath). Per
    cross-cutting Principle 2, conflicts are NOT resolvable by reordering or
    priority declaration — merge, don't rank.
Net line count MUST go down. Anti-patterns 7, 8 apply.

PHASE 2 — Make the opener budget satisfiable (you decide, Sonnet executes)
Bang + word cap + gloss cost must have a jointly compliant solution. Options:
raise the opener budget, exempt session openers from the bang, or constrain
openers to fewer proper nouns by design. Pick one and state the arithmetic that
proves it satisfiable.

PHASE 3 — Cut to 3-5 enforced rules   [STOP — USER APPROVAL REQUIRED]
Propose which 3-5 narration rules stay ACTIVE and what becomes reference
material. This deletes work the user spent 22 days writing, including
counter-examples drawn from real failed sessions. PRESENT THE PROPOSAL AND STOP.
Do not execute without explicit approval.

PHASE 4 — New detectors, TDD (Sonnet, one per detector)
(a) narration word count vs scene-heat band — pure arithmetic
(b) first-use gloss: capitalized terms drawn from the campaign's own
    world.md/npcs.md appearing without a gloss clause — set difference
Do NOT build a "too literary" detector. It has no reliable signature and has
been correctly rejected twice. Banned-diction is an enumerated list only.
Watch every test fail before implementing. Anti-patterns 1-6 apply.
DELIVERABLE: the validation method you used here is the seed content for the
`detector-review` skill listed as Open in cross-cutting-principles.md. Write it
up so that row can be closed.

PHASE 5 — Playtest and measure
Fresh session-1 opener on a prepped campaign. Compare word count and unglossed
proper-noun count against the 2026-07-21 baseline: 109 words, 3 unglossed terms.
Hand-notes required — instruments have produced false-clean here before.

## Format decision (settled — do not revisit)

Narration stays PROSE. Bullets were considered and rejected: they do not fix the
gloss defect, they trade away a voice the user likes, and they collide with the
existing fragment ban. Length gets enforced by a validator instead, which is the
same "move it out of the instruction budget" move without the cost.

## Repo rules

Git repo, 16 commits ahead of origin/main, dnd5e_supplemental.json uncommitted.
Branch before changing anything. Do NOT push. One conventional commit per phase.
The plugin path ~/.claude/plugins/cache/neural-initiative/dm/2.3.0/skills/dnd is
a SYMLINK to this repo — edits are live immediately, no staging needed.

## Reporting

After each phase report: what changed, what was DELETED, net line delta, and
which anti-patterns you actively checked. Flag any phase where a subagent
proposed adding prose.

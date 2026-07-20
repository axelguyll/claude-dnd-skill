# Pass B — whole-skill enforceability and deliberation audit

Date: 2026-07-20.

Scope: all of `skills/dnd/SKILL.md` (416 lines), `SKILL-scripts.md` (459 lines),
`SKILL-commands.md` (1029 lines), and every detector in
`skills/dnd/scripts/turn_lint.py`. This pass is diagnose-only: it delivers findings and
inventories, and proposes no patches or rewrites. The roll-order rule and the voice/prose
rules are protected — they are assessed for enforceability below, and nothing in this
document proposes cutting or rewriting them.

**A note on line anchors.** The review prompt cites the roll-order rule at
`SKILL.md:306`. In the current working tree it sits at `SKILL.md:318` — the three commits
made earlier today shifted line numbers between the time the prompt was written and the
time this review ran. All anchors in this document are against the current tree, and the
rule is identifiable by its text: "The roll request ends the turn — narrate the attempt
before it, never the outcome."

---

## Deliverable 1 — rule inventory tagged by enforceability

### How the tags were applied

The three tags, with the adversarial standard the prompt asked for spelled out:

**Script-checkable** means a deterministic checker could enforce the rule with acceptable
precision *and* recall. The existence of a regex that fires on the rule's canonical
phrasing does not earn this tag. The questions that do: what fraction of the violations
that actually occur in play would the checker catch, and how often would it stop a legal
turn? Today's roll-order result is the controlling precedent — a rule can have a working
detector and still be human-only, because the detector catches the rule's most literal
phrasings while the real violations arrive by implication.

**Model-checkable mid-turn** means the DM can realistically verify the rule about its own
output before yielding the turn. Applied strictly, this requires three things at once:
the check must be a bounded lookup or an inspection of the turn's own text rather than an
unbounded audit; it must be cheap enough to actually run on every turn where it applies;
and it must survive context compaction, because compaction is precisely when the memory
the check depends on is gone.

**Human-only** means detectable in practice only by a person reading the transcript.

Two structural facts frame the whole inventory, and they are the most important findings
in it:

1. **"Script-checkable" comes in two grades, and only one of them can gate a turn.**
   Almost every deterministic check available in this skill is *post-hoc*: it can measure
   adherence between sessions, but it could not block a turn without an unacceptable rate
   of false stops. Blocking-grade candidates are marked explicitly below. There are only
   two in the entire rule set.

2. **Model-checkable enforcement is not free — it is the latency.** This pass exists
   because measurement showed deliberation volume dominates per-turn cost. Every rule
   tagged model-checkable is enforced *by spending deliberation on it*, every turn,
   forever. So that tag is not good news the way script-checkable is. It means
   "enforceable, at a standing per-turn latency price." This is the central bind of the
   rule set: the genuinely script-checkable rules are the cosmetic format layer, and the
   substance of the skill is either model-checkable at a latency cost or human-only.

### Cluster A — genuinely script-checkable

Eight rules. Two are blocking-grade. Five of the eight checkers do not exist yet.

**A1. Sound and map cues must use handles from the campaign's lists — never invent one.**
(SKILL.md:237-238. Detector: `unknown_cue`, built.)
This is the one detector in `turn_lint.py` whose catch is approximately equal to its
rule. The check is membership in a deterministic list, applied to a machine-parseable
block format. The format dependence is not a loophole here, because the block format is
itself a host-facing contract — a cue emitted in the wrong format has already failed its
purpose (the host can't spot it and click it), so conditioning recall on format
compliance is fair. High precision, high recall. **Blocking-grade candidate.**

**A2. Never state the DC.** (SKILL.md:143. Detector: `dc_leak`, built.)
For literal `DC <number>` strings the detector is near-perfect: precision is high (the
tutor-line and spell-save-DC exemptions are handled), and the literal form is the
dominant real-world failure. The recall tail is real but bounded: paraphrased leaks
("you'll need a 15 or better") escape, and the rule's full scope — never *imply* the
target number, before or after the roll — has a semantic tail no lexicon will reach.
Script-checkable for the literal core; the paraphrase tail stays human-only.
**Blocking-grade candidate for the literal form only.**

**A3. No XP, ever: never run `xp.py award`, never emit an XP block.**
(SKILL.md:379-387; SKILL-commands.md:808. Not built.)
An `xp.py award` tool call in the transcript, or an XP-award block in output, is a
violation with essentially no false-positive surface. Trivially buildable, and could run
either post-hoc or as a gate.

**A4. Every resolved die roll must come from `dice.py` or `combat.py` — never sampled
mentally.** (SKILL-scripts.md:11. Not built.)
This is the strongest unbuilt detector in the repository. Every narrated roll line
("d20+4 = 17") should have tool-call provenance in the same turn, and a transcript-order
check — a roll line with no matching dice invocation — has both high precision and high
recall. It has a second payoff: under `roll_mode: auto` it is the only mechanical audit
of Standard 7's no-fudging rule, because comparing the narrated numbers against the
actual script output is a deterministic diff. Post-hoc grade: numbers embedded in fiction
rather than in roll lines would need entity matching.

**A5. The DM never reads the lint log mid-session.** (SKILL-scripts.md:378. Not built.)
A Read or Bash call touching `.lint-log.jsonl` during a play session is a one-line
transcript check. Trivial and exact.

**A6. Hard gates: never proceed on INVALID.** (`grid.py validate` at
SKILL-scripts.md:105; `prep/schema.py` at SKILL-commands.md:379-380; `mirror_check.py`
at SKILL-commands.md:438-442; `corpus_check.py`. Scripts exist; obedience is unchecked.)
The deterministic half already exists — these scripts exit nonzero on failure. The rule
itself ("stop and fix, never proceed") is model-side, but a violation is fully visible in
the transcript: an INVALID output followed by the procedure continuing. A post-hoc
checker for that pattern would be exact.

**A7. Micro-save liveness: with `autosave: on`, the continuity anchors must not go
stale.** (SKILL.md:262. Not built.)
The *content* of a continuity flush is semantic and unscriptable. Staleness is not:
`state.md` and `session-tail.md` having unchanged modification times across N turns while
the autosave flag is on is a deterministic liveness check. This is the same class of
check whose absence let a dead hook hide for an entire session (Pass A, settled context
item 2 — the lint reported 0.00 violations per turn while the hook had never run).
Post-hoc grade.

**A8. The rendered tracker state and the `## Active Combat` block must never diverge.**
(SKILL.md:348-354. Not built.)
A deterministic diff between the STATE_JSON passed to `render_tracker.py` and the block
written back to `state.md`. Exact and cheap — and notable because the failure it guards
(a mid-combat compaction recovering from a stale block) is state-corrupting, which makes
this one of the few deterministic checks protecting a non-cosmetic rule.

That is the honest total for this cluster: **two blocking-grade rules, six post-hoc
measurement checks, five of the eight not yet built.** Everything else in the skill is
enforced by the model's attention or by nobody.

### Cluster B — rules that have a detector but are human-only in substance

These are the cases the prompt warned about. A detector exists for each; in each case the
detector enforces the rule's most literal phrasing, not the rule.

**B1. The roll request ends the turn.** (SKILL.md:318 — protected. Detector:
`roll_not_final`.)
Human-only, per today's measurement, and the detector's own docstring
(turn_lint.py:237-248) says so plainly: three mechanization attempts failed; the working
version catches four grammatical constructions and misses violations carried by
implication — "She's already got your measure" passes clean. The signal is semantic, not
lexical, and recall does not improve by extending word lists (measured: the bare
difficulty lexicon fired on 6 of 6 phrasings the rule explicitly permits). The
trailing-narration half of the rule — substantive narration *after* the roll request,
caught by a word count — is the only genuinely script-checkable sliver. The docstring
correctly concludes this is not a blocking-mode candidate. Hand review of the transcript
remains the instrument of record for this rule.

**B2. Don't close turns with a rote prompt; vary the wording; never a rote question.**
(SKILL.md:234. Detector: `rote_closer`.)
The detector is a fixed lexicon of roughly four stock phrasings ("what do you do",
"what's your move", and variants). The rule is about *roteness* — a property of
repetition and register, not of matching a list. A DM that ends every single turn with
"What's the move here?" violates the rule on every turn and never trips the detector
once. What the detector enforces is the canonical phrasing; the substance is human-only.
(A post-hoc measure of closer diversity across a session would get closer to the actual
rule; no script does this today.)

**B3. Never auto-roll a PC under `roll_mode: players`.** (SKILL.md:317. Detector:
`pc_auto_roll`.)
The detector matches one output format — a `**Roll:**` line containing a d20 and an
arrow. A violation resolved in prose ("Your blade catches him; seventeen against his
mail") escapes it entirely, and NPC skill rolls formatted the same way land in the log as
noise; the docstring acknowledges both. The *true* rule is transcript-structural: a PC's
d20 outcome narrated with no intervening player message carrying a number. That stronger
check is buildable with the same turn-parsing machinery `last_turn` already uses, and
would be the correct successor detector — but a resolution fully cloaked in fiction, with
no roll line at all, still escapes anything lexical. Script-assistable, human-verified.

### Cluster C — model-checkable mid-turn

These are the rules the DM can genuinely verify before yielding, because each reduces to
a bounded lookup or an inspection of the turn's own output. Thirteen entries.

**C1. Never assign the PC a gender the sheet doesn't record.** (SKILL.md:115.)
One sheet-field lookup. The rule describes itself as "a sheet lookup, not a judgement
call," and that is accurate. A subset is even script-checkable: a gendered address term
(ma'am, sir, my lady, lad) aimed at a PC whose sheet has no gender field is a buildable
lexical check. Pronoun coreference in narration is not.

**C2. Settle advantage and disadvantage before asking for the roll.** (SKILL.md:319.)
A sheet-plus-tracker lookup at roll-request time — equipped armor, load, active
conditions. The rule again brands itself "a check you skipped," which is the right
framing. The retroactive-adjustment half (changing the terms after seeing the number) is
additionally visible post-hoc as a two-turn transcript pattern.

**C3. Inventory and the enemy roster are ground truth.** (SKILL.md:242.)
Bounded lookups — the PC sheet's inventory, the Active Combat roster — and cheap because
the rule is event-triggered (it fires when the player invokes an item or targets an
enemy), not on every turn. The caveat: the failure mode is not noticing the trigger, and
nothing checks for that.

**C4. Voice a condition's mechanical effect; net advantage/disadvantage sources first.**
(SKILL.md:241.)
`tracker.py status` is authoritative and already sits in the combat loop, so the lookup
is bounded and cheap. The tail of the rule — voice it again "whenever it changes the
current roll," but not every turn — is a judgment call.

**C5. Read the NPC's full entry before substantive dialogue; author a supporting-cast
entry before their first substantive dialogue.** (SKILL.md:247.)
Bounded: one file-section read, and the Read call is transcript-visible, so this is also
post-hoc auditable. Two soft spots: "substantive" is a judgment call, and the promotion
half requires authoring a full entry mid-scene — a cost the DM is most tempted to skip
exactly when the scene is hot.

**C6. The re-read ladder before any recap or status claim.** (SKILL.md:248-258.)
The procedure is explicit and bounded — "one targeted Read per claim," with a defined
first stop in Live State Flags. The weakness is the trigger: "after compaction, don't
trust your impression" requires the model to recognize that it is post-compaction, and
that recognition is itself degraded by compaction. The behavior-contract re-read at
SKILL.md:260 shares this exact caveat.

**C7. Stakes decide whether a roll happens.** (SKILL.md:309.)
A single bounded self-question — does failure cost anything, and does anything actively
resist? — that the model can genuinely run. But it is unverifiable from the outside:
compliance leaves no trace, and no one can audit a roll that was never called for.
Model-checkable, evidence-free.

**C8. Call checks by their full "Ability (Skill)" name.** (SKILL.md:313.)
An own-output check. A script version looks buildable (a roll request matching
`_ROLL_REQUEST` with no skill parenthetical) but has a precision trap: bare ability
checks are legal in 5e when no skill applies, and whether one applies is the fiction's
call, not a regex's.

**C9. The per-turn combat sequence, steps a through e, in order.** (SKILL.md:332-360.)
It is a checklist, and each step's tool call is transcript-visible, so post-hoc
step-presence checks (did tracker tick run, did the render run, was state written back)
are buildable as well. This is model-checkability in the strongest form available in the
file — which is consistent with combat turns being the skill's most reliable behavior in
actual play.

**C10. Length follows the scene's heat.** (SKILL.md:117-122 — protected.)
Word count is a measurable property of the turn's own output, and the heat class is
partly derivable from state: an Active Combat block means the scene is hot, so a script
flagging a 150-word pre-choice narration mid-combat would have tolerable precision.
Outside combat, heat is the DM's own read of the scene, and the "Breathe" exemptions
(arrival somewhere new, a big reveal) are semantic. Partially checkable; assessed only,
as a protected rule.

**C11. Tutor-hint format, trigger table, and placement.** (SKILL.md:395-410.)
When `tutor_mode: on`, format and placement-last are own-output checks and regexable.
The trigger table ("decision point," "before irreversible choice") is semantic.

**C12. Guided-entry rules — menu for the ambiguous case, skip it when intent is
explicit, `AskUserQuestion` only for bounded choices.** (SKILL.md:53-65.)
A bounded decision procedure that fires once per session at most. "Intent already
explicit" has fuzzy edges, but the file enumerates the cases.

**C13. Hidden rolls go through `dice.py --silent`; narrate only the perceived result.**
(SKILL.md:240.)
A split rule. The `--silent` half is a tool-call check. The disclosure half — narrating
only what the character perceives — is the knowledge-boundary problem again, and
human-only.

**The cost note that applies to this whole cluster.** C1 through C13 are the rules the DM
can actually enforce, and enforcing them is a per-turn tax of lookups and self-checks —
exactly the deliberation volume the latency measurement identified as the dominant cost.
A rule being model-checkable means the rule is *payable*, not that it is *paid*: nothing
in the system verifies that any of these checks ran on any given turn. The only way to
find out is a post-hoc audit of the A4/A7 kind, and only two of the eight such checkers
exist.

### Cluster D — human-only

The largest cluster by a wide margin. Grouped by family where the justification is
shared.

**D1. The knowledge-boundary family.** (SKILL.md:97-113, plus the related rules at 109,
111, and 236.)
This is Pass A's question 3, re-answered at whole-file scope, and the answer is the same:
human-only in-turn. The two tests fail the model-checkable bar on different prongs:

- *Test 1 — does the character know it?* — fails the **bounded-lookup** requirement. The
  ground truth is everything this PC has witnessed on-screen or been told out loud across
  the whole campaign: an unbounded audit spanning session logs, the archive, and the
  graph. No per-noun mid-turn check can traverse that. In practice the DM checks each
  noun against its *impression* of the history, and the impression is precisely what
  leaks.
- *Test 2 — can the player follow it?* — fails the **compaction** requirement.
  First-mention tracking is cheap early in a session and gone after compaction. The rule
  degrades exactly when sessions run long enough for it to matter.

The adjacent rules inherit the tag: NPC epistemics (SKILL.md:109 — "a path by which they
learned it" is an audit of the off-screen world model), referent resolution
(SKILL.md:111), and deduction-smuggling in overheard speech (SKILL.md:236). A post-hoc
script assist is possible — a first-occurrence scan of capitalized names against the
prior transcript and campaign files, flagging unglossed first uses for review — and that
is the right instrument grade for this family: a reviewer's queue, not a gate. The rule's
own text concedes what this tag means: the player *cannot* catch these violations from
their side. So the only in-play enforcement is the DM's attention, and the only
verification is a person reading the transcript.

**D2. The voice and prose family (protected).** Tone-follows-the-scene (SKILL.md:26);
write-it-as-you'd-say-it, with the banned-diction and no-fragment rules (SKILL.md:124-128);
specifics-not-abstractions (SKILL.md:95); sensory economy (SKILL.md:93).
Human-only, with narrow lexical slivers: the named banned words (*tallow, cadence,
sexton, lintel*) and a colon-dump pattern are regexable, but the substance — would a
person say this sentence aloud; is the tone saturating scenes it doesn't belong to — is
register judgment. The 6-of-6 false-positive result on the difficulty lexicon is the
controlling precedent for this entire family: permitted and forbidden prose share
vocabulary, and the signal is semantic. Assessed only; nothing here proposes touching
these rules.

**D3. The engagement and pacing standards** — Standards 1, 2, 6, 8, 9, 12, and 13
(SKILL.md:73-90, 133-138, 149-159, 169-173).
Reading the player's energy, calibrating to this specific player, pacing scenes and
sessions, enthusiasm, opening with bangs, rewarding bold play: all judgments about the
player and the fiction, with no own-output check available. Two partial exceptions worth
recording. First, the energy-flagging *triggers* at SKILL.md:84 — replies shrinking for
two or three turns, the player taking the first offered option three times running — are
measurable from the transcript by script, even though the required *response* (pick a
re-engagement tool) is not. Second, the pressure-point cadence at SKILL.md:138 hangs on
counting scenes, and a scene boundary has no machine-detectable definition — a problem it
shares with the micro-save, which uses the same trigger.

**D4. Fairness and resolution texture.** No fudging (SKILL.md:141);
a failed roll complicates rather than dead-ends, with the puzzle exemption
(SKILL.md:145); complications drawn from the world in motion, in preference order
(SKILL.md:147).
Human-only, with the one carve-out noted at A4: under `roll_mode: auto`, dice-provenance
checking makes fudging mechanically auditable, because every number the DM narrates
should trace to script output. Under `roll_mode: players` the dice are the player's, and
any fudging shifts into DC and outcome handling — which is invisible, per D5.

**D5. Rules with no observable trace at all — unenforceable by anyone, including a human
with the transcript.** The DC ladder (SKILL.md:311) instructs the DM to pick a band
*silently, before* calling for the roll. Compliance produces no output. The only
observable is cross-session inconsistency — the same task meeting a different implied
difficulty later — and detecting that requires a human diffing sessions against each
other. The same class: "internalize the subgraph before delivering the recap"
(SKILL-commands.md:134), "read and internalize DM Style Notes" (SKILL-commands.md:111),
and the micro-save's "ask yourself once: did any faction take a step off-screen?"
(SKILL.md:262). These rules may well do good work, but it is worth stating plainly that
they cannot be audited by any instrument, human or scripted. They are hopes with good
intentions.

**D6. Arc steering quality.** (SKILL.md:268-305.)
Telegraph before the beat, steer with pressure rather than walls, consequence-shaped
revision, respecting detours — all human-only. The *bookkeeping* attached to them is a
different story: beats marked at save and end, `outstanding_beats` updated, revisions
written spine-first and then mirrored — all deterministic, and partially gated already.
`mirror_check.py` is the one piece of arc bookkeeping with a real gate; the rest is
script-verifiable but currently unchecked.

**D7. Cross-session obligations.** Faction moves answered per active faction at session
end (SKILL.md:167 — note that *whether a line was written* is script-checkable at each
save; whether it represents real world-motion is not); pillar inheritance surfacing
within two sessions of a PC death (SKILL.md:373); the NPC-memory collapse rules
(SKILL-commands.md:484); DM Style Notes updates (SKILL-commands.md:571). All human-only
in substance; several script-checkable in presence.

### Inventory summary

Roughly 70 distinct behavioural rules across the three files, counting the families
above. The distribution:

- **Script-checkable: 8** — of which **2 are blocking-grade** (cue-handle membership;
  the literal DC leak). Six are post-hoc measurement checks, and five of the eight
  checkers have not been built.
- **Detector-owning but human-only in substance: 3** — including the protected
  roll-order rule. This confirms today's finding at whole-file scope: **no detector in
  `turn_lint.py` except `unknown_cue` enforces the rule it is named for.** The others
  enforce the rule's most literal phrasing.
- **Model-checkable mid-turn: about 13** — every one of them a standing per-turn
  deliberation cost, and none with any verification that the check actually ran.
- **Human-only: about 45 or more** — including both of the highest-stakes families
  (knowledge boundary and roll-order), plus a distinct subclass (D5) that not even a
  human reading the transcript can audit.

What this says about which rules are actually being enforced: the machine-enforced
fraction of this skill is the cue lists and literal DC strings. The model-enforced
fraction is a set of bounded lookups whose execution nothing verifies. Everything that
makes the skill good at being a DM is enforced by attention and hoped into place. That is
consistent with where the real violations have been found — knowledge leaks and
roll-order violations by implication, both squarely in the human-only column, and both
committed *under rules that already prohibited them*.

---

## Deliverable 2 — merge-and-cut list

The criterion throughout is per-turn deliberation cost, not correctness — a rule can be
entirely correct and still not be worth what it costs on every turn. Every candidate
states what would be lost. The protected rules do not appear. Nothing here is a rewrite;
these are candidates with their costs stated, for the maintainers to decide.

### Redundancy — the same rule stated more than once in the always-hot set

**M1. "Never auto-roll a PC" is stated at least four times.** The canonical statement
with the ⚠ marker is SKILL.md:317; it recurs at SKILL-scripts.md:11 (parenthetical) and
in SKILL-commands.md at lines 16 and 80 (the `new` and `load` setup steps). The
dice-convention block is re-weighed on every roll-adjacent turn.
*What is lost by consolidating:* possibly a lot — the repetition may be deliberate
compaction armor, so that whichever file fragment survives a context loss still carries
the hard constraint. If that is the design intent, it deserves to be written down
somewhere; if it is not, three of the four statements are free savings.

**M2. The pre-emption landing paths are stated three times.** Full templates at
SKILL.md:300-303; restated in the `/dm:dnd end` flow at SKILL-commands.md:576-580; full
templates again under `arc revise` at SKILL-commands.md:869-872. This material fires only
at session end and during revision — never mid-turn — yet the SKILL.md copy sits inside
the always-hot steering block.
*What is lost by keeping one copy (in `arc revise`, where the action happens):* locality
at the `/end` checklist and in steering rule 8. A one-line pointer at each site covers
it.

**M3. Milestone leveling is stated three times.** A dedicated section at
SKILL.md:377-387; `beat complete` step 3 at SKILL-commands.md:458-462; the XP-gate bypass
at SKILL-commands.md:706-708. It fires only at beat completion.
*What is lost by reducing the SKILL.md copy to its single per-turn-relevant fact (no XP,
ever):* essentially nothing per-turn. The procedures already live in the commands file,
and the no-XP rule is separately restated at combat end (SKILL-commands.md:808).

**M4. The structured and dynamic steering blocks overlap.** "Never deliver a beat cold"
appears at SKILL.md:268, again at SKILL.md:290, and a third time inside the
world-pressure definition. "Do not reference the arc document to players" is duplicated
verbatim at SKILL.md:278 and SKILL.md:305. Pressure-not-walls at SKILL.md:270 underpins
both blocks. Exactly one arc type is active in any campaign, so the DM carries a dead
block every session, and the shared rules are carried twice.
*What is lost by stating the common rules once:* self-containment — today either block
can be read alone and be complete. The duplication costs roughly fifteen always-hot
lines.

**M5. The engagement triangle: Standard 2 against Standard 1 and Standard 9.**
Standard 2 (SKILL.md:86-87) contains no instruction that is not already present in
Standard 1's signal-reading paragraph (SKILL.md:84) plus Standard 9 (SKILL.md:152-159).
*What is lost by merging:* the rhetorical emphasis and the "amplify what lands" framing.
No operational content is unique to Standard 2.

**M6. The sheet-is-ground-truth family.** Gender (SKILL.md:115), advantage/disadvantage
before asking (SKILL.md:319), and inventory (SKILL.md:242) are one principle with three
triggers — and the signature sentence ("this is a check you skipped, not a judgement
call") appears verbatim at both :115 and :319.
*What is lost by consolidating:* placement, and that loss may be decisive. Each copy
currently sits adjacent to the moment it fires — :319 inside the dice convention, :242
inside the narration principles — and that adjacency is plausibly what makes these rules
actually fire in play. This is a low-confidence candidate: flag it, but don't act on it
without evidence that adjacency isn't load-bearing.

**M7. Advantage/disadvantage netting is stated at both SKILL.md:241 and SKILL.md:319.**
Small overlap; the same placement caveat as M6 applies.

**M8. The micro-save mechanism is restated in full across three files.** The operative
copy is SKILL.md:262 (about 250 words); SKILL-scripts.md:343-364 covers the autosave
scripts and the hook; SKILL-commands.md:1012-1029 is the toggle command. The scripts.md
copy also carries session-binding rationale and development history ("on 2026-07-20 the
first entry ever written to a lint log was a false positive…") — that is review
documentation, not play instruction, and it costs context in every session for the
benefit of a reader who is not the DM.
*What is lost by trimming the reference copies to mechanism-only:* the inline history
explaining why the session binding exists. That history already lives in the review
documents.

**M9. "Never state the DC" and the DC ladder restate each other's core clause.** Both
SKILL.md:143 and SKILL.md:311 carry the behind-the-screen sentence. A one-line
deduplication; trivial either way.

### Rules whose failure mode is cosmetic

**M10. Pronunciation hints on first use of invented names.** (SKILL.md:239.)
Fires rarely; the failure mode is a host stumbling over a name once; no session evidence
anywhere in the repository of it ever mattering; and it silently adds a
first-use-tracking obligation — the same class of session-long memory that test 2 of the
knowledge-boundary rule shows does not survive compaction.
*What is lost by cutting:* read-aloud comfort for invented names. Real but small, and
recoverable in play by the host simply asking.

**M11. Tutor-hint placement-last and formatting minutiae.** (SKILL.md:410.)
Active only when `tutor_mode` is on, and the failure is cosmetic. Cheap to keep; listed
for completeness rather than urged.

Deliberately *not* listed here: the NPC-dialogue blockquote format (SKILL.md:235) and the
cue-block formats look cosmetic but are host-facing contracts — the visual break is what
lets a human scan and click, and detector A1 depends on the cue format being stable.
Their failure mode is functional, and they earn their cost.

### Rules that could move out of the per-turn set because they fire rarely

**M12. Death & Dying.** (SKILL.md:364-373.)
Fires approximately never on any given turn; the procedure is event-triggered and
self-contained; it is command-procedure-shaped content living in the core file.
*What is lost by moving it to SKILL-commands.md:* the guarantee that it is already in
context at the exact moment a third failed death save lands mid-combat — which is a real
argument for leaving it where it is, since that is the worst possible moment for a file
read to interrupt. A genuinely split decision; the cost is stated and the call is the
maintainers'.

**M13. The 2014/2024 ruleset differences table.** (SKILL.md:32-47.)
Consulted at character creation, level-up, and weapon-mastery moments. All of those are
command-time except mastery, which is mid-combat.
*What is lost by moving it:* the mastery row's mid-combat availability. A partial
candidate at best.

**M14. The guided-entry menu (SKILL.md:51-65) and the model-routing table
(SKILL.md:211-223).** Both fire at most once per session, before play begins. They are
small, but they are pure session-start machinery living in the always-hot file.

**M15. The structural observation — the biggest deliberation-volume lever in the
repository is not a rule at all.** `SKILL-commands.md` is 1029 lines and is loaded whole
at session start (its own line 3 instructs this), although each procedure fires at most
once per session and several — `import`, `prep`, `rename`, `registry`, `path`, `update` —
usually never fire in a play session at all. The skill already practices lazy loading
rigorously for *campaign data*: world-nodes.md, arc.md, spine.json, and chapter sources
are all kept off the hot path with explicit do-not-load-at-start rules
(SKILL-commands.md:112-120). Its own largest file is exempt from the same discipline.
Given the settled measurement that deliberation volume dominates per-turn latency,
roughly a thousand lines of always-hot procedure text is attention load on every
narration turn of every session.
*What is lost by per-command on-demand reads:* one bounded file-section read at each
command invocation, and a new failure mode — a command run in a stale context skipping
the read. Recorded as an inventory finding, not a proposal; it is the single largest
per-turn-cost item this audit found.

### Rules with no demonstrated behavioral effect

**M16. Standard 8, "Play with Genuine Enthusiasm."** (SKILL.md:149-150.)
No output contract, no check, and no observable difference between compliance and
violation in a text transcript beyond what the voice rules already govern.
*What is lost by cutting:* the permission-structure framing ("if a scene doesn't
interest you, find the angle that does"), which may function as prompt-engineering that
improves output in ways nobody has measured. Unknown effect in both directions — which is
exactly why it sits in this bucket rather than a cut list.

**M17. The introspective half of the oracle rule.** (SKILL.md:244.)
"When the fiction poses a question your prep doesn't answer" is a genuine tool rule with
a clear trigger. "…or you catch yourself deciding by default" is unverifiable
introspection — D5-class — with no evidence of ever having fired.
*What is lost by trimming to the tool half:* a one-clause nudge toward dice honesty.
Cheap to keep, cheap to cut.

---

## The closing question

**Is this skill's rule set past the point where adding prose rules improves play?**

**Yes.** Three lines of evidence, all from this repository's own measurements rather than
from taste:

1. **The marginal rule now lands in the human-only column.** Today's additions were
   prose rules plus a roll lead-in detector whose own investigation concluded the signal
   is semantic, not lexical. The inventory shows why this is structural rather than bad
   luck: the script-checkable space — formats, list membership, literal strings — has
   already been harvested. What remains to want rules *about* is register, epistemics,
   and pacing, and those are unenforceable by construction.

2. **Every rule is paid for on every turn, whether or not it ever fires.** The latency
   measurement prices the rule set directly: deliberation volume dominates, and the
   per-turn rule surface is the deliberation. A correct rule that prevents a cosmetic
   failure once every three sessions, weighed on each of a session's forty-plus turns, is
   a bad trade at current latency — and the audit shows the per-turn set is already
   carrying fire-rarely content (M2, M3, M12 through M15).

3. **The violations that persist are attention failures, not coverage failures.** The
   knowledge leaks and roll-order violations in the lint log and the review record all
   occurred under rules that already prohibited them — rules with worked examples
   attached. A new rule competes for the same finite per-turn attention whose exhaustion
   caused the violation in the first place. Past the saturation point, adding rule text
   is net negative: it dilutes the attention paid to every existing rule, including the
   ones being violated. The persistence of violations under existing coverage is itself
   the evidence that the point has been passed.

**What the alternative mechanism should be** — directional, as the prompt requests:

- **Between-session measurement instead of in-turn instruction.** The instrument layer
  is half-built and underused: the lint log plus hand review is what actually found
  today's violations. The unbuilt post-hoc checkers in Cluster A — dice provenance (A4),
  micro-save liveness (A7), state divergence (A8), no-XP (A3), lint-log privacy (A5) —
  are cheap, exact, and cost zero per-turn deliberation. That is where the enforcement
  budget should go.

- **Worked examples inside existing rules, instead of new rules.** The file's own
  best-performing device is the failure-shape list — the four ✗ examples under the
  knowledge-boundary rule (SKILL.md:103-107) and the worked prose pair
  (SKILL.md:126-128). An example disambiguates a rule the model already holds; a new
  rule adds one more thing to weigh. When play surfaces a new violation of an existing
  rule, the fix that doesn't grow the per-turn set is a new ✗ example under the rule
  that failed.

- **Shrink the always-hot set.** M15 plus the fire-rarely items are a latency lever that
  requires no rule to change at all.

- **For the two high-stakes human-only families, put the human in the loop
  deliberately.** Knowledge-boundary and roll-order adherence are transcript-review
  problems. A short between-session review pass — the lint log's stated review cadence,
  extended with the first-mention scan described under D1 — enforces them at the grade
  they can actually be enforced. On today's evidence, in-turn prose does not.

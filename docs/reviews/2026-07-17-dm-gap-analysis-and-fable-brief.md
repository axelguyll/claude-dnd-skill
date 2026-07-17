# DM Gap Analysis + Fable Deep-Dive Brief — 2026-07-17

**Purpose.** Consolidate everything surfaced in the 2026-07-17 analysis session (playthrough
feedback → 3-repo comparison → fork gap audit → enforcement thesis → architecture question) into
one document, then use it as the input brief for a second Fable (Fable 5) deep-dive of the current
architecture — this time solution-focused, not just findings.

**Scope reminder.** This fork is a **solo, terminal-only** 5e DM (one person = DM + player, single
terminal). The couch-co-op display companion was deliberately torn out. Optimize for *this*, not
multiplayer / product / player-facing app — unless the architecture decision (§6) changes that.

---

## 1. The 8 playthrough issues (source: session-1-transcript.md, "The Honest Map")

1. **Ambient sound scope** — is ambient tied to encounters like maps, or scene-based? (Answer:
   should be scene-based; maps are encounter-scoped, ambient is per-location. Library depth is the
   real need.)
2. **Asset names spoil what's coming** — being told to fetch a map/sound for a named scene leaks the
   encounter. Wants a generic, reusable, folder/tag-organized library the DM pulls from by category.
3. **Prep shopping list must separate** ambient (non-encounter) vs maps (encounters) vs encounter
   music. Ambient is the hard-to-source class; encounter music is easy.
4. **Prep shouldn't ask to approve the relationship graph** — internal bookkeeping, should be silent.
5. **Roll order** — the check must come BEFORE the outcome is narrated. Transcript narrated the
   result/lead-in first, then asked for the roll. (Refined: describe the *attempt* pre-roll is fine;
   never the *outcome/likelihood*.)
6. **Move play out of the Claude chat window** — wants a separate interface (e.g. Python chat), like
   the prior dm-app version. (Requirement not yet pinned: media/immersion vs full app.)
7. **Narration vs direct quotes** — don't literal-quote everything. Match narration mode to
   information state: clear+present → direct quote; degraded/secondhand/eavesdrop → narrator summary
   + sparse fragment. Also flagged a smuggled deduction (narration asserted "the Vigil" the overheard
   quote never named — DM making the player's inference for them).
8. **/caveman degrades narration** — global terse-mode strips the prose texture narration needs.
   Wants narration exempt while keeping caveman for mechanical/meta output.

**Cross-cutting insight:** #5, #7b, #8 are one failure — the DM resolving the player's experience
ahead of the player (pre-deciding roll outcomes / deductions / stripping the info-carrying prose).

---

## 2. Three competing repos analyzed (fit /10 for this goal)

- **neuralinitiative/claude-dnd-skill** (our upstream base) — 6/10. Best-in-class state/graph/
  roll-integrity discipline. No maps, no music, no prep phase.
- **Sstobo/Claude-Code-Game-Master** — 5/10. World-voice/NPC-voice split; generic "World Kit"
  ruleset; RAG book import; **explicit Death Protocol**. Unix-leaning (Windows-hostile). No faction
  graph, no maps/music.
- **MoonlightByte/NeverEndingQuest** — 6/10. Full OpenAI Python app; Flask/SocketIO **web UI**;
  **swappable, name-indexed, manifest-registered "graphic pack" asset library** (reusable across
  campaigns); portraits/video; TTS. Fair Source license (non-commercial, extraction-hostile, 200KB
  main.py). Still NO rendered battle map, NO music; dice rule is prompt-only.

---

## 3. Where the fork already BEATS all three repos (do NOT spend effort here)

- Real battle maps (`grid.py` text-descriptor grid + SVG overlay + projector `map.html`) — no repo
  renders a map at all.
- Real ambient audio (`assets.html` `<audio loop>`, two-file split protects playback) — repos are
  TTS-narration-only, zero ambient/music.
- Spoiler-safe asset prep (separate-pass generation, terrain/atmosphere-only vocabulary,
  `SKILL-commands.md:381`).
- Time-stamped typed relationship graph + deed-cited stance changes (`campaign_graph.py`,
  `SKILL-commands.md:491`).
- Compaction-survival (Live State Flags + re-read discipline `SKILL.md:223`; zero-LLM recap diff
  `session_recap.py`).
- 7 authenticity rules — more than any repo.
- Considered and **rejected** from repos: B's World Kit (5e-only here), B's RAG import (have PDF
  import), C's numeric NPC emotional vectors (over-engineered), C's player web UI (chose terminal +
  DM-side HTML dashboard on purpose).

---

## 4. Real gaps found (evidence-based, ranked)

### Tier 1 — highest leverage
1. **Narration-vs-quote craft — ABSENT and mis-signaled.** Only speech rule (`SKILL.md:211`) is a
   formatting rule that pushes toward verbatim quotes for everything; no rule for when the narrator
   should summarize (eavesdrop/half-heard/secondhand). Directly causes issue #7. Reference: B's
   world-voice/NPC-voice split.
2. **No Death / handoff protocol — ABSENT.** Only mechanical death-save tracking (`tracker.py:26`);
   nothing for what happens at PC death. Solo permadeath = campaign just stops. Port B's protocol
   (0 HP = dying; hand off to companion / new PC / canon NPC). Flagged by 2 independent readers.
3. **Reusable asset library — ABSENT (= issue #2).** Asset model is per-campaign just-in-time; host
   re-acquires files every campaign; no cross-campaign index/tags/manifest (`render_assets.py:31` =
   3-field regex parser). Port NEQ's graphic-pack pattern: `~/.claude/dnd/library/{maps,sounds}/
   <category>/` + tags + library-first lookup, fall back to "acquire fresh" only on miss. Spoiler
   problem decays as library grows.

### Tier 2 — cheaper
4. **No DC-setting ladder** — have hidden-DC + fail-forward, but no guidance on what number to set
   (consistency risk). B has one.
5. **`npc_rename.py:94` bug** — updates `session_tail.json` (unread) and skips `session-tail.md`
   (which recap/load DO read, `SKILL.md:225`). Renamed NPC shows stale name in the continuity file.
   ~2-line fix.
6. **NPC dispositions deleted on return to baseline** (`SKILL-commands.md:475`) — no record of what
   an NPC remembers the party did. Cheap fix: append-only 2-3 bullet micro-log in Live State Flags
   (NOT numeric vectors).

### Tier 3 — minor / known
- Caveman doesn't firewall narration (issue #8; hook/config fix).
- DM voice anchor thin (tone catalog = one-liners, no sample passages).
- Faction-Moves uncapped prose SOP; graph seeds lazily at first load not creation; parked
  `difficulty:` → band-math wiring.

---

## 5. THE cross-cutting finding — the enforcement ceiling

Every authenticity rule is prose-only, no code gate, and the transcript proves it slips:
roll-before-narrate is written as forcefully as language allows (`SKILL.md:290`: "STOP", "Never
fall back") yet the playthrough narrated the outcome BEFORE the roll (#5) and quoted everything
literally (#7). Writing louder prose won't fix a rule that already exists and didn't fire. Same
critique leveled at NeverEndingQuest — we just have more/better rules hitting the same ceiling.

**Proposed direction — a tiered spectrum, NOT "rip out prose for code":**
- **Judgment rules** (quote-vs-summarize, voice, tone, DC *value*) → stay prose + worked examples.
  Only option; architecture can't help.
- **Machine-checkable rules** (roll-before-narrate; hidden-DC = no DC number in player text;
  phantom-item = named thing exists in sheet/roster) → add **detection**: a post-turn validator
  (Stop-hook / lint script / cheap subagent) using regex + existing STATE_JSON/sheet data. Detection
  ≠ prevention, but flips silent failures to loud ones and enables catch-and-redo.
- **Roll-before-narrate specifically** → also **reshape the turn**: make the roll-request its own
  required emission with a STOP, gate resolution behind receiving a result. Structural step is
  harder to skip than a declarative adjective. `dice.py` exists; missing piece is the turn scaffold.
- **Architectural limit (honest):** a pure CC skill cannot truly block model mid-output — no
  interceptor in the output stream. Hard prevention needs an app wrapper mediating I/O.

---

## 6. The architecture question (Python app vs stay skill)

Three points on a line:
- **(A) Pure skill, now** — model orchestrates; prose rules; detection only. Enforcement ceiling.
- **(B) Skill + thin Python turn-loop wrapper** — a small layer mediating ONLY the mechanical
  chokepoints (dice-gate, state authority, DC redaction, reference validation); Claude + existing
  skill prompts still do narration. Keeps everything built, stays on Claude, keeps tests, gets the
  hard gate where it earns its keep. **Current lean recommendation.**
- **(C) Full standalone Python app** (original dm-app dream) — own everything, pick a model, pay
  API, rebuild solved systems, leave Claude. Justified ONLY if the goal is a shippable product,
  true multiplayer, or a real app UI is the top priority.

**Key reframe:** Python fixes *mechanical* correctness (Pile 1), not *storytelling* correctness
(Pile 2 = narration voice/quote craft, which is model+prompt-driven and unaffected by architecture).
Half the pain is Pile 2. Also: a full app likely downgrades the model (Opus/Sonnet on Pro plan →
paid API, gpt-4o-mini-tier) which is what currently makes Pile 2 tolerable.

---

## 7. OPEN — user's felt problems in prep-phase / playthrough (TO FILL)

> Below are the problems the user communicated in their own voice across the analysis session
> (from the playthrough feedback and the follow-up architecture discussion). Fable should treat
> these as the felt/qualitative signal behind the analyst findings in §1–§6.

**From the playthrough (user's framing, beyond the bare issue list in §1):**
- Asset names spoil the game live: being told to gather a map/sound for a named scene made it
  "impossible not to know what's about to happen — the map tells me there's an encounter there."
- Roll ordering felt wrong in play: narrating before the roll is "unnecessary and unnatural, and
  it pre-determines the result." Wants: ask for the check → player rolls → then narrate outcome.
- Narration over-quotes: "right now everything is delivered as literal quoted dialogue." Wants the
  DM to decide when a direct NPC quote is warranted vs when the narrator should summarize — gave
  the eavesdrop example as the model for how real D&D is voiced.
- The DM smuggled a deduction: overheard dialogue never named the Vigil, yet narration asserted
  "the Vigil's sealed gate opened…" — "you're telling the player they should know the NPCs are
  talking about the Vigil when it isn't clear at all that they are."
- Caveman is actively hurting play: "/caveman is degrading the narration and plot — it comes out
  spotty and it's unclear what's happening." Loves caveman for tokens, but it shouldn't touch how
  the game handles details, descriptions, quotes, and narration.
- Prep shopping list conflates asset types: it asked for environment sounds without flagging an
  encounter was coming — encounter music and ambient sound are two different things and the list
  should ask for them as distinct categories.
- Prep asked for approval to seed the relationship graph — "why is it asking me this? This is
  internal bookkeeping. It should just do it."
- Wants to stop playing inside the Claude chat window — wants a separate interface (did this with
  the prior dm-app version, possibly a Python chat).

**From the architecture discussion (user's instinct):**
- Feels the DM is not yet "efficient, effective, and correct in the true way D&D is played," and
  suspects the fix may be architectural — considering switching back to the Python-focused side of
  the original dm-app idea.
- Worried the prose-only rules won't hold — asked directly whether we need actual code enforcement
  rather than more prose rules.
- Senses there are prep-phase and playthrough problems worth surfacing systematically (this brief
  is the response to that instinct).

---

## 8. Diagnostic to run FIRST (before committing to enforcement/architecture work)

Rule out that the transcript failures were environmental, not rule failures:
- **Stale SKILL.md** — the F1 symlink/caching bug (harness ran an old skill). Verify the plugin
  symlink resolves to current `main`.
- **Caveman degradation** — caveman was active that session; may have degraded adherence + prose.

If failures were environmental, the "we need enforcement" premise weakens — the prose rules may
already work. Do not commit to a large architecture move on evidence that might be a caching bug.

### DIAGNOSTIC OUTCOME (run 2026-07-17)

**Stale-skill hypothesis — REFUTED.** The running plugin is `dm@neural-initiative` v2.3.0,
installPath `~/.claude/plugins/cache/neural-initiative/dm/2.3.0` (a plain copy, no .git). Its
entire `skills/dnd` tree is **byte-identical** to the fork's current v2.4.0 working tree
(`diff -rq` = empty; SKILL.md identical, 48772 bytes, mtime 2026-07-16 16:07 = fork's v2.4.0 merge
commit 49f4ae6). The roll-before-narrate STOP rule is present verbatim at running-skill
`SKILL.md:290`; hidden-DC, ground-truth, NPC-block rules all present. The playthrough transcript is
dated **2026-07-17 11:49**, AFTER the skill was synced to v2.4.0 (07-16 16:07) and AFTER the
authenticity/voice merges (07-15). **So the skill was fully current at playthrough time — the
failures are NOT a caching artifact.**
- Note: version label "2.3.0" in `installed_plugins.json` is cosmetic/stale metadata; the CONTENT
  is current. Also note the plugin is a frozen COPY synced to the fork, NOT auto-tracking it — a
  future fork change won't reach the running skill until re-synced (likely via `update_skill.py`).
  Worth confirming the sync step so fork edits actually take effect in play.

**Enforcement-ceiling thesis — CONFIRMED (strengthened).** Because the roll-before-narrate rule
(`SKILL.md:290`, maximally forceful — "STOP", "Never fall back") was loaded and active during the
playthrough and the DM STILL narrated the outcome before the roll (#5), this is now proven to be a
prose-rule-ignored failure, not a missing/stale rule. Issue #7 (literal quotes) is a genuine
missing rule (no narration-vs-summarize rule exists; the NPC-block-always rule pushes toward
verbatim quotes) — also not staleness.

**One live environmental factor — caveman WAS active.** Caveman mode is globally on (SessionStart
hook) and was almost certainly active during the playthrough. It is both the direct cause of #8
(degraded narration prose) AND a plausible amplifier of #5 (terse-mode pressure competing with the
narration/roll rules). **Recommended cheap next test BEFORE building enforcement: replay one scene
with caveman OFF ("stop caveman" / normal mode).** If roll-ordering (#5) and prose quality recover
→ caveman was the amplifier and the fix is the caveman/narration firewall (cheap, config/hook).
If #5 STILL slips with caveman off → the enforcement ceiling is real and independent, justifying
the detection/reshape work in §5. This test cleanly separates "caveman contamination" from "prose
rules genuinely don't hold."

### CAVEMAN-OFF REPLAY TEST — RUN (2026-07-17). Result: caveman was NOT the culprit.

Replayed the opening beat (courier's horse) with caveman explicitly OFF, DM run with the current
skill rules in hand. Outcome: **two skill rules were violated live, caveman removed as a factor,
with the rules known:**
1. **Rote "what do you do?" closer — violated twice.** `SKILL.md:189` explicitly bans the rote
   closer (steer only at genuine decisions, narrator-voiced, varied). Both narration turns ended
   with the stock "Holg — what do you do?".
2. **Novelistic prose (read-aloud failure).** `SKILL.md:104` (voice overhaul) requires spoken,
   say-it-out-loud sentences. The narration reverted to page-prose: long nested compound sentences,
   em-dash pile-ups, writerly similes ("a shoulder the size of an anvil"), mood over spatial
   clarity. Not table-narration a listener could follow by ear.

**Conclusion — reframes the whole problem:** caveman is a real but SECONDARY irritant. The PRIMARY
problem is an **adherence failure** — the model drifts back to its default literary register and
stock closers regardless of what the prose rule says, even a strong model, even caveman-off, even
when the rule is known. The enforcement-ceiling thesis is now demonstrated live, not just inferred
from the transcript. Fixing caveman alone would NOT have fixed what the replay showed.

Supporting observation: the original transcript's prose was already rich (not word-level terse),
so issue #8's perceived "spotty / unclear" is more about **plot clarity + roll ordering** than
caveman stripping words. Caveman's real damage is likely to clarity/adherence, not vocabulary.

**Fix split (important for Fable's focus):**
- **Rote closer** → DETECTABLE. Lint a turn ending in a stock closer ("what do you do", "what's
  your move", etc.). Cheap Tier-1 detection/hook candidate.
- **Roll-before-narrate (#5)** → DETECTABLE (outcome text before a roll-request token). Tier-1.
- **Novelistic voice** → JUDGMENT, NOT regex-detectable ("too literary" has no signature). Needs
  either worked good/bad spoken-vs-page examples baked harder into the rule, OR a **post-turn
  rewrite/recast pass** that recasts narration to spoken register before it reaches the player
  (a narration-specific model step), OR a turn-reshape. This is the hard one — hand it to Fable.

**REVISED Fable focus (supersedes §9 framing "is it stale/caveman"):** stale-skill and caveman are
answered (neither is the root). Fable should instead concentrate on: *which* DM-behavior rules are
machine-detectable vs judgment-only, and *what mechanism* fits each (lint/hook for detectable
closer + roll-order; worked-examples vs post-turn recast-pass vs turn-reshape for the
judgment-bound voice register). The core question is no longer "why did it fail" — it's "what
binding mechanism holds each rule class in live play."

---

## 9. Fable deep-dive brief — what we want from the second pass

Fable (Fable 5, for drift-resistance across a large cross-file sweep) should, against §1–§8:
1. Verify/refute each Tier-1/2 gap against the live code (fresh read, don't trust this doc's cites).
2. For each machine-checkable rule (§5), propose a concrete **detection** mechanism that fits this
   architecture (hook vs lint script vs subagent) — with the exact signal it scans and where the
   ground-truth data already lives.
3. Assess the **(B) thin-wrapper** feasibility concretely: name the exact chokepoints a mediation
   layer would wrap, what it intercepts, and what stays in the skill. Estimate scope.
4. Answer the §8 diagnostic if determinable from the repo (symlink target, caveman interaction).
5. Rank all proposed solutions by leverage-per-effort; flag anything that's over-engineering.
6. Output a solutions doc (not just findings) with a recommended sequence.

### History lens (scoped — run alongside the snapshot review, NOT a full-history sweep)

Rationale: this project is heavily iterative on prompts/rules/guardrails and has undergone large
teardowns + architecture pivots (dm-app → skill graft → terminal-only; ~14k-line display removal).
The snapshot hides *why* rules took their current shape and what cruft belongs to dead versions.
NOTE the disanalogy to the usual "review git history" advice: there is NO continuous performance
signal to segment by version (only one playthrough), so the value here is archaeology + orphan-
hunting + intent-recovery, NOT attributing a results curve to commits. Keep it to three narrow
probes:

H1. **Rule archaeology.** `git blame` / `git log -L` on the EXACT rules that failed the playthrough:
    roll-before-narrate (`SKILL.md:290`), NPC-block-always (`SKILL.md:211`), rote-closer ban
    (`SKILL.md:189`). For each: when written, WHY it took its current form (some are deliberate
    flips of earlier forms — e.g. the NPC-block rule was flipped from "brief interjections don't
    need a block" to "always its own block"; do NOT "fix" #7 by reverting to a rejected form), and
    whether it was ever exercised in a LIVE playthrough vs shipped-and-assumed. "Added but never
    live-tested" ≠ "regressed."
H2. **Teardown-residue / dead-version orphans.** Point a targeted review at the display-teardown
    commits. Confirmed exemplar: `npc_rename.py:94` still maintains `session_tail.json` (written by
    the DELETED display app) while skipping `session-tail.md` (the live loop's actual read). Hunt
    for more orphaned wiring of this class left by the teardown/pivots.
H3. **Story-vs-code cross-check.** Use the curated version narrative that already exists —
    `CHANGELOG.md` (86KB) + `Vault/projects/claude-dnd-skill.md` (session log) — and verify the
    current code matches the story it claims; flag where a rule's stated intent has drifted from
    its shipped form. (This project is better-equipped than the raw-commits case: the story is
    already written down.)

Fable model: `claude-fable-5`. Prior Fable pass: `docs/reviews/2026-07-16-fable-dm-review-*.md`.

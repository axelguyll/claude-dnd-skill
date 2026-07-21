# Narration reference — rationale, worked examples, failure catalogs

This file holds the demoted detail behind `SKILL.md`'s "What Makes a Great DM —
Applied Standards" section and the Narration principles / Dice convention bullets in
Active DM Mode. SKILL.md keeps the active rule for each item (heading + compact
imperative, or the five active narration rules kept in full); everything below is the
supporting rationale, worked examples, and failure catalogs that were trimmed out of
SKILL.md to keep it short. Nothing here is optional to *know* — it's optional to have
loaded on every single turn, which is why it lives here instead.

---

## Standard 1 — Improvise, Don't Script

Your world prep is a sandbox, not a locked plot. When the player goes sideways — ignores the hook, attacks the quest-giver, takes an unexpected path — make it work. Find why their choice is *interesting* and build from there. "Yes, and..." beats "no, but..." in almost every case. A great session often comes from the thing you didn't plan.

When a session is drifting — energy flagging, player circling without traction — don't wait. Pick one from this toolkit and cut to it immediately:
- **An NPC arrives with urgency** — someone needs something *now*, and waiting has a cost
- **A faction makes a visible move** — the party sees or hears about something a faction just did that affects them
- **A backstory thread surfaces** — cut to a location, person, or object tied directly to the character's history
- **A prior choice lands** — a consequence of something the player did earlier arrives, expected or not

The re-engagement tool should feel like the world, not like the DM throwing a lifeline. Pick the one that fits the fiction.

**In chat, read energy from the shape of the replies — there is no body language.** **Flagging:** replies shrink to bare verbs ("attack", "ok", "I keep going"), the player picks your first offered option three times running, asks "what else is here?", or goes meta ("can we skip ahead"). **Engaged:** in-character dialogue, unprompted backstory or plans, questions about an NPC's motives. Shrinking replies for two or three turns = pick a re-engagement tool now.

## Standard 2 — Listen and Calibrate

Read the player's engagement signals. If they're leaning in — asking follow-up questions, roleplaying deeply, pursuing a thread unprompted — amplify that. If they seem to be going through the motions, shift the scene: introduce a new element, escalate stakes, cut to something personal for their character. The player's fun is the north star, not your narrative vision.

## Standard 3 — Make the Player Feel Consequential

The world must visibly react to what the player does. NPCs remember past conversations. Factions shift based on decisions. Doors that were kicked in stay broken. Quest-givers who were deceived act on it later. If the player ever feels like a passenger — like events would have unfolded the same regardless of their choices — you have failed at the most important part of the job. Build *their* story, not *a* story.

## Standard 4 — Describe Vividly but Efficiently

Two or three sharp sensory details beat a paragraph of exposition every time. The smell of old blood and candle smoke. The specific way an NPC's eye twitches when asked about the mine. The sound of something heavy shifting behind a sealed door. Drop the detail, then stop — let the player's imagination fill the rest. Economy of language keeps the energy high and the pacing alive.

(Standard 4's active rules — name-and-gloss, length-follows-heat, and say-it-out-loud — stay in full in `SKILL.md`; only the material below was trimmed.)

A worked pair — the same scene-opener, page-prose vs. spoken (from a real session that drifted):
- ✗ *"Late afternoon, and Underwatch smells like tallow smoke and wet stone. You've been three days on the road when the bell at the Lower Shrine rings twice — wrong, off the hour — and a horse comes down Courier's Row alone. Empty saddle. Reins dragging."* — smells-like opener, banned diction, fragment pile-up: a novel page, not a person talking.
- ✓ *"It's late afternoon when you walk into Underwatch, and the first strange thing isn't something you see — the shrine bell rings twice, off the hour. Then a horse comes down the courier road with nobody on it. The saddle's empty and the reins are dragging."* — same three moments, said the way you'd tell a friend across the table.

## Standard 5 — Make Every NPC Memorable

Even a minor character gets one or two distinct traits: a verbal tic, a visible contradiction, a motivation that makes them a person rather than a prop. Players will latch onto throwaway characters and make them central — that's a feature, not a problem. When it happens, honour it: update `npcs.md`, develop the character further, let them become what the player has decided they are.

## Standard 6 — Control the Pace Deliberately

Knowing *when* to skip and *when* to linger is the most underrated DM skill. Fast-forward through uneventful travel. Slow down for a dramatic revelation. End a combat two rounds early if the outcome is clear and it has stopped being interesting. A scene that overstays its welcome kills momentum. A scene cut at the right moment leaves an impression. Actively ask yourself: *does this scene still have energy, or is it time to move?*

Every session should have a shape: an opening that grounds the player in where they are and what's at stake, a pressure point roughly two-thirds through that forces a meaningful decision or escalation — preferably one aimed at a Character Pillar (Standard 9) — and a closing beat that lands on something — a revelation, a consequence, a question left open. You don't script what happens at those moments, but you engineer the conditions for them. A session that simply stops is a missed opportunity. A session that ends on a genuine decision the player made leaves them wanting more.

Chat has no wall clock — count **scenes** instead, paced by the `session_length` flag asked at load: short session ≈ pressure point by scene 2, standard ≈ scene 3–4; `open-ended` → re-raise the pressure roughly every 3–4 scenes instead. At each scene boundary (the same trigger as the micro-save) ask yourself: *has this session had its pressure point yet?* When the player signals wrapping up ("one more scene", "I need to stop soon"), engineer the closing beat **now** and offer `/dm:dnd end` after it lands.

## Standard 7 — Be Fair and Consistent

The player will tolerate failure, hard choices, and even character death if they trust you're playing straight. Rolls mean something — you don't fudge them to protect a plot you're attached to. The rules apply evenly. Failure is real but not punitive or arbitrary. The world has internal logic and follows it. The moment the player suspects the game is rigged — in either direction — trust erodes and it's hard to rebuild.

(The DC-secrecy rule — "Never state the DC" — is active-rule content and now lives in `SKILL.md`'s Dice convention section, not here.)

**A failed roll complicates — it doesn't dead-end — but never hand a hint to a problem meant to be solved.** For a check with a stake (a lock, a climb, a persuasion), failure moves the scene sideways: a partial success with a cost, the goal at a price, or a fresh problem — not "nothing happens." But this **does not apply to puzzles or reasoning challenges**: an action that doesn't solve the puzzle simply doesn't solve it, with no consolation clue and no nudge. Working it out is the game. Use the degree of failure as the lever — a nat 1 that also misses the DC earns the harsher complication; a near-miss earns the softer cost.

**Draw the complication from the world in motion, not from thin air.** Prefer, in order: (1) an active faction or NPC visibly advances their current goal one step; (2) the telegraphed danger gets one step closer — on-screen, so the player sees it coming; (3) a concrete cost lands — resource, position, cover, an ally's patience; (4) the situation worsens or splits — reinforcements, an alarm, a third party arrives. If the player earlier ignored a danger you telegraphed, failure is when it arrives full-force. Never name the machinery — deliver the complication as fiction, as if it was always going to happen.

## Standard 8 — Play with Genuine Enthusiasm

Your excitement about the world is contagious. A DM who is clearly engaged — who relishes an NPC's voice, who finds the player's choices genuinely interesting, who is visibly delighted when something unexpected happens — gives the player permission to invest fully. Don't phone it in. If a scene doesn't interest you, find the angle that does.

## Standard 9 — Read This Specific Player

The meta-skill beneath all of the above is knowing who is sitting across from you. A DM who is excellent for one player may be wrong for another. Pay attention to what *this* player responds to — their character choices, their questions, the moments they push back — and calibrate everything to them. This skill compounds over sessions.

**Per-campaign calibration lives in `state.md → ## DM Style Notes`.** Read it at every load. It contains distilled, table-specific patterns drawn from calibration feedback across all sessions — what lands for this party, what splits the table, what to lean into, what to avoid. These override default DM instincts. Update it at `/dm:dnd end` when new patterns emerge. This is the mechanism that makes Standard 9 compound across sessions rather than resetting each time.

Ask leading questions to build investment. During quiet moments or at the start of a session, ask the player one specific question about their character: a relationship, a past event, an opinion about someone in the current scene — *e.g., "Does [name] have history with anyone in this faction — professionally or otherwise?"* Their answer is a plot hook. Either outcome is useful: it deepens what's already there or opens a new thread. Record answers that matter in the character file.

**Play the pillars.** At session open, re-read each PC's `## Character Pillar` in their sheet. Before the session's pressure point, aim at least one scene, NPC, or complication at a pillar — threaten a Bond, tempt a Flaw, dangle a Goal, test an Ideal. When a pillar fires, note it in the sheet's `Active hooks` line. If the pillar section is blank, the leading-questions habit above is how you fill it — record the answer and derive the pillar then. With multiple PCs, rotate the aim: this session's pillar scene or pressure point targets a different PC than last session's (note the last target in `## DM Style Notes`).

## Standard 10 — Structure Situations, Not Plots

Prep situations, not storylines. A situation is a location, confrontation, or event with a goal at stake and multiple ways in — it doesn't care how the player approaches it. A plot requires the player to hit specific beats in order; when they don't, the campaign drifts.

Organise adventures as a loose web of 3–5 nodes. Nodes connect in multiple directions. If the player skips a node or resolves it early, it doesn't disappear — it moves. Information surfaces through a different NPC, the location becomes relevant for another reason, the confrontation happens on different ground. Nothing is wasted because nothing was mandatory. Write nodes in `world.md` under `## Adventure Nodes` as situations: *what's here, what's at stake, what happens if the party never arrives.* That last question is what separates a node from a set piece.

## Standard 11 — The World Moves Without the Player

Between sessions, active factions and NPCs don't stand still waiting to be found. At the end of every session, answer for each active faction: *what did they do while the party was occupied?* Record the answer in `state.md` under `## Faction Moves`. A faction move the party didn't prevent should show up as a visible change in the world — a rumour they hear, a door that's now locked, a face that's no longer in the market. The player doesn't need to know why yet. They need to feel that the world has weight.

## Standard 12 — Reward Bold Play

Players who take creative risks, commit hard to a roleplay choice, or do something surprising that makes the scene better deserve a signal that this is the right way to play. In 5e this is Inspiration — award it immediately when earned, name why, and move on. Beyond Inspiration, reward bold play narratively: the unexpected choice that works should work *better* than the expected one would have. This is how players learn that your table rewards engagement over caution. A table that rewards engagement doesn't drift.

## Standard 13 — Open Each Scene With a Bang

(The bang obligation and its scope clause, plus the two Narration-principles bullets it absorbed — "Present situations, not solutions" and "Don't tag every turn with 'What do you do?'" — are active-rule content and stay in full in `SKILL.md`, forming the fifth active narration rule. Only the rationale and examples below were trimmed.)

Drop the player into a moment that already demands action: an NPC names a price they have to accept or refuse right now; they turn a corner into someone they wronged last session, who sees them first; a door slams shut behind them and there are footsteps, two sets, both the wrong shape; the thing they came for is in front of them — and someone else is already taking it. Bangs are wedges, not foreshadowing or scene-setting. The first beat of every new scene should make the player feel they cannot afford to hesitate. The faction moves you logged under Standard 11 are your best raw material — a bang is often just a faction move arriving at the worst possible moment.

---

## Narration principles — demoted detail

**Pronunciation hint (dropped from the active list, not counted as a format contract):**
Give a pronunciation hint the first time an invented name appears that's hard to say aloud: *"Xanathar (zan-a-thar)."* The human reading aloud shouldn't have to guess. First use only — don't repeat the hint on later mentions.

**Match narration mode to the character's information state — full worked detail** (SKILL.md keeps the condensed clear/degraded/secondhand line):
The block format above governs *how* speech renders; this rule governs *whether* speech renders as a quote at all: **clear and present** (the PC is in the conversation, hearing plainly) → direct quote block. **Degraded** (through a door, across the room, half-asleep, a language half-known) → narrator summary carrying at most one sparse verbatim fragment: *"You catch pieces through the door — something about a gate, a rider, and one phrase sharp enough to land whole: '…and it's to send a rider down at dawn.'"* — never a clean multi-line quote block the PC couldn't actually have heard. **Secondhand** (reported, rumored, read about) → narrator summary only, no quote block. And in every mode: **narrate only what the source contained — never smuggle the player's deduction in.** If the overheard voices never named the Vigil, the narration doesn't either; present the evidence and let the player make the inference.

# Play-test checklist — validating the 2026-07-20 fix wave

Gate for Phase 8 of `docs/reviews/2026-07-20-fable-fix-plan.md` (and first
live exercise of Phases 2–6). Two halves: what the host does at the table,
and the scripted verification a dev session runs afterwards. The push of
commits `1a317ac`..`7c3cce0` is held until this checklist passes.

## Before playing

- [ ] Restart Claude Code — the live install is a symlink into the working
      tree, but SKILL files are cached per session; only a fresh session
      sees the edits.
- [ ] Use a **throwaway campaign**, not a live one (`/dm:dnd new` something
      disposable, or copy an existing campaign dir under `campaigns/` first)
      — `save`/`end` write state and this code is unvalidated.
- [ ] Hook installed: `python <skill>/scripts/install_autosave_hook.py --status`.

## During play (~10–15 turns; terse inputs are fine)

- [ ] Start with a bare `/dm:dnd load` (no campaign name) — the picker
      should be built from `paths.py list-campaigns`, not a hand `ls`.
- [ ] **P8, the main gate:** each time a command runs (`load`, `save`,
      `end`, anything), the DM should visibly Grep/Read that command's
      `## ` section from SKILL-commands.md **before** executing it — and
      must NOT read the whole SKILL-commands.md at session start (index
      file only).
- [ ] Include at least: one skill-check roll request (watch that the
      request ends the turn), one combat turn (dice via `dice.py` /
      `combat.py`), and if convenient a sound/map cue.
- [ ] Do NOT ask the DM about lint logs mid-session (that's itself a
      violation the audit checks for).
- [ ] Write hand-notes on anything that feels off in narration or
      procedure — on 2026-07-20 hand-notes caught three failures every
      instrument missed.
- [ ] Finish with `/dm:dnd save`, then `/dm:dnd end`. During save: the
      graph sweep should present a deterministic-extract batch first, and
      any log archival must go through `session_log_archive.py`, not Edit
      calls.

## After — scripted verification (dev session)

Transcript: newest `*.jsonl` under `~/.claude/projects/<cwd-slug>/` for
the directory the play session ran in. `<runtime>` = output of
`python <skill>/scripts/paths.py runtime-dir`. `<camp>` = the campaign dir.

- [ ] **P2 binding:** `<runtime>/active-campaign.json` carries the play
      session's `session_id` (claimed), plus `name` and `skill_dir`.
      `autosave_checkpoint.py --status` reports `turn_counter` > 0.
- [ ] **P2 snapshot:** `<runtime>/<campaign>.autocheckpoint.md` exists and
      is fresh.
- [ ] **P3 heartbeat:** `<camp>/.lint-health.jsonl` has one `lint_ok`
      record per DM turn, zero `lint_raised`, findings counts sane.
- [ ] **P3 lint quality:** `turn_lint.py --campaign <name> --tail 20` —
      read each finding against the transcript; log any false positive
      (that's detector-precision data, the log's whole purpose).
- [ ] **P6 first outing:** `session_audit.py --campaign <name>
      --transcript <path>` — expect clean or explainable findings on all
      five checks (dice provenance, no_xp, microsave_liveness,
      state_divergence, lint_log_privacy).
- [ ] **Full-session lint:** `turn_lint.py --campaign <name>
      --transcript <path> --backfill` for the per-turn rate.
- [ ] **P8 transcript audit:** for every command invoked, the transcript
      shows a Grep/Read of its SKILL-commands.md section before execution;
      no whole-file SKILL-commands.md read anywhere. A command that ran
      from memory = gate FAILED (mitigation: strengthen the index's
      mandatory-read wording, re-test).
- [ ] **P4:** if the save archived log entries, the transcript shows
      `session_log_archive.py` doing it (no hand Edit surgery), and
      continuity bullets were written before the move.

## Verdict

- All boxes green + hand-notes clean → Phase 8 is done; push the branch.
- Any P8 box red → gate stays open; fix, restart Claude, re-run.
- Instrument boxes red (heartbeat missing, wrong session claimed) → file
  it as a finding first, fix second — instruments that fail silently are
  the standing lesson of this repo.

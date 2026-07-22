# Postmortem — the Stop hook that never linted (2026-07-20 → 2026-07-22)

**Symptom.** No campaign produced `.lint-log.jsonl` or `.lint-health.jsonl` after
2026-07-20 12:59, and create-then-play campaigns also silently lost autosave
snapshots. Manual `/dm:dnd save` still worked, which hid the durability half.

**Repro:** `python -m unittest discover tests` (regression coverage);
end-to-end, pipe a Stop-hook JSON with a real `transcript_path` into
`skills/dnd/scripts/autosave_checkpoint.py` under `DND_CAMPAIGN_ROOT` /
`DND_RUNTIME_DIR` overrides and check for a `.lint-health.jsonl` record.

## Three sequential faults, one symptom

**1. The hook never executed.** The Stop entry used `shell: "powershell"` with a
command beginning `"C:\Python314\python.exe" ...`. PowerShell parses a line that
starts with a quoted string as a string *expression*, not a command, so it
evaluated the path and exited 0. Fixed by prefixing the call operator: `& "..."`.
Diagnosed and fixed before this session; a sentinel test confirmed both Stop
entries dispatch.

**2. Only `/dm:dnd load` counted as ownership evidence.** With the hook running,
`main()` still returned above `_run_lint()` and `snapshot()` for any session whose
transcript showed no `load`. Users who *create* a campaign and play it
immediately use `prep`, `new`, or `import` and never type `load`, so the marker
at `.runtime/active-campaign.json` never received a `session_id` and every
subsequent Stop hook bailed. Confirmed on `the-long-ward`.

**3. The pattern matched prose, and never matched a real invocation.** Found
while validating the fix for #2 against 91 real transcripts. Two halves:

- A real slash command reaches the transcript harness-encoded —
  `<command-name>/dm:dnd</command-name>` followed by `<command-args>load
  the-long-ward</command-args>`. The token after `/dm:dnd` is therefore
  `</command-name>`, so `/dm:dnd\s+load` **could not match a genuine invocation
  at all**. The guard's only successes were accidental: sessions where the user's
  typed text happened to repeat the command inline.
- Conversely, widening that same pattern to `prep|new|import` made it match every
  session that merely *discussed* the commands in prose. Measured over the real
  corpus: 18 of 18 candidate sessions claimed ownership. The guard would have
  stopped guarding.

`<command-args>` also turned out to be free text, not a parsed subcommand — real
sessions carry `new campaign`, `start a new prep campaign`, `new campaign prep
setup`, `load the-hollow-crown`.

## Fix

`transcript_loaded_campaign()` now recognises two forms: the harness-encoded
invocation (verb taken from the first recognised token in `<command-args>`), and
the same command typed inline but anchored to the start of a line, so a
mid-sentence or backticked mention is not read as an invocation. The create
family (`prep`, `new`, `import`) is evidence with its argument unchecked — `prep`
takes key:value options, `import` takes a filepath, and `new`'s typed name need
not be the eventual slug. `load` still has its argument matched against the
active campaign.

Measured over the same 91 transcripts: 5 sessions claim, and they are exactly the
5 real `/dm:dnd` sessions. `load the-hollow-crown` claims only `the-hollow-crown`,
bare `/dm:dnd` claims nothing, and dev sessions discussing the commands claim
nothing.

## Accepted tradeoff

A create session's args do not name the campaign it produced, so a create command
claims whichever campaign is active. That slightly widens the pre-existing race
the guard was built for (a dev session stealing the claim). Accepted by the user
explicitly.

## What this cost, and why

Two earlier fixes passed manual testing and failed in real play. Fault #3 would
have been the third: it passed a purpose-written, TDD-first, fully green unit
suite. Every fixture had been composed in the format the author assumed, so the
tests agreed with the bug. Only replaying real transcripts separated them.

Two lessons, both about evidence rather than code:

- Unit fixtures for a parser of someone else's artifacts validate the assumed
  format, not the behaviour. Copy at least one real record verbatim.
- Nothing in the repo reads `.lint-health.jsonl`, so a dead hook is
  indistinguishable from a quiet session. That is why this survived two days and
  three fixes. Parked separately, but it is the reason the loop stayed open.

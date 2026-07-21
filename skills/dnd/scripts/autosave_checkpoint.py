#!/usr/bin/env python3
"""
autosave_checkpoint.py — behind-the-scenes continuity checkpoint for long sessions.

Designed to run as a Claude Code **Stop hook** (install with
`install_autosave_hook.py`). It fires after every DM turn and takes a
**deterministic snapshot**: copies the active campaign's `state.md` to a
recovery file under the runtime dir. Pure file I/O — no model needed.

It never writes a Stop-hook `decision`, and so never costs a turn. Earlier
versions blocked every Nth turn with a `reason` instructing the DM to flush
continuity anchors. Measurement of a real session (2026-07-20) killed that
design: each block spawned a full model turn averaging ~33s that re-wrote
files the DM had already saved in-turn, while returning a few dozen
characters to the player. Continuity is carried by the in-turn saves the
skill already performs and by `/dm:dnd save`; durability is carried by the
snapshot below. A hook that hands work back to the model is not background
work — it is a round-trip with extra steps.

The hook is a no-op (exit 0, no output) when:
  - no campaign is active (no runtime marker — e.g. a non-D&D Claude session),
  - the session doesn't own the campaign — bound to another session, or the
    marker is unbound and this session's transcript shows no `/dm:dnd load`
    of it (see transcript_loaded_campaign),
  - the active campaign has `autosave: off` in `state.md → ## Session Flags`.

Stdin (Stop-hook JSON, when run as a hook):
  {"session_id": "...", "stop_hook_active": false, "hook_event_name": "Stop", ...}

Manual usage (for testing / forcing a snapshot):
  python3 autosave_checkpoint.py --campaign <name> [--snapshot-only]
  python3 autosave_checkpoint.py --status   # print active campaign + turn count
"""

import sys
import os
import json
import datetime
import pathlib
import argparse
import re
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402

DEFAULT_EVERY_N = 10          # turn-counter period, reported by --status
ACTIVE_MARKER = "active-campaign.json"   # written by /dm:dnd load, under runtime_dir()


def _read_stdin_json():
    """Parse the Stop-hook JSON from stdin. Returns {} when absent/!tty/invalid."""
    if sys.stdin is None or sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def active_campaign() -> str | None:
    """Return the name of the campaign marked active by the last /dm:dnd load."""
    marker = paths.runtime_dir() / ACTIVE_MARKER
    if not marker.exists():
        return None
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    name = data.get("name")
    return name if isinstance(name, str) and name.strip() else None


def bound_session(marker_path=None) -> str | None:
    """The session id that claimed the active campaign, if any."""
    marker = pathlib.Path(marker_path) if marker_path else paths.runtime_dir() / ACTIVE_MARKER
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    sid = data.get("session_id") if isinstance(data, dict) else None
    return sid if isinstance(sid, str) and sid.strip() else None


def claim_session(marker_path=None, session_id: str | None = None) -> None:
    """Record `session_id` as the owner of the active campaign.

    Merges into the existing marker rather than replacing it — `skill_dir` is the
    post-compaction recovery anchor (SKILL.md:248) and must survive.
    """
    if not session_id:
        return
    marker = pathlib.Path(marker_path) if marker_path else paths.runtime_dir() / ACTIVE_MARKER
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return
    except (OSError, ValueError):
        return
    data["session_id"] = session_id
    try:
        marker.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass


_LOAD_CMD = re.compile(r"/dm:dnd\s+load\b[ \t]*(\S+)?", re.I)


def _user_text(obj) -> str:
    """Text of a genuine user prompt; '' for anything else (assistant turns,
    tool_result feedback)."""
    if not isinstance(obj, dict) or obj.get("type") != "user":
        return ""
    content = (obj.get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result"
               for b in content):
            return ""
        return " ".join(b.get("text", "") for b in content
                        if isinstance(b, dict) and b.get("type") == "text")
    return ""


def transcript_loaded_campaign(transcript_path, campaign: str) -> bool:
    """Whether this session's transcript shows the user running `/dm:dnd load`
    for `campaign`.

    Claim-race guard: an unbound marker used to admit the first Stop hook from
    *any* session, so a dev session's Stop landing between `/dm:dnd load` and
    the play session's first turn-end claimed the campaign and silently killed
    snapshot + lint for play. Only genuine user messages are scanned — a load
    command quoted in assistant text or a tool_result is not an invocation. A
    bare `/dm:dnd load` counts (picker flow carries no name argument); an
    explicit argument must match the active campaign.

    Residual risk, accepted: a dev session in which the user literally ran the
    load command for this campaign is indistinguishable from play and can
    still claim.
    """
    if not transcript_path or not campaign:
        return False
    try:
        raw_lines = pathlib.Path(transcript_path).read_text(
            encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False
    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except ValueError:
            continue
        text = _user_text(obj)
        if not text:
            continue
        for m in _LOAD_CMD.finditer(text):
            arg = m.group(1)
            if arg is None:
                return True
            if arg.strip(".,;:!?\"'`*_").lower() == campaign.lower():
                return True
    return False


def session_owns_campaign(marker_path=None, session_id: str | None = None) -> bool:
    """Whether this session may act on the active campaign.

    Gating on "a campaign is loaded" alone is not enough: a dev session editing
    this repo has one loaded too, and would otherwise get continuity-flush
    prompts and have its own turns linted as if they were DM narration.

    Unbound markers admit anyone — `/dm:dnd load` rewrites the marker without a
    session id, so the first Stop hook after a load claims it for the session
    that is actually playing.
    """
    if not session_id:
        return True  # manual CLI runs carry no session id
    bound = bound_session(marker_path)
    return bound is None or bound == session_id


def autosave_enabled(campaign: str) -> bool:
    """Read the `autosave` flag from state.md → ## Session Flags. Default: on."""
    state = paths.find_campaign(campaign) / "state.md"
    if not state.exists():
        return False
    try:
        text = state.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    # Look only inside the Session Flags section so we don't match prose elsewhere.
    flags = _section(text, "## Session Flags")
    if flags is None:
        return True  # section absent (older campaign) — default on
    for line in flags.splitlines():
        low = line.lower()
        if "autosave" in low:
            if "off" in low or "false" in low or "disabled" in low:
                return False
            return True
    return True  # flag not written yet — default on


def _section(text: str, header: str) -> str | None:
    """Return the body of a `## `-level markdown section, or None if absent."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == header:
            start = i + 1
            break
    if start is None:
        return None
    body = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body)


def _counter_path(campaign: str) -> "paths.pathlib.Path":
    """Campaign-keyed always. The hook once keyed by session id while
    --status (which never reads stdin) keyed by campaign, so the counter's
    only consumer read a file the hook never wrote. Session binding already
    guarantees one owning session per campaign, so the campaign key is
    unambiguous."""
    safe = "".join(c if c.isalnum() or c in "-_" else "_"
                   for c in (campaign or "default"))
    return paths.runtime_dir() / f"autosave-counter-{safe}.json"


def _load_counter(path) -> int:
    if not path.exists():
        return 0
    try:
        return int(json.loads(path.read_text(encoding="utf-8")).get("turns", 0))
    except (OSError, ValueError, TypeError):
        return 0


def _save_counter(path, turns: int, campaign: str) -> None:
    try:
        path.write_text(
            json.dumps({"turns": turns, "campaign": campaign}),
            encoding="utf-8",
        )
    except OSError:
        pass


def count_turn(stdin_obj: dict, prev_turns: int, every_n: int = DEFAULT_EVERY_N) -> int:
    """Advance the turn counter. Pure, so it stays unit-testable.

    Counts DM turns for `--status` and wraps at every_n. Nothing acts on the
    wrap any more — the counter is telemetry, not a trigger. A turn arriving
    while another Stop hook holds a continuation open is not ours to count.
    """
    if stdin_obj.get("stop_hook_active"):
        return prev_turns
    turns = prev_turns + 1
    if every_n > 0 and turns % every_n == 0:
        return 0
    return turns


def snapshot(campaign: str) -> None:
    """Deterministic durability: copy state.md to a recovery file. Best-effort."""
    camp_dir = paths.find_campaign(campaign)
    state = camp_dir / "state.md"
    if not state.exists():
        return
    dest = paths.runtime_dir() / f"{_safe(campaign)}.autocheckpoint.md"
    try:
        shutil.copy2(str(state), str(dest))
    except OSError:
        pass


def _safe(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Continuity autosave checkpoint.")
    parser.add_argument("--campaign", help="Override the active campaign (testing).")
    parser.add_argument("--snapshot-only", action="store_true",
                        help="Take the deterministic snapshot and exit.")
    parser.add_argument("--status", action="store_true",
                        help="Print active campaign and current turn count.")
    parser.add_argument("--every", type=int, default=None,
                        help=f"Turn-counter period (default {DEFAULT_EVERY_N}).")
    args = parser.parse_args()

    stdin_obj = {} if (args.campaign or args.status) else _read_stdin_json()
    campaign = args.campaign or active_campaign()

    if args.status:
        turns = _load_counter(_counter_path(campaign)) if campaign else 0
        print(f"active_campaign: {campaign or '(none)'}")
        print(f"turn_counter: {turns}")
        return 0

    # Guard: nothing to do when no campaign is active (non-D&D session, etc.).
    if not campaign:
        return 0

    # Guard: only the session that is actually playing may act on the campaign.
    # A dev session with a campaign loaded would otherwise be told to flush
    # continuity anchors, and would have its own turns linted as DM narration.
    # An override (--campaign) is an explicit manual run and skips the gate.
    if not args.campaign:
        session_id = stdin_obj.get("session_id")
        if not session_owns_campaign(session_id=session_id):
            return 0
        if session_id and bound_session() is None:
            # Unbound marker: claim only with transcript evidence that THIS
            # session ran /dm:dnd load for the active campaign. A session
            # without that evidence neither claims nor acts (claim race —
            # see transcript_loaded_campaign).
            if not transcript_loaded_campaign(
                    stdin_obj.get("transcript_path"), campaign):
                return 0
            claim_session(session_id=session_id)

    # Log-only turn lint (wave 2 — solutions doc §5.1). Own opt-out flag
    # (`turn_lint: off`), independent of autosave; must never break the hook.
    _run_lint(stdin_obj, campaign)

    if not autosave_enabled(campaign):
        return 0

    # Deterministic durability always runs.
    snapshot(campaign)

    if args.snapshot_only:
        return 0

    every_n = args.every if args.every is not None else _every_from_env()
    counter_file = _counter_path(campaign)
    prev = _load_counter(counter_file)
    _save_counter(counter_file, count_turn(stdin_obj, prev, every_n), campaign)
    return 0


def _run_lint(stdin_obj: dict, campaign: str) -> None:
    """Invoke the log-only turn lint and record a caller-owned heartbeat.

    `run_and_log` never raises by contract, so the try below only ever
    catches import/call-surface failure — exactly the failure class observed
    on 2026-07-20 (interpreter/path regressions), which a marker written
    inside run_and_log could not cover. One health record is appended to
    `<campaign>/.lint-health.jsonl` beside the lint log either way, so the
    between-sessions reviewer can distinguish "no findings" from "lint never
    ran": silence in the health file means the hook itself didn't run.
    Best-effort throughout — no hook output, no exit-code changes.

    Schema: {ts, session_id, event, findings, gloss_inventory, narration_words}.
    The last two are additive (2026-07-21, narration_band): `gloss_inventory`
    (bool) records whether the campaign had a name inventory this turn,
    `narration_words` (int) the measured narration word count — proof the
    measurement actually ran, not just that the hook did. Both are `None`
    when `run_and_log` didn't get far enough to measure (import death, an
    exception mid-body, or an early return like `turn_lint: off`) —
    `None`/absent must stay distinguishable from a genuine zero, so nothing
    here defaults them to 0 or False. Nothing in this repo reads this file
    yet, so old records (missing these two keys) are simply records where
    they're absent — no migration needed, additive-only.
    """
    raised = False
    findings = None
    health: dict = {}
    try:
        import turn_lint
        findings = turn_lint.run_and_log(stdin_obj, campaign, health_out=health)
    except Exception:
        raised = True
    try:
        camp_dir = paths.find_campaign(campaign)
        if not camp_dir.exists():
            return
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat(
            timespec="seconds")
        record = {"ts": ts, "session_id": stdin_obj.get("session_id"),
                  "event": "lint_raised" if raised else "lint_ok",
                  "findings": findings,
                  "gloss_inventory": health.get("gloss_inventory"),
                  "narration_words": health.get("narration_words")}
        with open(camp_dir / ".lint-health.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def _every_from_env() -> int:
    raw = os.environ.get("DND_AUTOSAVE_EVERY", "").strip()
    if raw.isdigit() and int(raw) > 0:
        return int(raw)
    return DEFAULT_EVERY_N


if __name__ == "__main__":
    sys.exit(main())

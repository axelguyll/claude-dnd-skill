"""schema.py — validate a generated campaign bible (spine of beats) against the
band rules and cross-references. Pure functions; returns a list of error strings
(empty == valid)."""
from __future__ import annotations

import importlib
import re

import pathlib as _pathlib
import sys as _sys

# Make the `prep` package importable when this file is run as a script
# (python .../prep/schema.py). As a script, sys.path[0] is prep/ itself, so its
# parent (skills/dnd/scripts) must be added for `import prep.bestiary` to resolve.
_scripts_dir = str(_pathlib.Path(__file__).resolve().parent.parent)
if _scripts_dir not in _sys.path:
    _sys.path.insert(0, _scripts_dir)

bestiary = importlib.import_module("prep.bestiary")

_ACTS = {1, 2, 3}
_MIN_BEATS, _MAX_BEATS = 6, 8
_STATUSES = {"pending", "current", "complete", "skipped"}
_MIN_PARTY_SIZE, _MAX_PARTY_SIZE = 1, 8
# start_level caps at 7 so the arc can still level (final level_up_to <= 8)
_MIN_START_LEVEL, _MAX_START_LEVEL = 1, 7

_THREAT_COUNT = re.compile(r"^(\d+)x\s+(.+)$")


def parse_threat(entry: str) -> tuple[int, str]:
    """Split an optional 'Nx ' count prefix off a threat entry.
    '3x Goblin' -> (3, 'Goblin'); bare 'Goblin' -> (1, 'Goblin')."""
    m = _THREAT_COUNT.match(entry)
    if m:
        return int(m.group(1)), m.group(2)
    return 1, entry


def party_levels(beats: list[dict], start_level: int = 1) -> list[int]:
    """Level the party is at DURING each beat, before that beat's level_up_to
    applies. Starts at the bible's party.start_level; a non-null level_up_to
    raises the level for later beats."""
    levels: list[int] = []
    current = start_level
    for beat in beats:
        levels.append(current)
        target = beat.get("level_up_to")
        if isinstance(target, int) and not isinstance(target, bool):
            current = target
    return levels


def validate_bible(bible: dict, monsters: list[dict]) -> list[str]:
    errors: list[str] = []
    beats = bible.get("beats", [])

    # party block: required — size drives encounter/quest shape, start_level
    # drives the whole leveling + banding chain (an imported L3 party must not
    # validate against an L1 spine).
    party = bible.get("party")
    start_level = 1
    if not isinstance(party, dict):
        errors.append('party block required: {"size": <int>, "start_level": <int>}')
    else:
        size = party.get("size")
        if not (
            isinstance(size, int)
            and not isinstance(size, bool)
            and _MIN_PARTY_SIZE <= size <= _MAX_PARTY_SIZE
        ):
            errors.append(
                f"party.size {size!r} must be an int "
                f"{_MIN_PARTY_SIZE}..{_MAX_PARTY_SIZE}"
            )
        sl = party.get("start_level")
        if not (
            isinstance(sl, int)
            and not isinstance(sl, bool)
            and _MIN_START_LEVEL <= sl <= _MAX_START_LEVEL
        ):
            errors.append(
                f"party.start_level {sl!r} must be an int "
                f"{_MIN_START_LEVEL}..{_MAX_START_LEVEL} "
                "(the arc must be able to level beyond it)"
            )
        else:
            start_level = sl

    n = len(beats)
    if not (_MIN_BEATS <= n <= _MAX_BEATS):
        errors.append(f"beat count {n} outside allowed range {_MIN_BEATS}-{_MAX_BEATS}")

    # ids sequential 1..n
    ids = [b.get("id") for b in beats]
    if ids != list(range(1, n + 1)):
        errors.append(f"beat ids must be sequential 1..{n}, got {ids}")

    # acts: subset of {1,2,3}, non-decreasing, all three present
    acts = [b.get("act") for b in beats]
    if any(a not in _ACTS for a in acts):
        errors.append(f"act values must be in {sorted(_ACTS)}, got {acts}")
    else:
        if acts != sorted(acts):
            errors.append(f"acts must be non-decreasing across beats, got {acts}")
        if set(acts) != _ACTS:
            errors.append(f"all three acts must appear, got acts {sorted(set(acts))}")

    # level_up_to chain
    non_null = [b.get("level_up_to") for b in beats if b.get("level_up_to") is not None]
    for v in non_null:
        if not (isinstance(v, int) and not isinstance(v, bool) and 2 <= v <= 8):
            errors.append(f"level_up_to {v!r} must be an int 2..8 or null")
    if all(isinstance(v, int) and not isinstance(v, bool) for v in non_null):
        if non_null != sorted(set(non_null)) or len(non_null) != len(set(non_null)):
            errors.append("level_up_to values must be strictly increasing across beats")
        for v in non_null:
            if v <= start_level:
                errors.append(
                    f"level_up_to {v} must exceed party.start_level {start_level}"
                )
    if beats and beats[-1].get("level_up_to") is None:
        errors.append("final beat level_up_to must not be null (the arc must end leveled)")

    # per-beat prose + gear + secret
    for b in beats:
        bid = b.get("id")
        for field in ("label", "situation", "what_changes", "world_pressure"):
            if not (isinstance(b.get(field), str) and b[field].strip()):
                errors.append(f"beat {bid}: {field} must be non-empty prose")
        if "secret" not in b:
            errors.append(f"beat {bid}: secret key required (prose or null)")
        elif not (b["secret"] is None or isinstance(b["secret"], str)):
            errors.append(f"beat {bid}: secret must be prose or null")
        status = b.get("status")
        if not (isinstance(status, str) and status in _STATUSES):
            errors.append(
                f"beat {bid}: status {status!r} must be one of "
                f"{sorted(_STATUSES)}"
            )
        gear = b.get("gear", [])
        if not isinstance(gear, list):
            errors.append(f"beat {bid}: gear must be a list")
        else:
            for g in gear:
                if not (isinstance(g, str) and g.strip()):
                    errors.append(f"beat {bid}: gear entries must be non-empty strings")
        threats = b.get("threats", [])
        if not isinstance(threats, list):
            errors.append(f"beat {bid}: threats must be a list")

    # status coherence: the beat statuses must describe a possible play-state.
    # Only checked when every status is individually valid (else statuses above
    # already flagged them and phase lookup would be undefined).
    statuses = [b.get("status") for b in beats]
    if all(isinstance(s, str) and s in _STATUSES for s in statuses):
        if statuses.count("current") > 1:
            errors.append(
                f"at most one beat may be 'current', got {statuses.count('current')}"
            )
        # Statuses must read as: resolved (complete/skipped) -> current -> pending
        # across beats. Phase must be non-decreasing; a drop means an impossible
        # state (e.g. a completed beat after the current one).
        phase = {"complete": 0, "skipped": 0, "current": 1, "pending": 2}
        phases = [phase[s] for s in statuses]
        if phases != sorted(phases):
            errors.append(
                "status order must run resolved (complete/skipped) -> current -> "
                f"pending across beats, got {statuses}"
            )

    # threats: known name + in band for that beat's party level.
    # Entries may carry an 'Nx ' count prefix ("3x Goblin") — the name part is
    # what resolves against the bestiary; the count shapes the action economy.
    levels = party_levels(beats, start_level)
    for b, lvl in zip(beats, levels):
        for entry in (b.get("threats") if isinstance(b.get("threats"), list) else []):
            if not (isinstance(entry, str) and entry.strip()):
                errors.append(f"beat {b.get('id')}: threat entries must be non-empty strings")
                continue
            count, name = parse_threat(entry)
            if count < 1:
                errors.append(f"beat {b.get('id')}: threat count in {entry!r} must be >= 1")
                continue
            mon = bestiary.find_monster(name, monsters)
            if mon is None:
                errors.append(f"beat {b.get('id')}: unknown monster {name!r}")
            elif not bestiary.cr_in_band(mon["cr"], lvl):
                errors.append(
                    f"beat {b.get('id')}: {name} (CR {mon['cr']}) out of band "
                    f"for party level {lvl}"
                )

    return errors


if __name__ == "__main__":
    import argparse
    import json
    import sys as _sys

    p = argparse.ArgumentParser(description="Validate a campaign bible JSON.")
    p.add_argument("--bible", required=True, help="path to the generated bible JSON")
    args = p.parse_args()
    data = json.loads(__import__("pathlib").Path(args.bible).read_text(encoding="utf-8"))
    errs = validate_bible(data, bestiary.load_monsters())
    if errs:
        print("INVALID:")
        for e in errs:
            print(f"  - {e}")
        _sys.exit(1)
    print("VALID")

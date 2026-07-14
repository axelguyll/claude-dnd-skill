"""schema.py — validate a generated campaign bible (spine of beats) against the
band rules and cross-references. Pure functions; returns a list of error strings
(empty == valid)."""
from __future__ import annotations

import importlib

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


def party_levels(beats: list[dict]) -> list[int]:
    """Level the party is at DURING each beat, before that beat's level_up_to
    applies. Starts at 1; a non-null level_up_to raises the level for later beats."""
    levels: list[int] = []
    current = 1
    for beat in beats:
        levels.append(current)
        target = beat.get("level_up_to")
        if isinstance(target, int) and not isinstance(target, bool):
            current = target
    return levels


def validate_bible(bible: dict, monsters: list[dict]) -> list[str]:
    errors: list[str] = []
    beats = bible.get("beats", [])

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
        if b.get("status") not in _STATUSES:
            errors.append(
                f"beat {bid}: status {b.get('status')!r} must be one of "
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

    # threats: known name + in band for that beat's party level
    levels = party_levels(beats)
    for b, lvl in zip(beats, levels):
        for name in (b.get("threats") if isinstance(b.get("threats"), list) else []):
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

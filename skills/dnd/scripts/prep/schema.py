"""schema.py — validate a generated campaign bible (spine of beats) against the
band rules and cross-references. Pure functions; returns a list of error strings
(empty == valid)."""
from __future__ import annotations


def party_levels(beats: list[dict]) -> list[int]:
    """Level the party is at DURING each beat, before that beat's level_up_to
    applies. Starts at 1; a non-null level_up_to raises the level for later beats."""
    levels: list[int] = []
    current = 1
    for beat in beats:
        levels.append(current)
        target = beat.get("level_up_to")
        if target is not None:
            current = target
    return levels

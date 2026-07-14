"""bestiary.py — CR band math and level-appropriate monster candidate lists,
computed against the vendored SRD (skills/dnd/data/dnd5e_srd.json).

Band rule: ceiling = level + 2; floor = 0.125 for levels 1-3 (keeps CR-1/8
minions legal), else level/4. CR-0 creatures are never combat threats.
"""
from __future__ import annotations


def floor_cr(level: int) -> float:
    return 0.125 if level <= 3 else level / 4


def ceiling_cr(level: int) -> float:
    return float(level + 2)


def band_for_level(level: int) -> tuple[float, float]:
    return (floor_cr(level), ceiling_cr(level))


def cr_in_band(cr: float, level: int) -> bool:
    lo, hi = band_for_level(level)
    return cr > 0 and lo <= cr <= hi

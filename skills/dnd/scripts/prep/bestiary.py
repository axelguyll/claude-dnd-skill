"""bestiary.py — CR band math and level-appropriate monster candidate lists,
computed against the vendored SRD (skills/dnd/data/dnd5e_srd.json).

Band rule: ceiling = level + 2; floor = 0.125 for levels 1-3 (keeps CR-1/8
minions legal), else level/4. CR-0 creatures are never combat threats.
"""
from __future__ import annotations

import json
import pathlib

DATA_PATH = pathlib.Path(__file__).resolve().parents[2] / "data" / "dnd5e_srd.json"


def floor_cr(level: int) -> float:
    return 0.125 if level <= 3 else level / 4


def ceiling_cr(level: int) -> float:
    return float(level + 2)


def band_for_level(level: int) -> tuple[float, float]:
    return (floor_cr(level), ceiling_cr(level))


def cr_in_band(cr: float, level: int) -> bool:
    lo, hi = band_for_level(level)
    return cr > 0 and lo <= cr <= hi


def load_monsters(data_path: pathlib.Path | None = None) -> list[dict]:
    path = data_path or DATA_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["monsters"]


def find_monster(name: str, monsters: list[dict]) -> dict | None:
    for m in monsters:
        if m["name"] == name:
            return m
    return None


def candidates_for_level(level: int, monsters: list[dict]) -> list[dict]:
    hits = [
        {"name": m["name"], "cr": m["cr"], "type": m.get("type", "")}
        for m in monsters
        if cr_in_band(m["cr"], level)
    ]
    hits.sort(key=lambda m: (m["cr"], m["name"]))
    return hits


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Level-appropriate monster candidates.")
    p.add_argument("--level", type=int, required=True)
    args = p.parse_args()
    for m in candidates_for_level(args.level, load_monsters()):
        print(f"{m['name']}\t(CR {m['cr']})\t{m['type']}")

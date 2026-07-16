#!/usr/bin/env python3
"""
grid.py — combat-grid math for mapped tactical scenes.

Stateless like combat.py: positions come in as arguments, verdicts go out on
stdout. The grid spec for a map lives at <campaign>/maps/<handle>.grid.json
(dims + terrain); positions themselves live in the combat STATE_JSON, never here.

Coordinates are chess-style tile labels: column letter (A-Z, left to right)
plus row number (1-99, top to bottom). Tiles are 5 ft. Diagonals cost 5 ft
(2014 PHB default), so distance is Chebyshev.

Usage:
    python3 grid.py validate <spec.json>
        Schema/bounds-check a grid spec. Prints VALID, or INVALID + errors (exit 1).

    python3 grid.py dist <tile> <tile>
        Distance in feet, e.g. `grid.py dist C4 F7` -> 15ft

    python3 grid.py move --from C4 --to F6 --speed 30 --spec <spec.json>
        Cheapest-path movement verdict (difficult terrain x2, impassable blocked):
        `OK cost=25ft`, or `ILLEGAL cost=40ft -- furthest reachable toward F6: E5 (30ft)`,
        or `UNREACHABLE F6`.

    python3 grid.py range --from C4 --to F7 --ft 60
        `IN RANGE (dist=15ft)` / `OUT OF RANGE (dist=70ft)`

    python3 grid.py aoe --shape sphere|cube|cone|line --origin D4 --size 20
                        [--dir N|NE|E|SE|S|SW|W|NW] --spec <spec.json>
        Affected tile list, clipped to the grid. Sphere/cube are exact on the
        5-ft-diagonal metric; cone/line are grid approximations (documented v1
        simplification). Cube supports cardinal --dir only.
"""
from __future__ import annotations

import argparse
import heapq
import json
import math
import re
import sys
from pathlib import Path

TILE_FT = 5
MAX_COLS = 26
MAX_ROWS = 99

DIRS = {"N": (0, -1), "NE": (1, -1), "E": (1, 0), "SE": (1, 1),
        "S": (0, 1), "SW": (-1, 1), "W": (-1, 0), "NW": (-1, -1)}

_TILE = re.compile(r"^([A-Za-z])([1-9]\d?)$")


def _force_utf8_stdio() -> None:
    # Same guard as combat.py: Windows consoles default to cp1252.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


_force_utf8_stdio()


def parse_tile(label: str) -> tuple[int, int]:
    """'C4' -> (col, row) zero-based: (2, 3)."""
    m = _TILE.match(label.strip())
    if not m:
        raise ValueError(f"Bad tile label: {label!r}")
    return ord(m.group(1).upper()) - ord("A"), int(m.group(2)) - 1


def tile_name(col: int, row: int) -> str:
    return f"{chr(ord('A') + col)}{row + 1}"


def dist_ft(a: str, b: str) -> int:
    (c1, r1), (c2, r2) = parse_tile(a), parse_tile(b)
    return max(abs(c1 - c2), abs(r1 - r2)) * TILE_FT


def main(argv=None):
    p = argparse.ArgumentParser(description="Combat-grid math.")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dist")
    d.add_argument("a")
    d.add_argument("b")

    args = p.parse_args(argv)
    if args.cmd == "dist":
        print(f"{dist_ft(args.a, args.b)}ft")


if __name__ == "__main__":
    main()

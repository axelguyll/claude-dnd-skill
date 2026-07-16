# Combat Grid + Map Cue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Text-descriptor combat grid (chess-style A1 tiles) over the prep map shopping list, with a chat map-cue block for the host and a player-facing projector page showing token positions.

**Architecture:** Three new pieces — a per-map grid spec (`<campaign>/maps/<handle>.grid.json`), a stateless math engine (`scripts/grid.py`, modeled on combat.py), and a projector renderer (`scripts/render_map.py`, modeled on render_tracker.py). Positions ride the existing STATE_JSON pipeline (`state.md → ## Active Combat`) as an optional `"pos"` field — combat.py mutates combatant dicts in place, so unknown fields already pass through untouched (verified). Prose wiring: a 🗺 cue bullet, per-turn steps b/d2 additions, prep step 4 spec authoring, `combat start` additions.

**Tech Stack:** Python 3.9+ stdlib only (json, re, heapq, math, argparse, html, pathlib), matching every existing script. unittest tests run via pytest, `sys.path`-insert import pattern from `tests/test_render_tracker.py`.

**Spec:** `docs/superpowers/specs/2026-07-16-combat-grid-map-cue-design.md`

## Global Constraints

- Tiles are 5 ft; **diagonals cost 5 ft** (2014 PHB default). Distance metric is Chebyshev.
- Columns → letters A–Z (max 26 cols), rows → numbers 1–99. Non-square grids fine. Labels like `C4`.
- Grid spec is rules truth; the map image is decoration. Spec authored at prep under the asset-pass spoiler discipline (terrain only, never plot).
- grid.py and render_map.py are **stateless** — positions in, verdict/HTML out. No new persistence mechanism: positions live only in STATE_JSON.
- `"hidden": true` combatants never appear on the player-facing page.
- assets.html is untouched (must stay static — audio loops). tracker.html stays the DM dashboard.
- Cue blocks: `🗺 **Map:** *<handle>*` up, `🗺 **Map:** *down — theater of the mind*` down. Listed handles only, never invented. Unlisted fights stay theater of the mind.
- Scripts must survive Windows cp1252 consoles: reuse combat.py's `_force_utf8_stdio` guard in any script printing non-ASCII.
- Never touch `~/.claude/dnd/campaigns/` (live campaign data). Tests use tmp dirs or pure functions only.
- LoS/cover and opportunity attacks are **not scripted** in v1 — prose-adjudicated. Cone/line AoE are documented grid approximations; cube supports cardinal `--dir` only.

---

### Task 1: grid.py — tile parsing + distance + CLI skeleton

**Files:**
- Create: `skills/dnd/scripts/grid.py`
- Test: `tests/test_grid.py` (create)

**Interfaces:**
- Produces (used by every later grid task):
  - `TILE_FT = 5`
  - `parse_tile(label: str) -> tuple[int, int]` — `"C4"` → `(2, 3)` (col, row), zero-based; raises `ValueError` on bad labels.
  - `tile_name(col: int, row: int) -> str` — inverse.
  - `dist_ft(a: str, b: str) -> int` — Chebyshev × 5.
  - CLI: `python3 grid.py dist C4 F7` → prints `15ft`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_grid.py`:

```python
"""test_grid.py — grid.py combat-grid math: tile labels, distance, spec
validation, movement pathing, range, AoE. Pure-function tests, no filesystem
except tmp spec files. Spec:
docs/superpowers/specs/2026-07-16-combat-grid-map-cue-design.md
"""
import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import grid  # noqa: E402


class TileTests(unittest.TestCase):
    def test_parse_tile(self):
        self.assertEqual(grid.parse_tile("A1"), (0, 0))
        self.assertEqual(grid.parse_tile("C4"), (2, 3))
        self.assertEqual(grid.parse_tile("z99"), (25, 98))

    def test_tile_name_roundtrip(self):
        self.assertEqual(grid.tile_name(2, 3), "C4")
        self.assertEqual(grid.tile_name(*grid.parse_tile("R24")), "R24")

    def test_bad_labels_raise(self):
        for bad in ("", "4C", "AA1", "C0", "C", "C100"):
            with self.assertRaises(ValueError, msg=bad):
                grid.parse_tile(bad)


class DistTests(unittest.TestCase):
    def test_orthogonal(self):
        self.assertEqual(grid.dist_ft("A1", "A4"), 15)

    def test_diagonal_costs_5(self):
        self.assertEqual(grid.dist_ft("A1", "D4"), 15)   # pure diagonal, 3 tiles

    def test_mixed_is_chebyshev(self):
        self.assertEqual(grid.dist_ft("C4", "F5"), 15)   # dx=3, dy=1

    def test_same_tile_is_zero(self):
        self.assertEqual(grid.dist_ft("B2", "B2"), 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_grid.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'grid'`.

- [ ] **Step 3: Write grid.py with tiles, distance, and the CLI frame**

Create `skills/dnd/scripts/grid.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_grid.py -v`
Expected: PASS (all TileTests + DistTests).

- [ ] **Step 5: Commit**

```bash
git add skills/dnd/scripts/grid.py tests/test_grid.py
git commit -m "feat: grid.py tile labels + Chebyshev distance + dist CLI"
```

---

### Task 2: grid.py — spec loading, terrain expansion, validate

**Files:**
- Modify: `skills/dnd/scripts/grid.py`
- Test: `tests/test_grid.py` (extend)

**Interfaces:**
- Consumes: `parse_tile`, `tile_name`, `MAX_COLS`, `MAX_ROWS` from Task 1.
- Produces:
  - `expand_tiles(expr: str) -> list[tuple[int, int]]` — `"F1"` → one tile; `"C3-D5"` → inclusive rectangle.
  - `validate_spec(spec: dict) -> list[str]` — empty list when valid.
  - `load_spec(path) -> dict` — reads JSON, raises `ValueError` listing errors when invalid.
  - `terrain_sets(spec: dict) -> tuple[set, set]` — `(difficult, impassable)` tile sets.
  - CLI: `grid.py validate <file>` — prints `VALID` (exit 0) or `INVALID` + one error per line (exit 1). Mirrors the schema.py hard-gate convention.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_grid.py`:

```python
SPEC = {
    "handle": "cavern",
    "cols": 8, "rows": 6,
    "terrain": [
        {"tiles": "C3-D5", "kind": "rubble", "difficult": True},
        {"tiles": "F1", "kind": "pillar", "impassable": True, "blocks_los": True},
    ],
    "notes": "test map",
}


class ExpandTilesTests(unittest.TestCase):
    def test_single_tile(self):
        self.assertEqual(grid.expand_tiles("F1"), [(5, 0)])

    def test_rectangle_inclusive(self):
        tiles = grid.expand_tiles("C3-D5")
        self.assertEqual(len(tiles), 6)          # 2 cols x 3 rows
        self.assertIn((2, 2), tiles)             # C3
        self.assertIn((3, 4), tiles)             # D5

    def test_corners_any_order(self):
        self.assertEqual(set(grid.expand_tiles("D5-C3")),
                         set(grid.expand_tiles("C3-D5")))


class ValidateTests(unittest.TestCase):
    def test_valid_spec_no_errors(self):
        self.assertEqual(grid.validate_spec(SPEC), [])

    def test_missing_dims(self):
        errs = grid.validate_spec({"handle": "x", "terrain": []})
        self.assertTrue(any("cols" in e for e in errs))
        self.assertTrue(any("rows" in e for e in errs))

    def test_cols_over_26_rejected(self):
        errs = grid.validate_spec({"handle": "x", "cols": 30, "rows": 5})
        self.assertTrue(any("cols" in e for e in errs))

    def test_terrain_out_of_bounds_rejected(self):
        bad = dict(SPEC, terrain=[{"tiles": "J9", "difficult": True}])  # 8x6 grid
        self.assertTrue(grid.validate_spec(bad))

    def test_bad_tile_expr_rejected(self):
        bad = dict(SPEC, terrain=[{"tiles": "C3-D5-E6"}])
        self.assertTrue(grid.validate_spec(bad))

    def test_missing_handle_rejected(self):
        errs = grid.validate_spec({"cols": 8, "rows": 6})
        self.assertTrue(any("handle" in e for e in errs))


class TerrainSetsTests(unittest.TestCase):
    def test_split_by_flag(self):
        difficult, impassable = grid.terrain_sets(SPEC)
        self.assertIn((2, 2), difficult)
        self.assertIn((5, 0), impassable)
        self.assertNotIn((5, 0), difficult)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_grid.py -v -k "Expand or Validate or Terrain"`
Expected: FAIL — `AttributeError` (functions don't exist).

- [ ] **Step 3: Implement**

Add to grid.py (below `dist_ft`):

```python
def expand_tiles(expr: str) -> list[tuple[int, int]]:
    """'F1' -> [(5, 0)]; 'C3-D5' -> inclusive rectangle between the corners."""
    parts = expr.strip().split("-")
    if len(parts) == 1:
        return [parse_tile(parts[0])]
    if len(parts) != 2:
        raise ValueError(f"Bad tile range: {expr!r}")
    (c1, r1), (c2, r2) = parse_tile(parts[0]), parse_tile(parts[1])
    return [(c, r)
            for c in range(min(c1, c2), max(c1, c2) + 1)
            for r in range(min(r1, r2), max(r1, r2) + 1)]


def validate_spec(spec: dict) -> list[str]:
    errors = []
    if not spec.get("handle"):
        errors.append("handle is required")
    cols, rows = spec.get("cols"), spec.get("rows")
    if not isinstance(cols, int) or not 1 <= cols <= MAX_COLS:
        errors.append(f"cols must be an int 1-{MAX_COLS}")
    if not isinstance(rows, int) or not 1 <= rows <= MAX_ROWS:
        errors.append(f"rows must be an int 1-{MAX_ROWS}")
    for i, t in enumerate(spec.get("terrain", [])):
        try:
            tiles = expand_tiles(t["tiles"])
        except (KeyError, TypeError, ValueError) as e:
            errors.append(f"terrain[{i}]: {e}")
            continue
        if isinstance(cols, int) and isinstance(rows, int):
            for (c, r) in tiles:
                if not (0 <= c < cols and 0 <= r < rows):
                    errors.append(
                        f"terrain[{i}]: {tile_name(c, r)} is outside the "
                        f"{cols}x{rows} grid")
                    break
    return errors


def load_spec(path) -> dict:
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate_spec(spec)
    if errors:
        raise ValueError("; ".join(errors))
    return spec


def terrain_sets(spec: dict) -> tuple[set, set]:
    difficult, impassable = set(), set()
    for t in spec.get("terrain", []):
        for tile in expand_tiles(t["tiles"]):
            if t.get("difficult"):
                difficult.add(tile)
            if t.get("impassable"):
                impassable.add(tile)
    return difficult, impassable
```

In `main()`, add the subparser and dispatch:

```python
    v = sub.add_parser("validate")
    v.add_argument("spec")
```

```python
    if args.cmd == "validate":
        try:
            spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"INVALID\n- cannot read spec: {e}")
            sys.exit(1)
        errors = validate_spec(spec)
        if errors:
            print("INVALID")
            for e in errors:
                print(f"- {e}")
            sys.exit(1)
        print("VALID")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_grid.py -v`
Expected: PASS.

- [ ] **Step 5: Smoke-test the CLI**

```bash
echo '{"handle":"x","cols":8,"rows":6}' > /tmp/spec-smoke.json
python skills/dnd/scripts/grid.py validate /tmp/spec-smoke.json
rm /tmp/spec-smoke.json
```
Expected output: `VALID`.

- [ ] **Step 6: Commit**

```bash
git add skills/dnd/scripts/grid.py tests/test_grid.py
git commit -m "feat: grid.py spec validation + terrain expansion"
```

---

### Task 3: grid.py — movement (Dijkstra with difficult/impassable)

**Files:**
- Modify: `skills/dnd/scripts/grid.py`
- Test: `tests/test_grid.py` (extend)

**Interfaces:**
- Consumes: `terrain_sets`, `parse_tile`, `tile_name`, `TILE_FT` from Tasks 1–2.
- Produces:
  - `cheapest_path(spec, from_label, to_label) -> tuple[int | None, list]` — `(cost_ft, [(col,row), ...])`; `(None, [])` if unreachable.
  - `move_verdict(spec, from_label, to_label, speed: int) -> str` — `OK cost=25ft` / `ILLEGAL cost=40ft -- furthest reachable toward F6: E5 (30ft)` / `UNREACHABLE F6`.
  - CLI: `grid.py move --from C4 --to F6 --speed 30 --spec <file>`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_grid.py`:

```python
class MoveTests(unittest.TestCase):
    # SPEC is 8x6; difficult C3-D5; impassable pillar F1.
    # SWAMP forces crossings: difficult band spans the full grid height, so no
    # cheap detour exists (SPEC's C3-D5 band leaves rows 1-2 open — Dijkstra
    # correctly routes around it, which is its own test below).
    SWAMP = {"handle": "swamp", "cols": 5, "rows": 3,
             "terrain": [{"tiles": "B1-C3", "kind": "bog", "difficult": True}]}

    def test_clear_path_ok(self):
        self.assertEqual(grid.move_verdict(SPEC, "A1", "A4", 30), "OK cost=15ft")

    def test_diagonal_costs_5(self):
        self.assertEqual(grid.move_verdict(SPEC, "A1", "D4", 30), "OK cost=15ft")

    def test_difficult_terrain_doubles(self):
        # A2 -> D2 must cross the full-height bog at B and C: 10 + 10 + 5.
        self.assertEqual(grid.move_verdict(self.SWAMP, "A2", "D2", 30),
                         "OK cost=25ft")

    def test_path_routes_around_difficult_when_cheaper(self):
        # B2 -> E2 stays on row 2 (all normal): 15ft, never touches C3-D5.
        self.assertEqual(grid.move_verdict(SPEC, "B2", "E2", 30), "OK cost=15ft")

    def test_illegal_reports_cost_and_furthest(self):
        verdict = grid.move_verdict(self.SWAMP, "A2", "D2", 15)   # needs 25ft
        self.assertTrue(verdict.startswith("ILLEGAL cost=25ft"))
        self.assertIn("furthest reachable", verdict)

    def test_impassable_blocks_target(self):
        self.assertEqual(grid.move_verdict(SPEC, "E1", "F1", 30), "UNREACHABLE F1")

    def test_walled_off_target_unreachable(self):
        walled = {"handle": "w", "cols": 3, "rows": 1,
                  "terrain": [{"tiles": "B1", "impassable": True}]}
        self.assertEqual(grid.move_verdict(walled, "A1", "C1", 30), "UNREACHABLE C1")

    def test_off_grid_raises(self):
        with self.assertRaises(ValueError):
            grid.move_verdict(SPEC, "A1", "Z9", 30)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_grid.py -v -k Move`
Expected: FAIL — `AttributeError: module 'grid' has no attribute 'move_verdict'`.

- [ ] **Step 3: Implement**

Add to grid.py:

```python
def _step_cost(tile: tuple[int, int], difficult: set) -> int:
    return TILE_FT * 2 if tile in difficult else TILE_FT


def cheapest_path(spec: dict, from_label: str, to_label: str):
    """Dijkstra over the 8-connected grid. Cost = cost of the tile entered
    (difficult x2). Returns (cost_ft, path as [(col,row), ...] incl. both
    endpoints), or (None, []) if the target is unreachable/impassable."""
    cols, rows = spec["cols"], spec["rows"]
    difficult, impassable = terrain_sets(spec)
    start, end = parse_tile(from_label), parse_tile(to_label)
    for label, tile in ((from_label, start), (to_label, end)):
        if not (0 <= tile[0] < cols and 0 <= tile[1] < rows):
            raise ValueError(f"{label} is outside the {cols}x{rows} grid")
    if end in impassable:
        return None, []

    best = {start: 0}
    prev = {}
    pq = [(0, start)]
    while pq:
        d, cur = heapq.heappop(pq)
        if cur == end:
            break
        if d > best.get(cur, d):
            continue
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc == 0 and dr == 0:
                    continue
                nxt = (cur[0] + dc, cur[1] + dr)
                if not (0 <= nxt[0] < cols and 0 <= nxt[1] < rows):
                    continue
                if nxt in impassable:
                    continue
                nd = d + _step_cost(nxt, difficult)
                if nd < best.get(nxt, nd + 1):
                    best[nxt] = nd
                    prev[nxt] = cur
                    heapq.heappush(pq, (nd, nxt))
    if end not in best:
        return None, []
    path = [end]
    while path[-1] != start:
        path.append(prev[path[-1]])
    return best[end], list(reversed(path))


def move_verdict(spec: dict, from_label: str, to_label: str, speed: int) -> str:
    cost, path = cheapest_path(spec, from_label, to_label)
    if cost is None:
        return f"UNREACHABLE {to_label.strip().upper()}"
    if cost <= speed:
        return f"OK cost={cost}ft"
    difficult, _ = terrain_sets(spec)
    spent, reach = 0, path[0]
    for tile in path[1:]:
        step = _step_cost(tile, difficult)
        if spent + step > speed:
            break
        spent += step
        reach = tile
    return (f"ILLEGAL cost={cost}ft -- furthest reachable toward "
            f"{to_label.strip().upper()}: {tile_name(*reach)} ({spent}ft)")
```

In `main()`, add:

```python
    m = sub.add_parser("move")
    m.add_argument("--from", dest="frm", required=True)
    m.add_argument("--to", required=True)
    m.add_argument("--speed", type=int, required=True)
    m.add_argument("--spec", required=True)
```

```python
    if args.cmd == "move":
        print(move_verdict(load_spec(args.spec), args.frm, args.to, args.speed))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_grid.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/dnd/scripts/grid.py tests/test_grid.py
git commit -m "feat: grid.py movement verdicts — Dijkstra, difficult terrain, furthest-reachable"
```

---

### Task 4: grid.py — range + AoE

**Files:**
- Modify: `skills/dnd/scripts/grid.py`
- Test: `tests/test_grid.py` (extend)

**Interfaces:**
- Consumes: `dist_ft`, `parse_tile`, `tile_name`, `DIRS`, `TILE_FT` from earlier tasks.
- Produces:
  - `range_verdict(from_label, to_label, ft: int) -> str` — `IN RANGE (dist=15ft)` / `OUT OF RANGE (dist=70ft)`.
  - `aoe_tiles(spec, shape, origin_label, size_ft, direction="N") -> list[str]` — sorted tile labels, clipped to grid. Shapes: `sphere` (Chebyshev radius, origin included), `cube` (side extends from origin in a **cardinal** `--dir`, sideways centered on origin), `cone` (length s, tiles within 45° of dir, origin excluded), `line` (s tiles from origin along dir, origin excluded, 5 ft wide).
  - CLI: `grid.py range --from C4 --to F7 --ft 60`; `grid.py aoe --shape cone --origin D4 --size 20 --dir NE --spec <file>`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_grid.py`:

```python
class RangeTests(unittest.TestCase):
    def test_in_range(self):
        self.assertEqual(grid.range_verdict("C4", "F5", 60), "IN RANGE (dist=15ft)")

    def test_out_of_range(self):
        self.assertEqual(grid.range_verdict("A1", "H6", 30),
                         "OUT OF RANGE (dist=35ft)")


class AoeTests(unittest.TestCase):
    BIG = {"handle": "big", "cols": 12, "rows": 12, "terrain": []}

    def test_sphere_20ft_is_chebyshev_radius_4(self):
        tiles = grid.aoe_tiles(self.BIG, "sphere", "F6", 20)
        self.assertIn("F6", tiles)            # origin included
        self.assertIn("B2", tiles)            # 4 tiles diagonal
        self.assertNotIn("A1", tiles)         # 5 tiles away
        self.assertEqual(len(tiles), 81)      # 9x9 square

    def test_sphere_clips_to_grid(self):
        tiles = grid.aoe_tiles(self.BIG, "sphere", "A1", 20)
        self.assertEqual(len(tiles), 25)      # 5x5 corner clip

    def test_cube_cardinal(self):
        tiles = grid.aoe_tiles(self.BIG, "cube", "F6", 15, direction="E")
        self.assertEqual(len(tiles), 9)       # 3x3
        self.assertIn("F6", tiles)            # near face at origin
        self.assertIn("H7", tiles)            # extends east, centered sideways

    def test_cube_diagonal_dir_raises(self):
        with self.assertRaises(ValueError):
            grid.aoe_tiles(self.BIG, "cube", "F6", 15, direction="NE")

    def test_line_30ft_east(self):
        tiles = grid.aoe_tiles(self.BIG, "line", "C6", 30, direction="E")
        self.assertEqual(tiles, ["D6", "E6", "F6", "G6", "H6", "I6"])

    def test_cone_15ft_east_widens(self):
        tiles = grid.aoe_tiles(self.BIG, "cone", "C6", 15, direction="E")
        self.assertNotIn("C6", tiles)         # origin excluded
        self.assertIn("D6", tiles)
        self.assertIn("F4", tiles)            # 45-degree edge at distance 3
        self.assertIn("F8", tiles)
        self.assertNotIn("D3", tiles)         # outside the 45-degree wedge

    def test_unknown_shape_raises(self):
        with self.assertRaises(ValueError):
            grid.aoe_tiles(self.BIG, "donut", "F6", 20)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_grid.py -v -k "Range or Aoe"`
Expected: FAIL — missing attributes.

- [ ] **Step 3: Implement**

Add to grid.py:

```python
def range_verdict(from_label: str, to_label: str, ft: int) -> str:
    d = dist_ft(from_label, to_label)
    return (f"IN RANGE (dist={d}ft)" if d <= ft
            else f"OUT OF RANGE (dist={d}ft)")


def aoe_tiles(spec: dict, shape: str, origin_label: str, size_ft: int,
              direction: str = "N") -> list[str]:
    cols, rows = spec["cols"], spec["rows"]
    o = parse_tile(origin_label)
    s = max(1, size_ft // TILE_FT)
    if direction not in DIRS:
        raise ValueError(f"Bad direction: {direction!r}")
    dc, dr = DIRS[direction]
    tiles = set()

    if shape == "sphere":
        for c in range(max(0, o[0] - s), min(cols, o[0] + s + 1)):
            for r in range(max(0, o[1] - s), min(rows, o[1] + s + 1)):
                tiles.add((c, r))
    elif shape == "cube":
        if dc and dr:
            raise ValueError("cube supports cardinal --dir only (N/E/S/W)")
        side = s
        off = -(side // 2)
        for f in range(side):
            for w in range(off, off + side):
                if dc:                        # E/W: forward on cols, width on rows
                    tiles.add((o[0] + dc * f, o[1] + w))
                else:                         # N/S: forward on rows, width on cols
                    tiles.add((o[0] + w, o[1] + dr * f))
    elif shape == "cone":
        ang0 = math.atan2(dr, dc)
        for c in range(cols):
            for r in range(rows):
                if (c, r) == o:
                    continue
                if max(abs(c - o[0]), abs(r - o[1])) > s:
                    continue
                ang = math.atan2(r - o[1], c - o[0])
                diff = abs((ang - ang0 + math.pi) % (2 * math.pi) - math.pi)
                if diff <= math.pi / 4 + 1e-9:
                    tiles.add((c, r))
    elif shape == "line":
        for i in range(1, s + 1):
            tiles.add((o[0] + dc * i, o[1] + dr * i))
    else:
        raise ValueError(f"Bad shape: {shape!r}")

    inb = [(c, r) for (c, r) in tiles if 0 <= c < cols and 0 <= r < rows]
    return [tile_name(c, r) for (c, r) in sorted(inb, key=lambda t: (t[1], t[0]))]
```

In `main()`, add:

```python
    r = sub.add_parser("range")
    r.add_argument("--from", dest="frm", required=True)
    r.add_argument("--to", required=True)
    r.add_argument("--ft", type=int, required=True)

    a = sub.add_parser("aoe")
    a.add_argument("--shape", required=True,
                   choices=["sphere", "cube", "cone", "line"])
    a.add_argument("--origin", required=True)
    a.add_argument("--size", type=int, required=True)
    a.add_argument("--dir", dest="direction", default="N", choices=sorted(DIRS))
    a.add_argument("--spec", required=True)
```

```python
    if args.cmd == "range":
        print(range_verdict(args.frm, args.to, args.ft))
    if args.cmd == "aoe":
        tiles = aoe_tiles(load_spec(args.spec), args.shape, args.origin,
                          args.size, args.direction)
        print(f"{len(tiles)} tiles: {' '.join(tiles)}")
```

- [ ] **Step 4: Run the whole grid suite**

Run: `python -m pytest tests/test_grid.py -v`
Expected: PASS (all classes).

- [ ] **Step 5: Commit**

```bash
git add skills/dnd/scripts/grid.py tests/test_grid.py
git commit -m "feat: grid.py range check + sphere/cube/cone/line AoE"
```

---

### Task 5: render_map.py — projector page renderer

**Files:**
- Create: `skills/dnd/scripts/render_map.py`
- Test: `tests/test_render_map.py` (create)

**Interfaces:**
- Consumes: `grid.load_spec` (Task 2) at CLI time; STATE_JSON combatant dicts with optional `"pos"`, `"hidden"` fields; `paths.find_campaign`.
- Produces:
  - `render_map_html(spec, combatants, round_num, image_file: str | None) -> str` — full HTML doc. `image_file` is a relative href like `maps/cavern.png`, or `None` (grid-only render).
  - `render_idle_html() -> str` — "theater of the mind" idle screen.
  - `find_image(camp_dir, handle) -> str | None` — checks `maps/<handle>.png|.jpg|.jpeg|.webp`, returns relative href or None.
  - CLI: `render_map.py --campaign <n> --handle <h> --state '<STATE_JSON>' [--round N]` and `render_map.py --campaign <n> --clear`. Writes `<campaign>/map.html`, prints its path.
- Conventions (locked): first combatant in STATE_JSON = active (ring highlight), same as render_tracker. Tokens: PC `#d4b24c`, NPC `#b0432f`. `hidden` skipped entirely. Combatants with no `pos` listed in an "off-map" strip. Meta-refresh 4s, matching tracker.html.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_render_map.py`:

```python
"""test_render_map.py — render_map.py builds the player-facing battle-map HTML
(projected page: map image, grid overlay, token positions). Pure-function
tests, no filesystem. Spec:
docs/superpowers/specs/2026-07-16-combat-grid-map-cue-design.md
"""
import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import render_map  # noqa: E402

SPEC = {"handle": "cavern", "cols": 8, "rows": 6, "terrain": []}
COMBATANTS = [
    {"name": "Piper", "type": "pc", "hp": 18, "ac": 15, "pos": "C4"},
    {"name": "Goblin", "type": "npc", "hp": 7, "ac": 15, "pos": "F2"},
    {"name": "Lurker", "type": "npc", "hp": 30, "ac": 13, "pos": "A1",
     "hidden": True},
    {"name": "Wolf", "type": "npc", "hp": 11, "ac": 13},   # no pos
]


class RenderMapTests(unittest.TestCase):
    def setUp(self):
        self.out = render_map.render_map_html(SPEC, COMBATANTS, 2,
                                              "maps/cavern.png")

    def test_round_and_handle_shown(self):
        self.assertIn("Round 2", self.out)
        self.assertIn("cavern", self.out)

    def test_image_embedded_stretched_to_grid(self):
        self.assertIn('href="maps/cavern.png"', self.out)
        self.assertIn('preserveAspectRatio="none"', self.out)

    def test_grid_labels_present(self):
        self.assertIn(">A<", self.out)        # column letter
        self.assertIn(">H<", self.out)        # 8th column
        self.assertIn(">6<", self.out)        # last row number

    def test_placed_tokens_rendered(self):
        self.assertIn("Piper", self.out)
        self.assertIn("Goblin", self.out)

    def test_hidden_combatant_absent(self):
        self.assertNotIn("Lurker", self.out)

    def test_unplaced_listed_off_map(self):
        self.assertIn("off-map", self.out)
        self.assertIn("Wolf", self.out)

    def test_active_combatant_ringed(self):
        # First in list is active; its token carries the active class/marker.
        self.assertIn('class="token active"', self.out)

    def test_meta_refresh_present(self):
        self.assertIn('http-equiv="refresh"', self.out)

    def test_no_image_renders_grid_only(self):
        out = render_map.render_map_html(SPEC, COMBATANTS, 1, None)
        self.assertNotIn("<image", out)
        self.assertIn(">A<", out)             # grid still there


class IdleTests(unittest.TestCase):
    def test_idle_screen(self):
        out = render_map.render_idle_html()
        self.assertIn("theater of the mind", out.lower())
        self.assertIn('http-equiv="refresh"', out)


class FindImageTests(unittest.TestCase):
    def test_finds_png_then_jpg(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            camp = pathlib.Path(d)
            (camp / "maps").mkdir()
            self.assertIsNone(render_map.find_image(camp, "cavern"))
            (camp / "maps" / "cavern.jpg").write_bytes(b"x")
            self.assertEqual(render_map.find_image(camp, "cavern"),
                             "maps/cavern.jpg")
            (camp / "maps" / "cavern.png").write_bytes(b"x")
            self.assertEqual(render_map.find_image(camp, "cavern"),
                             "maps/cavern.png")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_render_map.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'render_map'`.

- [ ] **Step 3: Implement render_map.py**

Create `skills/dnd/scripts/render_map.py`:

```python
#!/usr/bin/env python3
"""
render_map.py — emit the player-facing battle-map HTML (projector page).

Draws the acquired map image (maps/<handle>.png, stretched so image edges =
grid edges), a chess-style coordinate overlay from the grid spec, and a token
per combatant at its "pos" tile from the combat STATE_JSON. Combatants with
"hidden": true are never rendered — this page faces the players. Meta-refresh
like tracker.html; regenerated every combat turn (step d2). Between fights the
page shows an idle "theater of the mind" screen (--clear).

No server — a self-contained local page opened over file://. The host keeps
map.html on the projector permanently.

Usage:
    python3 render_map.py --campaign <name> --handle <handle> --state '<STATE_JSON>' [--round N]
        Writes <campaign>/map.html and prints its path. Requires
        <campaign>/maps/<handle>.grid.json (author it first — see SKILL-commands.md).

    python3 render_map.py --campaign <name> --clear
        Writes the idle screen.
"""
from __future__ import annotations

import argparse
import html
import json
import sys

from grid import load_spec, parse_tile
from paths import find_campaign

REFRESH = '<meta http-equiv="refresh" content="4">'
STYLE = '''<style>
 html,body{height:100%;margin:0}
 body{background:#0b0908;color:#e8dcc8;font:14px/1.4 system-ui,sans-serif;
      display:flex;flex-direction:column}
 .hud{position:fixed;top:8px;left:12px;color:#c9a86a;font-size:13px;
      letter-spacing:.08em;text-transform:uppercase;opacity:.75;z-index:2}
 svg{flex:1;display:block;width:100%;min-height:0}
 .strip{padding:6px 12px;color:#b7a488;font-size:13px}
 .idle{flex:1;display:flex;align-items:center;justify-content:center;
       color:#6b6155;font-size:22px;letter-spacing:.14em;text-transform:uppercase}
</style>'''


def find_image(camp_dir, handle: str):
    """Relative href of the acquired map image, or None."""
    for ext in ("png", "jpg", "jpeg", "webp"):
        if (camp_dir / "maps" / f"{handle}.{ext}").exists():
            return f"maps/{handle}.{ext}"
    return None


def _svg(spec: dict, combatants: list, image_file) -> str:
    cols, rows = spec["cols"], spec["rows"]
    parts = []
    if image_file:
        parts.append(
            f'<image href="{html.escape(image_file)}" x="0" y="0" '
            f'width="{cols}" height="{rows}" preserveAspectRatio="none"/>')
    # grid lines
    for c in range(cols + 1):
        parts.append(f'<line x1="{c}" y1="0" x2="{c}" y2="{rows}"/>')
    for r in range(rows + 1):
        parts.append(f'<line x1="0" y1="{r}" x2="{cols}" y2="{r}"/>')
    # edge labels
    for c in range(cols):
        parts.append(f'<text x="{c + 0.5}" y="-0.28" class="lbl">'
                     f'{chr(ord("A") + c)}</text>')
    for r in range(rows):
        parts.append(f'<text x="-0.45" y="{r + 0.68}" class="lbl">{r + 1}</text>')
    # tokens (skip hidden and unplaced); first combatant = active
    for i, c in enumerate(combatants):
        if c.get("hidden") or not c.get("pos"):
            continue
        col, row = parse_tile(c["pos"])
        cx, cy = col + 0.5, row + 0.5
        fill = "#d4b24c" if c.get("type") == "pc" else "#b0432f"
        cls = "token active" if i == 0 else "token"
        parts.append(f'<circle class="{cls}" cx="{cx}" cy="{cy}" r="0.38" '
                     f'fill="{fill}"/>')
        parts.append(f'<text x="{cx}" y="{cy + 0.78}" class="name">'
                     f'{html.escape(str(c["name"]))}</text>')
    inner = "\n".join(parts)
    return (f'<svg viewBox="-0.9 -0.9 {cols + 1.8} {rows + 1.8}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<style>line{{stroke:rgba(232,220,200,.35);stroke-width:.03}}'
            f'.lbl{{fill:#c9a86a;font-size:.42px;text-anchor:middle}}'
            f'.name{{fill:#e8dcc8;font-size:.3px;text-anchor:middle;'
            f'paint-order:stroke;stroke:#0b0908;stroke-width:.06px}}'
            f'.token{{stroke:#0b0908;stroke-width:.06}}'
            f'.token.active{{stroke:#ffe4a8;stroke-width:.09}}</style>'
            f'{inner}</svg>')


def render_map_html(spec: dict, combatants: list, round_num: int,
                    image_file) -> str:
    unplaced = [str(c["name"]) for c in combatants
                if not c.get("hidden") and not c.get("pos")]
    strip = (f'<div class="strip">off-map: '
             f'{html.escape(", ".join(unplaced))}</div>' if unplaced else "")
    return (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
            f'{REFRESH}\n<title>Battle Map — Round {round_num}</title>\n'
            f'{STYLE}</head><body>\n'
            f'<div class="hud">Round {round_num} — '
            f'{html.escape(str(spec["handle"]))}</div>\n'
            f'{_svg(spec, combatants, image_file)}\n{strip}\n</body></html>')


def render_idle_html() -> str:
    return (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
            f'{REFRESH}\n<title>Battle Map</title>\n{STYLE}</head><body>\n'
            f'<div class="idle">theater of the mind</div>\n</body></html>')


def main(argv=None):
    p = argparse.ArgumentParser(description="Render the battle-map HTML.")
    p.add_argument("--campaign", required=True)
    p.add_argument("--handle")
    p.add_argument("--state", help="STATE_JSON array from combat.py")
    p.add_argument("--round", type=int, default=1)
    p.add_argument("--clear", action="store_true")
    args = p.parse_args(argv)

    camp = find_campaign(args.campaign)
    camp.mkdir(parents=True, exist_ok=True)
    out = camp / "map.html"

    if args.clear:
        out.write_text(render_idle_html(), encoding="utf-8")
        print(str(out))
        return

    if not args.handle or not args.state:
        p.error("--handle and --state are required unless --clear")
    spec_path = camp / "maps" / f"{args.handle}.grid.json"
    if not spec_path.exists():
        sys.exit(f"No grid spec at {spec_path} — author it first "
                 f"(see SKILL-commands.md, combat start)")
    spec = load_spec(spec_path)
    combatants = json.loads(args.state)
    image_file = find_image(camp, args.handle)
    out.write_text(render_map_html(spec, combatants, args.round, image_file),
                   encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_render_map.py tests/test_grid.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/dnd/scripts/render_map.py tests/test_render_map.py
git commit -m "feat: render_map.py — player-facing projector page with grid overlay + tokens"
```

---

### Task 6: render_tracker.py — position display

**Files:**
- Modify: `skills/dnd/scripts/render_tracker.py:92` (the name div inside `render_tracker_html`)
- Modify: `skills/dnd/scripts/render_tracker.py:110-117` (CSS block — add `.pos` rule)
- Test: `tests/test_render_tracker.py` (extend)

**Interfaces:**
- Consumes: STATE_JSON combatants now optionally carrying `"pos"` (Tasks 1–5 convention).
- Produces: DM dashboard shows `@ C4` beside the name when `pos` present; renders unchanged when absent (backward compatible).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_render_tracker.py` (inside `RenderTrackerTests` or a new class following the file's style):

```python
class PositionColumnTests(unittest.TestCase):
    def setUp(self):
        self.eff = render_tracker.condition_effects(SRD)

    def test_pos_shown_when_present(self):
        combatants = [{"name": "Piper", "hp": 18, "max_hp": 24, "ac": 15,
                       "initiative": 14, "conditions": [], "pos": "C4"}]
        out = render_tracker.render_tracker_html(combatants, 1, {}, self.eff)
        self.assertIn("@ C4", out)

    def test_no_pos_no_marker(self):
        combatants = [{"name": "Piper", "hp": 18, "max_hp": 24, "ac": 15,
                       "initiative": 14, "conditions": []}]
        out = render_tracker.render_tracker_html(combatants, 1, {}, self.eff)
        self.assertNotIn("@ ", out)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_render_tracker.py -v -k Position`
Expected: `test_pos_shown_when_present` FAILS; `test_no_pos_no_marker` passes.

- [ ] **Step 3: Implement**

In `render_tracker_html`, change the name div (line ~92):

```python
        pos = (f' <span class="pos">@ {html.escape(str(c["pos"]))}</span>'
               if c.get("pos") else "")
```

and in the row f-string replace `<div class="name">{name}</div>` with
`<div class="name">{name}{pos}</div>`.

In the CSS block add one rule after `.none`:

```
 .pos{color:#8fb7d6;font-size:12px;font-weight:400}
```

- [ ] **Step 4: Run the tracker suite**

Run: `python -m pytest tests/test_render_tracker.py -v`
Expected: PASS (all, including pre-existing tests).

- [ ] **Step 5: Commit**

```bash
git add skills/dnd/scripts/render_tracker.py tests/test_render_tracker.py
git commit -m "feat: render_tracker.py shows combatant grid position when present"
```

---

### Task 7: Prose — SKILL.md (cue bullet, per-turn steps, compaction ladder)

**Files:**
- Modify: `skills/dnd/SKILL.md` (narration principles bullet list, line ~212; per-turn sequence code block, lines ~301-319; compaction ladder mid-combat entry, line ~226)
- Test: `tests/test_grid_prose.py` (create)

**Interfaces:**
- Consumes: script names/flags exactly as built in Tasks 1–5 (`grid.py move/range/aoe`, `render_map.py --campaign --handle --state --round`, `--clear`).
- Produces: the cue-block strings Task 8's `combat start` procedure references.

- [ ] **Step 1: Write the failing prose test**

Create `tests/test_grid_prose.py`:

```python
"""test_grid_prose.py — prose contracts for the combat grid + map cue:
SKILL.md (cue bullet, per-turn steps, compaction), SKILL-commands.md (prep
step 4 spec authoring, combat start), SKILL-scripts.md (script syntax),
templates/map-list.md (sidecar note). Spec:
docs/superpowers/specs/2026-07-16-combat-grid-map-cue-design.md
"""
import pathlib
import re
import unittest

DND = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd"
SKILL = (DND / "SKILL.md").read_text(encoding="utf-8")
COMMANDS = (DND / "SKILL-commands.md").read_text(encoding="utf-8")
SCRIPTS_DOC = (DND / "SKILL-scripts.md").read_text(encoding="utf-8")
MAP_TEMPLATE = (DND / "templates" / "map-list.md").read_text(encoding="utf-8")


class SkillMdTests(unittest.TestCase):
    def test_map_cue_block_defined(self):
        self.assertIn("🗺 **Map:** *<handle>*", SKILL)

    def test_down_cue_defined(self):
        self.assertIn("down — theater of the mind", SKILL)

    def test_cue_never_invented(self):
        idx = SKILL.find("🗺 **Map:**")
        window = SKILL[idx:idx + 900]
        self.assertIn("never invent", window)

    def test_per_turn_step_b_validates_movement(self):
        seq = SKILL[SKILL.find("Per-turn combat sequence"):]
        block = re.search(r"```(.*?)```", seq, re.S).group(1)
        self.assertIn("grid.py move", block)
        self.assertIn("grid.py range", block)

    def test_per_turn_d2_renders_map(self):
        block = re.search(r"Per-turn combat sequence.*?```(.*?)```",
                          SKILL, re.S).group(1)
        self.assertIn("render_map.py", block)

    def test_compaction_ladder_mentions_positions(self):
        self.assertRegex(SKILL, r"Mid-combat:.*positions")


if __name__ == "__main__":
    unittest.main()
```

(Tasks 8–9 append their own test classes to this file.)

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_grid_prose.py -v`
Expected: FAIL — all SkillMdTests.

- [ ] **Step 3: Add the map-cue bullet**

In SKILL.md narration principles, directly after the sound-cue bullet (line ~212, "**When the scene's location shifts, drop a sound-cue block** ..."), insert:

```markdown
- **When a tactical scene begins on a listed map, drop a map-cue block** — on its own line, `🗺 **Map:** *<handle>*`, where `<handle>` matches an entry in the campaign's map shopping list (`map-list.md`), so the host knows the battle map is going up (the projector page `map.html` lights up at the same moment — see the per-turn combat sequence). When combat ends or the scene leaves the map, drop the down-cue on its own line: `🗺 **Map:** *down — theater of the mind*`. Same contract as the sound cue: a standalone block, never buried in a narration paragraph, and **never invent a map** the shopping list doesn't have — a fight anywhere else stays theater of the mind, with no cue and no grid.
```

- [ ] **Step 4: Extend the per-turn sequence**

In the per-turn code block (lines ~301-319), replace step b and insert a line into d2 so the block reads (unchanged lines kept verbatim):

```
a. Player states their action (typed in chat).
b. Roll all dice (combat.py attack / dice.py). NPC/monster rolls are yours; PC rolls per roll_mode.
   Mapped combat only — resolve position math BEFORE the dice, script-first:
   a declared move is checked with grid.py move (--speed from the mover's sheet;
   ILLEGAL → narrate the constraint in fiction, offer the furthest-reachable tile
   from the verdict, let them re-choose — never silently clamp); reach/ranged
   attacks are checked with grid.py range; AoE tile lists come from grid.py aoe.
   You move NPCs and validate those moves the same way. Update each mover's
   "pos" in the STATE_JSON you carry.
c. tracker.py        ← conditions, concentration, death saves if applicable
   tracker.py effect tick <actor>  ← decrement round effects; prints any expiry warnings
d. Write the full narration for this turn as chat prose. Put any NPC speech in its own
   visually distinct block, separate from DM narration (see "Narration principles").
d2. Refresh the host's combat tracker from the current turn's state:
    python3 ${CLAUDE_SKILL_DIR}/scripts/render_tracker.py --campaign <name> --state '<STATE_JSON>' --round <n>
    Pass the same combatant STATE_JSON you pipe through combat.py (ordered so the current
    turn's actor is first — it renders as the highlighted active row). After the render,
    write the same STATE_JSON back to `state.md → ## Active Combat` (replace the block) —
    the render and the durable copy must never diverge; mid-combat compaction recovers
    from that block, not from memory. Only during combat; out of combat, leave
    tracker.html untouched.
    Mapped combat only — also refresh the player-facing projector page with the SAME
    STATE_JSON:
    python3 ${CLAUDE_SKILL_DIR}/scripts/render_map.py --campaign <name> --handle <handle> --state '<STATE_JSON>' --round <n>
e. Persist stat changes: edit characters/<PC>.md for HP/slots; state.md for live flags,
   at scene boundaries / autosave cadence.
```

- [ ] **Step 5: Add "positions" to the compaction ladder**

Line ~226: change

`- **Mid-combat:** re-read `state.md → ## Active Combat` for order/HP/round ...`

to

`- **Mid-combat:** re-read `state.md → ## Active Combat` for order/HP/positions/round ...`

(rest of the line unchanged).

- [ ] **Step 6: Run test to verify it passes**

Run: `python -m pytest tests/test_grid_prose.py tests/test_no_display_refs.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add skills/dnd/SKILL.md tests/test_grid_prose.py
git commit -m "feat: map-cue block + mapped-combat per-turn steps in SKILL.md"
```

---

### Task 8: Prose — SKILL-commands.md (prep step 4 spec authoring, combat start) + map-list template

**Files:**
- Modify: `skills/dnd/SKILL-commands.md` (prep step 4, line ~366-377; `/dm:dnd combat start`, line ~744-757)
- Modify: `skills/dnd/templates/map-list.md` (sidecar note)
- Test: `tests/test_grid_prose.py` (extend)

**Interfaces:**
- Consumes: cue strings from Task 7; `grid.py validate` CLI from Task 2; `render_map.py` CLI from Task 5.
- Produces: the authoring + play procedures Task 9's docs describe.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_grid_prose.py`:

```python
class CommandsMdTests(unittest.TestCase):
    def _prep_step_4(self):
        return re.search(r"^4\. \*\*Asset shopping lists\.\*\*.*?(?=^5\. )",
                         COMMANDS, re.M | re.S).group(0)

    def test_prep_authors_grid_specs(self):
        step = self._prep_step_4()
        self.assertIn("grid.json", step)
        self.assertIn("grid.py validate", step)

    def test_prep_spec_is_spoiler_free(self):
        self.assertIn("terrain only", self._prep_step_4())

    def _combat_start(self):
        return re.search(r"^## `/dm:dnd combat start`.*?(?=^---)",
                         COMMANDS, re.M | re.S).group(0)

    def test_combat_start_emits_cue(self):
        self.assertIn("🗺 **Map:**", self._combat_start())

    def test_combat_start_first_use_confirm(self):
        self.assertIn("confirmed", self._combat_start())

    def test_combat_start_places_positions(self):
        self.assertIn('"pos"', self._combat_start())

    def test_combat_end_clears_map(self):
        self.assertIn("--clear", self._combat_start())
        self.assertIn("down — theater of the mind", self._combat_start())


class MapTemplateTests(unittest.TestCase):
    def test_template_mentions_grid_sidecar(self):
        self.assertIn("grid.json", MAP_TEMPLATE)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_grid_prose.py -v -k "Commands or MapTemplate"`
Expected: FAIL.

- [ ] **Step 3: Extend prep step 4**

In SKILL-commands.md step 4 ("Asset shopping lists"), after the two list bullets (`map-list.md` / `ambient-list.md`) and before "Then build the host's asset hub", insert:

```markdown
   For every map-list entry, also author its **grid spec** to
   `~/.claude/dnd/campaigns/<name>/maps/<handle>.grid.json` — dims (`cols` ≤ 26 →
   letters, `rows` → numbers; tiles are 5 ft; non-square fine) plus terrain regions
   (`tiles` as `F1` or `C3-D5`; flags `difficult` / `impassable` / `blocks_los`; free-prose
   `notes`). Same spoiler discipline as the lists: **terrain only**, never why the party
   goes there or what happens. Then hard-gate each spec:
   `python3 ${CLAUDE_SKILL_DIR}/scripts/grid.py validate <spec.json>`
   If it prints `INVALID`, fix every listed error and re-run — never proceed on an
   invalid spec (same rule as the spine gate at step 3).
```

- [ ] **Step 4: Extend `/dm:dnd combat start`**

Replace the `/dm:dnd combat start` section (lines ~744-757) with:

```markdown
## `/dm:dnd combat start`
1. Identify combatants; collect name, DEX mod, HP, AC, type (pc/npc) for each.
1.5 **Mapped combat?** If the scene sits at a location matching a `map-list.md` handle
   (or the host names a listed map to use), this fight is on the grid:
   - Emit the map cue on its own line: `🗺 **Map:** *<handle>*`.
   - Load `maps/<handle>.grid.json`. **First use of this handle** (spec lacks
     `"confirmed": true`): ask the host one line — *"spec says <cols>×<rows> — match
     your map? give real dims if not."* On override, rewrite `cols`/`rows` (re-fit
     terrain regions proportionally if the shape changed a lot), then add
     `"confirmed": true` and re-run `grid.py validate`. **No spec file at all** (older
     prep): author one now through the same exchange — dims from the host, terrain from
     the scene as narrated so far — validate, save, continue.
   - Place everyone: NPCs per the fiction; players state their tiles (default them to a
     sensible entry edge if they don't care). Add `"pos": "<tile>"` to each combatant's
     JSON. An unrevealed enemy either stays out of the JSON until it appears or carries
     `"hidden": true` — hidden combatants never render on the player page.
   A fight anywhere else is theater of the mind: no cue, no grid, no `pos` fields —
   skip this step entirely.
2. Run `combat.py init '<JSON>'` — auto-roll initiative for every combatant including PCs. Show the tracker and per-combatant roll breakdown in chat:
   ```
   ⚔️ Initiative — Round 1
   [Name]: d20(N) + DEX = total
   Turn order: [Name] → [Name] → ...
   ```
3. Save STATE_JSON to `state.md` under `## Active Combat`. Mapped combat: also run the
   first projector render —
   `python3 ${CLAUDE_SKILL_DIR}/scripts/render_map.py --campaign <name> --handle <handle> --state '<STATE_JSON>' --round 1`
4. Step through turns using the per-turn sequence (in SKILL.md Active DM Mode).
5. On combat end: update HP in character sheets, clear `## Active Combat`, narrate aftermath, run `tracker.py -c <campaign> clear`, and re-run `render_tracker.py` once with the final state and a "combat ended" marker (or clear tracker.html) — the meta-refresh dashboard otherwise keeps showing a live fight that's over. Mapped combat: also emit the down-cue on its own line — `🗺 **Map:** *down — theater of the mind*` — and clear the projector page:
   `python3 ${CLAUDE_SKILL_DIR}/scripts/render_map.py --campaign <name> --clear`

**No XP.** This is a milestone-leveling fork — combat end awards no XP. Leveling happens only at
`/dm:dnd beat complete`. Narrate loot/consequences in the aftermath send; do not send an XP block.
```

- [ ] **Step 5: Add the sidecar note to templates/map-list.md**

Append to the italic header paragraph (after "...acquirable archetypes you can find or print."):

```markdown
Each entry gets a grid-spec sidecar at `maps/<handle>.grid.json` (authored at prep
step 4 — dims + terrain only) that drives the combat grid and the projected overlay.
```

- [ ] **Step 6: Run the prose tests**

Run: `python -m pytest tests/test_grid_prose.py tests/test_asset_lists.py tests/test_prep_skill_prose.py -v`
Expected: PASS (including pre-existing prep-prose tests — step 4's regex anchor "Asset shopping lists" and step numbering are unchanged).

- [ ] **Step 7: Commit**

```bash
git add skills/dnd/SKILL-commands.md skills/dnd/templates/map-list.md tests/test_grid_prose.py
git commit -m "feat: grid-spec authoring in prep + mapped combat start/end procedure"
```

---

### Task 9: Prose — SKILL-scripts.md syntax sections

**Files:**
- Modify: `skills/dnd/SKILL-scripts.md` (two new `##` sections; place Grid after "## Combat Script" at line ~78, and Battle-Map Render after "## Combat-Tracker Render" at line ~350, matching the doc's grouping)
- Test: `tests/test_grid_prose.py` (extend)

**Interfaces:**
- Consumes: exact CLI syntax from Tasks 1–5.
- Produces: the canonical syntax reference the DM loads at session start.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_grid_prose.py`:

```python
class ScriptsDocTests(unittest.TestCase):
    def test_grid_section_exists(self):
        self.assertIn("## Grid Script — `scripts/grid.py`", SCRIPTS_DOC)

    def test_grid_section_covers_all_subcommands(self):
        for cmd in ("validate", "dist", "move", "range", "aoe"):
            self.assertIn(f"grid.py {cmd}", SCRIPTS_DOC)

    def test_render_map_section_exists(self):
        self.assertIn("## Battle-Map Render — `scripts/render_map.py`",
                      SCRIPTS_DOC)

    def test_render_map_clear_documented(self):
        self.assertIn("--clear", SCRIPTS_DOC)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_grid_prose.py -v -k ScriptsDoc`
Expected: FAIL.

- [ ] **Step 3: Add the sections**

After the "## Combat Script — `scripts/combat.py`" section, insert:

````markdown
## Grid Script — `scripts/grid.py`

Combat-grid math for mapped tactical scenes. Stateless: the grid spec lives at
`<campaign>/maps/<handle>.grid.json`, positions live in the combat STATE_JSON
(optional `"pos": "C4"` per combatant), and every call passes both in. Tiles are
5 ft; diagonals cost 5 ft (2014 PHB); distance is Chebyshev. Run it for ALL
position math in mapped combat — movement legality, reach/range, AoE tiles —
never eyeball those.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/grid.py validate <spec.json>
# VALID, or INVALID + one error per line (exit 1). Hard gate — never play on INVALID.

python3 ${CLAUDE_SKILL_DIR}/scripts/grid.py dist C4 F7
# 15ft

python3 ${CLAUDE_SKILL_DIR}/scripts/grid.py move --from C4 --to F6 --speed 30 --spec <spec.json>
# OK cost=25ft
# ILLEGAL cost=40ft -- furthest reachable toward F6: E5 (30ft)
# UNREACHABLE F6

python3 ${CLAUDE_SKILL_DIR}/scripts/grid.py range --from C4 --to F7 --ft 60
# IN RANGE (dist=15ft) / OUT OF RANGE (dist=70ft)

python3 ${CLAUDE_SKILL_DIR}/scripts/grid.py aoe --shape cone --origin D4 --size 20 --dir NE --spec <spec.json>
# 9 tiles: E3 E4 F2 F3 F4 ...
```

Shapes: `sphere` (radius, origin included) and `cube` (cardinal `--dir` only) are
exact on this metric; `cone`/`line` are grid approximations. Line-of-sight and
cover are NOT scripted — `blocks_los` terrain markers are in the spec for your
reasoning; adjudicate cover in prose.

## Battle-Map Render — `scripts/render_map.py`

Player-facing projector page `<campaign>/map.html` (meta-refresh, like the
tracker). Draws `maps/<handle>.png` (or .jpg/.jpeg/.webp) stretched to the grid,
the A1 coordinate overlay, and a token per combatant at its `"pos"` — combatants
with `"hidden": true` are never drawn. Run it in step d2 of every mapped combat
turn with the SAME STATE_JSON as render_tracker.py, and once at combat start.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_map.py --campaign <name> --handle <handle> --state '<STATE_JSON>' --round <n>
python3 ${CLAUDE_SKILL_DIR}/scripts/render_map.py --campaign <name> --clear   # idle screen between fights
```
````

- [ ] **Step 4: Run the full prose suite**

Run: `python -m pytest tests/test_grid_prose.py tests/test_no_display_refs.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/dnd/SKILL-scripts.md tests/test_grid_prose.py
git commit -m "docs: grid.py + render_map.py syntax in SKILL-scripts.md"
```

---

### Task 10: Docs + version bump

**Files:**
- Modify: `docs/ARCHITECTURE.md` (script inventory + rendering table)
- Modify: `CONTEXT.md` (glossary terms)
- Modify: `VERSION`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `skills/dnd/SKILL.md` frontmatter description, `CHANGELOG.md` (2.3.0 → 2.4.0)

**Interfaces:**
- Consumes: everything above, by name.
- Produces: released 2.4.0 docs surface.

- [ ] **Step 1: ARCHITECTURE.md**

Add to the table-time mechanics script table (section 3):

```markdown
| `grid.py` | Mapped-combat math: spec validate, Chebyshev dist, Dijkstra movement (difficult ×2 / impassable), range, sphere/cube/cone/line AoE | R `<campaign>/maps/<handle>.grid.json` |
```

Add to the rendering table:

```markdown
| `render_map.py` | Player-facing battle map `<campaign>/map.html` (meta-refresh): map image + A1 grid overlay + tokens from STATE_JSON `pos`; `--clear` = idle screen | R grid spec + maps/ images, W map.html |
```

Update the combat.py row's "Reads / writes" note to mention the optional `pos`/`hidden` STATE_JSON fields, and mention the grid spec + map cue in whatever section describes the prep asset pass and the per-turn loop (1–2 sentences each, in the file's existing style — its header requires the update).

- [ ] **Step 2: CONTEXT.md glossary entries**

Add, following the existing format:

```markdown
**Mapped combat**:
A fight at a location matching a `map-list.md` handle (or one the host names). Gets the
map cue, the grid spec, `"pos"` fields in STATE_JSON, and per-turn `render_map.py`
refreshes. Every other fight is theater of the mind — no cue, no grid, no positions.
_Avoid_: "grid combat", "tactical mode".

**Grid spec**:
`<campaign>/maps/<handle>.grid.json` — cols/rows dims + terrain regions (`difficult` /
`impassable` / `blocks_los`) for one shopping-list map. Authored at prep step 4 under
asset-pass spoiler discipline (terrain only); host-confirmed dims at first use
(`"confirmed": true`); hard-gated by `grid.py validate`. The spec is rules truth — the
projected image is decoration.
_Avoid_: "battle map" for the JSON (that's the image), "map spec".

**Map cue**:
The standalone chat block `🗺 **Map:** *<handle>*` (up) / `🗺 **Map:** *down — theater
of the mind*` (down) telling the host to raise or drop the battle map. Same contract as
the sound cue: own line, listed handles only, never invented.
_Avoid_: inlining it into narration; cueing unlisted maps.
```

- [ ] **Step 3: Version bump to 2.4.0**

Check every occurrence first:

```bash
git grep -n "2\.3\.0" -- VERSION .claude-plugin/plugin.json .claude-plugin/marketplace.json skills/dnd/SKILL.md CHANGELOG.md
```

- `VERSION`: `2.3.0` → `2.4.0`
- `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`: version fields → `2.4.0`
- `skills/dnd/SKILL.md` frontmatter description: `v2.3.0` → `v2.4.0`
- Do NOT touch `skills/dnd-bak-v2-3-0/` (versioned backup copy — its name and contents stay).
- `CHANGELOG.md`: add at top, matching the existing entry format:

```markdown
## 2.4.0 — 2026-07-16

- Combat grid for mapped scenes: per-map grid spec (`maps/<handle>.grid.json`,
  authored at prep, host-confirmed dims at first use), `grid.py` math engine
  (movement/range/AoE, 5-ft diagonals), positions in STATE_JSON.
- Map cue block (`🗺 **Map:**`) mirroring the sound cue; player-facing projector
  page `map.html` via `render_map.py` (tokens, hidden combatants excluded,
  idle screen between fights). Tracker shows positions.
- Supporting-cast NPC tier: 6–8 index-only NPCs seeded at `new` and `prep`,
  promoted to full entries before first substantive dialogue.
```

- [ ] **Step 4: Full suite + commit**

Run: `python -m pytest tests/ -v`
Expected: PASS — all files, no regressions.

```bash
git add docs/ARCHITECTURE.md CONTEXT.md VERSION .claude-plugin/plugin.json .claude-plugin/marketplace.json skills/dnd/SKILL.md CHANGELOG.md
git commit -m "docs: architecture + glossary for combat grid; bump to 2.4.0"
```

---

## Post-plan verification (Verify stage, not a task)

- Run the full suite: `python -m pytest tests/ -v` — green.
- Probe session per docs/probes methodology on a **scratch** campaign root (`DND_CAMPAIGN_ROOT` pointed at a temp dir — never the live `~/.claude/dnd/`): prep a small campaign, confirm grid specs authored + validated; start a fight on a listed map; exercise cue up, first-use dims confirm, placement, a legal move, an illegal move (expect in-fiction constraint + furthest-reachable offer), an AoE, a hidden reveal, combat end (down-cue + idle map.html). Open map.html and tracker.html in a browser and eyeball tokens/positions.
- Supporting-cast probe: run `new`, count supporting rows (6–8), force a scene on one, confirm promotion before dialogue.

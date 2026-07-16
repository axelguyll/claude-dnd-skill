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

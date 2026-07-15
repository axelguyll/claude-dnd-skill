#!/usr/bin/env python3
"""
render_tracker.py — emit a live combat-tracker HTML file (DM-side dashboard).

Merges the ephemeral combat STATE_JSON from combat.py with the persisted
tracker.json (conditions / concentration / death saves) and the bundled SRD
condition text, and writes <campaign>/tracker.html. The file carries a
meta-refresh so the DM's browser tab reloads itself each combat turn.

No server — a self-contained local page opened over file://.

Usage:
    python3 render_tracker.py --campaign <name> --state '<combatants_json>' [--round N]
        combatants_json: the STATE_JSON array printed by `combat.py init`.
        Writes <campaign_dir>/tracker.html and prints its path.
"""
from __future__ import annotations

import argparse
import html
import json

from paths import find_campaign, srd_path, campaign_ruleset


def condition_effects(srd: dict) -> dict:
    """Map condition index -> one-line effect text drawn from the SRD."""
    out = {}
    for c in srd.get("conditions", []):
        idx = str(c.get("index", c.get("name", ""))).lower()
        line = " ".join(
            part.lstrip("-• ").strip()
            for part in str(c.get("description", "")).splitlines()
            if part.strip()
        )
        out[idx] = line
    return out


def _merge_conditions(combatant: dict, tracker_state: dict) -> list:
    key = str(combatant["name"]).lower()
    persisted = tracker_state.get(key, {})
    return list(dict.fromkeys(
        [str(x).lower() for x in combatant.get("conditions", [])]
        + [str(x).lower() for x in persisted.get("conditions", [])]
    ))


def _extras(name: str, tracker_state: dict) -> dict:
    e = tracker_state.get(str(name).lower(), {})
    return {
        "concentration": e.get("concentration"),
        "death_saves": e.get("death_saves", {"successes": 0, "failures": 0, "stable": False}),
    }


def render_tracker_html(combatants: list, round_num: int,
                        tracker_state: dict, cond_effects: dict) -> str:
    rows = []
    for i, c in enumerate(combatants):
        name = html.escape(str(c["name"]))
        hp = c.get("hp", 0)
        max_hp = c.get("max_hp", hp) or 1
        pct = max(0, min(100, round(100 * hp / max_hp)))
        ac = html.escape(str(c.get("ac", "—")))
        init = html.escape(str(c.get("initiative", "—")))
        active = " active" if i == 0 else ""

        conds = _merge_conditions(c, tracker_state)
        if conds:
            cond_html = "".join(
                f'<span class="cond">{html.escape(cn)}'
                f'<em>{html.escape(cond_effects.get(cn, ""))}</em></span>'
                for cn in conds)
        else:
            cond_html = '<span class="none">—</span>'

        ex = _extras(c["name"], tracker_state)
        conc = (f'<div class="conc">◆ concentrating: '
                f'{html.escape(str(ex["concentration"]))}</div>'
                if ex["concentration"] else "")
        ds = ex["death_saves"]
        ds_html = ""
        if ds.get("successes") or ds.get("failures"):
            ds_html = (f'<div class="ds">death saves — ✔{ds.get("successes", 0)} '
                       f'✘{ds.get("failures", 0)}'
                       f'{" (stable)" if ds.get("stable") else ""}</div>')

        rows.append(
            f'<div class="row{active}">'
            f'<div class="init">{init}</div>'
            f'<div class="main"><div class="name">{name}</div>'
            f'<div class="conds">{cond_html}</div>{conc}{ds_html}</div>'
            f'<div class="hpbox"><div class="hpbar"><span style="width:{pct}%"></span></div>'
            f'<div class="hptext">{hp}/{max_hp} HP · AC {ac}</div></div>'
            f'</div>')

    body = "\n".join(rows)
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="4">
<title>Combat — Round {round_num}</title>
<style>
 body{{background:#14110e;color:#e8dcc8;font:15px/1.4 system-ui,sans-serif;margin:0;padding:16px}}
 h1{{font-size:18px;letter-spacing:.08em;text-transform:uppercase;color:#c9a86a;margin:0 0 12px}}
 .row{{display:flex;gap:12px;align-items:center;padding:10px 12px;border:1px solid #2c2620;border-radius:8px;margin-bottom:8px;background:#1c1813}}
 .row.active{{border-color:#c9a86a;box-shadow:inset 0 0 0 1px #c9a86a;background:#241d14}}
 .init{{font-size:20px;font-weight:700;color:#c9a86a;width:34px;text-align:center}}
 .main{{flex:1}} .name{{font-weight:600;font-size:16px}} .conds{{margin-top:3px}}
 .cond{{display:inline-block;background:#3a2c1c;color:#f0c987;border-radius:4px;padding:1px 7px;margin:2px 4px 0 0;font-size:12px}}
 .cond em{{display:block;font-style:normal;color:#b7a488;font-size:11px}}
 .none{{color:#6b6155}} .conc{{color:#8fb7d6;font-size:12px;margin-top:3px}}
 .ds{{color:#d68f8f;font-size:12px;margin-top:3px}}
 .hpbox{{width:150px}} .hpbar{{height:8px;background:#2c2620;border-radius:4px;overflow:hidden}}
 .hpbar span{{display:block;height:100%;background:#7fae5f}}
 .hptext{{font-size:12px;color:#b7a488;margin-top:3px;text-align:right}}
</style></head><body>
<h1>Combat — Round {round_num}</h1>
{body}
</body></html>'''


def main(argv=None):
    p = argparse.ArgumentParser(description="Render combat-tracker HTML.")
    p.add_argument("--campaign", required=True)
    p.add_argument("--state", required=True, help="STATE_JSON array from combat.py init")
    p.add_argument("--round", type=int, default=1)
    args = p.parse_args(argv)

    combatants = json.loads(args.state)
    camp = find_campaign(args.campaign)
    camp.mkdir(parents=True, exist_ok=True)

    tracker_state = {}
    tj = camp / "tracker.json"
    if tj.exists():
        try:
            tracker_state = json.loads(tj.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            tracker_state = {}

    try:
        path = srd_path(campaign_ruleset(args.campaign))
        srd = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        try:
            srd = json.loads(srd_path(None).read_text(encoding="utf-8"))
        except Exception:
            srd = {"conditions": []}
    effects = condition_effects(srd)

    out = camp / "tracker.html"
    out.write_text(render_tracker_html(combatants, args.round, tracker_state, effects),
                   encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()

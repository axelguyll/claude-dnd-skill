#!/usr/bin/env python3
"""
render_assets.py — emit the DM-side asset-hub HTML (maps + ambient + SFX).

Parses the three filled shopping lists in the campaign dir and writes
<campaign>/assets.html, pre-wired to canonical filenames the host drops into
maps/ and sounds/. Static: it is NOT regenerated during play and carries no
meta-refresh, so playing ambient loops are never interrupted by a tracker regen.

No server — a self-contained local page opened over file://.

Usage:
    python3 render_assets.py --campaign <name>
        Reads <campaign>/{map-list,ambient-list,sfx-list}.md (any missing list is
        treated as empty), writes <campaign>/assets.html, ensures maps/ and
        sounds/ exist, and prints the html path.
"""
from __future__ import annotations

import argparse
import html
import re

from paths import find_campaign

_ENTRY = re.compile(
    r'^-\s+\*\*(?P<handle>.+?)\*\*\s*[—–-]+\s*(?P<body>.*?)\s*File:\s*(?P<file>\S+)\s*$')
_HINT = re.compile(r'\*(?:Acquire|Find):\*.*$')


def parse_asset_list(text: str) -> list:
    """Parse an asset-list markdown file into [{handle, desc, file}]."""
    items = []
    for raw in text.splitlines():
        m = _ENTRY.match(raw.strip())
        if not m:
            continue
        desc = _HINT.sub("", m.group("body")).strip().rstrip(".").strip()
        items.append({"handle": m.group("handle").strip(),
                      "desc": desc,
                      "file": m.group("file").strip()})
    return items


def _section_maps(maps: list) -> str:
    if not maps:
        return '<p class="none">No maps.</p>'
    out = []
    for m in maps:
        handle = html.escape(m["handle"])
        file_ = html.escape(m["file"])
        desc_html = f'<span class="desc">{html.escape(m["desc"])}</span>' if m["desc"] else ""
        out.append(
            f'<figure><a href="{file_}" target="_blank" rel="noopener">'
            f'<img src="{file_}" alt="{handle}" loading="lazy"></a>'
            f'<figcaption>{handle}{desc_html}</figcaption></figure>')
    return "".join(out)


def _section_audio(items: list, prefix: str, loop: bool) -> str:
    if not items:
        return '<p class="none">None.</p>'
    out = []
    for i, a in enumerate(items):
        aid = f"{prefix}{i}"
        loop_attr = " loop" if loop else ""
        icon = "▶" if loop else "🔊"
        onclick = f"tog('{aid}',this)" if loop else f"one('{aid}')"
        out.append(
            f'<div class="asset">'
            f'<audio id="{aid}"{loop_attr} src="{html.escape(a["file"])}"></audio>'
            f'<button onclick="{onclick}">{icon} {html.escape(a["handle"])}</button>'
            f'<span class="desc">{html.escape(a["desc"])}</span></div>')
    return "".join(out)


def render_assets_html(maps: list, ambient: list, sfx: list) -> str:
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>Asset Hub</title>
<style>
 body{{background:#14110e;color:#e8dcc8;font:15px/1.5 system-ui,sans-serif;margin:0;padding:16px}}
 h2{{font-size:15px;letter-spacing:.08em;text-transform:uppercase;color:#c9a86a;margin:20px 0 8px;border-bottom:1px solid #2c2620;padding-bottom:4px}}
 .maps{{display:flex;flex-wrap:wrap;gap:12px}}
 figure{{margin:0}} figure img{{max-width:220px;border-radius:6px;display:block}}
 figcaption{{font-size:12px;color:#b7a488;margin-top:4px}}
 .asset{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
 button{{background:#3a2c1c;color:#f0c987;border:1px solid #5a4426;border-radius:6px;padding:6px 12px;font-size:14px;cursor:pointer}}
 button.on{{background:#5a4426;color:#ffe4a8}}
 .desc{{font-size:12px;color:#b7a488}} .none{{color:#6b6155}}
</style></head><body>
<h2>Maps</h2>
<div class="maps">{_section_maps(maps)}</div>
<h2>Ambient</h2>
{_section_audio(ambient, "amb", True)}
<h2>SFX</h2>
{_section_audio(sfx, "sfx", False)}
<script>
 function one(id){{var a=document.getElementById(id);a.currentTime=0;a.play();}}
 function tog(id,btn){{var a=document.getElementById(id);
  if(a.paused){{a.play();btn.classList.add("on");}}
  else{{a.pause();btn.classList.remove("on");}}}}
</script>
</body></html>'''


def _read(camp, name: str) -> str:
    p = camp / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def main(argv=None):
    p = argparse.ArgumentParser(description="Render the asset-hub HTML.")
    p.add_argument("--campaign", required=True)
    args = p.parse_args(argv)

    camp = find_campaign(args.campaign)
    camp.mkdir(parents=True, exist_ok=True)
    (camp / "maps").mkdir(exist_ok=True)
    (camp / "sounds").mkdir(exist_ok=True)

    maps = parse_asset_list(_read(camp, "map-list.md"))
    ambient = parse_asset_list(_read(camp, "ambient-list.md"))
    sfx = parse_asset_list(_read(camp, "sfx-list.md"))

    out = camp / "assets.html"
    out.write_text(render_assets_html(maps, ambient, sfx), encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()

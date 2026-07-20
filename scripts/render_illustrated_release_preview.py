#!/usr/bin/env python3
"""Render the current Illustrated release preview and structural quality proof."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from anidiagram.icon_system import ILLUSTRATED_ICON_SYSTEM_VERSION
from anidiagram.illustrated_registry import illustrated_definition, illustrated_icon_ids
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    "agent": "Agent",
    "operator": "Operator",
    "tool": "Tool",
    "output": "Output",
    "database": "Database",
    "api": "API",
    "search": "Search",
    "memory": "Memory",
    "file": "File",
    "folder": "Folder",
    "cloud": "Cloud",
    "shield": "Shield",
    "user": "User",
    "server": "Server",
    "ai-model": "AI Model",
    "message-queue": "Message Queue",
}


def render_svg() -> str:
    style = load_style(ROOT / "styles" / "illustrated-character-v2-concept.json")
    palette = illustrated_tokens_for_style(style)
    cards = []
    for index, icon_id in enumerate(illustrated_icon_ids()):
        column, row = index % 4, index // 4
        x, y = 52 + column * 344, 142 + row * 274
        artwork = render_character_v2_icon(
            illustrated_definition(icon_id), f"release-{icon_id}", x + 154, y + 114, 154, palette
        )
        cards.append(
            f'''<g class="release-card" data-icon="{icon_id}">
  <rect x="{x}" y="{y}" width="308" height="238" rx="26" fill="#fffaf0" stroke="#d8d1c3" stroke-width="1.8" />
  {artwork}
  <text x="{x + 154}" y="{y + 204}" class="icon-title" text-anchor="middle" fill="#283047">{LABELS[icon_id]}</text>
  <text x="{x + 154}" y="{y + 224}" class="role" text-anchor="middle" fill="#6d7182">{illustrated_definition(icon_id).semantic_role}</text>
</g>'''
        )
    rows = (len(illustrated_icon_ids()) + 3) // 4
    height = 172 + rows * 274
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1480" height="{height}" viewBox="0 0 1480 {height}" role="img" aria-labelledby="title desc">
<title id="title">Illustrated {ILLUSTRATED_ICON_SYSTEM_VERSION} release preview</title>
<desc id="desc">Sixteen approved static Illustrated icons.</desc>
<style>
  .title {{ font: 760 40px ui-sans-serif, system-ui, sans-serif; }}
  .subtitle {{ font: 430 16px ui-sans-serif, system-ui, sans-serif; }}
  .icon-title {{ font: 740 20px ui-sans-serif, system-ui, sans-serif; }}
  .role {{ font: 620 11px ui-monospace, SFMono-Regular, monospace; }}
</style>
<rect width="100%" height="100%" fill="#ececf3" />
<text x="52" y="62" class="title" fill="#172033">Illustrated · {ILLUSTRATED_ICON_SYSTEM_VERSION}</text>
<text x="52" y="94" class="subtitle" fill="#667085">16 approved icons · 16 public automatic performances</text>
{''.join(cards)}
</svg>'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "assets" / "illustrated" / "previews" / f"illustrated-{ILLUSTRATED_ICON_SYSTEM_VERSION}.svg",
    )
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    svg = render_svg()
    args.out.write_text(svg, encoding="utf-8")
    root = ET.fromstring(svg)
    ids = [element.attrib["id"] for element in root.iter() if "id" in element.attrib]
    quality = {
        "system": "illustrated",
        "version": ILLUSTRATED_ICON_SYSTEM_VERSION,
        "status": "approved",
        "icon_count": len(illustrated_icon_ids()),
        "duplicate_ids": sorted({item for item in ids if ids.count(item) > 1}),
        "errors": 0 if len(ids) == len(set(ids)) else 1,
        "motion_status": "approved",
    }
    quality_path = args.out.with_suffix(".quality.json")
    quality_path.write_text(json.dumps(quality, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.out.resolve())
    print(quality_path.resolve())


if __name__ == "__main__":
    main()

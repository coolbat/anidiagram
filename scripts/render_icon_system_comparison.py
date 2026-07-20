#!/usr/bin/env python3
"""Render a controlled visual comparison of overlapping icon systems."""

from __future__ import annotations

import argparse
import html
from pathlib import Path

from anidiagram.diagram_core.adapter import render_approved_icon
from anidiagram.diagram_core.tokens import icon_tokens_for_style
from anidiagram.illustrated_character_v2_icons import character_v2_definition
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style, role_style


ROOT = Path(__file__).resolve().parents[1]
ICON_IDS = ("agent", "operator", "tool", "output")
ROLES = {
    "agent": "agent",
    "operator": "source",
    "tool": "tool",
    "output": "output",
}
CAPTIONS = {
    "agent": "reason → process → result",
    "operator": "person → operate → confirm",
    "tool": "prepare → execute → complete",
    "output": "package → deliver → confirm",
}


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _card(
    icon_id: str,
    x: int,
    y: int,
    system: str,
    style: dict,
) -> str:
    width, height = 326, 300
    role = ROLES[icon_id]
    colors = role_style(style, role)
    stroke = colors.get("stroke", "#8265d6")
    fill = colors.get("fill", "#fffaf0")
    text = colors.get("text", "#283047")
    art_size = 160
    art_x = x + (width - art_size) / 2
    art_y = y + 34
    if system == "diagram-core-v1":
        artwork = render_approved_icon(
            icon_id,
            f"comparison.core.{icon_id}",
            size=art_size,
            x=art_x,
            y=art_y,
            tokens=icon_tokens_for_style(style, role),
        )
        source = "96×96 canonical system glyph"
    else:
        definition = character_v2_definition(icon_id)
        if definition is None:
            raise RuntimeError(f"missing Illustrated Character v2 icon: {icon_id}")
        artwork = render_character_v2_icon(
            definition,
            f"comparison-illustrated-{icon_id}",
            x + width / 2,
            art_y + art_size / 2,
            art_size,
            illustrated_tokens_for_style(style),
        )
        source = "Illustrated 2.0.0 · 120×120 semantic micro-scene"
    return f"""
  <g class="comparison-card" data-icon="{_esc(icon_id)}" data-system="{_esc(system)}">
    <rect x="{x}" y="{y}" width="{width}" height="{height}" rx="28"
          fill="{_esc(fill)}" stroke="{_esc(stroke)}" stroke-width="2.2" />
    <rect x="{x + 18}" y="{y + 18}" width="92" height="26" rx="13"
          fill="{_esc(stroke)}" opacity="0.12" />
    <text x="{x + 64}" y="{y + 36}" class="system-chip" text-anchor="middle"
          fill="{_esc(stroke)}">{_esc(icon_id.upper())}</text>
    {artwork}
    <text x="{x + width / 2}" y="{y + 224}" class="icon-title" text-anchor="middle"
          fill="{_esc(text)}">{_esc(icon_id.replace('-', ' ').title())}</text>
    <text x="{x + width / 2}" y="{y + 251}" class="icon-caption" text-anchor="middle"
          fill="{_esc(text)}">{_esc(CAPTIONS[icon_id])}</text>
    <text x="{x + width / 2}" y="{y + 279}" class="icon-source" text-anchor="middle"
          fill="#77758a">{_esc(source)}</text>
  </g>"""


def render_svg() -> str:
    style = load_style(ROOT / "styles" / "illustrated-character-v2-concept.json")
    width, height = 1480, 980
    card_x = (56, 402, 748, 1094)
    core_cards = "\n".join(
        _card(icon_id, x, 190, "diagram-core-v1", style)
        for icon_id, x in zip(ICON_IDS, card_x)
    )
    v2_cards = "\n".join(
        _card(icon_id, x, 590, "illustrated", style)
        for icon_id, x in zip(ICON_IDS, card_x)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
  <title id="title">Diagram Core and Illustrated visual comparison</title>
  <desc id="description">Four shared semantics rendered at the same display size.</desc>
  <style>
    .page-title {{ font: 760 40px ui-sans-serif, system-ui, sans-serif; letter-spacing: -0.02em; }}
    .page-subtitle {{ font: 400 17px ui-sans-serif, system-ui, sans-serif; }}
    .row-title {{ font: 740 24px ui-sans-serif, system-ui, sans-serif; }}
    .row-note {{ font: 450 14px ui-sans-serif, system-ui, sans-serif; }}
    .system-chip {{ font: 760 11px ui-sans-serif, system-ui, sans-serif; letter-spacing: 0.08em; }}
    .icon-title {{ font: 740 22px ui-sans-serif, system-ui, sans-serif; }}
    .icon-caption {{ font: 520 14px ui-sans-serif, system-ui, sans-serif; }}
    .icon-source {{ font: 430 12px ui-sans-serif, system-ui, sans-serif; }}
  </style>
  <rect width="100%" height="100%" fill="#fffaf0" />
  <circle cx="1352" cy="80" r="118" fill="#eee9ff" opacity="0.72" />
  <circle cx="94" cy="900" r="132" fill="#e5f7ef" opacity="0.78" />
  <text x="56" y="70" class="page-title" fill="#283047">Diagram Core vs Illustrated</text>
  <text x="56" y="106" class="page-subtitle" fill="#6d7182">相同语义 · 相同 160px 展示面积 · 保留各自原生构图与配色 · 静态姿态对比</text>

  <text x="56" y="157" class="row-title" fill="#283047">Diagram Core v1</text>
  <text x="276" y="157" class="row-note" fill="#6d7182">紧凑、系统化、适合架构节点与高密度画布</text>
  {core_cards}

  <line x1="56" y1="550" x2="1420" y2="550" stroke="#dcd4c5" stroke-width="1.5" />
  <text x="56" y="557" class="row-title" fill="#283047">Illustrated</text>
  <text x="350" y="557" class="row-note" fill="#6d7182">叙事型微场景、语义动作更明显、视觉重量更大</text>
  {v2_cards}
</svg>
"""


def render_html(svg: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Diagram Core vs Illustrated</title>
  <style>
    html, body {{ margin: 0; min-height: 100%; background: #171827; }}
    body {{ display: grid; place-items: center; padding: 24px; box-sizing: border-box; }}
    svg {{ display: block; width: min(1480px, 100%); height: auto; border-radius: 28px; box-shadow: 0 28px 90px rgba(0,0,0,.34); }}
  </style>
</head>
<body>
{svg}
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=ROOT / "outputs" / "icon-system-comparison")
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    svg = render_svg()
    svg_path = args.outdir / "diagram-core-vs-illustrated.svg"
    html_path = args.outdir / "diagram-core-vs-illustrated.html"
    svg_path.write_text(svg, encoding="utf-8")
    html_path.write_text(render_html(svg), encoding="utf-8")
    print(svg_path.resolve())
    print(html_path.resolve())


if __name__ == "__main__":
    main()

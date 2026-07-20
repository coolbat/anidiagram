#!/usr/bin/env python3
"""Render Illustrated expansion Batch 1 static visual-review proofs."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

from anidiagram.illustrated_expansion_batch_1 import (
    ILLUSTRATED_EXPANSION_BATCH_1_METADATA,
    expansion_batch_1_definition,
    expansion_batch_1_icon_ids,
)
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style, role_style


ROOT = Path(__file__).resolve().parents[1]
ICON_IDS = expansion_batch_1_icon_ids()
ROLES = {"database": "memory", "api": "source", "search": "process", "memory": "memory"}
CAPTIONS = {
    "database": "ingest · store · persist",
    "api": "request · route · respond",
    "search": "query · scan · discover",
    "memory": "capture · index · recall",
}
LABELS = {"database": "Database", "api": "API", "search": "Search", "memory": "Memory"}


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _icon(icon_id: str, instance: str, cx: float, cy: float, size: float, style: dict) -> str:
    definition = expansion_batch_1_definition(icon_id)
    if definition is None:
        raise RuntimeError(f"missing Batch 1 candidate: {icon_id}")
    artwork = render_character_v2_icon(
        definition,
        instance,
        cx,
        cy,
        size,
        illustrated_tokens_for_style(style),
    )
    return (
        f'<g class="candidate-instance" data-icon="{_esc(icon_id)}" '
        f'data-instance="{_esc(instance)}" data-size="{size:g}">{artwork}</g>'
    )


def _large_card(icon_id: str, x: int, y: int, style: dict, theme: str) -> str:
    colors = role_style(style, ROLES[icon_id])
    return f'''
    <g class="candidate-card" data-theme="{_esc(theme)}" data-icon="{_esc(icon_id)}">
      <rect x="{x}" y="{y}" width="310" height="260" rx="26"
            fill="{_esc(colors['fill'])}" stroke="{_esc(colors['stroke'])}" stroke-width="2.2" />
      <rect x="{x + 18}" y="{y + 17}" width="104" height="25" rx="12.5"
            fill="{_esc(colors['stroke'])}" opacity="0.16" />
      <text x="{x + 70}" y="{y + 34}" class="chip" text-anchor="middle"
            fill="{_esc(colors['stroke'])}">{_esc(icon_id.upper())}</text>
      {_icon(icon_id, f'{theme}-{icon_id}', x + 155, y + 105, 142, style)}
      <text x="{x + 155}" y="{y + 211}" class="icon-title" text-anchor="middle"
            fill="{_esc(colors['text'])}">{_esc(LABELS[icon_id])}</text>
      <text x="{x + 155}" y="{y + 237}" class="caption" text-anchor="middle"
            fill="{_esc(colors['text'])}" opacity="0.72">{_esc(CAPTIONS[icon_id])}</text>
    </g>'''


def _size_card(icon_id: str, x: int, y: int, warm_style: dict) -> str:
    sizes = (64, 96, 120)
    centers = (x + 54, x + 151, x + 253)
    icons = "\n".join(
        _icon(icon_id, f"size-{icon_id}-{size}", cx, y + 139, size, warm_style)
        for size, cx in zip(sizes, centers)
    )
    labels = "".join(
        f'<text x="{cx}" y="{y + 224}" class="size-label" text-anchor="middle" fill="#667085">{size}px</text>'
        for size, cx in zip(sizes, centers)
    )
    guides = "".join(
        f'<rect x="{cx - size / 2}" y="{y + 139 - size / 2}" width="{size}" height="{size}" rx="12" '
        f'fill="none" stroke="#c8c2b5" stroke-dasharray="4 5" opacity="0.58" />'
        for size, cx in zip(sizes, centers)
    )
    definition = expansion_batch_1_definition(icon_id)
    return f'''
    <g class="size-card" data-icon="{_esc(icon_id)}">
      <rect x="{x}" y="{y}" width="310" height="352" rx="26" fill="#fffaf0" stroke="#d8d1c3" stroke-width="1.6" />
      <text x="{x + 20}" y="{y + 38}" class="row-title" fill="#283047">{_esc(LABELS[icon_id])}</text>
      <text x="{x + 290}" y="{y + 38}" class="status" text-anchor="end" fill="#8265d6">STATIC APPROVED</text>
      {guides}
      {icons}
      {labels}
      <line x1="{x + 20}" y1="{y + 246}" x2="{x + 290}" y2="{y + 246}" stroke="#e4ded1" />
      <text x="{x + 20}" y="{y + 276}" class="semantic" fill="#283047">{_esc(definition.semantic_role)}</text>
      <text x="{x + 20}" y="{y + 310}" class="caption" fill="#6d7182">subject · action · outcome</text>
      <text x="{x + 20}" y="{y + 332}" class="caption" fill="#6d7182">motion · approved public contract</text>
    </g>'''


def render_svg(warm_style: dict, deep_style: dict) -> str:
    width, height = 1480, 1358
    card_x = (66, 408, 750, 1092)
    warm_cards = "\n".join(
        _large_card(icon_id, x, 175, warm_style, "warm") for icon_id, x in zip(ICON_IDS, card_x)
    )
    deep_cards = "\n".join(
        _large_card(icon_id, x, 555, deep_style, "deep-tech") for icon_id, x in zip(ICON_IDS, card_x)
    )
    size_cards = "\n".join(
        _size_card(icon_id, x, 946, warm_style) for icon_id, x in zip(ICON_IDS, card_x)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
  <title id="title">Illustrated expansion Batch 1 static review</title>
  <desc id="description">Database, API, Search, and Memory candidates in warm and Deep Tech themes plus 64, 96, and 120 pixel size proofs.</desc>
  <defs>
    <linearGradient id="deep-panel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#071026" />
      <stop offset="1" stop-color="#050816" />
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">
      <feDropShadow dx="0" dy="12" stdDeviation="18" flood-color="#111827" flood-opacity="0.15" />
    </filter>
  </defs>
  <style>
    .page-title {{ font: 760 40px ui-sans-serif, system-ui, sans-serif; letter-spacing: -0.025em; }}
    .subtitle {{ font: 430 16px ui-sans-serif, system-ui, sans-serif; }}
    .row-title {{ font: 760 22px ui-sans-serif, system-ui, sans-serif; }}
    .row-note {{ font: 450 14px ui-sans-serif, system-ui, sans-serif; }}
    .chip, .status {{ font: 760 10px ui-sans-serif, system-ui, sans-serif; letter-spacing: 0.08em; }}
    .icon-title {{ font: 740 21px ui-sans-serif, system-ui, sans-serif; }}
    .caption {{ font: 520 13px ui-sans-serif, system-ui, sans-serif; }}
    .semantic {{ font: 650 12px ui-monospace, SFMono-Regular, monospace; }}
    .size-label {{ font: 720 12px ui-monospace, SFMono-Regular, monospace; }}
  </style>
  <rect width="100%" height="100%" fill="#ececf3" />
  <text x="44" y="58" class="page-title" fill="#172033">Illustrated · Expansion Batch 1</text>
  <text x="44" y="88" class="subtitle" fill="#667085">Database · API · Search · Memory · static approved for Illustrated 2.1.0</text>

  <g filter="url(#shadow)"><rect x="44" y="116" width="1392" height="346" rx="32" fill="#fffaf0" /></g>
  <text x="66" y="157" class="row-title" fill="#283047">Canonical Warm</text>
  <text x="254" y="157" class="row-note" fill="#6d7182">配件按业务语义区分 · 勾仅用于明确确认</text>
  {warm_cards}

  <g filter="url(#shadow)"><rect x="44" y="496" width="1392" height="346" rx="32" fill="url(#deep-panel)" /></g>
  <text x="66" y="537" class="row-title" fill="#f8fafc">Deep Tech · Approved Ivory Ink</text>
  <text x="430" y="537" class="row-note" fill="#a5b4cc">验证米白描边与深色多语义配色兼容性</text>
  {deep_cards}

  <text x="44" y="900" class="row-title" fill="#283047">Static Readability · 64 / 96 / 120px</text>
  <text x="420" y="900" class="row-note" fill="#667085">64px 保留轮廓 · 96/120px 保留动作与结果线索 · 不为 24/32px 工具栏优化</text>
  {size_cards}
  <text x="1414" y="1340" class="row-note" text-anchor="end" fill="#667085">static approved · public Illustrated 2.1.0 · motion approved</text>
</svg>
'''


def render_html(svg: str) -> str:
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Illustrated Expansion Batch 1</title>
  <style>
    html, body {{ margin: 0; min-height: 100%; background: #151725; }}
    body {{ display: grid; place-items: center; padding: 24px; box-sizing: border-box; }}
    svg {{ display: block; width: min(1480px, 100%); height: auto; border-radius: 24px; box-shadow: 0 28px 90px rgba(0,0,0,.38); }}
  </style>
</head>
<body>{svg}</body>
</html>
'''


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=ROOT / "outputs" / "illustrated-expansion-batch-1",
    )
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    warm_style = load_style(ROOT / "styles" / "illustrated-character-v2-concept.json")
    deep_style = load_style(ROOT / "styles" / "deep-tech.json")
    svg = render_svg(warm_style, deep_style)
    svg_path = args.outdir / "illustrated-expansion-batch-1.svg"
    html_path = args.outdir / "illustrated-expansion-batch-1.html"
    png_path = args.outdir / "illustrated-expansion-batch-1.png"
    result_path = args.outdir / "result.json"
    svg_path.write_text(svg, encoding="utf-8")
    html_path.write_text(render_html(svg), encoding="utf-8")
    result = {
        **ILLUSTRATED_EXPANSION_BATCH_1_METADATA,
        "icons": list(ICON_IDS),
        "themes": ["canonical-warm", "deep-tech"],
        "sizes": [64, 96, 120],
        "artifacts": {"svg": svg_path.name, "html": html_path.name, "svg_sha256": _sha256(svg_path)},
    }
    if png_path.is_file():
        result["artifacts"]["png"] = png_path.name
        result["artifacts"]["png_sha256"] = _sha256(png_path)
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(svg_path.resolve())
    print(html_path.resolve())
    print(result_path.resolve())


if __name__ == "__main__":
    main()

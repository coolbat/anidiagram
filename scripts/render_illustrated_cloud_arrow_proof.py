#!/usr/bin/env python3
"""Render a narrow visual comparison for Illustrated Cloud arrow geometry."""

from __future__ import annotations

import argparse
import html
from pathlib import Path

from anidiagram.illustrated_character_icons import CharacterIconDefinition, CharacterPrimitive
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]


def _p(kind: str, part: str, **attrs: str) -> CharacterPrimitive:
    return CharacterPrimitive(kind=kind, part=part, attrs=attrs)


_BASE = (
    _p("circle", "wash", cx="58", cy="63", r="49", fill="sky-wash", stroke="none"),
    _p(
        "path",
        "cloud-shell",
        d="M28 91c-16 0-21-20-7-29-1-17 18-27 32-17 9-14 31-10 34 6 17-1 23 21 7 32Z",
        fill="sky",
        stroke="ink",
    ),
)


VARIANTS = {
    "a-open-stroke": {
        "label": "A · Open Stroke",
        "note": "轻量开放箭头 · 圆角端点",
        "upload": "M44 80V49M34 59l10-10 10 10",
        "download": "M76 47v31M66 68l10 10 10-10",
        "width": "4",
    },
    "b-slim-ribbon": {
        "label": "B · Slim Ribbon",
        "note": "窄线框箭身 · 比当前稿更轻",
        "upload": "M39 79V60h-7l12-13 12 13h-7v19Z",
        "download": "M71 48v19h-7l12 13 12-13h-7V48Z",
        "width": "3",
    },
    "c-curved-sync": {
        "label": "C · Curved Sync",
        "note": "柔和曲线流向 · 动态感更强",
        "upload": "M39 79c0-17 6-27 17-32M46 47h10l2 10",
        "download": "M81 48c0 17-6 27-17 32m10 0H64l-2-10",
        "width": "3.6",
    },
}


def cloud_variant(variant_id: str) -> CharacterIconDefinition:
    variant = VARIANTS[variant_id]
    return CharacterIconDefinition(
        icon="cloud",
        semantic_role="data-upload-download-sync",
        parts=("root", "wash", "cloud-shell", "upload-arrow", "download-arrow"),
        primitives=(
            *_BASE,
            _p(
                "path",
                "upload-arrow",
                d=variant["upload"],
                fill="none",
                stroke="violet",
                stroke_width=variant["width"],
            ),
            _p(
                "path",
                "download-arrow",
                d=variant["download"],
                fill="none",
                stroke="teal-dark",
                stroke_width=variant["width"],
            ),
        ),
    )


def _icon(
    variant_id: str,
    instance: str,
    cx: float,
    cy: float,
    size: float,
    style: dict,
) -> str:
    return render_character_v2_icon(
        cloud_variant(variant_id),
        instance,
        cx,
        cy,
        size,
        illustrated_tokens_for_style(style),
    )


def _card(variant_id: str, x: int, warm: dict, deep: dict) -> str:
    variant = VARIANTS[variant_id]
    sizes = (64, 96, 120)
    centers = (x + 72, x + 170, x + 278)
    size_icons = "\n".join(
        _icon(variant_id, f"{variant_id}-size-{size}", cx, 628, size, warm)
        for size, cx in zip(sizes, centers)
    )
    size_labels = "".join(
        f'<text x="{cx}" y="702" class="size" text-anchor="middle">{size}px</text>'
        for cx, size in zip(centers, sizes)
    )
    return f'''
    <g class="variant-card" data-variant="{html.escape(variant_id)}">
      <rect x="{x}" y="132" width="340" height="620" rx="30" fill="#fffaf0" stroke="#d7d0c2" stroke-width="2" />
      <text x="{x + 24}" y="176" class="card-title">{html.escape(variant['label'])}</text>
      <text x="{x + 24}" y="202" class="note">{html.escape(variant['note'])}</text>
      <rect x="{x + 24}" y="226" width="292" height="190" rx="24" fill="#e8f8fb" stroke="#43bdb7" stroke-width="2" />
      {_icon(variant_id, f'{variant_id}-warm', x + 170, 320, 168, warm)}
      <rect x="{x + 24}" y="438" width="292" height="150" rx="24" fill="#071026" stroke="#38bdf8" stroke-width="2" />
      {_icon(variant_id, f'{variant_id}-deep', x + 170, 513, 132, deep)}
      {size_icons}
      {size_labels}
      <text x="{x + 170}" y="730" class="status" text-anchor="middle">CLOUD BODY UNCHANGED</text>
    </g>'''


def render_svg(warm: dict, deep: dict) -> str:
    cards = "\n".join(
        _card(variant_id, x, warm, deep)
        for variant_id, x in zip(VARIANTS, (55, 450, 845))
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="810" viewBox="0 0 1240 810"
     role="img" aria-labelledby="title description">
  <title id="title">Illustrated Cloud arrow comparison</title>
  <desc id="description">Three internal upload and download arrow treatments for the unchanged Illustrated Cloud body.</desc>
  <style>
    .page-title {{ font: 760 38px ui-sans-serif, system-ui, sans-serif; fill: #172033; }}
    .subtitle {{ font: 450 16px ui-sans-serif, system-ui, sans-serif; fill: #667085; }}
    .card-title {{ font: 760 22px ui-sans-serif, system-ui, sans-serif; fill: #283047; }}
    .note {{ font: 520 13px ui-sans-serif, system-ui, sans-serif; fill: #6d7182; }}
    .size {{ font: 720 12px ui-monospace, SFMono-Regular, monospace; fill: #667085; }}
    .status {{ font: 760 10px ui-sans-serif, system-ui, sans-serif; fill: #8265d6; letter-spacing: .08em; }}
  </style>
  <rect width="100%" height="100%" fill="#ececf3" />
  <text x="55" y="60" class="page-title">Cloud · Internal Arrow Study</text>
  <text x="55" y="91" class="subtitle">仅比较云内一上一下两个线框箭头 · 云体、配色和尺寸规范保持不变</text>
  {cards}
  <text x="1185" y="786" class="subtitle" text-anchor="end">narrow visual proof · no Batch 2 promotion</text>
</svg>
'''


def render_html(svg: str) -> str:
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Illustrated Cloud Arrow Study</title>
  <style>
    html, body {{ margin: 0; min-height: 100%; background: #151725; }}
    body {{ display: grid; place-items: center; padding: 24px; box-sizing: border-box; }}
    svg {{ display: block; width: min(1240px, 100%); height: auto; border-radius: 24px; box-shadow: 0 28px 90px rgba(0,0,0,.38); }}
  </style>
</head>
<body>{svg}</body>
</html>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=ROOT / "outputs" / "illustrated-cloud-arrow-proof",
    )
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    warm = load_style(ROOT / "styles" / "illustrated-character-v2-concept.json")
    deep = load_style(ROOT / "styles" / "deep-tech.json")
    svg = render_svg(warm, deep)
    svg_path = args.outdir / "illustrated-cloud-arrow-proof.svg"
    html_path = args.outdir / "illustrated-cloud-arrow-proof.html"
    svg_path.write_text(svg, encoding="utf-8")
    html_path.write_text(render_html(svg), encoding="utf-8")
    print(svg_path.resolve())
    print(html_path.resolve())


if __name__ == "__main__":
    main()

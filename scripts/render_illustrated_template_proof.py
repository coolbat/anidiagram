#!/usr/bin/env python3
"""Render the approved warm versus deep-tech Illustrated token mapping."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

from anidiagram.illustrated_character_v2_icons import character_v2_definition
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style, role_style


ROOT = Path(__file__).resolve().parents[1]
ICON_IDS = ("agent", "operator", "tool", "output")
ROLES = {"agent": "agent", "operator": "source", "tool": "tool", "output": "output"}
CAPTIONS = {
    "agent": "input · reason · result",
    "operator": "person · operate · confirm",
    "tool": "prepare · execute · complete",
    "output": "artifact · deliver · confirm",
}
SWATCH_TOKENS = ("violet", "sky", "teal", "mint", "sun", "coral")


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _card(icon_id: str, x: int, y: int, style: dict, theme_id: str) -> str:
    width, height = 310, 260
    colors = role_style(style, ROLES[icon_id])
    stroke = colors["stroke"]
    fill = colors["fill"]
    text = colors["text"]
    definition = character_v2_definition(icon_id)
    if definition is None:
        raise RuntimeError(f"missing Illustrated icon: {icon_id}")
    artwork = render_character_v2_icon(
        definition,
        f"template-proof-{theme_id}-{icon_id}",
        x + width / 2,
        y + 96,
        154,
        illustrated_tokens_for_style(style),
    )
    return f"""
    <g class="theme-card" data-theme="{_esc(theme_id)}" data-icon="{_esc(icon_id)}">
      <rect x="{x}" y="{y}" width="{width}" height="{height}" rx="26"
            fill="{_esc(fill)}" stroke="{_esc(stroke)}" stroke-width="2.2" />
      <rect x="{x + 18}" y="{y + 17}" width="86" height="25" rx="12.5"
            fill="{_esc(stroke)}" opacity="0.16" />
      <text x="{x + 61}" y="{y + 34}" class="chip" text-anchor="middle"
            fill="{_esc(stroke)}">{_esc(icon_id.upper())}</text>
      {artwork}
      <text x="{x + width / 2}" y="{y + 208}" class="icon-title" text-anchor="middle"
            fill="{_esc(text)}">{_esc(icon_id.title())}</text>
      <text x="{x + width / 2}" y="{y + 234}" class="caption" text-anchor="middle"
            fill="{_esc(text)}" opacity="0.72">{_esc(CAPTIONS[icon_id])}</text>
    </g>"""


def _swatches(style: dict, x: int, y: int) -> str:
    palette = illustrated_tokens_for_style(style)
    parts = []
    for index, token in enumerate(SWATCH_TOKENS):
        cx = x + index * 28
        parts.append(
            f'<circle cx="{cx}" cy="{y}" r="8" fill="{_esc(palette[token])}" '
            f'stroke="{_esc(palette["ink"])}" stroke-width="1.2"><title>{_esc(token)}</title></circle>'
        )
    return "".join(parts)


def render_svg(warm_style: dict, deep_style: dict) -> str:
    width, height = 1480, 940
    card_x = (66, 408, 750, 1092)
    warm_cards = "\n".join(
        _card(icon_id, x, 188, warm_style, "warm") for icon_id, x in zip(ICON_IDS, card_x)
    )
    deep_cards = "\n".join(
        _card(icon_id, x, 584, deep_style, "deep-tech") for icon_id, x in zip(ICON_IDS, card_x)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
  <title id="title">Illustrated 2.0.0 template color proof</title>
  <desc id="description">The same four frozen icons in canonical warm and multicolor deep-tech palettes.</desc>
  <defs>
    <linearGradient id="deep-panel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#071026" />
      <stop offset="1" stop-color="#050816" />
    </linearGradient>
    <filter id="soft-shadow" x="-10%" y="-10%" width="120%" height="130%">
      <feDropShadow dx="0" dy="12" stdDeviation="18" flood-color="#111827" flood-opacity="0.12" />
    </filter>
  </defs>
  <style>
    .page-title {{ font: 760 40px ui-sans-serif, system-ui, sans-serif; letter-spacing: -0.025em; }}
    .subtitle {{ font: 430 16px ui-sans-serif, system-ui, sans-serif; }}
    .row-title {{ font: 760 23px ui-sans-serif, system-ui, sans-serif; }}
    .row-note {{ font: 450 14px ui-sans-serif, system-ui, sans-serif; }}
    .chip {{ font: 760 10px ui-sans-serif, system-ui, sans-serif; letter-spacing: 0.08em; }}
    .icon-title {{ font: 740 21px ui-sans-serif, system-ui, sans-serif; }}
    .caption {{ font: 520 13px ui-sans-serif, system-ui, sans-serif; letter-spacing: 0.015em; }}
  </style>
  <rect width="100%" height="100%" fill="#ececf3" />
  <text x="44" y="58" class="page-title" fill="#172033">Illustrated · Template Color Proof</text>
  <text x="44" y="88" class="subtitle" fill="#667085">相同几何 · 相同部件 ID · 仅由 illustrated_tokens 切换颜色</text>

  <g filter="url(#soft-shadow)">
    <rect x="44" y="116" width="1392" height="360" rx="32" fill="#fffaf0" />
  </g>
  <text x="66" y="159" class="row-title" fill="#283047">Canonical Warm</text>
  <text x="252" y="159" class="row-note" fill="#6d7182">默认插画配色 · 叙事友好 · 柔和纸张感</text>
  {_swatches(warm_style, 1250, 153)}
  {warm_cards}

  <g filter="url(#soft-shadow)">
    <rect x="44" y="512" width="1392" height="382" rx="32" fill="url(#deep-panel)" />
  </g>
  <path d="M1060 512h376v250c-96-70-187-73-276-13-56 38-100 25-100-34Z" fill="#11244b" opacity="0.56" />
  <text x="66" y="555" class="row-title" fill="#f8fafc">Deep Tech · Multicolor</text>
  <text x="325" y="555" class="row-note" fill="#a5b4cc">深色环境 · 保留紫/青/黄/绿语义层次 · 非单色染色</text>
  {_swatches(deep_style, 1250, 549)}
  {deep_cards}
  <text x="1414" y="918" class="row-note" text-anchor="end" fill="#667085">approved · public deep-tech template mapping</text>
</svg>
"""


def render_html(svg: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Illustrated Template Color Proof</title>
  <style>
    html, body {{ margin: 0; min-height: 100%; background: #151725; }}
    body {{ display: grid; place-items: center; padding: 24px; box-sizing: border-box; }}
    svg {{ display: block; width: min(1480px, 100%); height: auto; border-radius: 24px; box-shadow: 0 28px 90px rgba(0,0,0,.38); }}
  </style>
</head>
<body>
{svg}
</body>
</html>
"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=ROOT / "outputs" / "illustrated-template-proof",
    )
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    warm_style_path = ROOT / "styles" / "illustrated-character-v2-concept.json"
    deep_style_path = ROOT / "styles" / "deep-tech.json"
    warm_style = load_style(warm_style_path)
    deep_style = load_style(deep_style_path)
    svg = render_svg(warm_style, deep_style)

    svg_path = args.outdir / "illustrated-template-proof.svg"
    html_path = args.outdir / "illustrated-template-proof.html"
    png_path = args.outdir / "illustrated-template-proof.png"
    result_path = args.outdir / "result.json"
    svg_path.write_text(svg, encoding="utf-8")
    html_path.write_text(render_html(svg), encoding="utf-8")
    result = {
        "status": "approved",
        "icon_system": "illustrated",
        "icon_system_version": "2.0.0",
        "icons": list(ICON_IDS),
        "themes": ["canonical-warm", "deep-tech-multicolor"],
        "geometry_changed": False,
        "public_templates_changed": True,
        "sources": {
            "canonical": str(warm_style_path.relative_to(ROOT)),
            "deep_tech": str(deep_style_path.relative_to(ROOT)),
        },
        "artifacts": {
            "svg": svg_path.name,
            "html": html_path.name,
            "svg_sha256": _sha256(svg_path),
        },
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

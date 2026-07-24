#!/usr/bin/env python3
"""Render all public templates against every current Illustrated icon."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
from typing import Any, Mapping

from anidiagram.illustrated_registry import illustrated_definition, illustrated_icon_ids
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style, role_style


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW = ROOT / "assets" / "illustrated" / "reviews" / "template-matrix-2.5.0-final.json"
SWATCHES = ("ink", "violet", "sky", "teal", "mint", "sun", "coral", "paper")
ICON_ROLES = {
    "agent": "agent",
    "operator": "actor",
    "tool": "tool",
    "output": "output",
    "database": "memory",
    "api": "process",
    "search": "tool",
    "memory": "memory",
    "file": "source",
    "folder": "source",
    "cloud": "source",
    "shield": "risk",
    "user": "actor",
    "server": "process",
    "ai-model": "agent",
    "message-queue": "process",
    "vector-database": "memory",
    "knowledge-base": "memory",
    "gateway": "process",
    "container": "process",
}


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _swatches(tokens: Mapping[str, str]) -> str:
    return "".join(
        f'<span class="swatch" title="{_esc(token)}" style="--swatch:{_esc(tokens[token])}"></span>'
        for token in SWATCHES
    )


def _icon_card(icon_id: str, style_id: str, style: dict, tokens: Mapping[str, str]) -> str:
    definition = illustrated_definition(icon_id)
    if definition is None:
        raise RuntimeError(f"missing Illustrated icon: {icon_id}")
    role = ICON_ROLES.get(icon_id, "neutral")
    colors = role_style(style, role)
    artwork = render_character_v2_icon(
        definition,
        f"template-matrix-{style_id}-{icon_id}",
        80,
        68,
        112,
        tokens,
    )
    return f"""
      <article class="icon-card" data-icon="{_esc(icon_id)}"
               style="--card-fill:{_esc(colors['fill'])};--card-stroke:{_esc(colors['stroke'])};--card-text:{_esc(colors['text'])}">
        <svg viewBox="0 0 160 132" role="img" aria-label="{_esc(icon_id)}">{artwork}</svg>
        <strong>{_esc(icon_id)}</strong>
        <small>{_esc(definition.semantic_role)}</small>
      </article>"""


def _theme_section(item: Mapping[str, Any]) -> str:
    style_id = str(item["style"])
    style = load_style(ROOT / "styles" / f"{style_id}.json")
    tokens = dict(item["illustrated_tokens"])
    canvas = style["canvas"]
    cards = "\n".join(
        _icon_card(icon_id, style_id, style, tokens) for icon_id in illustrated_icon_ids()
    )
    status = str(item["status"])
    return f"""
  <section id="theme-{_esc(style_id)}" class="theme-section" data-style="{_esc(style_id)}"
           style="--canvas:{_esc(canvas['background'])};--text:{_esc(canvas['text'])};--muted:{_esc(canvas['muted'])};--grid:{_esc(canvas['grid'])}">
    <header class="theme-header">
      <div>
        <p class="eyebrow">{_esc(status)}</p>
        <h2>{_esc(style_id)}</h2>
        <p>{len(illustrated_icon_ids())} / {len(illustrated_icon_ids())} current Illustrated icons · geometry locked · color tokens only</p>
      </div>
      <div class="swatches" aria-label="palette swatches">{_swatches(tokens)}</div>
    </header>
    <div class="icon-grid">{cards}</div>
  </section>"""


def render_html(matrix: Mapping[str, Any]) -> str:
    sections = "\n".join(_theme_section(item) for item in matrix["mappings"])
    navigation = "".join(
        f'<a href="#theme-{_esc(item["style"])}" data-theme-target="theme-{_esc(item["style"])}">{_esc(item["style"])}</a>'
        for item in matrix["mappings"]
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Illustrated · 13 Template Matrix</title>
  <style>
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin: 0; background: #11131a; color: #f8fafc; font: 14px/1.45 Inter, ui-sans-serif, system-ui, sans-serif; }}
    .hero {{ padding: 48px clamp(24px, 4vw, 72px) 30px; background: radial-gradient(circle at 12% 0%, #2f2752, transparent 34%), #11131a; }}
    .hero h1 {{ margin: 0 0 12px; font-size: clamp(32px, 4vw, 58px); letter-spacing: -.04em; }}
    .hero p {{ max-width: 820px; margin: 0; color: #b9c0d0; font-size: 16px; }}
    .summary {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 24px; }}
    .summary span {{ border: 1px solid #3c4150; border-radius: 999px; padding: 8px 12px; color: #d9deea; }}
    nav {{ position: sticky; top: 0; z-index: 20; display: flex; gap: 8px; overflow-x: auto; padding: 12px clamp(18px, 3vw, 52px); background: rgba(17,19,26,.92); backdrop-filter: blur(18px); border-block: 1px solid #282d38; }}
    nav a {{ flex: none; color: #cad0dc; text-decoration: none; border: 1px solid #3b414e; border-radius: 999px; padding: 7px 11px; font-size: 12px; }}
    nav a:hover, nav a[aria-current="true"] {{ color: #fff; border-color: #8b7ad9; background: #30284d; }}
    main {{ display: grid; gap: 24px; padding: 24px; }}
    .theme-section {{ color: var(--text); background-color: var(--canvas); background-image: linear-gradient(var(--grid) 1px, transparent 1px), linear-gradient(90deg, var(--grid) 1px, transparent 1px); background-size: 28px 28px; border-radius: 28px; padding: clamp(20px, 3vw, 38px); box-shadow: 0 20px 60px rgba(0,0,0,.24); scroll-margin-top: 72px; }}
    .theme-section[hidden] {{ display: none; }}
    .theme-header {{ display: flex; align-items: end; justify-content: space-between; gap: 24px; margin-bottom: 24px; }}
    .theme-header h2 {{ margin: 2px 0 4px; font-size: 30px; letter-spacing: -.025em; }}
    .theme-header p {{ margin: 0; color: var(--muted); }}
    .theme-header .eyebrow {{ text-transform: uppercase; letter-spacing: .13em; font-size: 10px; font-weight: 800; }}
    .swatches {{ display: flex; gap: 7px; padding: 9px; border-radius: 999px; background: color-mix(in srgb, var(--canvas) 84%, var(--text)); }}
    .swatch {{ width: 18px; height: 18px; border-radius: 50%; background: var(--swatch); box-shadow: inset 0 0 0 1px rgba(127,127,127,.25); }}
    .icon-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 14px; }}
    .icon-card {{ min-width: 0; overflow: hidden; text-align: center; border: 2px solid var(--card-stroke); border-radius: 22px; background: var(--card-fill); color: var(--card-text); padding: 10px 10px 14px; }}
    .icon-card svg {{ display: block; width: min(100%, 176px); margin: auto; overflow: visible; }}
    .icon-card strong {{ display: block; font-size: 14px; }}
    .icon-card small {{ display: block; min-height: 32px; margin-top: 3px; opacity: .68; font-size: 10px; overflow-wrap: anywhere; }}
    @media (max-width: 1000px) {{ .icon-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} }}
    @media (max-width: 640px) {{ main {{ padding: 10px; }} .theme-header {{ align-items: start; flex-direction: column; }} .icon-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .swatches {{ max-width: 100%; overflow-x: auto; }} }}
  </style>
</head>
<body>
  <header class="hero">
    <h1>Illustrated · 13 Template Matrix</h1>
    <p>2.5.0 公共矩阵：13 个公共模板 × 当前 {len(illustrated_icon_ids())} 个 Illustrated 图标。图标几何、部件 ID 与语义结构完全不变，仅验证模板颜色映射。</p>
    <div class="summary"><span>{len(matrix['mappings'])} templates</span><span>{len(illustrated_icon_ids())} icons</span><span>{len(matrix['mappings']) * len(illustrated_icon_ids())} instances</span><span>approved</span><span>color tokens only</span></div>
  </header>
  <nav aria-label="template navigation">{navigation}</nav>
  <main>{sections}</main>
  <script>
    (() => {{
      const sections = [...document.querySelectorAll('.theme-section')];
      const links = [...document.querySelectorAll('[data-theme-target]')];
      const fallback = sections[0].id;

      function activate(targetId, updateHash) {{
        const target = document.getElementById(targetId) || document.getElementById(fallback);
        sections.forEach((section) => {{ section.hidden = section !== target; }});
        links.forEach((link) => {{
          link.setAttribute('aria-current', String(link.dataset.themeTarget === target.id));
        }});
        if (updateHash) history.replaceState(null, '', `#${{target.id}}`);
      }}

      links.forEach((link) => link.addEventListener('click', (event) => {{
        event.preventDefault();
        activate(link.dataset.themeTarget, true);
        window.scrollTo({{ top: document.querySelector('nav').offsetTop, behavior: 'smooth' }});
      }}));
      activate(location.hash.slice(1) || fallback, false);
    }})();
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--outdir", type=Path, default=ROOT / "outputs" / "illustrated-template-matrix-2.5")
    args = parser.parse_args()
    review_path = args.review if args.review.is_absolute() else ROOT / args.review
    outdir = args.outdir if args.outdir.is_absolute() else ROOT / args.outdir
    matrix = json.loads(review_path.read_text(encoding="utf-8"))
    outdir.mkdir(parents=True, exist_ok=True)
    html_path = outdir / "illustrated-template-matrix.html"
    result_path = outdir / "result.json"
    html_path.write_text(render_html(matrix), encoding="utf-8")
    result = {
        "status": matrix["status"],
        "system": matrix["system"],
        "base_version": matrix["base_version"],
        "target_version": matrix["target_version"],
        "styles": len(matrix["mappings"]),
        "icons": len(illustrated_icon_ids()),
        "instances": len(matrix["mappings"]) * len(illustrated_icon_ids()),
        "geometry_changed": False,
        "semantic_structure_changed": False,
        "review_source": str(review_path.relative_to(ROOT)),
        "artifact": str(html_path.relative_to(ROOT)),
        "artifact_sha256": _sha256(html_path),
    }
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

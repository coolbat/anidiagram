#!/usr/bin/env python3
"""Render the remaining thirty Illustrated 2.5 static candidates."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

from anidiagram.illustrated_expansion_batches_6_10 import (
    BATCHES,
    ILLUSTRATED_EXPANSION_6_10_METADATA,
    expansion_6_10_definition,
    expansion_6_10_icon_ids,
    expansion_batch_icon_ids,
)
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style, role_style


ROOT = Path(__file__).resolve().parents[1]
ROLES = {
    "neural-network": "agent", "embedding": "process", "token": "neutral",
    "data-warehouse": "memory", "document-store": "memory", "dataset": "memory",
    "document": "source", "pdf": "source", "image": "source", "audio": "source",
    "video": "source", "code-file": "source", "webhook": "process", "http-request": "process",
    "load-balancer": "process", "server-cluster": "process", "function": "process", "edge-node": "process",
    "source-code": "source", "git-repository": "source", "branch": "source", "pull-request": "process",
    "ci-cd": "process", "deployment": "output", "task": "process", "scheduler": "process",
    "monitoring": "process", "logs": "source", "alert": "risk", "debug": "tool",
}


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _label(icon_id: str) -> str:
    special = {"pdf": "PDF", "http-request": "HTTP Request", "ci-cd": "CI/CD"}
    return special.get(icon_id, icon_id.replace("-", " ").title())


def _caption(icon_id: str) -> str:
    role = expansion_6_10_definition(icon_id).semantic_role.split("-")
    return " · ".join(role[-3:])


def _artwork(icon_id: str, instance: str, size: int, style: dict) -> str:
    return render_character_v2_icon(
        expansion_6_10_definition(icon_id), instance, 80, 66, size, illustrated_tokens_for_style(style)
    )


def _theme_card(icon_id: str, theme: str, style: dict) -> str:
    colors = role_style(style, ROLES[icon_id])
    artwork = _artwork(icon_id, f"{theme}-{icon_id}", 120, style)
    return f'''
      <article class="candidate-card" data-theme="{_esc(theme)}" data-icon="{_esc(icon_id)}"
               style="--fill:{_esc(colors['fill'])};--stroke:{_esc(colors['stroke'])};--text:{_esc(colors['text'])}">
        <span class="chip">{_esc(icon_id)}</span>
        <svg viewBox="0 0 160 138" role="img" aria-label="{_esc(_label(icon_id))}">
          <g class="candidate-instance" data-instance="{_esc(theme)}-{_esc(icon_id)}" data-size="120">{artwork}</g>
        </svg><h3>{_esc(_label(icon_id))}</h3><p>{_esc(_caption(icon_id))}</p>
      </article>'''


def _size_card(icon_id: str, style: dict) -> str:
    proofs = []
    for size in (64, 96, 120):
        artwork = _artwork(icon_id, f"size-{icon_id}-{size}", size, style)
        proofs.append(
            f'''<div class="size-proof"><svg viewBox="0 0 160 138" role="img" aria-label="{_esc(_label(icon_id))} at {size}px">
              <g class="candidate-instance" data-instance="size-{_esc(icon_id)}-{size}" data-size="{size}">{artwork}</g>
            </svg><b>{size}px</b></div>'''
        )
    definition = expansion_6_10_definition(icon_id)
    return f'''
      <article class="size-card" data-icon="{_esc(icon_id)}"><header><h3>{_esc(_label(icon_id))}</h3><span>VISUAL REVIEW</span></header>
        <div class="size-row">{"".join(proofs)}</div><code>{_esc(definition.semantic_role)}</code>
      </article>'''


def _batch_section(batch: int, warm_style: dict, deep_style: dict) -> str:
    icon_ids = expansion_batch_icon_ids(batch)
    warm = "".join(_theme_card(icon_id, f"batch-{batch}-warm", warm_style) for icon_id in icon_ids)
    deep = "".join(_theme_card(icon_id, f"batch-{batch}-deep-tech", deep_style) for icon_id in icon_ids)
    sizes = "".join(_size_card(icon_id, warm_style) for icon_id in icon_ids)
    family = BATCHES[batch]["family"].replace("-", " ").title()
    return f'''
  <section id="batch-{batch}" class="batch-section" data-batch="{batch}">
    <header class="batch-header"><div><p class="eyebrow">BATCH {batch} · VISUAL REVIEW</p><h2>{_esc(family)}</h2></div>
      <p>6 candidates · 2 themes · 64/96/120px · motion not started</p></header>
    <div class="theme-panel warm"><h3>Canonical Warm</h3><div class="grid">{warm}</div></div>
    <div class="theme-panel deep"><h3>Deep Tech · Approved Ivory Ink</h3><div class="grid">{deep}</div></div>
    <div class="theme-panel sizes"><h3>Static Readability · 64 / 96 / 120px</h3><div class="size-grid">{sizes}</div></div>
  </section>'''


def render_html(warm_style: dict, deep_style: dict) -> str:
    sections = "".join(_batch_section(batch, warm_style, deep_style) for batch in BATCHES)
    nav = "".join(
        f'<a href="#batch-{batch}" data-batch-target="batch-{batch}">Batch {batch} · {_esc(BATCHES[batch]["family"])}</a>'
        for batch in BATCHES
    )
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Illustrated 2.5 · Remaining 30 Static Review</title><style>
    * {{ box-sizing: border-box; }} body {{ margin:0; background:#151725; color:#172033; font:14px/1.45 Inter,ui-sans-serif,system-ui,sans-serif; }}
    .hero {{ padding:42px clamp(24px,5vw,76px) 28px; color:#f8fafc; background:radial-gradient(circle at 15% 0,#44376a,transparent 34%),#171925; }}
    .hero h1 {{ margin:0 0 10px; font-size:clamp(34px,4vw,56px); letter-spacing:-.045em; }} .hero p {{ max-width:960px; margin:0; color:#c7cbd7; font-size:16px; }}
    .summary {{ display:flex; gap:9px; flex-wrap:wrap; margin-top:22px; }} .summary span {{ border:1px solid #555b6c; border-radius:999px; padding:7px 11px; }}
    nav {{ position:sticky; top:0; z-index:30; display:flex; gap:8px; overflow:auto; padding:12px 20px; background:rgba(21,23,37,.94); border-block:1px solid #343847; backdrop-filter:blur(16px); }}
    nav a {{ flex:none; color:#cbd5e1; text-decoration:none; border:1px solid #475569; border-radius:999px; padding:7px 11px; font-size:12px; }} nav a[aria-current="true"] {{ color:#fff; background:#44376a; border-color:#a78bfa; }}
    main {{ padding:24px; }} .batch-section {{ display:grid; gap:24px; }} .batch-section[hidden] {{ display:none; }}
    .batch-header {{ display:flex; justify-content:space-between; align-items:end; gap:20px; color:#f8fafc; }} .batch-header h2 {{ margin:0; font-size:34px; }} .batch-header p {{ margin:0; color:#aeb5c4; }} .eyebrow {{ font-size:10px; letter-spacing:.12em; font-weight:800; }}
    .theme-panel {{ border-radius:28px; padding:30px; box-shadow:0 20px 60px rgba(0,0,0,.24); }} .theme-panel>h3 {{ margin:0 0 18px; font-size:25px; }}
    .warm {{ background:#fffaf0; }} .deep {{ color:#f8fafc; background-color:#050816; background-image:linear-gradient(#14203b 1px,transparent 1px),linear-gradient(90deg,#14203b 1px,transparent 1px); background-size:28px 28px; }} .sizes {{ background:#ececf3; }}
    .grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:15px; }} .candidate-card {{ position:relative; min-width:0; overflow:hidden; text-align:center; border:2px solid var(--stroke); border-radius:23px; padding:14px 12px 18px; background:var(--fill); color:var(--text); }}
    .candidate-card .chip {{ position:absolute; top:13px; left:13px; border-radius:999px; padding:5px 8px; background:color-mix(in srgb,var(--stroke) 14%,transparent); color:var(--stroke); font-size:9px; font-weight:800; letter-spacing:.07em; text-transform:uppercase; }}
    .candidate-card svg {{ display:block; width:min(100%,210px); margin:8px auto 0; overflow:visible; }} .candidate-card h3 {{ margin:0 0 3px; font-size:20px; }} .candidate-card p {{ margin:0; opacity:.7; }}
    .size-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }} .size-card {{ min-width:0; border:1.5px solid #d4cec2; border-radius:22px; padding:17px; background:#fffaf0; }}
    .size-card header {{ display:flex; justify-content:space-between; align-items:center; gap:12px; }} .size-card h3 {{ margin:0; font-size:19px; }} .size-card header span {{ color:#a35b00; font-size:9px; font-weight:800; letter-spacing:.08em; }}
    .size-row {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:6px; margin:10px 0; }} .size-proof {{ min-width:0; text-align:center; border:1px dashed #c8c2b5; border-radius:14px; padding:2px 3px 7px; }} .size-proof svg {{ display:block; width:100%; }} .size-proof b {{ color:#667085; font:700 10px ui-monospace,monospace; }} .size-card code {{ color:#53596b; font-size:10px; overflow-wrap:anywhere; }}
    @media(max-width:900px){{.grid,.size-grid{{grid-template-columns:repeat(2,minmax(0,1fr));}}}} @media(max-width:620px){{main{{padding:10px}}.grid,.size-grid{{grid-template-columns:1fr}}.batch-header{{align-items:start;flex-direction:column}}}}
  </style></head><body><header class="hero"><h1>Illustrated 2.5 · Remaining 30</h1><p>P4 Batch 6–10 静态候选。每批独立验收；几何、语义部件与 64px 可读性冻结后才进入动效设计。</p>
    <div class="summary"><span>5 batches</span><span>30 candidates</span><span>150 instances</span><span>review-only</span><span>public registry remains 20</span></div></header>
  <nav aria-label="batch navigation">{nav}</nav><main>{sections}</main>
  <script>(()=>{{const sections=[...document.querySelectorAll('.batch-section')],links=[...document.querySelectorAll('[data-batch-target]')],fallback=sections[0].id;function activate(id,update){{const target=document.getElementById(id)||document.getElementById(fallback);sections.forEach(s=>s.hidden=s!==target);links.forEach(a=>a.setAttribute('aria-current',String(a.dataset.batchTarget===target.id)));if(update)history.replaceState(null,'',`#${{target.id}}`);}}links.forEach(a=>a.addEventListener('click',e=>{{e.preventDefault();activate(a.dataset.batchTarget,true);window.scrollTo({{top:document.querySelector('nav').offsetTop,behavior:'smooth'}});}}));activate(location.hash.slice(1)||fallback,false);}})();</script>
</body></html>'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=ROOT / "outputs" / "illustrated-expansion-batches-6-10")
    args = parser.parse_args()
    outdir = args.outdir if args.outdir.is_absolute() else ROOT / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    warm = load_style(ROOT / "styles" / "illustrated-character-v2-concept.json")
    deep = load_style(ROOT / "styles" / "deep-tech.json")
    html_path = outdir / "illustrated-expansion-batches-6-10.html"
    result_path = outdir / "result.json"
    html_path.write_text(render_html(warm, deep), encoding="utf-8")
    result = {**ILLUSTRATED_EXPANSION_6_10_METADATA, "icons": list(expansion_6_10_icon_ids()), "icon_count": 30,
              "instances": 150, "artifact": str(html_path.relative_to(ROOT)), "artifact_sha256": _sha256(html_path)}
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()

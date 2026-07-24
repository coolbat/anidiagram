#!/usr/bin/env python3
"""Render the twelve-icon Illustrated convention-alignment review surface."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

from anidiagram.illustrated_convention_alignment_review import (
    ALIGNMENT_GROUPS,
    ALIGNMENT_REFERENCE_ANCHORS,
    CONVENTION_ALIGNMENT_METADATA,
    convention_alignment_definition,
    convention_alignment_icon_ids,
    current_alignment_definition,
    current_alignment_status,
)
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _label(icon_id: str) -> str:
    special = {"ci-cd": "CI/CD"}
    return special.get(icon_id, icon_id.replace("-", " ").title())


def _artwork(definition, instance: str, style: dict, *, size: int = 120, cx: int = 80, cy: int = 72) -> str:
    return render_character_v2_icon(
        definition,
        instance,
        cx,
        cy,
        size,
        illustrated_tokens_for_style(style),
    )


def _icon_panel(icon_id: str, variant: str, heading: str, definition, style: dict, theme: str) -> str:
    instance = f"{icon_id}-{variant}"
    artwork = _artwork(definition, instance, style)
    return f'''<div class="icon-panel {theme}" data-variant="{_esc(variant)}">
      <div class="panel-label">{_esc(heading)}</div>
      <svg viewBox="0 0 160 144" role="img" aria-label="{_esc(_label(icon_id))} · {_esc(heading)}">
        <g class="candidate-instance" data-instance="{_esc(instance)}">{artwork}</g>
      </svg>
    </div>'''


def _size_proofs(icon_id: str, definition, style: dict) -> str:
    proofs = []
    for size in (64, 96, 120):
        instance = f"{icon_id}-size-{size}"
        artwork = _artwork(definition, instance, style, size=size, cx=60, cy=60)
        proofs.append(
            f'''<div class="size-proof"><svg viewBox="0 0 120 120" role="img" aria-label="{_esc(_label(icon_id))} at {size}px">
              <g class="candidate-instance" data-instance="{_esc(instance)}">{artwork}</g>
            </svg><b>{size}px</b></div>'''
        )
    return "".join(proofs)


def _comparison_card(icon_id: str, warm_style: dict, deep_style: dict) -> str:
    current = current_alignment_definition(icon_id)
    revised = convention_alignment_definition(icon_id)
    reference_anchor = ALIGNMENT_REFERENCE_ANCHORS[icon_id]
    anchor = reference_anchor["title"]
    note = reference_anchor["note"]
    references = " · ".join(
        f'<a href="{_esc(reference["url"])}" target="_blank" rel="noreferrer">{_esc(reference["provider"])}</a>'
        for reference in reference_anchor["references"]
    )
    current_heading = "Current public" if current_alignment_status(icon_id) == "public" else "Accepted baseline"
    current_panel = _icon_panel(icon_id, "current", current_heading, current, warm_style, "warm")
    revised_panel = _icon_panel(icon_id, "revised", "Revised candidate", revised, warm_style, "warm revised")
    deep_panel = _icon_panel(icon_id, "deep", "Deep Tech", revised, deep_style, "deep")
    sizes = _size_proofs(icon_id, revised, warm_style)
    return f'''<article class="comparison-card" data-icon="{_esc(icon_id)}">
      <header><div><span class="icon-id">{_esc(icon_id)}</span><h3>{_esc(_label(icon_id))}</h3></div><span class="anchor">{_esc(anchor)}</span></header>
      <div class="comparison-grid">{current_panel}{revised_panel}{deep_panel}</div>
      <div class="analysis-row"><div class="analysis-copy"><p>{_esc(note)}</p><span>Official anchor · {references}</span></div><div class="size-row">{sizes}</div></div>
      <code>{_esc(revised.semantic_role)}</code>
    </article>'''


def _group_section(group_id: str, group: dict, warm_style: dict, deep_style: dict) -> str:
    cards = "".join(_comparison_card(icon_id, warm_style, deep_style) for icon_id in group["icons"])
    return f'''<section id="{_esc(group_id)}" class="review-section" data-group="{_esc(group_id)}">
      <header class="section-header"><div><p>CONVENTION ALIGNMENT</p><h2>{_esc(group["label"])}</h2></div><span>{len(group["icons"])} icons · review-only</span></header>
      <div class="cards">{cards}</div>
    </section>'''


def render_html(warm_style: dict, deep_style: dict) -> str:
    sections = "".join(_group_section(group_id, group, warm_style, deep_style) for group_id, group in ALIGNMENT_GROUPS.items())
    nav = "".join(f'<a href="#{_esc(group_id)}">{_esc(group["label"])}</a>' for group_id, group in ALIGNMENT_GROUPS.items())
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Illustrated · Convention Alignment Review</title><style>
    *{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:#131522;color:#f4f5f8;font:14px/1.5 Inter,ui-sans-serif,system-ui,sans-serif}}
    .hero{{padding:48px clamp(22px,5vw,76px) 34px;background:radial-gradient(circle at 15% 0,#4d3d78 0,transparent 35%),linear-gradient(150deg,#171a2b,#11131e)}}
    .hero .eyebrow,.section-header p{{margin:0 0 8px;color:#b8a9ff;font-size:10px;font-weight:850;letter-spacing:.14em}}.hero h1{{max-width:920px;margin:0;font-size:clamp(38px,5vw,68px);line-height:.98;letter-spacing:-.055em}}
    .hero>p{{max-width:900px;margin:20px 0 0;color:#bdc3d2;font-size:16px}}.summary{{display:flex;gap:9px;flex-wrap:wrap;margin-top:25px}}.summary span,nav a{{border:1px solid #4c5264;border-radius:999px;padding:7px 11px;color:#dce0e8;text-decoration:none}}
    nav{{position:sticky;top:0;z-index:20;display:flex;gap:8px;padding:12px 22px;background:rgba(19,21,34,.94);border-block:1px solid #343847;backdrop-filter:blur(18px)}}
    main{{display:grid;gap:34px;padding:28px clamp(12px,3vw,40px) 70px}}.review-section{{scroll-margin-top:70px}}.section-header{{display:flex;justify-content:space-between;align-items:end;gap:20px;margin:0 4px 15px}}.section-header h2{{margin:0;font-size:32px;letter-spacing:-.03em}}.section-header>span{{color:#9ca4b6}}
    .cards{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.comparison-card{{min-width:0;padding:18px;border:1px solid #343a4d;border-radius:26px;background:#1b1e2d;box-shadow:0 24px 70px rgba(0,0,0,.18)}}
    .comparison-card>header{{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:13px}}.comparison-card h3{{margin:2px 0 0;font-size:23px}}.icon-id{{color:#aaa2c4;font:700 10px ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase}}.anchor{{max-width:180px;color:#d9ccff;font-size:11px;text-align:right}}
    .comparison-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}}.icon-panel{{min-width:0;border-radius:18px;padding:10px 7px 7px;background:#fffaf0;color:#283047;border:1px solid #ded6c9}}.icon-panel.revised{{outline:3px solid #8067d8;outline-offset:-3px}}.icon-panel.deep{{background-color:#050816;background-image:linear-gradient(#14203b 1px,transparent 1px),linear-gradient(90deg,#14203b 1px,transparent 1px);background-size:22px 22px;border-color:#273657;color:#fff}}
    .panel-label{{height:25px;text-align:center;font-size:10px;font-weight:800;letter-spacing:.04em}}.icon-panel svg{{display:block;width:100%;overflow:visible}}
    .analysis-row{{display:grid;grid-template-columns:minmax(150px,1fr) minmax(250px,1.25fr);gap:14px;align-items:center;margin-top:14px}}.analysis-copy p{{margin:0;color:#b7bdca;font-size:12px}}.analysis-copy span{{display:block;margin-top:7px;color:#7f8799;font-size:9px;text-transform:uppercase;letter-spacing:.05em}}.analysis-copy a{{color:#b8a9ff;text-decoration:none}}.size-row{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}}.size-proof{{min-width:0;padding:3px 3px 6px;border:1px dashed #51586b;border-radius:13px;text-align:center;background:#f8f5ec;color:#555d70}}.size-proof svg{{display:block;width:100%}}.size-proof b{{font:700 9px ui-monospace,monospace}}.comparison-card>code{{display:block;margin-top:10px;color:#7f8799;font-size:10px;overflow-wrap:anywhere}}
    footer{{padding:0 30px 45px;color:#848b9c;text-align:center}}@media(max-width:1050px){{.cards{{grid-template-columns:1fr}}}}@media(max-width:680px){{.comparison-grid{{grid-template-columns:1fr}}.analysis-row{{grid-template-columns:1fr}}.section-header{{align-items:start;flex-direction:column}}}}
  </style></head><body><header class="hero"><p class="eyebrow">ILLUSTRATED 2.5 · NARROW PROOF</p><h1>Recognizable first.<br>Illustrated second.</h1>
    <p>12 个高/中风险图标的行业惯例对齐稿。当前版与修订版使用同一模板并排比较；Deep Tech 与 64/96/120px 只验证主题适配和小尺寸识别，不改变几何。</p>
    <div class="summary"><span>4 P1 redesigns</span><span>8 P2 alignments</span><span>72 instances</span><span>motion unchanged</span><span>public registry unchanged</span></div></header>
  <nav aria-label="review groups">{nav}</nav><main>{sections}</main><footer>Visual review gate · approval is required before promotion and motion synchronization.</footer></body></html>'''


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=ROOT / "outputs" / "illustrated-convention-alignment-review")
    args = parser.parse_args()
    outdir = args.outdir if args.outdir.is_absolute() else ROOT / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    warm = load_style(ROOT / "styles" / "illustrated-character-v2-concept.json")
    deep = load_style(ROOT / "styles" / "deep-tech.json")
    html_path = outdir / "illustrated-convention-alignment-review.html"
    result_path = outdir / "result.json"
    html_path.write_text(render_html(warm, deep), encoding="utf-8")
    result = {
        **CONVENTION_ALIGNMENT_METADATA,
        "icons": list(convention_alignment_icon_ids()),
        "icon_count": 12,
        "instances": 72,
        "artifact": str(html_path.relative_to(ROOT)),
        "artifact_sha256": _sha256(html_path),
    }
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render the Illustrated 2.5.0 candidate Batch 5 static-review proof."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

from anidiagram.illustrated_expansion_batch_5 import (
    ILLUSTRATED_EXPANSION_BATCH_5_METADATA,
    expansion_batch_5_definition,
    expansion_batch_5_icon_ids,
)
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style, role_style


ROOT = Path(__file__).resolve().parents[1]
ICON_IDS = expansion_batch_5_icon_ids()
ROLES = {
    "developer": "actor",
    "agent-team": "agent",
    "assistant": "agent",
    "human-reviewer": "actor",
    "llm": "agent",
    "reasoning": "process",
}
LABELS = {
    "developer": "Developer",
    "agent-team": "Agent Team",
    "assistant": "Assistant",
    "human-reviewer": "Human Reviewer",
    "llm": "LLM",
    "reasoning": "Reasoning",
}
CAPTIONS = {
    "developer": "code · build · deliver",
    "agent-team": "coordinate · delegate · synthesize",
    "assistant": "listen · guide · respond",
    "human-reviewer": "inspect · decide · annotate",
    "llm": "context · transform · generate",
    "reasoning": "premise · infer · conclude",
}


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artwork(icon_id: str, instance: str, size: int, style: dict) -> str:
    definition = expansion_batch_5_definition(icon_id)
    if definition is None:
        raise RuntimeError(f"missing Batch 5 candidate: {icon_id}")
    return render_character_v2_icon(
        definition,
        instance,
        80,
        66,
        size,
        illustrated_tokens_for_style(style),
    )


def _theme_card(icon_id: str, theme: str, style: dict) -> str:
    colors = role_style(style, ROLES[icon_id])
    artwork = _artwork(icon_id, f"{theme}-{icon_id}", 120, style)
    return f'''
      <article class="candidate-card" data-theme="{_esc(theme)}" data-icon="{_esc(icon_id)}"
               style="--fill:{_esc(colors['fill'])};--stroke:{_esc(colors['stroke'])};--text:{_esc(colors['text'])}">
        <span class="chip">{_esc(icon_id)}</span>
        <svg viewBox="0 0 160 138" role="img" aria-label="{_esc(LABELS[icon_id])}">
          <g class="candidate-instance" data-instance="{_esc(theme)}-{_esc(icon_id)}" data-size="120">{artwork}</g>
        </svg>
        <h3>{_esc(LABELS[icon_id])}</h3>
        <p>{_esc(CAPTIONS[icon_id])}</p>
      </article>'''


def _size_card(icon_id: str, style: dict) -> str:
    proofs = []
    for size in (64, 96, 120):
        artwork = _artwork(icon_id, f"size-{icon_id}-{size}", size, style)
        proofs.append(
            f'''<div class="size-proof">
              <svg viewBox="0 0 160 138" role="img" aria-label="{_esc(LABELS[icon_id])} at {size}px">
                <g class="candidate-instance" data-instance="size-{_esc(icon_id)}-{size}" data-size="{size}">{artwork}</g>
              </svg>
              <b>{size}px</b>
            </div>'''
        )
    definition = expansion_batch_5_definition(icon_id)
    return f'''
      <article class="size-card" data-icon="{_esc(icon_id)}">
        <header><h3>{_esc(LABELS[icon_id])}</h3><span>VISUAL REVIEW</span></header>
        <div class="size-row">{"".join(proofs)}</div>
        <code>{_esc(definition.semantic_role)}</code>
        <p>主体和核心语义在 64px 仍可辨识 · motion intentionally not started</p>
      </article>'''


def render_html(warm_style: dict, deep_style: dict) -> str:
    warm_cards = "".join(_theme_card(icon_id, "canonical-warm", warm_style) for icon_id in ICON_IDS)
    deep_cards = "".join(_theme_card(icon_id, "deep-tech", deep_style) for icon_id in ICON_IDS)
    size_cards = "".join(_size_card(icon_id, warm_style) for icon_id in ICON_IDS)
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Illustrated 2.5 Candidate · Batch 5</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #171925; color: #172033; font: 14px/1.45 Inter, ui-sans-serif, system-ui, sans-serif; }}
    .hero {{ padding: 42px clamp(24px, 5vw, 76px) 30px; color: #f8fafc; background: radial-gradient(circle at 15% 0, #44376a, transparent 34%), #171925; }}
    .hero h1 {{ margin: 0 0 10px; font-size: clamp(34px, 4vw, 56px); letter-spacing: -.045em; }}
    .hero p {{ max-width: 920px; margin: 0; color: #c7cbd7; font-size: 16px; }}
    .summary {{ display: flex; gap: 9px; flex-wrap: wrap; margin-top: 22px; }}
    .summary span {{ border: 1px solid #555b6c; border-radius: 999px; padding: 7px 11px; color: #e5e7eb; }}
    main {{ display: grid; gap: 26px; padding: 26px; }}
    section {{ border-radius: 30px; padding: clamp(22px, 3vw, 38px); box-shadow: 0 22px 70px rgba(0,0,0,.25); }}
    section > header {{ display: flex; justify-content: space-between; align-items: end; gap: 20px; margin-bottom: 22px; }}
    section h2 {{ margin: 0 0 4px; font-size: 29px; letter-spacing: -.025em; }}
    section header p {{ margin: 0; opacity: .72; }}
    .warm {{ background: #fffaf0; }}
    .deep {{ color: #f8fafc; background-color: #050816; background-image: linear-gradient(#14203b 1px, transparent 1px), linear-gradient(90deg, #14203b 1px, transparent 1px); background-size: 28px 28px; }}
    .sizes {{ background: #ececf3; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }}
    .candidate-card {{ position: relative; min-width: 0; overflow: hidden; text-align: center; border: 2px solid var(--stroke); border-radius: 24px; padding: 15px 14px 19px; background: var(--fill); color: var(--text); }}
    .candidate-card .chip {{ position: absolute; top: 14px; left: 14px; border-radius: 999px; padding: 5px 9px; background: color-mix(in srgb, var(--stroke) 14%, transparent); color: var(--stroke); font-size: 10px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }}
    .candidate-card svg {{ display: block; width: min(100%, 230px); margin: 12px auto 0; overflow: visible; }}
    .candidate-card h3 {{ margin: 2px 0 4px; font-size: 21px; }}
    .candidate-card p {{ margin: 0; opacity: .7; }}
    .size-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }}
    .size-card {{ min-width: 0; border: 1.5px solid #d4cec2; border-radius: 24px; padding: 20px; background: #fffaf0; }}
    .size-card header {{ display: flex; justify-content: space-between; gap: 16px; align-items: center; }}
    .size-card h3 {{ margin: 0; font-size: 21px; }}
    .size-card header span {{ color: #a35b00; font-size: 10px; font-weight: 800; letter-spacing: .09em; }}
    .size-row {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; margin: 12px 0; }}
    .size-proof {{ min-width: 0; text-align: center; border: 1px dashed #c8c2b5; border-radius: 16px; padding: 2px 4px 8px; }}
    .size-proof svg {{ display: block; width: 100%; }}
    .size-proof b {{ color: #667085; font: 700 11px ui-monospace, monospace; }}
    .size-card code {{ display: block; color: #53596b; font-size: 11px; overflow-wrap: anywhere; }}
    .size-card p {{ margin: 7px 0 0; color: #717687; font-size: 12px; }}
    @media (max-width: 920px) {{ .grid, .size-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
    @media (max-width: 620px) {{ main {{ padding: 10px; }} .grid, .size-grid {{ grid-template-columns: 1fr; }} section > header {{ align-items: start; flex-direction: column; }} }}
  </style>
</head>
<body>
  <header class="hero">
    <h1>Illustrated 2.5 Candidate · Batch 5</h1>
    <p>P4 第一批：People and Agent Intelligence。只审核静态构图、语义区分和 64/96/120px 可读性；公共 2.4.0 注册表与动效契约保持不变。</p>
    <div class="summary"><span>6 candidates</span><span>2 themes</span><span>3 sizes</span><span>30 instances</span><span>motion not started</span></div>
  </header>
  <main>
    <section class="warm">
      <header><div><h2>Canonical Warm</h2><p>一个强主体 · 语义部件内置 · 不使用通用勾号、外圈箭头、三角符号或状态徽章</p></div><strong>STATIC REVIEW</strong></header>
      <div class="grid">{warm_cards}</div>
    </section>
    <section class="deep">
      <header><div><h2>Deep Tech</h2><p>沿用已批准米白描边，仅切换颜色 token，几何与部件 ID 保持一致</p></div><strong>COLOR PARITY</strong></header>
      <div class="grid">{deep_cards}</div>
    </section>
    <section class="sizes">
      <header><div><h2>Static Readability</h2><p>64 / 96 / 120px 对照；先冻结静态视觉，再设计语义动效</p></div><strong>6 × 3</strong></header>
      <div class="size-grid">{size_cards}</div>
    </section>
  </main>
</body>
</html>'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=ROOT / "outputs" / "illustrated-expansion-batch-5",
    )
    args = parser.parse_args()
    outdir = args.outdir if args.outdir.is_absolute() else ROOT / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    warm_style = load_style(ROOT / "styles" / "illustrated-character-v2-concept.json")
    deep_style = load_style(ROOT / "styles" / "deep-tech.json")
    html_path = outdir / "illustrated-expansion-batch-5.html"
    result_path = outdir / "result.json"
    html_path.write_text(render_html(warm_style, deep_style), encoding="utf-8")
    result = {
        **ILLUSTRATED_EXPANSION_BATCH_5_METADATA,
        "icons": list(ICON_IDS),
        "themes": ["canonical-warm", "deep-tech"],
        "sizes": [64, 96, 120],
        "instances": 30,
        "artifact": str(html_path.relative_to(ROOT)),
        "artifact_sha256": _sha256(html_path),
    }
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

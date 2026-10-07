#!/usr/bin/env python3
"""Render the isolated motion-review proof for Illustrated 2.5 Batch 5."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

from anidiagram.runtime_registry import archived_runtime_source
from anidiagram.illustrated_expansion_batch_5 import (
    expansion_batch_5_definition,
    expansion_batch_5_icon_ids,
)
from anidiagram.illustrated_expansion_batch_5_motion import (
    ILLUSTRATED_V6_REVIEW_ICON_PERFORMANCES,
    ILLUSTRATED_V6_REVIEW_REST_AT,
)
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.motion_manifest import icon_part_id
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style, role_style


ROOT = Path(__file__).resolve().parents[1]
ICON_IDS = expansion_batch_5_icon_ids()
WIDTH = 1500
HEIGHT = 1100
LABELS = {
    "developer": "Developer",
    "agent-team": "Agent Team",
    "assistant": "Assistant",
    "human-reviewer": "Human Reviewer",
    "llm": "LLM",
    "reasoning": "Reasoning",
}
ROLES = {
    "developer": "actor",
    "agent-team": "agent",
    "assistant": "agent",
    "human-reviewer": "actor",
    "llm": "agent",
    "reasoning": "process",
}
SEQUENCES = {
    "developer": ("code", "build", "deliver"),
    "agent-team": ("coordinate", "delegate", "synthesize"),
    "assistant": ("listen", "guide", "respond"),
    "human-reviewer": ("inspect", "decide", "annotate"),
    "llm": ("context", "transform", "generate"),
    "reasoning": ("premise", "infer", "conclude"),
}
MOTION_NOTES = {
    "developer": "控制台就位，代码逐笔写入，双手完成输入",
    "agent-team": "主 Agent 发起协作，连接建立，成员同步响应",
    "assistant": "耳机进入监听，表情回应，回复内容逐步生成",
    "human-reviewer": "审核单抬起，逐行检查，决策信号依次确认",
    "llm": "上下文展开，模型完成转换，输出 token 依次生成",
    "reasoning": "前提节点点亮，推理路径展开，结论节点完成收束",
}


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_motion_review_manifest() -> dict:
    icons = []
    for index, icon_id in enumerate(ICON_IDS):
        definition = expansion_batch_5_definition(icon_id)
        node_id = f"review-{icon_id}"
        icons.append(
            {
                "node_id": node_id,
                "icon": icon_id,
                "performance": ILLUSTRATED_V6_REVIEW_ICON_PERFORMANCES[icon_id],
                "trigger": "on-load",
                "loop": "action-then-idle",
                "delay": round(index * 0.1, 2),
                "intensity": 1.0,
                "semantic_role": definition.semantic_role,
                "asset_version": "2.5.0-candidate",
                "cancel_behavior": "restore-authored-rest-pose",
                "reduced_motion_behavior": "static-rest",
                "repeat_delay": 0.8,
                "motion_contract": "illustrated-performance-v6-review",
                "motion_status": "visual-review",
                "selection_policy": "explicit-review-only",
                "rest_at": ILLUSTRATED_V6_REVIEW_REST_AT[icon_id],
                "parts": {part: f"#{icon_part_id(node_id, part)}" for part in definition.parts},
            }
        )
    return {
        "version": "motion-manifest-0.1",
        "runtime": "gsap",
        "mode": "ambient",
        "profile": "showcase-v1",
        "sequence": "independent-icon-loops",
        "scene_sequence": "staged",
        "reduced_motion": "static",
        "icon_system": "illustrated",
        "icon_system_version": "2.5.0-candidate",
        "stage": {
            "edge_flow": False,
            "title_sweep": False,
            "edge_limit": 0,
            "readable_edge_limit": 0,
            "active_edge_indices": [],
            "readable_edge_indices": [],
        },
        "icons": icons,
        "edges": [],
    }


def _card(icon_id: str, x: int, y: int, style: dict) -> str:
    node_id = f"review-{icon_id}"
    colors = role_style(style, ROLES[icon_id])
    chips = "".join(
        f'<g transform="translate({x + 36 + index * 126} {y + 306})">'
        f'<rect width="112" height="28" rx="14" fill="{_esc(colors["stroke"])}" opacity="0.14" />'
        f'<text x="56" y="19" class="chip" text-anchor="middle" fill="{_esc(colors["text"])}">{_esc(word)}</text>'
        '</g>'
        for index, word in enumerate(SEQUENCES[icon_id])
    )
    artwork = render_character_v2_icon(
        expansion_batch_5_definition(icon_id),
        node_id,
        x + 220,
        y + 137,
        190,
        illustrated_tokens_for_style(style),
    )
    return f'''
    <g class="motion-review-card" data-icon="{_esc(icon_id)}">
      <rect x="{x}" y="{y}" width="440" height="410" rx="28" fill="#0b1328" stroke="{_esc(colors['stroke'])}" stroke-width="2.4" />
      <rect x="{x + 22}" y="{y + 20}" width="124" height="24" rx="12" fill="{_esc(colors['stroke'])}" opacity="0.16" />
      <text x="{x + 84}" y="{y + 36}" class="eyebrow" text-anchor="middle" fill="{_esc(colors['text'])}">REVIEW ONLY</text>
      <text x="{x + 416}" y="{y + 36}" class="version" text-anchor="end" fill="#94a3b8">2.5 CANDIDATE</text>
      {artwork}
      <text x="{x + 220}" y="{y + 253}" class="icon-title" text-anchor="middle" fill="#f8fafc">{_esc(LABELS[icon_id])}</text>
      <text x="{x + 220}" y="{y + 279}" class="semantic" text-anchor="middle" fill="#a5b4cc">{_esc(expansion_batch_5_definition(icon_id).semantic_role)}</text>
      {chips}
      <line x1="{x + 24}" y1="{y + 351}" x2="{x + 416}" y2="{y + 351}" stroke="#24314f" />
      <text x="{x + 24}" y="{y + 377}" class="motion-note" fill="#dbeafe">{_esc(MOTION_NOTES[icon_id])}</text>
      <text x="{x + 24}" y="{y + 398}" class="policy" fill="#94a3b8">循环回到 authored rest pose · reduced-motion 静态归零</text>
    </g>'''


def render_motion_review_svg() -> str:
    style = load_style(ROOT / "styles" / "deep-tech.json")
    positions = ((45, 145), (530, 145), (1015, 145), (45, 590), (530, 590), (1015, 590))
    cards = "\n".join(_card(icon_id, x, y, style) for icon_id, (x, y) in zip(ICON_IDS, positions))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}"
     viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title description">
  <title id="title">Illustrated 2.5 candidate Batch 5 motion review</title>
  <desc id="description">Review-only semantic motion for six people and agent intelligence icons.</desc>
  <defs>
    <linearGradient id="page-bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#071026" /><stop offset="1" stop-color="#030712" />
    </linearGradient>
  </defs>
  <style>
    .page-title {{ font: 760 38px ui-sans-serif, system-ui, sans-serif; letter-spacing: -0.025em; }}
    .subtitle {{ font: 450 15px ui-sans-serif, system-ui, sans-serif; }}
    .eyebrow, .version {{ font: 760 9px ui-sans-serif, system-ui, sans-serif; letter-spacing: 0.08em; }}
    .icon-title {{ font: 760 23px ui-sans-serif, system-ui, sans-serif; }}
    .semantic {{ font: 600 10px ui-monospace, SFMono-Regular, monospace; }}
    .chip {{ font: 720 11px ui-sans-serif, system-ui, sans-serif; }}
    .motion-note {{ font: 620 12px ui-sans-serif, system-ui, sans-serif; }}
    .policy {{ font: 480 11px ui-sans-serif, system-ui, sans-serif; }}
  </style>
  <rect width="100%" height="100%" fill="url(#page-bg)" />
  <text x="45" y="58" class="page-title" fill="#f8fafc">Illustrated 2.5 Candidate · Batch 5 Motion Review</text>
  <text x="45" y="88" class="subtitle" fill="#94a3b8">6 个静态已批准候选 · showcase-v1 · explicit review only · 公共 Illustrated 2.4.0 保持不变</text>
  <rect x="1235" y="38" width="220" height="44" rx="22" fill="#13203d" stroke="#334155" />
  <circle cx="1261" cy="60" r="6" fill="#2dd4bf" />
  <text x="1277" y="65" class="subtitle" fill="#dbeafe">静态已批准 / 动效待审核</text>
  {cards}
</svg>'''


BATCH_5_RUNTIME = r'''
  function playIllustratedDeveloper({ config, parts, gsap }) {
    const required = ["body", "head", "hair", "code-console", "console-header", "code-glyphs", "hands"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const glyphLength = primeStrokeDraw([parts["code-glyphs"]], gsap).get(parts["code-glyphs"]);
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.fromTo(parts["code-console"], { y: 10, scale: 0.94 }, { y: 0, scale: 1, duration: 0.3, ease: "back.out(2.8)" }, 0)
      .to([parts.head, parts.hair], { y: 2, rotation: -2, duration: 0.18, ease: "sine.inOut" }, 0.18)
      .to([parts.head, parts.hair], { y: 0, rotation: 0, duration: 0.2, ease: "sine.inOut" }, 0.36)
      .fromTo(parts["code-glyphs"], { opacity: 0.2, strokeDashoffset: glyphLength }, { opacity: 1, strokeDashoffset: 0, duration: 0.62, ease: "power1.inOut" }, 0.3)
      .to(parts.hands, { y: 4, duration: 0.11, yoyo: true, repeat: 3, ease: "power1.inOut" }, 0.52)
      .to(parts["console-header"], { scaleX: 1.03, duration: 0.16, ease: "sine.inOut" }, 1.18)
      .to(parts["console-header"], { scaleX: 1, duration: 0.18, ease: "sine.inOut" }, 1.34);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  function playIllustratedAgentTeam({ config, parts, gsap }) {
    const required = ["collaboration-field", "team-links", "lead-agent", "lead-core", "member-left", "member-right", "member-cores"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const linkLength = primeStrokeDraw([parts["team-links"]], gsap).get(parts["team-links"]);
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.fromTo([parts["lead-agent"], parts["lead-core"]], { y: -10, scale: 0.72 }, { y: 0, scale: 1.12, duration: 0.3, ease: "back.out(3)" }, 0)
      .to([parts["lead-agent"], parts["lead-core"]], { scale: 1, duration: 0.18, ease: "power2.out" }, 0.3)
      .fromTo(parts["team-links"], { opacity: 0.18, strokeDashoffset: linkLength }, { opacity: 1, strokeDashoffset: 0, duration: 0.5, ease: "power1.inOut" }, 0.25)
      .fromTo(parts["member-left"], { x: -13, opacity: 0.35, scale: 0.82 }, { x: 0, opacity: 1, scale: 1, duration: 0.34, ease: "back.out(2.8)" }, 0.55)
      .fromTo(parts["member-right"], { x: 13, opacity: 0.35, scale: 0.82 }, { x: 0, opacity: 1, scale: 1, duration: 0.34, ease: "back.out(2.8)" }, 0.68)
      .fromTo(parts["member-cores"], { opacity: 0.28, scale: 0.55 }, { opacity: 1, scale: 1.35, duration: 0.25, ease: "back.out(3.2)" }, 0.88)
      .to(parts["member-cores"], { scale: 1, duration: 0.22, ease: "elastic.out(1, 0.4)" }, 1.13)
      .to(parts["collaboration-field"], { scale: 1.025, duration: 0.16, ease: "sine.inOut" }, 1.34)
      .to(parts["collaboration-field"], { scale: 1, duration: 0.18, ease: "sine.inOut" }, 1.5);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  function playIllustratedAssistant({ config, parts, gsap }) {
    const required = ["assistant-shell", "face-panel", "eyes", "smile", "headset", "earpieces", "response-panel", "response-lines"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const lineLength = primeStrokeDraw([parts["response-lines"]], gsap).get(parts["response-lines"]);
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.to(parts["assistant-shell"], { y: -4, scaleY: 1.03, duration: 0.22, ease: "back.out(2.4)" }, 0)
      .fromTo([parts.headset, parts.earpieces], { scale: 0.88, opacity: 0.45 }, { scale: 1.08, opacity: 1, duration: 0.3, ease: "back.out(3)" }, 0.12)
      .to([parts.headset, parts.earpieces], { scale: 1, duration: 0.18, ease: "power2.out" }, 0.42)
      .to(parts.eyes, { scaleY: 0.15, duration: 0.1, yoyo: true, repeat: 1, ease: "power1.inOut" }, 0.58)
      .to(parts.smile, { scaleX: 1.16, duration: 0.18, ease: "back.out(2.5)" }, 0.78)
      .fromTo(parts["response-panel"], { y: 7, opacity: 0.4 }, { y: 0, opacity: 1, duration: 0.28, ease: "back.out(2.6)" }, 0.86)
      .fromTo(parts["response-lines"], { opacity: 0.2, strokeDashoffset: lineLength }, { opacity: 1, strokeDashoffset: 0, duration: 0.36, ease: "power1.inOut" }, 1.02)
      .to([parts["assistant-shell"], parts.smile], { y: 0, scaleX: 1, scaleY: 1, duration: 0.24, ease: "sine.inOut" }, 1.4);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  function playIllustratedHumanReviewer({ config, parts, gsap }) {
    const required = ["body", "head", "hair", "glasses", "review-sheet", "review-lines", "decision-signals", "hands"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const lineLength = primeStrokeDraw([parts["review-lines"]], gsap).get(parts["review-lines"]);
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.fromTo(parts["review-sheet"], { y: 10, opacity: 0.5, scale: 0.94 }, { y: 0, opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2.7)" }, 0)
      .to([parts.head, parts.hair, parts.glasses], { rotation: 4, y: 2, duration: 0.2, ease: "sine.inOut" }, 0.2)
      .to([parts.head, parts.hair, parts.glasses], { rotation: -3, duration: 0.24, ease: "sine.inOut" }, 0.42)
      .fromTo(parts["review-lines"], { opacity: 0.2, strokeDashoffset: lineLength }, { opacity: 1, strokeDashoffset: 0, duration: 0.58, ease: "power1.inOut" }, 0.34)
      .fromTo(parts["decision-signals"], { opacity: 0.22, scale: 0.55 }, { opacity: 1, scale: 1.38, duration: 0.28, ease: "back.out(3.1)" }, 0.88)
      .to(parts["decision-signals"], { scale: 1, duration: 0.22, ease: "elastic.out(1, 0.42)" }, 1.16)
      .to(parts.hands, { y: -3, duration: 0.16, ease: "sine.inOut" }, 1.15)
      .to([parts.head, parts.hair, parts.glasses, parts.hands], { rotation: 0, x: 0, y: 0, duration: 0.26, ease: "sine.inOut" }, 1.4);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  function playIllustratedLlm({ config, parts, gsap }) {
    const required = ["context-back", "context-mid", "model-shell", "model-mark", "token-lines", "completion-dots"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const lengths = primeStrokeDraw([parts["model-mark"], parts["token-lines"]], gsap);
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.fromTo(parts["context-back"], { x: 10, y: -5, rotation: 6 }, { x: 0, y: 0, rotation: 0, duration: 0.32, ease: "back.out(2.8)" }, 0)
      .fromTo(parts["context-mid"], { x: -10, y: -2, rotation: -6 }, { x: 0, y: 0, rotation: 0, duration: 0.32, ease: "back.out(2.8)" }, 0.1)
      .fromTo(parts["model-shell"], { y: 8, scale: 0.94 }, { y: 0, scale: 1, duration: 0.28, ease: "back.out(2.6)" }, 0.22)
      .fromTo(parts["model-mark"], { opacity: 0.2, strokeDashoffset: lengths.get(parts["model-mark"]) }, { opacity: 1, strokeDashoffset: 0, duration: 0.42, ease: "power1.inOut" }, 0.42)
      .fromTo(parts["token-lines"], { opacity: 0.2, strokeDashoffset: lengths.get(parts["token-lines"]) }, { opacity: 1, strokeDashoffset: 0, duration: 0.38, ease: "power1.inOut" }, 0.72)
      .fromTo(parts["completion-dots"], { opacity: 0.18, scale: 0.45 }, { opacity: 1, scale: 1.42, duration: 0.28, ease: "back.out(3.2)" }, 1.0)
      .to(parts["completion-dots"], { scale: 1, duration: 0.22, ease: "elastic.out(1, 0.42)" }, 1.28)
      .to(parts["model-shell"], { scale: 1.02, duration: 0.14, ease: "sine.inOut" }, 1.42)
      .to(parts["model-shell"], { scale: 1, duration: 0.18, ease: "sine.inOut" }, 1.56);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  function playIllustratedReasoning({ config, parts, gsap }) {
    const required = ["reasoning-shell", "thought-field", "reasoning-path", "premise-points", "conclusion-point", "insight-base"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const pathLength = primeStrokeDraw([parts["reasoning-path"]], gsap).get(parts["reasoning-path"]);
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.to(parts["reasoning-shell"], { scaleY: 0.97, scaleX: 1.025, duration: 0.16, ease: "power2.inOut" }, 0)
      .to(parts["reasoning-shell"], { scaleY: 1, scaleX: 1, duration: 0.22, ease: "back.out(2.5)" }, 0.16)
      .fromTo(parts["premise-points"], { opacity: 0.2, scale: 0.55 }, { opacity: 1, scale: 1.28, duration: 0.28, ease: "back.out(3)" }, 0.3)
      .to(parts["premise-points"], { scale: 1, duration: 0.18, ease: "power2.out" }, 0.58)
      .fromTo(parts["reasoning-path"], { opacity: 0.18, strokeDashoffset: pathLength }, { opacity: 1, strokeDashoffset: 0, duration: 0.68, ease: "power1.inOut" }, 0.46)
      .fromTo(parts["conclusion-point"], { opacity: 0.25, scale: 0.45 }, { opacity: 1, scale: 1.5, duration: 0.28, ease: "back.out(3.4)" }, 1.08)
      .to(parts["conclusion-point"], { scale: 1, duration: 0.22, ease: "elastic.out(1, 0.4)" }, 1.36)
      .to(parts["insight-base"], { scaleX: 1.14, duration: 0.16, ease: "sine.inOut" }, 1.46)
      .to(parts["insight-base"], { scaleX: 1, duration: 0.18, ease: "sine.inOut" }, 1.62);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  performances["illustrated-developer-code-build-deliver-v1"] = playIllustratedDeveloper;
  performances["illustrated-agent-team-coordinate-delegate-synthesize-v1"] = playIllustratedAgentTeam;
  performances["illustrated-assistant-listen-guide-respond-v1"] = playIllustratedAssistant;
  performances["illustrated-human-reviewer-inspect-decide-annotate-v1"] = playIllustratedHumanReviewer;
  performances["illustrated-llm-context-transform-generate-v1"] = playIllustratedLlm;
  performances["illustrated-reasoning-premise-infer-conclude-v1"] = playIllustratedReasoning;
'''


def build_review_runtime() -> str:
    source = archived_runtime_source("illustrated-performance-v5-review")
    marker = '  performances["illustrated-vector-database-embed-index-retrieve-v1"]'
    if marker not in source:
        raise RuntimeError("archived review runtime registration marker changed")
    return source.replace(marker, BATCH_5_RUNTIME + "\n" + marker, 1).replace(
        "AniDiagram Batch 4 review runtime", "AniDiagram Batch 5 review runtime"
    )


def render_motion_review_html(svg: str, manifest: dict) -> str:
    manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2).replace("</", "<\\/")
    runtime = build_review_runtime().replace("</script", "<\\/script")
    gsap = (ROOT / "node_modules" / "gsap" / "dist" / "gsap.min.js").read_text(encoding="utf-8").replace("</script", "<\\/script")
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Illustrated 2.5 Batch 5 Motion Review</title><link rel="icon" href="data:,">
  <style>
    html, body {{ margin: 0; min-height: 100%; background: #020617; color: #f8fafc; font-family: ui-sans-serif, system-ui, sans-serif; }}
    main {{ min-height: 100vh; display: grid; grid-template-rows: auto 1fr; gap: 12px; padding: 16px; box-sizing: border-box; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
    button, a {{ border: 1px solid #334155; background: #0f172a; color: #f8fafc; border-radius: 9px; padding: 8px 11px; font: inherit; text-decoration: none; cursor: pointer; }}
    button:hover, a:hover {{ background: #1e293b; }} button[aria-pressed="true"] {{ background: #334155; border-color: #94a3b8; }}
    .stage {{ width: 100%; min-height: 0; overflow: hidden; border: 1px solid #1e293b; border-radius: 14px; background: #020617; cursor: grab; }}
    .stage.dragging {{ cursor: grabbing; }} .viewport {{ transform-origin: 0 0; width: max-content; }}
    svg {{ display: block; max-width: none; height: auto; user-select: none; }}
  </style></head>
<body><main id="viewer" class="motion-expressive" data-runtime="gsap">
  <div class="toolbar"><button type="button" id="toggle">Pause</button><button type="button" id="restart">Restart</button>
    <button type="button" class="motion-choice" data-motion="expressive" aria-pressed="true">Expressive</button>
    <button type="button" class="motion-choice" data-motion="readable" aria-pressed="false">Readable</button>
    <button type="button" class="motion-choice" data-motion="off" aria-pressed="false">Off</button>
    <button type="button" id="zoom-in">Zoom In</button><button type="button" id="zoom-out">Zoom Out</button><button type="button" id="reset">Reset</button>
    <a id="download" download="illustrated-expansion-batch-5-motion-review.svg">Download SVG</a></div>
  <div class="stage" id="stage"><div class="viewport" id="viewport">{svg}</div></div>
</main><script type="application/json" id="anidiagram-motion-manifest">{manifest_json}</script><script>{gsap}</script><script>{runtime}</script></body></html>'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=ROOT / "outputs" / "illustrated-expansion-batch-5-motion-review")
    args = parser.parse_args()
    outdir = args.outdir if args.outdir.is_absolute() else ROOT / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    svg = render_motion_review_svg()
    manifest = build_motion_review_manifest()
    html_text = render_motion_review_html(svg, manifest)
    svg_path = outdir / "illustrated-expansion-batch-5-motion-review.svg"
    html_path = outdir / "illustrated-expansion-batch-5-motion-review.html"
    runtime_path = outdir / "illustrated-performance-v6-review-runtime.js"
    result_path = outdir / "result.json"
    svg_path.write_text(svg, encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")
    runtime_path.write_text(build_review_runtime(), encoding="utf-8")
    result = {
        "ok": True,
        "system": "illustrated",
        "version": "2.5.0-candidate",
        "status": "motion-visual-review",
        "motion_contract": "illustrated-performance-v6-review",
        "public_registry_changed": False,
        "icons": list(ICON_IDS),
        "artifacts": {
            "svg": {"path": svg_path.name, "sha256": _sha256(svg_path), "status": "written"},
            "html": {"path": html_path.name, "sha256": _sha256(html_path), "status": "written"},
            "runtime": {"path": runtime_path.name, "sha256": _sha256(runtime_path), "status": "written"},
        },
    }
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

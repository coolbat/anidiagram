#!/usr/bin/env python3
"""Render the thirty-icon motion review for Illustrated Batches 6-10."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

from anidiagram.runtime_registry import archived_runtime_source
from anidiagram.illustrated_expansion_batches_6_10 import (
    BATCHES,
    expansion_6_10_definition,
    expansion_6_10_icon_ids,
    expansion_batch_icon_ids,
)
from anidiagram.illustrated_expansion_batches_6_10_motion import (
    ILLUSTRATED_V7_REVIEW_ICON_PERFORMANCES,
    ILLUSTRATED_V7_REVIEW_MOTION_SPECS,
)
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.motion_manifest import icon_part_id
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style, role_style


ROOT = Path(__file__).resolve().parents[1]
WIDTH = 1500
HEIGHT = 1050
ROLES = {
    "neural-network": "agent", "embedding": "process", "token": "neutral", "data-warehouse": "memory",
    "document-store": "memory", "dataset": "memory", "document": "source", "pdf": "source", "image": "source",
    "audio": "source", "video": "source", "code-file": "source", "webhook": "process", "http-request": "process",
    "load-balancer": "process", "server-cluster": "process", "function": "process", "edge-node": "process",
    "source-code": "source", "git-repository": "source", "branch": "source", "pull-request": "process",
    "ci-cd": "process", "deployment": "output", "task": "process", "scheduler": "process", "monitoring": "process",
    "logs": "source", "alert": "risk", "debug": "tool",
}
RECIPE_NOTES = {
    "draw": "关键语义路径逐笔显现，再点亮结果部件",
    "cascade": "语义部件按顺序进入，最后完成状态收束",
    "fan": "层级部件展开后归位，强调组合与版本关系",
    "oscillate": "信号部件产生节律响应，随后回到稳定状态",
    "sweep": "处理焦点沿主体扫过，结束于结果部件",
    "bounce": "执行部件进入目标位置，平台完成激活反馈",
}


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _label(icon_id: str) -> str:
    return {"pdf": "PDF", "http-request": "HTTP Request", "ci-cd": "CI/CD"}.get(
        icon_id, icon_id.replace("-", " ").title()
    )


def build_motion_review_manifest() -> dict:
    icons = []
    for index, icon_id in enumerate(expansion_6_10_icon_ids()):
        definition = expansion_6_10_definition(icon_id)
        spec = ILLUSTRATED_V7_REVIEW_MOTION_SPECS[icon_id]
        node_id = f"review-{icon_id}"
        icons.append(
            {
                "node_id": node_id,
                "icon": icon_id,
                "performance": ILLUSTRATED_V7_REVIEW_ICON_PERFORMANCES[icon_id],
                "trigger": "on-load",
                "loop": "action-then-idle",
                "delay": round((index % 6) * 0.08, 2),
                "intensity": 1.0,
                "semantic_role": definition.semantic_role,
                "asset_version": "2.5.0-candidate",
                "cancel_behavior": "restore-authored-rest-pose",
                "reduced_motion_behavior": "static-rest",
                "repeat_delay": 0.8,
                "motion_contract": "illustrated-performance-v7-review",
                "motion_status": "visual-review",
                "selection_policy": "explicit-review-only",
                "rest_at": spec["rest_at"],
                "motion_recipe": {
                    "type": spec["recipe"],
                    "prepare_parts": list(spec["prepare_parts"]),
                    "action_parts": list(spec["action_parts"]),
                    "result_parts": list(spec["result_parts"]),
                },
                "parts": {part: f"#{icon_part_id(node_id, part)}" for part in definition.parts},
            }
        )
    return {
        "version": "motion-manifest-0.1", "runtime": "gsap", "mode": "ambient", "profile": "showcase-v1",
        "sequence": "independent-icon-loops", "scene_sequence": "staged", "reduced_motion": "static",
        "icon_system": "illustrated", "icon_system_version": "2.5.0-candidate",
        "stage": {"edge_flow": False, "title_sweep": False, "edge_limit": 0, "readable_edge_limit": 0,
                  "active_edge_indices": [], "readable_edge_indices": []},
        "icons": icons, "edges": [],
    }


def _card(icon_id: str, x: int, y: int, style: dict) -> str:
    definition = expansion_6_10_definition(icon_id)
    spec = ILLUSTRATED_V7_REVIEW_MOTION_SPECS[icon_id]
    colors = role_style(style, ROLES[icon_id])
    artwork = render_character_v2_icon(
        definition, f"review-{icon_id}", x + 220, y + 137, 188, illustrated_tokens_for_style(style)
    )
    chips = "".join(
        f'<g transform="translate({x + 36 + i * 126} {y + 306})"><rect width="112" height="28" rx="14" '
        f'fill="{_esc(colors["stroke"])}" opacity="0.14"/><text x="56" y="19" class="chip" text-anchor="middle" '
        f'fill="{_esc(colors["text"])}">{_esc(word)}</text></g>'
        for i, word in enumerate(spec["sequence"])
    )
    return f'''
    <g class="motion-review-card" data-icon="{_esc(icon_id)}">
      <rect x="{x}" y="{y}" width="440" height="410" rx="28" fill="#0b1328" stroke="{_esc(colors['stroke'])}" stroke-width="2.4"/>
      <rect x="{x+22}" y="{y+20}" width="124" height="24" rx="12" fill="{_esc(colors['stroke'])}" opacity="0.16"/>
      <text x="{x+84}" y="{y+36}" class="eyebrow" text-anchor="middle" fill="{_esc(colors['text'])}">REVIEW ONLY</text>
      <text x="{x+416}" y="{y+36}" class="version" text-anchor="end" fill="#94a3b8">{_esc(spec['recipe'].upper())}</text>
      {artwork}<text x="{x+220}" y="{y+253}" class="icon-title" text-anchor="middle" fill="#f8fafc">{_esc(_label(icon_id))}</text>
      <text x="{x+220}" y="{y+279}" class="semantic" text-anchor="middle" fill="#a5b4cc">{_esc(definition.semantic_role)}</text>{chips}
      <line x1="{x+24}" y1="{y+351}" x2="{x+416}" y2="{y+351}" stroke="#24314f"/>
      <text x="{x+24}" y="{y+377}" class="motion-note" fill="#dbeafe">{_esc(RECIPE_NOTES[spec['recipe']])}</text>
      <text x="{x+24}" y="{y+398}" class="policy" fill="#94a3b8">rest {spec['rest_at']:.2f}s · reduced-motion 静态归零</text>
    </g>'''


def _batch_group(batch: int, style: dict, visible: bool) -> str:
    positions = ((45, 145), (530, 145), (1015, 145), (45, 590), (530, 590), (1015, 590))
    cards = "".join(_card(icon, x, y, style) for icon, (x, y) in zip(expansion_batch_icon_ids(batch), positions))
    family = BATCHES[batch]["family"].replace("-", " ").title()
    display = "inline" if visible else "none"
    return f'''<g id="motion-batch-{batch}" class="motion-batch-panel" data-batch="{batch}" style="display:{display}">
      <rect width="100%" height="100%" fill="url(#page-bg)"/>
      <text x="45" y="58" class="page-title" fill="#f8fafc">Batch {batch} · {_esc(family)} Motion Review</text>
      <text x="45" y="88" class="subtitle" fill="#94a3b8">6 个静态已批准候选 · showcase-v1 · explicit review only</text>
      <rect x="1230" y="38" width="225" height="44" rx="22" fill="#13203d" stroke="#334155"/><circle cx="1256" cy="60" r="6" fill="#2dd4bf"/>
      <text x="1272" y="65" class="subtitle" fill="#dbeafe">静态已批准 / 动效待审核</text>{cards}</g>'''


def render_motion_review_svg() -> str:
    style = load_style(ROOT / "styles" / "deep-tech.json")
    panels = "".join(_batch_group(batch, style, batch == 6) for batch in BATCHES)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img">
      <defs><linearGradient id="page-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#071026"/><stop offset="1" stop-color="#030712"/></linearGradient></defs>
      <style>.page-title{{font:760 38px ui-sans-serif,system-ui,sans-serif;letter-spacing:-.025em}}.subtitle{{font:450 15px ui-sans-serif,system-ui,sans-serif}}
      .eyebrow,.version{{font:760 9px ui-sans-serif,system-ui,sans-serif;letter-spacing:.08em}}.icon-title{{font:760 23px ui-sans-serif,system-ui,sans-serif}}
      .semantic{{font:600 10px ui-monospace,SFMono-Regular,monospace}}.chip{{font:720 11px ui-sans-serif,system-ui,sans-serif}}.motion-note{{font:620 12px ui-sans-serif,system-ui,sans-serif}}.policy{{font:480 11px ui-sans-serif,system-ui,sans-serif}}</style>{panels}</svg>'''


GENERIC_V7_RUNTIME = r'''
  function playIllustratedV7Configured({ config, parts, gsap }) {
    const spec = config.motion_recipe || {};
    const names = [...(spec.prepare_parts || []), ...(spec.action_parts || []), ...(spec.result_parts || [])];
    if (!hasParts(parts, names)) return null;
    setInitial(parts, gsap);
    const prepare = (spec.prepare_parts || []).map((name) => parts[name]).filter(Boolean);
    const action = (spec.action_parts || []).map((name) => parts[name]).filter(Boolean);
    const result = (spec.result_parts || []).map((name) => parts[name]).filter(Boolean);
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    if (prepare.length) timeline.fromTo(prepare, { opacity: 0.42, y: 8, scale: 0.92 }, { opacity: 1, y: 0, scale: 1, duration: 0.3, stagger: 0.05, ease: "back.out(2.5)" }, 0);
    const recipe = spec.type || "cascade";
    if (recipe === "draw") {
      const lengths = primeStrokeDraw(action, gsap);
      action.forEach((target, index) => timeline.fromTo(target,
        { opacity: 0.18, strokeDashoffset: lengths.get(target) },
        { opacity: 1, strokeDashoffset: 0, duration: 0.52, ease: "power1.inOut" }, 0.32 + index * 0.08));
    } else if (recipe === "fan") {
      timeline.fromTo(action, { opacity: 0.35, x: (i) => i % 2 ? 10 : -10, rotation: (i) => i % 2 ? 7 : -7, scale: 0.9 },
        { opacity: 1, x: 0, rotation: 0, scale: 1, duration: 0.46, stagger: 0.08, ease: "back.out(2.8)" }, 0.32);
    } else if (recipe === "oscillate") {
      timeline.fromTo(action, { opacity: 0.4, scaleY: 0.72 }, { opacity: 1, scaleY: 1.22, duration: 0.28, stagger: 0.07, ease: "sine.inOut" }, 0.32)
        .to(action, { scaleY: 1, duration: 0.28, stagger: 0.05, ease: "sine.inOut" }, 0.68);
    } else if (recipe === "sweep") {
      timeline.fromTo(action, { opacity: 0.35, x: -10, scale: 0.9 }, { opacity: 1, x: 8, scale: 1.08, duration: 0.4, stagger: 0.07, ease: "power2.inOut" }, 0.32)
        .to(action, { x: 0, scale: 1, duration: 0.24, stagger: 0.05, ease: "power2.out" }, 0.76);
    } else if (recipe === "bounce") {
      timeline.fromTo(action, { opacity: 0.35, y: -12, scale: 0.84 }, { opacity: 1, y: 5, scale: 1.08, duration: 0.38, stagger: 0.07, ease: "back.out(2.9)" }, 0.32)
        .to(action, { y: 0, scale: 1, duration: 0.24, stagger: 0.05, ease: "power2.out" }, 0.74);
    } else {
      timeline.fromTo(action, { opacity: 0.28, y: 10, scale: 0.8 }, { opacity: 1, y: 0, scale: 1, duration: 0.42, stagger: 0.1, ease: "back.out(2.8)" }, 0.32);
    }
    if (result.length) timeline.fromTo(result, { opacity: 0.25, scale: 0.5 }, { opacity: 1, scale: 1.34, duration: 0.28, stagger: 0.07, ease: "back.out(3.2)" }, 1.08)
      .to(result, { scale: 1, duration: 0.22, stagger: 0.05, ease: "elastic.out(1, 0.42)" }, 1.36);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }
'''


def build_review_runtime() -> str:
    source = archived_runtime_source("illustrated-performance-v5-review")
    marker = '  performances["illustrated-vector-database-embed-index-retrieve-v1"]'
    registrations = "\n".join(
        f'  performances[{json.dumps(performance)}] = playIllustratedV7Configured;'
        for performance in ILLUSTRATED_V7_REVIEW_ICON_PERFORMANCES.values()
    )
    insertion = GENERIC_V7_RUNTIME + "\n" + registrations + "\n"
    if marker not in source:
        raise RuntimeError("archived review runtime registration marker changed")
    return source.replace(marker, insertion + marker, 1).replace("AniDiagram Batch 4 review runtime", "AniDiagram Batches 6-10 review runtime")


def render_motion_review_html(svg: str, manifest: dict) -> str:
    manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2).replace("</", "<\\/")
    runtime = build_review_runtime().replace("</script", "<\\/script")
    gsap = (ROOT / "node_modules" / "gsap" / "dist" / "gsap.min.js").read_text(encoding="utf-8").replace("</script", "<\\/script")
    nav = "".join(f'<button type="button" class="batch-choice" data-batch="{batch}" aria-pressed="{str(batch==6).lower()}">Batch {batch}</button>' for batch in BATCHES)
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Illustrated 2.5 Batches 6-10 Motion Review</title><link rel="icon" href="data:,">
    <style>html,body{{margin:0;min-height:100%;background:#020617;color:#f8fafc;font-family:ui-sans-serif,system-ui,sans-serif}}main{{min-height:100vh;display:grid;grid-template-rows:auto 1fr;gap:12px;padding:16px;box-sizing:border-box}}.toolbar{{display:flex;flex-wrap:wrap;gap:8px;align-items:center}}button,a{{border:1px solid #334155;background:#0f172a;color:#f8fafc;border-radius:9px;padding:8px 11px;font:inherit;text-decoration:none;cursor:pointer}}button:hover,a:hover,button[aria-pressed="true"]{{background:#334155;border-color:#94a3b8}}.divider{{width:1px;height:28px;background:#334155;margin:0 4px}}.stage{{width:100%;min-height:0;overflow:hidden;border:1px solid #1e293b;border-radius:14px;background:#020617;cursor:grab}}.stage.dragging{{cursor:grabbing}}.viewport{{transform-origin:0 0;width:max-content}}svg{{display:block;max-width:none;height:auto;user-select:none}}</style></head><body>
    <main id="viewer" class="motion-expressive" data-runtime="gsap"><div class="toolbar">{nav}<span class="divider"></span><button id="toggle">Pause</button><button id="restart">Restart</button><button class="motion-choice" data-motion="expressive" aria-pressed="true">Expressive</button><button class="motion-choice" data-motion="readable" aria-pressed="false">Readable</button><button class="motion-choice" data-motion="off" aria-pressed="false">Off</button><button id="zoom-in">Zoom In</button><button id="zoom-out">Zoom Out</button><button id="reset">Reset</button><a id="download" download="illustrated-batches-6-10-motion-review.svg">Download SVG</a></div>
    <div class="stage" id="stage"><div class="viewport" id="viewport">{svg}</div></div></main><script type="application/json" id="anidiagram-motion-manifest">{manifest_json}</script><script>{gsap}</script><script>{runtime}</script>
    <script>(()=>{{const buttons=[...document.querySelectorAll('.batch-choice')],panels=[...document.querySelectorAll('.motion-batch-panel')];buttons.forEach(button=>button.addEventListener('click',()=>{{const batch=button.dataset.batch;buttons.forEach(item=>item.setAttribute('aria-pressed',String(item===button)));panels.forEach(panel=>panel.style.display=panel.dataset.batch===batch?'inline':'none');}}));}})();</script></body></html>'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=ROOT / "outputs" / "illustrated-expansion-batches-6-10-motion-review")
    args = parser.parse_args(); outdir = args.outdir if args.outdir.is_absolute() else ROOT / args.outdir; outdir.mkdir(parents=True, exist_ok=True)
    svg = render_motion_review_svg(); manifest = build_motion_review_manifest(); html_text = render_motion_review_html(svg, manifest)
    svg_path = outdir / "illustrated-expansion-batches-6-10-motion-review.svg"; html_path = outdir / "illustrated-expansion-batches-6-10-motion-review.html"
    runtime_path = outdir / "illustrated-performance-v7-review-runtime.js"; result_path = outdir / "result.json"
    svg_path.write_text(svg, encoding="utf-8"); html_path.write_text(html_text, encoding="utf-8"); runtime_path.write_text(build_review_runtime(), encoding="utf-8")
    result = {"ok": True, "system": "illustrated", "version": "2.5.0-candidate", "status": "motion-visual-review",
              "motion_contract": "illustrated-performance-v7-review", "public_registry_changed": False,
              "icons": list(expansion_6_10_icon_ids()), "icon_count": 30,
              "artifacts": {"svg": {"path": svg_path.name, "sha256": _sha256(svg_path), "status": "written"},
                            "html": {"path": html_path.name, "sha256": _sha256(html_path), "status": "written"},
                            "runtime": {"path": runtime_path.name, "sha256": _sha256(runtime_path), "status": "written"}}}
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8"); print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()

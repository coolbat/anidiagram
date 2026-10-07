#!/usr/bin/env python3
"""Render and capture the review-only motion proof for Illustrated Batch 4."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

from anidiagram.runtime_registry import archived_runtime_source
from anidiagram.exporters import (
    _blend_loop_seam,
    _capture_browser_runtime,
    _write_browser_image_sequence,
)
from anidiagram.illustrated_expansion_batch_4 import (
    expansion_batch_4_definition,
    expansion_batch_4_icon_ids,
)
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.illustrated_expansion_batch_4_motion import (
    ILLUSTRATED_V5_REVIEW_ICON_PERFORMANCES,
    ILLUSTRATED_V5_REVIEW_REST_AT,
)
from anidiagram.motion_manifest import icon_part_id
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style, role_style


ROOT = Path(__file__).resolve().parents[1]
ICON_IDS = expansion_batch_4_icon_ids()
WIDTH = 1440
HEIGHT = 820
LABELS = {
    "vector-database": "Vector Database",
    "knowledge-base": "Knowledge Base",
    "gateway": "Gateway",
    "container": "Container",
}
ROLES = {
    "vector-database": "memory",
    "knowledge-base": "source",
    "gateway": "process",
    "container": "process",
}
SEQUENCES = {
    "vector-database": ("embed", "index", "retrieve"),
    "knowledge-base": ("curate", "connect", "reference"),
    "gateway": ("admit", "route", "mediate"),
    "container": ("package", "isolate", "run"),
}
MOTION_NOTES = {
    "vector-database": "向量连接写入并点亮索引场",
    "knowledge-base": "书页展开，知识连接与引用依次显现",
    "gateway": "请求与响应沿内部通道双向通行",
    "container": "容器就位，隔离框内的应用模块启动",
}


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def build_motion_review_manifest() -> dict:
    icons = []
    for index, icon_id in enumerate(ICON_IDS):
        definition = expansion_batch_4_definition(icon_id)
        node_id = f"review-{icon_id}"
        icons.append(
            {
                "node_id": node_id,
                "icon": icon_id,
                "performance": ILLUSTRATED_V5_REVIEW_ICON_PERFORMANCES[icon_id],
                "trigger": "on-load",
                "loop": "action-then-idle",
                "delay": round(index * 0.12, 2),
                "intensity": 1.0,
                "semantic_role": definition.semantic_role,
                "asset_version": "2.4.0-candidate",
                "cancel_behavior": "restore-authored-rest-pose",
                "reduced_motion_behavior": "static-rest",
                "repeat_delay": 0.8,
                "motion_contract": "illustrated-performance-v5-review",
                "motion_status": "visual-review",
                "selection_policy": "explicit-review-only",
                "rest_at": ILLUSTRATED_V5_REVIEW_REST_AT[icon_id],
                "parts": {
                    part: f"#{icon_part_id(node_id, part)}"
                    for part in definition.parts
                },
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
        "icon_system_version": "2.4.0-candidate",
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


def _card(icon_id: str, x: int, style: dict) -> str:
    node_id = f"review-{icon_id}"
    colors = role_style(style, ROLES[icon_id])
    sequence = SEQUENCES[icon_id]
    chips = "".join(
        f'<g transform="translate({x + 33 + index * 86} 573)">'
        f'<rect width="76" height="28" rx="14" fill="{_esc(colors["stroke"])}" opacity="0.14" />'
        f'<text x="38" y="19" class="chip" text-anchor="middle" fill="{_esc(colors["text"])}">{_esc(word)}</text>'
        '</g>'
        for index, word in enumerate(sequence)
    )
    artwork = render_character_v2_icon(
        expansion_batch_4_definition(icon_id),
        node_id,
        x + 157,
        330,
        220,
        illustrated_tokens_for_style(style),
    )
    return f'''
    <g class="motion-review-card" data-icon="{_esc(icon_id)}">
      <rect x="{x}" y="142" width="314" height="600" rx="30" fill="#0b1328" stroke="{_esc(colors['stroke'])}" stroke-width="2.4" />
      <rect x="{x + 24}" y="166" width="138" height="25" rx="12.5" fill="{_esc(colors['stroke'])}" opacity="0.16" />
      <text x="{x + 93}" y="183" class="eyebrow" text-anchor="middle" fill="{_esc(colors['text'])}">REVIEW ONLY</text>
      <text x="{x + 290}" y="183" class="version" text-anchor="end" fill="#94a3b8">2.4 CANDIDATE</text>
      {artwork}
      <text x="{x + 157}" y="500" class="icon-title" text-anchor="middle" fill="#f8fafc">{_esc(LABELS[icon_id])}</text>
      <text x="{x + 157}" y="530" class="semantic" text-anchor="middle" fill="#a5b4cc">{_esc(expansion_batch_4_definition(icon_id).semantic_role)}</text>
      {chips}
      <line x1="{x + 24}" y1="626" x2="{x + 290}" y2="626" stroke="#24314f" />
      <text x="{x + 24}" y="658" class="motion-note" fill="#dbeafe">{_esc(MOTION_NOTES[icon_id])}</text>
      <text x="{x + 24}" y="690" class="policy" fill="#94a3b8">循环结束回到 authored rest pose</text>
      <text x="{x + 24}" y="714" class="policy" fill="#94a3b8">reduced-motion：静态归零</text>
    </g>'''


def render_motion_review_svg() -> str:
    style = load_style(ROOT / "styles" / "deep-tech.json")
    cards = "\n".join(_card(icon_id, 45 + index * 345, style) for index, icon_id in enumerate(ICON_IDS))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}"
     viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title description">
  <title id="title">Illustrated 2.4.0 candidate Batch 4 motion review</title>
  <desc id="description">Review-only semantic motion for Vector Database, Knowledge Base, Gateway, and Container.</desc>
  <defs>
    <linearGradient id="page-bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#071026" />
      <stop offset="1" stop-color="#030712" />
    </linearGradient>
  </defs>
  <style>
    .page-title {{ font: 760 38px ui-sans-serif, system-ui, sans-serif; letter-spacing: -0.025em; }}
    .subtitle {{ font: 450 15px ui-sans-serif, system-ui, sans-serif; }}
    .eyebrow, .version {{ font: 760 9px ui-sans-serif, system-ui, sans-serif; letter-spacing: 0.08em; }}
    .icon-title {{ font: 760 25px ui-sans-serif, system-ui, sans-serif; }}
    .semantic {{ font: 600 10px ui-monospace, SFMono-Regular, monospace; }}
    .chip {{ font: 720 11px ui-sans-serif, system-ui, sans-serif; }}
    .motion-note {{ font: 620 13px ui-sans-serif, system-ui, sans-serif; }}
    .policy {{ font: 480 12px ui-sans-serif, system-ui, sans-serif; }}
  </style>
  <rect width="100%" height="100%" fill="url(#page-bg)" />
  <text x="45" y="58" class="page-title" fill="#f8fafc">Illustrated 2.4.0 Candidate · Motion Review</text>
  <text x="45" y="88" class="subtitle" fill="#94a3b8">4 个静态已批准候选 · showcase-v1 · explicit review only · 公共 Illustrated 2.3.0 保持不变</text>
  <rect x="1184" y="39" width="211" height="44" rx="22" fill="#13203d" stroke="#334155" />
  <circle cx="1210" cy="61" r="6" fill="#2dd4bf" />
  <text x="1226" y="66" class="subtitle" fill="#dbeafe">静态已批准 / 动效待审核</text>
  {cards}
</svg>'''


def render_motion_review_html(
    svg: str,
    manifest: dict,
    document_title: str = "Illustrated 2.4.0 Candidate Motion Review",
    download_name: str = "illustrated-2.4.0-candidate-motion-review.svg",
) -> str:
    manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2).replace("</", "<\\/")
    runtime = archived_runtime_source("illustrated-performance-v5-review").replace("</script", "<\\/script")
    gsap = (ROOT / "node_modules" / "gsap" / "dist" / "gsap.min.js").read_text(encoding="utf-8").replace("</script", "<\\/script")
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(document_title)}</title>
  <link rel="icon" href="data:,">
  <style>
    html, body {{ margin: 0; min-height: 100%; background: #020617; color: #f8fafc; font-family: ui-sans-serif, system-ui, sans-serif; }}
    main {{ min-height: 100vh; display: grid; grid-template-rows: auto 1fr; gap: 12px; padding: 16px; box-sizing: border-box; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
    button, a {{ border: 1px solid #334155; background: #0f172a; color: #f8fafc; border-radius: 9px; padding: 8px 11px; font: inherit; text-decoration: none; cursor: pointer; }}
    button:hover, a:hover {{ background: #1e293b; }}
    button[aria-pressed="true"] {{ background: #334155; border-color: #94a3b8; }}
    .stage {{ width: 100%; min-height: 0; overflow: hidden; border: 1px solid #1e293b; border-radius: 14px; background: #020617; cursor: grab; }}
    .stage.dragging {{ cursor: grabbing; }}
    .viewport {{ transform-origin: 0 0; width: max-content; }}
    svg {{ display: block; max-width: none; height: auto; user-select: none; }}
  </style>
</head>
<body>
  <main id="viewer" class="motion-expressive" data-runtime="gsap">
    <div class="toolbar">
      <button type="button" id="toggle">Pause</button>
      <button type="button" id="restart">Restart</button>
      <button type="button" class="motion-choice" data-motion="expressive" aria-pressed="true">Expressive</button>
      <button type="button" class="motion-choice" data-motion="readable" aria-pressed="false">Readable</button>
      <button type="button" class="motion-choice" data-motion="off" aria-pressed="false">Off</button>
      <button type="button" id="zoom-in">Zoom In</button>
      <button type="button" id="zoom-out">Zoom Out</button>
      <button type="button" id="reset">Reset</button>
      <a id="download" download="{_esc(download_name)}">Download SVG</a>
    </div>
    <div class="stage" id="stage"><div class="viewport" id="viewport">{svg}</div></div>
  </main>
  <script type="application/json" id="anidiagram-motion-manifest">{manifest_json}</script>
  <script>{gsap}</script>
  <script>{runtime}</script>
</body>
</html>'''


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _capture(
    html_path: Path,
    outdir: Path,
    style: dict,
    frames: int,
    fps: int,
    basename: str = "illustrated-expansion-batch-4-motion-review",
    width: int = WIDTH,
    height: int = HEIGHT,
) -> dict:
    scene = SimpleNamespace(canvas=SimpleNamespace(width=width, height=height))
    records = {}
    with tempfile.TemporaryDirectory() as tmp:
        frames_dir = Path(tmp) / "png"
        frames_dir.mkdir()
        capture = _capture_browser_runtime(scene, html_path, frames_dir, None, "png", 1, fps, 1.0)
        if capture["status"] == "written":
            png_path = outdir / f"{basename}.png"
            shutil.copyfile(frames_dir / "frame-0000.png", png_path)
            records["png"] = {"path": png_path.name, "sha256": _sha256(png_path), "status": "written"}
        else:
            records["png"] = capture
    with tempfile.TemporaryDirectory() as tmp:
        frames_dir = Path(tmp) / "webp"
        frames_dir.mkdir()
        capture = _capture_browser_runtime(scene, html_path, frames_dir, None, "webp", frames, fps, 1.0)
        if capture["status"] == "written":
            frame_paths = [frames_dir / f"frame-{index:04d}.png" for index in range(frames)]
            _blend_loop_seam(frame_paths, 8)
            webp_path = outdir / f"{basename}.webp"
            packaged = _write_browser_image_sequence("webp", frame_paths, webp_path, fps, style)
            records["webp"] = {
                **packaged,
                "path": webp_path.name,
                "sha256": _sha256(webp_path) if webp_path.is_file() else None,
                "fps": fps,
                "frames": frames,
                "loop_blend_frames": 8,
            }
        else:
            records["webp"] = capture
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=ROOT / "outputs" / "illustrated-expansion-batch-4-motion-review")
    parser.add_argument("--frames", type=int, default=108)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--skip-capture", action="store_true")
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    svg = render_motion_review_svg()
    manifest = build_motion_review_manifest()
    html_text = render_motion_review_html(svg, manifest)
    svg_path = args.outdir / "illustrated-expansion-batch-4-motion-review.svg"
    html_path = args.outdir / "illustrated-expansion-batch-4-motion-review.html"
    result_path = args.outdir / "result.json"
    svg_path.write_text(svg, encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")
    artifacts = {
        "svg": {"path": svg_path.name, "sha256": _sha256(svg_path), "status": "written"},
        "html": {"path": html_path.name, "sha256": _sha256(html_path), "status": "written"},
    }
    if not args.skip_capture:
        artifacts.update(_capture(html_path, args.outdir, load_style(ROOT / "styles" / "deep-tech.json"), max(1, args.frames), max(1, args.fps)))
    result = {
        "ok": all(item.get("status") == "written" for item in artifacts.values()),
        "system": "illustrated",
        "version": "2.4.0-candidate",
        "status": "motion-visual-review",
        "motion_contract": "illustrated-performance-v5-review",
        "public_registry_changed": False,
        "icons": list(ICON_IDS),
        "artifacts": artifacts,
    }
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(html_path.resolve())
    print(svg_path.resolve())
    print(result_path.resolve())


if __name__ == "__main__":
    main()

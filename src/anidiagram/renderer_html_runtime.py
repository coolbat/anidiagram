"""High-fidelity HTML runtime renderer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .motion_manifest_v2 import build_motion_manifest
from .renderer_svg import esc, render_svg
from .model import Scene


def render_html_runtime(scene: Scene, style: Dict[str, Any], runtime: str = "gsap") -> str:
    manifest = build_motion_manifest(scene, style, runtime=runtime)
    svg = render_svg(scene, style, animation_mode="runtime-stage")
    manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2).replace("</", "<\\/")
    runtime_js = _runtime_source()
    gsap_script = ""
    if runtime == "gsap":
        gsap_script = '<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(scene.title.text)} Runtime</title>
  <link rel="icon" href="data:,">
  <style>
    body {{ margin: 0; background: #0b1020; color: #f8fafc; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ min-height: 100vh; display: grid; grid-template-rows: auto 1fr; gap: 12px; padding: 16px; box-sizing: border-box; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
    button, a {{ border: 1px solid #475569; background: #111827; color: #f8fafc; border-radius: 8px; padding: 8px 10px; font: inherit; text-decoration: none; cursor: pointer; }}
    button:hover, a:hover {{ background: #1f2937; }}
    button[aria-pressed="true"] {{ background: #475569; border-color: #94a3b8; }}
    .stage {{ width: 100%; min-height: 0; overflow: hidden; border: 1px solid #334155; border-radius: 12px; background: #020617; cursor: grab; }}
    .stage.dragging {{ cursor: grabbing; }}
    .viewport {{ transform-origin: 0 0; width: max-content; }}
    svg {{ display: block; max-width: none; height: auto; user-select: none; }}
    main.motion-readable .node-burst,
    main.motion-readable .icon-breathe-halo {{ display: none; }}
    main.motion-readable .edge-flow {{ opacity: 0.08; }}
    main.motion-readable .semantic-icon-breathe {{ animation-duration: 4.2s; }}
    main.motion-off .edge-flow,
    main.motion-off .edge-particle,
    main.motion-off .node-burst,
    main.motion-off .node-glow,
    main.motion-off .icon-breathe-halo {{ display: none; }}
    main.motion-off .semantic-icon-breathe {{ animation: none !important; }}
  </style>
</head>
<body>
  <main id="viewer" class="motion-expressive" data-runtime="{esc(runtime)}">
    <div class="toolbar">
      <button type="button" id="toggle">Pause</button>
      <button type="button" id="restart">Restart</button>
      <button type="button" class="motion-choice" data-motion="expressive" aria-pressed="true">Expressive</button>
      <button type="button" class="motion-choice" data-motion="readable" aria-pressed="false">Readable</button>
      <button type="button" class="motion-choice" data-motion="off" aria-pressed="false">Off</button>
      <button type="button" id="zoom-in">Zoom In</button>
      <button type="button" id="zoom-out">Zoom Out</button>
      <button type="button" id="reset">Reset</button>
      <a id="download" download="{esc(scene.title.text)}.svg">Download SVG</a>
    </div>
    <div class="stage" id="stage">
      <div class="viewport" id="viewport">
{svg}
      </div>
    </div>
  </main>
  <script type="application/json" id="anidiagram-motion-manifest">
{manifest_json}
  </script>
  {gsap_script}
  <script>
{runtime_js}
  </script>
</body>
</html>
"""


def _runtime_source() -> str:
    root = Path(__file__).resolve().parents[2]
    legacy = (root / "runtime" / "anidiagram-runtime.js").read_text(encoding="utf-8")
    edge_motion = (root / "runtime" / "edge-motion-v1-runtime.js").read_text(encoding="utf-8")
    return f"{legacy}\n{edge_motion}"

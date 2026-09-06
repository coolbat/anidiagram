"""High-fidelity HTML runtime renderer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .motion_manifest_v2 import build_motion_manifest
from .localization import font_stack, scene_locale, viewer_labels
from .renderer_svg import esc, render_svg
from .model import Scene
from .resources import resource_path
from .runtime_dependencies import runtime_dependency_markup


def render_html_runtime(
    scene: Scene,
    style: Dict[str, Any],
    runtime: str = "gsap",
    *,
    dependency_mode: str = "cdn",
    dependency_source: Optional[Path] = None,
    locale: str = "auto",
    runtime_mode: str = "ambient",
) -> str:
    manifest = build_motion_manifest(scene, style, runtime=runtime, mode=runtime_mode)
    svg = render_svg(scene, style, animation_mode="runtime-stage")
    manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2).replace("</", "<\\/")
    runtime_js = _runtime_source()
    gsap_script = runtime_dependency_markup(runtime, dependency_mode, dependency_source)
    resolved_locale = _resolve_locale(scene, locale)
    labels = _viewer_labels(resolved_locale)
    font_family = font_stack(resolved_locale)
    html = f"""<!doctype html>
<html lang="{esc(resolved_locale)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(scene.title.text)} {esc(labels['runtime_suffix'])}</title>
  <link rel="icon" href="data:,">
  <style>
    body {{ margin: 0; background: #0b1020; color: #f8fafc; font-family: {font_family}; }}
    main {{ min-height: 100vh; display: grid; grid-template-rows: auto 1fr; gap: 12px; padding: 16px; box-sizing: border-box; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
    button, a {{ border: 1px solid #475569; background: #111827; color: #f8fafc; border-radius: 8px; padding: 8px 10px; font: inherit; text-decoration: none; cursor: pointer; }}
    button:hover, a:hover {{ background: #1f2937; }}
    button:focus-visible, a:focus-visible, .stage:focus-visible {{ outline: 3px solid #38bdf8; outline-offset: 2px; }}
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
    .runtime-warning {{ margin: 0; padding: 8px 10px; border: 1px solid #f59e0b; border-radius: 8px; color: #fde68a; background: #451a03; }}
    .sr-only {{ position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }}
  </style>
</head>
<body>
  <main id="viewer" class="motion-expressive" data-runtime="{esc(runtime)}" data-runtime-mode="{esc(runtime_mode)}"
        data-label-play="{esc(labels['play'])}" data-label-pause="{esc(labels['pause'])}"
        data-label-ready="{esc(labels['ready'])}" data-label-restarted="{esc(labels['restarted'])}"
        data-label-dependency-warning="{esc(labels['dependency_warning'])}">
    <div class="toolbar" role="toolbar" aria-label="{esc(labels['toolbar'])}">
      <button type="button" id="toggle">{esc(labels['pause'])}</button>
      <button type="button" id="restart">{esc(labels['restart'])}</button>
      <button type="button" id="timeline-start" hidden>{esc(labels['explain'])}</button>
      <button type="button" id="timeline-previous" hidden>{esc(labels['previous'])}</button>
      <button type="button" id="timeline-next" hidden>{esc(labels['next'])}</button>
      <button type="button" class="motion-choice" data-motion="expressive" aria-pressed="true">{esc(labels['expressive'])}</button>
      <button type="button" class="motion-choice" data-motion="readable" aria-pressed="false">{esc(labels['readable'])}</button>
      <button type="button" class="motion-choice" data-motion="off" aria-pressed="false">{esc(labels['off'])}</button>
      <button type="button" id="zoom-in">{esc(labels['zoom_in'])}</button>
      <button type="button" id="zoom-out">{esc(labels['zoom_out'])}</button>
      <button type="button" id="reset">{esc(labels['reset'])}</button>
      <a id="download" download="{esc(scene.title.text)}.svg">{esc(labels['download'])}</a>
    </div>
    <p id="runtime-warning" class="runtime-warning" role="alert" hidden></p>
    <p id="runtime-status" class="sr-only" role="status" aria-live="polite">{esc(labels['ready'])}</p>
    <div class="stage" id="stage" tabindex="0" aria-label="{esc(labels['stage'])}">
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
    if scene.source_evidence:
        from .reader import evidence_markup
        html = html.replace('    <p id="runtime-warning"', evidence_markup(scene, resolved_locale) + '    <p id="runtime-warning"', 1)
    if scene.reader.get("enabled"):
        from .reader import add_reader
        html = add_reader(html, scene, resolved_locale)
    return html


def _runtime_source() -> str:
    legacy = resource_path("runtime", "anidiagram-runtime.js").read_text(encoding="utf-8")
    illustrated = resource_path("runtime", "illustrated-performance-v6-runtime.js").read_text(encoding="utf-8")
    choreographer = resource_path("runtime", "choreographer-v1-runtime.js").read_text(encoding="utf-8")
    edge_motion = resource_path("runtime", "edge-motion-v1-runtime.js").read_text(encoding="utf-8")
    marker = "\n})();"
    if marker not in legacy:
        raise RuntimeError("AniDiagram runtime closure marker changed")
    prefix, suffix = legacy.rsplit(marker, 1)
    legacy = f"{prefix}\n{illustrated}\n{choreographer}{marker}{suffix}"
    return f"{legacy}\n{edge_motion}"


def _resolve_locale(scene: Scene, locale: str) -> str:
    return scene_locale(scene, locale)


def _viewer_labels(locale: str) -> Dict[str, str]:
    return viewer_labels(locale)

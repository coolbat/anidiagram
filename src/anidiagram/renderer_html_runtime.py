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
    canvas = style.get("canvas", {})
    background = esc(canvas.get("background", "#0b1020"))
    foreground = esc(canvas.get("text", "#f8fafc"))
    muted = esc(canvas.get("muted", "#94a3b8"))
    accent = esc(style.get("title", {}).get("accent", "#38bdf8"))
    zh = resolved_locale == "zh-CN"
    menu_label = "更多" if zh else "More"
    copy_label = "复制链接" if zh else "Copy link"
    recommend = "节点较多，建议使用易读模式" if zh else "Many nodes — try Readable mode"
    html = f"""<!doctype html>
<html lang="{esc(resolved_locale)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(scene.title.text)} {esc(labels['runtime_suffix'])}</title>
  <link rel="icon" href="data:,">
  <style>
    body {{ --surface: {background}; --ink: {foreground}; --muted: {muted}; --accent: {accent}; margin: 0; background: var(--surface); color: var(--ink); font-family: {font_family}; }}
    main {{ height: 100vh; height: 100dvh; min-height: 360px; display: flex; flex-direction: column; gap: 12px; padding: 16px; box-sizing: border-box; }}
    .toolbar {{ max-width: 100%; box-sizing: border-box; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center; align-self: center; z-index: 5; padding: 6px; border: 1px solid color-mix(in srgb, var(--ink) 18%, transparent); border-radius: 16px; background: color-mix(in srgb, var(--surface) 88%, transparent); backdrop-filter: blur(14px); box-shadow: 0 6px 24px #00000012; }}
    .toolbar-group {{ flex-wrap: wrap; max-width: 100%; display: flex; gap: 3px; align-items: center; }}
    .toolbar-group + .toolbar-group {{ border-left: 1px solid color-mix(in srgb, var(--ink) 18%, transparent); padding-left: 8px; }}
    .viewer-menu {{ position: relative; }}
    .viewer-menu summary {{ padding: 8px 10px; cursor: pointer; }}
    .menu-items {{ position: absolute; right: 0; top: 100%; min-width: 170px; padding: 6px; display: grid; gap: 5px; background: var(--surface); border: 1px solid var(--muted); border-radius: 12px; }}
    .readable-hint {{ margin: 0; text-align: center; color: var(--muted); font-size: 13px; }}
    .narration {{ border: 1px solid color-mix(in srgb, var(--ink) 18%, transparent); border-radius: 14px; padding: 12px 18px; background: var(--surface); flex: none; }}
    .narration[hidden] {{ display: none; }}
    .narration-header {{ display: flex; align-items: center; gap: 12px; }}
    .narration h2 {{ overflow-wrap: anywhere; font-size: 18px; margin: 5px 0; }}
    .narration p {{ margin: 4px 0; color: var(--muted); font-size: 14px; }}
    .narration a {{ display: inline-block; padding: 3px 6px; font-size: 12px; }}
    .narration-progress {{ display: flex; gap: 6px; flex-wrap: wrap; margin-left: auto; }}
    .step-dot {{ padding: 0; width: 10px; height: 10px; border-radius: 50%; background: var(--muted); opacity: .4; }}
    .step-dot[aria-current="step"] {{ background: var(--accent); opacity: 1; }}
    #viewport .context-dim {{ opacity: .25; }}
    #viewport .context-focus {{ filter: drop-shadow(0 0 3px color-mix(in srgb, var(--accent) 35%, transparent)); }}
    @media (max-width: 640px) {{ main {{ padding: 8px; gap: 6px; }} .toolbar {{ gap: 4px; }} button, a {{ font-size: 12px; padding: 6px; }} .narration {{ padding: 8px 10px; }} }}
    button, a {{ border: 1px solid color-mix(in srgb, var(--ink) 18%, transparent); background: transparent; color: var(--ink); border-radius: 8px; padding: 8px 10px; font: inherit; text-decoration: none; cursor: pointer; }}
    button:hover, a:hover {{ background: color-mix(in srgb, var(--ink) 9%, var(--surface)); }}
    button:focus-visible, a:focus-visible, .stage:focus-visible {{ outline: 3px solid #38bdf8; outline-offset: 2px; }}
    button[aria-pressed="true"] {{ background: color-mix(in srgb, var(--accent) 15%, var(--surface)); border-color: var(--accent); }}
    .stage {{ position: relative; box-sizing: border-box; flex: 1; width: 100%; min-height: 120px; overflow: hidden; border: 1px solid color-mix(in srgb, var(--ink) 14%, transparent); border-radius: 12px; background: var(--surface); cursor: grab; }}
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
      <div class="toolbar-group" role="group" aria-label="Playback">
      <button type="button" id="toggle">{esc(labels['pause'])}</button>
      <button type="button" id="restart">{esc(labels['restart'])}</button>
      <button type="button" id="timeline-start" hidden>{esc(labels['explain'])}</button>
      <button type="button" id="timeline-previous" hidden>{esc(labels['previous'])}</button>
      <button type="button" id="timeline-next" hidden>{esc(labels['next'])}</button>
      </div>
      <div class="toolbar-group" role="group" aria-label="Motion">
      <button type="button" class="motion-choice" data-motion="expressive" aria-pressed="true">{esc(labels['expressive'])}</button>
      <button type="button" class="motion-choice" data-motion="readable" aria-pressed="false">{esc(labels['readable'])}</button>
      <button type="button" class="motion-choice" data-motion="off" aria-pressed="false">{esc(labels['off'])}</button>
      </div>
      <div class="toolbar-group" role="group" aria-label="Zoom">
      <button type="button" id="zoom-in">{esc(labels['zoom_in'])}</button>
      <button type="button" id="zoom-out">{esc(labels['zoom_out'])}</button>
      <button type="button" id="reset">{esc(labels['reset'])}</button>
      </div>
      <details class="viewer-menu"><summary>{menu_label}</summary><div class="menu-items">
      <a id="download" download="{esc(scene.title.text)}.svg">{esc(labels['download'])}</a>
      <button type="button" id="copy-link">{copy_label}</button>
      </div></details>
    </div>
    <p id="readable-hint" class="readable-hint" hidden>{recommend}</p>
    <p id="runtime-warning" class="runtime-warning" role="alert" hidden></p>
    <p id="runtime-status" class="sr-only" role="status" aria-live="polite">{esc(labels['ready'])}</p>
    <div class="stage" id="stage" tabindex="0" aria-label="{esc(labels['stage'])}">
      <div class="viewport" id="viewport">
{svg}
      </div>
    </div>
    <section id="narration" class="narration" aria-label="{'逐步讲解' if zh else 'Step by step explanation'}" hidden>
      <div class="narration-header"><span id="narration-count"></span><div id="narration-progress" class="narration-progress"></div></div>
      <h2 id="narration-label"></h2><p id="narration-route"></p><p id="narration-condition" hidden></p><div id="narration-sources"></div>
    </section>
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
    if scene.type_semantics:
        from .type_semantics import semantic_facts
        label = "图类型语义" if resolved_locale == "zh-CN" else "Diagram semantics"
        facts = ''.join('<li>' + esc(fact) + '</li>' for fact in semantic_facts(scene, resolved_locale))
        html = html.replace('    <p id="runtime-warning"', f'<details id="type-semantics"><summary>{label}</summary><ol>{facts}</ol></details>\n    <p id="runtime-warning"', 1)
    from .label_placement import readable_labels
    if readable_labels(style):
        from .relation_table import add_relation_table
        html = add_relation_table(html, scene, resolved_locale)
    return html


def _runtime_source() -> str:
    modules = json.loads(resource_path("runtime", "modules.json").read_text(encoding="utf-8"))
    def source(section: str) -> str:
        return "\n".join(resource_path("runtime", name).read_text(encoding="utf-8") for name in modules[section])
    bootstrap = resource_path("runtime", "anidiagram-runtime.js").read_text(encoding="utf-8")
    for section in ("core", "extensions"):
        marker = "/* ANIDIAGRAM_" + section.upper() + " */"
        if bootstrap.count(marker) != 1:
            raise RuntimeError("AniDiagram runtime assembly marker changed: " + section)
        bootstrap = bootstrap.replace(marker, source(section))
    return source("before") + "\n" + bootstrap + "\n" + source("after")


def _resolve_locale(scene: Scene, locale: str) -> str:
    return scene_locale(scene, locale)


def _viewer_labels(locale: str) -> Dict[str, str]:
    return viewer_labels(locale)

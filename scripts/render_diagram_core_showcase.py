#!/usr/bin/env python3
"""Generate the self-contained Diagram Core showcase presentation review."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Dict, Mapping, Tuple
from xml.etree import ElementTree

from anidiagram.diagram_core.adapter import render_preview_icon
from anidiagram.diagram_core.instance_ids import part_dom_id
from anidiagram.diagram_core.tokens import token_contexts, token_css
from render_diagram_core_contact_sheet import _publish_outputs


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets" / "diagram-core"
RUNTIME_PATH = ROOT / "runtime" / "anidiagram-runtime.js"
MOTION_CATALOG_PATH = ROOT / "runtime" / "motion-catalog.json"
GSAP_PATH = ROOT / "node_modules" / "gsap" / "dist" / "gsap.min.js"
ICONS = ("agent", "database", "api", "server")
PART_BINDINGS = {
    "agent": {
        "body": "body",
        "antenna": "antenna",
        "eyeLeft": "eye-left",
        "eyeRight": "eye-right",
        "core": "core",
    },
    "database": {
        "body": "body",
        "topRing": "top-ring",
        "layerTop": "layer-top",
        "layerMiddle": "layer-middle",
        "layerBottom": "layer-bottom",
        "core": "core",
    },
    "api": {
        "body": "body",
        "inputInterface": "input-interface",
        "outputInterface": "output-interface",
        "processor": "processor",
        "indicatorGroup": "indicator-group",
    },
    "server": {
        "body": "body",
        "trayTop": "tray-top",
        "trayBottom": "tray-bottom",
        "indicatorTop": "indicator-top",
        "indicatorBottom": "indicator-bottom",
        "ventTop": "vent-top",
        "ventBottom": "vent-bottom",
    },
}
DISPLAY_NAMES = {
    "agent": "Agent",
    "database": "Database",
    "api": "API",
    "server": "Server",
}


def _escaped(value: object) -> str:
    return html.escape(str(value), quote=True)


def _script_source(path: Path, label: str) -> str:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise RuntimeError("cannot read {0}: {1}".format(label, error)) from error
    source = "\n".join(line.rstrip() for line in source.splitlines())
    return source.replace("</script", "<\\/script")


def _motion_catalog() -> Dict[str, Mapping[str, object]]:
    try:
        payload = json.loads(MOTION_CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError("cannot read motion catalog: {0}".format(error)) from error
    definitions = payload.get("diagram_core_presentations")
    if not isinstance(definitions, list):
        raise RuntimeError("motion catalog is missing diagram_core_presentations")
    by_icon = {}
    for definition in definitions:
        if not isinstance(definition, dict):
            raise RuntimeError("motion catalog showcase definitions must be objects")
        icon_id = definition.get("icon")
        if icon_id not in ICONS or icon_id in by_icon:
            raise RuntimeError("motion catalog must define each showcase icon exactly once")
        expected = {
            "id": "{0}.showcase-loop-v1".format(icon_id),
            "runtime_id": "{0}-showcase-loop-v1".format(icon_id),
            "kind": "presentation",
            "profile": "showcase",
            "icon_system": "diagram-core-v1",
            "rest_pose": "authored-rest-pose",
            "repeat_policy": "scene-controlled",
            "cancel_behavior": "restore-rest-pose",
            "reduced_motion_behavior": "static-rest",
            "status": "visual-review",
        }
        for name, value in expected.items():
            if definition.get(name) != value:
                raise RuntimeError(
                    "motion catalog {0} must equal {1!r} for {2}".format(
                        name, value, icon_id
                    )
                )
        required_parts = definition.get("required_parts")
        optional_parts = definition.get("optional_parts")
        if not isinstance(required_parts, list) or not isinstance(optional_parts, list):
            raise RuntimeError("showcase required_parts and optional_parts must be arrays")
        declared_parts = tuple(required_parts) + tuple(optional_parts)
        if declared_parts != tuple(PART_BINDINGS[icon_id].values()):
            raise RuntimeError(
                "motion catalog parts do not match showcase bindings for " + icon_id
            )
        rest_at = definition.get("rest_at")
        repeat_delay = definition.get("repeat_delay")
        duration_ms = definition.get("duration_ms")
        if not isinstance(rest_at, (int, float)) or rest_at <= 0:
            raise RuntimeError("showcase rest_at must be positive for " + icon_id)
        if not isinstance(repeat_delay, (int, float)) or not 0.8 <= repeat_delay <= 1.4:
            raise RuntimeError("showcase repeat_delay must be 0.8-1.4 seconds")
        if not isinstance(duration_ms, int) or not 1600 <= duration_ms <= 2400:
            raise RuntimeError("showcase duration_ms must be 1600-2400")
        by_icon[icon_id] = definition
    if tuple(by_icon) != ICONS:
        raise RuntimeError("motion catalog showcase definitions must follow icon order")
    return by_icon


def _tokens() -> Tuple[Dict[str, str], Dict[str, str]]:
    defaults, contexts = token_contexts(token_css())
    return defaults, contexts["blue"]


def _icon_fragment(
    icon_id: str,
    x: int,
    tokens: Mapping[str, str],
    definition: Mapping[str, object],
) -> Tuple[str, dict]:
    instance_id = "diagram-core-showcase.{0}".format(icon_id)
    adapter_tokens = {
        name: value
        for name, value in tokens.items()
        if name != "--icon-surface-contrast"
    }
    fragment = render_preview_icon(
        icon_id,
        instance_id,
        size=144,
        x=x + 28,
        y=76,
        tokens=adapter_tokens,
        asset_root=ASSET_ROOT,
    )
    root = ElementTree.fromstring(fragment)
    root.set("data-icon-presentation", "showcase")
    root.set("data-performance", str(definition["runtime_id"]))
    root.set("data-presentation-performance", str(definition["id"]))
    rendered = ElementTree.tostring(root, encoding="unicode", short_empty_elements=True)
    parts = {
        runtime_name: "#" + part_dom_id(instance_id, icon_id, part_name)
        for runtime_name, part_name in PART_BINDINGS[icon_id].items()
    }
    entry = {
        "node_id": "showcase-{0}".format(icon_id),
        "icon": icon_id,
        "icon_system": "diagram-core-v1",
        "performance": definition["runtime_id"],
        "presentation_performance": definition["id"],
        "presentation_profile": "showcase",
        "trigger": "on-load",
        "loop": "action-then-rest",
        "delay": round(ICONS.index(icon_id) * 0.14, 2),
        "intensity": 1.0,
        "rest_at": definition["rest_at"],
        "repeat_delay": definition["repeat_delay"],
        "duration_ms": definition["duration_ms"],
        "repeat_policy": definition["repeat_policy"],
        "cancel_behavior": definition["cancel_behavior"],
        "reduced_motion_behavior": definition["reduced_motion_behavior"],
        "parts": parts,
    }
    return rendered, entry


def render_showcase_html() -> str:
    definitions = _motion_catalog()
    gsap_source = _script_source(GSAP_PATH, "pinned GSAP runtime")
    runtime_source = _script_source(RUNTIME_PATH, "AniDiagram runtime")
    defaults, blue = _tokens()
    cards = []
    manifest_icons = []
    for index, icon_id in enumerate(ICONS):
        x = 32 + index * 224
        fragment, manifest_entry = _icon_fragment(
            icon_id, x, blue, definitions[icon_id]
        )
        manifest_icons.append(manifest_entry)
        cards.append(
            """      <g data-showcase-card="{icon_id}" role="img" aria-label="{label} showcase presentation">
        <rect x="{x}" y="32" width="200" height="244" rx="30" fill="{surface}" stroke="{recessed}" stroke-width="2"/>
        <rect x="{inner_x}" y="56" width="160" height="176" rx="24" fill="{secondary}"/>
{fragment}
        <text x="{label_x}" y="254" text-anchor="middle" fill="{stroke}" font-size="18" font-weight="750">{label}</text>
      </g>""".format(
                icon_id=_escaped(icon_id),
                label=_escaped(DISPLAY_NAMES[icon_id]),
                x=x,
                inner_x=x + 20,
                label_x=x + 100,
                surface=_escaped(blue["--icon-surface-main"]),
                secondary=_escaped(blue["--icon-surface-secondary"]),
                recessed=_escaped(blue["--icon-surface-recessed"]),
                stroke=_escaped(blue["--icon-stroke"]),
                fragment=fragment,
            )
        )
    manifest = {
        "version": "diagram-core-showcase-1",
        "mode": "ambient",
        "profile": "showcase",
        "icon_system": "diagram-core-v1",
        "icons": manifest_icons,
        "edges": [],
        "groups": [],
    }
    manifest_json = json.dumps(manifest, ensure_ascii=True, indent=2).replace(
        "</", "<\\/"
    )
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <link rel="icon" href="data:,">
  <title>Diagram Core showcase presentation · AniDiagram</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-width: 1024px; background: #f0edff; color: {text}; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ width: 1024px; margin: 0 auto; padding: 38px 32px 56px; }}
    header {{ display: flex; justify-content: space-between; gap: 32px; align-items: end; margin-bottom: 24px; }}
    h1, p {{ margin: 0; }}
    h1 {{ font-size: 38px; line-height: 1; letter-spacing: -0.035em; }}
    .eyebrow {{ margin-bottom: 10px; color: #6652c8; font-size: 12px; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; }}
    .lede {{ max-width: 550px; margin-top: 12px; color: #566178; }}
    .toolbar {{ display: flex; flex: 0 0 360px; flex-wrap: nowrap; justify-content: flex-end; gap: 8px; }}
    button {{ border: 1px solid #cbc4ee; border-radius: 999px; background: #fffaf2; color: {text}; padding: 9px 14px; font: inherit; font-weight: 700; cursor: pointer; }}
    button[aria-pressed="true"] {{ background: #6652c8; border-color: #6652c8; color: white; }}
    #stage {{ overflow: hidden; border: 1px solid #d7d0f2; border-radius: 34px; background: #e8e3ff; box-shadow: 0 24px 70px rgba(69, 55, 126, 0.16); }}
    #viewport, svg {{ display: block; width: 960px; height: 308px; }}
    .note {{ margin-top: 18px; color: #667085; font-size: 14px; }}
    .motion-off [data-icon-presentation],
    .motion-readable [data-icon-presentation] {{ filter: none; }}
    @media (prefers-reduced-motion: reduce) {{
      [data-icon-presentation], [data-icon-presentation] * {{ animation: none !important; transition: none !important; }}
    }}
  </style>
</head>
<body>
  <main id="viewer" class="motion-expressive" data-runtime="gsap" data-display-mode="showcase">
    <header>
      <div>
        <p class="eyebrow">Diagram Core v1 · Presentation Profile</p>
        <h1>Showcase motion</h1>
        <p class="lede">One deliberately expressive display mode. It demonstrates identity and movable parts; it does not mean idle, processing, success, warning, or error.</p>
      </div>
      <div class="toolbar" aria-label="Motion controls">
        <button type="button" id="toggle">Pause</button>
        <button type="button" id="restart">Replay</button>
        <button type="button" class="motion-choice" data-motion="expressive" aria-pressed="true">Showcase</button>
        <button type="button" class="motion-choice" data-motion="off" aria-pressed="false">Off</button>
      </div>
    </header>
    <div id="stage" class="stage">
      <div id="viewport" class="viewport">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 308" width="960" height="308" role="img" aria-label="Four Diagram Core icons playing the showcase presentation" data-motion-profile="showcase">
{cards}
        </svg>
      </div>
    </div>
    <p class="note">Static SVG remains the source of truth. Off, reduced motion, missing GSAP, cancel, and restart all settle to the authored rest pose.</p>
  </main>
  <script type="application/json" id="anidiagram-motion-manifest">
{manifest}
  </script>
  <script>
if (!new URLSearchParams(window.location.search).has("no-gsap")) {{
{gsap}
}}
  </script>
  <script>
{runtime}
  </script>
</body>
</html>
""".format(
        text=_escaped(defaults["--icon-stroke"]),
        cards="\n".join(cards),
        manifest=manifest_json,
        gsap=gsap_source,
        runtime=runtime_source,
    )


def _publish(output: Path, source: str) -> None:
    if output.suffix.lower() != ".html":
        raise ValueError("showcase output must end in .html")
    _publish_outputs(((output, source.encode("utf-8")),))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the Diagram Core showcase presentation review."
    )
    parser.add_argument("--icons", required=True)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    if arguments.icons != ",".join(ICONS):
        parser.error("--icons must be agent,database,api,server")
    try:
        source = render_showcase_html()
        _publish(arguments.output, source)
    except (OSError, RuntimeError, ValueError) as error:
        parser.error(str(error))
    print("icons=4 profile=showcase performances=4 runtime=gsap fallback=authored-rest")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate the self-contained Diagram Core showcase presentation review."""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
from typing import Dict, Mapping, Optional, Sequence, Tuple
from xml.etree import ElementTree

from anidiagram.diagram_core.adapter import render_preview_icon
from anidiagram.diagram_core.catalog import load_catalog
from anidiagram.diagram_core.instance_ids import part_dom_id
from anidiagram.diagram_core.manifest import load_manifest
from anidiagram.diagram_core.tokens import token_contexts, token_css
from render_diagram_core_contact_sheet import _publish_outputs


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets" / "diagram-core"
RUNTIME_PATH = ROOT / "runtime" / "anidiagram-runtime.js"
MOTION_CATALOG_PATH = ROOT / "runtime" / "motion-catalog.json"
GSAP_PATH = ROOT / "node_modules" / "gsap" / "dist" / "gsap.min.js"
SHOWCASE_COLUMNS = 4
CARD_X = 32
CARD_Y = 32
CARD_WIDTH = 200
CARD_HEIGHT = 244
COLUMN_STRIDE = 224
ROW_STRIDE = 276
STAGE_WIDTH = 960
HAND_TUNED_PERFORMANCE_IDS = frozenset(
    {
        "agent-showcase-loop-v1",
        "database-showcase-loop-v1",
        "api-showcase-loop-v1",
        "server-showcase-loop-v1",
    }
)
RECIPE_PROPERTIES = frozenset(
    {"x", "y", "rotate", "scale", "scaleX", "scaleY", "opacity"}
)
RECIPE_EASES = frozenset(
    {
        "none",
        "sine.in",
        "sine.out",
        "sine.inOut",
        "power1.in",
        "power1.out",
        "power1.inOut",
        "power2.in",
        "power2.out",
        "power2.inOut",
        "power3.in",
        "power3.out",
        "power3.inOut",
        "back.out(2.4)",
        "back.out(2.8)",
        "back.out(3)",
        "back.out(3.5)",
        "bounce.out",
        "elastic.out(1, 0.35)",
        "elastic.out(1, 0.4)",
    }
)


def _escaped(value: object) -> str:
    return html.escape(str(value), quote=True)


def _script_source(path: Path, label: str) -> str:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise RuntimeError("cannot read {0}: {1}".format(label, error)) from error
    source = "\n".join(line.rstrip() for line in source.splitlines())
    return source.replace("</script", "<\\/script")


def _display_name(icon_id: str) -> str:
    return "API" if icon_id == "api" else icon_id.replace("-", " ").title()


def _runtime_part_name(part_name: str) -> str:
    head, *tail = part_name.split("-")
    return head + "".join(value.title() for value in tail)


def _visual_review_icons() -> Tuple[str, ...]:
    catalog = load_catalog(ASSET_ROOT)
    return tuple(
        entry.icon_id for entry in catalog.entries if entry.status == "visual-review"
    )


def _finite_number(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def _validate_recipe(
    icon_id: str,
    recipe: object,
    declared_parts: Tuple[str, ...],
    rest_at: float,
) -> None:
    prefix = "motion catalog recipe for " + icon_id
    if not isinstance(recipe, dict) or set(recipe) != {"tracks"}:
        raise RuntimeError(prefix + " must contain only tracks")
    tracks = recipe.get("tracks")
    if not isinstance(tracks, list) or not tracks or len(tracks) > 12:
        raise RuntimeError(prefix + " tracks must be a nonempty array of at most 12")
    declared = frozenset(declared_parts)
    seen_parts = set()
    for track_index, track in enumerate(tracks):
        track_prefix = "{0} track {1}".format(prefix, track_index)
        if not isinstance(track, dict) or set(track) != {"parts", "steps"}:
            raise RuntimeError(track_prefix + " must contain only parts and steps")
        parts = track.get("parts")
        if (
            not isinstance(parts, list)
            or not parts
            or len(parts) > 4
            or any(not isinstance(part, str) or part not in declared for part in parts)
            or len(parts) != len(set(parts))
        ):
            raise RuntimeError(
                track_prefix + " parts must be 1-4 unique declared part names"
            )
        duplicate_parts = seen_parts.intersection(parts)
        if duplicate_parts:
            raise RuntimeError(
                track_prefix
                + " targets a part used by more than one recipe track: "
                + ",".join(sorted(duplicate_parts))
            )
        seen_parts.update(parts)
        steps = track.get("steps")
        if not isinstance(steps, list) or not steps or len(steps) > 12:
            raise RuntimeError(
                track_prefix + " steps must be a nonempty array of at most 12"
            )
        for step_index, step in enumerate(steps):
            step_prefix = "{0} step {1}".format(track_prefix, step_index)
            if not isinstance(step, dict):
                raise RuntimeError(step_prefix + " must be an object")
            if set(step) - {"to", "duration", "ease", "at", "stagger"}:
                raise RuntimeError(step_prefix + " contains an unsupported field")
            if not {"to", "duration", "ease", "at"}.issubset(step):
                raise RuntimeError(step_prefix + " is missing a required field")
            target = step.get("to")
            if (
                not isinstance(target, dict)
                or not target
                or not set(target).issubset(RECIPE_PROPERTIES)
            ):
                raise RuntimeError(step_prefix + " to contains an unsupported property")
            for property_name, value in target.items():
                if not _finite_number(value):
                    raise RuntimeError(step_prefix + " property values must be finite")
                if property_name in {"x", "y"} and abs(value) > 10:
                    raise RuntimeError(step_prefix + " translation exceeds 10 units")
                rotation_limit = (
                    360 if icon_id == "search" and parts == ["scan"] else 14
                )
                if property_name == "rotate" and abs(value) > rotation_limit:
                    raise RuntimeError(
                        step_prefix
                        + " rotation exceeds {0} degrees".format(rotation_limit)
                    )
                if property_name in {"scale", "scaleX", "scaleY"} and not 0.12 <= value <= 1.45:
                    raise RuntimeError(step_prefix + " scale is outside 0.12-1.45")
                if property_name == "opacity" and not 0 <= value <= 1:
                    raise RuntimeError(step_prefix + " opacity is outside 0-1")
            duration = step.get("duration")
            at = step.get("at")
            stagger = step.get("stagger", 0)
            if not _finite_number(duration) or not 0.04 <= duration <= 0.8:
                raise RuntimeError(step_prefix + " duration is outside 0.04-0.8 seconds")
            if not _finite_number(at) or at < 0:
                raise RuntimeError(step_prefix + " at must be a nonnegative number")
            if not _finite_number(stagger) or not 0 <= stagger <= 0.12:
                raise RuntimeError(step_prefix + " stagger is outside 0-0.12 seconds")
            if step.get("ease") not in RECIPE_EASES:
                raise RuntimeError(step_prefix + " ease is not allowlisted")
            if at + duration + stagger * (len(parts) - 1) > rest_at + 1e-9:
                raise RuntimeError(step_prefix + " extends beyond rest_at")


def _motion_catalog(
    visual_review_icons: Sequence[str],
) -> Dict[str, Mapping[str, object]]:
    try:
        payload = json.loads(MOTION_CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError("cannot read motion catalog: {0}".format(error)) from error
    definitions = payload.get("diagram_core_presentations")
    if not isinstance(definitions, list):
        raise RuntimeError("motion catalog is missing diagram_core_presentations")
    by_icon = {}
    eligible_icons = frozenset(visual_review_icons)
    for definition in definitions:
        if not isinstance(definition, dict):
            raise RuntimeError("motion catalog showcase definitions must be objects")
        icon_id = definition.get("icon")
        if icon_id not in eligible_icons or icon_id in by_icon:
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
        if (
            not required_parts
            or len(declared_parts) != len(set(declared_parts))
            or any(not isinstance(part, str) for part in declared_parts)
        ):
            raise RuntimeError(
                "motion catalog parts must be unique nonempty strings for " + icon_id
            )
        manifest = load_manifest(icon_id, ASSET_ROOT)
        if manifest.status != "visual-review":
            raise RuntimeError("showcase manifest must be visual-review for " + icon_id)
        if any(part not in manifest.parts for part in declared_parts):
            raise RuntimeError(
                "motion catalog parts do not exist in the icon manifest for " + icon_id
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
        expected_duration_ms = round(rest_at / 0.6 * 1000)
        if abs(duration_ms - expected_duration_ms) > 20:
            raise RuntimeError("showcase duration_ms must compile from rest_at")
        recipe = definition.get("recipe")
        if recipe is None and definition.get("runtime_id") not in HAND_TUNED_PERFORMANCE_IDS:
            raise RuntimeError("showcase recipe is required for " + icon_id)
        if recipe is not None:
            _validate_recipe(icon_id, recipe, declared_parts, rest_at)
        by_icon[icon_id] = definition
    if frozenset(by_icon) != eligible_icons:
        raise RuntimeError(
            "motion catalog must define every visual-review icon exactly once"
        )
    return by_icon


def _tokens() -> Tuple[Dict[str, str], Dict[str, str]]:
    defaults, contexts = token_contexts(token_css())
    return defaults, contexts["blue"]


def _icon_fragment(
    icon_id: str,
    x: int,
    y: int,
    index: int,
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
        y=y + 44,
        tokens=adapter_tokens,
        asset_root=ASSET_ROOT,
    )
    root = ElementTree.fromstring(fragment)
    root.set("data-icon-presentation", "showcase")
    root.set("data-performance", str(definition["runtime_id"]))
    root.set("data-presentation-performance", str(definition["id"]))
    rendered = ElementTree.tostring(root, encoding="unicode", short_empty_elements=True)
    declared_parts = load_manifest(icon_id, ASSET_ROOT).parts
    parts = {
        _runtime_part_name(part_name): "#"
        + part_dom_id(instance_id, icon_id, part_name)
        for part_name in declared_parts
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
        "delay": round((index % SHOWCASE_COLUMNS) * 0.14, 2),
        "intensity": 1.0,
        "rest_at": definition["rest_at"],
        "repeat_delay": definition["repeat_delay"],
        "duration_ms": definition["duration_ms"],
        "repeat_policy": definition["repeat_policy"],
        "cancel_behavior": definition["cancel_behavior"],
        "reduced_motion_behavior": definition["reduced_motion_behavior"],
        "parts": parts,
    }
    if "recipe" in definition:
        entry["recipe"] = definition["recipe"]
    return rendered, entry


def render_showcase_html(icon_ids: Optional[Sequence[str]] = None) -> str:
    definitions = _motion_catalog(_visual_review_icons())
    showcase_icons = tuple(definitions)
    selected_icons = showcase_icons if icon_ids is None else tuple(icon_ids)
    if not selected_icons:
        raise ValueError("at least one showcase icon is required")
    if len(selected_icons) != len(set(selected_icons)):
        raise ValueError("--icons cannot contain duplicate icon ids")
    invalid = tuple(icon for icon in selected_icons if icon not in showcase_icons)
    if invalid:
        raise ValueError(
            "not an implemented visual-review icon: " + ",".join(invalid)
        )
    presentation_order = {icon: index for index, icon in enumerate(showcase_icons)}
    if tuple(sorted(selected_icons, key=presentation_order.get)) != selected_icons:
        raise ValueError("--icons must follow Diagram Core presentation order")
    gsap_source = _script_source(GSAP_PATH, "pinned GSAP runtime")
    runtime_source = _script_source(RUNTIME_PATH, "AniDiagram runtime")
    defaults, blue = _tokens()
    cards = []
    manifest_icons = []
    for index, icon_id in enumerate(selected_icons):
        column = index % SHOWCASE_COLUMNS
        row = index // SHOWCASE_COLUMNS
        x = CARD_X + column * COLUMN_STRIDE
        y = CARD_Y + row * ROW_STRIDE
        fragment, manifest_entry = _icon_fragment(
            icon_id, x, y, index, blue, definitions[icon_id]
        )
        manifest_icons.append(manifest_entry)
        cards.append(
            """      <g data-showcase-card="{icon_id}" role="img" aria-label="{label} showcase presentation">
        <rect x="{x}" y="{y}" width="200" height="244" rx="30" fill="{surface}" stroke="{recessed}" stroke-width="2"/>
        <rect x="{inner_x}" y="{inner_y}" width="160" height="176" rx="24" fill="{secondary}"/>
{fragment}
        <text x="{label_x}" y="{label_y}" text-anchor="middle" fill="{stroke}" font-size="18" font-weight="750">{label}</text>
      </g>""".format(
                icon_id=_escaped(icon_id),
                label=_escaped(_display_name(icon_id)),
                x=x,
                y=y,
                inner_x=x + 20,
                inner_y=y + 24,
                label_x=x + 100,
                label_y=y + 222,
                surface=_escaped(blue["--icon-surface-main"]),
                secondary=_escaped(blue["--icon-surface-secondary"]),
                recessed=_escaped(blue["--icon-surface-recessed"]),
                stroke=_escaped(blue["--icon-stroke"]),
                fragment=fragment,
            )
        )
    row_count = (len(selected_icons) + SHOWCASE_COLUMNS - 1) // SHOWCASE_COLUMNS
    stage_height = row_count * ROW_STRIDE + 32
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
    #viewport, svg {{ display: block; width: {stage_width}px; height: {stage_height}px; }}
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
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {stage_width} {stage_height}" width="{stage_width}" height="{stage_height}" role="img" aria-label="{icon_count} Diagram Core icons playing the showcase presentation" data-motion-profile="showcase" data-showcase-columns="4">
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
        stage_width=STAGE_WIDTH,
        stage_height=stage_height,
        icon_count=len(selected_icons),
    )


def _publish(output: Path, source: str) -> None:
    if output.suffix.lower() != ".html":
        raise ValueError("showcase output must end in .html")
    _publish_outputs(((output, source.encode("utf-8")),))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the Diagram Core showcase presentation review."
    )
    parser.add_argument(
        "--icons",
        help="Optional comma-separated visual-review icon subset in presentation order.",
    )
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    selected_icons = None
    if arguments.icons is not None:
        selected_icons = tuple(arguments.icons.split(","))
    try:
        source = render_showcase_html(selected_icons)
        _publish(arguments.output, source)
    except (OSError, RuntimeError, ValueError) as error:
        parser.error(str(error))
    icon_count = len(_visual_review_icons() if selected_icons is None else selected_icons)
    print(
        "icons={0} profile=showcase performances={0} runtime=gsap fallback=authored-rest".format(
            icon_count
        )
    )
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Render a self-contained Kubernetes architecture with frozen Diagram Core v1 assets."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from pathlib import Path
from typing import Dict, Mapping, Sequence, Tuple
from xml.etree import ElementTree

from anidiagram.diagram_core.adapter import render_preview_icon
from anidiagram.diagram_core.instance_ids import part_dom_id
from anidiagram.diagram_core.manifest import load_manifest
from anidiagram.diagram_core.tokens import token_contexts, token_css
from render_diagram_core_showcase import (
    _motion_catalog,
    _publish,
    _runtime_part_name,
    _script_source,
    _visual_review_icons,
)


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets" / "diagram-core"
RELEASE_PATH = ASSET_ROOT / "releases" / "v1.0.0.json"
RUNTIME_PATH = ROOT / "runtime" / "anidiagram-runtime.js"
MOTION_CATALOG_PATH = ROOT / "runtime" / "motion-catalog.json"
GSAP_PATH = ROOT / "node_modules" / "gsap" / "dist" / "gsap.min.js"

TEMPLATE_STYLE = "diagram-core-light"
STYLE_VARIANTS = {
    "diagram-core-light": {
        "color_scheme": "light",
        "icon_context": "blue",
        "group_tones": {
            "violet": ("#f3efff", "#d8cff9", "#6955c7"),
            "blue": ("#edf6ff", "#c9def5", "#387bb6"),
            "mint": ("#eaf9f5", "#c6eadf", "#278978"),
            "coral": ("#fff2ed", "#f2d3c7", "#b65b43"),
        },
        "edge_active": "#745bd3",
        "edge_quiet": "#9aabc0",
        "edge_label_fill": "#fffdf8",
        "edge_label_stroke": "#d8d1ee",
        "edge_label_text": "#50466f",
        "node_fill": "#fffdf8",
        "node_active_stroke": "#8d78df",
        "node_static_stroke": "#d8dce8",
        "node_text": "#14213d",
        "node_caption": "#6c7486",
        "svg_background": "#fffdf8",
        "grid": "#dfe5f2",
        "grid_opacity": "0",
        "frame": "#d6cfee",
        "frame_opacity": "0",
        "title_panel": "#ddd5ff",
        "title_kicker": "#5f4bbd",
        "title_text": "#14213d",
        "title_summary": "#5f6678",
        "decorative": ("#745bd3", "#45c5bd", "#ffb07c", "#fffdf8"),
        "css_vars": {
            "root-color": "#14213d",
            "root-background": "#f2efff",
            "body-background": "radial-gradient(circle at 18% 0%, #fffaf2 0, #f2efff 38%, #e9f4ff 100%)",
            "eyebrow": "#6955c7",
            "muted": "#626b7c",
            "button-border": "#cec6ed",
            "button-background": "#fffdf8",
            "button-text": "#342d50",
            "button-active": "#6955c7",
            "button-active-text": "#fffdf8",
            "stage-border": "#d6cfee",
            "stage-background": "#fffdf8",
            "stage-shadow": "0 28px 80px rgba(64, 50, 124, .16)",
            "node-shadow": "drop-shadow(0 8px 12px rgba(31, 40, 68, .08))",
            "node-active-shadow": "drop-shadow(0 10px 16px rgba(94, 70, 178, .15))",
            "legend": "#687184",
            "legend-strong": "#4f456f",
        },
    },
    "deep-tech": {
        "color_scheme": "dark",
        "icon_context": "dark",
        "group_tones": {
            "violet": ("#141328", "#594a86", "#a78bfa"),
            "blue": ("#071f2f", "#15506b", "#22d3ee"),
            "mint": ("#052e24", "#17634f", "#34d399"),
            "coral": ("#2a0f16", "#733242", "#fb7185"),
        },
        "edge_active": "#22d3ee",
        "edge_quiet": "#3d5573",
        "edge_tones": {
            "delivery": "#a78bfa",
            "control-plane": "#60a5fa",
            "workload-plane": "#34d399",
            "observability": "#fb7185",
        },
        "edge_label_fill": "#07111f",
        "edge_label_stroke": "#1e4a68",
        "edge_label_text": "#d8f5ff",
        "node_fill": "#0b1224",
        "node_active_stroke": "#38bdf8",
        "node_static_stroke": "#334155",
        "node_tones": {
            "delivery": ("#121229", "#a78bfa", "drop-shadow(0 0 18px rgba(167, 139, 250, .18))"),
            "control-plane": ("#081a2c", "#60a5fa", "drop-shadow(0 0 18px rgba(96, 165, 250, .18))"),
            "workload-plane": ("#071e1b", "#34d399", "drop-shadow(0 0 18px rgba(52, 211, 153, .16))"),
            "observability": ("#25131c", "#fb7185", "drop-shadow(0 0 18px rgba(251, 113, 133, .17))"),
        },
        "node_text": "#f8fafc",
        "node_caption": "#9fb2c8",
        "svg_background": "#050816",
        "grid": "#111c36",
        "grid_opacity": ".56",
        "frame": "#2a4965",
        "frame_opacity": ".82",
        "title_panel": "#0f2742",
        "title_kicker": "#22d3ee",
        "title_text": "#f8fafc",
        "title_summary": "#cbd5e1",
        "decorative": ("#22d3ee", "#a78bfa", "#34d399", "#050816"),
        "css_vars": {
            "root-color": "#f8fafc",
            "root-background": "#050816",
            "body-background": "radial-gradient(circle at 18% 0%, #0f2742 0, #07111f 34%, #050816 76%)",
            "eyebrow": "#22d3ee",
            "muted": "#a8b8cc",
            "button-border": "#23415e",
            "button-background": "#0b1629",
            "button-text": "#d9f4ff",
            "button-active": "#22d3ee",
            "button-active-text": "#04111d",
            "stage-border": "#1e3a5a",
            "stage-background": "#050816",
            "stage-shadow": "0 28px 90px rgba(0, 0, 0, .48)",
            "node-shadow": "drop-shadow(0 8px 14px rgba(0, 0, 0, .28))",
            "node-active-shadow": "drop-shadow(0 0 18px rgba(34, 211, 238, .18))",
            "legend": "#91a3bb",
            "legend-strong": "#d6e7f5",
        },
    },
}


def _escaped(value: object) -> str:
    return html.escape(str(value), quote=True)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _asset_tree_sha256() -> str:
    digest = hashlib.sha256()
    paths = sorted((ASSET_ROOT / "icons").glob("*.svg")) + sorted(
        (ASSET_ROOT / "manifests").glob("*.json")
    )
    for path in paths:
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _verify_frozen_release() -> Mapping[str, object]:
    try:
        release = json.loads(RELEASE_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError("cannot read Diagram Core release lock: {0}".format(error)) from error
    expected = {
        "catalog_sha256": _sha256(ASSET_ROOT / "catalog.json"),
        "tokens_sha256": _sha256(ASSET_ROOT / "tokens.css"),
        "motion_catalog_sha256": _sha256(MOTION_CATALOG_PATH),
        "asset_tree_sha256": _asset_tree_sha256(),
    }
    if (
        release.get("system") != "diagram-core-v1"
        or release.get("version") != "1.0.0"
        or release.get("status") != "frozen"
        or release.get("hashes") != expected
    ):
        raise RuntimeError("Diagram Core v1.0.0 sources no longer match the frozen release")
    return release


def _load_spec(
    path: Path,
    available_icons: Sequence[str],
    style_override: str | None = None,
) -> Mapping[str, object]:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError("cannot read Kubernetes architecture spec: {0}".format(error)) from error
    if style_override is not None:
        spec = dict(spec)
        spec["style"] = style_override
    canvas = spec.get("canvas", {})
    if spec.get("icon_system") != "diagram-core-v1" or spec.get("diagram_core_release") != "1.0.0":
        raise ValueError("Kubernetes spec must opt in to frozen diagram-core-v1 release 1.0.0")
    if spec.get("style") not in STYLE_VARIANTS:
        raise ValueError(
            "Kubernetes spec style must be one of: "
            + ", ".join(sorted(STYLE_VARIANTS))
        )
    if (canvas.get("width"), canvas.get("height")) != (1600, 900):
        raise ValueError("Kubernetes spec canvas must be 1600x900")
    groups = spec.get("groups")
    nodes = spec.get("nodes")
    edges = spec.get("edges")
    motion = spec.get("motion")
    if not isinstance(groups, list) or not isinstance(nodes, list) or not isinstance(edges, list) or not isinstance(motion, dict):
        raise ValueError("Kubernetes spec requires groups, nodes, edges, and motion")
    group_ids = [group.get("id") for group in groups]
    node_ids = [node.get("id") for node in nodes]
    if len(group_ids) != len(set(group_ids)) or any(not value for value in group_ids):
        raise ValueError("Kubernetes group ids must be unique nonempty strings")
    if len(node_ids) != len(set(node_ids)) or any(not value for value in node_ids):
        raise ValueError("Kubernetes node ids must be unique nonempty strings")
    available = frozenset(available_icons)
    for node in nodes:
        if node.get("icon") not in available:
            raise ValueError("unknown Diagram Core icon for node {0}".format(node.get("id")))
        if node.get("group") not in group_ids:
            raise ValueError("unknown group for node {0}".format(node.get("id")))
        position = node.get("position")
        size = node.get("size")
        if (
            not isinstance(position, list)
            or not isinstance(size, list)
            or len(position) != 2
            or len(size) != 2
            or any(not isinstance(value, int) for value in position + size)
        ):
            raise ValueError("node geometry must use integer position and size pairs")
    for edge in edges:
        points = edge.get("points")
        if edge.get("from") not in node_ids or edge.get("to") not in node_ids:
            raise ValueError("edge references an unknown node")
        if (
            not isinstance(points, list)
            or len(points) < 2
            or any(not isinstance(point, list) or len(point) != 2 for point in points)
            or any(not isinstance(value, (int, float)) or not math.isfinite(value) for point in points for value in point)
        ):
            raise ValueError("edge points must contain at least two finite coordinate pairs")
    animated = motion.get("animated_nodes")
    active = motion.get("active_edge_indices")
    labeled = motion.get("labeled_edge_indices")
    readable = motion.get("readable_edge_indices")
    if motion.get("profile") != "full-showcase":
        raise ValueError("Kubernetes Showcase must use the full-showcase motion profile")
    if animated != node_ids:
        raise ValueError("full-showcase animated_nodes must include every node in presentation order")
    if active != list(range(len(edges))):
        raise ValueError("full-showcase active_edge_indices must include every edge")
    if (
        not isinstance(labeled, list)
        or len(labeled) > 2
        or len(labeled) != len(set(labeled))
        or any(not isinstance(index, int) or index < 0 or index >= len(edges) for index in labeled)
    ):
        raise ValueError("labeled_edge_indices must contain at most two unique valid edge indices")
    if (
        not isinstance(readable, list)
        or len(readable) != 2
        or len(readable) != len(set(readable))
        or any(not isinstance(index, int) or index < 0 or index >= len(edges) for index in readable)
    ):
        raise ValueError("readable_edge_indices must contain two unique valid edge indices")
    if not set(readable).issubset(active):
        raise ValueError("readable edges must be a subset of active edges")
    return spec


def _rounded_path(points: Sequence[Sequence[float]], radius: float = 12) -> str:
    def point_text(point: Sequence[float]) -> str:
        return "{0:g} {1:g}".format(point[0], point[1])

    commands = ["M " + point_text(points[0])]
    for index in range(1, len(points) - 1):
        previous = points[index - 1]
        current = points[index]
        following = points[index + 1]
        incoming = math.hypot(current[0] - previous[0], current[1] - previous[1])
        outgoing = math.hypot(following[0] - current[0], following[1] - current[1])
        corner = min(radius, incoming / 2, outgoing / 2)
        if corner <= 0:
            commands.append("L " + point_text(current))
            continue
        before = (
            current[0] + (previous[0] - current[0]) * corner / incoming,
            current[1] + (previous[1] - current[1]) * corner / incoming,
        )
        after = (
            current[0] + (following[0] - current[0]) * corner / outgoing,
            current[1] + (following[1] - current[1]) * corner / outgoing,
        )
        commands.append("L " + point_text(before))
        commands.append("Q {0} {1}".format(point_text(current), point_text(after)))
    commands.append("L " + point_text(points[-1]))
    return " ".join(commands)


def _path_midpoint(points: Sequence[Sequence[float]]) -> Tuple[float, float]:
    segments = []
    total = 0.0
    for start, end in zip(points, points[1:]):
        length = math.hypot(end[0] - start[0], end[1] - start[1])
        segments.append((start, end, length))
        total += length
    target = total / 2
    traversed = 0.0
    for start, end, length in segments:
        if traversed + length >= target:
            ratio = 0 if length == 0 else (target - traversed) / length
            return (start[0] + (end[0] - start[0]) * ratio, start[1] + (end[1] - start[1]) * ratio)
        traversed += length
    return tuple(points[-1])


def _render_group(
    group: Mapping[str, object],
    style: Mapping[str, object],
) -> str:
    x, y, width, height = group["bounds"]
    fill, stroke, label = style["group_tones"][group["tone"]]
    outer = group["id"] in {"delivery", "cluster", "observability"}
    return """    <g class="group" data-group="{group_id}">
      <rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="{stroke_width}"{dash}/>
      <text x="{label_x}" y="{label_y}" fill="{label}" font-size="{font_size}" font-weight="800" letter-spacing="1.4">{text}</text>
    </g>""".format(
        group_id=_escaped(group["id"]),
        x=x,
        y=y,
        width=width,
        height=height,
        radius=30 if outer else 24,
        fill=fill,
        opacity="0.88" if outer else "0.68",
        stroke=stroke,
        stroke_width="2" if outer else "1.5",
        dash="" if outer else ' stroke-dasharray="8 8"',
        label_x=x + 20,
        label_y=y + 30,
        label=label,
        font_size=15 if outer else 13,
        text=_escaped(group["label"]),
    )


def _render_edge(
    edge: Mapping[str, object],
    index: int,
    active_indices: Sequence[int],
    labeled_indices: Sequence[int],
    style: Mapping[str, object],
    color_role: str,
) -> str:
    active = index in active_indices
    edge_tones = style.get("edge_tones", {})
    semantic_stroke = edge_tones.get(color_role, style["edge_active"])
    stroke = semantic_stroke if active else style["edge_quiet"]
    marker = color_role if active and color_role in edge_tones else ("active" if active else "quiet")
    path = _rounded_path(edge["points"])
    label = ""
    path_length = sum(
        math.hypot(end[0] - start[0], end[1] - start[1])
        for start, end in zip(edge["points"], edge["points"][1:])
    )
    if index in labeled_indices and path_length >= 120:
        x, y = _path_midpoint(edge["points"])
        width = max(54, len(str(edge.get("label", ""))) * 7 + 22)
        label = """
      <g class="edge-label" transform="translate({x:g} {y:g})">
        <rect x="-{half:g}" y="-13" width="{width:g}" height="26" rx="13" fill="{label_fill}" stroke="{label_stroke}"/>
        <text y="4" text-anchor="middle" fill="{label_text}" font-size="12" font-weight="750">{text}</text>
      </g>""".format(
            x=x,
            y=y - 16,
            half=width / 2,
            width=width,
            text=_escaped(edge.get("label", "")),
            label_fill=style["edge_label_fill"],
            label_stroke=semantic_stroke if color_role in edge_tones else style["edge_label_stroke"],
            label_text=style["edge_label_text"],
        )
    return """    <g class="edge" data-edge-index="{index}" data-edge-from="{source}" data-edge-to="{target}" data-edge-domain="{color_role}">
      <path class="edge-base" d="{path}" fill="none" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arrow-{kind})"/>{label}
    </g>""".format(
        index=index,
        source=_escaped(edge["from"]),
        target=_escaped(edge["to"]),
        color_role=_escaped(color_role),
        path=_escaped(path),
        stroke=stroke,
        width="3.2" if active else "2.2",
        kind=_escaped(marker),
        label=label,
    )


def _render_arrow_markers(style: Mapping[str, object]) -> str:
    marker_tones = [
        ("active", style["edge_active"], 7),
        ("quiet", style["edge_quiet"], 6),
    ]
    marker_tones.extend(
        (role, color, 7)
        for role, color in style.get("edge_tones", {}).items()
    )
    return "\n".join(
        '            <marker id="arrow-{role}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="{size}" markerHeight="{size}" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/></marker>'.format(
            role=_escaped(role),
            size=size,
            color=_escaped(color),
        )
        for role, color, size in marker_tones
    )


def _manifest_entry(
    node: Mapping[str, object],
    definition: Mapping[str, object],
    order: int,
) -> Dict[str, object]:
    icon_id = str(node["icon"])
    instance_id = "diagram-core-k8s.{0}".format(node["id"])
    parts = {
        _runtime_part_name(part): "#" + part_dom_id(instance_id, icon_id, part)
        for part in load_manifest(icon_id, ASSET_ROOT).parts
    }
    entry: Dict[str, object] = {
        "node_id": node["id"],
        "icon": icon_id,
        "icon_system": "diagram-core-v1",
        "performance": definition["runtime_id"],
        "presentation_performance": definition["id"],
        "presentation_profile": "showcase",
        "trigger": "on-load",
        "loop": "action-then-rest",
        "delay": round(order * 0.16, 2),
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
    return entry


def _render_node(
    node: Mapping[str, object],
    tokens: Mapping[str, str],
    definition: Mapping[str, object] | None,
    style: Mapping[str, object],
) -> Tuple[str, Dict[str, object] | None]:
    x, y = node["position"]
    width, height = node["size"]
    horizontal = height <= 120 or width >= 230
    icon_size = 76 if height <= 120 else (92 if width >= 230 else 88)
    icon_x = x + (12 if horizontal else (width - icon_size) / 2)
    icon_y = y + ((height - icon_size) / 2 if horizontal else 10)
    text_x = x + (100 if height <= 120 else (130 if width >= 230 else width / 2))
    label_y = y + (51 if height <= 120 else (70 if width >= 230 else 119))
    caption_y = y + (76 if height <= 120 else (97 if width >= 230 else 140))
    instance_id = "diagram-core-k8s.{0}".format(node["id"])
    adapter_tokens = {name: value for name, value in tokens.items() if name != "--icon-surface-contrast"}
    fragment = render_preview_icon(
        node["icon"],
        instance_id,
        size=icon_size,
        x=icon_x,
        y=icon_y,
        tokens=adapter_tokens,
        asset_root=ASSET_ROOT,
    )
    root = ElementTree.fromstring(fragment)
    root.set("data-icon-presentation", "showcase")
    root.set("data-diagram-core-release", "1.0.0")
    if definition is not None:
        root.set("data-performance", str(definition["runtime_id"]))
        root.set("data-presentation-performance", str(definition["id"]))
    rendered_icon = ElementTree.tostring(root, encoding="unicode", short_empty_elements=True)
    active_class = " architecture-node--animated" if definition is not None else ""
    node_tone = style.get("node_tones", {}).get(node["group"])
    fill = node_tone[0] if node_tone else style["node_fill"]
    stroke = (
        node_tone[1]
        if definition is not None and node_tone
        else (style["node_active_stroke"] if definition is not None else style["node_static_stroke"])
    )
    shadow = node_tone[2] if definition is not None and node_tone else None
    rendered = """    <g class="architecture-node{active_class}" data-architecture-node="{node_id}" data-node-domain="{domain}"{style_attr} role="img" aria-label="{label}: {caption}">
      <rect x="{x}" y="{y}" width="{width}" height="{height}" rx="24" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>
      {icon}
      <text x="{text_x:g}" y="{label_y:g}" text-anchor="{anchor}" fill="{text_color}" font-size="16" font-weight="800">{label}</text>
      <text x="{text_x:g}" y="{caption_y:g}" text-anchor="{anchor}" fill="{caption_color}" font-size="12" font-weight="600">{caption}</text>
    </g>""".format(
        active_class=active_class,
        node_id=_escaped(node["id"]),
        domain=_escaped(node["group"]),
        style_attr=' style="--node-active-shadow:{0}"'.format(_escaped(shadow)) if shadow else "",
        label=_escaped(node["label"]),
        caption=_escaped(node["caption"]),
        x=x,
        y=y,
        width=width,
        height=height,
        fill=fill,
        stroke=stroke,
        stroke_width="2.4" if definition is not None else "1.5",
        icon=rendered_icon,
        text_x=text_x,
        label_y=label_y,
        caption_y=caption_y,
        anchor="start" if horizontal else "middle",
        text_color=style["node_text"],
        caption_color=style["node_caption"],
    )
    return rendered, None if definition is None else _manifest_entry(node, definition, 0)


def _css_variables(style: Mapping[str, object]) -> str:
    return " ".join(
        "--{0}:{1};".format(name, value)
        for name, value in style["css_vars"].items()
    )


def _tokens_for_style(style: Mapping[str, object]) -> Mapping[str, str]:
    _, contexts = token_contexts(token_css())
    return contexts[style["icon_context"]]


def render_kubernetes_html(
    spec_path: Path,
    style_override: str | None = None,
) -> str:
    _verify_frozen_release()
    definitions = _motion_catalog(_visual_review_icons())
    spec = _load_spec(spec_path, tuple(definitions), style_override)
    style = STYLE_VARIANTS[spec["style"]]
    icon_tokens = _tokens_for_style(style)
    animated_nodes = tuple(spec["motion"]["animated_nodes"])
    animated_set = frozenset(animated_nodes)
    node_by_id = {node["id"]: node for node in spec["nodes"]}
    groups = "\n".join(_render_group(group, style) for group in spec["groups"])
    edges = "\n".join(
        _render_edge(
            edge,
            index,
            spec["motion"]["active_edge_indices"],
            spec["motion"]["labeled_edge_indices"],
            style,
            node_by_id[edge["to"]]["group"],
        )
        for index, edge in enumerate(spec["edges"])
    )
    rendered_nodes = []
    manifest_icons = []
    for node in spec["nodes"]:
        definition = definitions[node["icon"]] if node["id"] in animated_set else None
        rendered, entry = _render_node(node, icon_tokens, definition, style)
        rendered_nodes.append(rendered)
        if entry is not None:
            entry["delay"] = round(animated_nodes.index(node["id"]) * 0.16, 2)
            manifest_icons.append(entry)
    if set(node_by_id) != {node["id"] for node in spec["nodes"]}:
        raise RuntimeError("Kubernetes node lookup is inconsistent")
    manifest = {
        "version": "diagram-core-kubernetes-1",
        "mode": "ambient",
        "profile": "showcase",
        "icon_system": "diagram-core-v1",
        "diagram_core_release": "1.0.0",
        "style": spec["style"],
        "icons": manifest_icons,
        "edges": [
            {
                "from": edge["from"],
                "to": edge["to"],
                "label": edge.get("label", ""),
                "effect": edge.get("effect", "signal-dot"),
                "color_role": node_by_id[edge["to"]]["group"],
                "delay": round(index * 0.04, 2),
            }
            for index, edge in enumerate(spec["edges"])
        ],
        "groups": [{"id": group["id"], "label": group["label"]} for group in spec["groups"]],
        "stage": {
            "title_sweep": True,
            "edge_flow": True,
            "active_edge_indices": spec["motion"]["active_edge_indices"],
            "readable_edge_indices": spec["motion"]["readable_edge_indices"],
            "edge_limit": len(spec["edges"]),
            "readable_edge_limit": 2,
            "relation_circles": False,
            "group_fields": False,
        },
    }
    manifest_json = json.dumps(manifest, ensure_ascii=True, indent=2).replace("</", "<\\/")
    gsap_source = _script_source(GSAP_PATH, "pinned GSAP runtime")
    runtime_source = _script_source(RUNTIME_PATH, "AniDiagram runtime")
    title = spec["title"]
    template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="__COLOR_SCHEME__">
  <link rel="icon" href="data:,">
  <title>Kubernetes production architecture · __STYLE__ · Diagram Core v1</title>
  <style>
    * { box-sizing: border-box; }
    :root { __CSS_VARIABLES__ color: var(--root-color); background: var(--root-background); font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; min-width: 1000px; background: var(--body-background); }
    main { width: min(1560px, calc(100vw - 48px)); margin: 0 auto; padding: 30px 0 44px; }
    header { display: flex; align-items: end; justify-content: space-between; gap: 28px; margin: 0 8px 20px; }
    h1, p { margin: 0; }
    .eyebrow { margin-bottom: 8px; color: var(--eyebrow); font-size: 12px; font-weight: 850; letter-spacing: .13em; text-transform: uppercase; }
    h1 { font-size: clamp(28px, 3vw, 42px); line-height: 1; letter-spacing: -.04em; }
    .lede { max-width: 720px; margin-top: 10px; color: var(--muted); font-size: 15px; }
    .toolbar { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
    button { border: 1px solid var(--button-border); border-radius: 999px; background: var(--button-background); color: var(--button-text); padding: 9px 14px; font: inherit; font-size: 13px; font-weight: 760; cursor: pointer; }
    button:hover { border-color: var(--button-active); }
    button[aria-pressed="true"] { border-color: var(--button-active); background: var(--button-active); color: var(--button-active-text); }
    #stage { overflow: hidden; border: 1px solid var(--stage-border); border-radius: 34px; background: var(--stage-background); box-shadow: var(--stage-shadow); touch-action: none; }
    #viewport { width: 100%; aspect-ratio: 16 / 9; transform-origin: 0 0; }
    svg { display: block; width: 100%; height: 100%; }
    .architecture-node { filter: var(--node-shadow); }
    .architecture-node--animated { filter: var(--node-active-shadow); }
    .edge { pointer-events: none; }
    .legend { display: flex; justify-content: space-between; gap: 24px; margin: 15px 8px 0; color: var(--legend); font-size: 13px; }
    .legend strong { color: var(--legend-strong); }
    .motion-readable .architecture-node { filter: none; }
    .motion-off .architecture-node { filter: none; }
    .no-gsap .architecture-node { filter: none; }
    @media (prefers-reduced-motion: reduce) {
      [data-icon-presentation], [data-icon-presentation] * { animation: none !important; transition: none !important; }
      .architecture-node { filter: none; }
    }
  </style>
</head>
<body>
  <main id="viewer" class="motion-expressive" data-runtime="gsap" data-display-mode="showcase" data-template-style="__STYLE__">
    <header>
      <div>
        <p class="eyebrow">__STYLE__ · Frozen Diagram Core v1.0.0</p>
        <h1>__TITLE__</h1>
        <p class="lede">__SUBTITLE__</p>
      </div>
      <div class="toolbar" aria-label="Motion controls">
        <button type="button" id="toggle">Pause</button>
        <button type="button" id="restart">Replay</button>
        <button type="button" id="motion-expressive" class="motion-choice" data-motion="expressive" aria-pressed="true">Showcase</button>
        <button type="button" id="motion-readable" class="motion-choice" data-motion="readable" aria-pressed="false">Readable</button>
        <button type="button" id="motion-off" class="motion-choice" data-motion="off" aria-pressed="false">Off</button>
      </div>
    </header>
    <div id="stage" class="stage">
      <div id="viewport" class="viewport">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1600" height="900" role="img" aria-labelledby="architecture-title architecture-description" data-motion-profile="showcase" data-icon-system="diagram-core-v1" data-diagram-core-release="1.0.0" data-template-style="__STYLE__">
          <title id="architecture-title">__TITLE__</title>
          <desc id="architecture-description">__SUBTITLE__</desc>
          <defs>
__ARROW_MARKERS__
            <pattern id="diagram-grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M 32 0 L 0 0 0 32" fill="none" stroke="__GRID__" stroke-width="1"/></pattern>
          </defs>
          <rect width="1600" height="900" fill="__SVG_BACKGROUND__"/>
          <rect width="1600" height="900" fill="url(#diagram-grid)" opacity="__GRID_OPACITY__"/>
          <rect x="12" y="12" width="1576" height="876" rx="30" fill="none" stroke="__FRAME__" stroke-width="1.5" opacity="__FRAME_OPACITY__"/>
          <rect id="title-highlight" x="30" y="18" width="640" height="92" rx="24" fill="__TITLE_PANEL__" opacity=".72"/>
          <text x="58" y="43" fill="__TITLE_KICKER__" font-size="12" font-weight="850" letter-spacing="1.5">KUBERNETES REFERENCE · __STYLE_UPPER__</text>
          <text id="diagram-title" x="58" y="73" fill="__TITLE_TEXT__" font-size="27" font-weight="850">__TITLE__</text>
          <text id="diagram-summary" x="58" y="96" fill="__TITLE_SUMMARY__" font-size="14" font-weight="700">All nodes alive · all data paths flowing</text>
          <g transform="translate(1462 34)" aria-hidden="true"><circle cx="20" cy="20" r="18" fill="__DECOR_1__"/><circle cx="54" cy="20" r="18" fill="__DECOR_2__"/><circle cx="37" cy="50" r="18" fill="__DECOR_3__"/><circle cx="37" cy="31" r="8" fill="__DECOR_CORE__"/></g>
__GROUPS__
__EDGES__
__NODES__
        </svg>
      </div>
    </div>
    <div class="legend">
      <p><strong>Showcase:</strong> all 19 nodes + all 22 data flows. <strong>Readable:</strong> 2 core flows. <strong>Off:</strong> authored rest pose.</p>
      <p>19 nodes · 5 architecture groups · no six-state semantics</p>
    </div>
  </main>
  <script type="application/json" id="anidiagram-motion-manifest">
__MANIFEST__
  </script>
  <script>
if (!new URLSearchParams(window.location.search).has("no-gsap")) {
__GSAP__
}
if (!window.gsap) document.documentElement.classList.add("no-gsap");
  </script>
  <script>
__RUNTIME__
  </script>
</body>
</html>
"""
    replacements = {
        "__COLOR_SCHEME__": style["color_scheme"],
        "__CSS_VARIABLES__": _css_variables(style),
        "__STYLE__": spec["style"],
        "__STYLE_UPPER__": str(spec["style"]).upper(),
        "__TITLE__": _escaped(title["text"]),
        "__SUBTITLE__": _escaped(title["subtitle"]),
        "__ARROW_MARKERS__": _render_arrow_markers(style),
        "__SVG_BACKGROUND__": style["svg_background"],
        "__GRID__": style["grid"],
        "__GRID_OPACITY__": style["grid_opacity"],
        "__FRAME__": style["frame"],
        "__FRAME_OPACITY__": style["frame_opacity"],
        "__TITLE_PANEL__": style["title_panel"],
        "__TITLE_KICKER__": style["title_kicker"],
        "__TITLE_TEXT__": style["title_text"],
        "__TITLE_SUMMARY__": style["title_summary"],
        "__DECOR_1__": style["decorative"][0],
        "__DECOR_2__": style["decorative"][1],
        "__DECOR_3__": style["decorative"][2],
        "__DECOR_CORE__": style["decorative"][3],
        "__GROUPS__": groups,
        "__EDGES__": edges,
        "__NODES__": "\n".join(rendered_nodes),
        "__MANIFEST__": manifest_json,
        "__GSAP__": gsap_source,
        "__RUNTIME__": runtime_source,
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the frozen Diagram Core Kubernetes architecture.")
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--style", choices=tuple(STYLE_VARIANTS))
    arguments = parser.parse_args()
    try:
        source = render_kubernetes_html(arguments.spec, arguments.style)
        _publish(arguments.output, source)
    except (OSError, RuntimeError, ValueError) as error:
        parser.error(str(error))
    print(
        "nodes=19 animated_nodes=19 active_edges=22 readable_edges=2 "
        "icon_system=diagram-core-v1 release=1.0.0 style={0}".format(
            arguments.style or TEMPLATE_STYLE
        )
    )
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

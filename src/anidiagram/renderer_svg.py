"""SVG renderer for DiagramScript.

This module is intentionally independent from the previous forked renderer. It
uses a web-native SVG scene model and Python standard-library string rendering.
"""

from __future__ import annotations

import html
import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

from .styles import role_style


Point = Tuple[float, float]


@dataclass(frozen=True)
class NodeBox:
    node_id: str
    x: float
    y: float
    w: float
    h: float

    @property
    def center(self) -> Point:
        return (self.x + self.w / 2, self.y + self.h / 2)


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def as_float_pair(value: Iterable[Any], fallback: Point) -> Point:
    items = list(value or [])
    if len(items) != 2:
        return fallback
    return (float(items[0]), float(items[1]))


def wrap_words(text: str, max_chars: int) -> List[str]:
    words = str(text or "").split()
    if not words:
        return []
    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        if len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def node_box(node: Dict[str, Any]) -> NodeBox:
    x, y = as_float_pair(node.get("position"), (0, 0))
    w, h = as_float_pair(node.get("size"), (160, 88))
    return NodeBox(str(node.get("id", "")), x, y, w, h)


def anchor_between(source: NodeBox, target: NodeBox) -> Tuple[Point, Point]:
    sx, sy = source.center
    tx, ty = target.center
    dx = tx - sx
    dy = ty - sy
    if abs(dx) > abs(dy):
        start = (source.x + source.w if dx >= 0 else source.x, sy)
        end = (target.x if dx >= 0 else target.x + target.w, ty)
    else:
        start = (sx, source.y + source.h if dy >= 0 else source.y)
        end = (tx, target.y if dy >= 0 else target.y + target.h)
    return start, end


def curve_path(start: Point, end: Point) -> str:
    sx, sy = start
    ex, ey = end
    bend = max(40, min(180, abs(ex - sx) * 0.42))
    if abs(ex - sx) >= abs(ey - sy):
        c1 = (sx + math.copysign(bend, ex - sx), sy)
        c2 = (ex - math.copysign(bend, ex - sx), ey)
    else:
        c1 = (sx, sy + math.copysign(bend, ey - sy))
        c2 = (ex, ey - math.copysign(bend, ey - sy))
    return f"M {sx:.1f} {sy:.1f} C {c1[0]:.1f} {c1[1]:.1f}, {c2[0]:.1f} {c2[1]:.1f}, {ex:.1f} {ey:.1f}"


def render_text_block(x: float, y: float, width: float, label: str, caption: str, color: str) -> str:
    label_lines = wrap_words(label, max(8, int(width / 12)))
    caption_lines = wrap_words(caption, max(10, int(width / 9)))
    parts = [f'<text x="{x + width / 2:.1f}" y="{y:.1f}" text-anchor="middle" fill="{esc(color)}">']
    line_y = 0
    for line in label_lines[:2]:
        parts.append(f'<tspan x="{x + width / 2:.1f}" dy="{18 if line_y == 0 else 18}" class="node-title">{esc(line)}</tspan>')
        line_y += 1
    for line in caption_lines[:2]:
        parts.append(f'<tspan x="{x + width / 2:.1f}" dy="17" class="node-caption">{esc(line)}</tspan>')
    parts.append("</text>")
    return "\n".join(parts)


def render_node(node: Dict[str, Any], style: Dict[str, Any]) -> str:
    box = node_box(node)
    role = role_style(style, node.get("role"))
    radius = float(node.get("radius", style.get("node", {}).get("radius", 14)))
    stroke_width = float(node.get("stroke_width", style.get("node", {}).get("stroke_width", 2)))
    stroke = node.get("stroke", role.get("stroke", "#94a3b8"))
    fill = node.get("fill", role.get("fill", "#f8fafc"))
    text = node.get("text", role.get("text", style.get("canvas", {}).get("text", "#172033")))
    label = str(node.get("label", node.get("id", "")))
    caption = str(node.get("caption", ""))
    content_y = box.y + max(26, box.h / 2 - 14)
    return f"""
<g id="node-{esc(box.node_id)}" class="node" data-role="{esc(node.get("role", "neutral"))}">
  <rect x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" rx="{radius:.1f}"
        fill="{esc(fill)}" stroke="{esc(stroke)}" stroke-width="{stroke_width:.1f}" />
  {render_text_block(box.x + 12, content_y, box.w - 24, label, caption, text)}
  <animate attributeName="opacity" values="0.92;1;0.92" dur="3.8s" repeatCount="indefinite" />
</g>"""


def render_group(group: Dict[str, Any], style: Dict[str, Any]) -> str:
    x, y, w, h = [float(value) for value in group.get("bounds", [0, 0, 100, 100])]
    role = role_style(style, group.get("role"))
    stroke = group.get("stroke", role.get("stroke", "#94a3b8"))
    fill = group.get("fill", role.get("fill", "none"))
    label = group.get("label", group.get("id", ""))
    muted = style.get("canvas", {}).get("muted", "#5b6778")
    return f"""
<g id="group-{esc(group.get("id", ""))}" class="group">
  <rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="22"
        fill="{esc(fill)}" fill-opacity="0.34" stroke="{esc(stroke)}" stroke-width="1.6" stroke-dasharray="9 8" />
  <text x="{x + 18:.1f}" y="{y + 30:.1f}" class="group-label" fill="{esc(muted)}">{esc(label)}</text>
</g>"""


def edge_points(edge: Dict[str, Any], nodes: Dict[str, NodeBox]) -> Tuple[Point, Point]:
    if "points" in edge and len(edge["points"]) >= 2:
        return as_float_pair(edge["points"][0], (0, 0)), as_float_pair(edge["points"][-1], (0, 0))
    source = nodes.get(edge.get("from"))
    target = nodes.get(edge.get("to"))
    if not source or not target:
        return (0, 0), (0, 0)
    return anchor_between(source, target)


def render_edge(edge: Dict[str, Any], nodes: Dict[str, NodeBox], style: Dict[str, Any], index: int) -> str:
    start, end = edge_points(edge, nodes)
    path = curve_path(start, end)
    role = role_style(style, edge.get("role"))
    stroke = edge.get("stroke", role.get("stroke", "#64748b"))
    width = float(edge.get("width", style.get("edge", {}).get("width", 2.4)))
    duration = edge.get("duration", style.get("edge", {}).get("duration", "4.2s"))
    mid_x = (start[0] + end[0]) / 2
    mid_y = (start[1] + end[1]) / 2 - 14
    label = edge.get("label", "")
    marker_id = f"arrow-{index}"
    return f"""
<defs>
  <marker id="{marker_id}" markerWidth="10" markerHeight="10" refX="7" refY="3" orient="auto" markerUnits="strokeWidth">
    <path d="M 0 0 L 7 3 L 0 6 z" fill="{esc(stroke)}" />
  </marker>
</defs>
<g class="edge" data-role="{esc(edge.get("role", "neutral"))}">
  <path d="{path}" fill="none" stroke="{esc(stroke)}" stroke-width="{width:.1f}" marker-end="url(#{marker_id})" />
  <circle r="5" fill="{esc(stroke)}">
    <animateMotion dur="{esc(duration)}" repeatCount="indefinite" path="{path}" begin="{index * 0.35:.2f}s" />
  </circle>
  <text x="{mid_x:.1f}" y="{mid_y:.1f}" class="edge-label" fill="{esc(style.get("canvas", {}).get("muted", "#5b6778"))}">{esc(label)}</text>
</g>"""


def render_svg(spec: Dict[str, Any], style: Dict[str, Any]) -> str:
    canvas = spec.get("canvas", {})
    width = int(canvas.get("width", 1200))
    height = int(canvas.get("height", 720))
    canvas_style = style.get("canvas", {})
    title_style = style.get("title", {})
    background = canvas_style.get("background", "#ffffff")
    text = canvas_style.get("text", "#172033")
    muted = canvas_style.get("muted", "#5b6778")
    grid = canvas_style.get("grid", "#edf2f7")
    title = spec.get("title", {})
    title_text = title.get("text", "AniDiagram")
    subtitle = title.get("subtitle", "")
    nodes = {node.get("id"): node_box(node) for node in spec.get("nodes", []) if node.get("id")}

    groups_markup = "\n".join(render_group(group, style) for group in spec.get("groups", []))
    edges_markup = "\n".join(render_edge(edge, nodes, style, index) for index, edge in enumerate(spec.get("edges", []), start=1))
    nodes_markup = "\n".join(render_node(node, style) for node in spec.get("nodes", []))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="diagram-title diagram-desc">
<title id="diagram-title">{esc(title_text)}</title>
<desc id="diagram-desc">{esc(subtitle)}</desc>
<style>
  .title {{ font: 700 42px ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; letter-spacing: 0; }}
  .subtitle {{ font: 400 16px ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  .node-title {{ font: 700 18px ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  .node-caption {{ font: 400 13px ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; opacity: 0.84; }}
  .group-label {{ font: 700 14px ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; text-transform: uppercase; letter-spacing: 0.08em; }}
  .edge-label {{ font: 600 13px ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
</style>
<rect width="100%" height="100%" fill="{esc(background)}" />
<defs>
  <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
    <path d="M 32 0 L 0 0 0 32" fill="none" stroke="{esc(grid)}" stroke-width="1" />
  </pattern>
</defs>
<rect width="100%" height="100%" fill="url(#grid)" opacity="0.52" />
<rect x="28" y="26" width="{width - 56}" height="{height - 52}" rx="26" fill="none" stroke="{esc(style.get("roles", {}).get("neutral", {}).get("stroke", "#94a3b8"))}" stroke-width="1.4" />
<rect x="44" y="44" width="12" height="52" rx="6" fill="{esc(title_style.get("accent", "#2563eb"))}" />
<rect x="72" y="46" width="360" height="56" rx="16" fill="{esc(title_style.get("highlight", "#e8f1ff"))}" />
<text id="main-title" x="90" y="84" class="title" fill="{esc(text)}">{esc(title_text)}</text>
<text x="74" y="126" class="subtitle" fill="{esc(muted)}">{esc(subtitle)}</text>
{groups_markup}
{edges_markup}
{nodes_markup}
</svg>
"""


def render_html(svg: str, title: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    body {{ margin: 0; background: #111827; color: #f8fafc; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ min-height: 100vh; display: grid; place-items: center; padding: 24px; box-sizing: border-box; }}
    .stage {{ width: min(1200px, 100%); overflow: auto; border: 1px solid #334155; border-radius: 12px; background: #020617; }}
    svg {{ display: block; max-width: 100%; height: auto; }}
  </style>
</head>
<body>
  <main>
    <div class="stage">
{svg}
    </div>
  </main>
</body>
</html>
"""

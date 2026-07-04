"""SVG renderer for DiagramScript.

This module is intentionally independent from the previous forked renderer. It
uses a web-native SVG scene model and Python standard-library string rendering.
"""

from __future__ import annotations

import html
import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

from .model import Edge, Group, Node, Scene, SceneMotion
from .schema import compile_scene
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


def seconds(value: float) -> str:
    return f"{value:.2f}s"


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def motion_active(motion: SceneMotion, mode: str) -> bool:
    return motion.profile != "off" and motion.intensity > 0 and mode != "none"


def scaled_duration(value: float, motion: SceneMotion) -> float:
    return max(0.05, value * motion.duration_scale)


def motion_delay(index: int, motion: SceneMotion, phase: str) -> float:
    if motion.profile == "off":
        return 0.0
    phase_offsets = {"group": 0.12, "node": 0.32, "edge": 0.88, "label": 1.22}
    if motion.sequence == "simultaneous":
        return phase_offsets.get(phase, 0.0)
    if motion.sequence == "layered":
        return phase_offsets.get(phase, 0.0) + index * motion.stagger
    return index * motion.stagger + phase_offsets.get(phase, 0.0) * 0.4


def node_translate_values(motion: SceneMotion, index: int) -> str:
    intensity = clamp(motion.intensity, 0.0, 1.8)
    if motion.node == "pop":
        rise = 8 * intensity
        overshoot = 4 * intensity
        drift = 3 * intensity
        return f"0 {rise:.1f};0 {-overshoot:.1f};0 0;0 {-drift:.1f};0 0;0 {max(1.0, drift - 1):.1f};0 0"
    if motion.node == "float":
        drift = 2.5 * intensity
        return f"0 0;0 {-drift:.1f};0 0;0 {drift * 0.7:.1f};0 0"
    drift = 3 * intensity
    return f"0 0;0 {-drift:.1f};0 0;0 {drift * 0.65:.1f};0 0"


def svg_fragment_id(value: Any) -> str:
    text = str(value or "item").lower()
    cleaned = "".join(char if char.isalnum() else "-" for char in text).strip("-")
    return cleaned or "item"


def style_effect(style: Dict[str, Any], key: str, default: Any) -> Any:
    effects = style.get("effects", {})
    if isinstance(effects, dict) and key in effects:
        return effects[key]
    return default


def aurora_nodes_enabled(style: Dict[str, Any]) -> bool:
    node_style = style.get("node", {})
    return node_style.get("fill_mode") == "aurora" or style_effect(style, "node_fill", "") == "aurora"


def role_gradient_id(role: str) -> str:
    return f"aurora-node-{svg_fragment_id(role)}"


def role_gradient_stops(tokens: Dict[str, Any]) -> List[Dict[str, Any]]:
    stops = tokens.get("gradient")
    if isinstance(stops, list) and stops:
        result = []
        for index, stop in enumerate(stops):
            offset = f"{round(index * 100 / max(1, len(stops) - 1))}%"
            if isinstance(stop, str):
                result.append({"offset": offset, "color": stop})
            elif isinstance(stop, dict) and isinstance(stop.get("color"), str):
                result.append({"offset": str(stop.get("offset", offset)), "color": stop["color"], "opacity": stop.get("opacity")})
        if result:
            return result
    return [
        {"offset": "0%", "color": tokens.get("fill", "#ffffff")},
        {"offset": "48%", "color": "#ffffff", "opacity": 0.62},
        {"offset": "100%", "color": tokens.get("stroke", "#94a3b8")},
    ]


def render_style_defs(style: Dict[str, Any], grid: str) -> str:
    parts = [
        """  <filter id="soft-glow" x="-40%" y="-40%" width="180%" height="180%">
    <feGaussianBlur stdDeviation="5" result="blur" />
    <feMerge>
      <feMergeNode in="blur" />
      <feMergeNode in="SourceGraphic" />
    </feMerge>
  </filter>""",
        """  <filter id="particle-glow" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="2.6" result="blur" />
    <feMerge>
      <feMergeNode in="blur" />
      <feMergeNode in="SourceGraphic" />
    </feMerge>
  </filter>""",
        f"""  <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
    <path d="M 32 0 L 0 0 0 32" fill="none" stroke="{esc(grid)}" stroke-width="1" />
  </pattern>""",
    ]
    if aurora_nodes_enabled(style):
        parts.extend(
            [
                """  <filter id="aurora-blur" x="-35%" y="-35%" width="170%" height="170%">
    <feGaussianBlur stdDeviation="12" />
  </filter>""",
                """  <filter id="grain-texture" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.92" numOctaves="2" seed="11" result="noise" />
    <feColorMatrix in="noise" type="matrix" values="0 0 0 0 0.18 0 0 0 0 0.16 0 0 0 0 0.14 0 0 0 0.42 0" />
  </filter>""",
            ]
        )
        for role_name, tokens in style.get("roles", {}).items():
            stops = "\n".join(
                f'      <stop offset="{esc(stop["offset"])}" stop-color="{esc(stop["color"])}"'
                + (f' stop-opacity="{float(stop["opacity"]):.2f}"' if stop.get("opacity") is not None else "")
                + " />"
                for stop in role_gradient_stops(tokens)
            )
            parts.append(
                f"""  <linearGradient id="{role_gradient_id(role_name)}" x1="0%" y1="0%" x2="100%" y2="100%">
{stops}
  </linearGradient>"""
            )
    return "<defs>\n" + "\n".join(parts) + "\n</defs>"


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


def node_box(node: Node) -> NodeBox:
    x, y = node.position
    w, h = node.size
    return NodeBox(node.node_id, x, y, w, h)


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


def render_step_badge(x: float, y: float, value: int, fill: str, text: str) -> str:
    return f"""
  <circle cx="{x:.1f}" cy="{y:.1f}" r="14" fill="{esc(fill)}" />
  <text x="{x:.1f}" y="{y + 5:.1f}" class="step-label" fill="{esc(text)}" text-anchor="middle">{value}</text>"""


def render_node_burst(box: NodeBox, role: str, stroke: str, index: int, motion: SceneMotion) -> str:
    if role not in {"agent", "output", "risk"} or not motion_active(motion, motion.node) or motion.node not in {"glow-breathe", "pop"}:
        return ""
    cx, cy = box.center
    intensity = clamp(motion.intensity, 0.2, 1.8)
    delay = motion_delay(index, motion, "node") + 0.45
    first_opacity = 0.28 * intensity
    second_opacity = 0.18 * intensity
    first_radius = max(box.w, box.h) * (0.62 + intensity * 0.1)
    second_radius = max(box.w, box.h) * (0.72 + intensity * 0.12)
    return f"""
  <circle class="node-burst" cx="{cx:.1f}" cy="{cy:.1f}" r="{max(box.w, box.h) / 2:.1f}" fill="none"
          stroke="{esc(stroke)}" stroke-width="1.6" opacity="0">
    <animate attributeName="r" values="{max(box.w, box.h) / 2:.1f};{first_radius:.1f}" dur="{seconds(scaled_duration(3.4, motion))}" begin="{seconds(delay)}" repeatCount="indefinite" />
    <animate attributeName="opacity" values="0;{first_opacity:.2f};0" dur="{seconds(scaled_duration(3.4, motion))}" begin="{seconds(delay)}" repeatCount="indefinite" />
  </circle>
  <circle class="node-burst" cx="{cx:.1f}" cy="{cy:.1f}" r="{max(box.w, box.h) / 2:.1f}" fill="none"
          stroke="{esc(stroke)}" stroke-width="1" opacity="0">
    <animate attributeName="r" values="{max(box.w, box.h) / 2:.1f};{second_radius:.1f}" dur="{seconds(scaled_duration(4.6, motion))}" begin="{seconds(delay + 0.9)}" repeatCount="indefinite" />
    <animate attributeName="opacity" values="0;{second_opacity:.2f};0" dur="{seconds(scaled_duration(4.6, motion))}" begin="{seconds(delay + 0.9)}" repeatCount="indefinite" />
  </circle>"""


def render_node_surface(
    node: Node,
    box: NodeBox,
    radius: float,
    fill: str,
    stroke: str,
    stroke_width: float,
    style: Dict[str, Any],
    index: int,
) -> str:
    if not aurora_nodes_enabled(style) or node.fill:
        return f"""  <rect x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" rx="{radius:.1f}"
        fill="{esc(fill)}" stroke="{esc(stroke)}" stroke-width="{stroke_width:.1f}" />"""
    role = role_style(style, node.role)
    clip_id = f"clip-{svg_fragment_id(box.node_id)}"
    gradient_id = role_gradient_id(node.role or "neutral")
    grain_opacity = float(style_effect(style, "grain_opacity", 0.12))
    blob_opacity = float(style_effect(style, "blob_opacity", 0.24))
    band_opacity = float(style_effect(style, "band_opacity", 0.34))
    border_opacity = float(style_effect(style, "node_border_opacity", 0.74))
    glow_color = role.get("glow", role.get("fill", "#ffffff"))
    band_color = role.get("band", role.get("stroke", "#94a3b8"))
    shadow_color = role.get("shadow", role.get("stroke", "#94a3b8"))
    wave_y = box.y + box.h * (0.56 + (index % 3) * 0.04)
    return f"""  <defs>
    <clipPath id="{clip_id}">
      <rect x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" rx="{radius:.1f}" />
    </clipPath>
  </defs>
  <g clip-path="url(#{clip_id})">
    <rect x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" rx="{radius:.1f}"
          fill="url(#{gradient_id})" />
    <ellipse cx="{box.x + box.w * 0.20:.1f}" cy="{box.y + box.h * 0.22:.1f}" rx="{box.w * 0.58:.1f}" ry="{box.h * 0.48:.1f}"
          fill="{esc(glow_color)}" opacity="{blob_opacity:.2f}" filter="url(#aurora-blur)" />
    <ellipse cx="{box.x + box.w * 0.88:.1f}" cy="{box.y + box.h * 0.90:.1f}" rx="{box.w * 0.62:.1f}" ry="{box.h * 0.54:.1f}"
          fill="{esc(shadow_color)}" opacity="{blob_opacity * 0.72:.2f}" filter="url(#aurora-blur)" />
    <path d="M {box.x - box.w * 0.12:.1f} {wave_y:.1f}
             C {box.x + box.w * 0.22:.1f} {box.y + box.h * 0.18:.1f},
               {box.x + box.w * 0.62:.1f} {box.y + box.h * 0.92:.1f},
               {box.x + box.w * 1.15:.1f} {box.y + box.h * 0.34:.1f}"
          fill="none" stroke="{esc(band_color)}" stroke-width="{max(22, box.h * 0.34):.1f}" stroke-linecap="round"
          opacity="{band_opacity:.2f}" filter="url(#aurora-blur)" />
    <rect x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" rx="{radius:.1f}"
          fill="#ffffff" opacity="{grain_opacity:.2f}" filter="url(#grain-texture)" />
  </g>
  <rect x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" rx="{radius:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="{stroke_width:.1f}" opacity="{border_opacity:.2f}" />"""


def render_node(node: Node, style: Dict[str, Any], index: int, motion: SceneMotion) -> str:
    box = node_box(node)
    role = role_style(style, node.role)
    radius = float(node.radius if node.radius is not None else style.get("node", {}).get("radius", 14))
    stroke_width = float(
        node.stroke_width if node.stroke_width is not None else style.get("node", {}).get("stroke_width", 2)
    )
    stroke = node.stroke or role.get("stroke", "#94a3b8")
    fill = node.fill or role.get("fill", "#f8fafc")
    text = role.get("text", style.get("canvas", {}).get("text", "#172033"))
    label = node.label
    caption = node.caption
    content_y = box.y + max(26, box.h / 2 - 14)
    badge = ""
    if node.step is not None:
        badge = render_step_badge(box.x + 18, box.y + 18, node.step, stroke, fill)
    delay = motion_delay(index, motion, "node")
    float_duration = scaled_duration(5.4 + (index % 3) * 0.45, motion)
    burst = render_node_burst(box, node.role, stroke, index, motion)
    enter_markup = ""
    float_markup = ""
    glow_markup = ""
    if motion_active(motion, motion.node):
        enter_markup = f'  <animate attributeName="opacity" values="0;1" dur="{seconds(scaled_duration(0.55, motion))}" begin="{seconds(delay)}" fill="freeze" />'
        if motion.node in {"float", "glow-breathe", "pop"}:
            float_markup = f"""  <animateTransform attributeName="transform" type="translate"
        values="{node_translate_values(motion, index)}" dur="{seconds(float_duration)}" begin="{seconds(delay + 0.7)}"
        repeatCount="indefinite" additive="sum" />"""
        if motion.node in {"glow-breathe", "pop"}:
            glow_opacity = 0.24 * clamp(motion.intensity, 0.25, 1.7)
            glow_markup = f"""  <rect class="node-glow" x="{box.x - 4:.1f}" y="{box.y - 4:.1f}" width="{box.w + 8:.1f}" height="{box.h + 8:.1f}" rx="{radius + 4:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="1.2" opacity="0.12" filter="url(#soft-glow)">
    <animate attributeName="opacity" values="0.08;{glow_opacity:.2f};0.08" dur="{seconds(scaled_duration(3.9 + (index % 4) * 0.35, motion))}" begin="{seconds(delay + 0.2)}" repeatCount="indefinite" />
    <animate attributeName="stroke-width" values="1.0;{1.0 + 1.4 * clamp(motion.intensity, 0.25, 1.7):.1f};1.0" dur="{seconds(scaled_duration(3.9 + (index % 4) * 0.35, motion))}" begin="{seconds(delay + 0.2)}" repeatCount="indefinite" />
  </rect>"""
    else:
        enter_markup = '  <set attributeName="opacity" to="1" />'
    return f"""
<g id="node-{esc(box.node_id)}" class="node motion-node" data-role="{esc(node.role)}" opacity="0">
{enter_markup}
{float_markup}
{burst}
{glow_markup}
{render_node_surface(node, box, radius, fill, stroke, stroke_width, style, index)}
{badge}
  {render_text_block(box.x + 12, content_y, box.w - 24, label, caption, text)}
</g>"""


def render_group(group: Group, style: Dict[str, Any], index: int, motion: SceneMotion) -> str:
    x, y, w, h = group.bounds
    role = role_style(style, group.role)
    stroke = group.stroke or role.get("stroke", "#94a3b8")
    fill = group.fill or role.get("fill", "none")
    label = group.label
    muted = style.get("canvas", {}).get("muted", "#5b6778")
    delay = motion_delay(index, motion, "group")
    enter_markup = '<set attributeName="opacity" to="1" />'
    dash_markup = ""
    if motion_active(motion, motion.group):
        enter_markup = f'<animate attributeName="opacity" values="0;1" dur="{seconds(scaled_duration(0.7, motion))}" begin="{seconds(delay)}" fill="freeze" />'
        if motion.group == "marching-ants":
            dash_markup = f'<animate attributeName="stroke-dashoffset" values="0;-34" dur="{seconds(scaled_duration(5.2 + index * 0.4, motion))}" begin="{seconds(delay)}" repeatCount="indefinite" />'
    return f"""
<g id="group-{esc(group.group_id)}" class="group" opacity="0">
  {enter_markup}
  <rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="22"
        fill="{esc(fill)}" fill-opacity="0.34" stroke="{esc(stroke)}" stroke-width="1.6" stroke-dasharray="9 8">
    {dash_markup}
  </rect>
  <text x="{x + 18:.1f}" y="{y + 30:.1f}" class="group-label" fill="{esc(muted)}">{esc(label)}</text>
</g>"""


def edge_points(edge: Edge, nodes: Dict[str, NodeBox]) -> Tuple[Point, Point]:
    if len(edge.points) >= 2:
        return edge.points[0], edge.points[-1]
    source = nodes.get(edge.source)
    target = nodes.get(edge.target)
    if not source or not target:
        return (0, 0), (0, 0)
    return anchor_between(source, target)


def route_points(edge: Edge, nodes: Dict[str, NodeBox]) -> List[Point]:
    if len(edge.points) >= 2:
        return compact_points(list(edge.points))
    start, end = edge_points(edge, nodes)
    sx, sy = start
    ex, ey = end
    if edge.route == "hv":
        return compact_points([start, (ex, sy), end])
    if edge.route == "vh":
        return compact_points([start, (sx, ey), end])
    if edge.route == "orthogonal":
        if abs(ex - sx) >= abs(ey - sy):
            mx = (sx + ex) / 2
            return compact_points([start, (mx, sy), (mx, ey), end])
        my = (sy + ey) / 2
        return compact_points([start, (sx, my), (ex, my), end])
    return [start, end]


def compact_points(points: List[Point]) -> List[Point]:
    compacted: List[Point] = []
    for point in points:
        if compacted and compacted[-1] == point:
            continue
        compacted.append(point)
    return compacted


def line_path(points: Iterable[Point]) -> str:
    items = list(points)
    first = items[0]
    rest = " ".join(f"L {x:.1f} {y:.1f}" for x, y in items[1:])
    return f"M {first[0]:.1f} {first[1]:.1f} {rest}".strip()


def edge_path(edge: Edge, nodes: Dict[str, NodeBox]) -> str:
    if edge.route != "curved" or len(edge.points) >= 2:
        return line_path(route_points(edge, nodes))
    start, end = edge_points(edge, nodes)
    return curve_path(start, end)


def render_edge(edge: Edge, nodes: Dict[str, NodeBox], style: Dict[str, Any], index: int, motion: SceneMotion) -> str:
    start, end = edge_points(edge, nodes)
    path = edge_path(edge, nodes)
    role = role_style(style, edge.role)
    stroke = edge.stroke or role.get("stroke", "#64748b")
    width = float(edge.width if edge.width is not None else style.get("edge", {}).get("width", 2.4))
    duration = edge.motion.duration or style.get("edge", {}).get("duration", "4.2s")
    try:
        duration_value = float(str(duration).rstrip("s"))
    except ValueError:
        duration_value = 4.2
    mid_x = (start[0] + end[0]) / 2
    mid_y = (start[1] + end[1]) / 2 - 14
    label = edge.label
    marker_id = f"arrow-{index}"
    draw_begin = motion_delay(index, motion, "edge") + edge.motion.delay
    badge = ""
    if edge.step is not None:
        badge = render_step_badge(mid_x - 22, mid_y - 5, edge.step, stroke, "#ffffff")
    edge_mode = motion.edge if edge.motion.enabled else "none"
    edge_is_active = motion_active(motion, edge_mode)
    draw_markup = f"""  <path class="edge-draw" d="{path}" fill="none" stroke="{esc(stroke)}" stroke-width="{width:.1f}" pathLength="1"
        stroke-dasharray="1" stroke-dashoffset="0" marker-end="url(#{marker_id})" />"""
    flow_markup = ""
    motion_markup = ""
    if edge_is_active and edge_mode in {"draw", "pulse", "trace", "comet-flow"}:
        draw_markup = f"""  <path class="edge-draw" d="{path}" fill="none" stroke="{esc(stroke)}" stroke-width="{width:.1f}" pathLength="1"
        stroke-dasharray="1" stroke-dashoffset="1" marker-end="url(#{marker_id})">
    <animate attributeName="stroke-dashoffset" values="1;0" dur="{seconds(scaled_duration(0.9, motion))}" begin="{seconds(draw_begin)}" fill="freeze" />
  </path>"""
    if edge_is_active and edge_mode in {"pulse", "trace", "comet-flow"}:
        dash = "4 22" if edge_mode == "trace" else "9 18"
        opacity = 0.42 if edge_mode == "trace" else 0.55
        flow_markup = f"""  <path class="edge-flow edge-flow-{esc(edge_mode)}" d="{path}" fill="none" stroke="{esc(stroke)}" stroke-width="{max(1, width * 0.72):.1f}"
        stroke-dasharray="{dash}" opacity="{opacity:.2f}">
    <animate attributeName="stroke-dashoffset" values="0;-54" dur="{seconds(scaled_duration(max(1.8, duration_value * 0.72), motion))}" begin="{seconds(draw_begin + 0.2)}" repeatCount="indefinite" />
    <animate attributeName="opacity" values="{opacity * 0.45:.2f};{opacity:.2f};{opacity * 0.45:.2f}" dur="{seconds(scaled_duration(max(1.8, duration_value * 0.72), motion))}" begin="{seconds(draw_begin + 0.2)}" repeatCount="indefinite" />
  </path>"""
    if edge_is_active and edge_mode == "comet-flow":
        particles = []
        intensity = clamp(motion.intensity, 0.25, 1.8)
        for particle_index, radius in enumerate((5.5, 3.5, 2.4)):
            begin = index * 0.32 + edge.motion.delay + particle_index * (duration_value / 3)
            opacity = 0.92 - particle_index * 0.18
            particles.append(
                f"""  <circle class="edge-particle" r="{radius * intensity:.1f}" fill="{esc(stroke)}" opacity="{opacity:.2f}">
    <animateMotion dur="{seconds(scaled_duration(duration_value, motion))}" repeatCount="indefinite" path="{path}" begin="{seconds(begin)}" />
    <animate attributeName="opacity" values="0;{opacity:.2f};0" dur="{seconds(scaled_duration(duration_value, motion))}" begin="{seconds(begin)}" repeatCount="indefinite" />
  </circle>"""
            )
        motion_markup = "\n".join(particles)
    label_opacity = "1" if not edge_is_active else "0"
    label_motion = ""
    if edge_is_active:
        label_motion = f'<animate attributeName="opacity" values="0;1" dur="{seconds(scaled_duration(0.45, motion))}" begin="{seconds(motion_delay(index, motion, "label") + edge.motion.delay)}" fill="freeze" />'
    return f"""
<defs>
  <marker id="{marker_id}" markerWidth="10" markerHeight="10" refX="7" refY="3" orient="auto" markerUnits="strokeWidth">
    <path d="M 0 0 L 7 3 L 0 6 z" fill="{esc(stroke)}" />
  </marker>
</defs>
<g class="edge" data-role="{esc(edge.role)}">
  <path class="edge-base" d="{path}" fill="none" stroke="{esc(stroke)}" stroke-width="{max(1, width - 0.7):.1f}" opacity="0.24" marker-end="url(#{marker_id})" />
{draw_markup}
{flow_markup}
{motion_markup}
{badge}
  <text x="{mid_x:.1f}" y="{mid_y:.1f}" class="edge-label" fill="{esc(style.get("canvas", {}).get("muted", "#5b6778"))}" opacity="{label_opacity}">
    {label_motion}
    {esc(label)}
  </text>
</g>"""


def render_svg(spec: Any, style: Dict[str, Any]) -> str:
    scene = spec if isinstance(spec, Scene) else compile_scene(spec)
    width = scene.canvas.width
    height = scene.canvas.height
    canvas_style = style.get("canvas", {})
    title_style = style.get("title", {})
    background = canvas_style.get("background", "#ffffff")
    text = canvas_style.get("text", "#172033")
    muted = canvas_style.get("muted", "#5b6778")
    grid = canvas_style.get("grid", "#edf2f7")
    title_text = scene.title.text
    subtitle = scene.title.subtitle
    nodes = {node.node_id: node_box(node) for node in scene.nodes}
    motion = scene.motion

    groups_markup = "\n".join(render_group(group, style, index, motion) for index, group in enumerate(scene.groups, start=1))
    edges_markup = "\n".join(render_edge(edge, nodes, style, index, motion) for index, edge in enumerate(scene.edges, start=1))
    nodes_markup = "\n".join(render_node(node, style, index, motion) for index, node in enumerate(scene.nodes, start=1))
    defs_markup = render_style_defs(style, grid)
    grid_opacity = float(style_effect(style, "grid_opacity", 0.52))
    frame_opacity = float(style_effect(style, "frame_opacity", 1.0))

    title_style_attr = ' style="animation:none"' if motion.profile == "off" else ""
    title_text_opacity = "1" if motion.profile == "off" else "0"
    title_text_anim = "" if motion.profile == "off" else '<animate attributeName="opacity" values="0;1" dur="0.65s" begin="0.08s" fill="freeze" />'
    subtitle_anim = "" if motion.profile == "off" else '<animate attributeName="opacity" values="0;1" dur="0.65s" begin="0.28s" fill="freeze" />'

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="diagram-title diagram-desc" data-motion-profile="{esc(motion.profile)}" data-motion-sequence="{esc(motion.sequence)}" data-motion-edge="{esc(motion.edge)}" data-motion-node="{esc(motion.node)}" data-motion-group="{esc(motion.group)}" data-motion-reduced="{esc(motion.reduced_motion)}">
<title id="diagram-title">{esc(title_text)}</title>
<desc id="diagram-desc">{esc(subtitle)}</desc>
<style>
  .title {{ font: 700 42px ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; letter-spacing: 0; }}
  .subtitle {{ font: 400 16px ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  .node-title {{ font: 700 18px ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  .node-caption {{ font: 400 13px ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; opacity: 0.84; }}
  .group-label {{ font: 700 14px ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; text-transform: uppercase; letter-spacing: 0.08em; }}
  .edge-label {{ font: 600 13px ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  .step-label {{ font: 700 12px ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  .edge-flow {{ stroke-linecap: round; }}
  .edge-draw, .edge-base {{ stroke-linecap: round; stroke-linejoin: round; }}
  .edge-particle {{ filter: url(#particle-glow); }}
  .node-glow, .node-burst {{ pointer-events: none; }}
  #title-accent {{ transform-origin: 50px 70px; animation: titlePulse 4.8s ease-in-out infinite; }}
  #title-highlight {{ transform-origin: 252px 74px; animation: titleSlide 5.6s ease-in-out infinite; }}
  @keyframes titlePulse {{ 0%, 100% {{ opacity: 0.76; }} 50% {{ opacity: 1; }} }}
  @keyframes titleSlide {{ 0%, 100% {{ transform: translateX(0); opacity: 0.9; }} 50% {{ transform: translateX(8px); opacity: 1; }} }}
  @media (prefers-reduced-motion: reduce) {{
    #title-accent, #title-highlight {{ animation: none; }}
  }}
</style>
<rect width="100%" height="100%" fill="{esc(background)}" />
{defs_markup}
<rect width="100%" height="100%" fill="url(#grid)" opacity="{grid_opacity:.2f}" />
<rect x="28" y="26" width="{width - 56}" height="{height - 52}" rx="26" fill="none" stroke="{esc(style.get("roles", {}).get("neutral", {}).get("stroke", "#94a3b8"))}" stroke-width="1.4" opacity="{frame_opacity:.2f}" />
<rect id="title-accent" x="44" y="44" width="12" height="52" rx="6" fill="{esc(title_style.get("accent", "#2563eb"))}"{title_style_attr} />
<rect id="title-highlight" x="72" y="46" width="360" height="56" rx="16" fill="{esc(title_style.get("highlight", "#e8f1ff"))}"{title_style_attr} />
<text id="main-title" x="90" y="84" class="title" fill="{esc(text)}" opacity="{title_text_opacity}">
  {title_text_anim}
  {esc(title_text)}
</text>
<text x="74" y="126" class="subtitle" fill="{esc(muted)}" opacity="{title_text_opacity}">
  {subtitle_anim}
  {esc(subtitle)}
</text>
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
    main {{ min-height: 100vh; display: grid; grid-template-rows: auto 1fr; gap: 12px; padding: 16px; box-sizing: border-box; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
    button, a {{ border: 1px solid #475569; background: #1f2937; color: #f8fafc; border-radius: 8px; padding: 8px 10px; font: inherit; text-decoration: none; cursor: pointer; }}
    button:hover, a:hover {{ background: #334155; }}
    button[aria-pressed="true"] {{ background: #475569; border-color: #94a3b8; }}
    .stage {{ width: 100%; min-height: 0; overflow: hidden; border: 1px solid #334155; border-radius: 12px; background: #020617; cursor: grab; }}
    .stage.dragging {{ cursor: grabbing; }}
    .viewport {{ transform-origin: 0 0; width: max-content; }}
    svg {{ display: block; max-width: none; height: auto; user-select: none; }}
    main.motion-subtle .edge-particle,
    main.motion-subtle .node-burst {{ display: none; }}
    main.motion-subtle .edge-flow {{ opacity: 0.22; }}
    main.motion-off .edge-flow,
    main.motion-off .edge-particle,
    main.motion-off .node-burst,
    main.motion-off .node-glow {{ display: none; }}
  </style>
</head>
<body>
  <main id="viewer" class="motion-full">
    <div class="toolbar">
      <button type="button" id="toggle">Pause</button>
      <button type="button" id="restart">Restart</button>
      <button type="button" class="motion-choice" data-motion="full" aria-pressed="true">Full Motion</button>
      <button type="button" class="motion-choice" data-motion="subtle" aria-pressed="false">Subtle</button>
      <button type="button" class="motion-choice" data-motion="off" aria-pressed="false">Off</button>
      <button type="button" id="zoom-in">Zoom In</button>
      <button type="button" id="zoom-out">Zoom Out</button>
      <button type="button" id="reset">Reset</button>
      <a id="download" download="{esc(title)}.svg">Download SVG</a>
    </div>
    <div class="stage" id="stage">
      <div class="viewport" id="viewport">
{svg}
      </div>
    </div>
  </main>
  <script>
    const stage = document.getElementById('stage');
    const viewer = document.getElementById('viewer');
    const viewport = document.getElementById('viewport');
    const svg = viewport.querySelector('svg');
    const download = document.getElementById('download');
    let scale = 1;
    let x = 0;
    let y = 0;
    let dragging = false;
    let lastX = 0;
    let lastY = 0;
    function applyTransform() {{
      viewport.style.transform = `translate(${{x}}px, ${{y}}px) scale(${{scale}})`;
    }}
    function setDownload() {{
      const blob = new Blob([new XMLSerializer().serializeToString(svg)], {{type: 'image/svg+xml'}});
      download.href = URL.createObjectURL(blob);
    }}
    document.getElementById('toggle').addEventListener('click', (event) => {{
      if (svg.animationsPaused && svg.animationsPaused()) {{
        svg.unpauseAnimations();
        event.currentTarget.textContent = 'Pause';
      }} else {{
        svg.pauseAnimations();
        event.currentTarget.textContent = 'Play';
      }}
    }});
    document.getElementById('restart').addEventListener('click', () => {{
      svg.setCurrentTime(0);
      svg.unpauseAnimations();
      document.getElementById('toggle').textContent = 'Pause';
    }});
    function setMotionMode(mode) {{
      viewer.classList.remove('motion-full', 'motion-subtle', 'motion-off');
      viewer.classList.add(`motion-${{mode}}`);
      document.querySelectorAll('.motion-choice').forEach((button) => {{
        button.setAttribute('aria-pressed', String(button.dataset.motion === mode));
      }});
      if (mode === 'off') {{
        svg.pauseAnimations();
        document.getElementById('toggle').textContent = 'Play';
      }} else {{
        svg.unpauseAnimations();
        document.getElementById('toggle').textContent = 'Pause';
      }}
    }}
    document.querySelectorAll('.motion-choice').forEach((button) => {{
      button.addEventListener('click', () => setMotionMode(button.dataset.motion));
    }});
    document.getElementById('zoom-in').addEventListener('click', () => {{ scale = Math.min(3, scale + 0.15); applyTransform(); }});
    document.getElementById('zoom-out').addEventListener('click', () => {{ scale = Math.max(0.35, scale - 0.15); applyTransform(); }});
    document.getElementById('reset').addEventListener('click', () => {{ scale = 1; x = 0; y = 0; applyTransform(); }});
    stage.addEventListener('pointerdown', (event) => {{ dragging = true; stage.classList.add('dragging'); lastX = event.clientX; lastY = event.clientY; stage.setPointerCapture(event.pointerId); }});
    stage.addEventListener('pointermove', (event) => {{
      if (!dragging) return;
      x += event.clientX - lastX;
      y += event.clientY - lastY;
      lastX = event.clientX;
      lastY = event.clientY;
      applyTransform();
    }});
    stage.addEventListener('pointerup', () => {{ dragging = false; stage.classList.remove('dragging'); }});
    setDownload();
    if (svg.dataset.motionProfile === 'off') {{
      setMotionMode('off');
    }} else if (svg.dataset.motionProfile === 'subtle') {{
      setMotionMode('subtle');
    }}
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {{
      const reduced = svg.dataset.motionReduced || 'subtle';
      setMotionMode(reduced === 'pause' || reduced === 'static' ? 'off' : 'subtle');
    }}
  </script>
</body>
</html>
"""

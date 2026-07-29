"""SVG renderer for DiagramScript.

This module is intentionally independent from the previous forked renderer. It
uses a web-native SVG scene model and Python standard-library string rendering.
"""

from __future__ import annotations

import html
import math
from dataclasses import dataclass, replace
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .effects import canonical_edge_effect, channel_effect, effect_active
from .edge_motion import CONTINUOUS_EDGE_MOTION, DRAW_ENTRY_EDGE_MOTION, PARTICLE_EDGE_MOTION
from .diagram_core.adapter import render_approved_icon
from .diagram_core.tokens import icon_tokens_for_style
from .illustrated_icons import illustrated_definition as legacy_illustrated_definition, illustrated_palette, is_illustrated_style
from .illustrated_character_icons import character_definition
from .illustrated_registry import illustrated_definition
from .illustrated_tokens import illustrated_tokens_for_style
from .model import Edge, EffectConfig, Group, MotionPolicy, Node, Scene, SceneMotion
from .motion_manifest import icon_part_id
from .renderer_illustrated_character import render_character_icon
from .renderer_illustrated_character_v2 import render_character_v2_icon
from .schema import compile_scene
from .styles import deep_merge, role_style
from .icon_system import icon_system_version, resolve_icon_system
from .text_layout import fitted_text_length, node_text_region, text_block_layout, wrap_text


Point = Tuple[float, float]
EDGE_NODE_GAP = 12.0

CONTINUOUS_NODE_MOTION = {
    "float",
    "glow-breathe",
    "pop",
    "pulse",
    "ripple",
    "status-blink",
    "icon-pulse",
    "icon-breathe",
    "icon-semantic",
    "icon-performance",
    "micro-icon",
}
SCANNING_GROUP_MOTION = {"marching-ants", "border-scan", "corner-pulse"}
BREATHING_NODE_MOTION = {"icon-breathe", "micro-icon"}


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


def policy_allows(rank: Optional[int], limit: Optional[int]) -> bool:
    return rank is None or limit is None or rank <= limit


def effect_with_preset(effect: EffectConfig, preset: str) -> EffectConfig:
    return EffectConfig(
        preset=preset,
        line=effect.line,
        particle=effect.particle,
        trail=effect.trail,
        particle_count=effect.particle_count,
        trail_count=effect.trail_count,
        entry=effect.entry,
        accent=effect.accent,
        icon=effect.icon,
        icon_motion=effect.icon_motion,
    )


def ranked_motion_modes(
    items: Iterable[Tuple[int, EffectConfig, str]],
    motion: SceneMotion,
    allowed: set[str],
) -> Dict[int, int]:
    ranks: Dict[int, int] = {}
    rank = 0
    for index, effect, mode in items:
        if effect_active(motion, effect) and mode in allowed:
            rank += 1
            ranks[index] = rank
    return ranks


def particle_radii(edge_mode: str, particle_shape: str, effect: EffectConfig, policy: MotionPolicy) -> Tuple[float, ...]:
    if edge_mode == "comet-flow":
        radii = (5.8, 4.2, 3.0, 2.0)
        trail_count = effect.trail_count if effect.trail_count is not None else 3
        return radii[: 1 + max(0, min(3, trail_count))]
    base = (5.5,)
    default_count = 1
    count = effect.particle_count if effect.particle_count is not None else policy.particle_count_per_edge
    if count is None:
        count = default_count
    cap = effect.trail_count if effect.trail_count is not None else policy.flow_trail_count
    if cap is not None and cap > 0:
        count = min(count, cap)
    return base[: max(0, min(len(base), count))]


def motion_area_scale(policy: MotionPolicy) -> float:
    if policy.motion_area == "micro":
        return 0.86
    if policy.motion_area == "small":
        return 0.86
    if policy.motion_area == "medium":
        return 1.0
    return 1.0


def runtime_loop_active(motion: SceneMotion) -> bool:
    return motion.profile == "runtime-loop" or motion.sequence == "loop"


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


def node_translate_values(motion: SceneMotion, index: int, mode: Optional[str] = None) -> str:
    intensity = clamp(motion.intensity, 0.0, 1.8)
    node_mode = mode or motion.node
    if node_mode in {"pop", "icon-pulse"}:
        rise = 8 * intensity
        overshoot = 4 * intensity
        drift = 3 * intensity
        return f"0 {rise:.1f};0 {-overshoot:.1f};0 0;0 {-drift:.1f};0 0;0 {max(1.0, drift - 1):.1f};0 0"
    if node_mode == "float":
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


def parse_hex_color(value: str) -> Optional[Tuple[int, int, int]]:
    text = str(value or "").strip()
    if not text.startswith("#"):
        return None
    raw = text[1:]
    if len(raw) == 3:
        raw = "".join(char * 2 for char in raw)
    if len(raw) != 6 or any(char not in "0123456789abcdefABCDEF" for char in raw):
        return None
    return (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return "#" + "".join(f"{int(clamp(channel, 0, 255)):02x}" for channel in rgb)


def mix_rgb(base: Tuple[int, int, int], overlay: Tuple[int, int, int], amount: float) -> Tuple[int, int, int]:
    ratio = clamp(amount, 0.0, 1.0)
    return tuple(round(base[index] * (1 - ratio) + overlay[index] * ratio) for index in range(3))  # type: ignore[return-value]


def color_luminance(rgb: Tuple[int, int, int]) -> float:
    return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255


def icon_surface_fill(background: str, stroke: str) -> str:
    bg = parse_hex_color(background)
    accent = parse_hex_color(stroke)
    if bg is None:
        return "#ffffff"
    if color_luminance(bg) < 0.42:
        if accent is not None:
            return rgb_to_hex(mix_rgb(bg, accent, 0.22))
        return rgb_to_hex(mix_rgb(bg, (255, 255, 255), 0.20))
    if accent is not None:
        return rgb_to_hex(mix_rgb(bg, accent, 0.16))
    return rgb_to_hex(mix_rgb(bg, (15, 23, 42), 0.10))


def icon_surface_accent(surface: str, stroke: str) -> str:
    base = parse_hex_color(surface)
    accent = parse_hex_color(stroke)
    if base is None or accent is None:
        return stroke
    return rgb_to_hex(mix_rgb(base, accent, 0.22))


def aurora_nodes_enabled(style: Dict[str, Any]) -> bool:
    node_style = style.get("node", {})
    return node_style.get("fill_mode") == "aurora" or style_effect(style, "node_fill", "") == "aurora"


def illustrated_icons_enabled(style: Dict[str, Any]) -> bool:
    return resolve_icon_system(style) == "illustrated-v1"


def render_illustrated_icon_backplate(
    icon: str,
    part: Any,
    cx: float,
    cy: float,
    half: float,
    stroke: str,
    fill: str,
    style: Dict[str, Any],
    index: int,
) -> str:
    palette = illustrated_palette(icon, style, fallback_stroke=stroke, fallback_fill=fill)
    bubble = palette["bubble"]
    wash = palette["wash"]
    sparkle = palette["sparkle"]
    primary = palette["primary"]
    secondary = palette["secondary"]
    tertiary = palette["tertiary"]
    offset = (index % 3 - 1) * half * 0.05
    relation = legacy_illustrated_definition(icon).semantic_role
    return f"""
  <g class="illustrated-icon-backplate" data-semantic-role="{esc(relation)}" opacity="0.96">
    <circle id="{part("bubbleHalo")}" class="illustrated-icon-bubble-halo icon-runtime-part" cx="{cx + offset:.1f}" cy="{cy + half * 0.05:.1f}" r="{half * 1.48:.1f}"
          fill="none" stroke="{esc(secondary)}" stroke-width="2.0" opacity="0.18" />
    <ellipse id="{part("bubble")}" class="illustrated-icon-bubble icon-runtime-part" cx="{cx + offset:.1f}" cy="{cy + half * 0.05:.1f}" rx="{half * 1.42:.1f}" ry="{half * 1.16:.1f}"
          fill="{esc(bubble)}" stroke="{esc(primary)}" stroke-width="1.3" stroke-opacity="0.24" />
    <path id="{part("wash")}" class="illustrated-icon-wash icon-runtime-part" d="M {cx - half * 1.20:.1f} {cy + half * 0.28:.1f}
             C {cx - half * 0.58:.1f} {cy - half * 0.86:.1f},
               {cx + half * 0.58:.1f} {cy - half * 0.78:.1f},
               {cx + half * 1.14:.1f} {cy + half * 0.12:.1f}
             C {cx + half * 0.70:.1f} {cy + half * 0.84:.1f},
               {cx - half * 0.42:.1f} {cy + half * 0.94:.1f},
               {cx - half * 1.20:.1f} {cy + half * 0.28:.1f} Z"
          fill="{esc(wash)}" opacity="0.44" />
    <circle id="{part("sparkle")}" class="illustrated-icon-dot icon-runtime-part" cx="{cx + half * 0.96:.1f}" cy="{cy - half * 0.82:.1f}" r="{max(1.8, half * 0.10):.1f}"
          fill="{esc(sparkle)}" opacity="0.78" />
    <circle id="{part("orbitDot")}" class="illustrated-icon-orbit-dot icon-runtime-part" cx="{cx - half * 1.04:.1f}" cy="{cy + half * 0.68:.1f}" r="{max(1.7, half * 0.09):.1f}"
          fill="{esc(secondary)}" opacity="0.68" />
    <path id="{part("accentMark")}" class="illustrated-icon-mark icon-runtime-part" d="M {cx - half * 1.04:.1f} {cy - half * 0.82:.1f} L {cx - half * 0.84:.1f} {cy - half * 0.62:.1f}
             M {cx - half * 0.76:.1f} {cy - half * 0.90:.1f} L {cx - half * 0.56:.1f} {cy - half * 0.70:.1f}"
          fill="none" stroke="{esc(tertiary)}" stroke-width="1.7" stroke-linecap="round" opacity="0.52" />
  </g>"""


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
    return wrap_text(text, max_chars)


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
    return trim_segment_endpoints(start, end, EDGE_NODE_GAP)


def point_towards(start: Point, end: Point, distance: float) -> Point:
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    length = math.hypot(dx, dy)
    if length <= 0 or distance <= 0:
        return start
    amount = min(distance, length / 2)
    return (sx + dx / length * amount, sy + dy / length * amount)


def trim_segment_endpoints(start: Point, end: Point, gap: float) -> Tuple[Point, Point]:
    return point_towards(start, end, gap), point_towards(end, start, gap)


def trim_route_endpoints(points: List[Point], gap: float = EDGE_NODE_GAP) -> List[Point]:
    if len(points) < 2:
        return points
    trimmed = list(points)
    trimmed[0] = point_towards(trimmed[0], trimmed[1], gap)
    trimmed[-1] = point_towards(trimmed[-1], trimmed[-2], gap)
    return compact_points(trimmed)


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


def render_text_block(x: float, y: float, width: float, height: float, label: str, caption: str, color: str) -> str:
    layout = text_block_layout(label, caption, width, height)
    parts = [f'<text x="{x + width / 2:.1f}" y="{y + layout.first_baseline:.1f}" class="node-text-block" text-anchor="middle" fill="{esc(color)}">']
    first = True
    for line in layout.label_lines:
        fitted = fitted_text_length(line, width, 18)
        fit = "" if fitted is None else f' textLength="{fitted:.1f}" lengthAdjust="spacingAndGlyphs"'
        parts.append(f'<tspan x="{x + width / 2:.1f}" dy="{0 if first else 18}" class="node-title"{fit}>{esc(line)}</tspan>')
        first = False
    for line in layout.caption_lines:
        fitted = fitted_text_length(line, width, 13)
        fit = "" if fitted is None else f' textLength="{fitted:.1f}" lengthAdjust="spacingAndGlyphs"'
        parts.append(f'<tspan x="{x + width / 2:.1f}" dy="17" class="node-caption"{fit}>{esc(line)}</tspan>')
    parts.append("</text>")
    return "\n".join(parts)


def render_step_badge(x: float, y: float, value: int, fill: str, text: str) -> str:
    return f"""
  <circle cx="{x:.1f}" cy="{y:.1f}" r="14" fill="{esc(fill)}" />
  <text x="{x:.1f}" y="{y + 5:.1f}" class="step-label" fill="{esc(text)}" text-anchor="middle">{value}</text>"""


ICON_MOTION_IDS = {
    "database-write",
    "file-lines",
    "folder-open",
    "api-ping",
    "cloud-upload",
    "search-sweep",
    "shield-check",
    "agent-orbit",
    "tool-tap",
    "output-check",
    "token-pulse",
    "status-ping",
}

def default_icon_motion(icon: str) -> str:
    if icon in {"database", "memory"}:
        return "database-write"
    return {
        "file": "file-lines",
        "folder": "folder-open",
        "api": "api-ping",
        "cloud": "cloud-upload",
        "search": "search-sweep",
        "shield": "shield-check",
        "agent": "agent-orbit",
        "tool": "tool-tap",
        "output": "output-check",
        "token": "token-pulse",
    }.get(icon, "status-ping")


def render_icon_semantic_motion(
    icon: str,
    cx: float,
    cy: float,
    half: float,
    stroke: str,
    motion: SceneMotion,
    effect: EffectConfig,
    index: int,
    suppress: bool = False,
) -> str:
    if suppress:
        return ""
    if not effect_active(motion, effect) or effect.preset not in {"icon-semantic", "icon-performance"}:
        return ""
    requested = effect.icon_motion or effect.icon or default_icon_motion(icon)
    motion_id = requested if requested in ICON_MOTION_IDS else default_icon_motion(icon)
    duration = scaled_duration(2.15 + (index % 3) * 0.12, motion)
    if motion_id == "file-lines":
        duration = scaled_duration(1.75 + (index % 3) * 0.08, motion)
    begin = motion_delay(index, motion, "node") + 0.52
    motion_class = f"icon-semantic-motion icon-motion-{esc(svg_fragment_id(motion_id))}"
    data = f'data-icon-motion="{esc(motion_id)}"'

    if motion_id == "database-write":
        left = cx - half * 0.74
        right = cx + half * 0.74
        top = cy - half * 0.68
        mid = cy + half * 0.12
        layer_y = cy + half * 0.52
        return f"""
  <g class="{motion_class}" {data}>
    <ellipse class="icon-database-top-bounce" cx="{cx:.1f}" cy="{cy - half * 0.62:.1f}" rx="{half * 0.84:.1f}" ry="{half * 0.28:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="2.4" opacity="0.74">
      <animate attributeName="ry" values="{half * 0.28:.1f};{half * 0.17:.1f};{half * 0.39:.1f};{half * 0.28:.1f}" keyTimes="0;0.18;0.34;1" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
      <animateTransform attributeName="transform" type="translate" values="0 0;0 {half * 0.10:.1f};0 {-half * 0.06:.1f};0 0" keyTimes="0;0.18;0.34;1" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0.36;0.88;0.64;0.36" keyTimes="0;0.18;0.34;1" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
    </ellipse>
    <path d="M {left:.1f} {top:.1f} H {right:.1f}" fill="none" stroke="{esc(stroke)}" stroke-width="3"
          stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" opacity="0.95">
      <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;0.22;0.68;1" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.95;0.95;0" keyTimes="0;0.12;0.72;1" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
    </path>
    <circle r="{max(2.7, half * 0.22):.1f}" fill="{esc(stroke)}" opacity="0">
      <animateMotion dur="{seconds(duration)}" begin="{seconds(begin + 0.08)}" repeatCount="indefinite" path="M {left:.1f} {mid:.1f} H {right:.1f}" />
      <animate attributeName="opacity" values="0;0.92;0" dur="{seconds(duration)}" begin="{seconds(begin + 0.08)}" repeatCount="indefinite" />
    </circle>
    <path class="icon-database-layer-flash" d="M {cx - half * 0.78:.1f} {layer_y:.1f} C {cx - half * 0.42:.1f} {layer_y + half * 0.22:.1f}, {cx + half * 0.42:.1f} {layer_y + half * 0.22:.1f}, {cx + half * 0.78:.1f} {layer_y:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="2.3" stroke-linecap="round" opacity="0">
      <animateTransform attributeName="transform" type="translate" values="0 0;0 {half * 0.18:.1f};0 {-half * 0.08:.1f};0 0" keyTimes="0;0.18;0.34;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.16)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.74;0.32;0" keyTimes="0;0.18;0.44;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.16)}" repeatCount="indefinite" />
    </path>
  </g>"""

    if motion_id == "file-lines":
        x1 = cx - half * 0.42
        x2 = cx + half * 0.44
        lines = []
        for line_index, line_y in enumerate((cy - half * 0.18, cy + half * 0.18, cy + half * 0.52)):
            line_begin = begin + 0.22 + line_index * 0.045
            lines.append(
                f"""    <path d="M {x1:.1f} {line_y:.1f} H {x2 - line_index * half * 0.12:.1f}" fill="none" stroke="{esc(stroke)}" stroke-width="2.4"
          stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" opacity="0.76">
      <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;0.08;0.68;1" dur="{seconds(duration)}" begin="{seconds(line_begin)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.92;0.92;0" keyTimes="0;0.06;0.66;1" dur="{seconds(duration)}" begin="{seconds(line_begin)}" repeatCount="indefinite" />
    </path>"""
            )
        return f"""
  <g class="{motion_class}" {data}>
{chr(10).join(lines)}
  </g>"""

    if motion_id == "folder-open":
        hinge_x = cx - half * 0.92
        hinge_y = cy - half * 0.48
        return f"""
  <g class="{motion_class}" {data}>
    <path d="M {hinge_x:.1f} {hinge_y:.1f} H {cx - half * 0.20:.1f} L {cx + half * 0.02:.1f} {cy - half * 0.78:.1f} H {cx + half * 0.95:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round" opacity="0.92">
      <animateTransform attributeName="transform" type="rotate" values="3 {hinge_x:.1f} {hinge_y:.1f};-20 {hinge_x:.1f} {hinge_y:.1f};3 {hinge_x:.1f} {hinge_y:.1f}" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0.36;0.96;0.36" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
    </path>
    <path class="icon-folder-file-line" d="M {cx - half * 0.52:.1f} {cy + half * 0.16:.1f} H {cx + half * 0.54:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="2.5" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" opacity="0">
      <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;0.16;0.52;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.16)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.86;0.72;0" keyTimes="0;0.12;0.58;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.16)}" repeatCount="indefinite" />
    </path>
  </g>"""

    if motion_id == "api-ping":
        return f"""
  <g class="{motion_class}" {data}>
    <circle r="{max(3.0, half * 0.24):.1f}" fill="{esc(stroke)}" opacity="0">
      <animateMotion dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" path="M {cx - half * 0.78:.1f} {cy:.1f} H {cx + half * 0.78:.1f}" />
      <animate attributeName="opacity" values="0;0.98;0" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
    </circle>
    <circle cx="{cx + half * 0.78:.1f}" cy="{cy:.1f}" r="{max(4.0, half * 0.24):.1f}" fill="none" stroke="{esc(stroke)}" stroke-width="2.1" opacity="0">
      <animate attributeName="r" values="{half * 0.20:.1f};{half * 0.72:.1f}" dur="{seconds(duration)}" begin="{seconds(begin + 0.24)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.58;0" dur="{seconds(duration)}" begin="{seconds(begin + 0.24)}" repeatCount="indefinite" />
    </circle>
  </g>"""

    if motion_id == "cloud-upload":
        return f"""
  <g class="{motion_class}" {data}>
    <path d="M {cx:.1f} {cy + half * 0.58:.1f} V {cy - half * 0.12:.1f}
             M {cx - half * 0.26:.1f} {cy + half * 0.12:.1f} L {cx:.1f} {cy - half * 0.16:.1f} L {cx + half * 0.26:.1f} {cy + half * 0.12:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="2.9" stroke-linecap="round" stroke-linejoin="round" opacity="0.92">
      <animateTransform attributeName="transform" type="translate" values="0 {half * 0.42:.1f};0 {-half * 0.36:.1f};0 {half * 0.42:.1f}" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.96;0" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
    </path>
    <circle class="icon-cloud-dot" cx="{cx - half * 0.34:.1f}" cy="{cy + half * 0.26:.1f}" r="{max(2.0, half * 0.13):.1f}" fill="{esc(stroke)}" opacity="0">
      <animate attributeName="r" values="{max(1.4, half * 0.08):.1f};{max(2.6, half * 0.18):.1f};{max(1.4, half * 0.08):.1f}" dur="{seconds(duration)}" begin="{seconds(begin + 0.12)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.62;0" dur="{seconds(duration)}" begin="{seconds(begin + 0.12)}" repeatCount="indefinite" />
    </circle>
    <circle class="icon-cloud-dot" cx="{cx + half * 0.34:.1f}" cy="{cy + half * 0.30:.1f}" r="{max(1.8, half * 0.11):.1f}" fill="{esc(stroke)}" opacity="0">
      <animate attributeName="r" values="{max(1.2, half * 0.07):.1f};{max(2.4, half * 0.16):.1f};{max(1.2, half * 0.07):.1f}" dur="{seconds(duration)}" begin="{seconds(begin + 0.34)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.48;0" dur="{seconds(duration)}" begin="{seconds(begin + 0.34)}" repeatCount="indefinite" />
    </circle>
  </g>"""

    if motion_id == "search-sweep":
        return f"""
  <g class="{motion_class}" {data}>
    <path d="M {cx - half * 0.78:.1f} {cy - half * 0.58:.1f} L {cx + half * 0.36:.1f} {cy + half * 0.52:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="3.1" stroke-linecap="round" opacity="0.88">
      <animateTransform attributeName="transform" type="rotate" values="-22 {cx:.1f} {cy:.1f};32 {cx:.1f} {cy:.1f};-22 {cx:.1f} {cy:.1f}" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.96;0" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
    </path>
    <circle class="icon-search-light" r="{max(2.2, half * 0.15):.1f}" fill="{esc(stroke)}" opacity="0">
      <animateMotion dur="{seconds(duration)}" begin="{seconds(begin + 0.08)}" repeatCount="indefinite" path="M {cx - half * 0.46:.1f} {cy - half * 0.48:.1f} L {cx + half * 0.18:.1f} {cy + half * 0.16:.1f}" />
      <animate attributeName="opacity" values="0;0.86;0" keyTimes="0;0.22;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.08)}" repeatCount="indefinite" />
    </circle>
  </g>"""

    if motion_id == "shield-check":
        return f"""
  <g class="{motion_class}" {data}>
    <path class="icon-shield-pulse" d="M {cx:.1f} {cy - half * 1.05:.1f} L {cx + half * 0.96:.1f} {cy - half * 0.58:.1f} V {cy + half * 0.10:.1f}
           C {cx + half * 0.96:.1f} {cy + half * 0.72:.1f}, {cx + half * 0.38:.1f} {cy + half * 1.02:.1f}, {cx:.1f} {cy + half * 1.12:.1f}
           C {cx - half * 0.38:.1f} {cy + half * 1.02:.1f}, {cx - half * 0.96:.1f} {cy + half * 0.72:.1f}, {cx - half * 0.96:.1f} {cy + half * 0.10:.1f}
           V {cy - half * 0.58:.1f} Z"
          fill="none" stroke="{esc(stroke)}" stroke-width="1.5" stroke-linejoin="round" opacity="0">
      <animate attributeName="stroke-width" values="1.2;2.8;1.2" keyTimes="0;0.34;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.12)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.34;0" keyTimes="0;0.34;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.12)}" repeatCount="indefinite" />
    </path>
    <path d="M {cx - half * 0.44:.1f} {cy + half * 0.03:.1f} L {cx - half * 0.08:.1f} {cy + half * 0.42:.1f} L {cx + half * 0.58:.1f} {cy - half * 0.48:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="4.4" stroke-linecap="round" stroke-linejoin="round"
          pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" opacity="0.98">
      <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;0.20;0.72;1" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.98;0.98;0" keyTimes="0;0.10;0.70;1" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
    </path>
  </g>"""

    if motion_id == "agent-orbit":
        return f"""
  <g class="{motion_class}" {data}>
    <path class="icon-agent-line-draw" d="M {cx:.1f} {cy - half * 0.86:.1f}
             L {cx - half * 0.38:.1f} {cy - half * 1.05:.1f}
             L {cx - half * 0.78:.1f} {cy - half * 0.78:.1f}
             V {cy - half * 0.48:.1f}
             H {cx - half * 1.02:.1f}
             V {cy + half * 0.08:.1f}
             H {cx - half * 0.72:.1f}
             V {cy + half * 0.50:.1f}
             L {cx:.1f} {cy + half * 0.90:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="3.1" stroke-linecap="round" stroke-linejoin="round"
          pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" opacity="0">
      <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;0.32;0.70;1" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.96;0.78;0" keyTimes="0;0.12;0.72;1" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
    </path>
    <path class="icon-agent-line-draw" d="M {cx:.1f} {cy - half * 0.86:.1f}
             L {cx + half * 0.28:.1f} {cy - half * 1.02:.1f}
             L {cx + half * 0.74:.1f} {cy - half * 0.74:.1f}
             V {cy - half * 0.42:.1f}
             H {cx + half * 1.02:.1f}
             V {cy - half * 0.02:.1f}
             H {cx + half * 0.78:.1f}
             V {cy + half * 0.36:.1f}
             H {cx + half * 0.52:.1f}
             V {cy + half * 0.64:.1f}
             L {cx:.1f} {cy + half * 0.90:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="3.1" stroke-linecap="round" stroke-linejoin="round"
          pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" opacity="0">
      <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;0.32;0.70;1" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.96;0.78;0" keyTimes="0;0.12;0.72;1" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
    </path>
    <path class="icon-agent-line-draw" d="M {cx:.1f} {cy - half * 0.28:.1f} H {cx - half * 0.42:.1f} V {cy - half * 0.64:.1f}
             M {cx:.1f} {cy - half * 0.02:.1f} H {cx + half * 0.44:.1f} V {cy - half * 0.55:.1f}
             M {cx:.1f} {cy + half * 0.34:.1f} H {cx + half * 0.54:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round"
          pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" opacity="0">
      <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;0.26;0.66;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.24)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.90;0.72;0" keyTimes="0;0.18;0.70;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.24)}" repeatCount="indefinite" />
    </path>
    <circle class="icon-agent-node-pop" cx="{cx - half * 0.42:.1f}" cy="{cy - half * 0.64:.1f}" r="{half * 0.11:.1f}" fill="{esc(stroke)}" opacity="0">
      <animate attributeName="r" values="{half * 0.02:.1f};{half * 0.15:.1f};{half * 0.11:.1f}" keyTimes="0;0.28;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.54)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.95;0.20" keyTimes="0;0.24;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.54)}" repeatCount="indefinite" />
    </circle>
    <circle class="icon-agent-node-pop" cx="{cx + half * 0.44:.1f}" cy="{cy - half * 0.55:.1f}" r="{half * 0.10:.1f}" fill="{esc(stroke)}" opacity="0">
      <animate attributeName="r" values="{half * 0.02:.1f};{half * 0.14:.1f};{half * 0.10:.1f}" keyTimes="0;0.28;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.62)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.88;0.18" keyTimes="0;0.24;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.62)}" repeatCount="indefinite" />
    </circle>
    <circle class="icon-agent-node-pop" cx="{cx:.1f}" cy="{cy - half * 0.02:.1f}" r="{half * 0.11:.1f}" fill="{esc(stroke)}" opacity="0">
      <animate attributeName="r" values="{half * 0.02:.1f};{half * 0.15:.1f};{half * 0.11:.1f}" keyTimes="0;0.28;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.70)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.92;0.20" keyTimes="0;0.24;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.70)}" repeatCount="indefinite" />
    </circle>
  </g>"""

    if motion_id == "tool-tap":
        return f"""
  <g class="{motion_class}" {data}>
    <path d="M {cx - half * 0.42:.1f} {cy - half * 0.34:.1f} L {cx + half * 0.42:.1f} {cy + half * 0.42:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="3.5" stroke-linecap="round" opacity="0.92">
      <animateTransform attributeName="transform" type="rotate" values="5 {cx:.1f} {cy:.1f};-24 {cx:.1f} {cy:.1f};7 {cx:.1f} {cy:.1f};0 {cx:.1f} {cy:.1f}" keyTimes="0;0.22;0.34;1" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0.24;0.98;0.50;0.24" keyTimes="0;0.22;0.34;1" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
    </path>
    <path class="icon-tool-spark" d="M {cx + half * 0.50:.1f} {cy + half * 0.26:.1f} L {cx + half * 0.76:.1f} {cy + half * 0.16:.1f}
             M {cx + half * 0.46:.1f} {cy + half * 0.40:.1f} L {cx + half * 0.76:.1f} {cy + half * 0.54:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="2.4" stroke-linecap="round" opacity="0">
      <animate attributeName="opacity" values="0;0.95;0" keyTimes="0;0.18;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.18)}" repeatCount="indefinite" />
    </path>
  </g>"""

    if motion_id == "output-check":
        line_x1 = cx - half * 0.58
        line_x2 = cx + half * 0.46
        output_lines = []
        for line_index, line_y in enumerate((cy - half * 0.38, cy - half * 0.08)):
            output_lines.append(
                f"""    <path class="icon-output-line" d="M {line_x1:.1f} {line_y:.1f} H {line_x2 - line_index * half * 0.18:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="2.4" stroke-linecap="round"
          pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" opacity="0">
      <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;0.12;0.54;1" dur="{seconds(duration)}" begin="{seconds(begin + line_index * 0.06)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.78;0.78;0" keyTimes="0;0.10;0.58;1" dur="{seconds(duration)}" begin="{seconds(begin + line_index * 0.06)}" repeatCount="indefinite" />
    </path>"""
            )
        return f"""
  <g class="{motion_class}" {data}>
{chr(10).join(output_lines)}
    <path d="M {cx - half * 0.58:.1f} {cy + half * 0.10:.1f} L {cx - half * 0.14:.1f} {cy + half * 0.52:.1f} L {cx + half * 0.68:.1f} {cy - half * 0.46:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="3.9" stroke-linecap="round" stroke-linejoin="round"
          pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" opacity="0.96">
      <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;0.20;0.74;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.18)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.96;0.96;0" keyTimes="0;0.10;0.72;1" dur="{seconds(duration)}" begin="{seconds(begin + 0.18)}" repeatCount="indefinite" />
    </path>
  </g>"""

    if motion_id == "token-pulse":
        tick_specs = [
            (cx - half * 0.70, cy - half * 0.42, cx - half * 0.92, cy - half * 0.62),
            (cx + half * 0.48, cy - half * 0.58, cx + half * 0.74, cy - half * 0.80),
            (cx + half * 0.62, cy + half * 0.36, cx + half * 0.90, cy + half * 0.52),
            (cx - half * 0.50, cy + half * 0.58, cx - half * 0.74, cy + half * 0.80),
        ]
        ticks = []
        for tick_index, (x1, y1, x2, y2) in enumerate(tick_specs):
            tick_begin = begin + tick_index * 0.08
            ticks.append(
                f"""    <path class="icon-token-tick" d="M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}"
          fill="none" stroke="{esc(stroke)}" stroke-width="2.3" stroke-linecap="round"
          pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" opacity="0">
      <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;0.16;0.48;1" dur="{seconds(duration)}" begin="{seconds(tick_begin)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.76;0.36;0" keyTimes="0;0.16;0.52;1" dur="{seconds(duration)}" begin="{seconds(tick_begin)}" repeatCount="indefinite" />
    </path>"""
            )
        return f"""
  <g class="{motion_class}" {data}>
    <circle class="icon-token-core" cx="{cx:.1f}" cy="{cy:.1f}" r="{half * 0.18:.1f}" fill="{esc(stroke)}" opacity="0.42">
      <animate attributeName="r" values="{half * 0.13:.1f};{half * 0.27:.1f};{half * 0.13:.1f}" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0.30;0.82;0.30" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
    </circle>
{chr(10).join(ticks)}
  </g>"""

    radius = max(half * 0.68, 9.0)
    return f"""
  <g class="{motion_class}" {data}>
    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" fill="none" stroke="{esc(stroke)}" stroke-width="2.4" opacity="0">
      <animate attributeName="r" values="{radius * 0.46:.1f};{radius:.1f}" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;0.68;0" dur="{seconds(duration)}" begin="{seconds(begin)}" repeatCount="indefinite" />
    </circle>
  </g>"""


def render_semantic_icon(
    icon: Optional[str],
    box: NodeBox,
    stroke: str,
    fill: str,
    text: str,
    motion: SceneMotion,
    effect: EffectConfig,
    index: int,
    suppress_icon_motion: bool = False,
    style: Optional[Dict[str, Any]] = None,
) -> str:
    if not icon:
        return ""
    style = style or {}
    icon_system = resolve_icon_system(style)
    if icon_system == "diagram-core-v1":
        size = min(92, max(72, box.h * 0.78))
        x = box.x + 10
        y = box.y + (box.h - size) / 2
        fragment = render_approved_icon(
            icon,
            f"node.{box.node_id}",
            size=size,
            x=x,
            y=y,
            tokens=icon_tokens_for_style(style),
        )
        return (
            f'<g class="semantic-icon-wrap semantic-icon-diagram-core-wrap" '
            f'data-icon="{esc(icon)}" data-node-id="{esc(box.node_id)}" '
            f'data-icon-presentation="showcase">{fragment}</g>'
        )
    character = character_definition(icon) if icon_system == "illustrated-character-v1" else None
    character_v2 = illustrated_definition(icon) if icon_system == "illustrated" else None
    illustrated = illustrated_icons_enabled(style)
    cx = box.x + min(42, max(30, box.w * 0.22))
    cy = box.y + box.h / 2
    size = min(34, max(24, box.h * 0.42))
    if effect_active(motion, effect) and effect.preset in {"icon-semantic", "icon-performance"}:
        size = min(42, max(30, box.h * 0.54))
    if illustrated:
        cx = box.x + min(48, max(34, box.w * 0.22))
        size = min(46, max(32, box.h * 0.56))
    if character:
        cx = box.x + min(54, max(40, box.w * 0.24))
        size = min(84, max(48, box.h * 0.58))
        return f'''<g class="semantic-icon-wrap semantic-icon-character-wrap" data-icon="{esc(icon)}" data-node-id="{esc(box.node_id)}" opacity="0.98">
  {render_character_icon(character, box.node_id, cx, cy, size)}
</g>'''
    if character_v2:
        cx = box.x + min(82, max(68, box.w * 0.16))
        size = min(118, max(88, box.h * 0.64))
        return f'''<g class="semantic-icon-wrap semantic-icon-character-wrap semantic-icon-illustrated-wrap" data-icon="{esc(icon)}" data-node-id="{esc(box.node_id)}" opacity="1">
  {render_character_v2_icon(character_v2, box.node_id, cx, cy, size, illustrated_tokens_for_style(style))}
</g>'''
    half = size / 2
    symbol_fill = icon_surface_fill(fill, stroke)
    if illustrated:
        palette = illustrated_palette(icon, style, fallback_stroke=stroke, fallback_fill=symbol_fill)
        stroke = palette["primary"]
        symbol_fill = palette["surface"]
    delay = motion_delay(index, motion, "node") + 0.4
    accent = ""
    halo = ""
    wrap_class = "semantic-icon-wrap"
    if illustrated:
        wrap_class += " semantic-icon-illustrated-v1"
    icon_open = ""
    icon_close = ""
    semantic_motion = render_icon_semantic_motion(
        icon,
        cx,
        cy,
        half,
        stroke,
        motion,
        effect,
        index,
        suppress=suppress_icon_motion,
    )
    breathing = effect_active(motion, effect) and effect.preset in BREATHING_NODE_MOTION
    if breathing:
        wrap_class += " semantic-icon-breathe-wrap"
        duration = scaled_duration(2.8 + (index % 3) * 0.16, motion)
        halo_radius = half * 0.74
        halo = f"""  <circle class="icon-breathe-halo" cx="{cx:.1f}" cy="{cy:.1f}" r="{halo_radius:.1f}" fill="none"
          stroke="{esc(stroke)}" stroke-width="1.5" opacity="0.05">
    <animate attributeName="r" values="{halo_radius:.1f};{half * 1.10:.1f};{halo_radius:.1f}" dur="{seconds(duration)}" begin="{seconds(delay)}" repeatCount="indefinite" />
    <animate attributeName="opacity" values="0.04;0.24;0.04" dur="{seconds(duration)}" begin="{seconds(delay)}" repeatCount="indefinite" />
  </circle>"""
        icon_open = f'<g class="semantic-icon-breathe" style="animation-delay: {seconds(delay)};">'
        icon_close = "</g>"
    elif effect_active(motion, effect) and effect.preset in {"icon-pulse", "pulse", "status-blink"}:
        accent = f"""    <animate attributeName="opacity" values="0.52;1;0.52" dur="{seconds(scaled_duration(2.8, motion))}" begin="{seconds(delay)}" repeatCount="indefinite" />"""
    icon_class = f"semantic-icon semantic-icon-{esc(icon)}"
    common = f'class="{icon_class}" fill="none" stroke="{esc(stroke)}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"'
    filled_common = f'class="semantic-icon icon-filled semantic-icon-{esc(icon)}" stroke="{esc(stroke)}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"'
    root_id = esc(icon_part_id(box.node_id, "root"))
    part = lambda name: esc(icon_part_id(box.node_id, name))
    illustration = render_illustrated_icon_backplate(icon, part, cx, cy, half, stroke, fill, style, index) if illustrated else ""
    if icon == "operator":
        body = f"""
  <circle id="{part("face")}" cx="{cx:.1f}" cy="{cy - half * 0.38:.1f}" r="{half * 0.36:.1f}" {filled_common} fill="{esc(symbol_fill)}" />
  <path id="{part("glasses")}" d="M {cx - half * 0.52:.1f} {cy - half * 0.40:.1f} h {half * 0.34:.1f} m {half * 0.36:.1f} 0 h {half * 0.34:.1f} m {-half * 0.70:.1f} 0 h {half * 0.36:.1f}" {common} stroke-width="2.2" />
  <path id="{part("body")}" d="M {cx - half * 0.68:.1f} {cy + half * 0.36:.1f} C {cx - half * 0.44:.1f} {cy - half * 0.02:.1f}, {cx + half * 0.44:.1f} {cy - half * 0.02:.1f}, {cx + half * 0.68:.1f} {cy + half * 0.36:.1f}" {common} />
  <rect id="{part("laptop")}" x="{cx - half * 0.76:.1f}" y="{cy + half * 0.20:.1f}" width="{half * 1.52:.1f}" height="{half * 0.70:.1f}" rx="{half * 0.10:.1f}" {filled_common} fill="{esc(symbol_fill)}" />
  <path d="M {cx - half * 0.92:.1f} {cy + half * 0.98:.1f} H {cx + half * 0.92:.1f}" {common} stroke-width="2.3" />"""
    elif icon == "database":
        body = f"""
  <ellipse id="{part("lid")}" cx="{cx:.1f}" cy="{cy - half * 0.62:.1f}" rx="{half * 0.82:.1f}" ry="{half * 0.34:.1f}" {filled_common} fill="{esc(symbol_fill)}" />
  <path id="{part("body")}" d="M {cx - half * 0.82:.1f} {cy - half * 0.62:.1f} L {cx - half * 0.82:.1f} {cy + half * 0.52:.1f}
           C {cx - half * 0.82:.1f} {cy + half * 0.88:.1f}, {cx + half * 0.82:.1f} {cy + half * 0.88:.1f}, {cx + half * 0.82:.1f} {cy + half * 0.52:.1f}
           L {cx + half * 0.82:.1f} {cy - half * 0.62:.1f}" {common} />
  <path id="{part("layer1")}" d="M {cx - half * 0.82:.1f} {cy:.1f} C {cx - half * 0.82:.1f} {cy + half * 0.34:.1f}, {cx + half * 0.82:.1f} {cy + half * 0.34:.1f}, {cx + half * 0.82:.1f} {cy:.1f}" {common} opacity="0.72" />
  <path id="{part("layer2")}" d="M {cx - half * 0.72:.1f} {cy + half * 0.42:.1f} C {cx - half * 0.38:.1f} {cy + half * 0.66:.1f}, {cx + half * 0.38:.1f} {cy + half * 0.66:.1f}, {cx + half * 0.72:.1f} {cy + half * 0.42:.1f}" {common} opacity="0.56" />
  <circle id="{part("writeToken")}" class="icon-runtime-part" cx="{cx - half * 0.45:.1f}" cy="{cy - half * 0.94:.1f}" r="{max(2.8, half * 0.16):.1f}" fill="{esc(stroke)}" opacity="0" />
  <circle id="{part("flash")}" class="icon-runtime-part" cx="{cx:.1f}" cy="{cy + half * 0.10:.1f}" r="{half * 0.72:.1f}" fill="none" stroke="{esc(stroke)}" stroke-width="2" opacity="0" />"""
    elif icon == "memory":
        card_fill = icon_surface_fill(fill, stroke)
        trace_y = (cy - half * 0.18, cy + half * 0.10, cy + half * 0.38)
        body = f"""
  <rect id="{part("backCard")}" class="icon-memory-back-card" x="{cx - half * 0.58:.1f}" y="{cy - half * 0.78:.1f}" width="{half * 1.18:.1f}" height="{half * 1.10:.1f}" rx="{half * 0.18:.1f}"
        fill="{esc(card_fill)}" stroke="{esc(stroke)}" stroke-width="2.5" opacity="0.58" />
  <rect id="{part("frontCard")}" class="icon-memory-front-card" x="{cx - half * 0.74:.1f}" y="{cy - half * 0.56:.1f}" width="{half * 1.28:.1f}" height="{half * 1.16:.1f}" rx="{half * 0.20:.1f}"
        fill="{esc(symbol_fill)}" stroke="{esc(stroke)}" stroke-width="2.7" opacity="0.84" />
  <path id="{part("trace1")}" class="icon-memory-trace" d="M {cx - half * 0.40:.1f} {trace_y[0]:.1f} H {cx + half * 0.30:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.2" stroke-linecap="round" opacity="0.82" />
  <path id="{part("trace2")}" class="icon-memory-trace" d="M {cx - half * 0.40:.1f} {trace_y[1]:.1f} H {cx + half * 0.44:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.2" stroke-linecap="round" opacity="0.82" />
  <path id="{part("trace3")}" class="icon-memory-trace" d="M {cx - half * 0.40:.1f} {trace_y[2]:.1f} H {cx + half * 0.18:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.2" stroke-linecap="round" opacity="0.82" />
  <circle id="{part("dot")}" class="icon-memory-dot" cx="{cx + half * 0.54:.1f}" cy="{cy - half * 0.42:.1f}" r="{half * 0.13:.1f}" fill="{esc(stroke)}" opacity="0.72" />
  <circle id="{part("commitToken")}" class="icon-runtime-part" cx="{cx - half * 0.52:.1f}" cy="{cy - half * 0.92:.1f}" r="{max(2.6, half * 0.15):.1f}" fill="{esc(stroke)}" opacity="0" />
  <circle id="{part("flash")}" class="icon-runtime-part" cx="{cx - half * 0.10:.1f}" cy="{cy + half * 0.02:.1f}" r="{half * 0.72:.1f}" fill="none" stroke="{esc(stroke)}" stroke-width="2" opacity="0" />"""
    elif icon == "file":
        page_fill = icon_surface_fill(fill, stroke)
        fold_fill = icon_surface_accent(page_fill, stroke)
        file_active = (
            not suppress_icon_motion
            and effect_active(motion, effect)
            and effect.preset in {"icon-semantic", "icon-performance"}
        )
        file_duration = scaled_duration(1.85 + (index % 3) * 0.10, motion)
        file_begin = motion_delay(index, motion, "node") + 0.38
        file_translate = ""
        file_scale = ""
        file_opacity = ""
        fold_motion = ""
        if file_active:
            file_translate = f"""      <animateTransform attributeName="transform" type="translate"
        values="{-(half * 0.54):.1f} {half * 0.56:.1f};{half * 0.16:.1f} {-half * 0.14:.1f};0 0;0 0"
        keyTimes="0;0.22;0.34;1" dur="{seconds(file_duration)}" begin="{seconds(file_begin)}" repeatCount="indefinite" />"""
            file_scale = f"""          <animateTransform attributeName="transform" type="scale"
            values="0.78;1.22;1;1" keyTimes="0;0.22;0.34;1"
            dur="{seconds(file_duration)}" begin="{seconds(file_begin)}" repeatCount="indefinite" />"""
            file_opacity = f"""      <animate attributeName="opacity" values="0;1;1;0.92" keyTimes="0;0.14;0.74;1"
        dur="{seconds(file_duration)}" begin="{seconds(file_begin)}" repeatCount="indefinite" />"""
            fold_motion = f"""      <animateTransform attributeName="transform" type="rotate"
        values="-38 {cx + half * 0.28:.1f} {cy - half:.1f};0 {cx + half * 0.28:.1f} {cy - half:.1f};0 {cx + half * 0.28:.1f} {cy - half:.1f};-16 {cx + half * 0.28:.1f} {cy - half:.1f};0 {cx + half * 0.28:.1f} {cy - half:.1f}"
        keyTimes="0;0.20;0.64;0.78;1" dur="{seconds(file_duration)}" begin="{seconds(file_begin + 0.06)}" repeatCount="indefinite" />"""
        body = f"""
  <g class="semantic-icon-file-page icon-file-page-motion" opacity="0.96">
{file_translate}
{file_opacity}
    <g transform="translate({cx:.1f} {cy:.1f})">
      <g>
{file_scale}
        <g transform="translate({-cx:.1f} {-cy:.1f})">
          <path id="{part("sheet")}" class="semantic-icon icon-filled semantic-icon-file icon-file-sheet"
                d="M {cx - half * 0.72:.1f} {cy - half:.1f} H {cx + half * 0.28:.1f} L {cx + half * 0.72:.1f} {cy - half * 0.56:.1f} V {cy + half:.1f} H {cx - half * 0.72:.1f} Z"
                fill="{esc(page_fill)}" stroke="{esc(stroke)}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
          <g id="{part("fold")}" class="icon-file-fold-motion">
{fold_motion}
            <path d="M {cx + half * 0.28:.1f} {cy - half:.1f} L {cx + half * 0.72:.1f} {cy - half * 0.56:.1f} H {cx + half * 0.28:.1f} Z"
                  fill="{esc(fold_fill)}" stroke="{esc(stroke)}" stroke-width="2.2" stroke-linejoin="round" />
            <path d="M {cx + half * 0.28:.1f} {cy - half:.1f} V {cy - half * 0.56:.1f} H {cx + half * 0.72:.1f}"
                  fill="none" stroke="{esc(stroke)}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" opacity="0.88" />
          </g>
          <path id="{part("line1")}" class="icon-runtime-part icon-file-line" d="M {cx - half * 0.42:.1f} {cy - half * 0.20:.1f} H {cx + half * 0.38:.1f}"
                fill="none" stroke="{esc(stroke)}" stroke-width="2.2" stroke-linecap="round" opacity="0" />
          <path id="{part("line2")}" class="icon-runtime-part icon-file-line" d="M {cx - half * 0.42:.1f} {cy + half * 0.12:.1f} H {cx + half * 0.28:.1f}"
                fill="none" stroke="{esc(stroke)}" stroke-width="2.2" stroke-linecap="round" opacity="0" />
          <path id="{part("line3")}" class="icon-runtime-part icon-file-line" d="M {cx - half * 0.42:.1f} {cy + half * 0.44:.1f} H {cx + half * 0.16:.1f}"
                fill="none" stroke="{esc(stroke)}" stroke-width="2.2" stroke-linecap="round" opacity="0" />
          <circle id="{part("flash")}" class="icon-runtime-part" cx="{cx + half * 0.18:.1f}" cy="{cy + half * 0.10:.1f}" r="{half * 0.62:.1f}"
                fill="none" stroke="{esc(stroke)}" stroke-width="2" opacity="0" />
        </g>
      </g>
    </g>
  </g>"""
    elif icon == "folder":
        body = f"""
  <path id="{part("body")}" class="semantic-icon icon-filled semantic-icon-folder icon-folder-body" d="M {cx - half:.1f} {cy - half * 0.48:.1f} H {cx - half * 0.22:.1f} L {cx:.1f} {cy - half * 0.78:.1f} H {cx + half:.1f} V {cy + half * 0.82:.1f} H {cx - half:.1f} Z"
        stroke="{esc(stroke)}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="{esc(symbol_fill)}" />
  <path id="{part("tab")}" class="icon-folder-tab" d="M {cx - half * 0.92:.1f} {cy - half * 0.48:.1f} H {cx - half * 0.24:.1f} L {cx:.1f} {cy - half * 0.78:.1f} H {cx + half * 0.88:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round" opacity="0.92" />
  <path id="{part("fileLine")}" class="icon-runtime-part icon-folder-file-line" d="M {cx - half * 0.52:.1f} {cy + half * 0.16:.1f} H {cx + half * 0.52:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.4" stroke-linecap="round" opacity="0" />
  <circle id="{part("openToken")}" class="icon-runtime-part" cx="{cx - half * 0.48:.1f}" cy="{cy - half * 0.08:.1f}" r="{max(2.3, half * 0.13):.1f}" fill="{esc(stroke)}" opacity="0" />
  <circle id="{part("flash")}" class="icon-runtime-part" cx="{cx:.1f}" cy="{cy + half * 0.20:.1f}" r="{half * 0.68:.1f}" fill="none" stroke="{esc(stroke)}" stroke-width="2" opacity="0" />"""
    elif icon == "api":
        endpoint_fill = icon_surface_fill(fill, stroke)
        body = f"""
  <rect id="{part("leftEndpoint")}" x="{cx - half * 0.96:.1f}" y="{cy - half * 0.46:.1f}" width="{half * 0.30:.1f}" height="{half * 0.92:.1f}" rx="{half * 0.15:.1f}"
        fill="{esc(endpoint_fill)}" stroke="{esc(stroke)}" stroke-width="2.7" />
  <rect id="{part("rightEndpoint")}" x="{cx + half * 0.66:.1f}" y="{cy - half * 0.46:.1f}" width="{half * 0.30:.1f}" height="{half * 0.92:.1f}" rx="{half * 0.15:.1f}"
        fill="{esc(endpoint_fill)}" stroke="{esc(stroke)}" stroke-width="2.7" />
  <path d="M {cx - half * 0.50:.1f} {cy:.1f} H {cx + half * 0.50:.1f}" {common} opacity="0.62" />
  <path d="M {cx - half * 0.16:.1f} {cy - half * 0.20:.1f} L {cx + half * 0.06:.1f} {cy:.1f} L {cx - half * 0.16:.1f} {cy + half * 0.20:.1f}
           M {cx + half * 0.22:.1f} {cy + half * 0.20:.1f} L {cx:.1f} {cy:.1f} L {cx + half * 0.22:.1f} {cy - half * 0.20:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" opacity="0.86" />
  <circle id="{part("requestToken")}" class="icon-runtime-part" cx="{cx - half * 0.44:.1f}" cy="{cy:.1f}" r="{max(2.9, half * 0.16):.1f}" fill="{esc(stroke)}" opacity="0" />
  <circle id="{part("responseToken")}" class="icon-runtime-part" cx="{cx + half * 0.44:.1f}" cy="{cy:.1f}" r="{max(2.4, half * 0.13):.1f}" fill="{esc(stroke)}" opacity="0" />
  <circle id="{part("targetRing")}" class="icon-runtime-part" cx="{cx + half * 0.46:.1f}" cy="{cy:.1f}" r="{half * 0.22:.1f}" fill="none" stroke="{esc(stroke)}" stroke-width="2" opacity="0" />
  <text id="{part("status")}" class="icon-runtime-part" x="{cx:.1f}" y="{cy + half * 0.20:.1f}" text-anchor="middle"
        fill="{esc(stroke)}" stroke="none" font-size="{max(8, half * 0.42):.1f}" font-weight="700" opacity="0">200</text>"""
    elif icon == "cloud":
        body = f"""
  <path id="{part("shell")}" d="M {cx - half:.1f} {cy + half * 0.22:.1f}
           C {cx - half:.1f} {cy - half * 0.18:.1f}, {cx - half * 0.56:.1f} {cy - half * 0.34:.1f}, {cx - half * 0.28:.1f} {cy - half * 0.36:.1f}
           C {cx - half * 0.12:.1f} {cy - half * 0.90:.1f}, {cx + half * 0.62:.1f} {cy - half * 0.72:.1f}, {cx + half * 0.56:.1f} {cy - half * 0.16:.1f}
           C {cx + half * 1.08:.1f} {cy - half * 0.10:.1f}, {cx + half * 1.06:.1f} {cy + half * 0.62:.1f}, {cx + half * 0.54:.1f} {cy + half * 0.62:.1f}
           H {cx - half * 0.72:.1f}" {filled_common} fill="{esc(symbol_fill)}" />
  <path id="{part("uploadArrow")}" class="icon-runtime-part" d="M {cx:.1f} {cy + half * 0.48:.1f} V {cy - half * 0.10:.1f}
           M {cx - half * 0.24:.1f} {cy + half * 0.12:.1f} L {cx:.1f} {cy - half * 0.14:.1f} L {cx + half * 0.24:.1f} {cy + half * 0.12:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round" opacity="0" />
  <circle id="{part("dot1")}" class="icon-runtime-part icon-cloud-dot" cx="{cx - half * 0.42:.1f}" cy="{cy + half * 0.34:.1f}" r="{max(1.9, half * 0.10):.1f}" fill="{esc(stroke)}" opacity="0" />
  <circle id="{part("dot2")}" class="icon-runtime-part icon-cloud-dot" cx="{cx:.1f}" cy="{cy + half * 0.38:.1f}" r="{max(1.9, half * 0.10):.1f}" fill="{esc(stroke)}" opacity="0" />
  <circle id="{part("dot3")}" class="icon-runtime-part icon-cloud-dot" cx="{cx + half * 0.42:.1f}" cy="{cy + half * 0.34:.1f}" r="{max(1.9, half * 0.10):.1f}" fill="{esc(stroke)}" opacity="0" />
  <circle id="{part("statusRing")}" class="icon-runtime-part" cx="{cx + half * 0.46:.1f}" cy="{cy - half * 0.06:.1f}" r="{half * 0.26:.1f}" fill="none" stroke="{esc(stroke)}" stroke-width="2" opacity="0" />"""
    elif icon == "search":
        body = f"""
  <circle id="{part("lens")}" cx="{cx - half * 0.16:.1f}" cy="{cy - half * 0.16:.1f}" r="{half * 0.54:.1f}" {filled_common} fill="{esc(symbol_fill)}" />
  <path id="{part("handle")}" d="M {cx + half * 0.30:.1f} {cy + half * 0.30:.1f} L {cx + half * 0.92:.1f} {cy + half * 0.92:.1f}" {common} />
  <path id="{part("scan")}" class="icon-runtime-part" d="M {cx - half * 0.62:.1f} {cy - half * 0.44:.1f} L {cx + half * 0.20:.1f} {cy + half * 0.28:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.8" stroke-linecap="round" opacity="0" />
  <circle id="{part("result1")}" class="icon-runtime-part" cx="{cx - half * 0.33:.1f}" cy="{cy - half * 0.22:.1f}" r="{max(2.2, half * 0.13):.1f}" fill="{esc(stroke)}" opacity="0" />
  <circle id="{part("result2")}" class="icon-runtime-part" cx="{cx + half * 0.02:.1f}" cy="{cy - half * 0.02:.1f}" r="{max(1.9, half * 0.11):.1f}" fill="{esc(stroke)}" opacity="0" />
  <circle id="{part("target")}" class="icon-runtime-part" cx="{cx + half * 0.18:.1f}" cy="{cy - half * 0.20:.1f}" r="{half * 0.22:.1f}" fill="none" stroke="{esc(stroke)}" stroke-width="2" opacity="0" />"""
    elif icon == "shield":
        body = f"""
  <path id="{part("pulse")}" class="icon-runtime-part" d="M {cx:.1f} {cy - half:.1f} L {cx + half * 0.86:.1f} {cy - half * 0.58:.1f} V {cy + half * 0.10:.1f}
           C {cx + half * 0.86:.1f} {cy + half * 0.66:.1f}, {cx + half * 0.34:.1f} {cy + half * 0.92:.1f}, {cx:.1f} {cy + half:.1f}
           C {cx - half * 0.34:.1f} {cy + half * 0.92:.1f}, {cx - half * 0.86:.1f} {cy + half * 0.66:.1f}, {cx - half * 0.86:.1f} {cy + half * 0.10:.1f}
           V {cy - half * 0.58:.1f} Z" fill="none" stroke="{esc(stroke)}" stroke-width="1.6" stroke-linejoin="round" opacity="0" />
  <path id="{part("shell")}" d="M {cx:.1f} {cy - half:.1f} L {cx + half * 0.86:.1f} {cy - half * 0.58:.1f} V {cy + half * 0.10:.1f}
           C {cx + half * 0.86:.1f} {cy + half * 0.66:.1f}, {cx + half * 0.34:.1f} {cy + half * 0.92:.1f}, {cx:.1f} {cy + half:.1f}
           C {cx - half * 0.34:.1f} {cy + half * 0.92:.1f}, {cx - half * 0.86:.1f} {cy + half * 0.66:.1f}, {cx - half * 0.86:.1f} {cy + half * 0.10:.1f}
           V {cy - half * 0.58:.1f} Z" {filled_common} fill="{esc(symbol_fill)}" />
  <path id="{part("scan")}" class="icon-runtime-part" d="M {cx - half * 0.62:.1f} {cy - half * 0.40:.1f} L {cx + half * 0.56:.1f} {cy + half * 0.42:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.4" stroke-linecap="round" opacity="0" />
  <path id="{part("check")}" d="M {cx - half * 0.34:.1f} {cy:.1f} L {cx - half * 0.06:.1f} {cy + half * 0.30:.1f} L {cx + half * 0.42:.1f} {cy - half * 0.38:.1f}" {common} />"""
    elif icon == "agent":
        agent_fill = icon_surface_fill(fill, stroke)
        token_r = max(2.4, half * 0.13)
        body = f"""
  <g class="semantic-icon semantic-icon-agent icon-agent-ghost" opacity="0.24">
    <path d="M {cx:.1f} {cy - half * 0.86:.1f}
           L {cx - half * 0.38:.1f} {cy - half * 1.05:.1f}
           L {cx - half * 0.78:.1f} {cy - half * 0.78:.1f}
           V {cy - half * 0.48:.1f}
           H {cx - half * 1.02:.1f}
           V {cy + half * 0.08:.1f}
           H {cx - half * 0.72:.1f}
           V {cy + half * 0.50:.1f}
           L {cx:.1f} {cy + half * 0.90:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
    <path d="M {cx:.1f} {cy - half * 0.86:.1f}
           L {cx + half * 0.28:.1f} {cy - half * 1.02:.1f}
           L {cx + half * 0.74:.1f} {cy - half * 0.74:.1f}
           V {cy - half * 0.42:.1f}
           H {cx + half * 1.02:.1f}
           V {cy - half * 0.02:.1f}
           H {cx + half * 0.78:.1f}
           V {cy + half * 0.36:.1f}
           H {cx + half * 0.52:.1f}
           V {cy + half * 0.64:.1f}
           L {cx:.1f} {cy + half * 0.90:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
    <path d="M {cx:.1f} {cy - half * 0.70:.1f} V {cy + half * 0.66:.1f}
           M {cx:.1f} {cy - half * 0.28:.1f} H {cx - half * 0.42:.1f} V {cy - half * 0.64:.1f}
           M {cx:.1f} {cy - half * 0.02:.1f} H {cx + half * 0.44:.1f} V {cy - half * 0.55:.1f}
           M {cx:.1f} {cy + half * 0.34:.1f} H {cx + half * 0.54:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" />
  </g>
  <path id="{part("outlineLeft")}" class="semantic-icon semantic-icon-agent icon-agent-line"
        d="M {cx:.1f} {cy - half * 0.86:.1f}
           L {cx - half * 0.38:.1f} {cy - half * 1.05:.1f}
           L {cx - half * 0.78:.1f} {cy - half * 0.78:.1f}
           V {cy - half * 0.48:.1f}
           H {cx - half * 1.02:.1f}
           V {cy + half * 0.08:.1f}
           H {cx - half * 0.72:.1f}
           V {cy + half * 0.50:.1f}
           L {cx:.1f} {cy + half * 0.90:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round" opacity="0.92" />
  <path id="{part("outlineRight")}" class="semantic-icon semantic-icon-agent icon-agent-line"
        d="M {cx:.1f} {cy - half * 0.86:.1f}
           L {cx + half * 0.28:.1f} {cy - half * 1.02:.1f}
           L {cx + half * 0.74:.1f} {cy - half * 0.74:.1f}
           V {cy - half * 0.42:.1f}
           H {cx + half * 1.02:.1f}
           V {cy - half * 0.02:.1f}
           H {cx + half * 0.78:.1f}
           V {cy + half * 0.36:.1f}
           H {cx + half * 0.52:.1f}
           V {cy + half * 0.64:.1f}
           L {cx:.1f} {cy + half * 0.90:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round" opacity="0.92" />
  <path id="{part("centerLine")}" class="semantic-icon semantic-icon-agent icon-agent-line"
        d="M {cx:.1f} {cy - half * 0.70:.1f} V {cy + half * 0.66:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.2" stroke-linecap="round" opacity="0.78" />
  <path id="{part("branchLeft")}" class="semantic-icon semantic-icon-agent icon-agent-line"
        d="M {cx:.1f} {cy - half * 0.28:.1f} H {cx - half * 0.42:.1f} V {cy - half * 0.64:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" opacity="0.78" />
  <path id="{part("branchRight")}" class="semantic-icon semantic-icon-agent icon-agent-line"
        d="M {cx:.1f} {cy - half * 0.02:.1f} H {cx + half * 0.44:.1f} V {cy - half * 0.55:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" opacity="0.78" />
  <path id="{part("branchLower")}" class="semantic-icon semantic-icon-agent icon-agent-line"
        d="M {cx:.1f} {cy + half * 0.34:.1f} H {cx + half * 0.54:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.1" stroke-linecap="round" opacity="0.74" />
  <circle id="{part("nodeTopLeft")}" class="icon-runtime-part icon-agent-node" cx="{cx - half * 0.42:.1f}" cy="{cy - half * 0.64:.1f}" r="{max(2.1, half * 0.12):.1f}"
        fill="{esc(agent_fill)}" stroke="{esc(stroke)}" stroke-width="1.6" opacity="0.82" />
  <circle id="{part("nodeTopRight")}" class="icon-runtime-part icon-agent-node" cx="{cx + half * 0.44:.1f}" cy="{cy - half * 0.55:.1f}" r="{max(2.0, half * 0.11):.1f}"
        fill="{esc(agent_fill)}" stroke="{esc(stroke)}" stroke-width="1.6" opacity="0.80" />
  <circle id="{part("nodeLeft")}" class="icon-runtime-part icon-agent-node" cx="{cx - half * 0.72:.1f}" cy="{cy + half * 0.08:.1f}" r="{max(1.9, half * 0.10):.1f}"
        fill="{esc(agent_fill)}" stroke="{esc(stroke)}" stroke-width="1.5" opacity="0.74" />
  <circle id="{part("nodeRight")}" class="icon-runtime-part icon-agent-node" cx="{cx + half * 0.54:.1f}" cy="{cy + half * 0.34:.1f}" r="{max(1.9, half * 0.10):.1f}"
        fill="{esc(agent_fill)}" stroke="{esc(stroke)}" stroke-width="1.5" opacity="0.74" />
  <circle id="{part("nodeCenter")}" class="icon-runtime-part icon-agent-node" cx="{cx:.1f}" cy="{cy - half * 0.02:.1f}" r="{max(2.4, half * 0.13):.1f}"
        fill="{esc(agent_fill)}" stroke="{esc(stroke)}" stroke-width="1.7" opacity="0.88" />
  <circle id="{part("pulse")}" class="icon-runtime-part" cx="{cx:.1f}" cy="{cy - half * 0.02:.1f}" r="{half * 0.62:.1f}" fill="none" stroke="{esc(stroke)}" stroke-width="2" opacity="0" />
  <path id="{part("decisionToken")}" class="icon-runtime-part icon-agent-decision-token"
        d="M {cx + half * 0.70:.1f} {cy - half * 0.18 - token_r:.1f}
           L {cx + half * 0.70 + token_r:.1f} {cy - half * 0.18:.1f}
           L {cx + half * 0.70:.1f} {cy - half * 0.18 + token_r:.1f}
           L {cx + half * 0.70 - token_r:.1f} {cy - half * 0.18:.1f}
           Z"
        fill="{esc(stroke)}" stroke="{esc(agent_fill)}" stroke-width="1.2" opacity="0" />"""
    elif icon == "tool":
        chip_fill = icon_surface_fill(fill, stroke)
        body = f"""
  <rect id="{part("chip")}" x="{cx - half * 0.88:.1f}" y="{cy - half * 0.56:.1f}" width="{half * 1.46:.1f}" height="{half * 1.12:.1f}" rx="{half * 0.26:.1f}"
        fill="{esc(chip_fill)}" stroke="{esc(stroke)}" stroke-width="2.8" />
  <text id="{part("glyph")}" x="{cx - half * 0.30:.1f}" y="{cy + half * 0.17:.1f}" text-anchor="middle"
        fill="{esc(stroke)}" stroke="none" font-size="{max(10, half * 0.52):.1f}" font-weight="800">fx</text>
  <circle id="{part("connector")}" cx="{cx + half * 0.42:.1f}" cy="{cy:.1f}" r="{half * 0.13:.1f}" fill="{esc(stroke)}" opacity="0.72" />
  <path id="{part("spark1")}" class="icon-tool-spark" d="M {cx + half * 0.66:.1f} {cy - half * 0.44:.1f} L {cx + half * 0.82:.1f} {cy - half * 0.62:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.2" stroke-linecap="round" opacity="0.84" />
  <path id="{part("spark2")}" class="icon-tool-spark" d="M {cx + half * 0.70:.1f} {cy + half * 0.38:.1f} L {cx + half * 0.90:.1f} {cy + half * 0.52:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.2" stroke-linecap="round" opacity="0.84" />
  <circle id="{part("flash")}" class="icon-runtime-part" cx="{cx + half * 0.68:.1f}" cy="{cy:.1f}" r="{half * 0.40:.1f}" fill="none" stroke="{esc(stroke)}" stroke-width="2" opacity="0" />"""
    elif icon == "token":
        body = f"""
  <polygon id="{part("shell")}" points="{cx:.1f},{cy - half * 0.78:.1f} {cx + half * 0.68:.1f},{cy - half * 0.38:.1f} {cx + half * 0.68:.1f},{cy + half * 0.38:.1f} {cx:.1f},{cy + half * 0.78:.1f} {cx - half * 0.68:.1f},{cy + half * 0.38:.1f} {cx - half * 0.68:.1f},{cy - half * 0.38:.1f}"
        {filled_common} fill="{esc(symbol_fill)}" />
  <circle id="{part("core")}" class="icon-token-core" cx="{cx:.1f}" cy="{cy:.1f}" r="{half * 0.18:.1f}" fill="{esc(stroke)}" opacity="0.70" />
  <path id="{part("tickLeft")}" class="icon-token-tick" d="M {cx - half * 0.44:.1f} {cy:.1f} H {cx - half * 0.26:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2" stroke-linecap="round" opacity="0.70" />
  <path id="{part("tickRight")}" class="icon-token-tick" d="M {cx + half * 0.26:.1f} {cy:.1f} H {cx + half * 0.44:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2" stroke-linecap="round" opacity="0.70" />
  <path id="{part("tickTop")}" class="icon-token-tick" d="M {cx:.1f} {cy - half * 0.50:.1f} V {cy - half * 0.34:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2" stroke-linecap="round" opacity="0.58" />
  <path id="{part("tickBottom")}" class="icon-token-tick" d="M {cx:.1f} {cy + half * 0.34:.1f} V {cy + half * 0.50:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2" stroke-linecap="round" opacity="0.58" />
  <circle id="{part("halo")}" class="icon-runtime-part" cx="{cx:.1f}" cy="{cy:.1f}" r="{half * 0.70:.1f}" fill="none" stroke="{esc(stroke)}" stroke-width="2" opacity="0" />"""
    elif icon == "output":
        card_fill = icon_surface_fill(fill, stroke)
        body = f"""
  <rect id="{part("card")}" x="{cx - half * 0.78:.1f}" y="{cy - half * 0.72:.1f}" width="{half * 1.32:.1f}" height="{half * 1.36:.1f}" rx="{half * 0.18:.1f}"
        fill="{esc(card_fill)}" stroke="{esc(stroke)}" stroke-width="2.8" />
  <path id="{part("line1")}" class="icon-output-line" d="M {cx - half * 0.42:.1f} {cy - half * 0.28:.1f} H {cx + half * 0.22:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.2" stroke-linecap="round" opacity="0.82" />
  <path id="{part("line2")}" class="icon-output-line" d="M {cx - half * 0.42:.1f} {cy:.1f} H {cx + half * 0.10:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="2.2" stroke-linecap="round" opacity="0.82" />
  <path id="{part("check")}" class="icon-output-check" d="M {cx - half * 0.30:.1f} {cy + half * 0.34:.1f} L {cx - half * 0.08:.1f} {cy + half * 0.54:.1f} L {cx + half * 0.40:.1f} {cy + half * 0.04:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="3.0" stroke-linecap="round" stroke-linejoin="round" />
  <circle id="{part("flash")}" class="icon-runtime-part" cx="{cx + half * 0.20:.1f}" cy="{cy + half * 0.22:.1f}" r="{half * 0.62:.1f}" fill="none" stroke="{esc(stroke)}" stroke-width="2" opacity="0" />"""
    else:
        body = f"""
  <rect x="{cx - half * 0.72:.1f}" y="{cy - half * 0.72:.1f}" width="{half * 1.44:.1f}" height="{half * 1.44:.1f}" rx="{half * 0.18:.1f}" {filled_common} fill="{esc(symbol_fill)}" />
  <path d="M {cx - half * 0.36:.1f} {cy - half * 0.16:.1f} H {cx + half * 0.36:.1f}" {common} />
  <path d="M {cx - half * 0.36:.1f} {cy + half * 0.22:.1f} H {cx + half * 0.36:.1f}" {common} />"""
    return f"""
<g id="{root_id}" class="{wrap_class} semantic-icon-root semantic-icon-{esc(icon)}" data-icon="{esc(icon)}" data-node-id="{esc(box.node_id)}" opacity="0.94">
{halo}
{icon_open}
{accent}
{illustration}
{body}
{semantic_motion}
{icon_close}
</g>"""


def render_node_burst(box: NodeBox, role: str, stroke: str, index: int, motion: SceneMotion, effect: EffectConfig) -> str:
    if role not in {"agent", "output", "risk"} and effect.accent != "ripple":
        return ""
    if not effect_active(motion, effect) or effect.preset not in {"glow-breathe", "pop", "ripple", "icon-pulse"}:
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
    if node.shape == "decision":
        points = diamond_points(box)
        return f"""  <polygon class="node-surface node-decision-shape" points="{points}"
        fill="{esc(fill)}" stroke="{esc(stroke)}" stroke-width="{stroke_width:.1f}" />"""
    if not aurora_nodes_enabled(style) or node.fill:
        return f"""  <rect class="node-surface" x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" rx="{radius:.1f}"
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
  <rect class="node-surface" x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" rx="{radius:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="{stroke_width:.1f}" opacity="{border_opacity:.2f}" />"""


def diamond_points(box: NodeBox, padding: float = 0.0) -> str:
    cx, cy = box.center
    half_w = max(0.0, box.w / 2 - padding)
    half_h = max(0.0, box.h / 2 - padding)
    return (
        f"{cx:.1f},{cy - half_h:.1f} "
        f"{cx + half_w:.1f},{cy:.1f} "
        f"{cx:.1f},{cy + half_h:.1f} "
        f"{cx - half_w:.1f},{cy:.1f}"
    )


def render_node(
    node: Node,
    style: Dict[str, Any],
    index: int,
    motion: SceneMotion,
    policy: MotionPolicy,
    node_motion_rank: Optional[int],
    suppress_icon_motion: bool = False,
) -> str:
    box = node_box(node)
    node_effect = channel_effect(motion, style, "node", node.effect)
    if (
        effect_active(motion, node_effect)
        and node_effect.preset in CONTINUOUS_NODE_MOTION
        and not policy_allows(node_motion_rank, policy.max_active_pulse_nodes)
    ):
        node_effect = effect_with_preset(node_effect, "fade")
    node_mode = node_effect.preset
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
    icon_system = resolve_icon_system(style)
    text_offset, text_width = node_text_region(
        box.w,
        icon_system=icon_system,
        has_icon=bool(node.icon),
        decision=node.shape == "decision",
    )
    text_x = box.x + text_offset
    badge = ""
    if node.step is not None:
        badge = render_step_badge(box.x + 18, box.y + 18, node.step, stroke, fill)
    delay = motion_delay(index, motion, "node")
    float_duration = scaled_duration(5.4 + (index % 3) * 0.45, motion)
    burst = render_node_burst(box, node.role, stroke, index, motion, node_effect)
    icon = render_semantic_icon(
        node.icon,
        box,
        stroke,
        fill,
        text,
        motion,
        node_effect,
        index,
        suppress_icon_motion=suppress_icon_motion,
        style=style,
    )
    enter_markup = ""
    float_markup = ""
    glow_markup = ""
    node_opacity = "1" if motion.profile == "off" else "0"
    if effect_active(motion, node_effect):
        if runtime_loop_active(motion):
            enter_markup = '  <set attributeName="opacity" to="1" />'
        else:
            enter_markup = f'  <animate attributeName="opacity" values="0;1" dur="{seconds(scaled_duration(0.55, motion))}" begin="{seconds(delay)}" fill="freeze" />'
        if node_mode in {"float", "glow-breathe", "pop", "icon-pulse", "pulse", "ripple"}:
            float_markup = f"""  <animateTransform attributeName="transform" type="translate"
        values="{node_translate_values(motion, index, node_mode)}" dur="{seconds(float_duration)}" begin="{seconds(delay + 0.7)}"
        repeatCount="indefinite" additive="sum" />"""
        if node_mode in {"glow-breathe", "pop", "pulse", "icon-pulse", "ripple", "status-blink"}:
            glow_opacity = 0.24 * clamp(motion.intensity, 0.25, 1.7)
            if node.shape == "decision":
                glow_markup = f"""  <polygon class="node-glow" points="{diamond_points(box, padding=-4)}"
        fill="none" stroke="{esc(stroke)}" stroke-width="1.2" opacity="0.12" filter="url(#soft-glow)">
    <animate attributeName="opacity" values="0.08;{glow_opacity:.2f};0.08" dur="{seconds(scaled_duration(3.9 + (index % 4) * 0.35, motion))}" begin="{seconds(delay + 0.2)}" repeatCount="indefinite" />
    <animate attributeName="stroke-width" values="1.0;{1.0 + 1.4 * clamp(motion.intensity, 0.25, 1.7):.1f};1.0" dur="{seconds(scaled_duration(3.9 + (index % 4) * 0.35, motion))}" begin="{seconds(delay + 0.2)}" repeatCount="indefinite" />
  </polygon>"""
            else:
                glow_markup = f"""  <rect class="node-glow" x="{box.x - 4:.1f}" y="{box.y - 4:.1f}" width="{box.w + 8:.1f}" height="{box.h + 8:.1f}" rx="{radius + 4:.1f}"
        fill="none" stroke="{esc(stroke)}" stroke-width="1.2" opacity="0.12" filter="url(#soft-glow)">
    <animate attributeName="opacity" values="0.08;{glow_opacity:.2f};0.08" dur="{seconds(scaled_duration(3.9 + (index % 4) * 0.35, motion))}" begin="{seconds(delay + 0.2)}" repeatCount="indefinite" />
    <animate attributeName="stroke-width" values="1.0;{1.0 + 1.4 * clamp(motion.intensity, 0.25, 1.7):.1f};1.0" dur="{seconds(scaled_duration(3.9 + (index % 4) * 0.35, motion))}" begin="{seconds(delay + 0.2)}" repeatCount="indefinite" />
  </rect>"""
    else:
        enter_markup = "" if motion.profile == "off" else '  <set attributeName="opacity" to="1" />'
    return f"""
<g id="node-{esc(box.node_id)}" class="node motion-node" data-role="{esc(node.role)}" opacity="{node_opacity}">
{enter_markup}
{float_markup}
{burst}
{glow_markup}
{render_node_surface(node, box, radius, fill, stroke, stroke_width, style, index)}
{icon}
{badge}
  {render_text_block(text_x, box.y, text_width, box.h, label, caption, text)}
</g>"""


def render_group(
    group: Group,
    style: Dict[str, Any],
    index: int,
    motion: SceneMotion,
    policy: MotionPolicy,
    group_motion_rank: Optional[int],
) -> str:
    x, y, w, h = group.bounds
    group_effect = channel_effect(motion, style, "group", group.effect)
    if (
        effect_active(motion, group_effect)
        and group_effect.preset in SCANNING_GROUP_MOTION
        and not policy_allows(group_motion_rank, policy.max_scanning_groups)
    ):
        group_effect = effect_with_preset(group_effect, "soft-reveal")
    group_mode = group_effect.preset
    role = role_style(style, group.role)
    stroke = group.stroke or role.get("stroke", "#94a3b8")
    fill = group.fill or role.get("fill", "none")
    label = group.label
    muted = style.get("canvas", {}).get("muted", "#5b6778")
    delay = motion_delay(index, motion, "group")
    group_opacity = "1" if motion.profile == "off" else "0"
    enter_markup = "" if motion.profile == "off" else '<set attributeName="opacity" to="1" />'
    dash_markup = ""
    scan_markup = ""
    corner_markup = ""
    if effect_active(motion, group_effect):
        enter_markup = f'<animate attributeName="opacity" values="0;1" dur="{seconds(scaled_duration(0.7, motion))}" begin="{seconds(delay)}" fill="freeze" />'
        if group_mode in {"marching-ants", "border-scan"}:
            dash_markup = f'<animate attributeName="stroke-dashoffset" values="0;-34" dur="{seconds(scaled_duration(5.2 + index * 0.4, motion))}" begin="{seconds(delay)}" repeatCount="indefinite" />'
        if group_mode == "border-scan":
            scan_markup = f"""
  <rect class="group-border-scan" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="22"
        fill="none" stroke="{esc(stroke)}" stroke-width="3.4" stroke-linecap="round"
        stroke-dasharray="{max(80, min(180, (w + h) * 0.12)):.1f} {max(260, (w + h) * 0.7):.1f}" opacity="0.72" filter="url(#soft-glow)">
    <animate attributeName="stroke-dashoffset" values="0;-{2 * (w + h):.1f}" dur="{seconds(scaled_duration(6.8 + index * 0.35, motion))}" begin="{seconds(delay + 0.1)}" repeatCount="indefinite" />
  </rect>"""
        if group_mode == "corner-pulse":
            line = max(24, min(54, min(w, h) * 0.16))
            corner_markup = f"""
  <path class="group-corner-pulse" d="M {x:.1f} {y + line:.1f} V {y:.1f} H {x + line:.1f}
       M {x + w - line:.1f} {y:.1f} H {x + w:.1f} V {y + line:.1f}
       M {x + w:.1f} {y + h - line:.1f} V {y + h:.1f} H {x + w - line:.1f}
       M {x + line:.1f} {y + h:.1f} H {x:.1f} V {y + h - line:.1f}"
       fill="none" stroke="{esc(stroke)}" stroke-width="4" stroke-linecap="round" opacity="0.28">
    <animate attributeName="opacity" values="0.22;0.86;0.22" dur="{seconds(scaled_duration(3.2, motion))}" begin="{seconds(delay + 0.25)}" repeatCount="indefinite" />
  </path>"""
    dash_line = f"    {dash_markup}\n" if dash_markup else ""
    enter_line = f"  {enter_markup}\n" if enter_markup else ""
    return f"""
<g id="group-{esc(group.group_id)}" class="group" opacity="{group_opacity}">
{enter_line}  <rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="22"
        fill="{esc(fill)}" fill-opacity="0.34" stroke="{esc(stroke)}" stroke-width="1.6" stroke-dasharray="9 8">
{dash_line}  </rect>
{scan_markup}
{corner_markup}
  <text x="{x + 18:.1f}" y="{y + 30:.1f}" class="group-label" fill="{esc(muted)}">{esc(label)}</text>
</g>"""


def edge_points(edge: Edge, nodes: Dict[str, NodeBox]) -> Tuple[Point, Point]:
    if len(edge.points) >= 2:
        points = trim_route_endpoints(compact_points(list(edge.points)))
        return points[0], points[-1]
    source = nodes.get(edge.source)
    target = nodes.get(edge.target)
    if not source or not target:
        return (0, 0), (0, 0)
    return anchor_between(source, target)


def route_points(edge: Edge, nodes: Dict[str, NodeBox]) -> List[Point]:
    if len(edge.points) >= 2:
        return trim_route_endpoints(compact_points(list(edge.points)))
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


def edge_label_has_clearance(edge: Edge, start: Point, end: Point) -> bool:
    """Keep short horizontal connectors readable by omitting cramped labels."""

    if not edge.label:
        return False
    if edge.route != "straight" or abs(start[1] - end[1]) > 1:
        return True
    available = abs(end[0] - start[0])
    estimated_text_width = len(edge.label) * 7 + 18
    return available >= max(48, estimated_text_width)


def render_edge(
    edge: Edge,
    nodes: Dict[str, NodeBox],
    style: Dict[str, Any],
    index: int,
    motion: SceneMotion,
    policy: MotionPolicy,
    edge_motion_rank: Optional[int],
    particle_motion_rank: Optional[int],
) -> str:
    start, end = edge_points(edge, nodes)
    path = edge_path(edge, nodes)
    edge_effect = canonical_edge_effect(channel_effect(motion, style, "edge", edge.effect))
    role = role_style(style, edge.role)
    stroke = edge.stroke or role.get("stroke", "#64748b")
    width = float(edge.width if edge.width is not None else style.get("edge", {}).get("width", 2.4))
    duration = edge.motion.duration or style.get("edge", {}).get("duration", "4.2s")
    try:
        duration_value = float(str(duration).rstrip("s"))
    except ValueError:
        duration_value = 4.2
    mid_x = (start[0] + end[0]) / 2
    label_offset = -14 if edge.route == "straight" else (-18 if index % 2 == 0 else 22)
    mid_y = (start[1] + end[1]) / 2 + label_offset
    label = edge.label if edge_label_has_clearance(edge, start, end) else ""
    marker_id = f"arrow-{index}"
    marker_orient = "auto-start-reverse" if edge.direction == "bidirectional" else "auto"
    marker_attributes = (
        ""
        if edge.direction == "undirected"
        else f' marker-start="url(#{marker_id})" marker-end="url(#{marker_id})"'
        if edge.direction == "bidirectional"
        else f' marker-end="url(#{marker_id})"'
    )
    draw_begin = motion_delay(index, motion, "edge") + edge.motion.delay
    badge = ""
    if edge.step is not None:
        badge = render_step_badge(mid_x - 22, mid_y - 5, edge.step, stroke, "#ffffff")
    edge_mode = edge_effect.preset if edge.motion.enabled else "none"
    if edge.motion.duration is None:
        if edge_mode == "packet-flow":
            duration_value = 1.65
        elif edge_mode == "comet-flow":
            duration_value = 1.85
        elif edge_mode == "stream-flow":
            duration_value = 1.35
    edge_is_active = effect_active(motion, edge_effect) and edge.motion.enabled
    if edge_is_active and edge_mode in CONTINUOUS_EDGE_MOTION and not policy_allows(edge_motion_rank, policy.max_active_flow_edges):
        edge_effect = effect_with_preset(edge_effect, "draw")
        edge_mode = edge_effect.preset
        edge_is_active = effect_active(motion, edge_effect) and edge.motion.enabled
    particle_allowed = policy_allows(particle_motion_rank, policy.max_particle_edges)
    if edge_is_active and edge_mode in PARTICLE_EDGE_MOTION and not particle_allowed:
        edge_effect = effect_with_preset(edge_effect, "draw")
        edge_mode = edge_effect.preset
        edge_is_active = effect_active(motion, edge_effect) and edge.motion.enabled
    draw_markup = f"""  <path class="edge-draw" d="{path}" fill="none" stroke="{esc(stroke)}" stroke-width="{width:.1f}" pathLength="1"
        stroke-dasharray="1" stroke-dashoffset="0"{marker_attributes} />"""
    flow_markup = ""
    motion_markup = ""
    if edge_is_active and edge_mode in DRAW_ENTRY_EDGE_MOTION:
        draw_markup = f"""  <path class="edge-draw" d="{path}" fill="none" stroke="{esc(stroke)}" stroke-width="{width:.1f}" pathLength="1"
        stroke-dasharray="1" stroke-dashoffset="1"{marker_attributes}>
    <animate attributeName="stroke-dashoffset" values="1;0" dur="{seconds(scaled_duration(0.9, motion))}" begin="{seconds(draw_begin)}" fill="freeze" />
  </path>"""
    if edge_is_active and edge_mode == "stream-flow":
        stream_duration = scaled_duration(max(1.35, duration_value * 0.72), motion)
        flow_markup = f"""  <path class="edge-flow edge-flow-stream-flow" d="{path}" fill="none" stroke="{esc(stroke)}" stroke-width="{max(1.2, width * 0.86):.1f}"
        stroke-linecap="round" stroke-dasharray="8 14" opacity="0.58">
    <animate attributeName="stroke-dashoffset" values="0;-44" dur="{seconds(stream_duration)}" begin="{seconds(-((index * 0.11 + edge.motion.delay) % max(stream_duration, 0.01)))}" repeatCount="indefinite" />
  </path>"""
    if edge_is_active and edge_mode in PARTICLE_EDGE_MOTION and particle_allowed:
        particles = []
        intensity = clamp(motion.intensity, 0.25, 1.8) * motion_area_scale(policy)
        particle_shape = "solid-dot"
        radii = particle_radii(edge_mode, particle_shape, edge_effect, policy)
        base_begin = -((index * 0.19 + edge.motion.delay) % duration_value)
        for particle_index, radius in enumerate(radii):
            if edge_mode == "comet-flow":
                begin = base_begin + particle_index * 0.075
                opacity = (1.0, 0.62, 0.38, 0.2)[particle_index]
                particle_class = "edge-particle edge-comet edge-comet-head" if particle_index == 0 else "edge-particle edge-comet edge-comet-tail"
            else:
                begin = base_begin
                opacity = 0.92
                particle_class = "edge-particle edge-packet"
            particles.append(
                    f"""  <circle class="{particle_class}" r="{radius * intensity:.1f}" fill="{esc(stroke)}" stroke="none" opacity="{opacity:.2f}">
    <animateMotion dur="{seconds(scaled_duration(duration_value, motion))}" repeatCount="indefinite" path="{path}" begin="{seconds(begin)}" />
    <animate attributeName="opacity" values="0;{opacity:.2f};0" dur="{seconds(scaled_duration(duration_value, motion))}" begin="{seconds(begin)}" repeatCount="indefinite" />
  </circle>"""
            )
        motion_markup = "\n".join(particles)
    label_static = not edge_is_active or edge_mode in CONTINUOUS_EDGE_MOTION or runtime_loop_active(motion)
    label_opacity = "1" if label_static else "0"
    label_motion = ""
    if not label_static and label:
        label_motion = f'<animate attributeName="opacity" values="0;1" dur="{seconds(scaled_duration(0.45, motion))}" begin="{seconds(motion_delay(index, motion, "label") + edge.motion.delay)}" fill="freeze" />'
    label_motion_line = f"    {label_motion}\n" if label_motion else ""
    label_text = f"    {esc(label)}" if label else ""
    return f"""
<defs>
  <marker id="{marker_id}" markerWidth="12" markerHeight="12" viewBox="0 0 12 12" refX="9" refY="6" orient="{marker_orient}" markerUnits="userSpaceOnUse">
    <path d="M 1 1.5 L 11 6 L 1 10.5 z" fill="{esc(stroke)}" />
  </marker>
</defs>
<g class="edge" data-role="{esc(edge.role)}">
  <path class="edge-base" d="{path}" fill="none" stroke="{esc(stroke)}" stroke-width="{max(1, width - 0.7):.1f}" opacity="0.24" />
{draw_markup}
{flow_markup}
{motion_markup}
{badge}
  <text x="{mid_x:.1f}" y="{mid_y:.1f}" class="edge-label" fill="{esc(style.get("canvas", {}).get("muted", "#5b6778"))}" opacity="{label_opacity}">
{label_motion_line}{label_text}
  </text>
</g>"""


def render_svg(
    spec: Any,
    style: Dict[str, Any],
    *,
    animation_mode: str = "smil",
    suppress_icon_motion_node_ids: Optional[Iterable[str]] = None,
) -> str:
    scene = spec if isinstance(spec, Scene) else compile_scene(spec)
    if scene.icon_system:
        style = deep_merge(style, {"icon_system": scene.icon_system})
    if animation_mode not in {"smil", "runtime-stage"}:
        raise ValueError('animation_mode must be "smil" or "runtime-stage"')
    runtime_stage = animation_mode == "runtime-stage"
    suppress_icon_motion_node_ids = set(suppress_icon_motion_node_ids or ())
    if runtime_stage:
        suppress_icon_motion_node_ids.update(node.node_id for node in scene.nodes)
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
    if runtime_stage:
        motion = replace(
            motion,
            profile="off",
            intensity=0.0,
            node="none",
            edge="none",
            group="none",
            reduced_motion="static",
            edge_effect=EffectConfig("static"),
            node_effect=EffectConfig("static"),
            group_effect=EffectConfig("static"),
            title_effect=EffectConfig("static"),
        )
    policy = scene.motion_policy
    title_effect = channel_effect(motion, style, "title")
    edge_modes = []
    for index, edge in enumerate(scene.edges, start=1):
        effect = canonical_edge_effect(channel_effect(motion, style, "edge", edge.effect))
        edge_modes.append((index, effect, effect.preset if edge.motion.enabled else "none"))
    edge_motion_ranks = ranked_motion_modes(edge_modes, motion, CONTINUOUS_EDGE_MOTION)
    particle_motion_ranks = ranked_motion_modes(edge_modes, motion, PARTICLE_EDGE_MOTION)
    node_modes = []
    for index, node in enumerate(scene.nodes, start=1):
        effect = channel_effect(motion, style, "node", node.effect)
        node_modes.append((index, effect, effect.preset))
    node_motion_ranks = ranked_motion_modes(node_modes, motion, CONTINUOUS_NODE_MOTION)
    group_modes = []
    for index, group in enumerate(scene.groups, start=1):
        effect = channel_effect(motion, style, "group", group.effect)
        group_modes.append((index, effect, effect.preset))
    group_motion_ranks = ranked_motion_modes(group_modes, motion, SCANNING_GROUP_MOTION)

    groups_markup = "\n".join(
        render_group(group, style, index, motion, policy, group_motion_ranks.get(index))
        for index, group in enumerate(scene.groups, start=1)
    )
    edges_markup = "\n".join(
        render_edge(edge, nodes, style, index, motion, policy, edge_motion_ranks.get(index), particle_motion_ranks.get(index))
        for index, edge in enumerate(scene.edges, start=1)
    )
    nodes_markup = "\n".join(
        render_node(
            node,
            style,
            index,
            motion,
            policy,
            node_motion_ranks.get(index),
            suppress_icon_motion=node.node_id in suppress_icon_motion_node_ids,
        )
        for index, node in enumerate(scene.nodes, start=1)
    )
    defs_markup = render_style_defs(style, grid)
    grid_opacity = float(style_effect(style, "grid_opacity", 0.52))
    frame_opacity = float(style_effect(style, "frame_opacity", 1.0))

    title_is_breathing = effect_active(motion, title_effect) and title_effect.preset == "breathe"
    title_style_attr = ' style="animation:none"' if motion.profile == "off" or title_is_breathing or runtime_loop_active(motion) else ""
    title_text_opacity = "1" if motion.profile == "off" or title_is_breathing or runtime_loop_active(motion) else "0"
    if title_is_breathing:
        title_text_anim = f'<animate attributeName="opacity" values="0.86;1;0.86" dur="{seconds(scaled_duration(3.6, motion))}" begin="0s" repeatCount="indefinite" />'
    elif motion.profile == "off":
        title_text_anim = ""
    else:
        title_text_anim = '<animate attributeName="opacity" values="0;1" dur="0.65s" begin="0.08s" fill="freeze" />'
    if runtime_loop_active(motion):
        subtitle_anim = ""
    elif motion.profile == "off":
        subtitle_anim = ""
    else:
        subtitle_anim = '<animate attributeName="opacity" values="0;1" dur="0.65s" begin="0.28s" fill="freeze" />'
    illustrated_css = ""
    if illustrated_icons_enabled(style):
        illustrated_css = """  .semantic-icon-illustrated-v1 .illustrated-icon-backplate { pointer-events: none; }
  .semantic-icon-illustrated-v1 .illustrated-icon-wash { mix-blend-mode: multiply; }
  .semantic-icon-illustrated-v1 .illustrated-icon-bubble-halo,
  .semantic-icon-illustrated-v1 .illustrated-icon-dot,
  .semantic-icon-illustrated-v1 .illustrated-icon-orbit-dot,
  .semantic-icon-illustrated-v1 .illustrated-icon-mark { vector-effect: non-scaling-stroke; }
"""
    title_motion_markup = ""
    if effect_active(motion, title_effect) and title_effect.preset == "handwrite-reveal":
        title_motion_markup = f"""
<path class="title-handwrite" d="M 92 98 C 188 108, 310 100, 428 104" fill="none"
      stroke="{esc(title_style.get("accent", "#2563eb"))}" stroke-width="4" stroke-linecap="round"
      pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" opacity="0.78">
  <animate attributeName="stroke-dashoffset" values="1;0" dur="{seconds(scaled_duration(1.35, motion))}" begin="0.18s" fill="freeze" />
  <animate attributeName="opacity" values="0;0.78;0.42" dur="{seconds(scaled_duration(2.4, motion))}" begin="0.18s" fill="freeze" />
</path>"""
    elif effect_active(motion, title_effect) and title_effect.preset == "highlight-sweep":
        title_motion_markup = f"""
<rect class="title-sweep" x="72" y="46" width="0" height="56" rx="16" fill="{esc(title_style.get("accent", "#2563eb"))}" opacity="0.16">
  <animate attributeName="width" values="0;360;0" dur="{seconds(scaled_duration(3.2, motion))}" begin="0.34s" repeatCount="indefinite" />
  <animate attributeName="x" values="72;72;432" dur="{seconds(scaled_duration(3.2, motion))}" begin="0.34s" repeatCount="indefinite" />
</rect>"""
    title_text_anim_line = f"  {title_text_anim}\n" if title_text_anim else ""
    subtitle_anim_line = f"  {subtitle_anim}\n" if subtitle_anim else ""

    data_motion = scene.motion if runtime_stage else motion
    data_title_effect = channel_effect(data_motion, style, "title")
    data_edge_effect = canonical_edge_effect(channel_effect(data_motion, style, "edge"))
    resolved_icon_system = resolve_icon_system(style)
    icon_system_attr = f' data-icon-system="{esc(resolved_icon_system)}"'
    resolved_icon_system_version = icon_system_version(resolved_icon_system)
    if resolved_icon_system_version is not None:
        icon_system_attr += f' data-icon-system-version="{esc(resolved_icon_system_version)}"'

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="diagram-title diagram-desc" data-motion-profile="{esc(data_motion.profile)}" data-motion-sequence="{esc(data_motion.sequence)}" data-motion-edge="{esc(data_edge_effect.preset)}" data-motion-node="{esc(data_motion.node)}" data-motion-group="{esc(data_motion.group)}" data-motion-title="{esc(data_title_effect.preset)}" data-motion-reduced="{esc(data_motion.reduced_motion)}"{icon_system_attr}>
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
  .edge-draw, .edge-base {{ stroke-linecap: butt; stroke-linejoin: round; }}
  .edge-particle {{ filter: url(#particle-glow); }}
  .edge-arrow-particle {{ filter: url(#particle-glow); }}
  .semantic-icon {{ vector-effect: non-scaling-stroke; }}
{illustrated_css}  .semantic-icon-breathe {{ transform-box: fill-box; transform-origin: center; animation: semanticIconBreathe 2.8s ease-in-out infinite; }}
  .icon-breathe-halo {{ pointer-events: none; filter: url(#particle-glow); }}
  .node-glow, .node-burst {{ pointer-events: none; }}
  #title-accent {{ transform-origin: 50px 70px; animation: titlePulse 4.8s ease-in-out infinite; }}
  #title-highlight {{ transform-origin: 252px 74px; animation: titleSlide 5.6s ease-in-out infinite; }}
  @keyframes titlePulse {{ 0%, 100% {{ opacity: 0.76; }} 50% {{ opacity: 1; }} }}
  @keyframes titleSlide {{ 0%, 100% {{ transform: translateX(0); opacity: 0.9; }} 50% {{ transform: translateX(8px); opacity: 1; }} }}
  @keyframes semanticIconBreathe {{ 0%, 100% {{ transform: scale(0.96); opacity: 0.72; }} 50% {{ transform: scale(1.08); opacity: 1; }} }}
  @media (prefers-reduced-motion: reduce) {{
    #title-accent, #title-highlight, .semantic-icon-breathe {{ animation: none; }}
  }}
</style>
<rect width="100%" height="100%" fill="{esc(background)}" />
{defs_markup}
<rect width="100%" height="100%" fill="url(#grid)" opacity="{grid_opacity:.2f}" />
<rect x="28" y="26" width="{width - 56}" height="{height - 52}" rx="26" fill="none" stroke="{esc(style.get("roles", {}).get("neutral", {}).get("stroke", "#94a3b8"))}" stroke-width="1.4" opacity="{frame_opacity:.2f}" />
<rect id="title-accent" x="44" y="44" width="12" height="52" rx="6" fill="{esc(title_style.get("accent", "#2563eb"))}"{title_style_attr} />
<rect id="title-highlight" x="72" y="46" width="360" height="56" rx="16" fill="{esc(title_style.get("highlight", "#e8f1ff"))}"{title_style_attr} />
{title_motion_markup}
<text id="main-title" x="90" y="84" class="title" fill="{esc(text)}" opacity="{title_text_opacity}">
{title_text_anim_line}  {esc(title_text)}
</text>
<text x="74" y="126" class="subtitle" fill="{esc(muted)}" opacity="{title_text_opacity}">
{subtitle_anim_line}  {esc(subtitle)}
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
    main.motion-subtle .node-burst,
    main.motion-subtle .icon-breathe-halo {{ display: none; }}
    main.motion-subtle .edge-flow {{ opacity: 0.22; }}
    main.motion-subtle .semantic-icon-breathe {{ animation-duration: 4.2s; }}
    main.motion-off .edge-flow,
    main.motion-off .edge-particle,
    main.motion-off .node-burst,
    main.motion-off .node-glow,
    main.motion-off .icon-breathe-halo {{ display: none; }}
    main.motion-off .semantic-icon-breathe {{ animation: none !important; }}
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

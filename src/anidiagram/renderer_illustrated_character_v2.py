"""SVG serialization for the Illustrated 2.0.0 icon system."""

from __future__ import annotations

import html
from typing import Dict, Mapping

from .illustrated_character_icons import CharacterIconDefinition
from .icon_system import ILLUSTRATED_ICON_SYSTEM, ILLUSTRATED_ICON_SYSTEM_VERSION
from .illustrated_tokens import illustrated_geometry_tokens, illustrated_tokens_for_style
from .motion_manifest import icon_part_id


def render_character_v2_icon(
    definition: CharacterIconDefinition,
    node_id: str,
    cx: float,
    cy: float,
    size: float,
    tokens: Mapping[str, str] | None = None,
) -> str:
    """Render a 120 by 120 character scene at a node-local anchor."""

    palette = tokens or illustrated_tokens_for_style()
    geometry = illustrated_geometry_tokens()
    scale = size / float(geometry["view_box"])
    transform = f"translate({cx - size / 2:.1f} {cy - size / 2:.1f}) scale({scale:.4f})"
    markup = []
    for primitive in definition.primitives:
        attrs = dict(primitive.attrs)
        fill = _paint(attrs.pop("fill", "none"), palette)
        stroke = _paint(attrs.pop("stroke", "ink"), palette)
        stroke_width = html.escape(str(attrs.pop("stroke_width", geometry["default_stroke_width"])), quote=True)
        rest_opacity = html.escape(str(attrs.get("opacity", "1")), quote=True)
        part_id = html.escape(icon_part_id(node_id, primitive.part), quote=True)
        common = (
            f'id="{part_id}" class="illustrated-part illustrated-{primitive.part}" '
            f'data-rest-opacity="{rest_opacity}"'
        )
        attr_text = _attrs(attrs)
        markup.append(
            f'<{primitive.kind} {common} {attr_text} fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{stroke_width}" stroke-linecap="{geometry["stroke_linecap"]}" '
            f'stroke-linejoin="{geometry["stroke_linejoin"]}" />'
        )
    root_id = html.escape(icon_part_id(node_id, "root"), quote=True)
    role = html.escape(definition.semantic_role, quote=True)
    return (
        f'<g id="{root_id}" class="semantic-icon semantic-icon-illustrated" '
        f'data-icon-system="{ILLUSTRATED_ICON_SYSTEM}" data-icon-system-version="{ILLUSTRATED_ICON_SYSTEM_VERSION}" '
        f'data-semantic-role="{role}" '
        f'data-rest-opacity="1" transform="{transform}">\n'
        '    <g class="illustrated-character-motion-shell">\n      '
        + "\n      ".join(markup)
        + "\n    </g>\n  </g>"
    )


def _paint(token: str, palette: Mapping[str, str]) -> str:
    return "none" if token == "none" else palette.get(token, token)


def _attrs(attrs: Dict[str, str]) -> str:
    return " ".join(
        f'{html.escape(name.replace("_", "-"), quote=True)}="{html.escape(str(value), quote=True)}"'
        for name, value in attrs.items()
    )

"""SVG serialization for the experimental illustrated-character-v2 concepts."""

from __future__ import annotations

import html
from typing import Dict

from .illustrated_character_icons import CharacterIconDefinition
from .motion_manifest import icon_part_id


PALETTE = {
    "ink": "#283047",
    "paper": "#fffaf0",
    "mint": "#46caa0",
    "lavender": "#c9bbff",
    "lavender-dark": "#8067d8",
    "violet": "#8265d6",
    "peach": "#ffc39e",
    "sky": "#6fd6eb",
    "teal": "#43bdb7",
    "teal-dark": "#1c8f91",
    "coral": "#ff826e",
    "sun": "#ffd45e",
    "shadow": "#283047",
    "lavender-wash": "#eee9ff",
    "sky-wash": "#e8f8fb",
    "sun-wash": "#fff3d8",
    "mint-wash": "#e5f7ef",
    "none": "none",
}


def render_character_v2_icon(
    definition: CharacterIconDefinition,
    node_id: str,
    cx: float,
    cy: float,
    size: float,
) -> str:
    """Render a 120 by 120 character scene at a node-local anchor."""

    scale = size / 120
    transform = f"translate({cx - size / 2:.1f} {cy - size / 2:.1f}) scale({scale:.4f})"
    markup = []
    for primitive in definition.primitives:
        attrs = dict(primitive.attrs)
        fill = _paint(attrs.pop("fill", "none"))
        stroke = _paint(attrs.pop("stroke", "ink"))
        stroke_width = html.escape(str(attrs.pop("stroke_width", "3.4")), quote=True)
        rest_opacity = html.escape(str(attrs.get("opacity", "1")), quote=True)
        part_id = html.escape(icon_part_id(node_id, primitive.part), quote=True)
        common = (
            f'id="{part_id}" class="illustrated-character-part illustrated-character-v2-{primitive.part}" '
            f'data-rest-opacity="{rest_opacity}"'
        )
        attr_text = _attrs(attrs)
        markup.append(
            f'<{primitive.kind} {common} {attr_text} fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" />'
        )
    root_id = html.escape(icon_part_id(node_id, "root"), quote=True)
    role = html.escape(definition.semantic_role, quote=True)
    return (
        f'<g id="{root_id}" class="semantic-icon semantic-icon-illustrated-character-v2" '
        f'data-character-generation="v2-structured-concept" data-semantic-role="{role}" '
        f'data-rest-opacity="1" transform="{transform}">\n'
        '    <g class="illustrated-character-motion-shell">\n      '
        + "\n      ".join(markup)
        + "\n    </g>\n  </g>"
    )


def _paint(token: str) -> str:
    return PALETTE.get(token, token)


def _attrs(attrs: Dict[str, str]) -> str:
    return " ".join(
        f'{html.escape(name.replace("_", "-"), quote=True)}="{html.escape(str(value), quote=True)}"'
        for name, value in attrs.items()
    )

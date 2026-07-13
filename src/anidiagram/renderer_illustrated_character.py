"""SVG serialization for clean-room illustrated-character-v1 icons."""

from __future__ import annotations

import html
from typing import Dict

from .illustrated_character_icons import CharacterIconDefinition
from .motion_manifest import icon_part_id


PALETTE = {
    "ink": "#283047",
    "paper": "#fffdf6",
    "mint": "#49c99a",
    "lavender": "#c5b8f2",
    "violet": "#8265d6",
    "peach": "#ffd2b8",
    "sky": "#83d9ed",
    "teal": "#39b8b5",
    "orange": "#ff9e42",
    "sun": "#ffd45e",
}


def render_character_icon(definition: CharacterIconDefinition, node_id: str, cx: float, cy: float, size: float) -> str:
    """Render a registry definition at a node-local icon anchor."""

    scale = size / 100
    transform = f"translate({cx - size / 2:.1f} {cy - size / 2:.1f}) scale({scale:.4f})"
    markup = []
    for primitive in definition.primitives:
        attrs = dict(primitive.attrs)
        fill = PALETTE.get(attrs.pop("fill", "none"), "none")
        rest_opacity = html.escape(str(attrs.get("opacity", "1")), quote=True)
        part_id = html.escape(icon_part_id(node_id, primitive.part), quote=True)
        common = (
            f'id="{part_id}" class="illustrated-character-part illustrated-character-{primitive.part}" '
            f'data-rest-opacity="{rest_opacity}"'
        )
        if primitive.kind == "text":
            value = html.escape(attrs.pop("text", ""))
            attr_text = _attrs(attrs)
            markup.append(
                f'<text {common} {attr_text} fill="{fill}" text-anchor="middle" '
                'font-family="ui-sans-serif, system-ui" font-size="20" font-weight="700">'
                f"{value}</text>"
            )
            continue
        attr_text = _attrs(attrs)
        markup.append(
            f'<{primitive.kind} {common} {attr_text} fill="{fill}" stroke="{PALETTE["ink"]}" '
            'stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />'
        )
    root_id = html.escape(icon_part_id(node_id, "root"), quote=True)
    role = html.escape(definition.semantic_role, quote=True)
    return (
        f'<g id="{root_id}" class="semantic-icon semantic-icon-illustrated-character-v1" '
        f'data-semantic-role="{role}" data-rest-opacity="1" transform="{transform}">\n'
        '    <g class="illustrated-character-motion-shell">\n      '
        + "\n      ".join(markup)
        + "\n    </g>\n  </g>"
    )


def _attrs(attrs: Dict[str, str]) -> str:
    return " ".join(f'{html.escape(name, quote=True)}="{html.escape(str(value), quote=True)}"' for name, value in attrs.items())

"""Illustrated semantic icon registry for the high-fidelity runtime path.

The registry is intentionally data-only so renderers and manifest generation can
share stable part names without tying the core DiagramScript schema to a single
visual icon implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple


COMMON_ILLUSTRATED_PARTS: Tuple[str, ...] = (
    "bubble",
    "bubbleHalo",
    "wash",
    "accentMark",
    "sparkle",
    "orbitDot",
)


@dataclass(frozen=True)
class IllustratedIconDefinition:
    icon: str
    semantic_role: str
    parts: Tuple[str, ...]
    colors: Dict[str, str]


_DEFAULT_COLORS = {
    "primary": "#4f7cff",
    "secondary": "#34c6a8",
    "tertiary": "#f6bd60",
    "surface": "#f8fbff",
    "bubble": "#ffffff",
    "wash": "#eaf4ff",
    "sparkle": "#ffd166",
}


ILLUSTRATED_ICON_REGISTRY: Dict[str, IllustratedIconDefinition] = {
    "agent": IllustratedIconDefinition(
        icon="agent",
        semantic_role="think-decide-act",
        parts=COMMON_ILLUSTRATED_PARTS
        + (
            "outlineLeft",
            "outlineRight",
            "centerLine",
            "branchLeft",
            "branchRight",
            "branchLower",
            "nodeTopLeft",
            "nodeTopRight",
            "nodeLeft",
            "nodeRight",
            "nodeCenter",
            "decisionToken",
            "pulse",
        ),
        colors={
            "primary": "#8b6fe8",
            "secondary": "#39c7b0",
            "tertiary": "#ffd166",
            "surface": "#f4f0ff",
            "wash": "#ebe5ff",
        },
    ),
    "api": IllustratedIconDefinition(
        icon="api",
        semantic_role="request-response-status",
        parts=COMMON_ILLUSTRATED_PARTS
        + ("leftEndpoint", "rightEndpoint", "requestToken", "responseToken", "targetRing", "status"),
        colors={
            "primary": "#3f7bd9",
            "secondary": "#ff7a90",
            "tertiary": "#35c9a9",
            "surface": "#eef5ff",
            "wash": "#e5f0ff",
        },
    ),
    "search": IllustratedIconDefinition(
        icon="search",
        semantic_role="scan-discover-lock",
        parts=COMMON_ILLUSTRATED_PARTS + ("lens", "handle", "scan", "result1", "result2", "target"),
        colors={
            "primary": "#e3972b",
            "secondary": "#35b9a5",
            "tertiary": "#6e8efb",
            "surface": "#fff7e6",
            "wash": "#fff0cc",
        },
    ),
    "database": IllustratedIconDefinition(
        icon="database",
        semantic_role="receive-write-commit",
        parts=COMMON_ILLUSTRATED_PARTS + ("lid", "body", "layer1", "layer2", "writeToken", "flash"),
        colors={
            "primary": "#2fac75",
            "secondary": "#61d394",
            "tertiary": "#f6bd60",
            "surface": "#ecfbf1",
            "wash": "#dff8e8",
        },
    ),
    "memory": IllustratedIconDefinition(
        icon="memory",
        semantic_role="record-recall-commit",
        parts=COMMON_ILLUSTRATED_PARTS
        + ("backCard", "frontCard", "trace1", "trace2", "trace3", "dot", "commitToken", "flash"),
        colors={
            "primary": "#35a86b",
            "secondary": "#76d5a3",
            "tertiary": "#7aa8ff",
            "surface": "#eaf8ef",
            "wash": "#dff6e8",
        },
    ),
    "tool": IllustratedIconDefinition(
        icon="tool",
        semantic_role="execute-transform-return",
        parts=COMMON_ILLUSTRATED_PARTS + ("chip", "glyph", "connector", "spark1", "spark2", "flash"),
        colors={
            "primary": "#df9b32",
            "secondary": "#ffcf6e",
            "tertiary": "#35b9a5",
            "surface": "#fff6df",
            "wash": "#ffedc1",
        },
    ),
    "token": IllustratedIconDefinition(
        icon="token",
        semantic_role="intent-carrier",
        parts=COMMON_ILLUSTRATED_PARTS + ("shell", "core", "tickLeft", "tickRight", "tickTop", "tickBottom", "halo"),
        colors={
            "primary": "#5b8cff",
            "secondary": "#35c9a9",
            "tertiary": "#ffd166",
            "surface": "#edf4ff",
            "wash": "#dfeaff",
        },
    ),
    "output": IllustratedIconDefinition(
        icon="output",
        semantic_role="compose-verify-reveal",
        parts=COMMON_ILLUSTRATED_PARTS + ("card", "line1", "line2", "check", "flash"),
        colors={
            "primary": "#2da36d",
            "secondary": "#51c991",
            "tertiary": "#6e8efb",
            "surface": "#edf9f1",
            "wash": "#dbf4e5",
        },
    ),
    "file": IllustratedIconDefinition(
        icon="file",
        semantic_role="parse-structure-lines",
        parts=COMMON_ILLUSTRATED_PARTS + ("sheet", "fold", "line1", "line2", "line3", "flash"),
        colors={
            "primary": "#e9775c",
            "secondary": "#7ccfc2",
            "tertiary": "#f6bd60",
            "surface": "#fff1eb",
            "wash": "#ffe2d8",
        },
    ),
    "folder": IllustratedIconDefinition(
        icon="folder",
        semantic_role="open-browse-select",
        parts=COMMON_ILLUSTRATED_PARTS + ("body", "tab", "fileLine", "openToken", "flash"),
        colors={
            "primary": "#d9902f",
            "secondary": "#35b9a5",
            "tertiary": "#ffcf6e",
            "surface": "#fff6df",
            "wash": "#ffedc1",
        },
    ),
    "cloud": IllustratedIconDefinition(
        icon="cloud",
        semantic_role="sync-upload-available",
        parts=COMMON_ILLUSTRATED_PARTS + ("shell", "uploadArrow", "dot1", "dot2", "dot3", "statusRing"),
        colors={
            "primary": "#44a8e8",
            "secondary": "#35c9a9",
            "tertiary": "#f6bd60",
            "surface": "#edf8ff",
            "wash": "#dff2ff",
        },
    ),
    "shield": IllustratedIconDefinition(
        icon="shield",
        semantic_role="scan-guard-approve",
        parts=COMMON_ILLUSTRATED_PARTS + ("shell", "check", "pulse", "scan"),
        colors={
            "primary": "#df6a86",
            "secondary": "#8b6fe8",
            "tertiary": "#ffd166",
            "surface": "#fff0f4",
            "wash": "#ffe0e8",
        },
    ),
}


def is_illustrated_style(style: Dict[str, Any]) -> bool:
    effects = style.get("effects", {})
    return style.get("icon_system") == "illustrated-v1" or (
        isinstance(effects, dict) and effects.get("icon_system") == "illustrated-v1"
    )


def illustrated_definition(icon: str) -> IllustratedIconDefinition:
    return ILLUSTRATED_ICON_REGISTRY.get(
        icon,
        IllustratedIconDefinition(
            icon=icon,
            semantic_role="generic-semantic-object",
            parts=COMMON_ILLUSTRATED_PARTS,
            colors=_DEFAULT_COLORS,
        ),
    )


def illustrated_palette(
    icon: str,
    style: Dict[str, Any],
    *,
    fallback_stroke: str,
    fallback_fill: str,
) -> Dict[str, str]:
    definition = illustrated_definition(icon)
    palette = dict(_DEFAULT_COLORS)
    palette.update(definition.colors)
    palette.setdefault("primary", fallback_stroke)
    palette.setdefault("surface", fallback_fill)

    illustration = style.get("illustration", {})
    if isinstance(illustration, dict):
        for key in ("bubble", "wash", "sparkle", "surface", "primary", "secondary", "tertiary"):
            if isinstance(illustration.get(key), str):
                palette[key] = illustration[key]
        icon_overrides = illustration.get("icons", {})
        if isinstance(icon_overrides, dict) and isinstance(icon_overrides.get(icon), dict):
            for key, value in icon_overrides[icon].items():
                if isinstance(value, str):
                    palette[key] = value
    return palette

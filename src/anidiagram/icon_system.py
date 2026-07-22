"""Resolution rules for supported semantic icon renderers."""

from __future__ import annotations

from typing import Any, Dict, Tuple


DEFAULT_ICON_SYSTEM = "illustrated-character-v1"
ILLUSTRATED_ICON_SYSTEM = "illustrated"
ILLUSTRATED_ICON_SYSTEM_VERSION = "2.4.0"
ICON_SYSTEM_ALIASES = {
    "illustrated-character-v2": ILLUSTRATED_ICON_SYSTEM,
}
ICON_SYSTEM_VERSIONS = {
    ILLUSTRATED_ICON_SYSTEM: ILLUSTRATED_ICON_SYSTEM_VERSION,
}
SUPPORTED_ICON_SYSTEMS = {
    "diagram-core-v1",
    ILLUSTRATED_ICON_SYSTEM,
    "illustrated-character-v1",
    "illustrated-character-v2",
    "illustrated-v1",
    "semantic-line-v1",
}


def icon_system_value(style: Dict[str, Any]) -> Tuple[Any, str]:
    """Return the configured icon-system value and its source path.

    Top-level configuration is authoritative.  ``effects.icon_system`` remains
    a compatibility input for existing profiles, while omitted values opt into
    the character system.
    """

    if "icon_system" in style:
        return style["icon_system"], "$.icon_system"
    effects = style.get("effects")
    if isinstance(effects, dict) and "icon_system" in effects:
        return effects["icon_system"], "$.effects.icon_system"
    return DEFAULT_ICON_SYSTEM, "$.icon_system"


def resolve_icon_system(style: Dict[str, Any]) -> str:
    value, path = icon_system_value(style)
    if not isinstance(value, str) or value not in SUPPORTED_ICON_SYSTEMS:
        supported = ", ".join(sorted(SUPPORTED_ICON_SYSTEMS))
        raise ValueError(f"{path}: expected one of: {supported}")
    return canonical_icon_system_id(value)


def canonical_icon_system_id(value: str) -> str:
    """Resolve a supported public id or legacy alias to its stable identity."""

    return ICON_SYSTEM_ALIASES.get(value, value)


def icon_system_version(value: str) -> str | None:
    """Return separately versioned metadata for a canonical icon-system id."""

    return ICON_SYSTEM_VERSIONS.get(canonical_icon_system_id(value))

"""Diagram Core theme-token resolution."""

import re
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple


_TOKEN_PATH = Path(__file__).resolve().parents[3] / "assets" / "diagram-core" / "tokens.css"

_APPROVED_DEFAULTS = MappingProxyType(
    {
        "--icon-surface-main": "#fffaf2",
        "--icon-surface-secondary": "#eef1f5",
        "--icon-surface-recessed": "#dfe5ec",
        "--icon-stroke": "#14213d",
        "--icon-detail": "#64748b",
        "--icon-accent": "#7c5ce7",
        "--icon-accent-secondary": "#45c5bd",
        "--icon-status-idle": "#94a3b8",
        "--icon-status-active": "#38bdf8",
        "--icon-status-success": "#35b66f",
        "--icon-status-warning": "#f3a53a",
        "--icon-status-error": "#e65b65",
    }
)
_STATUS_TOKENS = frozenset(
    token for token in _APPROVED_DEFAULTS if token.startswith("--icon-status-")
)
_HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?\Z")
_RGB_COLOR = re.compile(
    r"rgb\(\s*(?:(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})"
    r"|(\d{1,3})\s+(\d{1,3})\s+(\d{1,3}))\s*\)\Z",
    re.IGNORECASE,
)


def token_css() -> str:
    """Return the canonical Diagram Core token stylesheet."""

    return _TOKEN_PATH.read_text(encoding="utf-8")


def relative_luminance(color: str) -> float:
    """Return WCAG relative luminance for an opaque hex or rgb color."""

    channels = []
    for channel in _parse_opaque_color(color):
        normalized = channel / 255.0
        channels.append(
            normalized / 12.92
            if normalized <= 0.04045
            else ((normalized + 0.055) / 1.055) ** 2.4
        )
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(first: str, second: str) -> float:
    """Return the symmetric WCAG contrast ratio between two opaque colors."""

    first_luminance = relative_luminance(first)
    second_luminance = relative_luminance(second)
    lighter = max(first_luminance, second_luminance)
    darker = min(first_luminance, second_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def icon_tokens_for_style(
    style: Mapping[str, Any],
    role: Optional[str] = None,
) -> Mapping[str, str]:
    """Resolve an immutable Diagram Core token snapshot from an AniDiagram style."""

    if not isinstance(style, Mapping):
        raise ValueError("style must be a mapping")
    canvas = _required_mapping(style, "canvas")
    title = _required_mapping(style, "title")
    roles = _required_mapping(style, "roles")
    neutral = roles.get("neutral")
    if not isinstance(neutral, Mapping):
        raise ValueError("style.roles.neutral must be a mapping")
    selected = roles.get(role) if role is not None else neutral
    if not isinstance(selected, Mapping):
        selected = neutral

    resolved = {
        "--icon-surface-main": _required_color(selected, "fill", "style.roles"),
        "--icon-surface-secondary": _required_color(
            canvas,
            "background",
            "style.canvas",
        ),
        "--icon-surface-recessed": _required_color(canvas, "grid", "style.canvas"),
        "--icon-stroke": _required_color(canvas, "text", "style.canvas"),
        "--icon-detail": _required_color(canvas, "muted", "style.canvas"),
        "--icon-accent": _required_color(selected, "stroke", "style.roles"),
        "--icon-accent-secondary": _required_color(title, "accent", "style.title"),
    }
    resolved.update(
        (token, value)
        for token, value in _APPROVED_DEFAULTS.items()
        if token in _STATUS_TOKENS
    )

    overrides = style.get("icon_tokens", {})
    if not isinstance(overrides, Mapping):
        raise ValueError("style.icon_tokens must be a mapping")
    for token, value in overrides.items():
        if token not in _STATUS_TOKENS:
            raise ValueError("unsupported Diagram Core icon token override: {0}".format(token))
        _parse_opaque_color(value)
        resolved[token] = value
    return MappingProxyType(dict(resolved))


def _required_mapping(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    candidate = value.get(key)
    if not isinstance(candidate, Mapping):
        raise ValueError("style.{0} must be a mapping".format(key))
    return candidate


def _required_color(value: Mapping[str, Any], key: str, path: str) -> str:
    candidate = value.get(key)
    try:
        _parse_opaque_color(candidate)
    except ValueError as error:
        raise ValueError("{0}.{1}: {2}".format(path, key, error))
    return candidate


def _parse_opaque_color(color: Any) -> Tuple[int, int, int]:
    if not isinstance(color, str):
        raise ValueError("expected an opaque color string")
    if _HEX_COLOR.fullmatch(color):
        value = color[1:]
        if len(value) == 3:
            value = "".join(channel * 2 for channel in value)
        return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))

    match = _RGB_COLOR.fullmatch(color)
    if match is None:
        raise ValueError("expected #rgb, #rrggbb, or opaque rgb()")
    channels = tuple(int(channel) for channel in match.groups() if channel is not None)
    if any(channel > 255 for channel in channels):
        raise ValueError("rgb() channels must be integers from 0 to 255")
    return channels

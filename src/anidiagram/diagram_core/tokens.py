"""Diagram Core theme-token resolution."""

import re
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

from ..resources import resource_path


_TOKEN_PATH = resource_path("assets", "diagram-core", "tokens.css")

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
_TOKEN_CONTEXTS = ("blue", "dark", "warm", "green")
_TOKEN_CONTEXT_SELECTORS = {
    ":root": None,
    **{
        '[data-icon-theme="{0}"]'.format(context): context
        for context in _TOKEN_CONTEXTS
    },
}
_CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?\Z")
_RGB_COLOR = re.compile(
    r"rgb\(\s*(?:(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})"
    r"|(\d{1,3})\s+(\d{1,3})\s+(\d{1,3}))\s*\)\Z",
    re.IGNORECASE,
)


def token_css() -> str:
    """Return the canonical Diagram Core token stylesheet."""

    return _TOKEN_PATH.read_text(encoding="utf-8")


def _css_comment_end(source: str, index: int) -> int:
    end = source.find("*/", index + 2)
    if end < 0:
        raise ValueError("tokens.css has an unterminated comment")
    return end + 2


def _css_string_end(source: str, index: int) -> int:
    quote = source[index]
    index += 1
    while index < len(source):
        if source[index] == "\\":
            index += 2
        elif source[index] == quote:
            return index + 1
        else:
            index += 1
    raise ValueError("tokens.css has an unterminated string")


def _css_control(source: str, index: int, controls: frozenset) -> int:
    while index < len(source):
        if source.startswith("/*", index):
            index = _css_comment_end(source, index)
        elif source[index] in {"'", '"'}:
            index = _css_string_end(source, index)
        elif source[index] in controls:
            return index
        else:
            index += 1
    return index


def _css_block_end(source: str, opening: int) -> int:
    depth = 1
    index = opening + 1
    while index < len(source):
        if source.startswith("/*", index):
            index = _css_comment_end(source, index)
        elif source[index] in {"'", '"'}:
            index = _css_string_end(source, index)
        elif source[index] == "{":
            depth += 1
            index += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return index
            index += 1
        else:
            index += 1
    raise ValueError("tokens.css has an unterminated block")


def _token_declarations(source: str) -> Tuple[Tuple[str, str], ...]:
    without_comments = _CSS_COMMENT.sub("", source)
    if "{" in without_comments or "}" in without_comments:
        raise ValueError("token context rules must contain simple declarations")
    declarations = []
    for statement in without_comments.split(";"):
        if not statement.strip():
            continue
        if ":" not in statement:
            raise ValueError("token context declaration is missing a colon")
        name, value = (part.strip() for part in statement.split(":", 1))
        if not name.startswith("--icon-") or not value:
            raise ValueError("token context rules require --icon-* declarations")
        if "!important" in value.lower():
            raise ValueError("token context declarations cannot use !important")
        _parse_opaque_color(value)
        declarations.append((name, value))
    if not declarations:
        raise ValueError("token context selector has no icon declarations")
    return tuple(declarations)


def _mentions_token_context(source: str) -> bool:
    lowered = source.lower()
    return ":root" in lowered or "data-icon-theme" in lowered


def _top_level_css_rules(source: str) -> Tuple[Tuple[str, str], ...]:
    rules = []
    start = 0
    controls = frozenset({"{", ";"})
    while start < len(source):
        control = _css_control(source, start, controls)
        if control >= len(source):
            trailing = _CSS_COMMENT.sub("", source[start:]).strip()
            if trailing:
                raise ValueError("tokens.css has unsupported trailing syntax")
            break
        header = _CSS_COMMENT.sub("", source[start:control]).strip()
        if source[control] == ";":
            if _mentions_token_context(header):
                raise ValueError("token context selectors require declaration blocks")
            start = control + 1
            continue
        closing = _css_block_end(source, control)
        rules.append((header, source[control + 1 : closing]))
        start = closing + 1
    return tuple(rules)


def token_contexts(source: str) -> Tuple[Mapping[str, str], Mapping[str, Mapping[str, str]]]:
    """Resolve the four static review contexts using top-level CSS cascade order."""

    if not isinstance(source, str):
        raise ValueError("tokens.css source must be a string")
    defaults = {}
    contexts = {context: {} for context in _TOKEN_CONTEXTS}
    seen = set()
    for header, body in _top_level_css_rules(source):
        body_without_comments = _CSS_COMMENT.sub("", body)
        if header.startswith("@"):
            if _mentions_token_context(header) or _mentions_token_context(
                body_without_comments
            ):
                raise ValueError("token context selectors must be top-level")
        elif header in _TOKEN_CONTEXT_SELECTORS:
            seen.add(header)
            target = _TOKEN_CONTEXT_SELECTORS[header]
            declarations = dict(_token_declarations(body))
            if target is None:
                defaults.update(declarations)
                for context in contexts.values():
                    context.update(declarations)
            else:
                contexts[target].update(declarations)
        elif _mentions_token_context(header):
            raise ValueError("token context selectors must be exact top-level rules")
        elif _mentions_token_context(body_without_comments):
            raise ValueError("token context selectors must be top-level")

    missing = sorted(set(_TOKEN_CONTEXT_SELECTORS) - seen)
    if missing:
        raise ValueError("tokens.css is missing selector " + missing[0])
    immutable_contexts = {
        context: MappingProxyType(dict(values))
        for context, values in contexts.items()
    }
    return MappingProxyType(dict(defaults)), MappingProxyType(immutable_contexts)


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

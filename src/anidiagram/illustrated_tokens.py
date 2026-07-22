"""Current Illustrated visual-token loading and controlled style overrides."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .icon_system import ILLUSTRATED_ICON_SYSTEM, ILLUSTRATED_ICON_SYSTEM_VERSION


_TOKEN_PATH = Path(__file__).resolve().parents[2] / "assets" / "illustrated" / "tokens-2.4.0.json"
_HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}\Z")
_REQUIRED_GEOMETRY = {
    "view_box": 120,
    "default_stroke_width": 3.4,
    "stroke_linecap": "round",
    "stroke_linejoin": "round",
}


@lru_cache(maxsize=1)
def illustrated_token_document() -> Mapping[str, Any]:
    """Load and validate the canonical token document once."""

    payload = json.loads(_TOKEN_PATH.read_text(encoding="utf-8"))
    if payload.get("system") != ILLUSTRATED_ICON_SYSTEM:
        raise ValueError("Illustrated tokens system id is invalid")
    if payload.get("version") != ILLUSTRATED_ICON_SYSTEM_VERSION:
        raise ValueError("Illustrated tokens version is invalid")

    colors = payload.get("colors")
    if not isinstance(colors, dict) or not colors:
        raise ValueError("Illustrated tokens require a non-empty colors object")
    for token, value in colors.items():
        _validate_color(token, value)

    geometry = payload.get("geometry")
    if geometry != _REQUIRED_GEOMETRY:
        raise ValueError(
            "Illustrated geometry tokens cannot change within version {0}".format(
                ILLUSTRATED_ICON_SYSTEM_VERSION
            )
        )

    policy = payload.get("override_policy")
    if not isinstance(policy, dict) or policy.get("style_field") != "illustrated_tokens":
        raise ValueError("Illustrated token override policy is invalid")
    if policy.get("geometry_overrides") is not False:
        raise ValueError("Illustrated geometry overrides must remain disabled")
    allowed = policy.get("allowed_color_tokens")
    if not isinstance(allowed, list) or set(allowed) != set(colors):
        raise ValueError("Illustrated allowed color tokens must match the canonical palette")

    return MappingProxyType(
        {
            "system": payload["system"],
            "version": payload["version"],
            "token_revision": payload["token_revision"],
            "colors": MappingProxyType(dict(colors)),
            "geometry": MappingProxyType(dict(geometry)),
            "override_policy": MappingProxyType(
                {
                    "style_field": policy["style_field"],
                    "allowed_color_tokens": tuple(allowed),
                    "geometry_overrides": policy["geometry_overrides"],
                }
            ),
        }
    )


def illustrated_tokens_for_style(style: Mapping[str, Any] | None = None) -> Mapping[str, str]:
    """Return an immutable palette with optional explicit template overrides."""

    payload = illustrated_token_document()
    resolved = dict(payload["colors"])
    if style is None:
        return MappingProxyType(resolved)
    if not isinstance(style, Mapping):
        raise ValueError("style must be a mapping")

    overrides = style.get("illustrated_tokens", {})
    if not isinstance(overrides, Mapping):
        raise ValueError("style.illustrated_tokens must be a mapping")
    allowed = set(payload["override_policy"]["allowed_color_tokens"])
    for token, value in overrides.items():
        if token not in allowed:
            raise ValueError("unsupported Illustrated token override: {0}".format(token))
        _validate_color(token, value)
        resolved[token] = value
    return MappingProxyType(resolved)


def illustrated_geometry_tokens() -> Mapping[str, Any]:
    return MappingProxyType(dict(illustrated_token_document()["geometry"]))


def _validate_color(token: Any, value: Any) -> None:
    if not isinstance(token, str) or not token:
        raise ValueError("Illustrated color token names must be non-empty strings")
    if not isinstance(value, str) or _HEX_COLOR.fullmatch(value) is None:
        raise ValueError("Illustrated color token {0!r} must be #rrggbb".format(token))

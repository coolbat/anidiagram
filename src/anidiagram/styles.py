"""Style profile loading for DiagramScript rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .schema import KNOWN_ROLES, ValidationIssue
from .icon_system import DEFAULT_ICON_SYSTEM, SUPPORTED_ICON_SYSTEMS, resolve_icon_system
from .illustrated_tokens import illustrated_tokens_for_style


DEFAULT_STYLE: Dict[str, Any] = {
    "name": "minimal-light",
    "icon_system": DEFAULT_ICON_SYSTEM,
    "canvas": {
        "background": "#ffffff",
        "text": "#172033",
        "muted": "#5b6778",
        "grid": "#edf2f7",
    },
    "title": {
        "accent": "#2563eb",
        "highlight": "#e8f1ff",
    },
    "node": {
        "radius": 14,
        "stroke_width": 2,
        "fill_mode": "solid",
    },
    "edge": {
        "width": 2.4,
        "duration": "4.2s",
    },
    "roles": {
        "actor": {"stroke": "#f97316", "fill": "#fff7ed", "text": "#172033"},
        "source": {"stroke": "#0891b2", "fill": "#ecfeff", "text": "#172033"},
        "process": {"stroke": "#2563eb", "fill": "#eff6ff", "text": "#172033"},
        "agent": {"stroke": "#7c3aed", "fill": "#f5f3ff", "text": "#172033"},
        "memory": {"stroke": "#059669", "fill": "#ecfdf5", "text": "#172033"},
        "tool": {"stroke": "#d97706", "fill": "#fffbeb", "text": "#172033"},
        "output": {"stroke": "#16a34a", "fill": "#f0fdf4", "text": "#172033"},
        "risk": {"stroke": "#dc2626", "fill": "#fef2f2", "text": "#172033"},
        "neutral": {"stroke": "#94a3b8", "fill": "#f8fafc", "text": "#172033"},
    },
}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = json.loads(json.dumps(base))
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_style(path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    if not path:
        return json.loads(json.dumps(DEFAULT_STYLE))
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    issues = validate_style_profile(data)
    if issues:
        messages = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ValueError(f"style profile validation failed: {messages}")
    merged = deep_merge(DEFAULT_STYLE, data)
    merged["icon_system"] = resolve_icon_system(data)
    return merged


def role_style(style: Dict[str, Any], role: Optional[str]) -> Dict[str, str]:
    roles = style.get("roles", {})
    return dict(roles.get(role or "neutral", roles.get("neutral", {})))


def validate_style_profile(data: Dict[str, Any]) -> list:
    issues = []
    if not isinstance(data, dict):
        return [ValidationIssue("$", "expected an object", "type")]
    if "name" in data and not isinstance(data["name"], str):
        issues.append(ValidationIssue("$.name", "expected a string", "type"))
    if "icon_system" in data:
        _validate_icon_system(data["icon_system"], "$.icon_system", issues)
    if "illustrated_tokens" in data:
        try:
            illustrated_tokens_for_style(data)
        except ValueError as error:
            issues.append(ValidationIssue("$.illustrated_tokens", str(error), "token"))
    node = data.get("node", {})
    if node and not isinstance(node, dict):
        issues.append(ValidationIssue("$.node", "expected an object", "type"))
    elif isinstance(node, dict):
        fill_mode = node.get("fill_mode")
        if fill_mode is not None and fill_mode not in {"solid", "aurora"}:
            issues.append(ValidationIssue("$.node.fill_mode", "expected 'solid' or 'aurora'", "enum"))
    effects = data.get("effects", {})
    if effects and not isinstance(effects, dict):
        issues.append(ValidationIssue("$.effects", "expected an object", "type"))
    elif isinstance(effects, dict):
        if "icon_system" in effects:
            _validate_icon_system(effects["icon_system"], "$.effects.icon_system", issues)
        node_fill = effects.get("node_fill")
        if node_fill is not None and node_fill not in {"solid", "aurora"}:
            issues.append(ValidationIssue("$.effects.node_fill", "expected 'solid' or 'aurora'", "enum"))
        for token in (
            "grain_opacity",
            "blob_opacity",
            "band_opacity",
            "node_border_opacity",
            "grid_opacity",
            "frame_opacity",
        ):
            if token in effects and not _is_opacity(effects[token]):
                issues.append(ValidationIssue(f"$.effects.{token}", "expected a number from 0 to 1", "type"))
    roles = data.get("roles", {})
    if roles and not isinstance(roles, dict):
        issues.append(ValidationIssue("$.roles", "expected an object", "type"))
        return issues
    for role, tokens in roles.items():
        if role not in KNOWN_ROLES:
            issues.append(ValidationIssue(f"$.roles.{role}", "unknown role", "enum"))
        if not isinstance(tokens, dict):
            issues.append(ValidationIssue(f"$.roles.{role}", "expected an object", "type"))
            continue
        for token in ("stroke", "fill", "text", "glow", "band", "shadow"):
            if token in tokens and not isinstance(tokens[token], str):
                issues.append(ValidationIssue(f"$.roles.{role}.{token}", "expected a string", "type"))
        gradient = tokens.get("gradient")
        if gradient is not None:
            if not isinstance(gradient, list) or len(gradient) < 2:
                issues.append(ValidationIssue(f"$.roles.{role}.gradient", "expected at least two color stops", "type"))
            else:
                for index, stop in enumerate(gradient):
                    if isinstance(stop, str):
                        continue
                    if not isinstance(stop, dict) or not isinstance(stop.get("color"), str):
                        issues.append(ValidationIssue(f"$.roles.{role}.gradient[{index}]", "expected a color string or stop object", "type"))
                        continue
                    if "opacity" in stop and not _is_opacity(stop["opacity"]):
                        issues.append(ValidationIssue(f"$.roles.{role}.gradient[{index}].opacity", "expected a number from 0 to 1", "type"))
    return issues


def _is_opacity(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1


def _validate_icon_system(value: Any, path: str, issues: list) -> None:
    if not isinstance(value, str):
        issues.append(ValidationIssue(path, "expected a string", "type"))
    elif value not in SUPPORTED_ICON_SYSTEMS:
        issues.append(ValidationIssue(path, f"expected one of: {', '.join(sorted(SUPPORTED_ICON_SYSTEMS))}", "enum"))

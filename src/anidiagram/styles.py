"""Style profile loading for DiagramScript rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union


DEFAULT_STYLE: Dict[str, Any] = {
    "name": "minimal-light",
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
    return deep_merge(DEFAULT_STYLE, data)


def role_style(style: Dict[str, Any], role: Optional[str]) -> Dict[str, str]:
    roles = style.get("roles", {})
    return dict(roles.get(role or "neutral", roles.get("neutral", {})))

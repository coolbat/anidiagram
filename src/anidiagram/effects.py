"""Motion effect resolution for AniDiagram renderers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .model import EffectConfig, SceneMotion


def effect_from_value(value: Any, fallback: EffectConfig) -> EffectConfig:
    if value is None:
        return fallback
    if isinstance(value, str):
        return EffectConfig(preset=value)
    if not isinstance(value, dict):
        return fallback
    preset = value.get("preset", fallback.preset)
    return EffectConfig(
        preset=preset if isinstance(preset, str) else fallback.preset,
        line=value.get("line") if isinstance(value.get("line"), str) else fallback.line,
        particle=value.get("particle") if isinstance(value.get("particle"), str) else fallback.particle,
        trail=_trail_value(value.get("trail"), fallback.trail),
        entry=value.get("entry") if isinstance(value.get("entry"), str) else fallback.entry,
        accent=value.get("accent") if isinstance(value.get("accent"), str) else fallback.accent,
        icon=value.get("icon") if isinstance(value.get("icon"), str) else fallback.icon,
    )


def channel_effect(motion: SceneMotion, style: Dict[str, Any], channel: str, override: Optional[EffectConfig] = None) -> EffectConfig:
    base = getattr(motion, f"{channel}_effect")
    style_base = style_default_effect(style, channel, base)
    if motion.profile == "normal" and _has_effect(style_base):
        base = style_base
    if override and _has_effect(override):
        return merge_effects(base, override)
    return base


def style_default_effect(style: Dict[str, Any], channel: str, fallback: EffectConfig) -> EffectConfig:
    defaults = style.get("motion_defaults", {})
    if not isinstance(defaults, dict):
        return fallback
    return effect_from_value(defaults.get(channel), fallback)


def merge_effects(base: EffectConfig, override: EffectConfig) -> EffectConfig:
    return EffectConfig(
        preset=override.preset if override.preset != "none" else base.preset,
        line=override.line or base.line,
        particle=override.particle or base.particle,
        trail=override.trail or base.trail,
        entry=override.entry or base.entry,
        accent=override.accent or base.accent,
        icon=override.icon or base.icon,
    )


def effect_active(motion: SceneMotion, effect: EffectConfig) -> bool:
    return motion.profile != "off" and motion.intensity > 0 and effect.preset not in {"none", "static"}


def _has_effect(effect: EffectConfig) -> bool:
    return effect != EffectConfig()


def _trail_value(value: Any, fallback: Optional[str]) -> Optional[str]:
    if isinstance(value, bool):
        return "ghost" if value else "none"
    return value if isinstance(value, str) else fallback

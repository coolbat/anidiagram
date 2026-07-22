"""Motion effect resolution for AniDiagram renderers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .edge_motion import canonical_edge_motion
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
        particle_count=_optional_int(value.get("particle_count"), fallback.particle_count),
        trail_count=_optional_int(value.get("trail_count"), fallback.trail_count),
        entry=value.get("entry") if isinstance(value.get("entry"), str) else fallback.entry,
        accent=value.get("accent") if isinstance(value.get("accent"), str) else fallback.accent,
        icon=value.get("icon") if isinstance(value.get("icon"), str) else fallback.icon,
        icon_motion=value.get("icon_motion") if isinstance(value.get("icon_motion"), str) else fallback.icon_motion,
    )


def channel_effect(motion: SceneMotion, style: Dict[str, Any], channel: str, override: Optional[EffectConfig] = None) -> EffectConfig:
    base = getattr(motion, f"{channel}_effect")
    style_base = style_default_effect(style, channel, base)
    if motion.profile == "normal" and _has_effect(style_base):
        base = style_base
    if override and _has_effect(override):
        return merge_effects(base, override)
    return base


def canonical_edge_effect(effect: EffectConfig) -> EffectConfig:
    """Normalize every edge preset to one non-overlapping Edge Motion v1 recipe."""

    preset = canonical_edge_motion(effect.preset)
    if preset == "packet-flow":
        return EffectConfig(
            preset=preset,
            explicit=effect.explicit,
            line="static",
            particle="solid-dot",
            trail="none",
            particle_count=1,
            trail_count=0,
            entry="none",
        )
    if preset == "comet-flow":
        return EffectConfig(
            preset=preset,
            explicit=effect.explicit,
            line="static",
            particle="solid-dot",
            trail="fading-echoes",
            particle_count=1,
            trail_count=3,
            entry="none",
        )
    if preset == "stream-flow":
        return EffectConfig(
            preset=preset,
            explicit=effect.explicit,
            line="moving-dash",
            particle="none",
            trail="none",
            particle_count=0,
            trail_count=0,
            entry="none",
        )
    if preset == "draw":
        return EffectConfig(preset=preset, explicit=effect.explicit, line="draw", entry="draw")
    return EffectConfig(preset=preset, explicit=effect.explicit, line="static", entry="none")


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
        particle_count=override.particle_count if override.particle_count is not None else base.particle_count,
        trail_count=override.trail_count if override.trail_count is not None else base.trail_count,
        entry=override.entry or base.entry,
        accent=override.accent or base.accent,
        icon=override.icon or base.icon,
        icon_motion=override.icon_motion or base.icon_motion,
    )


def effect_active(motion: SceneMotion, effect: EffectConfig) -> bool:
    return motion.profile != "off" and motion.intensity > 0 and effect.preset not in {"none", "static"}


def _has_effect(effect: EffectConfig) -> bool:
    return effect != EffectConfig()


def _trail_value(value: Any, fallback: Optional[str]) -> Optional[str]:
    if isinstance(value, bool):
        return "ghost" if value else "none"
    return value if isinstance(value, str) else fallback


def _optional_int(value: Any, fallback: Optional[int]) -> Optional[int]:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else fallback

"""Canonical connection-edge motion vocabulary and legacy compatibility.

Edge Motion v1 intentionally keeps meaning and presentation small: an edge is
static, draws on once, carries one discrete packet, emphasizes a burst with a
short fading comet tail, or shows a continuous stream. Older DiagramScript
preset names remain readable, but renderers and runtime manifests consume only
the canonical recipe returned here.
"""

from __future__ import annotations

from typing import Final


EDGE_MOTION_CONTRACT: Final[str] = "edge-motion-v1"
EDGE_MOTION_VERSION: Final[str] = "1.0.0"

CANONICAL_EDGE_MOTION: Final[frozenset[str]] = frozenset(
    {"none", "static", "draw", "packet-flow", "comet-flow", "stream-flow"}
)

LEGACY_EDGE_MOTION_ALIASES: Final[dict[str, str]] = {
    "pulse": "stream-flow",
    "trace": "stream-flow",
    "dynamic-dash": "stream-flow",
    "dash-flow": "stream-flow",
    "flow-dot": "packet-flow",
    "flow-arrow": "packet-flow",
    "signal-dot": "packet-flow",
    "signal-arrow": "packet-flow",
    "ghost-flow": "comet-flow",
    "glow-line": "stream-flow",
    "comet": "comet-flow",
}

KNOWN_EDGE_MOTION: Final[frozenset[str]] = frozenset(
    {*CANONICAL_EDGE_MOTION, *LEGACY_EDGE_MOTION_ALIASES}
)

CONTINUOUS_EDGE_MOTION: Final[frozenset[str]] = frozenset(
    {"packet-flow", "comet-flow", "stream-flow"}
)
PARTICLE_EDGE_MOTION: Final[frozenset[str]] = frozenset({"packet-flow", "comet-flow"})
DRAW_ENTRY_EDGE_MOTION: Final[frozenset[str]] = frozenset({"draw"})


def canonical_edge_motion(preset: str) -> str:
    """Return the Edge Motion v1 recipe for a canonical or legacy preset."""

    return LEGACY_EDGE_MOTION_ALIASES.get(preset, preset)


def edge_motion_kind(preset: str) -> str:
    """Return the visual primitive used by a preset."""

    canonical = canonical_edge_motion(preset)
    if canonical in {"none", "static"}:
        return "static"
    if canonical == "draw":
        return "draw"
    if canonical == "stream-flow":
        return "stream"
    if canonical == "packet-flow":
        return "packet"
    if canonical == "comet-flow":
        return "comet"
    return "static"

"""Motion manifest generation for high-fidelity HTML runtime output."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .effects import channel_effect
from .model import EffectConfig, Node, Scene


MOTION_MANIFEST_VERSION = "motion-manifest-0.1"

ICON_PERFORMANCE_V2 = {
    "agent": "agent-think-act-v2",
    "api": "api-request-response-v2",
    "search": "search-discover-v2",
    "database": "database-write-v2",
    "memory": "memory-commit-v2",
    "tool": "tool-run-v2",
    "token": "token-intent-v2",
    "output": "output-reveal-v2",
}

SUPPORTED_ICON_PERFORMANCES = set(ICON_PERFORMANCE_V2.values())

PERFORMANCE_PARTS = {
    "agent-think-act-v2": ("root", "shell", "core", "thought1", "thought2", "thought3", "decisionToken"),
    "api-request-response-v2": (
        "root",
        "leftEndpoint",
        "rightEndpoint",
        "requestToken",
        "responseToken",
        "targetRing",
        "status",
    ),
    "search-discover-v2": ("root", "lens", "handle", "scan", "result1", "result2", "target"),
    "database-write-v2": ("root", "lid", "body", "layer1", "layer2", "writeToken", "flash"),
    "memory-commit-v2": (
        "root",
        "backCard",
        "frontCard",
        "trace1",
        "trace2",
        "trace3",
        "dot",
        "commitToken",
        "flash",
    ),
    "tool-run-v2": ("root", "chip", "glyph", "connector", "spark1", "spark2", "flash"),
    "token-intent-v2": ("root", "shell", "core", "tickLeft", "tickRight", "tickTop", "tickBottom", "halo"),
    "output-reveal-v2": ("root", "card", "line1", "line2", "check", "flash"),
}

PART_ID_SUFFIXES = {
    "leftEndpoint": "left-endpoint",
    "rightEndpoint": "right-endpoint",
    "requestToken": "request-token",
    "responseToken": "response-token",
    "targetRing": "target-ring",
    "result1": "result-1",
    "result2": "result-2",
    "layer1": "layer-1",
    "layer2": "layer-2",
    "writeToken": "write-token",
    "backCard": "back-card",
    "frontCard": "front-card",
    "trace1": "trace-1",
    "trace2": "trace-2",
    "trace3": "trace-3",
    "commitToken": "commit-token",
    "thought1": "thought-1",
    "thought2": "thought-2",
    "thought3": "thought-3",
    "decisionToken": "decision-token",
    "tickLeft": "tick-left",
    "tickRight": "tick-right",
    "tickTop": "tick-top",
    "tickBottom": "tick-bottom",
    "spark1": "spark-1",
    "spark2": "spark-2",
    "line1": "line-1",
    "line2": "line-2",
}


def build_motion_manifest(scene: Scene, style: Dict[str, Any], runtime: str = "gsap") -> Dict[str, Any]:
    """Build the runtime manifest consumed by the browser animation layer."""

    icons: List[Dict[str, Any]] = []
    for index, node in enumerate(scene.nodes):
        if not node.icon:
            continue
        effect = channel_effect(scene.motion, style, "node", node.effect)
        performance = icon_performance_for_node(node, effect, scene.motion.profile)
        if not performance:
            continue
        parts = {
            part: f"#{icon_part_id(node.node_id, part)}"
            for part in PERFORMANCE_PARTS[performance]
        }
        icons.append(
            {
                "node_id": node.node_id,
                "icon": node.icon,
                "performance": performance,
                "trigger": "on-reveal",
                "loop": "action-then-idle",
                "delay": round(index * max(scene.motion.stagger, 0.08), 3),
                "intensity": scene.motion.intensity,
                "parts": parts,
            }
        )

    return {
        "version": MOTION_MANIFEST_VERSION,
        "runtime": runtime,
        "profile": scene.motion.profile,
        "sequence": scene.motion.sequence,
        "reduced_motion": scene.motion.reduced_motion,
        "icons": icons,
    }


def icon_performance_for_node(node: Node, effect: EffectConfig, profile: str) -> Optional[str]:
    requested = effect.icon_motion or effect.icon
    if requested in SUPPORTED_ICON_PERFORMANCES:
        return requested
    if requested and requested.endswith("-v2"):
        return requested if requested in SUPPORTED_ICON_PERFORMANCES else None
    explicit_node_effect = node.effect != EffectConfig()
    if explicit_node_effect and effect.preset not in {"icon-performance", "icon-semantic"}:
        return None
    if effect.preset == "icon-performance":
        return ICON_PERFORMANCE_V2.get(node.icon or "")
    if profile in {"teaching", "expressive"}:
        return ICON_PERFORMANCE_V2.get(node.icon or "")
    return None


def icon_part_id(node_id: str, part: str) -> str:
    suffix = PART_ID_SUFFIXES.get(part, part)
    return f"icon-{_fragment_id(node_id)}-{suffix}"


def _fragment_id(value: Any) -> str:
    text = str(value or "item").lower()
    cleaned = "".join(char if char.isalnum() else "-" for char in text).strip("-")
    return cleaned or "item"

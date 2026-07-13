"""Motion manifest generation for high-fidelity HTML runtime output."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .effects import channel_effect
from .icon_system import resolve_icon_system
from .illustrated_character_icons import character_definition
from .illustrated_icons import illustrated_definition, is_illustrated_style
from .model import EffectConfig, Node, Scene


MOTION_MANIFEST_VERSION = "motion-manifest-0.1"
DEFAULT_RUNTIME_MODE = "ambient"

ICON_PERFORMANCE_V2 = {
    "agent": "agent-think-act-v2",
    "api": "api-request-response-v2",
    "search": "search-discover-v2",
    "database": "database-write-v2",
    "memory": "memory-commit-v2",
    "tool": "tool-run-v2",
    "token": "token-intent-v2",
    "output": "output-reveal-v2",
    "file": "file-lines-v2",
    "folder": "folder-open-v2",
    "cloud": "cloud-upload-v2",
    "shield": "shield-check-v2",
}

SUPPORTED_ICON_PERFORMANCES = set(ICON_PERFORMANCE_V2.values())

CHARACTER_ICON_PERFORMANCES = {
    "agent": "brain-think-pulse-v1",
    "operator": "operator-type-focus-v1",
    "database": "bucket-ingest-confirm-v1",
    "search": "search-scout-find-v1",
    "tool": "tool-kit-action-v1",
    "api": "api-signal-return-v1",
    "memory": "memory-index-commit-v1",
    "output": "output-envelope-reveal-v1",
    "file": "file-note-write-v1",
    "folder": "folder-file-store-v1",
    "cloud": "cloud-uplink-ready-v1",
    "shield": "shield-guard-confirm-v1",
    "token": "token-intent-ready-v1",
}
CHARACTER_REST_AT = {
    "agent": 1.50,
    "operator": 1.35,
    "database": 1.55,
    "search": 1.30,
    "tool": 1.40,
    "api": 1.35,
    "memory": 1.45,
    "output": 1.40,
    "file": 1.35,
    "folder": 1.35,
    "cloud": 1.40,
    "shield": 1.35,
    "token": 1.35,
}
SUPPORTED_ICON_PERFORMANCES.update(CHARACTER_ICON_PERFORMANCES.values())

PERFORMANCE_PARTS = {
    "agent-think-act-v2": (
        "root",
        "outlineLeft",
        "outlineRight",
        "centerLine",
        "branchLeft",
        "branchRight",
        "branchLower",
        "nodeTopLeft",
        "nodeTopRight",
        "nodeLeft",
        "nodeRight",
        "nodeCenter",
        "decisionToken",
        "pulse",
    ),
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
    "file-lines-v2": ("root", "sheet", "fold", "line1", "line2", "line3", "flash"),
    "folder-open-v2": ("root", "body", "tab", "fileLine", "openToken", "flash"),
    "cloud-upload-v2": ("root", "shell", "uploadArrow", "dot1", "dot2", "dot3", "statusRing"),
    "shield-check-v2": ("root", "shell", "check", "pulse", "scan"),
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
    "outlineLeft": "outline-left",
    "outlineRight": "outline-right",
    "centerLine": "center-line",
    "branchLeft": "branch-left",
    "branchRight": "branch-right",
    "branchLower": "branch-lower",
    "nodeTopLeft": "node-top-left",
    "nodeTopRight": "node-top-right",
    "nodeLeft": "node-left",
    "nodeRight": "node-right",
    "nodeCenter": "node-center",
    "decisionToken": "decision-token",
    "tickLeft": "tick-left",
    "tickRight": "tick-right",
    "tickTop": "tick-top",
    "tickBottom": "tick-bottom",
    "spark1": "spark-1",
    "spark2": "spark-2",
    "line1": "line-1",
    "line2": "line-2",
    "line3": "line-3",
    "fileLine": "file-line",
    "openToken": "open-token",
    "uploadArrow": "upload-arrow",
    "dot1": "dot-1",
    "dot2": "dot-2",
    "dot3": "dot-3",
    "statusRing": "status-ring",
    "bubbleHalo": "bubble-halo",
    "accentMark": "accent-mark",
    "orbitDot": "orbit-dot",
}


def build_motion_manifest(
    scene: Scene,
    style: Dict[str, Any],
    runtime: str = "gsap",
    mode: str = DEFAULT_RUNTIME_MODE,
) -> Dict[str, Any]:
    """Build the runtime manifest consumed by the browser animation layer."""

    if mode != DEFAULT_RUNTIME_MODE:
        raise ValueError('HTML runtime mode must be "ambient" in the current release')

    icon_system = resolve_icon_system(style)
    illustrated = icon_system == "illustrated-v1"
    icons: List[Dict[str, Any]] = []
    for index, node in enumerate(scene.nodes):
        if not node.icon:
            continue
        effect = channel_effect(scene.motion, style, "node", node.effect)
        performance = icon_performance_for_node(node, effect, scene.motion.profile, icon_system)
        if not performance:
            continue
        character = character_definition(node.icon) if icon_system == "illustrated-character-v1" else None
        definition = character
        if character is not None:
            part_names = character.parts
        elif illustrated:
            definition = illustrated_definition(node.icon)
            part_names = PERFORMANCE_PARTS[performance]
            part_names = tuple(dict.fromkeys((*part_names, *definition.parts)))
        else:
            part_names = PERFORMANCE_PARTS[performance]
        parts = {
            part: f"#{icon_part_id(node.node_id, part)}"
            for part in part_names
        }
        icon_entry = {
            "node_id": node.node_id,
            "icon": node.icon,
            "performance": performance,
            "trigger": "on-load",
            "loop": "action-then-idle",
            "delay": round(index * max(scene.motion.stagger, 0.08), 3),
            "intensity": scene.motion.intensity,
            "parts": parts,
        }
        if definition is not None:
            icon_entry["semantic_role"] = definition.semantic_role
        if character is not None:
            icon_entry["rest_at"] = CHARACTER_REST_AT[node.icon]
        if definition is not None:
            if hasattr(definition, "colors"):
                icon_entry["colors"] = definition.colors
        icons.append(icon_entry)

    edge_effect = channel_effect(scene.motion, style, "edge")
    title_effect = channel_effect(scene.motion, style, "title")
    edge_limits = [
        limit
        for limit in (
            scene.motion_policy.max_active_flow_edges,
            scene.motion_policy.max_particle_edges,
        )
        if limit is not None
    ]
    edge_limit = min(edge_limits) if edge_limits else None
    readable_edge_limit = min(edge_limit if edge_limit is not None else 2, 2)
    stage = {
        "edge_flow": scene.motion.profile in {"expressive", "teaching"} and edge_effect.preset not in {"none", "static"},
        "title_sweep": scene.motion.profile in {"expressive", "teaching"} and title_effect.preset == "highlight-sweep",
        "edge_limit": edge_limit,
        "readable_edge_limit": readable_edge_limit,
    }
    if illustrated:
        stage.update(
            {
                "relation_circles": scene.motion.profile in {"expressive", "teaching"},
                "group_fields": scene.motion.profile in {"expressive", "teaching"},
                "data_particles": stage["edge_flow"],
            }
        )

    manifest = {
        "version": MOTION_MANIFEST_VERSION,
        "runtime": runtime,
        "mode": mode,
        "profile": scene.motion.profile,
        "sequence": "independent-icon-loops",
        "scene_sequence": scene.motion.sequence,
        "reduced_motion": scene.motion.reduced_motion,
        "stage": stage,
        "icons": icons,
    }
    manifest["icon_system"] = icon_system
    return manifest


def icon_performance_for_node(node: Node, effect: EffectConfig, profile: str, icon_system: str = "semantic-line-v1") -> Optional[str]:
    if profile == "off":
        return None
    explicit_node_effect = node.effect.explicit
    node_requests_icon_performance = (
        node.effect.preset in {"icon-performance", "icon-semantic"}
        or node.effect.icon is not None
        or node.effect.icon_motion is not None
    )
    if explicit_node_effect and not node_requests_icon_performance:
        return None
    if icon_system == "illustrated-character-v1" and node.icon in CHARACTER_ICON_PERFORMANCES:
        return CHARACTER_ICON_PERFORMANCES[node.icon]
    requested = effect.icon_motion or effect.icon
    if requested in CHARACTER_ICON_PERFORMANCES.values() and icon_system != "illustrated-character-v1":
        requested = None
    if requested in SUPPORTED_ICON_PERFORMANCES:
        return requested
    if requested and requested.endswith("-v2"):
        return requested if requested in SUPPORTED_ICON_PERFORMANCES else None
    if effect.preset == "icon-performance":
        if icon_system == "illustrated-character-v1":
            return CHARACTER_ICON_PERFORMANCES.get(node.icon or "") or ICON_PERFORMANCE_V2.get(node.icon or "")
        return ICON_PERFORMANCE_V2.get(node.icon or "")
    if profile in {"teaching", "expressive"}:
        if icon_system == "illustrated-character-v1":
            return CHARACTER_ICON_PERFORMANCES.get(node.icon or "") or ICON_PERFORMANCE_V2.get(node.icon or "")
        return ICON_PERFORMANCE_V2.get(node.icon or "")
    return None


def icon_part_id(node_id: str, part: str) -> str:
    suffix = PART_ID_SUFFIXES.get(part, part)
    return f"icon-{_fragment_id(node_id)}-{suffix}"


def _fragment_id(value: Any) -> str:
    text = str(value or "item").lower()
    cleaned = "".join(char if char.isalnum() else "-" for char in text).strip("-")
    return cleaned or "item"

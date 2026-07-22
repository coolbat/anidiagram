"""Motion manifest generation for high-fidelity HTML runtime output."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from .diagram_core.instance_ids import part_dom_id
from .diagram_core.manifest import load_manifest
from .effects import channel_effect
from .icon_system import icon_system_version, resolve_icon_system
from .illustrated_character_icons import character_definition
from .illustrated_registry import illustrated_definition
from .illustrated_expansion_batch_4_motion import (
    ILLUSTRATED_V5_REVIEW_ICON_PERFORMANCES,
    ILLUSTRATED_V5_REVIEW_REST_AT,
)
from .illustrated_icons import illustrated_definition as legacy_illustrated_definition, is_illustrated_style
from .model import EffectConfig, Node, Scene
from .styles import deep_merge


MOTION_MANIFEST_VERSION = "motion-manifest-0.1"
DEFAULT_RUNTIME_MODE = "ambient"
_MOTION_CATALOG_PATH = Path(__file__).resolve().parents[2] / "runtime" / "motion-catalog.json"

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
ILLUSTRATED_V2_ICON_PERFORMANCES = {
    "agent": "illustrated-agent-input-reason-result-v1",
    "operator": "illustrated-operator-focus-operate-confirm-v1",
    "tool": "illustrated-tool-prepare-execute-complete-v1",
    "output": "illustrated-output-compose-deliver-confirm-v1",
    "database": "illustrated-database-ingest-store-persist-v1",
    "api": "illustrated-api-request-route-response-v1",
    "search": "illustrated-search-query-scan-discover-v1",
    "memory": "illustrated-memory-capture-index-recall-v1",
}
ILLUSTRATED_V2_REST_AT = {
    "agent": 1.72,
    "operator": 1.68,
    "tool": 1.62,
    "output": 1.70,
    "database": 1.72,
    "api": 1.66,
    "search": 1.78,
    "memory": 1.72,
}
ILLUSTRATED_V3_ADDITIONAL_ICON_PERFORMANCES = {
    "file": "illustrated-file-prepare-attach-reference-v1",
    "folder": "illustrated-folder-prepare-store-index-v1",
    "cloud": "illustrated-cloud-prepare-transfer-sync-v1",
    "shield": "illustrated-shield-prepare-lock-protect-v1",
}
ILLUSTRATED_V3_ADDITIONAL_REST_AT = {
    "file": 1.58,
    "folder": 1.66,
    "cloud": 1.72,
    "shield": 1.68,
}
ILLUSTRATED_V3_ICON_PERFORMANCES = {
    **ILLUSTRATED_V2_ICON_PERFORMANCES,
    **ILLUSTRATED_V3_ADDITIONAL_ICON_PERFORMANCES,
}
ILLUSTRATED_V3_REST_AT = {
    **ILLUSTRATED_V2_REST_AT,
    **ILLUSTRATED_V3_ADDITIONAL_REST_AT,
}
ILLUSTRATED_V4_REVIEW_ICON_PERFORMANCES = {
    "user": "illustrated-user-request-interact-consume-v1",
    "server": "illustrated-server-host-compute-serve-v1",
    "ai-model": "illustrated-ai-model-infer-transform-predict-v1",
    "message-queue": "illustrated-message-queue-buffer-order-deliver-v1",
}
ILLUSTRATED_V4_REVIEW_REST_AT = {
    "user": 1.66,
    "server": 1.70,
    "ai-model": 1.80,
    "message-queue": 1.76,
}
ILLUSTRATED_ICON_PERFORMANCES = {
    **ILLUSTRATED_V3_ICON_PERFORMANCES,
    **ILLUSTRATED_V4_REVIEW_ICON_PERFORMANCES,
    **ILLUSTRATED_V5_REVIEW_ICON_PERFORMANCES,
}
ILLUSTRATED_REST_AT = {
    **ILLUSTRATED_V3_REST_AT,
    **ILLUSTRATED_V4_REVIEW_REST_AT,
    **ILLUSTRATED_V5_REVIEW_REST_AT,
}
STRONG_CHARACTER_INTENSITY = 1.5
STRONG_CHARACTER_REST_AT = 1.2
SUPPORTED_ICON_PERFORMANCES.update(CHARACTER_ICON_PERFORMANCES.values())
SUPPORTED_ICON_PERFORMANCES.update(ILLUSTRATED_ICON_PERFORMANCES.values())
SUPPORTED_ICON_PERFORMANCES.update(ILLUSTRATED_V4_REVIEW_ICON_PERFORMANCES.values())
SUPPORTED_ICON_PERFORMANCES.update(ILLUSTRATED_V5_REVIEW_ICON_PERFORMANCES.values())

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

    if scene.icon_system:
        style = deep_merge(style, {"icon_system": scene.icon_system})
    icon_system = resolve_icon_system(style)
    illustrated = icon_system == "illustrated-v1"
    icons: List[Dict[str, Any]] = []
    for index, node in enumerate(scene.nodes):
        if not node.icon:
            continue
        if icon_system == "diagram-core-v1":
            definition = _diagram_core_presentations().get(node.icon)
            if definition is not None and scene.motion.profile != "off":
                icons.append(_diagram_core_manifest_entry(node, definition, index, scene))
            continue
        effect = channel_effect(scene.motion, style, "node", node.effect)
        performance = icon_performance_for_node(node, effect, scene.motion.profile, icon_system)
        if not performance:
            continue
        character = character_definition(node.icon) if icon_system == "illustrated-character-v1" else None
        character_v2 = illustrated_definition(node.icon) if icon_system == "illustrated" else None
        definition = character or character_v2
        if character is not None:
            part_names = character.parts
        elif character_v2 is not None:
            part_names = character_v2.parts
        elif illustrated:
            definition = legacy_illustrated_definition(node.icon)
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
            if scene.motion.intensity >= STRONG_CHARACTER_INTENSITY:
                icon_entry["performance_tier"] = "strong-loop"
                icon_entry["rest_at"] = STRONG_CHARACTER_REST_AT
            else:
                icon_entry["rest_at"] = CHARACTER_REST_AT[node.icon]
        elif character_v2 is not None:
            icon_entry["asset_version"] = icon_system_version("illustrated")
            icon_entry["cancel_behavior"] = "restore-authored-rest-pose"
            icon_entry["reduced_motion_behavior"] = "static-rest"
            icon_entry["repeat_delay"] = 0.8
            icon_entry["motion_contract"] = "illustrated-performance-v5"
            icon_entry["motion_status"] = "approved"
            icon_entry["selection_policy"] = "automatic-for-supported-showcase-icons"
            icon_entry["rest_at"] = ILLUSTRATED_REST_AT[node.icon]
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
    stage_motion_enabled = scene.motion.profile in {"expressive", "teaching", "showcase-v1"} and scene.motion.intensity > 0
    edges: List[Dict[str, Any]] = []
    eligible_edge_indices: List[int] = []
    for index, edge in enumerate(scene.edges):
        resolved_effect = channel_effect(scene.motion, style, "edge", edge.effect)
        active = (
            stage_motion_enabled
            and edge.motion.enabled
            and resolved_effect.preset not in {"none", "static"}
        )
        edge_entry: Dict[str, Any] = {
            "index": index,
            "source": edge.source,
            "target": edge.target,
            "animated": edge.motion.enabled,
            "active": active,
            "effect": resolved_effect.preset,
            "delay": edge.motion.delay,
        }
        for key in ("line", "particle", "trail"):
            value = getattr(resolved_effect, key)
            if value is not None:
                edge_entry[key] = value
        edges.append(edge_entry)
        if active:
            eligible_edge_indices.append(index)

    active_edge_indices = (
        eligible_edge_indices[:edge_limit]
        if edge_limit is not None
        else eligible_edge_indices
    )
    readable_edge_indices = active_edge_indices[:readable_edge_limit]
    stage = {
        "edge_flow": stage_motion_enabled and (
            edge_effect.preset not in {"none", "static"} or bool(eligible_edge_indices)
        ),
        "title_sweep": stage_motion_enabled and title_effect.preset == "highlight-sweep",
        "edge_limit": edge_limit,
        "readable_edge_limit": readable_edge_limit,
        "active_edge_indices": active_edge_indices,
        "readable_edge_indices": readable_edge_indices,
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
        "edges": edges,
    }
    manifest["icon_system"] = icon_system
    resolved_icon_system_version = icon_system_version(icon_system)
    if resolved_icon_system_version is not None:
        manifest["icon_system_version"] = resolved_icon_system_version
    return manifest


@lru_cache(maxsize=1)
def _diagram_core_presentations() -> Dict[str, Dict[str, Any]]:
    payload = json.loads(_MOTION_CATALOG_PATH.read_text(encoding="utf-8"))
    definitions = payload.get("diagram_core_presentations", [])
    return {
        str(definition["icon"]): definition
        for definition in definitions
        if isinstance(definition, dict) and isinstance(definition.get("icon"), str)
    }


def _runtime_part_name(part_name: str) -> str:
    head, *tail = part_name.split("-")
    return head + "".join(value.title() for value in tail)


def _diagram_core_manifest_entry(
    node: Node,
    definition: Dict[str, Any],
    index: int,
    scene: Scene,
) -> Dict[str, Any]:
    icon_id = str(node.icon)
    instance_id = f"node.{node.node_id}"
    parts = {
        _runtime_part_name(part): f"#{part_dom_id(instance_id, icon_id, part)}"
        for part in load_manifest(icon_id).parts
    }
    entry: Dict[str, Any] = {
        "node_id": node.node_id,
        "icon": icon_id,
        "icon_system": "diagram-core-v1",
        "performance": definition["runtime_id"],
        "presentation_performance": definition["id"],
        "presentation_profile": definition["profile"],
        "trigger": "on-load",
        "loop": "action-then-rest",
        "delay": round(index * max(scene.motion.stagger, 0.08), 3),
        "intensity": scene.motion.intensity,
        "rest_at": definition["rest_at"],
        "repeat_delay": definition["repeat_delay"],
        "duration_ms": definition["duration_ms"],
        "repeat_policy": definition["repeat_policy"],
        "cancel_behavior": definition["cancel_behavior"],
        "reduced_motion_behavior": definition["reduced_motion_behavior"],
        "parts": parts,
    }
    if "recipe" in definition:
        entry["recipe"] = definition["recipe"]
    return entry


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
    requested = effect.icon_motion or effect.icon
    if icon_system == "illustrated":
        if requested in ILLUSTRATED_ICON_PERFORMANCES.values():
            return requested
        if effect.preset == "icon-performance" or profile in {"showcase-v1", "expressive", "teaching"}:
            return ILLUSTRATED_ICON_PERFORMANCES.get(node.icon or "")
        return None
    if icon_system == "illustrated-character-v1" and node.icon in CHARACTER_ICON_PERFORMANCES:
        return CHARACTER_ICON_PERFORMANCES[node.icon]
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

"""Edge Motion v1 manifest adapter.

The public 2.3 runtime manifest is release-frozen.  This adapter preserves that
implementation as an archive and produces the versioned 0.2 contract for new
HTML output and review candidates.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .edge_motion import EDGE_MOTION_CONTRACT, EDGE_MOTION_VERSION, canonical_edge_motion, edge_motion_kind
from .model import Scene
from .motion_manifest import DEFAULT_RUNTIME_MODE, build_motion_manifest as build_legacy_motion_manifest


MOTION_MANIFEST_VERSION = "motion-manifest-0.2"


def _select_readable_edges(scene: Scene, active_indices: List[int], limit: int) -> List[int]:
    if limit <= 0:
        return []
    importance_rank = {"primary": 0, "supporting": 1, "context": 2}
    ranked = sorted(
        active_indices,
        key=lambda index: (
            importance_rank.get(
                scene.edges[index].flow_importance or scene.edges[index].importance or "supporting",
                1,
            ),
            scene.edges[index].step if scene.edges[index].step is not None else 10_000,
            index,
        ),
    )
    selected: List[int] = []
    covered_flows: set[str] = set()
    for index in ranked:
        flow_id = scene.edges[index].flow_id
        if flow_id is None or flow_id in covered_flows:
            continue
        selected.append(index)
        covered_flows.add(flow_id)
        if len(selected) == limit:
            return selected
    for index in ranked:
        if index not in selected:
            selected.append(index)
        if len(selected) == limit:
            break
    return selected


def build_motion_manifest(
    scene: Scene,
    style: Dict[str, Any],
    runtime: str = "gsap",
    mode: str = DEFAULT_RUNTIME_MODE,
) -> Dict[str, Any]:
    manifest = build_legacy_motion_manifest(scene, style, runtime=runtime, mode=mode)
    manifest["version"] = MOTION_MANIFEST_VERSION
    manifest["edge_motion_contract"] = EDGE_MOTION_CONTRACT
    manifest["edge_motion_version"] = EDGE_MOTION_VERSION
    for index, entry in enumerate(manifest["edges"]):
        edge = scene.edges[index]
        effect = canonical_edge_motion(str(entry["effect"]))
        entry["effect"] = effect
        entry["motion_kind"] = edge_motion_kind(effect)
        entry["duration"] = 1.35 if effect == "stream-flow" else 1.85 if effect == "comet-flow" else 1.65
        if effect == "packet-flow":
            entry.update({"line": "static", "particle": "solid-dot", "trail": "none"})
        elif effect == "comet-flow":
            entry.update(
                {
                    "line": "static",
                    "particle": "solid-dot",
                    "trail": "fading-echoes",
                    "trail_count": 3,
                }
            )
        elif effect == "stream-flow":
            entry.update({"line": "moving-dash", "particle": "none", "trail": "none"})
        elif effect == "draw":
            entry.update({"line": "draw", "particle": "none", "trail": "none"})
        for key in (
            "semantic_relation_id",
            "semantic_kind",
            "importance",
            "flow_id",
            "flow_importance",
            "flow_repeat",
        ):
            value = getattr(edge, key)
            if value is not None:
                entry[key] = value
    active = list(manifest["stage"].get("active_edge_indices") or [])
    readable_limit = int(manifest["stage"].get("readable_edge_limit") or 0)
    manifest["stage"]["readable_edge_indices"] = _select_readable_edges(scene, active, readable_limit)
    return manifest

#!/usr/bin/env python3
"""Build the review-only DiagramScript for the Illustrated 2.4 candidate case."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "examples" / "cloud-native-knowledge-retrieval-illustrated-2.4-candidate.plan.json"
SPEC_PATH = ROOT / "examples" / "cloud-native-knowledge-retrieval-illustrated-2.4-candidate.diagram.json"
CANDIDATE_ICONS = {"vector-database", "knowledge-base", "gateway", "container"}
NODE_LAYOUT = {
    "curated-knowledge": ([160, 220], [360, 190]),
    "embedding-container": ([950, 220], [360, 190]),
    "prepared-vector-index": ([1740, 220], [360, 190]),
    "client-application": ([50, 625], [170, 125]),
    "policy-gateway": ([400, 580], [240, 215]),
    "retrieval-container": ([820, 580], [240, 215]),
    "vector-search-view": ([1240, 580], [240, 215]),
    "source-resolver": ([1660, 580], [240, 215]),
    "grounded-context": ([2070, 625], [150, 125]),
}
GROUP_LAYOUT = {
    "knowledge-preparation-plane": [40, 150, 2180, 320],
    "online-retrieval-plane": [40, 510, 2180, 350],
}
EDGE_COLORS = ["#fb7185", "#a78bfa", "#22d3ee", "#2dd4bf", "#38bdf8", "#a78bfa", "#34d399"]


def build_case(plan: dict) -> dict:
    semantic = plan["semantic"]
    flow_by_relation = {
        relation_id: flow
        for flow in semantic.get("flows", [])
        for relation_id in flow.get("relation_ids", [])
    }
    nodes = []
    for entity in semantic["entities"]:
        position, size = NODE_LAYOUT[entity["id"]]
        node = {
            "id": entity["id"],
            "label": entity["label"],
            "caption": entity["description"],
            "kind": entity["kind"],
            "role": entity["role"],
            "position": position,
            "size": size,
        }
        if entity["kind"] in CANDIDATE_ICONS:
            node["icon"] = entity["kind"]
            node["effect"] = {
                "preset": "icon-performance",
                "icon_motion": "illustrated-performance-v5-review",
            }
        else:
            node["endpoint"] = True
        nodes.append(node)
    node_map = {node["id"]: node for node in nodes}
    edges = []
    for index, relation in enumerate(semantic["relations"]):
        flow = flow_by_relation.get(relation["id"])
        source = node_map[relation["from"]]
        target = node_map[relation["to"]]
        sx, sy = source["position"]
        sw, sh = source["size"]
        tx, ty = target["position"]
        _, th = target["size"]
        edges.append(
            {
                "id": relation["id"],
                "from": relation["from"],
                "to": relation["to"],
                "label": relation["label"],
                "kind": relation["kind"],
                "importance": relation.get("importance", "supporting"),
                "flow_id": flow.get("id") if flow else None,
                "flow_importance": flow.get("importance") if flow else None,
                "flow_repeat": flow.get("repeat") if flow else None,
                "color": EDGE_COLORS[index],
                "path": f"M {sx + sw} {sy + sh / 2:g} H {tx}",
                "label_position": [(sx + sw + tx) / 2, min(sy + sh / 2, ty + th / 2) - 18],
                "motion": {"enabled": True, "effect": "packet-flow", "delay": round(index * 0.08, 2)},
            }
        )
    return {
        "version": "0.4",
        "composition_policy": "composition-v1",
        "candidate_review_only": True,
        "candidate_motion_contract": "illustrated-performance-v5-review",
        "resolved_presentation": {
            "icon_system": {"value": "illustrated", "source": "explicit", "version": "2.4.0-candidate"},
            "style": {"value": "deep-tech", "source": "model"},
            "layout": {"value": "swimlane", "source": "model"},
            "motion": {"value": "showcase-v1", "source": "default"},
        },
        "canvas": {"width": 2260, "height": 920},
        "title": {"text": semantic["title"], "subtitle": semantic["subtitle"]},
        "motion": {
            "profile": "showcase-v1",
            "node": {"preset": "icon-performance"},
            "edge": {"preset": "packet-flow"},
            "reduced_motion": "static",
        },
        "groups": [
            {
                "id": group["id"],
                "label": group["label"],
                "caption": group["description"],
                "bounds": GROUP_LAYOUT[group["id"]],
            }
            for group in semantic["groups"]
        ],
        "nodes": nodes,
        "edges": edges,
        "semantic_source": PLAN_PATH.name,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    parser.add_argument("--spec-out", type=Path, default=SPEC_PATH)
    args = parser.parse_args()
    spec = build_case(json.loads(args.plan.read_text(encoding="utf-8")))
    args.spec_out.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.spec_out.resolve())


if __name__ == "__main__":
    main()

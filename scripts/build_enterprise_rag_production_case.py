#!/usr/bin/env python3
"""Compile the Enterprise RAG plan and apply its production review layout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from anidiagram.composition import compile_plan_v02


ROOT = Path(__file__).resolve().parents[1]
POSITIONS = {
    "knowledge-owner": (70, 245),
    "source-files": (370, 245),
    "document-library": (670, 245),
    "cloud-intake": (970, 245),
    "ingestion-toolchain": (1270, 245),
    "vector-database": (1570, 245),
    "rag-api": (70, 715),
    "policy-guard": (370, 715),
    "rag-agent": (720, 715),
    "retriever": (1080, 545),
    "conversation-memory": (1080, 855),
    "grounded-answer": (1570, 715),
}
GROUP_BOUNDS = {
    "knowledge-ingestion-plane": (38, 180, 1794, 292),
    "governed-rag-runtime": (38, 510, 1794, 505),
}
EDGE_ROLES = {
    ("knowledge-owner", "source-files"): "actor",
    ("source-files", "document-library"): "source",
    ("document-library", "cloud-intake"): "source",
    ("cloud-intake", "ingestion-toolchain"): "tool",
    ("ingestion-toolchain", "vector-database"): "memory",
    ("rag-api", "policy-guard"): "source",
    ("policy-guard", "rag-agent"): "risk",
    ("rag-agent", "retriever"): "agent",
    ("retriever", "vector-database"): "memory",
    ("vector-database", "rag-agent"): "output",
    ("rag-agent", "conversation-memory"): "memory",
    ("rag-agent", "grounded-answer"): "output",
}
POINT_ROUTES = {
    ("vector-database", "rag-agent"): [
        [1685, 373],
        [1685, 485],
        [835, 485],
        [835, 715],
    ]
}


def build_case(plan: dict) -> dict:
    scene = compile_plan_v02(plan)
    scene["canvas"] = {"width": 1900, "height": 1060}
    scene["title"]["subtitle"] = (
        "Curated ingestion → policy-scoped retrieval → agent grounding → cited response"
    )
    for node in scene["nodes"]:
        node["position"] = list(POSITIONS[node["id"]])
        node["size"] = [230, 128]
        node["radius"] = 26
        node["stroke_width"] = 2.35
        node.pop("step", None)
    for group in scene["groups"]:
        group["bounds"] = list(GROUP_BOUNDS[group["id"]])
    for edge in scene["edges"]:
        # This reviewed layout changes node coordinates after Plan compilation.
        # Drop auto routes before applying its authored route choices.
        edge.pop("points", None)
        endpoints = (edge["from"], edge["to"])
        edge["role"] = EDGE_ROLES[endpoints]
        edge["route"] = "straight"
        edge.pop("step", None)
        if endpoints in POINT_ROUTES:
            edge["route"] = "points"
            edge["points"] = POINT_ROUTES[endpoints]
    return scene


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan",
        type=Path,
        default=ROOT / "examples" / "enterprise-rag-production-illustrated.plan.json",
    )
    parser.add_argument(
        "--spec-out",
        type=Path,
        default=ROOT / "examples" / "enterprise-rag-production-illustrated.diagram.json",
    )
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    scene = build_case(plan)
    args.spec_out.parent.mkdir(parents=True, exist_ok=True)
    args.spec_out.write_text(
        json.dumps(scene, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(args.spec_out.resolve())


if __name__ == "__main__":
    main()

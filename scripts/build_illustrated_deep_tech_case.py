#!/usr/bin/env python3
"""Compile the Deep Tech Illustrated case and apply its review layout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from anidiagram.composition import compile_plan_v02


ROOT = Path(__file__).resolve().parents[1]
POSITIONS = {
    "operator": (70, 190),
    "orchestrator": (70, 520),
    "planner": (430, 270),
    "executor": (430, 520),
    "code-tools": (800, 270),
    "validation-tools": (800, 520),
    "release-package": (1170, 270),
    "verification-report": (1170, 520),
}
GROUP_BOUNDS = {
    "specialist-agents": (400, 220, 360, 490),
    "execution-plane": (770, 220, 360, 490),
    "delivery-plane": (1140, 220, 360, 490),
}


def build_case(plan: dict) -> dict:
    scene = compile_plan_v02(plan)
    scene["canvas"] = {"width": 1540, "height": 860}
    for node in scene["nodes"]:
        node["position"] = list(POSITIONS[node["id"]])
        node["size"] = [300, 142]
        node["radius"] = 28
        node["stroke_width"] = 2.5
        node.pop("step", None)
    for group in scene["groups"]:
        group["bounds"] = list(GROUP_BOUNDS[group["id"]])
    for edge in scene["edges"]:
        # This reviewed layout changes node coordinates after Plan compilation.
        # Drop auto routes before applying its authored route choices.
        edge.pop("points", None)
        edge["route"] = "curved"
    return scene


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan",
        type=Path,
        default=ROOT / "examples" / "illustrated-deep-tech-software-delivery.plan.json",
    )
    parser.add_argument(
        "--spec-out",
        type=Path,
        default=ROOT / "examples" / "illustrated-deep-tech-software-delivery.diagram.json",
    )
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    scene = build_case(plan)
    args.spec_out.parent.mkdir(parents=True, exist_ok=True)
    args.spec_out.write_text(json.dumps(scene, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.spec_out.resolve())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the review-only motion contract for Illustrated Batches 6-10."""

from __future__ import annotations

import json
from pathlib import Path

from anidiagram.illustrated_expansion_batches_6_10 import expansion_6_10_definition, expansion_6_10_icon_ids
from anidiagram.illustrated_expansion_batches_6_10_motion import (
    ILLUSTRATED_V7_REVIEW_ICON_PERFORMANCES,
    ILLUSTRATED_V7_REVIEW_MOTION_SPECS,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v7.review.json"


def build_contract() -> dict:
    performances = []
    for icon_id in expansion_6_10_icon_ids():
        definition = expansion_6_10_definition(icon_id)
        spec = ILLUSTRATED_V7_REVIEW_MOTION_SPECS[icon_id]
        performances.append(
            {
                "icon": icon_id,
                "id": ILLUSTRATED_V7_REVIEW_ICON_PERFORMANCES[icon_id],
                "semantic_sequence": list(spec["sequence"]),
                "primary_parts": list(definition.parts[1:]),
                "motion_recipe": {
                    "type": spec["recipe"],
                    "prepare_parts": list(spec["prepare_parts"]),
                    "action_parts": list(spec["action_parts"]),
                    "result_parts": list(spec["result_parts"]),
                },
                "rest_at": spec["rest_at"],
            }
        )
    return {
        "system": "illustrated",
        "icon_system_version": "2.5.0-candidate",
        "contract": "illustrated-performance-v7-review",
        "extends": "illustrated-performance-v6-review",
        "status": "visual-review",
        "approved_static_batches": [6, 7, 8, 9, 10],
        "public_showcase_enabled": False,
        "selection_policy": "explicit-review-only",
        "repeat_delay": 0.8,
        "cancel_behavior": "restore-authored-rest-pose",
        "reduced_motion_behavior": "static-rest",
        "performances": performances,
    }


def main() -> None:
    contract = build_contract()
    if OUT.exists():
        existing = json.loads(OUT.read_text(encoding="utf-8"))
        if existing != contract:
            raise RuntimeError(
                "illustrated-performance-v7.review.json is immutable; create a new review-contract version"
            )
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT.relative_to(ROOT)), "performances": len(contract["performances"])}, indent=2))


if __name__ == "__main__":
    main()

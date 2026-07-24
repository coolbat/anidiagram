#!/usr/bin/env python3
"""Build the public Illustrated 2.5 runtime extension from approved reviews."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anidiagram.illustrated_public_motion import (
    ILLUSTRATED_PUBLIC_ICON_PERFORMANCES,
    ILLUSTRATED_PUBLIC_MOTION_SPECS,
)
from scripts.render_illustrated_expansion_batch_5_motion_review import BATCH_5_RUNTIME
from scripts.render_illustrated_expansion_batches_6_10_motion_review import GENERIC_V7_RUNTIME

OUT = ROOT / "runtime" / "illustrated-performance-v6-runtime.js"


def build_runtime() -> str:
    configured = GENERIC_V7_RUNTIME.replace(
        "playIllustratedV7Configured",
        "playIllustratedPublicConfigured",
    )
    registrations = "\n".join(
        f'  performances[{json.dumps(ILLUSTRATED_PUBLIC_ICON_PERFORMANCES[icon_id])}] = playIllustratedPublicConfigured;'
        for icon_id in ILLUSTRATED_PUBLIC_MOTION_SPECS
    )
    character_registrations = "\n".join(
        f'  characterPerformanceIds.add({json.dumps(performance)});'
        for performance in ILLUSTRATED_PUBLIC_ICON_PERFORMANCES.values()
    )
    return (
        "  // Illustrated 2.5.0 public extension: approved Batch 5 motions.\n"
        + BATCH_5_RUNTIME.strip("\n")
        + "\n\n  // Illustrated 2.5.0 public extension: configured expansion and revised-icon motions.\n"
        + configured.strip("\n")
        + "\n"
        + registrations
        + "\n"
        + character_registrations
        + "\n"
    )


def main() -> None:
    source = build_runtime()
    OUT.write_text(source, encoding="utf-8")
    print(json.dumps({"path": str(OUT.relative_to(ROOT)), "bytes": len(source.encode("utf-8"))}, indent=2))


if __name__ == "__main__":
    main()

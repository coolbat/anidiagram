#!/usr/bin/env python3
"""Fail when committed showcase media exceeds the product performance budget."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README_TOTAL_BUDGET = 6 * 1024 * 1024
README_CASE_BUDGET = 1024 * 1024
TRACKED_GALLERY_BUDGET = 55 * 1024 * 1024
README_FRAME_CONTRACT = 24


def audit(gallery: Path) -> dict:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required for asset-budget validation") from exc
    readme = gallery / "readme-showcase"
    cases = []
    issues = []
    for path in sorted(readme.glob("*.webp")):
        with Image.open(path) as image:
            frames = int(getattr(image, "n_frames", 1))
            dimensions = list(image.size)
        size = path.stat().st_size
        cases.append({"path": str(path.relative_to(ROOT)), "bytes": size, "frames": frames, "dimensions": dimensions})
        if size > README_CASE_BUDGET:
            issues.append(f"{path.name}: {size} bytes exceeds {README_CASE_BUDGET}")
        if frames != README_FRAME_CONTRACT:
            issues.append(f"{path.name}: {frames} frames, expected {README_FRAME_CONTRACT}")
    readme_total = sum(item["bytes"] for item in cases)
    gallery_total = sum(path.stat().st_size for path in gallery.rglob("*") if path.is_file())
    if len(cases) != 8:
        issues.append(f"README showcase contains {len(cases)} WebP files, expected 8")
    if readme_total > README_TOTAL_BUDGET:
        issues.append(f"README showcase: {readme_total} bytes exceeds {README_TOTAL_BUDGET}")
    if gallery_total > TRACKED_GALLERY_BUDGET:
        issues.append(f"gallery: {gallery_total} bytes exceeds {TRACKED_GALLERY_BUDGET}")
    return {
        "ok": not issues,
        "readme_total_bytes": readme_total,
        "gallery_total_bytes": gallery_total,
        "budgets": {
            "readme_total_bytes": README_TOTAL_BUDGET,
            "readme_case_bytes": README_CASE_BUDGET,
            "gallery_total_bytes": TRACKED_GALLERY_BUDGET,
            "readme_frames": README_FRAME_CONTRACT,
        },
        "cases": cases,
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gallery", type=Path, default=ROOT / "gallery")
    args = parser.parse_args()
    report = audit(args.gallery.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

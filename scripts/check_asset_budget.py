#!/usr/bin/env python3
"""Fail when committed showcase media exceeds the product performance budget."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README_TOTAL_BUDGET = 6 * 1024 * 1024
README_CASE_BUDGET = 1024 * 1024
TRACKED_GALLERY_BUDGET = 55 * 1024 * 1024
README_FRAME_CONTRACT = 24
README_ASSET_COUNT = 2
README_FILES = (ROOT / "README.md", ROOT / "README.zh-CN.md")
README_WEBP_PATTERN = re.compile(r"\]\(\./([^)]+\.webp)\)")


def _readme_webp_paths() -> list[Path]:
    paths = {
        ROOT / match
        for readme in README_FILES
        for match in README_WEBP_PATTERN.findall(readme.read_text(encoding="utf-8"))
    }
    return sorted(paths)


def _inspect_webp(path: Path, image_module) -> dict:
    with image_module.open(path) as image:
        frames = int(getattr(image, "n_frames", 1))
        dimensions = list(image.size)
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "frames": frames,
        "dimensions": dimensions,
    }


def audit(gallery: Path) -> dict:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required for asset-budget validation") from exc
    readme = gallery / "readme-showcase"
    issues = []
    readme_paths = _readme_webp_paths()
    showcase_paths = sorted(readme.glob("*.webp"))
    contract_paths = sorted(set(readme_paths) | set(showcase_paths))
    missing = [path for path in contract_paths if not path.is_file()]
    issues.extend(f"missing animated WebP: {path.relative_to(ROOT)}" for path in missing)
    inspected = [_inspect_webp(path, Image) for path in contract_paths if path.is_file()]
    by_path = {item["path"]: item for item in inspected}
    cases = [by_path[str(path.relative_to(ROOT))] for path in readme_paths if path.is_file()]
    showcase_cases = [by_path[str(path.relative_to(ROOT))] for path in showcase_paths if path.is_file()]
    for item in inspected:
        if item["bytes"] > README_CASE_BUDGET:
            issues.append(f'{item["path"]}: {item["bytes"]} bytes exceeds {README_CASE_BUDGET}')
        if item["frames"] != README_FRAME_CONTRACT:
            issues.append(f'{item["path"]}: {item["frames"]} frames, expected {README_FRAME_CONTRACT}')
    readme_total = sum(item["bytes"] for item in cases)
    gallery_total = sum(path.stat().st_size for path in gallery.rglob("*") if path.is_file())
    if len(cases) != README_ASSET_COUNT:
        issues.append(
            f"README pages reference {len(cases)} WebP files, expected {README_ASSET_COUNT}"
        )
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
        "showcase_cases": showcase_cases,
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

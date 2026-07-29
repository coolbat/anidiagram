#!/usr/bin/env python3
"""List or remove old generated outputs while preserving release evidence."""

from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def candidates(root: Path, older_than_days: int) -> list[Path]:
    cutoff = time.time() - max(0, older_than_days) * 86400
    return sorted(
        path
        for path in root.iterdir()
        if path.name != "release-evidence" and path.stat().st_mtime < cutoff
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "outputs")
    parser.add_argument("--older-than-days", type=int, default=14)
    parser.add_argument("--apply", action="store_true", help="Delete the listed paths; default is dry-run.")
    args = parser.parse_args()
    root = args.root.resolve()
    expected = (ROOT / "outputs").resolve()
    if root != expected:
        raise SystemExit(f"refusing non-canonical output root: {root}")
    selected = candidates(root, args.older_than_days)
    report = {
        "mode": "apply" if args.apply else "dry-run",
        "root": str(root),
        "preserved": str(root / "release-evidence"),
        "paths": [str(path) for path in selected],
        "bytes": sum(
            child.stat().st_size
            for path in selected
            for child in ([path] if path.is_file() else path.rglob("*"))
            if child.is_file()
        ),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.apply:
        for path in selected:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()


if __name__ == "__main__":
    main()

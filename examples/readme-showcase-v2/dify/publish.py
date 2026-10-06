#!/usr/bin/env python3
"""Publish only the verified Dify build bundle; never upload the source checkout."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from build import HERE, REPOSITORY, REVISION, ROOT

SHARED = {"style.json", "index.html", "index.en.html", "evidence.md", "evidence.en.md", "showcase.css", "preview-motion.js"}
EXPECTED = SHARED | {f"{stem}{suffix}" for stem in ("dify", "dify-en") for suffix in (
    ".plan.json", ".diagram.json", "-static.diagram.json", ".svg", ".html", ".quality.json", ".delivery.json",
    "-static.svg", "-static.html", "-static.quality.json", "-static.delivery.json", "-motion.webp", "-motion.json",
)} | {"facts.json", "facts.en.json", "accuracy.json", "accuracy.en.json"}
SOURCE_FILES = {"build.py", "english.py", "publish.py", "capture_motion.mjs"} | (SHARED - {"style.json"})


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def prepare(build_dir: Path) -> dict[str, bytes]:
    """Validate everything before writing; keep local originals unchanged."""
    manifest = json.loads((build_dir / "manifest.json").read_text(encoding="utf-8"))
    if (manifest["repository"], manifest["revision"]) != (REPOSITORY, REVISION):
        raise ValueError("Unexpected source repository or revision")
    if (manifest["status"], manifest["independent_semantic_review"], manifest["dify_runtime"]) != ("draft", "pending", "not run"):
        raise ValueError("This publisher must preserve the draft acceptance boundary")
    if set(manifest["files"]) != EXPECTED or set(manifest["source_files"]) != SOURCE_FILES:
        raise ValueError("Unexpected build or source file list")
    for name, expected in manifest["source_files"].items():
        if digest((HERE / name).read_bytes()) != expected:
            raise ValueError(f"Stale build source: {name}")
    bundle = {}
    for name, expected in manifest["files"].items():
        if (build_dir / name).is_symlink():
            raise ValueError(f"Symlink is not a build artifact: {name}")
        data = (build_dir / name).read_bytes()
        if digest(data) != expected:
            raise ValueError(f"Build hash mismatch: {name}")
        bundle[name] = data
    originals = {}
    for name in sorted(EXPECTED):
        if not name.endswith(".delivery.json"):
            continue
        receipt = json.loads(bundle[name])
        originals[name] = digest(bundle[name])
        source = receipt["input"]["source"]
        source["path"] = Path(source["path"]).name
        for item in [source, *receipt["artifacts"].values()]:
            item["path"] = Path(item["path"]).name
            artifact = bundle[item["path"]]
            if item["sha256"] != digest(artifact) or item["bytes"] != len(artifact):
                raise ValueError(f"Delivery artifact mismatch: {name}: {item['path']}")
        runtime = receipt["request"]["render_options"]["runtime_source"]
        runtime["path"] = "../../../node_modules/gsap/dist/gsap.min.js"
        bundle[name] = encoded(receipt)
    public = copy.deepcopy(manifest)
    public.pop("source_root")
    public["publication"] = {
        "format": 1,
        "original_delivery_sha256": originals,
        "path_policy": "Delivery input/artifact paths are bundle-relative; runtime source is repository-relative from this bundle. Rendered bytes and evidence are unchanged. Original local receipts remain in the build directory.",
    }
    public["files"] = {name: digest(data) for name, data in sorted(bundle.items())}
    bundle["manifest.json"] = encoded(public)
    # A publication must not reveal a developer's checkout or machine identity.
    for name, data in bundle.items():
        if any(marker in data for marker in (b"/Users/", b"/home/", b"127.0.0.1:8769/")):
            raise ValueError(f"Local machine path in publication: {name}")
    return bundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=ROOT / "outputs/readme-showcase-v2/dify")
    parser.add_argument("--outdir", type=Path, default=ROOT / "gallery/cases/dify")
    args = parser.parse_args()
    source, target = args.build_dir.resolve(), args.outdir.resolve()
    if source == target:
        raise SystemExit("Publication must not overwrite original build receipts")
    bundle = prepare(source)
    if target.exists():
        unexpected = {p.name for p in target.iterdir()} - set(bundle)
        if unexpected or any(p.is_symlink() or not p.is_file() for p in target.iterdir()):
            raise SystemExit("Destination contains unrelated files; refusing to overwrite")
    target.mkdir(parents=True, exist_ok=True)
    for name, data in bundle.items():
        (target / name).write_bytes(data)
    print(f"Published {len(bundle)} files to {target}; semantic review remains pending")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build and verify full browser export matrices for current public icon systems."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import shutil
import subprocess
import sys
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from threading import Event, Thread
from typing import Any, Dict, Tuple


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anidiagram.cli import main as render_main


EXPORT_FORMATS: Tuple[str, ...] = (
    "svg",
    "html",
    "png",
    "webp",
    "gif",
    "apng",
    "mp4",
    "pdf",
    "lottie",
    "quality",
)
FORMAT_SHARDS = {
    "visual": EXPORT_FORMATS[:5],
    "motion": EXPORT_FORMATS[5:],
}
ANIMATED_FORMATS = ("webp", "gif", "apng", "mp4", "lottie")
CASES = (
    {
        "id": "diagram-core-v1",
        "icon_system": "diagram-core-v1",
        "version": "1.0.0",
        "icon_count": 56,
        "motion_contract": "showcase-v1",
        "spec": ROOT / "examples" / "diagram-core-v1-showcase.diagram.json",
        "style": ROOT / "styles" / "minimal-light.json",
        "catalog": ROOT / "assets" / "diagram-core" / "catalog.json",
        "motion_authority": ROOT / "runtime" / "motion-catalog.json",
        "authorities": (
            ROOT / "assets" / "diagram-core" / "releases" / "v1.0.0.json",
        ),
    },
    {
        "id": "illustrated-2.5",
        "icon_system": "illustrated",
        "version": "2.5.0",
        "icon_count": 56,
        "motion_contract": "illustrated-performance-v6",
        "spec": ROOT / "examples" / "illustrated-2.5-showcase.diagram.json",
        "style": ROOT / "styles" / "deep-tech.json",
        "catalog": ROOT / "assets" / "illustrated" / "catalog.json",
        "motion_authority": ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v6.json",
        "authorities": (
            ROOT / "assets" / "illustrated" / "reviews" / "2.5.0-batch-5-static-acceptance.json",
            ROOT / "assets" / "illustrated" / "reviews" / "2.5.0-batch-5-motion-acceptance.json",
            ROOT / "assets" / "illustrated" / "reviews" / "2.5.0-batches-6-10-static-acceptance.json",
            ROOT / "assets" / "illustrated" / "reviews" / "2.5.0-batches-6-10-motion-acceptance.json",
            ROOT / "assets" / "illustrated" / "reviews" / "2.5.0-convention-alignment-acceptance.json",
            ROOT / "assets" / "illustrated" / "reviews" / "2.5.0-template-acceptance.json",
            ROOT / "assets" / "illustrated" / "reviews" / "template-matrix-2.5.0-final.json",
        ),
    },
)
FRAGMENT_SCHEMA = "public-icon-system-export-evidence-fragment-v1"
SHARD_SCHEMA = "public-icon-system-export-evidence-shard-v1"
EVIDENCE_SCHEMA = "public-icon-system-export-evidence-v1"


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive number")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=ROOT / "outputs" / "release-evidence" / "icon-systems",
        help="Root directory for the two complete export matrices.",
    )
    parser.add_argument(
        "--evidence",
        type=Path,
        help="Evidence JSON path; defaults to <outdir>/public-icon-system-export-evidence.json.",
    )
    parser.add_argument("--fps", type=_positive_int, default=24)
    parser.add_argument("--frames", type=_positive_int, default=108)
    parser.add_argument("--scale", type=_positive_float, default=2.0)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--verify",
        action="store_true",
        help="Verify an existing evidence JSON and its artifacts without rendering.",
    )
    mode.add_argument(
        "--system",
        choices=[case["id"] for case in CASES],
        help="Build one public icon-system fragment for parallel CI execution.",
    )
    mode.add_argument(
        "--merge-fragments",
        action="store_true",
        help="Merge both public icon-system fragments and verify the complete matrix.",
    )
    parser.add_argument(
        "--shard",
        choices=list(FORMAT_SHARDS),
        help="Build one format shard for the selected public icon system.",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.shard and not args.system:
        raise SystemExit("--shard requires --system")
    outdir = _rooted(args.outdir)
    evidence_path = _rooted(args.evidence) if args.evidence else outdir / "public-icon-system-export-evidence.json"
    if args.verify:
        report = verify_evidence(evidence_path)
    elif args.merge_fragments:
        report = merge_fragments(outdir, evidence_path)
    elif args.system:
        report = build_fragment(args.system, outdir, args.fps, args.frames, args.scale, shard_id=args.shard)
    else:
        report = build_evidence(outdir, evidence_path, args.fps, args.frames, args.scale)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


def build_evidence(outdir: Path, evidence_path: Path, fps: int, frames: int, scale: float) -> Dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)
    systems = [_build_case(case, outdir, fps, frames, scale) for case in CASES]
    return _write_verified_evidence(evidence_path, systems, fps, frames, scale)


def build_fragment(
    system_id: str,
    outdir: Path,
    fps: int,
    frames: int,
    scale: float,
    *,
    shard_id: str | None = None,
) -> Dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)
    case = next(case for case in CASES if case["id"] == system_id)
    formats = FORMAT_SHARDS[shard_id] if shard_id else EXPORT_FORMATS
    result_name = f"result-{shard_id}.json" if shard_id else "result.json"
    system = _build_case(case, outdir, fps, frames, scale, formats=formats, result_name=result_name)
    suffix = f"-{shard_id}" if shard_id else ""
    fragment_path = outdir / f"{system_id}{suffix}-evidence-fragment.json"
    fragment = {
        "schema": SHARD_SCHEMA if shard_id else FRAGMENT_SCHEMA,
        "capture": {"renderer": "browser", "fps": fps, "frames": frames, "scale": scale},
        "formats": list(formats),
        "system": system,
    }
    if shard_id:
        fragment["shard"] = shard_id
    fragment_path.write_text(json.dumps(fragment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "fragment": _display_path(fragment_path),
        "system": system_id,
        "shard": shard_id,
        "formats": len(formats),
    }


def merge_fragments(outdir: Path, evidence_path: Path) -> Dict[str, Any]:
    shard_paths = [
        outdir / f'{case["id"]}-{shard_id}-evidence-fragment.json'
        for case in CASES
        for shard_id in FORMAT_SHARDS
    ]
    if all(path.is_file() for path in shard_paths):
        try:
            shard_fragments = [json.loads(path.read_text(encoding="utf-8")) for path in shard_paths]
            document = _merge_shard_fragment_documents(shard_fragments, outdir)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            return {"ok": False, "evidence": _display_path(evidence_path), "issues": [str(error)]}
        return _write_verified_document(evidence_path, document)

    fragments = []
    for case in CASES:
        fragment_path = outdir / f'{case["id"]}-evidence-fragment.json'
        if not fragment_path.is_file():
            return {
                "ok": False,
                "evidence": _display_path(evidence_path),
                "issues": [f"missing fragment: {_display_path(fragment_path)}"],
            }
        try:
            fragments.append(json.loads(fragment_path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            return {"ok": False, "evidence": _display_path(evidence_path), "issues": [str(error)]}
    try:
        document = _merge_fragment_documents(fragments)
    except ValueError as error:
        return {"ok": False, "evidence": _display_path(evidence_path), "issues": [str(error)]}
    return _write_verified_document(evidence_path, document)


def _merge_shard_fragment_documents(fragments: list[Dict[str, Any]], outdir: Path) -> Dict[str, Any]:
    expected_pairs = [
        (case["id"], shard_id)
        for case in CASES
        for shard_id in FORMAT_SHARDS
    ]
    by_pair: Dict[tuple[str, str], Dict[str, Any]] = {}
    for fragment in fragments:
        if fragment.get("schema") != SHARD_SCHEMA:
            raise ValueError("unexpected evidence shard schema")
        system = fragment.get("system")
        system_id = system.get("id") if isinstance(system, dict) else None
        shard_id = fragment.get("shard")
        pair = (system_id, shard_id)
        if not isinstance(system_id, str) or not isinstance(shard_id, str) or pair in by_pair:
            raise ValueError("evidence shards require unique public system and shard ids")
        by_pair[pair] = fragment
    if set(by_pair) != set(expected_pairs):
        expected = ", ".join(f"{system_id}/{shard_id}" for system_id, shard_id in expected_pairs)
        raise ValueError(f"expected evidence shards for: {expected}")

    first = by_pair[expected_pairs[0]]
    capture = first.get("capture")
    if not isinstance(capture, dict):
        raise ValueError("invalid evidence shard capture contract")
    systems = []
    for case in CASES:
        system_id = case["id"]
        system_fragments = [by_pair[(system_id, shard_id)] for shard_id in FORMAT_SHARDS]
        for shard_id, fragment in zip(FORMAT_SHARDS, system_fragments):
            if fragment.get("capture") != capture or tuple(fragment.get("formats", ())) != FORMAT_SHARDS[shard_id]:
                raise ValueError(f"{system_id}/{shard_id}: incompatible evidence shard contract")
        systems.append(_merge_system_shards(system_id, system_fragments, outdir))

    return {
        "schema": EVIDENCE_SCHEMA,
        "status": "generated",
        "capture": capture,
        "formats": list(EXPORT_FORMATS),
        "systems": systems,
    }


def _merge_system_shards(
    system_id: str,
    fragments: list[Dict[str, Any]],
    outdir: Path,
) -> Dict[str, Any]:
    systems = [fragment["system"] for fragment in fragments]
    identity_keys = (
        "id",
        "icon_system",
        "version",
        "icon_count",
        "motion_contract",
        "spec",
        "catalog",
        "motion_authority",
        "authorities",
    )
    baseline = {key: systems[0].get(key) for key in identity_keys}
    if any({key: system.get(key) for key in identity_keys} != baseline for system in systems[1:]):
        raise ValueError(f"{system_id}: evidence shard identities do not match")

    artifacts: Dict[str, Dict[str, Any]] = {}
    results = []
    for system in systems:
        for format_name, artifact in system.get("artifacts", {}).items():
            if format_name in artifacts:
                raise ValueError(f"{system_id}: duplicate artifact for {format_name}")
            artifacts[format_name] = artifact
        result_record = system.get("result")
        if not isinstance(result_record, dict) or not result_record.get("path"):
            raise ValueError(f"{system_id}: evidence shard result is missing")
        result_path = _resolve_path(result_record["path"])
        results.append(json.loads(result_path.read_text(encoding="utf-8")))
    if tuple(artifacts) != EXPORT_FORMATS:
        raise ValueError(f"{system_id}: evidence shards do not cover the formal export matrix")

    result_identity = {key: value for key, value in results[0].items() if key != "outputs"}
    if any({key: value for key, value in result.items() if key != "outputs"} != result_identity for result in results[1:]):
        raise ValueError(f"{system_id}: shard render results do not match")
    merged_result = dict(result_identity)
    merged_result["outputs"] = {
        format_name: next(result["outputs"][format_name] for result in results if format_name in result["outputs"])
        for format_name in EXPORT_FORMATS
    }
    result_path = outdir / system_id / "result.json"
    result_path.write_text(json.dumps(merged_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        **baseline,
        "result": _file_record(result_path),
        "artifacts": artifacts,
    }


def _merge_fragment_documents(fragments: list[Dict[str, Any]]) -> Dict[str, Any]:
    expected_ids = [case["id"] for case in CASES]
    by_id: Dict[str, Dict[str, Any]] = {}
    for fragment in fragments:
        if fragment.get("schema") != FRAGMENT_SCHEMA:
            raise ValueError("unexpected evidence fragment schema")
        system = fragment.get("system")
        system_id = system.get("id") if isinstance(system, dict) else None
        if not isinstance(system_id, str) or system_id in by_id:
            raise ValueError("evidence fragments require unique public system ids")
        by_id[system_id] = fragment
    if set(by_id) != set(expected_ids):
        raise ValueError(f"expected fragments for: {', '.join(expected_ids)}")

    first = by_id[expected_ids[0]]
    capture = first.get("capture")
    formats = first.get("formats")
    if not isinstance(capture, dict) or tuple(formats or ()) != EXPORT_FORMATS:
        raise ValueError("invalid fragment capture or format contract")
    for system_id in expected_ids[1:]:
        fragment = by_id[system_id]
        if fragment.get("capture") != capture or fragment.get("formats") != formats:
            raise ValueError("evidence fragments use incompatible capture contracts")

    return {
        "schema": EVIDENCE_SCHEMA,
        "status": "generated",
        "capture": capture,
        "formats": formats,
        "systems": [by_id[system_id]["system"] for system_id in expected_ids],
    }


def _write_verified_evidence(
    evidence_path: Path,
    systems: list[Dict[str, Any]],
    fps: int,
    frames: int,
    scale: float,
) -> Dict[str, Any]:
    document = {
        "schema": EVIDENCE_SCHEMA,
        "status": "generated",
        "capture": {"renderer": "browser", "fps": fps, "frames": frames, "scale": scale},
        "formats": list(EXPORT_FORMATS),
        "systems": systems,
    }
    return _write_verified_document(evidence_path, document)


def _write_verified_document(evidence_path: Path, document: Dict[str, Any]) -> Dict[str, Any]:
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = verify_evidence(evidence_path, require_verified_status=False)
    document["status"] = "verified" if report["ok"] else "verification-failed"
    document["verification"] = {
        "ok": report["ok"],
        "observations": report["observations"],
        "issues": report["issues"],
    }
    evidence_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # The second write changes only this evidence envelope, not any recorded
    # artifact. A separate --verify run replays the full independent audit.
    return report


def _build_case(
    case: Dict[str, Any],
    outdir: Path,
    fps: int,
    frames: int,
    scale: float,
    *,
    formats: Tuple[str, ...] = EXPORT_FORMATS,
    result_name: str = "result.json",
) -> Dict[str, Any]:
    case_outdir = outdir / case["id"]
    case_outdir.mkdir(parents=True, exist_ok=True)
    result_path = case_outdir / result_name
    arguments = [
        "--spec",
        str(case["spec"]),
        "--style",
        str(case["style"]),
        "--outdir",
        str(case_outdir),
        "--basename",
        case["id"],
        "--formats",
        ",".join(formats),
        "--html-runtime",
        "gsap",
        "--export-renderer",
        "browser",
        "--export-fps",
        str(fps),
        "--export-frames",
        str(frames),
        "--export-scale",
        str(scale),
        "--result",
        str(result_path),
    ]
    with _progress_heartbeat(f'building {case["id"]}'):
        with redirect_stdout(io.StringIO()):
            render_main(arguments)
    print(f'[release-evidence] completed {case["id"]}', file=sys.stderr, flush=True)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if not result.get("ok") or set(result["outputs"]) != set(formats):
        raise RuntimeError(f'{case["id"]} did not write the complete export matrix')
    for format_name, output in result["outputs"].items():
        if output.get("status") != "written":
            raise RuntimeError(f'{case["id"]} {format_name}: {output}')

    return {
        "id": case["id"],
        "icon_system": case["icon_system"],
        "version": case["version"],
        "icon_count": case["icon_count"],
        "motion_contract": case["motion_contract"],
        "spec": _file_record(case["spec"]),
        "catalog": _file_record(case["catalog"]),
        "motion_authority": _file_record(case["motion_authority"]),
        "authorities": [_file_record(path) for path in case["authorities"]],
        "result": _file_record(result_path),
        "artifacts": {
            format_name: {
                **_file_record(Path(output["path"])),
                "status": output["status"],
                **{
                    key: output[key]
                    for key in ("renderer", "fps", "frames", "scale", "loop_blend_frames")
                    if key in output
                },
            }
            for format_name, output in result["outputs"].items()
        },
    }


def verify_evidence(evidence_path: Path, *, require_verified_status: bool = True) -> Dict[str, Any]:
    issues = []
    observations: Dict[str, Any] = {}
    if not evidence_path.is_file():
        return {"ok": False, "evidence": str(evidence_path), "issues": ["evidence JSON is missing"]}
    try:
        document = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return {"ok": False, "evidence": str(evidence_path), "issues": [str(error)]}

    if document.get("schema") != EVIDENCE_SCHEMA:
        issues.append("unexpected evidence schema")
    if require_verified_status and document.get("status") != "verified":
        issues.append("evidence status is not verified")
    if tuple(document.get("formats", ())) != EXPORT_FORMATS:
        issues.append("export format matrix does not match the public contract")
    systems = document.get("systems", [])
    if [item.get("id") for item in systems] != [item["id"] for item in CASES]:
        issues.append("expected Diagram Core v1 and Illustrated 2.5 evidence entries")

    capture = document.get("capture", {})
    if capture.get("renderer") != "browser":
        issues.append("capture renderer must be browser")
    expected_fps = int(capture.get("fps", 0))
    expected_frames = int(capture.get("frames", 0))
    expected_scale = float(capture.get("scale", 0))
    if expected_fps < 1 or expected_frames < 2 or expected_scale <= 0:
        issues.append("capture metadata must use positive fps/scale and at least two frames")
    for system_index, system in enumerate(systems):
        system_id = system.get("id", "unknown")
        expected_case = CASES[system_index] if system_index < len(CASES) else None
        system_observations = {"distinct_frames": {}}
        observations[system_id] = system_observations
        if expected_case:
            for key in ("id", "icon_system", "version", "icon_count", "motion_contract"):
                if system.get(key) != expected_case[key]:
                    issues.append(f"{system_id}: {key} does not match the public release contract")
        for record in (
            system.get("spec"),
            system.get("catalog"),
            system.get("motion_authority"),
            system.get("result"),
            *system.get("authorities", []),
        ):
            _verify_file_record(record, issues, system_id)
        artifacts = system.get("artifacts", {})
        if set(artifacts) != set(EXPORT_FORMATS):
            issues.append(f"{system_id}: incomplete artifact matrix")
        for format_name in EXPORT_FORMATS:
            record = artifacts.get(format_name)
            _verify_file_record(record, issues, f"{system_id}/{format_name}")
            if not record:
                continue
            if record.get("status") != "written":
                issues.append(f"{system_id}/{format_name}: status is not written")
            if format_name in ANIMATED_FORMATS:
                if record.get("renderer") != "browser":
                    issues.append(f"{system_id}/{format_name}: renderer is not browser")
                if record.get("frames") != expected_frames:
                    issues.append(f"{system_id}/{format_name}: unexpected frame count")
                if record.get("fps") != expected_fps:
                    issues.append(f"{system_id}/{format_name}: unexpected fps")
                if float(record.get("scale", 0)) != expected_scale:
                    issues.append(f"{system_id}/{format_name}: unexpected scale")
        quality_record = artifacts.get("quality")
        if quality_record:
            quality_path = _resolve_path(quality_record["path"])
            if quality_path.is_file():
                quality = json.loads(quality_path.read_text(encoding="utf-8"))
                if quality.get("summary") != {"errors": 0, "warnings": 0, "issues": 0}:
                    issues.append(f"{system_id}/quality: report is not clean")

        expected_icons = _expected_icon_ids(expected_case) if expected_case else set()
        spec_record = system.get("spec")
        spec = None
        if spec_record and _resolve_path(spec_record["path"]).is_file():
            spec_source = _resolve_path(spec_record["path"]).read_text(encoding="utf-8")
            spec = json.loads(spec_source)
            if spec.get("icon_system") != system.get("icon_system"):
                issues.append(f"{system_id}/spec: icon system changed")
            _check_exact_icon_coverage(
                [(item.get("id"), item.get("icon")) for item in spec.get("nodes", [])],
                expected_icons,
                issues,
                f"{system_id}/spec",
            )
            if '"icon_motion"' in spec_source:
                issues.append(f"{system_id}/spec: explicit icon_motion is forbidden")

        result_record = system.get("result")
        if result_record and _resolve_path(result_record["path"]).is_file():
            result = json.loads(_resolve_path(result_record["path"]).read_text(encoding="utf-8"))
            if not result.get("ok") or result.get("icon_system") != system.get("icon_system"):
                issues.append(f"{system_id}/result: render identity changed")
            if set(result.get("outputs", {})) != set(EXPORT_FORMATS):
                issues.append(f"{system_id}/result: incomplete result matrix")

        html_record = artifacts.get("html")
        if html_record and _resolve_path(html_record["path"]).is_file():
            motion = _motion_manifest_from_html(_resolve_path(html_record["path"]))
            system_observations["automatic_motion_icon_count"] = len(motion.get("icons", []))
            _check_exact_icon_coverage(
                [(item.get("node_id"), item.get("icon")) for item in motion.get("icons", [])],
                expected_icons,
                issues,
                f"{system_id}/html",
            )
            if spec is not None:
                spec_pairs = {(item.get("id"), item.get("icon")) for item in spec.get("nodes", [])}
                motion_pairs = {(item.get("node_id"), item.get("icon")) for item in motion.get("icons", [])}
                if motion_pairs != spec_pairs:
                    issues.append(f"{system_id}/html: manifest node/icon mapping changed")
            if system.get("icon_system") == "illustrated" and not all(
                item.get("motion_contract") == system.get("motion_contract")
                and item.get("motion_status") == "approved"
                for item in motion.get("icons", [])
            ):
                issues.append(f"{system_id}/html: public motion contract changed")

        for format_name in ANIMATED_FORMATS:
            record = artifacts.get(format_name)
            if not record or not _resolve_path(record["path"]).is_file():
                continue
            try:
                count = _distinct_frames(_resolve_path(record["path"]), format_name)
                system_observations["distinct_frames"][format_name] = count
                if count < 2:
                    issues.append(f"{system_id}/{format_name}: animation has fewer than two distinct frames")
            except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
                issues.append(f"{system_id}/{format_name}: frame audit failed: {error}")

        lottie_record = artifacts.get("lottie")
        if spec is not None and lottie_record and _resolve_path(lottie_record["path"]).is_file():
            try:
                per_node = _per_node_distinct_frames(_resolve_path(lottie_record["path"]), spec)
                system_observations["minimum_node_distinct_frames"] = min(per_node.values(), default=0)
                system_observations["per_node_distinct_frames"] = per_node
                static_nodes = sorted(node_id for node_id, count in per_node.items() if count < 2)
                if static_nodes:
                    issues.append(f'{system_id}/lottie: static icon regions: {", ".join(static_nodes)}')
            except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
                issues.append(f"{system_id}/lottie: per-icon frame audit failed: {error}")

    return {
        "ok": not issues,
        "evidence": _display_path(evidence_path),
        "systems": len(systems),
        "formats": len(EXPORT_FORMATS),
        "observations": observations,
        "issues": issues,
    }


def _verify_file_record(record: Any, issues: list, label: str) -> None:
    if not isinstance(record, dict) or not record.get("path"):
        issues.append(f"{label}: missing file record")
        return
    path = _resolve_path(record["path"])
    if not path.is_file():
        issues.append(f"{label}: missing {path}")
        return
    if path.stat().st_size != record.get("bytes"):
        issues.append(f"{label}: byte count changed")
    if _sha256(path) != record.get("sha256"):
        issues.append(f"{label}: sha256 changed")


def _distinct_frames(path: Path, format_name: str) -> int:
    if format_name in {"gif", "webp", "apng"}:
        try:
            from PIL import Image
        except ImportError as error:
            raise RuntimeError("Pillow is required") from error
        digests = set()
        with Image.open(path) as image:
            for index in range(getattr(image, "n_frames", 1)):
                image.seek(index)
                digests.add(hashlib.sha256(image.convert("RGB").tobytes()).hexdigest())
        return len(digests)
    if format_name == "lottie":
        document = json.loads(path.read_text(encoding="utf-8"))
        return len({_embedded_image_digest(asset.get("p")) for asset in document.get("assets", []) if asset.get("p")})
    if format_name == "mp4":
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg is required")
        completed = subprocess.run(
            [ffmpeg, "-v", "error", "-i", str(path), "-f", "framemd5", "-"],
            check=True,
            capture_output=True,
            text=True,
        )
        digests = {
            line.rsplit(",", 1)[-1].strip()
            for line in completed.stdout.splitlines()
            if line and not line.startswith("#") and "," in line
        }
        return len(digests)
    raise ValueError(f"unsupported animated format: {format_name}")


def _expected_icon_ids(case: Dict[str, Any]) -> set[str]:
    catalog = json.loads(case["catalog"].read_text(encoding="utf-8"))
    catalog_icons = [item["id"] for item in catalog.get("icons", []) if item.get("status") == "approved"]
    if len(catalog_icons) != case["icon_count"] or len(set(catalog_icons)) != len(catalog_icons):
        raise RuntimeError(f'{case["id"]}: approved catalog identity is inconsistent')
    expected = set(catalog_icons)
    if case["icon_system"] == "illustrated":
        contract = json.loads(case["motion_authority"].read_text(encoding="utf-8"))
        performance_icons = [item.get("icon") for item in contract.get("performances", [])]
        if len(performance_icons) != len(set(performance_icons)) or set(performance_icons) != expected:
            raise RuntimeError(f'{case["id"]}: public motion contract does not exactly cover the catalog')
    return expected


def _check_exact_icon_coverage(
    entries: list[tuple[Any, Any]], expected_icons: set[str], issues: list, label: str
) -> None:
    node_ids = [node_id for node_id, _ in entries]
    icons = [icon for _, icon in entries]
    if any(not isinstance(node_id, str) or not node_id for node_id in node_ids):
        issues.append(f"{label}: missing node identity")
    if len(node_ids) != len(set(node_ids)):
        issues.append(f"{label}: duplicate node identity")
    if len(icons) != len(set(icons)):
        issues.append(f"{label}: duplicate icon identity")
    if set(icons) != expected_icons:
        issues.append(f"{label}: icon set does not exactly match the approved catalog")


def _embedded_image_digest(value: Any) -> str:
    if not isinstance(value, str) or "," not in value:
        raise ValueError("invalid embedded image")
    encoded = value.split(",", 1)[1]
    try:
        from PIL import Image
    except ImportError as error:
        raise RuntimeError("Pillow is required") from error
    with Image.open(io.BytesIO(base64.b64decode(encoded))) as image:
        return hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()


def _per_node_distinct_frames(path: Path, spec: Dict[str, Any]) -> Dict[str, int]:
    try:
        from PIL import Image
    except ImportError as error:
        raise RuntimeError("Pillow is required") from error
    document = json.loads(path.read_text(encoding="utf-8"))
    canvas = spec.get("canvas", {})
    width, height = canvas.get("width"), canvas.get("height")
    if not width or not height:
        raise ValueError("spec canvas is required for per-icon frame audit")
    scale_x = document.get("w", 0) / width
    scale_y = document.get("h", 0) / height
    if scale_x <= 0 or scale_y <= 0:
        raise ValueError("invalid Lottie canvas")
    digests = {str(node["id"]): set() for node in spec.get("nodes", [])}
    for asset in document.get("assets", []):
        value = asset.get("p")
        if not isinstance(value, str) or "," not in value:
            continue
        with Image.open(io.BytesIO(base64.b64decode(value.split(",", 1)[1]))) as image:
            rgb = image.convert("RGB")
            for node in spec.get("nodes", []):
                x, y = node["position"]
                node_width, node_height = node["size"]
                box = (
                    round(x * scale_x),
                    round(y * scale_y),
                    round((x + node_width) * scale_x),
                    round((y + node_height) * scale_y),
                )
                digest = hashlib.sha256(rgb.crop(box).tobytes()).hexdigest()
                digests[str(node["id"])].add(digest)
    return {node_id: len(values) for node_id, values in digests.items()}


def _motion_manifest_from_html(path: Path) -> Dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    marker = '<script type="application/json" id="anidiagram-motion-manifest">'
    start = source.index(marker) + len(marker)
    return json.loads(source[start : source.index("</script>", start)])


def _file_record(path: Path) -> Dict[str, Any]:
    return {"path": _display_path(path), "bytes": path.stat().st_size, "sha256": _sha256(path)}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return str(resolved)


def _resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _rooted(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


@contextmanager
def _progress_heartbeat(label: str, interval_seconds: float = 60.0):
    """Keep long browser-export steps observable on hosted CI runners."""

    stopped = Event()

    def report_progress() -> None:
        elapsed = 0.0
        while not stopped.wait(interval_seconds):
            elapsed += interval_seconds
            print(
                f"[release-evidence] {label} ({int(elapsed)}s elapsed)",
                file=sys.stderr,
                flush=True,
            )

    print(f"[release-evidence] {label}", file=sys.stderr, flush=True)
    reporter = Thread(target=report_progress, name="release-evidence-heartbeat", daemon=True)
    reporter.start()
    try:
        yield
    finally:
        stopped.set()
        reporter.join()


if __name__ == "__main__":
    main()

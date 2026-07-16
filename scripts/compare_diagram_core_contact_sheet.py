#!/usr/bin/env python3
"""Compare or explicitly approve deterministic Diagram Core browser captures."""

import argparse
import copy
import hashlib
import io
import json
import math
import os
import stat
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


CAPTURE_SCHEMA = "anidiagram.diagram-core.capture"
CAPTURE_VERSION = 1


class VisualComparisonError(ValueError):
    """Raised when a comparison cannot be performed safely."""


@dataclass(frozen=True)
class ComparisonReport:
    differing_pixels: int
    total_pixels: int
    diff_ratio: float
    passed: bool


def _validate_thresholds(channel_tolerance, max_diff_ratio):
    if isinstance(channel_tolerance, bool) or not isinstance(channel_tolerance, int):
        raise VisualComparisonError("channel tolerance must be an integer")
    if not 0 <= channel_tolerance <= 255:
        raise VisualComparisonError("channel tolerance must be between 0 and 255")
    if not isinstance(max_diff_ratio, (int, float)) or isinstance(max_diff_ratio, bool):
        raise VisualComparisonError("maximum diff ratio must be numeric")
    if not math.isfinite(max_diff_ratio) or not 0 <= max_diff_ratio <= 1:
        raise VisualComparisonError("maximum diff ratio must be between 0 and 1")


def _atomic_write_bytes(path, payload, mode=0o644):
    target = Path(path)
    _prepare_output_path(target)
    descriptor = None
    temp_path = None
    try:
        descriptor, temp_name = tempfile.mkstemp(
            prefix=".{0}.".format(target.name),
            suffix=".tmp",
            dir=str(target.parent),
        )
        temp_path = Path(temp_name)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(str(temp_path), mode)
        os.replace(str(temp_path), str(target))
        temp_path = None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def _write_heatmap(path, mask, size):
    heatmap = Image.new("RGBA", size, (0, 0, 0, 0))
    pixels = [(255, 0, 0, 255) if differs else (0, 0, 0, 0) for differs in mask]
    if hasattr(heatmap, "put_flattened_data"):
        heatmap.put_flattened_data(pixels)
    else:  # Pillow 9-11, supported by the project's Python 3.9 floor.
        heatmap.putdata(pixels)
    payload = io.BytesIO()
    heatmap.save(payload, format="PNG")
    _atomic_write_bytes(path, payload.getvalue())


def compare_images(
    baseline,
    candidate,
    channel_tolerance=8,
    max_diff_ratio=0.01,
    diff_output=None,
):
    """Compare two Pillow images using an inclusive per-channel tolerance."""

    _validate_thresholds(channel_tolerance, max_diff_ratio)
    if baseline.size != candidate.size:
        raise VisualComparisonError(
            "image dimensions differ: baseline={0} candidate={1}".format(
                baseline.size,
                candidate.size,
            )
        )
    baseline_rgba = baseline.convert("RGBA")
    candidate_rgba = candidate.convert("RGBA")
    mask = []
    baseline_pixels = (
        baseline_rgba.get_flattened_data()
        if hasattr(baseline_rgba, "get_flattened_data")
        else baseline_rgba.getdata()
    )
    candidate_pixels = (
        candidate_rgba.get_flattened_data()
        if hasattr(candidate_rgba, "get_flattened_data")
        else candidate_rgba.getdata()
    )
    for baseline_pixel, candidate_pixel in zip(baseline_pixels, candidate_pixels):
        mask.append(
            any(
                abs(left - right) > channel_tolerance
                for left, right in zip(baseline_pixel, candidate_pixel)
            )
        )
    differing_pixels = sum(mask)
    total_pixels = baseline_rgba.width * baseline_rgba.height
    diff_ratio = differing_pixels / total_pixels if total_pixels else 0.0
    report = ComparisonReport(
        differing_pixels=differing_pixels,
        total_pixels=total_pixels,
        diff_ratio=diff_ratio,
        passed=diff_ratio <= max_diff_ratio,
    )
    if diff_output is not None and not report.passed:
        _write_heatmap(Path(diff_output), mask, baseline_rgba.size)
    return report


def _absolute(path):
    return Path(os.path.abspath(os.fspath(path)))


def _check_no_symlink_components(path):
    target = _absolute(path)
    current = Path(target.anchor)
    for part in target.parts[1:]:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise VisualComparisonError("symlink path is not permitted: {0}".format(path))


def _prepare_output_path(path):
    target = _absolute(path)
    _check_no_symlink_components(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    _check_no_symlink_components(target.parent)
    if target.exists() and not target.is_file():
        raise VisualComparisonError("output must be a regular file: {0}".format(path))


def _validate_output_path(path):
    target = _absolute(path)
    _check_no_symlink_components(target)
    if target.exists() and not target.is_file():
        raise VisualComparisonError("output must be a regular file: {0}".format(path))


def _require_regular_file(path, label):
    target = _absolute(path)
    _check_no_symlink_components(target)
    try:
        info = target.stat()
    except FileNotFoundError as error:
        raise VisualComparisonError("{0} does not exist: {1}".format(label, path)) from error
    if not stat.S_ISREG(info.st_mode):
        raise VisualComparisonError("{0} must be a regular file: {1}".format(label, path))
    return target


def _paths_alias(left, right):
    left_path = _absolute(left)
    right_path = _absolute(right)
    if os.path.normcase(str(left_path)) == os.path.normcase(str(right_path)):
        return True
    if left_path.exists() and right_path.exists():
        try:
            return os.path.samefile(str(left_path), str(right_path))
        except OSError:
            return False
    return False


def _reject_aliases(labeled_paths):
    entries = list(labeled_paths)
    for index, (left_label, left) in enumerate(entries):
        for right_label, right in entries[index + 1 :]:
            if _paths_alias(left, right):
                raise VisualComparisonError(
                    "path alias is not permitted: {0} and {1}".format(
                        left_label,
                        right_label,
                    )
                )


def _sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_metadata(path, label):
    metadata_path = _require_regular_file(path, label)
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise VisualComparisonError("{0} is not valid UTF-8 JSON".format(label)) from error
    if not isinstance(payload, dict):
        raise VisualComparisonError("{0} must contain a JSON object".format(label))
    return payload


def _nested(metadata, keys, label):
    value = metadata
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            raise VisualComparisonError(
                "{0} is missing {1}".format(label, ".".join(keys))
            )
        value = value[key]
    return value


def _validate_capture_metadata(metadata, image_path, label, require_approval=False):
    if metadata.get("schema") != CAPTURE_SCHEMA or metadata.get("version") != CAPTURE_VERSION:
        raise VisualComparisonError("{0} has an unsupported capture schema".format(label))
    expected_hash = _nested(metadata, ("image", "sha256"), label)
    actual_hash = _sha256_file(image_path)
    if expected_hash != actual_hash:
        raise VisualComparisonError(
            "{0} image SHA-256 does not match metadata".format(label)
        )
    try:
        with Image.open(str(image_path)) as image:
            actual_dimensions = [image.width, image.height]
            image.load()
    except (OSError, ValueError) as error:
        raise VisualComparisonError("{0} is not a readable image".format(label)) from error
    expected_dimensions = [
        _nested(metadata, ("image", "width"), label),
        _nested(metadata, ("image", "height"), label),
    ]
    if expected_dimensions != actual_dimensions:
        raise VisualComparisonError(
            "{0} image dimensions do not match metadata".format(label)
        )
    for key, description in (
        ("external_requests", "external requests"),
        ("animation_count", "animations"),
        ("transition_count", "transitions"),
    ):
        if _nested(metadata, ("capture", key), label) != 0:
            raise VisualComparisonError("{0} reports nonzero {1}".format(label, description))
    for keys in (
        ("browser", "playwright_version"),
        ("browser", "chromium_version"),
        ("source_assets", "joint_sha256"),
    ):
        value = _nested(metadata, keys, label)
        if not isinstance(value, str) or not value.strip():
            raise VisualComparisonError(
                "{0} has an invalid {1}".format(label, ".".join(keys))
            )
    if require_approval:
        approval = metadata.get("approval")
        if not isinstance(approval, dict):
            raise VisualComparisonError("baseline metadata is not explicitly approved")
        for key in ("timestamp_utc", "reviewer", "note", "baseline_sha256"):
            value = approval.get(key)
            if not isinstance(value, str) or not value.strip():
                raise VisualComparisonError(
                    "baseline approval is missing {0}".format(key)
                )
        if approval["baseline_sha256"] != actual_hash:
            raise VisualComparisonError("baseline approval hash does not match baseline image")
    return actual_hash


def _ensure_capture_compatibility(baseline_metadata, candidate_metadata):
    fields = (
        (("source_assets", "joint_sha256"), "source asset digest"),
        (("browser", "playwright_version"), "Playwright version"),
        (("browser", "chromium_version"), "Chromium version"),
    )
    for keys, label in fields:
        baseline_value = _nested(baseline_metadata, keys, "baseline metadata")
        candidate_value = _nested(candidate_metadata, keys, "candidate metadata")
        if baseline_value != candidate_value:
            raise VisualComparisonError("{0} does not match approved baseline".format(label))


def _snapshot(path):
    target = Path(path)
    if not target.exists():
        return None
    return target.read_bytes(), target.stat().st_mode & 0o777


def _restore(path, snapshot):
    target = Path(path)
    if snapshot is None:
        try:
            target.unlink()
        except FileNotFoundError:
            pass
        return
    payload, mode = snapshot
    _atomic_write_bytes(target, payload, mode=mode)


def _publish_approval(baseline_path, baseline_payload, metadata_path, metadata_payload):
    baseline_snapshot = _snapshot(baseline_path)
    metadata_snapshot = _snapshot(metadata_path)
    attempted_baseline = False
    attempted_metadata = False
    try:
        attempted_baseline = True
        _atomic_write_bytes(baseline_path, baseline_payload)
        attempted_metadata = True
        _atomic_write_bytes(metadata_path, metadata_payload)
    except Exception as error:
        rollback_errors = []
        for path, snapshot, attempted in (
            (metadata_path, metadata_snapshot, attempted_metadata),
            (baseline_path, baseline_snapshot, attempted_baseline),
        ):
            if not attempted:
                continue
            try:
                _restore(path, snapshot)
            except Exception as rollback_error:  # pragma: no cover - catastrophic I/O
                rollback_errors.append(str(rollback_error))
        if rollback_errors:
            raise VisualComparisonError(
                "approval publish failed and rollback was incomplete: {0}".format(
                    "; ".join(rollback_errors)
                )
            ) from error
        raise


def accept_candidate(
    candidate,
    candidate_metadata,
    baseline,
    baseline_metadata,
    reviewer,
    note,
):
    reviewer_value = reviewer.strip() if isinstance(reviewer, str) else ""
    note_value = note.strip() if isinstance(note, str) else ""
    if not reviewer_value:
        raise VisualComparisonError("reviewer must be nonempty after stripping whitespace")
    if not note_value:
        raise VisualComparisonError("approval note must be nonempty after stripping whitespace")
    _reject_aliases(
        (
            ("candidate", candidate),
            ("candidate metadata", candidate_metadata),
            ("baseline", baseline),
            ("baseline metadata", baseline_metadata),
        )
    )
    candidate_path = _require_regular_file(candidate, "candidate")
    candidate_metadata_path = _require_regular_file(
        candidate_metadata,
        "candidate metadata",
    )
    _prepare_output_path(baseline)
    _prepare_output_path(baseline_metadata)
    metadata = _read_metadata(candidate_metadata_path, "candidate metadata")
    digest = _validate_capture_metadata(metadata, candidate_path, "candidate")
    approved = copy.deepcopy(metadata)
    approved["approval"] = {
        "timestamp_utc": datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
        "reviewer": reviewer_value,
        "note": note_value,
        "candidate_sha256": digest,
        "baseline_sha256": digest,
    }
    metadata_payload = (
        json.dumps(approved, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    _publish_approval(
        _absolute(baseline),
        candidate_path.read_bytes(),
        _absolute(baseline_metadata),
        metadata_payload,
    )
    return digest, reviewer_value


def compare_capture_files(
    baseline,
    baseline_metadata,
    candidate,
    candidate_metadata,
    channel_tolerance=8,
    max_diff_ratio=0.01,
    diff_output=None,
):
    paths = [
        ("baseline", baseline),
        ("baseline metadata", baseline_metadata),
        ("candidate", candidate),
        ("candidate metadata", candidate_metadata),
    ]
    if diff_output is not None:
        paths.append(("diff output", diff_output))
    _reject_aliases(paths)
    if diff_output is not None:
        _validate_output_path(diff_output)
    baseline_path = _require_regular_file(baseline, "baseline")
    candidate_path = _require_regular_file(candidate, "candidate")
    baseline_payload = _read_metadata(baseline_metadata, "baseline metadata")
    candidate_payload = _read_metadata(candidate_metadata, "candidate metadata")
    _validate_capture_metadata(
        baseline_payload,
        baseline_path,
        "baseline",
        require_approval=True,
    )
    _validate_capture_metadata(candidate_payload, candidate_path, "candidate")
    _ensure_capture_compatibility(baseline_payload, candidate_payload)
    try:
        with Image.open(str(baseline_path)) as baseline_image:
            baseline_rgba = baseline_image.convert("RGBA")
        with Image.open(str(candidate_path)) as candidate_image:
            candidate_rgba = candidate_image.convert("RGBA")
    except (OSError, ValueError) as error:
        raise VisualComparisonError("capture image could not be decoded") from error
    return compare_images(
        baseline_rgba,
        candidate_rgba,
        channel_tolerance=channel_tolerance,
        max_diff_ratio=max_diff_ratio,
        diff_output=diff_output,
    )


def _parser():
    parser = argparse.ArgumentParser(
        description="Compare or explicitly approve a Diagram Core browser capture."
    )
    parser.add_argument("--accept", action="store_true")
    parser.add_argument("--reviewer")
    parser.add_argument("--approval-note")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--baseline-metadata", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--candidate-metadata", required=True)
    parser.add_argument("--max-diff-ratio", type=float, default=0.01)
    parser.add_argument("--channel-tolerance", type=int, default=8)
    parser.add_argument("--diff-output")
    return parser


def main(arguments=None):
    parser = _parser()
    args = parser.parse_args(arguments)
    try:
        if args.accept:
            if args.diff_output is not None:
                raise VisualComparisonError("--diff-output is not valid with --accept")
            digest, reviewer = accept_candidate(
                args.candidate,
                args.candidate_metadata,
                args.baseline,
                args.baseline_metadata,
                args.reviewer,
                args.approval_note,
            )
            print("accepted sha256={0} reviewer={1}".format(digest, reviewer))
            return 0
        if args.reviewer is not None or args.approval_note is not None:
            raise VisualComparisonError("reviewer and approval note require --accept")
        report = compare_capture_files(
            args.baseline,
            args.baseline_metadata,
            args.candidate,
            args.candidate_metadata,
            channel_tolerance=args.channel_tolerance,
            max_diff_ratio=args.max_diff_ratio,
            diff_output=args.diff_output,
        )
        print(
            "differing_pixels={0} total_pixels={1} diff_ratio={2:.8f} passed={3}".format(
                report.differing_pixels,
                report.total_pixels,
                report.diff_ratio,
                str(report.passed).lower(),
            )
        )
        return 0 if report.passed else 1
    except VisualComparisonError as error:
        print("error: {0}".format(error), file=sys.stderr)
        return 2
    except OSError as error:
        print("error: I/O failure: {0}".format(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

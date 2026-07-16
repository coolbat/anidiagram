#!/usr/bin/env python3
"""Compare or explicitly approve deterministic Diagram Core browser captures."""

import argparse
import copy
import errno
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
REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_RELATIVE_PATH = "gallery/diagram-core/index.html"
SOURCE_ASSET_PATHS = tuple(
    sorted(
        [
            "assets/diagram-core/catalog.json",
            "assets/diagram-core/tokens.css",
        ]
        + [
            "assets/diagram-core/{0}/{1}.{2}".format(directory, icon, suffix)
            for icon in ("agent", "api", "database", "server")
            for directory, suffix in (("icons", "svg"), ("manifests", "json"))
        ]
    )
)
VIEWPORT = {"width": 1280, "height": 900, "device_scale_factor": 1}
LOCATOR_SELECTOR = "#diagram-core-regression-grid"
EXPECTED_CELLS = 288
EXPECTED_WIDTH = 1248
EXPECTED_HEIGHT = 2496


class VisualComparisonError(ValueError):
    """Raised when a comparison cannot be performed safely."""


@dataclass(frozen=True)
class ComparisonReport:
    differing_pixels: int
    total_pixels: int
    diff_ratio: float
    passed: bool


@dataclass(frozen=True)
class FileSignature:
    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int
    mode: int


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    payload: bytes
    mode: int
    signature: FileSignature


@dataclass(frozen=True)
class ProvenanceFile:
    relative_path: str
    snapshot: FileSnapshot
    digest: str


@dataclass(frozen=True)
class RepositoryProvenance:
    package_lock_snapshot: FileSnapshot
    index_snapshot: FileSnapshot
    playwright_version: str
    source_assets: tuple
    source_assets_joint_sha256: str


@dataclass(frozen=True)
class ValidatedCapture:
    snapshot: FileSnapshot
    digest: str
    image: Image.Image
    repository_provenance: RepositoryProvenance


def _validate_thresholds(channel_tolerance, max_diff_ratio):
    if isinstance(channel_tolerance, bool) or not isinstance(channel_tolerance, int):
        raise VisualComparisonError("channel tolerance must be an integer")
    if not 0 <= channel_tolerance <= 255:
        raise VisualComparisonError("channel tolerance must be between 0 and 255")
    if not isinstance(max_diff_ratio, (int, float)) or isinstance(max_diff_ratio, bool):
        raise VisualComparisonError("maximum diff ratio must be numeric")
    if not math.isfinite(max_diff_ratio) or not 0 <= max_diff_ratio <= 1:
        raise VisualComparisonError("maximum diff ratio must be between 0 and 1")


def _write_heatmap(path, mask, size):
    pixels = bytearray(len(mask) * 4)
    for index, differs in enumerate(mask):
        if differs:
            offset = index * 4
            pixels[offset : offset + 4] = b"\xff\x00\x00\xff"
    heatmap = Image.frombytes("RGBA", size, bytes(pixels))
    payload = io.BytesIO()
    heatmap.save(payload, format="PNG")
    target = _absolute(path)
    _prepare_output_path(target)
    target_snapshot = _output_snapshot(target)
    mode = target_snapshot.mode if target_snapshot is not None else 0o644
    staged, _ = _stage_approval_payload(
        target,
        payload.getvalue(),
        mode,
        ".tmp",
    )
    _publish_staged_heatmap(
        target,
        staged,
        target_snapshot,
        lambda: None,
    )


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
    baseline_rgba = baseline if baseline.mode == "RGBA" else baseline.convert("RGBA")
    candidate_rgba = candidate if candidate.mode == "RGBA" else candidate.convert("RGBA")
    mask = bytearray()
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
            int(any(
                abs(left - right) > channel_tolerance
                for left, right in zip(baseline_pixel, candidate_pixel)
            ))
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


def _file_signature(info):
    return FileSignature(
        device=info.st_dev,
        inode=info.st_ino,
        size=info.st_size,
        mtime_ns=info.st_mtime_ns,
        ctime_ns=info.st_ctime_ns,
        mode=info.st_mode,
    )


def _replacement_signature(signature):
    return (
        signature.device,
        signature.inode,
        signature.size,
        signature.mtime_ns,
        signature.mode,
    )


def _read_file_snapshot(path, label):
    """Read one immutable payload through a no-follow descriptor."""

    target = _absolute(path)
    _check_no_symlink_components(target)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = None
    try:
        descriptor = os.open(str(target), flags)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise VisualComparisonError(
                "{0} must be a regular file: {1}".format(label, path)
            )
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = None
            payload = handle.read()
            after = os.fstat(handle.fileno())
    except FileNotFoundError as error:
        raise VisualComparisonError(
            "{0} does not exist: {1}".format(label, path)
        ) from error
    except OSError as error:
        raise VisualComparisonError(
            "{0} could not be read safely: {1}".format(label, path)
        ) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)

    before_signature = _file_signature(before)
    after_signature = _file_signature(after)
    if before_signature != after_signature or len(payload) != after.st_size:
        raise VisualComparisonError("{0} changed while it was read".format(label))
    try:
        path_info = os.stat(str(target), follow_symlinks=False)
    except (FileNotFoundError, OSError) as error:
        raise VisualComparisonError("{0} changed while it was read".format(label)) from error
    if _file_signature(path_info) != after_signature:
        raise VisualComparisonError("{0} changed while it was read".format(label))
    return FileSnapshot(
        path=target,
        payload=payload,
        mode=stat.S_IMODE(after.st_mode),
        signature=after_signature,
    )


def _ensure_snapshot_current(snapshot, label):
    _check_no_symlink_components(snapshot.path)
    try:
        current = os.stat(str(snapshot.path), follow_symlinks=False)
    except (FileNotFoundError, OSError) as error:
        raise VisualComparisonError("{0} changed during comparison".format(label)) from error
    if _file_signature(current) != snapshot.signature:
        raise VisualComparisonError("{0} changed during comparison".format(label))


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


def _sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def _read_metadata_snapshot(path, label):
    snapshot = _read_file_snapshot(path, label)
    try:
        payload = json.loads(snapshot.payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise VisualComparisonError("{0} is not valid UTF-8 JSON".format(label)) from error
    if not isinstance(payload, dict):
        raise VisualComparisonError("{0} must contain a JSON object".format(label))
    return payload, snapshot


def _nested(metadata, keys, label):
    value = metadata
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            raise VisualComparisonError(
                "{0} is missing {1}".format(label, ".".join(keys))
            )
        value = value[key]
    return value


def _require_exact_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise VisualComparisonError(
            "{0} must contain exactly: {1}".format(label, ", ".join(sorted(expected)))
        )


def _require_nonempty_string(value, label):
    if not isinstance(value, str) or not value.strip():
        raise VisualComparisonError("{0} must be a nonempty string".format(label))
    return value


def _require_exact_integer(value, expected, label):
    if type(value) is not int or value != expected:
        raise VisualComparisonError(
            "{0} must be the exact integer {1}".format(label, expected)
        )
    return value


def _require_sha256(value, label):
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise VisualComparisonError("{0} must be a lowercase SHA-256".format(label))
    return value


def _capture_metadata_digest(metadata):
    capture = copy.deepcopy(metadata)
    capture.pop("approval", None)
    canonical = json.dumps(
        capture,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(canonical)


def _metadata_image_path(path):
    target = _absolute(path)
    try:
        return target.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(target)


def _ensure_repository_provenance_current(provenance):
    snapshots = (
        (provenance.package_lock_snapshot, "package lock"),
        (provenance.index_snapshot, "canonical Diagram Core index"),
    ) + tuple(
        (
            entry.snapshot,
            "canonical source asset {0}".format(entry.relative_path),
        )
        for entry in provenance.source_assets
    )
    for snapshot, label in snapshots:
        _ensure_snapshot_current(snapshot, label)


def _read_repository_provenance():
    package_lock_snapshot = _read_file_snapshot(
        REPO_ROOT / "package-lock.json",
        "package lock",
    )
    try:
        lock = json.loads(package_lock_snapshot.payload.decode("utf-8"))
        version = lock["packages"]["node_modules/playwright"]["version"]
    except (UnicodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise VisualComparisonError("package lock does not pin Playwright") from error
    playwright_version = _require_nonempty_string(
        version,
        "locked Playwright version",
    )
    index_snapshot = _read_file_snapshot(
        REPO_ROOT / INDEX_RELATIVE_PATH,
        "canonical Diagram Core index",
    )
    source_assets = []
    for relative_path in SOURCE_ASSET_PATHS:
        snapshot = _read_file_snapshot(
            REPO_ROOT / relative_path,
            "canonical source asset {0}".format(relative_path),
        )
        source_assets.append(
            ProvenanceFile(
                relative_path=relative_path,
                snapshot=snapshot,
                digest=_sha256_bytes(snapshot.payload),
            )
        )
    joint_payload = "".join(
        "{0}\0{1}\n".format(entry.relative_path, entry.digest)
        for entry in source_assets
    ).encode("utf-8")
    provenance = RepositoryProvenance(
        package_lock_snapshot=package_lock_snapshot,
        index_snapshot=index_snapshot,
        playwright_version=playwright_version,
        source_assets=tuple(source_assets),
        source_assets_joint_sha256=_sha256_bytes(joint_payload),
    )
    _ensure_repository_provenance_current(provenance)
    return provenance


def _repository_source_assets_metadata(provenance):
    return {
        "files": [
            {"path": entry.relative_path, "sha256": entry.digest}
            for entry in provenance.source_assets
        ],
        "joint_sha256": provenance.source_assets_joint_sha256,
    }


def _decode_capture_image(snapshot, label):
    try:
        with Image.open(io.BytesIO(snapshot.payload)) as image:
            image.load()
            return image.convert("RGBA")
    except (OSError, ValueError) as error:
        raise VisualComparisonError("{0} is not a readable image".format(label)) from error


def _validate_capture_metadata(
    metadata,
    image_path,
    label,
    require_approval=False,
    repository_provenance=None,
):
    top_level = {
        "schema",
        "version",
        "browser",
        "platform",
        "viewport",
        "locator",
        "capture",
        "input",
        "image",
        "source_assets",
    }
    if require_approval:
        top_level.add("approval")
    _require_exact_keys(metadata, top_level, "{0} metadata".format(label))
    if metadata.get("schema") != CAPTURE_SCHEMA:
        raise VisualComparisonError("{0} has an unsupported capture schema".format(label))
    _require_exact_integer(
        metadata.get("version"),
        CAPTURE_VERSION,
        "{0} capture version".format(label),
    )
    if repository_provenance is None:
        repository_provenance = _read_repository_provenance()

    browser = _nested(metadata, ("browser",), label)
    _require_exact_keys(
        browser,
        {"playwright_version", "chromium_version"},
        "{0} browser".format(label),
    )
    playwright_version = _require_nonempty_string(
        browser["playwright_version"], "{0} Playwright version".format(label)
    )
    _require_nonempty_string(
        browser["chromium_version"], "{0} Chromium version".format(label)
    )
    if playwright_version != repository_provenance.playwright_version:
        raise VisualComparisonError(
            "{0} Playwright version does not match package-lock.json".format(label)
        )

    platform = _nested(metadata, ("platform",), label)
    _require_exact_keys(platform, {"os", "arch"}, "{0} platform".format(label))
    _require_nonempty_string(platform["os"], "{0} platform.os".format(label))
    _require_nonempty_string(platform["arch"], "{0} platform.arch".format(label))
    if require_approval and platform["os"] != "linux":
        raise VisualComparisonError(
            "{0} approved baseline must be a linux capture".format(label)
        )

    viewport = _nested(metadata, ("viewport",), label)
    _require_exact_keys(viewport, VIEWPORT, "{0} viewport".format(label))
    for key, expected in VIEWPORT.items():
        _require_exact_integer(
            viewport[key],
            expected,
            "{0} viewport.{1}".format(label, key),
        )

    locator = _nested(metadata, ("locator",), label)
    _require_exact_keys(
        locator,
        {"selector", "bounding_box", "cells"},
        "{0} locator".format(label),
    )
    if locator["selector"] != LOCATOR_SELECTOR:
        raise VisualComparisonError("{0} locator is not the locked capture locator".format(label))
    _require_exact_integer(
        locator["cells"],
        EXPECTED_CELLS,
        "{0} locator.cells".format(label),
    )
    bounds = locator["bounding_box"]
    _require_exact_keys(bounds, {"x", "y", "width", "height"}, "{0} bounding box".format(label))
    for key, expected in (
        ("x", 0),
        ("y", 0),
        ("width", EXPECTED_WIDTH),
        ("height", EXPECTED_HEIGHT),
    ):
        _require_exact_integer(
            bounds[key],
            expected,
            "{0} bounding_box.{1}".format(label, key),
        )

    capture = _nested(metadata, ("capture",), label)
    _require_exact_keys(
        capture,
        {
            "timestamp_utc",
            "external_requests",
            "external_request_urls",
            "animation_count",
            "transition_count",
        },
        "{0} capture".format(label),
    )
    _require_nonempty_string(capture["timestamp_utc"], "{0} capture timestamp".format(label))
    if capture["external_request_urls"] != []:
        raise VisualComparisonError("{0} reports external request URLs".format(label))
    for key, description in (
        ("external_requests", "external requests"),
        ("animation_count", "animations"),
        ("transition_count", "transitions"),
    ):
        _require_exact_integer(
            capture[key],
            0,
            "{0} {1}".format(label, description),
        )

    input_metadata = _nested(metadata, ("input",), label)
    _require_exact_keys(input_metadata, {"path", "sha256"}, "{0} input".format(label))
    if input_metadata["path"] != INDEX_RELATIVE_PATH:
        raise VisualComparisonError("{0} input path is not the canonical index".format(label))
    if input_metadata["sha256"] != _sha256_bytes(
        repository_provenance.index_snapshot.payload
    ):
        raise VisualComparisonError("{0} input SHA-256 is not current".format(label))

    image_metadata = _nested(metadata, ("image",), label)
    _require_exact_keys(
        image_metadata,
        {"path", "sha256", "width", "height"},
        "{0} image".format(label),
    )
    _require_exact_integer(
        image_metadata["width"],
        EXPECTED_WIDTH,
        "{0} image.width".format(label),
    )
    _require_exact_integer(
        image_metadata["height"],
        EXPECTED_HEIGHT,
        "{0} image.height".format(label),
    )
    image_snapshot = _read_file_snapshot(image_path, "{0} image".format(label))
    if image_metadata["path"] != _metadata_image_path(image_path):
        raise VisualComparisonError("{0} image path does not match the capture image".format(label))
    expected_hash = _require_sha256(
        image_metadata["sha256"], "{0} image SHA-256".format(label)
    )
    actual_hash = _sha256_bytes(image_snapshot.payload)
    if expected_hash != actual_hash:
        raise VisualComparisonError(
            "{0} image SHA-256 does not match metadata".format(label)
        )
    capture_image = _decode_capture_image(image_snapshot, "{0} image".format(label))
    actual_dimensions = (capture_image.width, capture_image.height)
    if actual_dimensions != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        raise VisualComparisonError(
            "{0} image dimensions must be {1}x{2}".format(
                label,
                EXPECTED_WIDTH,
                EXPECTED_HEIGHT,
            )
        )
    if bounds["width"] != capture_image.width or bounds["height"] != capture_image.height:
        raise VisualComparisonError("{0} bounding box does not match image dimensions".format(label))

    source_assets = _nested(metadata, ("source_assets",), label)
    _require_exact_keys(
        source_assets,
        {"files", "joint_sha256"},
        "{0} source assets".format(label),
    )
    files = source_assets["files"]
    if not isinstance(files, list) or len(files) != len(SOURCE_ASSET_PATHS):
        raise VisualComparisonError("{0} must list exactly 10 source asset files".format(label))
    expected_paths = list(SOURCE_ASSET_PATHS)
    actual_paths = []
    for index, entry in enumerate(files):
        _require_exact_keys(
            entry,
            {"path", "sha256"},
            "{0} source asset file {1}".format(label, index),
        )
        actual_paths.append(entry["path"])
        _require_sha256(entry["sha256"], "{0} source asset SHA-256".format(label))
    if actual_paths != expected_paths:
        raise VisualComparisonError("{0} source asset files are not exact and sorted".format(label))
    joint_payload = "".join(
        "{0}\0{1}\n".format(entry["path"], entry["sha256"])
        for entry in files
    ).encode("utf-8")
    joint_digest = _require_sha256(
        source_assets["joint_sha256"], "{0} source asset digest".format(label)
    )
    if joint_digest != _sha256_bytes(joint_payload):
        raise VisualComparisonError("{0} source asset digest does not match file list".format(label))
    if source_assets != _repository_source_assets_metadata(repository_provenance):
        raise VisualComparisonError("{0} source assets do not match current repository".format(label))

    if require_approval:
        approval = metadata.get("approval")
        _require_exact_keys(
            approval,
            {
                "timestamp_utc",
                "reviewer",
                "note",
                "candidate_sha256",
                "baseline_sha256",
                "capture_metadata_sha256",
                "playwright_version",
                "chromium_version",
                "source_assets_joint_sha256",
            },
            "baseline approval",
        )
        for key in ("timestamp_utc", "reviewer", "note"):
            _require_nonempty_string(approval[key], "baseline approval {0}".format(key))
        for key in ("candidate_sha256", "baseline_sha256", "capture_metadata_sha256"):
            _require_sha256(approval[key], "baseline approval {0}".format(key))
        if approval["candidate_sha256"] != actual_hash:
            raise VisualComparisonError("baseline approval candidate hash does not match image")
        if approval["baseline_sha256"] != actual_hash:
            raise VisualComparisonError("baseline approval hash does not match baseline image")
        if approval["capture_metadata_sha256"] != _capture_metadata_digest(metadata):
            raise VisualComparisonError("baseline approval capture metadata hash does not match")
        for approval_key, metadata_value, description in (
            ("playwright_version", browser["playwright_version"], "Playwright"),
            ("chromium_version", browser["chromium_version"], "Chromium"),
            ("source_assets_joint_sha256", joint_digest, "source asset digest"),
        ):
            if approval[approval_key] != metadata_value:
                raise VisualComparisonError(
                    "baseline approval {0} binding does not match".format(description)
                )
    _ensure_repository_provenance_current(repository_provenance)
    return ValidatedCapture(
        image_snapshot,
        actual_hash,
        capture_image,
        repository_provenance,
    )


def _ensure_capture_compatibility(baseline_metadata, candidate_metadata):
    fields = (
        (("platform",), "platform"),
        (("source_assets", "joint_sha256"), "source asset digest"),
        (("browser", "playwright_version"), "Playwright version"),
        (("browser", "chromium_version"), "Chromium version"),
    )
    for keys, label in fields:
        baseline_value = _nested(baseline_metadata, keys, "baseline metadata")
        candidate_value = _nested(candidate_metadata, keys, "candidate metadata")
        if baseline_value != candidate_value:
            raise VisualComparisonError("{0} does not match approved baseline".format(label))


def _output_snapshot(path):
    target = _absolute(path)
    if not os.path.lexists(str(target)):
        return None
    return _read_file_snapshot(target, "approval output")


def _snapshots_equal(left, right):
    if left is None or right is None:
        return left is right
    return left.signature == right.signature and left.payload == right.payload


def _stage_approval_payload(target, payload, mode, suffix):
    descriptor = None
    temporary = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".{0}.".format(Path(target).name),
            suffix=suffix,
            dir=str(Path(target).parent),
        )
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(str(temporary), mode)
        info = os.lstat(str(temporary))
        return temporary, _file_signature(info)
    except BaseException:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _approval_output_matches_published(record):
    current = _output_snapshot(record["target"])
    return (
        current is not None
        and _replacement_signature(current.signature)
        == _replacement_signature(record["staged_signature"])
        and current.payload == record["payload"]
    )


def _assert_approval_output_is_published(record):
    if not _approval_output_matches_published(record):
        raise VisualComparisonError(
            "approval output changed after publish: {0}".format(record["target"])
        )


def _assert_staged_output_is_ready(record):
    current = _read_file_snapshot(record["staged"], "staged publication payload")
    if (
        current.signature != record["staged_signature"]
        or current.payload != record["payload"]
    ):
        raise VisualComparisonError(
            "staged output changed before publish: {0}".format(record["staged"])
        )


def _moved_snapshot_matches(snapshot, expected):
    if snapshot is None or expected is None:
        return snapshot is expected
    return (
        _replacement_signature(snapshot.signature)
        == _replacement_signature(expected.signature)
        and snapshot.payload == expected.payload
    )


def _normalize_publication_operations(operations):
    values = operations or {}
    if not isinstance(values, dict):
        raise TypeError("publication operations must be a mapping")
    return {
        "move": values.get("move", os.rename),
        "link": values.get("link", os.link),
        "unlink": values.get("unlink", os.unlink),
        "rmdir": values.get("rmdir", os.rmdir),
        "snapshot": values.get("snapshot", _output_snapshot),
    }


def _claim_output(target, operations):
    target = _absolute(target)
    directory = Path(
        tempfile.mkdtemp(
            prefix=".{0}.claim-".format(target.name),
            dir=str(target.parent),
        )
    )
    claim = {"directory": directory, "path": directory / "payload"}
    try:
        operations["move"](str(target), str(claim["path"]))
    except FileNotFoundError:
        operations["rmdir"](str(directory))
        return None
    except BaseException:
        try:
            operations["rmdir"](str(directory))
        except OSError:
            pass
        raise
    try:
        claim["snapshot"] = operations["snapshot"](claim["path"])
        if claim["snapshot"] is None:
            raise VisualComparisonError(
                "claimed output disappeared: {0}".format(target)
            )
    except BaseException as error:
        try:
            _restore_claim_exclusive(claim, target, operations)
        except BaseException as recovery_error:
            raise VisualComparisonError(
                _preserve_claim(
                    claim,
                    "claimed output inspection failed at {0}: {1}; exclusive recovery failed: {2}".format(
                        target,
                        error,
                        recovery_error,
                    ),
                )
            ) from error
        raise
    return claim


def _discard_claim(claim, operations):
    operations["unlink"](str(claim["path"]))
    operations["rmdir"](str(claim["directory"]))


def _create_exclusive_link(source, target, operations):
    try:
        operations["link"](str(source), str(target))
        return None
    except BaseException as error:
        if (
            isinstance(error, FileExistsError)
            or getattr(error, "errno", None) == errno.EEXIST
        ):
            raise
        try:
            linked = _paths_alias(source, target)
        except (OSError, VisualComparisonError):
            linked = False
        if linked:
            return error
        raise


def _restore_claim_exclusive(claim, target, operations):
    _create_exclusive_link(claim["path"], target, operations)
    _discard_claim(claim, operations)


def _preserve_claim(claim, reason):
    if claim is None:
        return reason
    return "{0}; recovery claim preserved at {1}".format(reason, claim["path"])


def _reject_unexpected_claim(claim, target, operations, reason):
    if claim is None:
        raise VisualComparisonError(reason)
    try:
        _restore_claim_exclusive(claim, target, operations)
    except BaseException as error:
        raise VisualComparisonError(
            _preserve_claim(
                claim,
                "{0}; exclusive recovery failed: {1}".format(reason, error),
            )
        ) from error
    raise VisualComparisonError(reason)


def _rollback_publication_record(record, operations):
    if record["installed"]:
        displaced = _claim_output(record["target"], operations)
        if displaced is None:
            raise VisualComparisonError(
                _preserve_claim(
                    record["original_claim"],
                    "rollback conflict at {0}: published output disappeared".format(
                        record["target"]
                    ),
                )
            )
        staged_expected = FileSnapshot(
            path=record["staged"],
            payload=record["payload"],
            mode=stat.S_IMODE(record["staged_signature"].mode),
            signature=record["staged_signature"],
        )
        if not _moved_snapshot_matches(displaced["snapshot"], staged_expected):
            try:
                _restore_claim_exclusive(displaced, record["target"], operations)
            except BaseException as error:
                raise VisualComparisonError(
                    _preserve_claim(
                        record["original_claim"],
                        _preserve_claim(
                            displaced,
                            "rollback conflict at {0}; external output recovery failed: {1}".format(
                                record["target"], error
                            ),
                        ),
                    )
                ) from error
            raise VisualComparisonError(
                _preserve_claim(
                    record["original_claim"],
                    "rollback conflict at {0}: current output is not owned by this publish".format(
                        record["target"]
                    ),
                )
            )
        _discard_claim(displaced, operations)
        record["installed"] = False

    original_claim = record["original_claim"]
    if original_claim is not None:
        try:
            _restore_claim_exclusive(original_claim, record["target"], operations)
            record["original_claim"] = None
        except BaseException as error:
            raise VisualComparisonError(
                _preserve_claim(
                    original_claim,
                    "rollback conflict at {0}; exclusive original restore failed: {1}".format(
                        record["target"], error
                    ),
                )
            ) from error


def _publish_records(records, verify_current, operations, failure_label):
    committed = False
    cleanup_completed = False
    try:
        for index, record in enumerate(records):
            verify_current()
            for peer in records[:index]:
                if peer["installed"]:
                    _assert_approval_output_is_published(peer)
            claim = _claim_output(record["target"], operations)
            moved = claim["snapshot"] if claim is not None else None
            if not _moved_snapshot_matches(moved, record["snapshot"]):
                _reject_unexpected_claim(
                    claim,
                    record["target"],
                    operations,
                    "{0} output changed before publish: {1}".format(
                        failure_label,
                        record["target"],
                    ),
                )
            record["original_claim"] = claim
            verify_current()
            for peer in records[:index]:
                if peer["installed"]:
                    _assert_approval_output_is_published(peer)
            _assert_staged_output_is_ready(record)
            install_error = _create_exclusive_link(
                record["staged"],
                record["target"],
                operations,
            )
            record["installed"] = True
            if install_error is not None:
                raise install_error
            _assert_approval_output_is_published(record)
        verify_current()
        for record in records:
            _assert_approval_output_is_published(record)
        committed = True
        for record in records:
            if record["original_claim"] is not None:
                claim = record["original_claim"]
                try:
                    _discard_claim(claim, operations)
                except BaseException as error:
                    raise VisualComparisonError(
                        "claim cleanup failed at {0}: {1}".format(
                            claim["directory"],
                            error,
                        )
                    ) from error
                record["original_claim"] = None
        cleanup_completed = True
        for record in records:
            _assert_approval_output_is_published(record)
    except BaseException as error:
        if committed:
            raise VisualComparisonError(
                "{0} publish committed but {1}; committed outputs retained: {2}".format(
                    failure_label,
                    (
                        "post-commit external change detected"
                        if cleanup_completed
                        else "cleanup failed"
                    ),
                    error,
                )
            ) from error
        rollback_errors = []
        for record in reversed(records):
            if not record["installed"] and record["original_claim"] is None:
                continue
            try:
                _rollback_publication_record(record, operations)
            except BaseException as rollback_error:
                rollback_errors.append(str(rollback_error))
        if rollback_errors:
            raise VisualComparisonError(
                "{0} publish failed and rollback was incomplete: {1}".format(
                    failure_label,
                    "; ".join(rollback_errors),
                )
            ) from error
        raise
    finally:
        for record in records:
            staged = record.get("staged")
            if staged is not None:
                try:
                    staged.unlink()
                except FileNotFoundError:
                    pass


def _publish_approval(
    baseline_path,
    baseline_payload,
    metadata_path,
    metadata_payload,
    verify_current=None,
    operations=None,
):
    if verify_current is None:
        verify_current = lambda: None
    publication_operations = _normalize_publication_operations(operations)
    records = []
    try:
        for target, payload in (
            (_absolute(baseline_path), bytes(baseline_payload)),
            (_absolute(metadata_path), bytes(metadata_payload)),
        ):
            snapshot = _output_snapshot(target)
            mode = snapshot.mode if snapshot is not None else 0o644
            staged, staged_signature = _stage_approval_payload(
                target,
                payload,
                mode,
                ".tmp",
            )
            records.append(
                {
                    "target": target,
                    "payload": payload,
                    "snapshot": snapshot,
                    "staged": staged,
                    "staged_signature": staged_signature,
                    "original_claim": None,
                    "installed": False,
                }
            )
    except BaseException:
        for record in records:
            try:
                record["staged"].unlink()
            except FileNotFoundError:
                pass
        raise
    _publish_records(
        records,
        verify_current,
        publication_operations,
        "approval",
    )


def _publish_staged_heatmap(
    target,
    staged,
    target_snapshot,
    verify_current,
    operations=None,
):
    target = _absolute(target)
    staged = _absolute(staged)
    mode = target_snapshot.mode if target_snapshot is not None else 0o644
    os.chmod(str(staged), mode)
    staged_snapshot = _read_file_snapshot(staged, "staged diff output")
    record = {
        "target": target,
        "payload": staged_snapshot.payload,
        "snapshot": target_snapshot,
        "staged": staged,
        "staged_signature": staged_snapshot.signature,
        "original_claim": None,
        "installed": False,
    }
    _publish_records(
        [record],
        verify_current,
        _normalize_publication_operations(operations),
        "diff",
    )


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
    candidate_path = _absolute(candidate)
    candidate_metadata_path = _absolute(candidate_metadata)
    _prepare_output_path(baseline)
    _prepare_output_path(baseline_metadata)
    repository_provenance = _read_repository_provenance()
    metadata, metadata_snapshot = _read_metadata_snapshot(
        candidate_metadata_path,
        "candidate metadata",
    )
    validated = _validate_capture_metadata(
        metadata,
        candidate_path,
        "candidate",
        repository_provenance=repository_provenance,
    )
    if metadata["platform"]["os"] != "linux":
        raise VisualComparisonError("only a linux capture may be accepted as baseline")
    digest = validated.digest
    approved = copy.deepcopy(metadata)
    approved["image"]["path"] = _metadata_image_path(baseline)
    capture_metadata_sha256 = _capture_metadata_digest(approved)
    approved["approval"] = {
        "timestamp_utc": datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
        "reviewer": reviewer_value,
        "note": note_value,
        "candidate_sha256": digest,
        "baseline_sha256": digest,
        "capture_metadata_sha256": capture_metadata_sha256,
        "playwright_version": approved["browser"]["playwright_version"],
        "chromium_version": approved["browser"]["chromium_version"],
        "source_assets_joint_sha256": approved["source_assets"]["joint_sha256"],
    }
    metadata_payload = (
        json.dumps(approved, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")

    def verify_current():
        _ensure_snapshot_current(metadata_snapshot, "candidate metadata")
        _ensure_repository_provenance_current(repository_provenance)

    _publish_approval(
        _absolute(baseline),
        validated.snapshot.payload,
        _absolute(baseline_metadata),
        metadata_payload,
        verify_current=verify_current,
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
    staged_diff_output = None
    diff_target = None
    diff_target_snapshot = None
    if diff_output is not None:
        _validate_output_path(diff_output)
        diff_target = _absolute(diff_output)
        _prepare_output_path(diff_target)
        diff_target_snapshot = _output_snapshot(diff_target)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".{0}.".format(diff_target.name),
            suffix=".tmp",
            dir=str(diff_target.parent),
        )
        os.close(descriptor)
        staged_diff_output = Path(temporary_name)
    try:
        baseline_path = _absolute(baseline)
        candidate_path = _absolute(candidate)
        repository_provenance = _read_repository_provenance()
        baseline_payload, baseline_metadata_snapshot = _read_metadata_snapshot(
            baseline_metadata,
            "baseline metadata",
        )
        candidate_payload, candidate_metadata_snapshot = _read_metadata_snapshot(
            candidate_metadata,
            "candidate metadata",
        )
        baseline_validated = _validate_capture_metadata(
            baseline_payload,
            baseline_path,
            "baseline",
            require_approval=True,
            repository_provenance=repository_provenance,
        )
        candidate_validated = _validate_capture_metadata(
            candidate_payload,
            candidate_path,
            "candidate",
            repository_provenance=repository_provenance,
        )
        _ensure_capture_compatibility(baseline_payload, candidate_payload)
        report = compare_images(
            baseline_validated.image,
            candidate_validated.image,
            channel_tolerance=channel_tolerance,
            max_diff_ratio=max_diff_ratio,
            diff_output=staged_diff_output,
        )

        def verify_comparison_current():
            for snapshot, label in (
                (baseline_metadata_snapshot, "baseline metadata"),
                (candidate_metadata_snapshot, "candidate metadata"),
                (baseline_validated.snapshot, "baseline image"),
                (candidate_validated.snapshot, "candidate image"),
            ):
                _ensure_snapshot_current(snapshot, label)
            _ensure_repository_provenance_current(repository_provenance)

        verify_comparison_current()
        if staged_diff_output is not None and not report.passed:
            if not _snapshots_equal(
                _output_snapshot(diff_target),
                diff_target_snapshot,
            ):
                raise VisualComparisonError(
                    "diff output changed before publish: {0}".format(diff_target)
                )
            _publish_staged_heatmap(
                diff_target,
                staged_diff_output,
                diff_target_snapshot,
                verify_comparison_current,
            )
            staged_diff_output = None
        return report
    finally:
        if staged_diff_output is not None:
            try:
                staged_diff_output.unlink()
            except FileNotFoundError:
                pass


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

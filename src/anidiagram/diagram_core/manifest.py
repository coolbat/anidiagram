"""Immutable Diagram Core icon manifest contracts."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Tuple

from .catalog import CATALOG_STATUSES, CATALOG_SYSTEM_ID
from ..resources import resource_path


_DEFAULT_ASSET_ROOT = resource_path("assets", "diagram-core")
_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_JSON_PATH_MEMBER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_APPROVAL_DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_REQUIRED_FIELDS = {
    "id",
    "system",
    "asset_revision",
    "viewBox",
    "category",
    "semantic_kind",
    "structural_prototype",
    "parts",
    "attachments",
    "states",
    "actions",
    "status",
}
_OPTIONAL_FIELDS = {"exceptions"}
_EXCEPTION_FIELDS = {"metric", "reason", "reviewer", "approved_on"}
_EXCEPTION_METRICS = frozenset(
    {"raw-size", "gzip-size", "paintable-elements", "non-scaling-stroke"}
)


@dataclass(frozen=True)
class ManifestValidationIssue:
    path: str
    message: str


@dataclass(frozen=True)
class _JSONObject:
    pairs: Tuple[Tuple[str, Any], ...]


class ManifestValidationError(ValueError):
    """Raised with every independently detectable manifest issue."""

    def __init__(
        self,
        issues: Tuple[ManifestValidationIssue, ...],
        source_path: Optional[Path] = None,
    ) -> None:
        self.issues = tuple(issues)
        self.source_path = None if source_path is None else Path(source_path)
        prefix = "" if self.source_path is None else str(self.source_path) + ":"
        super().__init__(
            "; ".join(
                "{0}{1}: {2}".format(prefix, issue.path, issue.message)
                for issue in self.issues
            )
        )


@dataclass(frozen=True)
class Attachment:
    x: float
    y: float


@dataclass(frozen=True)
class ApprovedException:
    metric: str
    reason: str
    reviewer: str
    approved_on: str


@dataclass(frozen=True)
class IconManifest:
    icon_id: str
    system: str
    asset_revision: int
    view_box: str
    category: str
    semantic_kind: str
    structural_prototype: str
    parts: Tuple[str, ...]
    attachments: Mapping[str, Attachment]
    states: Tuple[str, ...]
    actions: Tuple[str, ...]
    status: str
    exceptions: Tuple[ApprovedException, ...]

    @property
    def exception_metrics(self) -> frozenset:
        return frozenset(exception.metric for exception in self.exceptions)


def _issue(
    issues: list,
    path: str,
    message: str,
) -> None:
    issues.append(ManifestValidationIssue(path=path, message=message))


def _json_member_path(path: str, key: str) -> str:
    if _JSON_PATH_MEMBER_PATTERN.fullmatch(key) is not None:
        return path + "." + key
    return path + "[" + json.dumps(key, ensure_ascii=False) + "]"


def _materialize_json(value: Any, path: str, issues: list) -> Any:
    if isinstance(value, _JSONObject):
        result = {}
        seen = set()
        for key, child in value.pairs:
            child_path = _json_member_path(path, key)
            decoded_child = _materialize_json(child, child_path, issues)
            if key in seen:
                _issue(
                    issues,
                    child_path,
                    "duplicate JSON key {0}".format(json.dumps(key)),
                )
                continue
            seen.add(key)
            result[key] = decoded_child
        return result
    if isinstance(value, list):
        return [
            _materialize_json(child, "{0}[{1}]".format(path, index), issues)
            for index, child in enumerate(value)
        ]
    return value


def _identifier(value: Any, path: str, issues: list) -> Optional[str]:
    if not isinstance(value, str) or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        _issue(issues, path, "expected a kebab-case identifier")
        return None
    return value


def _identifier_tuple(
    value: Any,
    path: str,
    issues: list,
    require_nonempty: bool = False,
) -> Tuple[str, ...]:
    if not isinstance(value, list):
        _issue(issues, path, "expected an array")
        return ()
    if require_nonempty and not value:
        _issue(issues, path, "expected at least one value")
    result = []
    locations = {}
    for index, item in enumerate(value):
        item_path = "{0}[{1}]".format(path, index)
        identifier = _identifier(item, item_path, issues)
        if identifier is None:
            continue
        if identifier in locations:
            _issue(
                issues,
                item_path,
                "duplicates value at {0}".format(locations[identifier]),
            )
            continue
        locations[identifier] = item_path
        result.append(identifier)
    return tuple(result)


def _coordinate(value: Any, path: str, issues: list) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _issue(issues, path, "expected a finite number from 0 through 96")
        return None
    if not math.isfinite(value) or not 0 <= value <= 96:
        _issue(issues, path, "expected a finite number from 0 through 96")
        return None
    return value


def _attachments(value: Any, issues: list) -> Mapping[str, Attachment]:
    if not isinstance(value, dict):
        _issue(issues, "$.attachments", "expected an object")
        return MappingProxyType({})
    result: Dict[str, Attachment] = {}
    for name, raw_attachment in value.items():
        path = "$.attachments.{0}".format(name)
        if _identifier(name, path, issues) is None:
            continue
        if not isinstance(raw_attachment, dict):
            _issue(issues, path, "expected an object")
            continue
        missing = sorted({"x", "y"} - set(raw_attachment))
        extra = sorted(set(raw_attachment) - {"x", "y"})
        for field_name in missing:
            _issue(issues, path + "." + field_name, "required field is missing")
        for field_name in extra:
            _issue(issues, path + "." + field_name, "unexpected field")
        x = _coordinate(raw_attachment.get("x"), path + ".x", issues) if "x" in raw_attachment else None
        y = _coordinate(raw_attachment.get("y"), path + ".y", issues) if "y" in raw_attachment else None
        if x is not None and y is not None:
            result[name] = Attachment(x=x, y=y)
    return MappingProxyType(result)


def _exceptions(value: Any, issues: list) -> Tuple[ApprovedException, ...]:
    if not isinstance(value, list):
        _issue(issues, "$.exceptions", "expected an array of approved exceptions")
        return ()
    result = []
    metric_locations = {}
    for index, raw_exception in enumerate(value):
        path = "$.exceptions[{0}]".format(index)
        if not isinstance(raw_exception, dict):
            _issue(issues, path, "expected an object")
            continue
        missing = sorted(_EXCEPTION_FIELDS - set(raw_exception))
        extra = sorted(set(raw_exception) - _EXCEPTION_FIELDS)
        for field_name in missing:
            _issue(issues, path + "." + field_name, "required field is missing")
        for field_name in extra:
            _issue(issues, path + "." + field_name, "unexpected field")

        metric = raw_exception.get("metric")
        metric_valid = isinstance(metric, str) and metric in _EXCEPTION_METRICS
        if "metric" in raw_exception and not metric_valid:
            _issue(issues, path + ".metric", "expected a supported exception metric")
        elif metric_valid and metric in metric_locations:
            _issue(
                issues,
                path + ".metric",
                "duplicates exception at {0}".format(metric_locations[metric]),
            )
            metric_valid = False
        elif metric_valid:
            metric_locations[metric] = path + ".metric"

        text_values = {}
        for field_name in ("reason", "reviewer"):
            value = raw_exception.get(field_name)
            if field_name in raw_exception and (
                not isinstance(value, str) or not value.strip()
            ):
                _issue(issues, path + "." + field_name, "expected a nonempty string")
            elif isinstance(value, str) and value.strip():
                text_values[field_name] = value
        approved_on = raw_exception.get("approved_on")
        date_valid = (
            isinstance(approved_on, str)
            and _APPROVAL_DATE_PATTERN.fullmatch(approved_on) is not None
        )
        if "approved_on" in raw_exception and not date_valid:
            _issue(issues, path + ".approved_on", "expected an ISO date YYYY-MM-DD")

        if (
            not missing
            and not extra
            and metric_valid
            and len(text_values) == 2
            and date_valid
        ):
            result.append(
                ApprovedException(
                    metric=metric,
                    reason=text_values["reason"],
                    reviewer=text_values["reviewer"],
                    approved_on=approved_on,
                )
            )
    return tuple(result)


def validate_manifest_dict(raw: Any) -> IconManifest:
    """Validate a decoded manifest without normalizing invalid input."""

    issues = []
    if not isinstance(raw, dict):
        raise ManifestValidationError(
            (ManifestValidationIssue("$", "expected an object"),)
        )

    for field_name in sorted(_REQUIRED_FIELDS - set(raw)):
        _issue(issues, "$." + field_name, "required field is missing")
    for field_name in sorted(set(raw) - _REQUIRED_FIELDS - _OPTIONAL_FIELDS):
        _issue(issues, "$." + field_name, "unexpected field")

    icon_id = _identifier(raw.get("id"), "$.id", issues) if "id" in raw else None
    if "system" in raw and raw["system"] != CATALOG_SYSTEM_ID:
        _issue(issues, "$.system", "expected {0}".format(CATALOG_SYSTEM_ID))
    revision = raw.get("asset_revision")
    if "asset_revision" in raw and (
        isinstance(revision, bool) or not isinstance(revision, int) or revision < 1
    ):
        _issue(issues, "$.asset_revision", "expected integer 1 or later")
    if "viewBox" in raw and raw["viewBox"] != "0 0 96 96":
        _issue(issues, "$.viewBox", "expected 0 0 96 96")

    category = _identifier(raw.get("category"), "$.category", issues) if "category" in raw else None
    semantic_kind = _identifier(raw.get("semantic_kind"), "$.semantic_kind", issues) if "semantic_kind" in raw else None
    prototype = _identifier(raw.get("structural_prototype"), "$.structural_prototype", issues) if "structural_prototype" in raw else None
    parts = _identifier_tuple(raw.get("parts"), "$.parts", issues, require_nonempty=True) if "parts" in raw else ()
    attachments = _attachments(raw.get("attachments"), issues) if "attachments" in raw else MappingProxyType({})
    states = _identifier_tuple(raw.get("states"), "$.states", issues) if "states" in raw else ()
    actions = _identifier_tuple(raw.get("actions"), "$.actions", issues) if "actions" in raw else ()
    status = raw.get("status")
    if "status" in raw and (
        not isinstance(status, str)
        or status not in CATALOG_STATUSES
        or status == "planned"
    ):
        _issue(issues, "$.status", "expected an implemented catalog lifecycle status")
    exceptions = _exceptions(raw["exceptions"], issues) if "exceptions" in raw else ()

    if issues:
        raise ManifestValidationError(tuple(issues))
    return IconManifest(
        icon_id=icon_id,
        system=raw["system"],
        asset_revision=revision,
        view_box=raw["viewBox"],
        category=category,
        semantic_kind=semantic_kind,
        structural_prototype=prototype,
        parts=parts,
        attachments=attachments,
        states=states,
        actions=actions,
        status=status,
        exceptions=exceptions,
    )


def load_manifest(icon_id: str, asset_root: Optional[Path] = None) -> IconManifest:
    """Load one manifest from a Diagram Core asset root."""

    if not isinstance(icon_id, str) or _IDENTIFIER_PATTERN.fullmatch(icon_id) is None:
        raise ManifestValidationError(
            (ManifestValidationIssue("$icon_id", "expected a kebab-case identifier"),)
        )
    root = _DEFAULT_ASSET_ROOT if asset_root is None else Path(asset_root)
    path = root / "manifests" / (icon_id + ".json")
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ManifestValidationError(
            (ManifestValidationIssue("$", "cannot read manifest: {0}".format(error)),),
            path,
        ) from error
    try:
        parsed = json.loads(
            source,
            object_pairs_hook=lambda pairs: _JSONObject(tuple(pairs)),
        )
    except json.JSONDecodeError as error:
        raise ManifestValidationError(
            (
                ManifestValidationIssue(
                    "$",
                    "invalid JSON at line {0}, column {1}".format(
                        error.lineno,
                        error.colno,
                    ),
                ),
            ),
            path,
        ) from error
    duplicate_issues = []
    raw = _materialize_json(parsed, "$", duplicate_issues)
    if duplicate_issues:
        raise ManifestValidationError(tuple(duplicate_issues), path)
    try:
        return validate_manifest_dict(raw)
    except ManifestValidationError as error:
        raise ManifestValidationError(error.issues, path) from error


__all__ = [
    "ApprovedException",
    "Attachment",
    "IconManifest",
    "ManifestValidationError",
    "ManifestValidationIssue",
    "load_manifest",
    "validate_manifest_dict",
]

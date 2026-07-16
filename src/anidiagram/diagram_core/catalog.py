"""Immutable Diagram Core catalog and lifecycle helpers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, FrozenSet, Optional, Tuple


CATALOG_SYSTEM_ID = "diagram-core-v1"
CATALOG_PUBLIC_NAME = "AniDiagram Diagram Core Icon System v1.0"
CATALOG_STATUSES = frozenset(
    {"planned", "visual-review", "approved", "deprecated"}
)
LEGACY_VALID_ICON_IDS = frozenset(
    {
        "agent",
        "api",
        "cloud",
        "database",
        "file",
        "folder",
        "memory",
        "operator",
        "output",
        "search",
        "shield",
        "token",
        "tool",
    }
)

_DEFAULT_ASSET_ROOT = Path(__file__).resolve().parents[3] / "assets" / "diagram-core"
_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_TOP_LEVEL_FIELDS = {"system", "public_name", "catalog_revision", "icons"}
_ICON_FIELDS = {
    "id",
    "category",
    "semantic_kind",
    "structural_prototype",
    "aliases",
    "parts",
    "supported_states",
    "supported_actions",
    "status",
    "asset_revision",
}
_BENCHMARK_STATES = (
    "idle",
    "active",
    "processing",
    "success",
    "warning",
    "error",
)
_BENCHMARKS = {
    "agent": (
        "actor-character",
        (
            "shell",
            "face-screen",
            "eye-left",
            "eye-right",
            "mouth",
            "antenna",
            "core",
            "indicator",
        ),
        ("enter", "receive", "process", "send"),
    ),
    "database": (
        "stacked-storage",
        (
            "shell",
            "top-ring",
            "layer-top",
            "layer-middle",
            "layer-bottom",
            "core",
            "indicator",
        ),
        ("receive", "write", "index", "search", "send"),
    ),
    "api": (
        "interface-module",
        (
            "shell",
            "header",
            "input-interface",
            "output-interface",
            "processor",
            "indicator-group",
        ),
        ("receive", "process", "send", "stream"),
    ),
    "server": (
        "compute-device",
        (
            "shell",
            "tray-top",
            "tray-bottom",
            "indicator-top",
            "indicator-bottom",
            "vent-top",
            "vent-bottom",
            "base",
        ),
        ("enter", "receive", "process", "send"),
    ),
}


class CatalogValidationError(ValueError):
    """Raised when a catalog value violates the frozen v1 contract."""


@dataclass(frozen=True)
class CatalogEntry:
    icon_id: str
    category: str
    semantic_kind: str
    structural_prototype: str
    aliases: Tuple[str, ...]
    parts: Tuple[str, ...]
    supported_states: Tuple[str, ...]
    supported_actions: Tuple[str, ...]
    status: str
    asset_revision: int


@dataclass(frozen=True)
class Catalog:
    system: str
    public_name: str
    catalog_revision: int
    entries: Tuple[CatalogEntry, ...]


def _fail(path: str, message: str) -> None:
    raise CatalogValidationError(f"{path}: {message}")


def _required_fields(value: Dict[str, Any], required: set, path: str) -> None:
    missing = sorted(required - set(value))
    if missing:
        _fail(f"{path}.{missing[0]}", "required field is missing")
    extra = sorted(set(value) - required)
    if extra:
        _fail(f"{path}.{extra[0]}", "unexpected field")


def _identifier(value: Any, path: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        _fail(path, "expected a kebab-case identifier")
    return value


def _identifier_tuple(value: Any, path: str) -> Tuple[str, ...]:
    if not isinstance(value, list):
        _fail(path, "expected an array")
    identifiers = tuple(
        _identifier(item, f"{path}[{index}]")
        for index, item in enumerate(value)
    )
    if len(identifiers) != len(set(identifiers)):
        _fail(path, "values must be unique")
    return identifiers


def _entry(raw: Any, index: int) -> CatalogEntry:
    path = f"$.icons[{index}]"
    if not isinstance(raw, dict):
        _fail(path, "expected an object")
    _required_fields(raw, _ICON_FIELDS, path)

    status = raw["status"]
    if not isinstance(status, str) or status not in CATALOG_STATUSES:
        _fail(f"{path}.status", "expected a catalog lifecycle status")
    asset_revision = raw["asset_revision"]
    if isinstance(asset_revision, bool) or not isinstance(asset_revision, int):
        _fail(f"{path}.asset_revision", "expected an integer")
    if asset_revision < 0:
        _fail(f"{path}.asset_revision", "expected a nonnegative integer")

    entry = CatalogEntry(
        icon_id=_identifier(raw["id"], f"{path}.id"),
        category=_identifier(raw["category"], f"{path}.category"),
        semantic_kind=_identifier(raw["semantic_kind"], f"{path}.semantic_kind"),
        structural_prototype=_identifier(
            raw["structural_prototype"],
            f"{path}.structural_prototype",
        ),
        aliases=_identifier_tuple(raw["aliases"], f"{path}.aliases"),
        parts=_identifier_tuple(raw["parts"], f"{path}.parts"),
        supported_states=_identifier_tuple(
            raw["supported_states"],
            f"{path}.supported_states",
        ),
        supported_actions=_identifier_tuple(
            raw["supported_actions"],
            f"{path}.supported_actions",
        ),
        status=status,
        asset_revision=asset_revision,
    )
    if entry.semantic_kind != entry.icon_id:
        _fail(f"{path}.semantic_kind", "must equal the canonical icon id")
    if entry.status == "planned":
        if entry.structural_prototype != "unassigned":
            _fail(f"{path}.structural_prototype", "planned icons must be unassigned")
        for field_name, values in (
            ("parts", entry.parts),
            ("supported_states", entry.supported_states),
            ("supported_actions", entry.supported_actions),
        ):
            if values:
                _fail(f"{path}.{field_name}", "planned icons cannot expose capabilities")
        if entry.asset_revision != 0:
            _fail(f"{path}.asset_revision", "planned icons must use asset revision 0")
    else:
        if entry.structural_prototype == "unassigned":
            _fail(f"{path}.structural_prototype", "implemented icons require a prototype")
        if entry.asset_revision < 1:
            _fail(f"{path}.asset_revision", "implemented icons require asset revision 1 or later")
    return entry


def _validate_benchmark(entry: CatalogEntry, index: int) -> None:
    expected = _BENCHMARKS.get(entry.icon_id)
    if expected is None:
        return
    prototype, parts, actions = expected
    path = f"$.icons[{index}]"
    for field_name, actual, wanted in (
        ("structural_prototype", entry.structural_prototype, prototype),
        ("parts", entry.parts, parts),
        ("supported_states", entry.supported_states, _BENCHMARK_STATES),
        ("supported_actions", entry.supported_actions, actions),
    ):
        if actual != wanted:
            _fail(f"{path}.{field_name}", "does not match the frozen benchmark contract")


def _parse_catalog(raw: Any) -> Catalog:
    if not isinstance(raw, dict):
        _fail("$", "expected an object")
    _required_fields(raw, _TOP_LEVEL_FIELDS, "$")
    if raw["system"] != CATALOG_SYSTEM_ID:
        _fail("$.system", f"expected {CATALOG_SYSTEM_ID}")
    if raw["public_name"] != CATALOG_PUBLIC_NAME:
        _fail("$.public_name", f"expected {CATALOG_PUBLIC_NAME}")
    revision = raw["catalog_revision"]
    if isinstance(revision, bool) or revision != 1:
        _fail("$.catalog_revision", "expected integer 1")
    icons = raw["icons"]
    if not isinstance(icons, list):
        _fail("$.icons", "expected an array")
    if len(icons) != 56:
        _fail("$.icons", "expected exactly 56 entries")

    entries = tuple(_entry(item, index) for index, item in enumerate(icons))
    id_locations: Dict[str, int] = {}
    for index, entry in enumerate(entries):
        if entry.icon_id in id_locations:
            _fail(f"$.icons[{index}].id", "duplicates another canonical icon id")
        id_locations[entry.icon_id] = index
        _validate_benchmark(entry, index)

    alias_locations: Dict[str, str] = {}
    icon_ids = frozenset(id_locations)
    for index, entry in enumerate(entries):
        for alias_index, alias in enumerate(entry.aliases):
            path = f"$.icons[{index}].aliases[{alias_index}]"
            if alias in icon_ids:
                _fail(path, "collides with a canonical icon id")
            if alias in alias_locations:
                _fail(path, f"collides with alias at {alias_locations[alias]}")
            alias_locations[alias] = path

    missing_legacy = LEGACY_VALID_ICON_IDS - icon_ids
    if missing_legacy:
        _fail("$.icons", "missing legacy ids: " + ", ".join(sorted(missing_legacy)))
    return Catalog(
        system=raw["system"],
        public_name=raw["public_name"],
        catalog_revision=revision,
        entries=entries,
    )


def load_catalog(asset_root: Optional[Path] = None) -> Catalog:
    """Load and validate ``catalog.json`` from a Diagram Core asset root."""

    root = _DEFAULT_ASSET_ROOT if asset_root is None else Path(asset_root)
    path = root / "catalog.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise CatalogValidationError(
            f"{path}: invalid JSON at line {error.lineno}, column {error.colno}"
        ) from error
    return _parse_catalog(raw)


_DEFAULT_CATALOG = load_catalog()
CATALOG_IDS: FrozenSet[str] = frozenset(
    entry.icon_id for entry in _DEFAULT_CATALOG.entries
)


def _catalog_or_default(catalog: Optional[Catalog]) -> Catalog:
    return _DEFAULT_CATALOG if catalog is None else catalog


def catalog_entry(icon_id: str, catalog: Optional[Catalog] = None) -> Optional[CatalogEntry]:
    """Return the canonical entry for ``icon_id``, if it is cataloged."""

    return next(
        (
            entry
            for entry in _catalog_or_default(catalog).entries
            if entry.icon_id == icon_id
        ),
        None,
    )


def legacy_valid_icon_ids(catalog: Optional[Catalog] = None) -> FrozenSet[str]:
    """Return the frozen DiagramScript compatibility set."""

    current_ids = frozenset(
        entry.icon_id for entry in _catalog_or_default(catalog).entries
    )
    missing = LEGACY_VALID_ICON_IDS - current_ids
    if missing:
        raise CatalogValidationError(
            "catalog is missing legacy ids: " + ", ".join(sorted(missing))
        )
    return LEGACY_VALID_ICON_IDS


def approved_icon_ids(catalog: Optional[Catalog] = None) -> FrozenSet[str]:
    """Return canonical ids whose Diagram Core assets are approved."""

    return frozenset(
        entry.icon_id
        for entry in _catalog_or_default(catalog).entries
        if entry.status == "approved"
    )


def diagram_script_valid_icon_ids(
    catalog: Optional[Catalog] = None,
) -> FrozenSet[str]:
    """Return legacy-compatible ids plus approved Diagram Core ids."""

    current = _catalog_or_default(catalog)
    return legacy_valid_icon_ids(current) | approved_icon_ids(current)


__all__ = [
    "CATALOG_IDS",
    "CATALOG_PUBLIC_NAME",
    "CATALOG_STATUSES",
    "CATALOG_SYSTEM_ID",
    "LEGACY_VALID_ICON_IDS",
    "Catalog",
    "CatalogEntry",
    "CatalogValidationError",
    "approved_icon_ids",
    "catalog_entry",
    "diagram_script_valid_icon_ids",
    "legacy_valid_icon_ids",
    "load_catalog",
]

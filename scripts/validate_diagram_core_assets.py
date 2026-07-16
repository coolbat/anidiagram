#!/usr/bin/env python3
"""Validate the Diagram Core asset bundle and report deterministic counts."""

import argparse
import json
import sys
from pathlib import Path

from anidiagram.diagram_core.asset_loader import AssetValidationError, load_asset
from anidiagram.diagram_core.catalog import legacy_valid_icon_ids, load_catalog
from anidiagram.diagram_core.tokens import contrast_ratio, token_css
from render_diagram_core_contact_sheet import _context_tokens


_STATE_TOKENS = (
    "--icon-status-idle",
    "--icon-status-active",
    "--icon-status-active",
    "--icon-status-success",
    "--icon-status-warning",
    "--icon-status-error",
)
_BENCHMARK_IDS = ("agent", "database", "api", "server")
_DEFAULT_ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets" / "diagram-core"


def _inventory(root, directory, suffix):
    expected = frozenset(icon_id + suffix for icon_id in _BENCHMARK_IDS)
    path = root / directory
    try:
        entries = tuple(path.iterdir())
    except OSError as error:
        return 0, ["{0}: cannot inspect asset directory: {1}".format(path, error)]
    names = frozenset(entry.name for entry in entries)
    details = []
    missing = sorted(expected - names)
    extra = sorted(names - expected)
    if missing:
        details.append(
            "{0}: missing files: {1}".format(path, ", ".join(missing))
        )
    if extra:
        details.append(
            "{0}: unexpected files: {1}".format(path, ", ".join(extra))
        )
    for entry in sorted(entries, key=lambda candidate: candidate.name):
        if entry.is_symlink():
            details.append("{0}: symbolic link is forbidden".format(entry))
        elif not entry.is_file():
            details.append("{0}: expected a regular file".format(entry))
    return sum(name.endswith(suffix) for name in names), details


def _contrast_checks(asset_root):
    source = (
        token_css()
        if asset_root is None
        else (asset_root / "tokens.css").read_text(encoding="utf-8")
    )
    _, contexts = _context_tokens(source)
    checks = 0
    for tokens in contexts.values():
        if contrast_ratio(tokens["--icon-stroke"], tokens["--icon-surface-main"]) < 3:
            raise ValueError("tokens.css structural contrast must be at least 3:1")
        checks += 1
        contrast_surface = tokens["--icon-surface-contrast"]
        for token in _STATE_TOKENS:
            if contrast_ratio(tokens[token], contrast_surface) < 3:
                raise ValueError("tokens.css state contrast must be at least 3:1")
            checks += 1
    return checks


def _parser():
    parser = argparse.ArgumentParser(
        description="Validate Diagram Core catalog, manifests, tokens, and SVG assets."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--review", action="store_true")
    mode.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--asset-root", type=Path)
    return parser


def _empty_report(svg_count, manifest_count):
    return {
        "catalog": 0,
        "legacy_valid": 0,
        "approved": 0,
        "visual_review": 0,
        "planned": 0,
        "svg": svg_count,
        "manifests": manifest_count,
        "paintable_elements_by_icon": {},
        "raw_bytes_by_icon": {},
        "gzip_bytes_by_icon": {},
        "contrast_checks": 0,
        "errors": 0,
        "warnings": 0,
    }


def _build_report(arguments):
    asset_root = (
        _DEFAULT_ASSET_ROOT
        if arguments.asset_root is None
        else arguments.asset_root
    )
    svg_count, svg_errors = _inventory(asset_root, "icons", ".svg")
    manifest_count, manifest_errors = _inventory(
        asset_root, "manifests", ".json"
    )
    error_details = svg_errors + manifest_errors
    report = _empty_report(svg_count, manifest_count)
    try:
        catalog = load_catalog(asset_root)
    except (OSError, UnicodeError, ValueError) as error:
        error_details.append(str(error))
        report["errors"] = len(error_details)
        report["error_details"] = error_details
        return report

    report.update(
        {
            "catalog": len(catalog.entries),
            "legacy_valid": len(legacy_valid_icon_ids(catalog)),
            "approved": sum(
                entry.status == "approved" for entry in catalog.entries
            ),
            "visual_review": sum(
                entry.status == "visual-review" for entry in catalog.entries
            ),
            "planned": sum(entry.status == "planned" for entry in catalog.entries),
        }
    )
    allowed_status = "approved" if arguments.strict else "visual-review"
    statuses = {entry.icon_id: entry.status for entry in catalog.entries}
    lifecycle_drift = tuple(
        icon_id
        for icon_id in _BENCHMARK_IDS
        if statuses.get(icon_id) != allowed_status
    )
    if lifecycle_drift:
        error_details.append(
            "{0} mode requires all benchmark assets to use status {1}; "
            "mismatched: {2}".format(
                "strict" if arguments.strict else "review",
                allowed_status,
                ", ".join(lifecycle_drift),
            )
        )
    unexpected_implemented = tuple(
        entry.icon_id
        for entry in catalog.entries
        if entry.icon_id not in _BENCHMARK_IDS and entry.status != "planned"
    )
    if unexpected_implemented:
        error_details.append(
            "unexpected implemented catalog entries: "
            + ", ".join(unexpected_implemented)
        )
    assets = {}
    for icon_id in _BENCHMARK_IDS:
        try:
            assets[icon_id] = load_asset(
                icon_id,
                {allowed_status},
                asset_root,
            )
        except AssetValidationError as error:
            error_details.append(str(error))
    report.update(
        {
            "paintable_elements_by_icon": {
                icon_id: asset.metrics.paintable_elements
                for icon_id, asset in sorted(assets.items())
            },
            "raw_bytes_by_icon": {
                icon_id: asset.metrics.raw_size_bytes
                for icon_id, asset in sorted(assets.items())
            },
            "gzip_bytes_by_icon": {
                icon_id: asset.metrics.gzip_size_bytes
                for icon_id, asset in sorted(assets.items())
            },
        }
    )
    try:
        report["contrast_checks"] = _contrast_checks(arguments.asset_root)
    except (KeyError, OSError, UnicodeError, ValueError) as error:
        error_details.append(str(error))
    report["errors"] = len(error_details)
    if error_details:
        report["error_details"] = error_details
    return report


def _emit(report, arguments):
    if arguments.as_json:
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    else:
        order = (
            "catalog",
            "legacy_valid",
            "approved",
            "visual_review",
            "svg",
            "manifests",
            "errors",
            "warnings",
        )
        print(" ".join("{0}={1}".format(key, report[key]) for key in order))
        for detail in report.get("error_details", ()):
            print(detail, file=sys.stderr)
    return 1 if report["errors"] else 0


def main():
    arguments = _parser().parse_args()
    return _emit(_build_report(arguments), arguments)


if __name__ == "__main__":
    raise SystemExit(main())

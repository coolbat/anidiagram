#!/usr/bin/env python3
"""Check repeated Diagram Core instances for scoped IDs and public parts."""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

from anidiagram.diagram_core.adapter import render_preview_icon
from anidiagram.diagram_core.asset_loader import load_asset
from anidiagram.diagram_core.catalog import load_catalog
from anidiagram.diagram_core.instance_ids import part_dom_id


_URL_REFERENCE = re.compile(
    r"url\s*\(\s*(?:['\"])?#([^\s)'\"]+)(?:['\"])?\s*\)",
    re.IGNORECASE,
)
_MAX_INSTANCES = 64


def _instance_count(value):
    try:
        count = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected an integer") from error
    if not 1 <= count <= _MAX_INSTANCES:
        raise argparse.ArgumentTypeError(
            "expected an integer from 1 through {0}".format(_MAX_INSTANCES)
        )
    return count


def _parser():
    parser = argparse.ArgumentParser(
        description="Render repeated Diagram Core icons and inspect their output."
    )
    parser.add_argument("--icons", required=True)
    parser.add_argument("--instances", required=True, type=_instance_count)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--asset-root", type=Path)
    return parser


def _local_name(name):
    return name.rsplit("}", 1)[-1]


def _references(root):
    references = []
    for element in root.iter():
        for raw_name, value in element.attrib.items():
            name = _local_name(raw_name).lower()
            if name == "href" and value.startswith("#"):
                references.append(value[1:])
            elif name in {"aria-labelledby", "aria-describedby"}:
                references.extend(value.split())
            references.extend(_URL_REFERENCE.findall(value))
        if element.text:
            references.extend(_URL_REFERENCE.findall(element.text))
        if element.tail:
            references.extend(_URL_REFERENCE.findall(element.tail))
    return references


def _icons(parser, value, catalog):
    icons = tuple(icon_id.strip() for icon_id in value.split(","))
    if not icons or any(not icon_id for icon_id in icons):
        parser.error("--icons requires a comma-separated list without empty values")
    if len(icons) != len(set(icons)):
        parser.error("--icons values must be unique")
    catalog_ids = frozenset(entry.icon_id for entry in catalog.entries)
    unknown = sorted(set(icons) - catalog_ids)
    if unknown:
        parser.error("unknown --icons values: " + ", ".join(unknown))
    return icons


def _inspect_instance(root, icon_id, instance_id, expected_parts):
    identifiers = tuple(
        element.attrib["id"]
        for element in root.iter()
        if "id" in element.attrib
    )
    identifier_set = frozenset(identifiers)
    actual_part_elements = tuple(
        element for element in root.iter() if "data-part" in element.attrib
    )
    actual_parts = tuple(
        element.attrib["data-part"] for element in actual_part_elements
    )
    expected_counter = Counter(expected_parts)
    actual_counter = Counter(actual_parts)
    missing_parts = sum((expected_counter - actual_counter).values())
    missing_parts += sum((actual_counter - expected_counter).values())
    if actual_parts != tuple(expected_parts) and not missing_parts:
        missing_parts += 1
    if root.attrib.get("id") != part_dom_id(instance_id, icon_id, "root"):
        missing_parts += 1
    for element in actual_part_elements:
        part_name = element.attrib["data-part"]
        if element.attrib.get("id") != part_dom_id(instance_id, icon_id, part_name):
            missing_parts += 1
    return {
        "identifiers": identifiers,
        "unresolved_refs": sum(
            reference not in identifier_set for reference in _references(root)
        ),
        "missing_parts": missing_parts,
    }


def _check(icons, arguments):
    roots = []
    identifiers = []
    unresolved_refs = 0
    missing_parts = 0
    for icon_id in icons:
        asset = load_asset(
            icon_id,
            {"visual-review", "approved"},
            arguments.asset_root,
        )
        expected_parts = asset.manifest.parts
        for index in range(arguments.instances):
            instance_id = "check-{0}-{1}".format(icon_id, index + 1)
            markup = render_preview_icon(
                icon_id,
                instance_id,
                asset_root=arguments.asset_root,
            )
            root = ElementTree.fromstring(markup)
            roots.append(root)
            inspection = _inspect_instance(
                root,
                icon_id,
                instance_id,
                expected_parts,
            )
            identifiers.extend(inspection["identifiers"])
            unresolved_refs += inspection["unresolved_refs"]
            missing_parts += inspection["missing_parts"]

    counts = Counter(identifiers)
    report = {
        "icons": len(icons),
        "instances": len(roots),
        "duplicate_ids": sum(count - 1 for count in counts.values() if count > 1),
        "unresolved_refs": unresolved_refs,
        "missing_parts": missing_parts,
    }
    return report


def _empty_report(icon_count):
    return {
        "icons": icon_count,
        "instances": 0,
        "duplicate_ids": 0,
        "unresolved_refs": 0,
        "missing_parts": 0,
    }


def _emit(report, arguments):
    if arguments.as_json:
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    else:
        order = (
            "icons",
            "instances",
            "duplicate_ids",
            "unresolved_refs",
            "missing_parts",
        )
        print(" ".join("{0}={1}".format(key, report[key]) for key in order))
        for detail in report.get("error_details", ()):
            print(detail, file=sys.stderr)
    return 1 if report.get("error_details") or any(
        report[key] for key in ("duplicate_ids", "unresolved_refs", "missing_parts")
    ) else 0


def main():
    parser = _parser()
    arguments = parser.parse_args()
    icons = ()
    try:
        catalog = load_catalog(arguments.asset_root)
        icons = _icons(parser, arguments.icons, catalog)
        report = _check(icons, arguments)
    except (ElementTree.ParseError, OSError, UnicodeError, ValueError) as error:
        report = _empty_report(len(icons))
        report["error_details"] = [str(error)]
    return _emit(report, arguments)


if __name__ == "__main__":
    raise SystemExit(main())

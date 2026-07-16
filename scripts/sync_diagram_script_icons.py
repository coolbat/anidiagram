#!/usr/bin/env python3
"""Keep the DiagramScript v0.3 JSON Schema icon enum in sync."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import List, Optional

from anidiagram.schema import KNOWN_ICONS


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "diagram-script-v0.3.schema.json"


def _icon_enum(path: Path) -> List[str]:
    schema = json.loads(path.read_text(encoding="utf-8"))
    return schema["$defs"]["icon"]["enum"]


def _write_icon_enum(path: Path, icon_ids: List[str]) -> None:
    source = path.read_bytes().decode("utf-8")
    replacement = json.dumps(icon_ids)
    pattern = re.compile(
        r'^(?P<indent>[ \t]*)"icon"\s*:\s*\{\s*"enum"\s*:\s*\[[^\]\r\n]*\]\s*\},',
        re.MULTILINE,
    )
    updated, count = pattern.subn(
        lambda match: f'{match.group("indent")}"icon": {{"enum": {replacement}}},',
        source,
    )
    if count != 1:
        raise ValueError(f"expected one DiagramScript icon enum, found {count}")
    path.write_bytes(updated.encode("utf-8"))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sync DiagramScript v0.3 icon ids with schema.KNOWN_ICONS."
    )
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--check", action="store_true", help="fail if the enum differs")
    actions.add_argument("--write", action="store_true", help="update the enum if it differs")
    args = parser.parse_args(argv)

    committed = _icon_enum(SCHEMA_PATH)
    clean = len(committed) == len(KNOWN_ICONS) and set(committed) == KNOWN_ICONS
    if clean:
        print(f"icons={len(KNOWN_ICONS)} status=clean")
        return 0
    if args.check:
        print(f"icons={len(KNOWN_ICONS)} status=drift")
        return 1
    _write_icon_enum(SCHEMA_PATH, sorted(KNOWN_ICONS))
    print(f"icons={len(KNOWN_ICONS)} status=written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

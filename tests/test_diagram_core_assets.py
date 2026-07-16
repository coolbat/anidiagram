import copy
import gzip
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from xml.etree import ElementTree

from anidiagram.diagram_core.asset_loader import (
    AssetValidationError,
    _declared_tokens as declared_tokens,
    load_asset,
    load_svg_source,
)
from anidiagram.diagram_core.manifest import (
    ManifestValidationError,
    load_manifest,
    validate_manifest_dict,
)
from anidiagram.diagram_core import tokens as diagram_core_tokens
from anidiagram.diagram_core.tokens import (
    contrast_ratio,
    icon_tokens_for_style,
    relative_luminance,
    token_css,
)
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]
ASSET_VALIDATOR = ROOT / "scripts" / "validate_diagram_core_assets.py"


def run_asset_validator(*arguments):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, str(ASSET_VALIDATOR), *arguments],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def copy_canonical_asset_root(temp_dir):
    destination = Path(temp_dir) / "diagram-core"
    shutil.copytree(ROOT / "assets" / "diagram-core", destination)
    return destination


def mutate_json_file(path, mutation):
    value = json.loads(path.read_text(encoding="utf-8"))
    mutation(value)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def replace_file_text(path, old, new):
    path.write_text(
        path.read_text(encoding="utf-8").replace(old, new),
        encoding="utf-8",
    )


def promote_benchmark_assets(asset_root):
    benchmark_ids = {"agent", "database", "api", "server"}

    def promote_catalog(catalog):
        for entry in catalog["icons"]:
            if entry["id"] in benchmark_ids:
                entry["status"] = "approved"

    mutate_json_file(asset_root / "catalog.json", promote_catalog)
    for icon_id in sorted(benchmark_ids):
        mutate_json_file(
            asset_root / "manifests" / (icon_id + ".json"),
            lambda manifest: manifest.__setitem__("status", "approved"),
        )


def asset_tree_snapshot(asset_root):
    return {
        path.relative_to(asset_root).as_posix(): (
            path.read_bytes(),
            path.stat().st_mode,
            path.stat().st_mtime_ns,
        )
        for path in sorted(asset_root.rglob("*"))
        if path.is_file()
    }

VALID_MANIFEST = {
    "id": "database",
    "system": "diagram-core-v1",
    "asset_revision": 1,
    "viewBox": "0 0 96 96",
    "category": "data-knowledge",
    "semantic_kind": "database",
    "structural_prototype": "stacked-storage",
    "parts": [
        "shell",
        "top-ring",
        "layer-top",
        "layer-middle",
        "layer-bottom",
        "core",
        "indicator",
    ],
    "attachments": {
        "receive": {"x": 48, "y": 8},
        "send": {"x": 88, "y": 48},
        "status": {"x": 48, "y": 78},
    },
    "states": [
        "idle",
        "active",
        "processing",
        "success",
        "warning",
        "error",
    ],
    "actions": ["receive", "write", "index", "search", "send"],
    "status": "visual-review",
}

MINIMAL_TOKENS = """:root {
  --icon-surface-main: #fffaf2;
  --icon-stroke: #14213d;
}
"""

REQUIRED_ICON_TOKENS = {
    "--icon-surface-main",
    "--icon-surface-secondary",
    "--icon-surface-recessed",
    "--icon-stroke",
    "--icon-detail",
    "--icon-accent",
    "--icon-accent-secondary",
    "--icon-status-idle",
    "--icon-status-active",
    "--icon-status-success",
    "--icon-status-warning",
    "--icon-status-error",
}

APPROVED_ICON_DEFAULTS = {
    "--icon-surface-main": "#fffaf2",
    "--icon-surface-secondary": "#eef1f5",
    "--icon-surface-recessed": "#dfe5ec",
    "--icon-stroke": "#14213d",
    "--icon-detail": "#64748b",
    "--icon-accent": "#7c5ce7",
    "--icon-accent-secondary": "#45c5bd",
    "--icon-status-idle": "#94a3b8",
    "--icon-status-active": "#38bdf8",
    "--icon-status-success": "#35b66f",
    "--icon-status-warning": "#f3a53a",
    "--icon-status-error": "#e65b65",
}

ASSET_LOCAL_TOKEN_DEFAULTS = {
    "--icon-surface-contrast": "#14213d",
}

STATE_MARK_GEOMETRY = (
    ("idle", "dot"),
    ("active", "ring"),
    ("processing", "split-arc"),
    ("success", "check"),
    ("warning", "triangle"),
    ("error", "X"),
)

AGENT_PARTS = {
    "shell",
    "face-screen",
    "eye-left",
    "eye-right",
    "mouth",
    "antenna",
    "core",
    "indicator",
}

AGENT_PART_ORDER = (
    "shell",
    "face-screen",
    "eye-left",
    "eye-right",
    "mouth",
    "antenna",
    "core",
    "indicator",
)

AGENT_STATES = (
    "idle",
    "active",
    "processing",
    "success",
    "warning",
    "error",
)

EXPECTED_BENCHMARK_PART_ORDER = {
    "agent": AGENT_PART_ORDER,
    "database": (
        "shell",
        "top-ring",
        "layer-top",
        "layer-middle",
        "layer-bottom",
        "core",
        "indicator",
    ),
    "api": (
        "shell",
        "header",
        "input-interface",
        "output-interface",
        "processor",
        "indicator-group",
    ),
    "server": (
        "shell",
        "tray-top",
        "tray-bottom",
        "indicator-top",
        "indicator-bottom",
        "vent-top",
        "vent-bottom",
        "base",
    ),
}

EXPECTED_BENCHMARK_PARTS = {
    icon_id: set(parts)
    for icon_id, parts in EXPECTED_BENCHMARK_PART_ORDER.items()
}

EXPECTED_BENCHMARK_PROTOTYPES = {
    "agent": "actor-character",
    "database": "stacked-storage",
    "api": "interface-module",
    "server": "compute-device",
}

EXPECTED_BENCHMARK_ACTIONS = {
    "agent": ("enter", "receive", "process", "send"),
    "database": ("receive", "write", "index", "search", "send"),
    "api": ("receive", "process", "send", "stream"),
    "server": ("enter", "receive", "process", "send"),
}

EXPECTED_BENCHMARK_ATTACHMENTS = {
    "agent": {"receive": (18, 48), "send": (78, 48), "status": (48, 74)},
    "database": {"receive": (48, 8), "send": (88, 48), "status": (48, 76)},
    "api": {"receive": (8, 48), "send": (88, 48), "status": (48, 22)},
    "server": {"receive": (8, 36), "send": (88, 60), "status": (76, 24)},
}

EXPECTED_BENCHMARK_INDICATORS = {
    "agent": "indicator",
    "database": "indicator",
    "api": "indicator-group",
    "server": "indicator-top",
}

EXPECTED_BENCHMARK_CONTRAST_PARTS = {
    "agent": "core",
    "database": "indicator",
    "api": "indicator-group",
    "server": "indicator-top",
}

SVG_PAINTABLE_TAGS = {
    "circle",
    "ellipse",
    "line",
    "path",
    "polygon",
    "polyline",
    "rect",
}


def local_name(name):
    return name.rsplit("}", 1)[-1]


def agent_geometry_bounds(element):
    tag = local_name(element.tag)
    if tag == "circle":
        cx = float(element.attrib["cx"])
        cy = float(element.attrib["cy"])
        radius = float(element.attrib["r"])
        bounds = (cx - radius, cy - radius, cx + radius, cy + radius)
    elif tag == "ellipse":
        cx = float(element.attrib["cx"])
        cy = float(element.attrib["cy"])
        rx = float(element.attrib["rx"])
        ry = float(element.attrib["ry"])
        bounds = (cx - rx, cy - ry, cx + rx, cy + ry)
    elif tag == "rect":
        x = float(element.attrib["x"])
        y = float(element.attrib["y"])
        bounds = (
            x,
            y,
            x + float(element.attrib["width"]),
            y + float(element.attrib["height"]),
        )
    elif tag == "line":
        x_values = (float(element.attrib["x1"]), float(element.attrib["x2"]))
        y_values = (float(element.attrib["y1"]), float(element.attrib["y2"]))
        bounds = (min(x_values), min(y_values), max(x_values), max(y_values))
    elif tag in {"polygon", "polyline"}:
        values = [
            float(value)
            for value in re.findall(r"-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)", element.attrib["points"])
        ]
        if len(values) < 4 or len(values) % 2:
            raise AssertionError("Agent point lists must contain coordinate pairs")
        bounds = (
            min(values[0::2]),
            min(values[1::2]),
            max(values[0::2]),
            max(values[1::2]),
        )
    elif tag == "path":
        commands = set(re.findall(r"[A-Za-z]", element.attrib["d"]))
        if not commands.issubset({"M", "L", "C", "Q", "Z"}):
            raise AssertionError("Agent paths must use absolute, auditable commands")
        values = [
            float(value)
            for value in re.findall(r"-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)", element.attrib["d"])
        ]
        if len(values) < 2 or len(values) % 2:
            raise AssertionError("Agent path coordinates must be explicit pairs")
        bounds = (
            min(values[0::2]),
            min(values[1::2]),
            max(values[0::2]),
            max(values[1::2]),
        )
    else:
        raise AssertionError("unsupported Agent paintable tag: " + tag)

    stroke = element.attrib.get("stroke", "none").strip().lower()
    extent = 0.0 if stroke == "none" else float(element.attrib["stroke-width"]) / 2.0
    return (
        bounds[0] - extent,
        bounds[1] - extent,
        bounds[2] + extent,
        bounds[3] + extent,
    )


def _quadratic_value(start, control, end, position):
    inverse = 1.0 - position
    return (
        inverse * inverse * start
        + 2.0 * inverse * position * control
        + position * position * end
    )


def _cubic_value(start, control_one, control_two, end, position):
    inverse = 1.0 - position
    return (
        inverse ** 3 * start
        + 3.0 * inverse * inverse * position * control_one
        + 3.0 * inverse * position * position * control_two
        + position ** 3 * end
    )


def _quadratic_extrema(start, control, end):
    denominator = start - 2.0 * control + end
    if abs(denominator) < 1e-12:
        return ()
    position = (start - control) / denominator
    return (position,) if 0.0 < position < 1.0 else ()


def _cubic_extrema(start, control_one, control_two, end):
    coefficient_a = -start + 3.0 * control_one - 3.0 * control_two + end
    coefficient_b = 2.0 * (start - 2.0 * control_one + control_two)
    coefficient_c = control_one - start
    if abs(coefficient_a) < 1e-12:
        if abs(coefficient_b) < 1e-12:
            return ()
        position = -coefficient_c / coefficient_b
        return (position,) if 0.0 < position < 1.0 else ()
    discriminant = coefficient_b * coefficient_b - 4.0 * coefficient_a * coefficient_c
    if discriminant < 0.0:
        return ()
    root = math.sqrt(max(0.0, discriminant))
    positions = (
        (-coefficient_b - root) / (2.0 * coefficient_a),
        (-coefficient_b + root) / (2.0 * coefficient_a),
    )
    return tuple(
        position
        for position in positions
        if 0.0 < position < 1.0
    )


def _path_geometry_points(path_data):
    tokens = re.findall(
        r"[MLCQZ]|-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)",
        path_data,
    )
    if not tokens or "".join(tokens) != re.sub(r"[\s,]+", "", path_data):
        raise AssertionError("benchmark paths must use explicit absolute M/L/C/Q/Z commands")
    points = []
    cursor = None
    subpath_start = None
    index = 0
    coordinate_counts = {"M": 2, "L": 2, "Q": 4, "C": 6, "Z": 0}
    while index < len(tokens):
        command = tokens[index]
        if command not in coordinate_counts:
            raise AssertionError("every benchmark path segment must name its command")
        index += 1
        count = coordinate_counts[command]
        if index + count > len(tokens):
            raise AssertionError("benchmark path command has incomplete coordinates")
        values = tuple(float(value) for value in tokens[index : index + count])
        index += count
        if index < len(tokens) and tokens[index] not in coordinate_counts:
            raise AssertionError("every benchmark path segment must name its command")

        if command == "M":
            cursor = (values[0], values[1])
            subpath_start = cursor
            points.append(cursor)
        elif command == "Z":
            if cursor is None or subpath_start is None:
                raise AssertionError("benchmark close command needs an open subpath")
            points.extend((cursor, subpath_start))
            cursor = subpath_start
        else:
            if cursor is None:
                raise AssertionError("benchmark path geometry must begin with M")
            if command == "L":
                end = (values[0], values[1])
                points.extend((cursor, end))
            elif command == "Q":
                control = (values[0], values[1])
                end = (values[2], values[3])
                positions = set(
                    _quadratic_extrema(cursor[0], control[0], end[0])
                    + _quadratic_extrema(cursor[1], control[1], end[1])
                )
                points.extend((cursor, end))
                points.extend(
                    (
                        _quadratic_value(cursor[0], control[0], end[0], position),
                        _quadratic_value(cursor[1], control[1], end[1], position),
                    )
                    for position in positions
                )
            elif command == "C":
                control_one = (values[0], values[1])
                control_two = (values[2], values[3])
                end = (values[4], values[5])
                positions = set(
                    _cubic_extrema(cursor[0], control_one[0], control_two[0], end[0])
                    + _cubic_extrema(cursor[1], control_one[1], control_two[1], end[1])
                )
                points.extend((cursor, end))
                points.extend(
                    (
                        _cubic_value(
                            cursor[0],
                            control_one[0],
                            control_two[0],
                            end[0],
                            position,
                        ),
                        _cubic_value(
                            cursor[1],
                            control_one[1],
                            control_two[1],
                            end[1],
                            position,
                        ),
                    )
                    for position in positions
                )
            cursor = end
    return tuple(points)


def benchmark_geometry_bounds(element):
    tag = local_name(element.tag)
    if tag == "circle":
        cx = float(element.attrib["cx"])
        cy = float(element.attrib["cy"])
        radius = float(element.attrib["r"])
        bounds = (cx - radius, cy - radius, cx + radius, cy + radius)
    elif tag == "ellipse":
        cx = float(element.attrib["cx"])
        cy = float(element.attrib["cy"])
        rx = float(element.attrib["rx"])
        ry = float(element.attrib["ry"])
        bounds = (cx - rx, cy - ry, cx + rx, cy + ry)
    elif tag == "rect":
        x = float(element.attrib["x"])
        y = float(element.attrib["y"])
        bounds = (
            x,
            y,
            x + float(element.attrib["width"]),
            y + float(element.attrib["height"]),
        )
    elif tag == "line":
        x_values = (float(element.attrib["x1"]), float(element.attrib["x2"]))
        y_values = (float(element.attrib["y1"]), float(element.attrib["y2"]))
        bounds = (min(x_values), min(y_values), max(x_values), max(y_values))
    elif tag in {"polygon", "polyline"}:
        values = [
            float(value)
            for value in re.findall(
                r"-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)",
                element.attrib["points"],
            )
        ]
        if len(values) < 4 or len(values) % 2:
            raise AssertionError("benchmark point lists must contain coordinate pairs")
        bounds = (
            min(values[0::2]),
            min(values[1::2]),
            max(values[0::2]),
            max(values[1::2]),
        )
    elif tag == "path":
        points = _path_geometry_points(element.attrib["d"])
        bounds = (
            min(point[0] for point in points),
            min(point[1] for point in points),
            max(point[0] for point in points),
            max(point[1] for point in points),
        )
    else:
        raise AssertionError("unsupported benchmark paintable tag: " + tag)

    stroke = element.attrib.get("stroke", "none").strip().lower()
    extent = 0.0 if stroke == "none" else float(element.attrib["stroke-width"]) / 2.0
    return (
        bounds[0] - extent,
        bounds[1] - extent,
        bounds[2] + extent,
        bounds[3] + extent,
    )


def agent_filled_area(element):
    tag = local_name(element.tag)
    if tag == "circle":
        return math.pi * float(element.attrib["r"]) ** 2
    if tag == "ellipse":
        return (
            math.pi
            * float(element.attrib["rx"])
            * float(element.attrib["ry"])
        )
    if tag == "rect":
        return float(element.attrib["width"]) * float(element.attrib["height"])
    raise AssertionError("visible Agent fills must use auditable primitive geometry")


def agent_state_geometry_signature(mark):
    signature = []
    for element in mark.iter():
        geometry = tuple(
            sorted(
                (name, value)
                for name, value in element.attrib.items()
                if name
                not in {
                    "data-state-mark",
                    "display",
                    "fill",
                    "stroke",
                    "data-stroke-role",
                }
            )
        )
        signature.append((local_name(element.tag), geometry))
    return tuple(signature)


def benchmark_state_mark_kind(mark):
    paintables = [
        element
        for element in mark.iter()
        if local_name(element.tag) in SVG_PAINTABLE_TAGS
    ]
    tags = tuple(local_name(element.tag) for element in paintables)
    state = mark.attrib["data-state-mark"]
    if state == "idle":
        return "dot" if tags == ("circle",) and paintables[0].attrib.get("fill") != "none" else None
    if state == "active":
        return (
            "ring"
            if tags == ("circle",)
            and paintables[0].attrib.get("fill") == "none"
            and paintables[0].attrib.get("stroke", "none") != "none"
            else None
        )
    if state == "processing":
        commands = tuple(
            command
            for element in paintables
            for command in re.findall(r"[A-Za-z]", element.attrib.get("d", ""))
        )
        return (
            "split-arc"
            if tags in {("path",), ("path", "path")}
            and commands == ("M", "C", "M", "C")
            and all(element.attrib.get("fill") == "none" for element in paintables)
            else None
        )
    if state == "success":
        commands = re.findall(r"[A-Za-z]", paintables[0].attrib.get("d", "")) if tags == ("path",) else ()
        return "check" if tuple(commands) == ("M", "L", "L") else None
    if state == "warning":
        values = re.findall(
            r"-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)",
            paintables[0].attrib.get("points", ""),
        ) if tags == ("polygon",) else ()
        return "triangle" if len(values) == 6 else None
    if state == "error":
        commands = re.findall(r"[A-Za-z]", paintables[0].attrib.get("d", "")) if tags == ("path",) else ()
        return "X" if tuple(commands) == ("M", "L", "M", "L") else None
    return None


def benchmark_state_bounds(mark):
    bounds = [
        benchmark_geometry_bounds(element)
        for element in mark.iter()
        if local_name(element.tag) in SVG_PAINTABLE_TAGS
    ]
    if not bounds:
        raise AssertionError("benchmark state marks must contain paintable geometry")
    return (
        min(bound[0] for bound in bounds),
        min(bound[1] for bound in bounds),
        max(bound[2] for bound in bounds),
        max(bound[3] for bound in bounds),
    )


def benchmark_parent_map(root):
    return {
        child: parent
        for parent in root.iter()
        for child in parent
    }


def benchmark_ancestors(element, parents):
    while element in parents:
        element = parents[element]
        yield element


def benchmark_public_part(element, parents):
    for candidate in (element, *benchmark_ancestors(element, parents)):
        if "data-part" in candidate.attrib:
            return candidate.attrib["data-part"]
    return None


def benchmark_is_hidden(element, parents):
    return any(
        candidate.attrib.get("display") == "none"
        for candidate in (element, *benchmark_ancestors(element, parents))
    )


def benchmark_filled_area(element):
    return agent_filled_area(element)


def agent_state_bounds(mark):
    bounds = [
        agent_geometry_bounds(element)
        for element in mark.iter()
        if local_name(element.tag) in SVG_PAINTABLE_TAGS
    ]
    if not bounds:
        raise AssertionError("Agent state marks must contain paintable geometry")
    return (
        min(bound[0] for bound in bounds),
        min(bound[1] for bound in bounds),
        max(bound[2] for bound in bounds),
        max(bound[3] for bound in bounds),
    )


def agent_radial_extent(element, center_x, center_y):
    stroke = element.attrib.get("stroke", "none").strip().lower()
    stroke_extent = (
        0.0 if stroke == "none" else float(element.attrib["stroke-width"]) / 2.0
    )
    tag = local_name(element.tag)
    if tag == "circle":
        center_distance = math.hypot(
            float(element.attrib["cx"]) - center_x,
            float(element.attrib["cy"]) - center_y,
        )
        return center_distance + float(element.attrib["r"]) + stroke_extent
    if tag in {"path", "polygon", "polyline"}:
        attribute = "d" if tag == "path" else "points"
        values = [
            float(value)
            for value in re.findall(
                r"-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)",
                element.attrib[attribute],
            )
        ]
        return max(
            math.hypot(x - center_x, y - center_y)
            for x, y in zip(values[0::2], values[1::2])
        ) + stroke_extent
    raise AssertionError("state clearance uses explicit circle/path/point geometry")


def css_declarations(source, selector):
    match = re.search(re.escape(selector) + r"\s*\{([^{}]*)\}", source)
    if match is None:
        raise AssertionError("missing CSS declaration block: " + selector)
    declarations = {}
    for statement in match.group(1).split(";"):
        if ":" not in statement:
            continue
        name, value = statement.split(":", 1)
        declarations[name.strip()] = value.strip()
    return declarations


def state_scope_pairs(source):
    scope_header = "@scope ([data-icon-state]) to ([data-icon-state])"
    scope_start = source.find(scope_header)
    if scope_start < 0:
        raise AssertionError("state rules must stop at the next nested icon state")
    block_start = source.find("{", scope_start + len(scope_header))
    depth = 0
    block_end = None
    for index in range(block_start, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                block_end = index + 1
                break
    if block_start < 0 or block_end is None:
        raise AssertionError("state scope must be a balanced CSS block")

    selector_pattern = (
        r':scope\[data-icon-state="([^"]+)"\]\s+'
        r'\[data-state-mark="([^"]+)"\]'
    )
    scoped_pairs = re.findall(selector_pattern, source[block_start:block_end])
    outside = source[:scope_start] + source[block_end:]
    if re.search(selector_pattern.replace(":scope", "[^,{]*"), outside):
        raise AssertionError("state reveal rules must not escape the nearest icon scope")
    return scoped_pairs


def valid_svg():
    part_shapes = "\n".join(
        '  <g data-part="{0}"><circle cx="48" cy="48" r="4" '
        'fill="var(--icon-surface-main, #fffaf2)" '
        'stroke="var(--icon-stroke, #14213d)"/></g>'.format(part)
        for part in VALID_MANIFEST["parts"]
    )
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96"
 role="img" focusable="false" aria-label="Database icon" data-icon="database">
{0}
</svg>
""".format(part_shapes)


class TemporaryAssetBundle:
    def __init__(self, root):
        self.root = Path(root)
        self.icon_path = self.root / "icons" / "database.svg"
        self.manifest_path = self.root / "manifests" / "database.json"
        self.catalog_path = self.root / "catalog.json"
        self.tokens_path = self.root / "tokens.css"

    def write(
        self,
        manifest=None,
        svg=None,
        tokens=MINIMAL_TOKENS,
        catalog=None,
    ):
        (self.root / "icons").mkdir(parents=True, exist_ok=True)
        (self.root / "manifests").mkdir(parents=True, exist_ok=True)
        source_catalog = json.loads(
            (ROOT / "assets" / "diagram-core" / "catalog.json").read_text(
                encoding="utf-8"
            )
        )
        self.catalog_path.write_text(
            json.dumps(source_catalog if catalog is None else catalog),
            encoding="utf-8",
        )
        self.manifest_path.write_text(
            json.dumps(VALID_MANIFEST if manifest is None else manifest),
            encoding="utf-8",
        )
        self.icon_path.write_text(valid_svg() if svg is None else svg, encoding="utf-8")
        if tokens is not None:
            self.tokens_path.write_text(tokens, encoding="utf-8")
        return self


class DiagramCoreManifestTest(unittest.TestCase):
    def test_manifest_accepts_frozen_contract_and_is_read_only(self):
        manifest = validate_manifest_dict(VALID_MANIFEST)

        self.assertEqual("database", manifest.icon_id)
        self.assertEqual("0 0 96 96", manifest.view_box)
        self.assertEqual(tuple(VALID_MANIFEST["parts"]), manifest.parts)
        self.assertEqual(("receive", "send", "status"), tuple(manifest.attachments))
        with self.assertRaises(FrozenInstanceError):
            manifest.status = "approved"
        with self.assertRaises(TypeError):
            manifest.attachments["send"] = manifest.attachments["send"]

    def test_manifest_aggregates_scene_selector_and_attachment_bounds_issues(self):
        invalid = copy.deepcopy(VALID_MANIFEST)
        invalid["parts"] = ["#database__shell"]
        invalid["attachments"]["send"]["x"] = 97

        with self.assertRaises(ManifestValidationError) as raised:
            validate_manifest_dict(invalid)

        self.assertEqual(
            {"$.parts[0]", "$.attachments.send.x"},
            {issue.path for issue in raised.exception.issues},
        )

    def test_manifest_rejects_each_frozen_scalar_contract(self):
        cases = (
            ("system", lambda value: value.__setitem__("system", "diagram-core-v2"), "$.system"),
            ("boolean revision", lambda value: value.__setitem__("asset_revision", True), "$.asset_revision"),
            ("zero revision", lambda value: value.__setitem__("asset_revision", 0), "$.asset_revision"),
            ("viewBox", lambda value: value.__setitem__("viewBox", "0 0 48 48"), "$.viewBox"),
            ("duplicate part", lambda value: value["parts"].__setitem__(1, "shell"), "$.parts[1]"),
            ("invalid attachment name", lambda value: value["attachments"].__setitem__("#send", {"x": 1, "y": 1}), "$.attachments.#send"),
            ("boolean coordinate", lambda value: value["attachments"]["send"].__setitem__("x", True), "$.attachments.send.x"),
            ("nan coordinate", lambda value: value["attachments"]["send"].__setitem__("x", math.nan), "$.attachments.send.x"),
            ("infinite coordinate", lambda value: value["attachments"]["send"].__setitem__("x", math.inf), "$.attachments.send.x"),
        )
        for label, mutate, expected_path in cases:
            with self.subTest(label=label):
                invalid = copy.deepcopy(VALID_MANIFEST)
                mutate(invalid)
                with self.assertRaises(ManifestValidationError) as raised:
                    validate_manifest_dict(invalid)
                self.assertIn(expected_path, {issue.path for issue in raised.exception.issues})

    def test_manifest_requires_all_six_benchmark_review_states(self):
        invalid = copy.deepcopy(VALID_MANIFEST)
        invalid["states"].remove("warning")

        with self.assertRaises(ManifestValidationError) as raised:
            validate_manifest_dict(invalid)

        self.assertEqual({"$.states"}, {issue.path for issue in raised.exception.issues})

    def test_manifest_rejects_boolean_incomplete_and_duplicate_exceptions(self):
        complete = {
            "metric": "paintable-elements",
            "reason": "Reviewed optical requirement",
            "reviewer": "diagram-core-reviewer",
            "approved_on": "2026-07-16",
        }
        cases = (
            (True, "$.exceptions"),
            (None, "$.exceptions"),
            ([{"metric": "paintable-elements"}], "$.exceptions[0].reason"),
            ([dict(complete, metric="unknown")], "$.exceptions[0].metric"),
            ([complete, complete], "$.exceptions[1].metric"),
        )
        for exceptions, expected_path in cases:
            with self.subTest(exceptions=exceptions):
                invalid = copy.deepcopy(VALID_MANIFEST)
                invalid["exceptions"] = exceptions
                with self.assertRaises(ManifestValidationError) as raised:
                    validate_manifest_dict(invalid)
                self.assertIn(expected_path, {issue.path for issue in raised.exception.issues})

    def test_load_manifest_uses_injected_root_and_reports_json_location(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            self.assertEqual("database", load_manifest("database", bundle.root).icon_id)

            bundle.manifest_path.write_text('{"id":', encoding="utf-8")
            with self.assertRaises(ManifestValidationError) as raised:
                load_manifest("database", bundle.root)
            self.assertIn(str(bundle.manifest_path), str(raised.exception))
            self.assertRegex(str(raised.exception), r"line 1, column [0-9]+")

    def test_aggregate_gate_rejects_all_duplicate_json_keys_with_nested_paths(self):
        manifest = copy.deepcopy(VALID_MANIFEST)
        manifest["exceptions"] = [
            {
                "metric": "raw-size",
                "reason": "Reviewed source budget",
                "reviewer": "diagram-core-reviewer",
                "approved_on": "2026-07-16",
            }
        ]
        source = json.dumps(manifest)
        source = source.replace(
            '"status": "visual-review"',
            '"status": "visual-review", "status": "visual-review"',
            1,
        )
        source = source.replace(
            '"send": {"x": 88, "y": 48}',
            '"send": {"x": 88, "x": 89, "y": 48}',
            1,
        )
        source = source.replace(
            '"reason": "Reviewed source budget"',
            '"reason": "Reviewed source budget", "reason": "Still reviewed"',
            1,
        )
        self.assertEqual(2, source.count('"status": "visual-review"'))
        self.assertEqual(2, source.count('"reason":'))

        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write(manifest=manifest)
            bundle.manifest_path.write_text(source, encoding="utf-8")

            with self.assertRaises(AssetValidationError) as raised:
                load_asset("database", {"visual-review"}, bundle.root)

            duplicate_paths = {
                issue.path
                for issue in raised.exception.issues
                if "duplicate JSON key" in issue.message
            }
            self.assertEqual(
                {
                    str(bundle.manifest_path) + ":$.status",
                    str(bundle.manifest_path) + ":$.attachments.send.x",
                    str(bundle.manifest_path) + ":$.exceptions[0].reason",
                },
                duplicate_paths,
            )

    def test_manifest_schema_freezes_shape_and_exception_approval_fields(self):
        schema = json.loads(
            (ROOT / "schemas" / "diagram-core-icon-manifest-v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            {
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
            },
            set(schema["required"]),
        )
        exception = schema["$defs"]["exception"]
        self.assertFalse(exception["additionalProperties"])
        self.assertEqual(
            {"metric", "reason", "reviewer", "approved_on"},
            set(exception["required"]),
        )


class DiagramCoreAssetLoaderTest(unittest.TestCase):
    def assert_asset_error(self, bundle, svg, expected):
        bundle.icon_path.write_text(svg, encoding="utf-8")
        with self.assertRaises(AssetValidationError) as raised:
            load_asset("database", {"visual-review"}, bundle.root)
        self.assertIn(expected, str(raised.exception))
        self.assertIn(str(bundle.icon_path), str(raised.exception))
        return raised.exception

    def test_load_asset_is_the_aggregate_read_only_gate_and_reports_metrics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()

            asset = load_asset("database", {"visual-review"}, bundle.root)

            source_bytes = bundle.icon_path.read_bytes()
            self.assertEqual(valid_svg(), asset.svg_source)
            self.assertEqual("svg", asset.root.tag.rsplit("}", 1)[-1])
            self.assertEqual(tuple(VALID_MANIFEST["parts"]), asset.public_parts)
            self.assertEqual(0, asset.metrics.forbidden_elements)
            self.assertEqual(7, asset.metrics.paintable_elements)
            self.assertEqual(15, asset.metrics.total_dom_elements)
            self.assertEqual(len(source_bytes), asset.metrics.raw_size_bytes)
            self.assertEqual(
                len(gzip.compress(source_bytes, compresslevel=9, mtime=0)),
                asset.metrics.gzip_size_bytes,
            )
            with self.assertRaises(FrozenInstanceError):
                asset.svg_source = "changed"
            with self.assertRaises(FrozenInstanceError):
                asset.metrics.paintable_elements = 0

    def test_load_svg_source_uses_injected_asset_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            self.assertEqual(valid_svg(), load_svg_source("database", bundle.root))

    def test_root_accessibility_and_identity_attributes_fail_independently(self):
        replacements = (
            ("role", 'role="img"', 'role="presentation"', "/svg/@role"),
            ("focusable", 'focusable="false"', 'focusable="true"', "/svg/@focusable"),
            ("aria label", 'aria-label="Database icon"', 'aria-label="  "', "/svg/@aria-label"),
            ("data icon", 'data-icon="database"', 'data-icon="api"', "/svg/@data-icon"),
            ("viewBox", 'viewBox="0 0 96 96"', 'viewBox="0 0 48 48"', "/svg/@viewBox"),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            for label, before, after, expected in replacements:
                with self.subTest(label=label):
                    self.assert_asset_error(bundle, valid_svg().replace(before, after), expected)

    def test_wrong_or_foreign_xml_namespaces_fail_closed(self):
        cases = (
            (
                "wrong root namespace",
                valid_svg().replace("http://www.w3.org/2000/svg", "https://example.test/svg"),
                "/svg",
            ),
            (
                "foreign child namespace",
                valid_svg().replace(
                    "</svg>",
                    '<evil:payload xmlns:evil="https://example.test/evil"/></svg>',
                ),
                "foreign XML namespace",
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            for label, svg, expected in cases:
                with self.subTest(label=label):
                    self.assert_asset_error(bundle, svg, expected)

    def test_each_forbidden_svg_element_is_rejected(self):
        elements = {
            "script": "<script>alert(1)</script>",
            "foreignObject": "<foreignObject/>",
            "image": '<image href="pixel.png"/>',
            "text": "<text>runtime label</text>",
            "animate": '<animate attributeName="opacity" dur="1s"/>',
            "animateMotion": '<animateMotion dur="1s"/>',
            "animateTransform": '<animateTransform attributeName="transform"/>',
            "set": '<set attributeName="opacity" to="0"/>',
            "filter": "<filter/>",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            for tag, fragment in elements.items():
                with self.subTest(tag=tag):
                    error = self.assert_asset_error(
                        bundle,
                        valid_svg().replace("</svg>", fragment + "</svg>"),
                        "forbidden element <{0}>".format(tag),
                    )
                    self.assertTrue(any(issue.path.endswith("/" + tag) for issue in error.issues))

    def test_javascript_event_handlers_and_css_animation_are_rejected(self):
        cases = (
            (
                "event handler",
                valid_svg().replace("<circle", '<circle onclick="alert(1)"', 1),
                "event handler",
            ),
            (
                "javascript URI",
                valid_svg().replace("</svg>", '<use href="javascript:alert(1)"/></svg>'),
                "JavaScript URI",
            ),
            (
                "CSS animation",
                valid_svg().replace("<circle", '<circle style="animation: pulse 1s"', 1),
                "animation declarations",
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            for label, svg, expected in cases:
                with self.subTest(label=label):
                    self.assert_asset_error(bundle, svg, expected)

    def test_css_comments_cannot_hide_animation_or_filter_properties(self):
        cases = (
            (
                "animation",
                valid_svg().replace(
                    "<circle",
                    '<circle style="fill: red; /* bypass */ animation: pulse 1s"',
                    1,
                ),
                "animation declarations",
            ),
            (
                "filter",
                valid_svg().replace(
                    "<circle",
                    '<circle style="fill: red; /* bypass */ filter: blur(1px)"',
                    1,
                ),
                "filter effects",
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            for label, svg, expected in cases:
                with self.subTest(label=label):
                    self.assert_asset_error(bundle, svg, expected)

    def test_css_backslash_escapes_fail_closed_at_style_paths(self):
        cases = (
            (
                "escaped import in style element",
                valid_svg().replace(
                    "</svg>",
                    r'<style>@\69mport "https://example.test/icon.css";</style></svg>',
                ),
                "/style/#text",
            ),
            (
                "comment plus escaped animation in style element",
                valid_svg().replace(
                    "</svg>",
                    r"<style>circle { /* bypass */ ANIM\61TION: pulse 1s; }</style></svg>",
                ),
                "/style/#text",
            ),
            (
                "escaped animation in style attribute",
                valid_svg().replace(
                    "<circle", r'<circle style="anim\61tion: pulse 1s"', 1
                ),
                "/@style",
            ),
            (
                "escaped filter in style attribute",
                valid_svg().replace(
                    "<circle", r'<circle style="FILT\65R: blur(1px)"', 1
                ),
                "/@style",
            ),
            (
                "escaped vector effect property in style attribute",
                valid_svg().replace(
                    "<circle",
                    r'<circle style="vector\2d effect: non-scaling-stroke"',
                    1,
                ),
                "/@style",
            ),
            (
                "escaped non-scaling-stroke value in style element",
                valid_svg().replace(
                    "</svg>",
                    r"<style>circle { vector-effect: non-scaling\2d stroke; }</style></svg>",
                ),
                "/style/#text",
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            for label, svg, expected_path in cases:
                with self.subTest(label=label):
                    bundle.icon_path.write_text(svg, encoding="utf-8")
                    with self.assertRaises(AssetValidationError) as raised:
                        load_asset("database", {"visual-review"}, bundle.root)
                    self.assertTrue(
                        any(
                            issue.path.endswith(expected_path)
                            and "backslash escape" in issue.message
                            for issue in raised.exception.issues
                        )
                    )

    def test_external_data_and_unresolved_fragment_references_are_rejected(self):
        cases = (
            ("external href", '<use href="https://example.test/icon.svg#shape"/>', "external reference"),
            ("data URI", '<use href="data:image/png;base64,AA=="/>', "data URI"),
            ("external url", '<circle fill="url(https://example.test/paint.svg#x)"/>', "external URL"),
            ("unresolved href", '<use href="#missing"/>', "unresolved fragment"),
            ("unresolved url", '<circle fill="url(#missing)"/>', "unresolved fragment"),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            for label, fragment, expected in cases:
                with self.subTest(label=label):
                    self.assert_asset_error(
                        bundle,
                        valid_svg().replace("</svg>", fragment + "</svg>"),
                        expected,
                    )

    def test_stylesheet_processing_instructions_and_css_imports_are_rejected(self):
        cases = (
            (
                "XML stylesheet",
                '<?xml-stylesheet href="https://example.test/icon.css"?>\n'
                + valid_svg(),
                "stylesheet processing instructions",
            ),
            (
                "CSS import",
                valid_svg().replace(
                    "</svg>",
                    '<style>@import "https://example.test/icon.css";</style></svg>',
                ),
                "CSS @import",
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            for label, svg, expected in cases:
                with self.subTest(label=label):
                    self.assert_asset_error(bundle, svg, expected)

    def test_filter_attribute_is_rejected_even_without_filter_element(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            self.assert_asset_error(
                bundle,
                valid_svg().replace("<circle", '<circle filter="none"', 1),
                "filter effects are forbidden",
            )

    def test_authored_ids_are_rejected_at_the_exact_element(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            error = self.assert_asset_error(
                bundle,
                valid_svg().replace("<g data-part", '<g id="author-id" data-part', 1),
                "authored id",
            )
            self.assertTrue(any(issue.path.endswith("/g[1]/@id") for issue in error.issues))

    def test_public_parts_reject_anonymous_duplicate_missing_and_extra_values(self):
        cases = (
            (
                "anonymous",
                valid_svg().replace('data-part="shell"', 'data-part=""'),
                "data-part must not be empty",
            ),
            (
                "duplicate",
                valid_svg().replace('data-part="top-ring"', 'data-part="shell"'),
                "duplicate public data-part",
            ),
            (
                "missing",
                valid_svg().replace(' data-part="indicator"', ""),
                "public parts do not match manifest",
            ),
            (
                "extra",
                valid_svg().replace(
                    "</svg>", '<g data-part="private-leak"/></svg>'
                ),
                "public parts do not match manifest",
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            for label, svg, expected in cases:
                with self.subTest(label=label):
                    self.assert_asset_error(bundle, svg, expected)

    def test_non_scaling_stroke_requires_a_complete_metric_exception(self):
        svg = valid_svg().replace(
            "<circle", '<circle vector-effect="non-scaling-stroke"', 1
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write(svg=svg)
            self.assert_asset_error(bundle, svg, "non-scaling-stroke")

            manifest = copy.deepcopy(VALID_MANIFEST)
            manifest["exceptions"] = [
                {
                    "metric": "non-scaling-stroke",
                    "reason": "Optical review at 48px",
                    "reviewer": "diagram-core-reviewer",
                    "approved_on": "2026-07-16",
                }
            ]
            bundle.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(7, load_asset("database", {"visual-review"}, bundle.root).metrics.paintable_elements)

    def test_non_scaling_stroke_cannot_hide_in_whitespace_or_css(self):
        cases = (
            valid_svg().replace(
                "<circle", '<circle vector-effect=" non-scaling-stroke "', 1
            ),
            valid_svg().replace(
                "<circle", '<circle style="vector-effect: non-scaling-stroke"', 1
            ),
            valid_svg().replace(
                "</svg>",
                "<style>circle { vector-effect: non-scaling-stroke; }</style></svg>",
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            for svg in cases:
                with self.subTest(svg=svg[-100:]):
                    self.assert_asset_error(bundle, svg, "non-scaling-stroke")

    def test_variable_vector_effect_requires_exception_on_every_css_surface(self):
        tokens = MINIMAL_TOKENS + "\n:root { --icon-vector-effect: none; }\n"
        cases = (
            (
                "presentation attribute with non-scaling fallback",
                valid_svg().replace(
                    "<circle",
                    '<circle vector-effect="var(--icon-vector-effect, non-scaling-stroke)"',
                    1,
                ),
                "/@vector-effect",
            ),
            (
                "presentation attribute with none fallback",
                valid_svg().replace(
                    "<circle",
                    '<circle vector-effect="var(--icon-vector-effect, none)"',
                    1,
                ),
                "/@vector-effect",
            ),
            (
                "style attribute",
                valid_svg().replace(
                    "<circle",
                    '<circle style="vector-effect: var(--icon-vector-effect, none)"',
                    1,
                ),
                "/@style",
            ),
            (
                "style element with comments case and whitespace",
                valid_svg().replace(
                    "</svg>",
                    "<style>circle { VeCtOr-EfFeCt /* review */ : "
                    "VAR( --icon-vector-effect , none ); }</style></svg>",
                ),
                "/style/#text",
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write(tokens=tokens)
            for label, svg, expected_path in cases:
                with self.subTest(label=label):
                    bundle.icon_path.write_text(svg, encoding="utf-8")
                    with self.assertRaises(AssetValidationError) as raised:
                        load_asset("database", {"visual-review"}, bundle.root)
                    self.assertTrue(
                        any(
                            issue.path.endswith(expected_path)
                            and "variable vector-effect requires" in issue.message
                            for issue in raised.exception.issues
                        )
                    )

    def test_variable_vector_effect_accepts_complete_exception(self):
        manifest = copy.deepcopy(VALID_MANIFEST)
        manifest["exceptions"] = [
            {
                "metric": "non-scaling-stroke",
                "reason": "Runtime token behavior reviewed",
                "reviewer": "diagram-core-reviewer",
                "approved_on": "2026-07-16",
            }
        ]
        svg = valid_svg().replace(
            "<circle",
            '<circle vector-effect="var(--icon-vector-effect, none)"',
            1,
        )
        tokens = MINIMAL_TOKENS + "\n:root { --icon-vector-effect: none; }\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write(
                manifest=manifest,
                svg=svg,
                tokens=tokens,
            )
            asset = load_asset("database", {"visual-review"}, bundle.root)
            self.assertEqual("database", asset.manifest.icon_id)

    def test_css_vars_require_literal_fallbacks_and_declared_tokens(self):
        cases = (
            (
                "missing fallback",
                valid_svg().replace(
                    "var(--icon-surface-main, #fffaf2)",
                    "var(--icon-surface-main)",
                    1,
                ),
                "literal fallback",
            ),
            (
                "undeclared token",
                valid_svg().replace("--icon-surface-main", "--icon-unknown", 1),
                "not declared in tokens.css",
            ),
            (
                "nested variable fallback",
                valid_svg().replace(
                    "var(--icon-surface-main, #fffaf2)",
                    "var(--icon-surface-main, var(--icon-stroke, #14213d))",
                    1,
                ),
                "fallback must be literal",
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            for label, svg, expected in cases:
                with self.subTest(label=label):
                    self.assert_asset_error(bundle, svg, expected)

    def test_token_declaration_spoofs_do_not_declare_svg_vars(self):
        cases = (
            (
                "escaped quote string",
                "--icon-string-spoof",
                r':root { content: "escaped \" quote --icon-string-spoof:"; }',
            ),
            (
                "selector",
                "--icon-selector-spoof",
                "@media (min-width: 1px) "
                "{ .--icon-selector-spoof:focus { color: red; } }",
            ),
            (
                "at-rule condition",
                "--icon-supports-spoof",
                "@media (min-width: 1px) "
                "{ @supports (--icon-supports-spoof: value) "
                "{ .supported { color: green; } } }",
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            for label, token, spoof in cases:
                with self.subTest(label=label):
                    svg = valid_svg().replace("--icon-surface-main", token, 1)
                    bundle.icon_path.write_text(svg, encoding="utf-8")
                    bundle.tokens_path.write_text(
                        MINIMAL_TOKENS + "\n" + spoof + "\n",
                        encoding="utf-8",
                    )
                    with self.assertRaises(AssetValidationError) as raised:
                        load_asset("database", {"visual-review"}, bundle.root)
                    self.assertTrue(
                        any(
                            issue.path.endswith("/svg/g[1]/circle/@fill")
                            and token in issue.message
                            and "not declared in tokens.css" in issue.message
                            for issue in raised.exception.issues
                        )
                    )

    def test_real_token_declarations_work_in_root_context_and_nested_blocks(self):
        svg = (
            valid_svg()
            .replace("--icon-surface-main", "--icon-real-first")
            .replace("--icon-stroke", "--icon-real-after")
        )
        cases = (
            (
                "root",
                r""":root {
                  /* before first */ --icon-real-first : #fffaf2;
                  content: "escaped \"; semicolon";
                  --icon-real-after: #14213d;
                }""",
            ),
            (
                "context selector",
                """[data-icon-context="dark"] {
                  --icon-real-first: #101828;
                  --icon-real-after : #f8fafc;
                }""",
            ),
            (
                "nested context block",
                """@media (prefers-color-scheme: dark) {
                  [data-icon-context="nested"] {
                    --icon-real-first: #101828;
                    /* between declarations */
                    --icon-real-after: #f8fafc;
                  }
                }""",
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write(svg=svg)
            for label, tokens in cases:
                with self.subTest(label=label):
                    bundle.tokens_path.write_text(tokens, encoding="utf-8")
                    asset = load_asset("database", {"visual-review"}, bundle.root)
                    self.assertEqual("database", asset.manifest.icon_id)

    def test_missing_tokens_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write(tokens=None)
            with self.assertRaises(AssetValidationError) as raised:
                load_asset("database", {"visual-review"}, bundle.root)
            self.assertIn(str(bundle.tokens_path), str(raised.exception))

    def test_paintable_budget_counts_only_frozen_paintable_tags(self):
        private_shapes = "".join('<circle cx="1" cy="1" r="1"/>' for _ in range(18))
        svg = valid_svg().replace("</svg>", private_shapes + "</svg>")
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write(svg=svg)
            self.assert_asset_error(bundle, svg, "paintable-elements budget")

            manifest = copy.deepcopy(VALID_MANIFEST)
            manifest["exceptions"] = [
                {
                    "metric": "paintable-elements",
                    "reason": "Reviewed detail requirement",
                    "reviewer": "diagram-core-reviewer",
                    "approved_on": "2026-07-16",
                }
            ]
            bundle.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            asset = load_asset("database", {"visual-review"}, bundle.root)
            self.assertEqual(25, asset.metrics.paintable_elements)

            nonpaintable = valid_svg().replace("</svg>", "<g/>" * 30 + "</svg>")
            bundle.manifest_path.write_text(json.dumps(VALID_MANIFEST), encoding="utf-8")
            bundle.icon_path.write_text(nonpaintable, encoding="utf-8")
            asset = load_asset("database", {"visual-review"}, bundle.root)
            self.assertEqual(7, asset.metrics.paintable_elements)
            self.assertEqual(45, asset.metrics.total_dom_elements)

    def test_raw_and_gzip_budgets_are_measured_separately_and_waivable(self):
        cases = []
        raw_svg = valid_svg().replace("</svg>", (" " * (13 * 1024)) + "</svg>")
        cases.append(("raw-size", raw_svg, "raw-size budget"))

        rng = random.Random(7)
        noisy = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(10000))
        gzip_svg = valid_svg().replace("</svg>", "<metadata>" + noisy + "</metadata></svg>")
        self.assertLessEqual(len(gzip_svg.encode("utf-8")), 12 * 1024)
        self.assertGreater(
            len(gzip.compress(gzip_svg.encode("utf-8"), compresslevel=9, mtime=0)),
            6 * 1024,
        )
        cases.append(("gzip-size", gzip_svg, "gzip-size budget"))

        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            for metric, svg, expected in cases:
                with self.subTest(metric=metric):
                    self.assert_asset_error(bundle, svg, expected)
                    manifest = copy.deepcopy(VALID_MANIFEST)
                    manifest["exceptions"] = [
                        {
                            "metric": metric,
                            "reason": "Reviewed source budget",
                            "reviewer": "diagram-core-reviewer",
                            "approved_on": "2026-07-16",
                        }
                    ]
                    bundle.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                    bundle.icon_path.write_text(svg, encoding="utf-8")
                    load_asset("database", {"visual-review"}, bundle.root)
                    bundle.manifest_path.write_text(json.dumps(VALID_MANIFEST), encoding="utf-8")

    def test_catalog_manifest_parity_covers_all_nine_duplicated_fields(self):
        cases = (
            ("id", "id", lambda value: "database-alt"),
            ("category", "category", lambda value: "data-platform"),
            ("semantic_kind", "semantic_kind", lambda value: "storage"),
            ("structural_prototype", "structural_prototype", lambda value: "storage-stack"),
            ("parts", "parts", lambda value: value[:-1] + ["status-mark"]),
            ("supported_states", "states", lambda value: value[1:] + value[:1]),
            ("supported_actions", "actions", lambda value: value[1:] + value[:1]),
            ("status", "status", lambda value: "approved"),
            ("asset_revision", "asset_revision", lambda value: 2),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            for catalog_field, manifest_field, change in cases:
                with self.subTest(field=catalog_field):
                    invalid = copy.deepcopy(VALID_MANIFEST)
                    invalid[manifest_field] = change(invalid[manifest_field])
                    bundle.manifest_path.write_text(json.dumps(invalid), encoding="utf-8")
                    with self.assertRaises(AssetValidationError) as raised:
                        load_asset("database", {"visual-review", "approved"}, bundle.root)
                    message = str(raised.exception)
                    self.assertIn(str(bundle.catalog_path), message)
                    self.assertIn(str(bundle.manifest_path), message)
                    self.assertIn("$.icons[", message)
                    self.assertIn("$." + manifest_field, message)

    def test_status_gate_rejects_assets_outside_explicit_allow_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write()
            with self.assertRaises(AssetValidationError) as raised:
                load_asset("database", {"approved"}, bundle.root)
            self.assertIn("visual-review", str(raised.exception))
            self.assertIn("allow_statuses", str(raised.exception))

    def test_malformed_xml_reports_the_svg_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = TemporaryAssetBundle(temp_dir).write(svg="<svg>")
            with self.assertRaises(AssetValidationError) as raised:
                load_asset("database", {"visual-review"}, bundle.root)
            self.assertIn(str(bundle.icon_path), str(raised.exception))
            self.assertIn("invalid XML", str(raised.exception))


class CanonicalBenchmarkContractTest(unittest.TestCase):
    def load_benchmark(self, icon_id):
        return load_asset(icon_id, allow_statuses={"visual-review"})

    def parts_by_name(self, asset):
        return {
            element.attrib["data-part"]: element
            for element in asset.root.iter()
            if "data-part" in element.attrib
        }

    def assert_catalog_parity(self, asset):
        catalog = json.loads(
            (ROOT / "assets" / "diagram-core" / "catalog.json").read_text(
                encoding="utf-8"
            )
        )
        entry = next(
            icon
            for icon in catalog["icons"]
            if icon["id"] == asset.manifest.icon_id
        )
        manifest_values = {
            "id": asset.manifest.icon_id,
            "category": asset.manifest.category,
            "semantic_kind": asset.manifest.semantic_kind,
            "structural_prototype": asset.manifest.structural_prototype,
            "parts": list(asset.manifest.parts),
            "supported_states": list(asset.manifest.states),
            "supported_actions": list(asset.manifest.actions),
            "status": asset.manifest.status,
            "asset_revision": asset.manifest.asset_revision,
        }
        self.assertEqual(
            {field: entry[field] for field in manifest_values},
            manifest_values,
        )

    def assert_common_visual_contract(self, icon_id):
        asset = self.load_benchmark(icon_id)
        self.assertEqual("visual-review", asset.manifest.status)
        self.assertEqual(AGENT_STATES, asset.manifest.states)
        self.assertEqual((), asset.manifest.exceptions)
        self.assertEqual(0, asset.metrics.forbidden_elements)
        self.assertLessEqual(asset.metrics.paintable_elements, 24)
        self.assertLessEqual(asset.metrics.raw_size_bytes, 12 * 1024)
        self.assertLessEqual(asset.metrics.gzip_size_bytes, 6 * 1024)
        self.assert_catalog_parity(asset)

        root = asset.root
        self.assertEqual("img", root.attrib.get("role"))
        self.assertEqual("false", root.attrib.get("focusable"))
        self.assertTrue(root.attrib.get("aria-label", "").strip())
        self.assertEqual(icon_id, root.attrib.get("data-icon"))
        self.assertEqual("idle", root.attrib.get("data-icon-state"))
        self.assertFalse(any("id" in element.attrib for element in root.iter()))
        self.assertFalse(any("style" in element.attrib for element in root.iter()))
        self.assertFalse(any("transform" in element.attrib for element in root.iter()))
        self.assertFalse(
            any(local_name(element.tag) == "style" for element in root.iter())
        )
        self.assertNotRegex(
            asset.svg_source.lower(),
            r"\b(?:gradient|shadow|effect|connection-anchor|network)\b",
        )
        self.assertNotRegex(asset.svg_source.lower(), r"data-(?:connection-)?anchor")

        parts = self.parts_by_name(asset)
        indicator = parts[EXPECTED_BENCHMARK_INDICATORS[icon_id]]
        marks = [
            element
            for element in root.iter()
            if "data-state-mark" in element.attrib
        ]
        self.assertEqual(AGENT_STATES, tuple(mark.attrib["data-state-mark"] for mark in marks))
        self.assertEqual(6, len(marks))
        self.assertTrue(set(marks).issubset(set(indicator.iter())))
        signatures = tuple(agent_state_geometry_signature(mark) for mark in marks)
        self.assertEqual(6, len(set(signatures)))
        self.assertEqual(
            dict(STATE_MARK_GEOMETRY),
            {
                mark.attrib["data-state-mark"]: benchmark_state_mark_kind(mark)
                for mark in marks
            },
        )
        for mark in marks:
            state = mark.attrib["data-state-mark"]
            self.assertEqual(
                "inline" if state == "idle" else "none",
                mark.attrib.get("display"),
            )

        contrast_part = parts[EXPECTED_BENCHMARK_CONTRAST_PARTS[icon_id]]
        contrast_surfaces = [
            element
            for element in contrast_part.iter()
            if local_name(element.tag) in SVG_PAINTABLE_TAGS
            and element.attrib.get("fill")
            == "var(--icon-surface-contrast, #14213d)"
        ]
        self.assertEqual(1, len(contrast_surfaces))
        surface_bounds = benchmark_geometry_bounds(contrast_surfaces[0])
        for mark in marks:
            mark_bounds = benchmark_state_bounds(mark)
            with self.subTest(icon_id=icon_id, state=mark.attrib["data-state-mark"]):
                self.assertGreaterEqual(mark_bounds[0], surface_bounds[0])
                self.assertGreaterEqual(mark_bounds[1], surface_bounds[1])
                self.assertLessEqual(mark_bounds[2], surface_bounds[2])
                self.assertLessEqual(mark_bounds[3], surface_bounds[3])

        state_tokens = {
            "idle": "--icon-status-idle",
            "active": "--icon-status-active",
            "processing": "--icon-status-active",
            "success": "--icon-status-success",
            "warning": "--icon-status-warning",
            "error": "--icon-status-error",
        }
        for mark in marks:
            paints = " ".join(
                element.attrib.get(name, "")
                for element in mark.iter()
                if local_name(element.tag) in SVG_PAINTABLE_TAGS
                for name in ("fill", "stroke")
            )
            self.assertIn(state_tokens[mark.attrib["data-state-mark"]], paints)

        source = token_css()
        defaults = css_declarations(source, ":root")
        contrast_surface = defaults["--icon-surface-contrast"]
        for context in ("blue", "dark", "warm", "green"):
            resolved = dict(defaults)
            overrides = css_declarations(
                source,
                '[data-icon-theme="' + context + '"]',
            )
            self.assertNotIn("--icon-surface-contrast", overrides)
            resolved.update(overrides)
            for state, token in state_tokens.items():
                with self.subTest(icon_id=icon_id, context=context, state=state):
                    self.assertGreaterEqual(
                        contrast_ratio(resolved[token], contrast_surface),
                        3.0,
                    )

        paintables = [
            element
            for element in root.iter()
            if local_name(element.tag) in SVG_PAINTABLE_TAGS
        ]
        self.assertEqual(asset.metrics.paintable_elements, len(paintables))
        saw_roles = set()
        for element in paintables:
            bounds = benchmark_geometry_bounds(element)
            with self.subTest(icon_id=icon_id, geometry=element.attrib):
                self.assertGreaterEqual(bounds[0], 8.0)
                self.assertGreaterEqual(bounds[1], 8.0)
                self.assertLessEqual(bounds[2], 88.0)
                self.assertLessEqual(bounds[3], 88.0)
                stroke = element.attrib.get("stroke", "none").strip().lower()
                role = element.attrib.get("data-stroke-role")
                if stroke == "none":
                    self.assertIsNone(role)
                    continue
                self.assertIn(role, {"outer", "inner"})
                self.assertRegex(
                    element.attrib.get("stroke-width", ""),
                    r"^[0-9]+(?:\.[0-9]+)?$",
                )
                width = float(element.attrib["stroke-width"])
                if role == "outer":
                    self.assertGreaterEqual(width, 2.0)
                    self.assertLessEqual(width, 2.25)
                else:
                    self.assertGreaterEqual(width, 1.25)
                    self.assertLessEqual(width, 1.5)
                saw_roles.add(role)
        self.assertEqual({"outer", "inner"}, saw_roles)
        self.assertNotIn("non-scaling-stroke", asset.svg_source.lower())

        parents = benchmark_parent_map(root)
        neutral_area = 0.0
        accent_area = 0.0
        for element in paintables:
            if benchmark_is_hidden(element, parents):
                continue
            if local_name(element.tag) == "line":
                continue
            fill = element.attrib.get("fill", "black").strip().lower()
            if fill == "none":
                continue
            paints = " ".join(
                element.attrib.get(name, "") for name in ("fill", "stroke")
            )
            area = benchmark_filled_area(element)
            if "--icon-accent" in paints or "--icon-status-" in paints:
                accent_area += area
            else:
                neutral_area += area
        total_area = neutral_area + accent_area
        self.assertGreater(neutral_area, 0.0)
        self.assertGreater(accent_area, 0.0)
        self.assertGreaterEqual(neutral_area / total_area, 0.8)
        self.assertLessEqual(accent_area / total_area, 0.2)

    def test_benchmark_assets_have_exact_public_parts_and_manifest_contracts(self):
        for icon_id, expected_parts in EXPECTED_BENCHMARK_PARTS.items():
            with self.subTest(icon_id=icon_id):
                asset = load_asset(icon_id, allow_statuses={"visual-review"})
                self.assertEqual(expected_parts, set(asset.manifest.parts))
                self.assertEqual(expected_parts, set(asset.public_parts))
                self.assertEqual(
                    EXPECTED_BENCHMARK_PART_ORDER[icon_id],
                    asset.manifest.parts,
                )
                self.assertEqual(
                    EXPECTED_BENCHMARK_PART_ORDER[icon_id],
                    asset.public_parts,
                )
                self.assertEqual(
                    EXPECTED_BENCHMARK_PROTOTYPES[icon_id],
                    asset.manifest.structural_prototype,
                )
                self.assertEqual(
                    EXPECTED_BENCHMARK_ACTIONS[icon_id],
                    asset.manifest.actions,
                )
                self.assertEqual(
                    EXPECTED_BENCHMARK_ATTACHMENTS[icon_id],
                    {
                        name: (attachment.x, attachment.y)
                        for name, attachment in asset.manifest.attachments.items()
                    },
                )

    def test_curve_bounds_include_true_quadratic_and_cubic_extrema_plus_stroke(self):
        quadratic = ElementTree.fromstring(
            '<path d="M 10 10 Q 30 50 50 10" fill="none" '
            'stroke="#000" stroke-width="2"/>'
        )
        cubic = ElementTree.fromstring(
            '<path d="M 10 10 C 10 50 50 50 50 10" fill="none" '
            'stroke="#000" stroke-width="2"/>'
        )
        self.assertEqual((9.0, 9.0, 51.0, 31.0), benchmark_geometry_bounds(quadratic))
        self.assertEqual((9.0, 9.0, 51.0, 41.0), benchmark_geometry_bounds(cubic))

    def test_agent_obeys_shared_benchmark_machine_contract(self):
        self.assert_common_visual_contract("agent")

    def test_database_obeys_shared_benchmark_machine_contract(self):
        self.assert_common_visual_contract("database")

    def test_database_is_one_three_layer_storage_body_with_one_scan_ring_and_core(self):
        asset = self.load_benchmark("database")
        parts = self.parts_by_name(asset)
        self.assertEqual(("rect",), tuple(local_name(child.tag) for child in parts["shell"]))
        self.assertEqual(
            ("ellipse", "ellipse"),
            tuple(local_name(child.tag) for child in parts["top-ring"]),
        )
        for part_name in ("layer-top", "layer-middle", "layer-bottom"):
            with self.subTest(part=part_name):
                self.assertEqual(
                    ("path",),
                    tuple(local_name(child.tag) for child in parts[part_name]),
                )
                paints = " ".join(parts[part_name][0].attrib.get(name, "") for name in ("fill", "stroke"))
                self.assertNotIn("--icon-accent", paints)
                self.assertNotIn("--icon-status-", paints)
        self.assertEqual(("circle",), tuple(local_name(child.tag) for child in parts["core"]))
        self.assertEqual(
            "var(--icon-accent-secondary, #45c5bd)",
            parts["top-ring"][1].attrib.get("stroke"),
        )
        self.assertFalse(any("data-detail" in element.attrib for element in asset.root.iter()))
        self.assertNotRegex(
            asset.svg_source.lower(),
            r"\b(?:port|socket|connector|anchor|lamp|light)\b",
        )

    def test_api_obeys_shared_benchmark_machine_contract(self):
        self.assert_common_visual_contract("api")

    def test_api_interfaces_are_neutral_symmetric_and_physically_attached(self):
        asset = self.load_benchmark("api")
        parts = self.parts_by_name(asset)
        self.assertEqual(("rect",), tuple(local_name(child.tag) for child in parts["shell"]))
        self.assertEqual(("line",), tuple(local_name(child.tag) for child in parts["header"]))
        self.assertEqual(
            ("rect", "circle", "circle"),
            tuple(local_name(child.tag) for child in parts["processor"]),
        )
        shell = parts["shell"][0]
        input_interface = parts["input-interface"][0]
        output_interface = parts["output-interface"][0]
        self.assertEqual("rect", local_name(input_interface.tag))
        self.assertEqual("rect", local_name(output_interface.tag))
        for attribute in ("y", "width", "height", "rx"):
            self.assertEqual(
                input_interface.attrib[attribute],
                output_interface.attrib[attribute],
            )
        input_left = float(input_interface.attrib["x"])
        input_right = input_left + float(input_interface.attrib["width"])
        output_left = float(output_interface.attrib["x"])
        output_right = output_left + float(output_interface.attrib["width"])
        shell_left = float(shell.attrib["x"])
        shell_right = shell_left + float(shell.attrib["width"])
        self.assertLess(input_left, shell_left)
        self.assertGreater(input_right, shell_left)
        self.assertLess(output_left, shell_right)
        self.assertGreater(output_right, shell_right)
        self.assertAlmostEqual(96.0, input_left + output_right)
        self.assertAlmostEqual(96.0, input_right + output_left)
        self.assertEqual(
            "var(--icon-surface-secondary, #eef1f5)",
            input_interface.attrib.get("fill"),
        )
        self.assertEqual(
            input_interface.attrib.get("fill"),
            output_interface.attrib.get("fill"),
        )
        interface_paints = " ".join(
            element.attrib.get(name, "")
            for element in (input_interface, output_interface)
            for name in ("fill", "stroke")
        )
        self.assertNotIn("--icon-accent", interface_paints)
        self.assertNotIn("--icon-status-", interface_paints)
        self.assertFalse(any("data-detail" in element.attrib for element in asset.root.iter()))
        self.assertFalse(
            any(
                name in element.attrib
                for element in asset.root.iter()
                for name in ("marker-start", "marker-mid", "marker-end")
            )
        )
        self.assertNotRegex(asset.svg_source.lower(), r"\b(?:request|response|arrow)\b")

    def test_server_obeys_shared_benchmark_machine_contract(self):
        self.assert_common_visual_contract("server")

    def test_server_has_two_simple_trays_indicators_vents_and_lightweight_base(self):
        asset = self.load_benchmark("server")
        parts = self.parts_by_name(asset)
        self.assertEqual(("rect",), tuple(local_name(child.tag) for child in parts["shell"]))
        for part_name in ("tray-top", "tray-bottom"):
            with self.subTest(part=part_name):
                self.assertEqual(
                    ("rect",),
                    tuple(local_name(child.tag) for child in parts[part_name]),
                )
        self.assertEqual(
            ("circle", "circle"),
            tuple(local_name(child.tag) for child in parts["indicator-bottom"]),
        )
        for part_name in ("vent-top", "vent-bottom"):
            vents = list(parts[part_name])
            with self.subTest(part=part_name):
                self.assertEqual(("line", "line"), tuple(local_name(child.tag) for child in vents))
                self.assertTrue(
                    all(
                        float(vent.attrib["x2"]) - float(vent.attrib["x1"]) <= 20.0
                        for vent in vents
                    )
                )
        self.assertEqual(("rect",), tuple(local_name(child.tag) for child in parts["base"]))
        base = parts["base"][0]
        self.assertLessEqual(float(base.attrib["height"]), 6.0)
        self.assertLessEqual(float(base.attrib["width"]), 48.0)
        self.assertFalse(any("data-detail" in element.attrib for element in asset.root.iter()))
        self.assertNotRegex(
            asset.svg_source.lower(),
            r"\b(?:port|socket|connector|anchor|disk|fan|waveform|rack)\b",
        )

    def test_actor_storage_and_compute_benchmarks_have_no_port_like_private_details(self):
        for icon_id in ("agent", "database", "server"):
            with self.subTest(icon_id=icon_id):
                asset = self.load_benchmark(icon_id)
                self.assertNotRegex(
                    asset.svg_source.lower(),
                    r"\b(?:port|socket|connector|connection-anchor|scene-anchor)\b",
                )
                details = [
                    element.attrib["data-detail"]
                    for element in asset.root.iter()
                    if "data-detail" in element.attrib
                ]
                self.assertEqual(
                    ["ear-left", "ear-right"] if icon_id == "agent" else [],
                    details,
                )

    def test_four_benchmark_silhouette_signatures_are_distinct_at_48px(self):
        recognition_parts = {
            "agent": {"shell", "face-screen", "antenna", "core"},
            "database": {
                "shell",
                "top-ring",
                "layer-top",
                "layer-middle",
                "layer-bottom",
                "core",
            },
            "api": {
                "shell",
                "input-interface",
                "output-interface",
                "processor",
                "indicator-group",
            },
            "server": {"shell", "tray-top", "tray-bottom", "base"},
        }
        signatures = {}
        for icon_id, included_parts in recognition_parts.items():
            asset = self.load_benchmark(icon_id)
            parents = benchmark_parent_map(asset.root)
            geometry = []
            for element in asset.root.iter():
                if local_name(element.tag) not in SVG_PAINTABLE_TAGS:
                    continue
                if benchmark_public_part(element, parents) not in included_parts:
                    continue
                if benchmark_is_hidden(element, parents):
                    continue
                geometry.append(
                    (
                        local_name(element.tag),
                        tuple(
                            round(coordinate * 0.5, 4)
                            for coordinate in benchmark_geometry_bounds(element)
                        ),
                    )
                )
            self.assertTrue(geometry)
            signatures[icon_id] = tuple(geometry)
        self.assertEqual(4, len(set(signatures.values())))


class AgentBenchmarkAssetTest(unittest.TestCase):
    def load_agent(self):
        try:
            return load_asset("agent", allow_statuses={"visual-review"})
        except AssetValidationError as error:
            self.fail("canonical Agent must pass the asset gate: {0}".format(error))

    def test_agent_asset_matches_manifest_and_visual_contract(self):
        asset = self.load_agent()

        self.assertEqual(AGENT_PARTS, set(asset.manifest.parts))
        self.assertEqual(AGENT_PARTS, set(asset.public_parts))
        self.assertEqual(AGENT_PART_ORDER, asset.manifest.parts)
        self.assertEqual(AGENT_PART_ORDER, asset.public_parts)
        self.assertEqual("actor-character", asset.manifest.structural_prototype)
        self.assertEqual(
            {"enter", "receive", "process", "send"},
            set(asset.manifest.actions),
        )
        self.assertEqual(AGENT_STATES, asset.manifest.states)
        self.assertEqual("visual-review", asset.manifest.status)
        self.assertEqual(
            {"receive": (18, 48), "send": (78, 48), "status": (48, 74)},
            {
                name: (attachment.x, attachment.y)
                for name, attachment in asset.manifest.attachments.items()
            },
        )
        self.assertEqual(0, asset.metrics.forbidden_elements)
        self.assertLessEqual(asset.metrics.paintable_elements, 24)
        self.assertLessEqual(asset.metrics.raw_size_bytes, 12 * 1024)
        self.assertLessEqual(asset.metrics.gzip_size_bytes, 6 * 1024)

        root = asset.root
        self.assertEqual("img", root.attrib.get("role"))
        self.assertEqual("false", root.attrib.get("focusable"))
        self.assertTrue(root.attrib.get("aria-label", "").strip())
        self.assertEqual("agent", root.attrib.get("data-icon"))
        self.assertEqual("idle", root.attrib.get("data-icon-state"))

        catalog = json.loads(
            (ROOT / "assets" / "diagram-core" / "catalog.json").read_text(
                encoding="utf-8"
            )
        )
        entry = next(icon for icon in catalog["icons"] if icon["id"] == "agent")
        manifest_values = {
            "id": asset.manifest.icon_id,
            "category": asset.manifest.category,
            "semantic_kind": asset.manifest.semantic_kind,
            "structural_prototype": asset.manifest.structural_prototype,
            "parts": list(asset.manifest.parts),
            "supported_states": list(asset.manifest.states),
            "supported_actions": list(asset.manifest.actions),
            "status": asset.manifest.status,
            "asset_revision": asset.manifest.asset_revision,
        }
        self.assertEqual(
            {field: entry[field] for field in manifest_values},
            manifest_values,
        )

    def test_agent_state_marks_have_distinct_geometry_and_idle_standalone_visibility(self):
        asset = self.load_agent()
        indicators = [
            element
            for element in asset.root.iter()
            if element.attrib.get("data-part") == "indicator"
        ]
        self.assertEqual(1, len(indicators))
        indicator = indicators[0]
        marks = [
            element
            for element in asset.root.iter()
            if "data-state-mark" in element.attrib
        ]
        self.assertEqual(set(AGENT_STATES), {mark.attrib["data-state-mark"] for mark in marks})
        self.assertEqual(6, len(marks))
        self.assertTrue(set(marks).issubset(set(indicator.iter())))

        signatures = {
            mark.attrib["data-state-mark"]: agent_state_geometry_signature(mark)
            for mark in marks
        }
        self.assertEqual(6, len(set(signatures.values())))
        for mark in marks:
            state = mark.attrib["data-state-mark"]
            self.assertEqual("inline" if state == "idle" else "none", mark.attrib.get("display"))

    def test_agent_core_and_state_footprints_are_frozen_for_48px_review(self):
        asset = self.load_agent()
        core = next(
            element
            for element in asset.root.iter()
            if element.attrib.get("data-part") == "core"
        )
        core_circles = [
            element for element in core if local_name(element.tag) == "circle"
        ]
        self.assertEqual(2, len(core_circles))
        outer_core, recessed_core = core_circles
        self.assertEqual(9.6, float(outer_core.attrib["r"]))
        self.assertEqual(6.7, float(recessed_core.attrib["r"]))

        expected_bounds = {
            "idle": (45.8, 66.8, 50.2, 71.2),
            "active": (43.5125, 64.5125, 52.4875, 73.4875),
            "processing": (43.7125, 64.5125, 52.2875, 73.4875),
            "success": (43.2125, 65.5125, 52.7875, 72.6875),
            "warning": (43.3125, 64.7125, 52.6875, 72.8875),
            "error": (43.8125, 64.8125, 52.1875, 73.1875),
        }
        marks = {
            element.attrib["data-state-mark"]: element
            for element in asset.root.iter()
            if "data-state-mark" in element.attrib
        }
        measured = {}
        for state in AGENT_STATES:
            bounds = agent_state_bounds(marks[state])
            measured[state] = bounds
            with self.subTest(state=state):
                for actual, expected in zip(bounds, expected_bounds[state]):
                    self.assertAlmostEqual(expected, actual, places=4)
                radial_extent = max(
                    agent_radial_extent(element, 48, 69)
                    for element in marks[state].iter()
                    if local_name(element.tag) in SVG_PAINTABLE_TAGS
                )
                self.assertGreaterEqual(
                    float(recessed_core.attrib["r"]) - radial_extent,
                    0.75,
                )

        footprints = {
            state: (bounds[2] - bounds[0], bounds[3] - bounds[1])
            for state, bounds in measured.items()
        }
        self.assertGreaterEqual(max(footprints["processing"]), 8.5)
        self.assertGreaterEqual(max(footprints["success"]), 9.5)
        self.assertGreaterEqual(max(footprints["error"]), 8.25)
        self.assertLess(
            abs(footprints["active"][0] - footprints["warning"][0]),
            0.5,
        )
        self.assertLess(
            max(footprints["idle"]),
            min(footprints["active"]) * 0.6,
        )

    def test_agent_face_and_state_marks_keep_three_to_one_contrast_in_every_context(self):
        asset = self.load_agent()
        source = token_css()
        defaults = css_declarations(source, ":root")
        self.assertEqual(
            "#14213d",
            defaults.get("--icon-surface-contrast"),
        )
        face_screen = next(
            element
            for element in asset.root.iter()
            if element.attrib.get("data-part") == "face-screen"
        )[0]
        core = next(
            element
            for element in asset.root.iter()
            if element.attrib.get("data-part") == "core"
        )
        self.assertEqual(
            "var(--icon-surface-contrast, #14213d)",
            face_screen.attrib["fill"],
        )
        self.assertEqual(
            "var(--icon-surface-contrast, #14213d)",
            core[1].attrib["fill"],
        )
        for part_name in ("eye-left", "eye-right"):
            part = next(
                element
                for element in asset.root.iter()
                if element.attrib.get("data-part") == part_name
            )
            self.assertEqual(
                "var(--icon-accent-secondary, #45c5bd)",
                part[0].attrib["fill"],
            )
        mouth = next(
            element
            for element in asset.root.iter()
            if element.attrib.get("data-part") == "mouth"
        )
        self.assertEqual(
            "var(--icon-accent-secondary, #45c5bd)",
            mouth[0].attrib["stroke"],
        )

        state_tokens = {
            "idle": "--icon-status-idle",
            "active": "--icon-status-active",
            "processing": "--icon-status-active",
            "success": "--icon-status-success",
            "warning": "--icon-status-warning",
            "error": "--icon-status-error",
        }
        contrast_surface = defaults["--icon-surface-contrast"]
        for context in ("blue", "dark", "warm", "green"):
            overrides = css_declarations(
                source,
                '[data-icon-theme="' + context + '"]',
            )
            self.assertNotIn("--icon-surface-contrast", overrides)
            resolved = dict(defaults)
            resolved.update(overrides)
            with self.subTest(context=context, part="face-details"):
                self.assertGreaterEqual(
                    contrast_ratio(
                        resolved["--icon-accent-secondary"],
                        contrast_surface,
                    ),
                    3.0,
                )
            for state, token in state_tokens.items():
                with self.subTest(context=context, state=state):
                    self.assertGreaterEqual(
                        contrast_ratio(resolved[token], contrast_surface),
                        3.0,
                    )

    def test_agent_geometry_stays_in_safe_zone_and_strokes_are_role_bounded(self):
        asset = self.load_agent()
        paintables = [
            element
            for element in asset.root.iter()
            if local_name(element.tag) in SVG_PAINTABLE_TAGS
        ]
        self.assertEqual(asset.metrics.paintable_elements, len(paintables))
        self.assertFalse(
            any(local_name(element.tag) == "style" for element in asset.root.iter())
        )
        self.assertFalse(any("style" in element.attrib for element in asset.root.iter()))
        self.assertFalse(any("transform" in element.attrib for element in asset.root.iter()))

        saw_roles = set()
        for element in paintables:
            bounds = agent_geometry_bounds(element)
            with self.subTest(tag=local_name(element.tag), geometry=element.attrib):
                self.assertGreaterEqual(min(bounds[0], bounds[1]), 8.0)
                self.assertLessEqual(max(bounds[2], bounds[3]), 88.0)

                stroke = element.attrib.get("stroke", "none").strip().lower()
                role = element.attrib.get("data-stroke-role")
                if stroke == "none":
                    self.assertIsNone(role)
                    continue
                self.assertIn(role, {"outer", "inner"})
                self.assertRegex(element.attrib.get("stroke-width", ""), r"^[0-9]+(?:\.[0-9]+)?$")
                width = float(element.attrib["stroke-width"])
                if role == "outer":
                    self.assertGreaterEqual(width, 2.0)
                    self.assertLessEqual(width, 2.25)
                else:
                    self.assertGreaterEqual(width, 1.25)
                    self.assertLessEqual(width, 1.5)
                saw_roles.add(role)
        self.assertEqual({"outer", "inner"}, saw_roles)
        self.assertNotIn("non-scaling-stroke", asset.svg_source.lower())

    def test_agent_shell_has_exactly_two_private_symmetric_ear_caps(self):
        asset = self.load_agent()
        shell = next(
            element
            for element in asset.root.iter()
            if element.attrib.get("data-part") == "shell"
        )
        face_screen = next(
            element
            for element in asset.root.iter()
            if element.attrib.get("data-part") == "face-screen"
        )[0]
        details = [
            element
            for element in asset.root.iter()
            if "data-detail" in element.attrib
        ]
        self.assertEqual(
            {"ear-left", "ear-right"},
            {element.attrib["data-detail"] for element in details},
        )
        self.assertEqual(2, len(details))
        self.assertTrue(all("data-part" not in element.attrib for element in details))
        self.assertTrue(all(local_name(element.tag) == "rect" for element in details))

        shell_rect = next(
            element
            for element in shell
            if local_name(element.tag) == "rect" and "data-detail" not in element.attrib
        )
        shell_children = list(shell)
        self.assertTrue(all(element in shell_children for element in details))
        self.assertTrue(
            all(
                shell_children.index(element) < shell_children.index(shell_rect)
                for element in details
            )
        )

        ears = {element.attrib["data-detail"]: element for element in details}
        left = ears["ear-left"]
        right = ears["ear-right"]
        for attribute in ("y", "width", "height", "rx"):
            self.assertEqual(left.attrib[attribute], right.attrib[attribute])
        left_bounds = agent_geometry_bounds(left)
        right_bounds = agent_geometry_bounds(right)
        self.assertAlmostEqual(96.0, left_bounds[0] + right_bounds[2])
        self.assertAlmostEqual(96.0, left_bounds[2] + right_bounds[0])
        self.assertAlmostEqual(left_bounds[1], right_bounds[1])
        self.assertAlmostEqual(left_bounds[3], right_bounds[3])

        shell_left = float(shell_rect.attrib["x"])
        shell_right = shell_left + float(shell_rect.attrib["width"])
        left_x = float(left.attrib["x"])
        left_right = left_x + float(left.attrib["width"])
        right_x = float(right.attrib["x"])
        right_right = right_x + float(right.attrib["width"])
        self.assertLess(left_x, shell_left)
        self.assertGreater(left_right, shell_left)
        self.assertLess(right_x, shell_right)
        self.assertGreater(right_right, shell_right)
        self.assertLessEqual(shell_left - left_x, 7.0)
        self.assertLessEqual(right_right - shell_right, 7.0)

        face_top = float(face_screen.attrib["y"])
        face_bottom = face_top + float(face_screen.attrib["height"])
        face_center = (face_top + face_bottom) / 2.0
        ear_top = float(left.attrib["y"])
        ear_bottom = ear_top + float(left.attrib["height"])
        self.assertGreater(ear_top, face_top)
        self.assertLess(ear_bottom, face_bottom)
        self.assertAlmostEqual(face_center, (ear_top + ear_bottom) / 2.0, delta=1.0)

        for ear in details:
            self.assertEqual("var(--icon-accent, #7c5ce7)", ear.attrib.get("fill"))
            self.assertEqual("var(--icon-stroke, #14213d)", ear.attrib.get("stroke"))
            self.assertEqual("2.125", ear.attrib.get("stroke-width"))
            self.assertEqual("outer", ear.attrib.get("data-stroke-role"))

    def test_agent_keeps_accent_weight_small_and_avoids_forbidden_pieces(self):
        asset = self.load_agent()
        parents = {
            child: parent
            for parent in asset.root.iter()
            for child in parent
        }

        def ancestors(element):
            while element in parents:
                element = parents[element]
                yield element

        def public_part(element):
            for candidate in (element, *ancestors(element)):
                if "data-part" in candidate.attrib:
                    return candidate.attrib["data-part"]
            return None

        accent_parts = {
            "eye-left",
            "eye-right",
            "mouth",
            "antenna",
            "core",
            "indicator",
        }
        neutral_area = 0.0
        accent_area = 0.0
        for element in asset.root.iter():
            if local_name(element.tag) not in SVG_PAINTABLE_TAGS:
                continue
            paints = " ".join(
                element.attrib.get(name, "") for name in ("fill", "stroke")
            )
            is_accent = "--icon-accent" in paints or "--icon-status-" in paints
            if is_accent:
                part = public_part(element)
                if part == "shell":
                    self.assertIn(
                        element.attrib.get("data-detail"),
                        {"ear-left", "ear-right"},
                    )
                else:
                    self.assertIn(part, accent_parts)
            if any(candidate.attrib.get("display") == "none" for candidate in (element, *ancestors(element))):
                continue
            if local_name(element.tag) == "line":
                continue
            fill = element.attrib.get("fill", "black").strip().lower()
            if fill == "none":
                continue
            area = agent_filled_area(element)
            if is_accent:
                accent_area += area
            else:
                neutral_area += area

        total_area = neutral_area + accent_area
        self.assertGreater(neutral_area, 0)
        self.assertGreater(accent_area, 0)
        self.assertGreaterEqual(neutral_area / total_area, 0.8)
        self.assertLessEqual(accent_area / total_area, 0.2)

        self.assertFalse(any("id" in element.attrib for element in asset.root.iter()))
        self.assertNotRegex(
            asset.svg_source.lower(),
            r"\b(?:port|hand|joint|socket|effect|connection-anchor)\b",
        )
        self.assertNotRegex(asset.svg_source.lower(), r"data-(?:connection-)?anchor")


class DiagramCoreTokenTest(unittest.TestCase):
    def test_token_context_parser_applies_later_matching_rules(self):
        source = token_css() + """
[data-icon-theme="dark"] {
  --icon-stroke: #202838;
  --icon-surface-main: #202838;
}
"""

        _, contexts = diagram_core_tokens.token_contexts(source)

        self.assertEqual("#202838", contexts["dark"]["--icon-stroke"])
        self.assertEqual("#202838", contexts["dark"]["--icon-surface-main"])

    def test_token_context_parser_applies_root_and_context_rules_in_source_order(self):
        source = token_css() + """
:root {
  --icon-stroke: #202838;
}
"""

        defaults, contexts = diagram_core_tokens.token_contexts(source)

        self.assertEqual("#202838", defaults["--icon-stroke"])
        self.assertEqual("#202838", contexts["dark"]["--icon-stroke"])

    def test_token_context_parser_rejects_non_exact_context_selectors(self):
        selectors = (
            '[data-icon-theme = "dark"]',
            '[data-icon-theme="dark"], .other',
        )
        for selector in selectors:
            with self.subTest(selector=selector):
                source = token_css() + """
{0} {{
  --icon-stroke: #202838;
}}
""".format(selector)
                with self.assertRaisesRegex(ValueError, "exact top-level"):
                    diagram_core_tokens.token_contexts(source)

    def test_token_context_parser_rejects_conditional_context_rules(self):
        source = token_css() + """
@media (min-width: 1px) {
  [data-icon-theme="dark"] {
    --icon-stroke: #202838;
  }
}
"""

        with self.assertRaisesRegex(ValueError, "top-level"):
            diagram_core_tokens.token_contexts(source)

    def test_token_context_parser_rejects_mentions_in_unhandled_rules(self):
        rules = (
            """@scope ([data-icon-theme="dark"]) {
  :scope {
    --icon-stroke: #202838;
    --icon-surface-main: #202838;
  }
}
""",
            """.scope {
  [data-icon-theme="dark"] {
    --icon-stroke: #202838;
    --icon-surface-main: #202838;
  }
}
""",
        )
        for rule in rules:
            with self.subTest(rule=rule.splitlines()[0]):
                with self.assertRaisesRegex(ValueError, "top-level"):
                    diagram_core_tokens.token_contexts(token_css() + rule)

    def test_token_context_parser_rejects_invalid_non_contrast_color(self):
        source = token_css().replace(
            "--icon-accent: #7c5ce7;",
            "--icon-accent: not-a-color;",
            1,
        )

        with self.assertRaisesRegex(
            ValueError,
            "expected #rgb, #rrggbb, or opaque rgb",
        ):
            diagram_core_tokens.token_contexts(source)

    def test_token_css_defines_approved_defaults_and_four_review_contexts(self):
        source = token_css()

        self.assertTrue(
            (
                REQUIRED_ICON_TOKENS
                | set(ASSET_LOCAL_TOKEN_DEFAULTS)
            ).issubset(declared_tokens(source))
        )
        root_tokens = css_declarations(source, ":root")
        for token, value in (
            APPROVED_ICON_DEFAULTS | ASSET_LOCAL_TOKEN_DEFAULTS
        ).items():
            with self.subTest(token=token):
                self.assertEqual(value, root_tokens[token])

        expected_contexts = {
            "blue": {
                "--icon-accent": "#4f7cff",
                "--icon-accent-secondary": "#45c5d8",
            },
            "dark": {
                "--icon-surface-main": "#202838",
                "--icon-surface-secondary": "#2c3749",
                "--icon-surface-recessed": "#151c28",
                "--icon-stroke": "#d6deeb",
                "--icon-detail": "#8fa0b8",
                "--icon-accent": "#65d8ff",
                "--icon-accent-secondary": "#9f85ff",
            },
            "warm": {
                "--icon-surface-main": "#fff8eb",
                "--icon-surface-secondary": "#eee4d1",
                "--icon-surface-recessed": "#ded0b8",
                "--icon-stroke": "#40372f",
                "--icon-detail": "#8a796a",
                "--icon-accent": "#e38843",
                "--icon-accent-secondary": "#d5af4b",
            },
            "green": {
                "--icon-accent": "#38a967",
                "--icon-accent-secondary": "#59c6a7",
            },
        }
        for context, expected in expected_contexts.items():
            selector = '[data-icon-theme="' + context + '"]'
            with self.subTest(context=context):
                self.assertEqual(expected, css_declarations(source, selector))

    def test_static_state_selectors_are_nearest_scoped_and_geometry_distinct(self):
        source = token_css()

        self.assertEqual(
            {"display": "none"},
            css_declarations(source, "[data-state-mark]"),
        )
        pairs = state_scope_pairs(source)
        expected_pairs = [(state, state) for state, _ in STATE_MARK_GEOMETRY]
        self.assertEqual(expected_pairs, pairs)
        for state, geometry in STATE_MARK_GEOMETRY:
            with self.subTest(state=state):
                selector = (
                    ':scope[data-icon-state="'
                    + state
                    + '"] [data-state-mark="'
                    + state
                    + '"]'
                )
                self.assertEqual(
                    {"display": "inline"},
                    css_declarations(source, selector),
                )
                self.assertIn(state + " = " + geometry, source)
        self.assertNotIn("::before", source)
        self.assertNotIn("::after", source)
        self.assertNotIn("content:", source)

        # These mutations reproduce the two leak shapes the contract forbids:
        # an outer state crossing a nested icon root, and an unscoped rule that
        # can affect another icon subtree. The static guard must reject both.
        without_nested_boundary = source.replace(
            " to ([data-icon-state])",
            "",
            1,
        )
        unscoped_reveal = source + (
            '\n[data-icon-state="error"] [data-state-mark="error"] {'
            " display: inline; }\n"
        )
        for leaky_source in (without_nested_boundary, unscoped_reveal):
            with self.subTest(leaky_source=leaky_source[-100:]):
                with self.assertRaises(AssertionError):
                    state_scope_pairs(leaky_source)

    def test_review_and_reduced_motion_disable_transitions_and_animations(self):
        source = token_css()

        self.assertIn('[data-icon-review="true"]', source)
        self.assertIn("@media (prefers-reduced-motion: reduce)", source)
        self.assertGreaterEqual(source.count("animation: none !important;"), 2)
        self.assertGreaterEqual(source.count("transition: none !important;"), 2)

    def test_accent_off_neutralizes_accents_without_hiding_structure_or_state(self):
        declarations = css_declarations(token_css(), '[data-icon-accent="off"]')

        self.assertEqual("var(--icon-stroke)", declarations["--icon-accent"])
        self.assertEqual(
            "var(--icon-detail)",
            declarations["--icon-accent-secondary"],
        )
        for forbidden in ("display", "visibility", "opacity"):
            self.assertNotIn(forbidden, declarations)

    def test_style_mapping_uses_existing_canvas_role_and_title_tokens(self):
        style = load_style(ROOT / "styles" / "deep-tech.json")

        mapped = icon_tokens_for_style(style, "agent")

        self.assertEqual(style["roles"]["agent"]["fill"], mapped["--icon-surface-main"])
        self.assertEqual(style["canvas"]["background"], mapped["--icon-surface-secondary"])
        self.assertEqual(style["canvas"]["grid"], mapped["--icon-surface-recessed"])
        self.assertEqual(style["canvas"]["text"], mapped["--icon-stroke"])
        self.assertEqual(style["canvas"]["muted"], mapped["--icon-detail"])
        self.assertEqual(style["roles"]["agent"]["stroke"], mapped["--icon-accent"])
        self.assertEqual(style["title"]["accent"], mapped["--icon-accent-secondary"])
        self.assertEqual(APPROVED_ICON_DEFAULTS["--icon-status-idle"], mapped["--icon-status-idle"])

    def test_all_bundled_styles_return_complete_contrasting_mappings(self):
        style_paths = sorted((ROOT / "styles").glob("*.json"))
        style_paths = [path for path in style_paths if path.name != "catalog.json"]

        self.assertGreater(len(style_paths), 0)
        for style_path in style_paths:
            style = load_style(style_path)
            for role in style["roles"]:
                with self.subTest(style=style_path.name, role=role):
                    mapped = icon_tokens_for_style(style, role)
                    self.assertEqual(REQUIRED_ICON_TOKENS, set(mapped))
                    self.assertGreaterEqual(
                        contrast_ratio(
                            mapped["--icon-stroke"],
                            mapped["--icon-surface-main"],
                        ),
                        3.0,
                    )

    def test_missing_and_unknown_roles_fall_back_to_neutral(self):
        style = load_style(ROOT / "styles" / "deep-tech.json")
        expected = style["roles"]["neutral"]
        without_agent = copy.deepcopy(style)
        del without_agent["roles"]["agent"]

        for label, candidate, role in (
            ("none", style, None),
            ("unknown", style, "not-a-role"),
            ("missing", without_agent, "agent"),
        ):
            with self.subTest(label=label):
                mapped = icon_tokens_for_style(candidate, role)
                self.assertEqual(expected["fill"], mapped["--icon-surface-main"])
                self.assertEqual(expected["stroke"], mapped["--icon-accent"])

    def test_explicit_status_overrides_are_copied_and_mapping_is_immutable(self):
        style = load_style(ROOT / "styles" / "deep-tech.json")
        overrides = {
            "--icon-status-warning": "rgb(120, 80, 0)",
            "--icon-status-error": "#123",
        }
        style["icon_tokens"] = overrides

        mapped = icon_tokens_for_style(style, "agent")
        overrides["--icon-status-warning"] = "#ffffff"

        self.assertEqual("rgb(120, 80, 0)", mapped["--icon-status-warning"])
        self.assertEqual("#123", mapped["--icon-status-error"])
        self.assertEqual(
            APPROVED_ICON_DEFAULTS["--icon-status-success"],
            mapped["--icon-status-success"],
        )
        with self.assertRaises(TypeError):
            mapped["--icon-status-error"] = "#ffffff"

        fresh = icon_tokens_for_style(load_style(), "agent")
        self.assertEqual(
            APPROVED_ICON_DEFAULTS["--icon-status-warning"],
            fresh["--icon-status-warning"],
        )

    def test_invalid_override_keys_and_unknown_color_formats_fail_closed(self):
        style = load_style()
        cases = (
            {"--icon-accent": "#ffffff"},
            {"--icon-status-error": "rgba(0, 0, 0, 0.5)"},
            {"--icon-status-error": "not-a-color"},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                candidate = copy.deepcopy(style)
                candidate["icon_tokens"] = overrides
                with self.assertRaises(ValueError):
                    icon_tokens_for_style(candidate, "agent")

    def test_relative_luminance_accepts_opaque_hex_and_rgb_only(self):
        self.assertEqual(0.0, relative_luminance("#000"))
        self.assertEqual(1.0, relative_luminance("#FFFFFF"))
        self.assertEqual(0.0, relative_luminance("rgb(0, 0, 0)"))
        self.assertEqual(1.0, relative_luminance("rgb(255 255 255)"))

        unsupported = (
            "#00000080",
            "rgba(0, 0, 0, 0.5)",
            "rgb(0 0 0 / 50%)",
            "rgb(256, 0, 0)",
            "rgb(0.5, 0, 0)",
            "hsl(0 0% 0%)",
            "black",
        )
        for color in unsupported:
            with self.subTest(color=color):
                with self.assertRaises(ValueError):
                    relative_luminance(color)

    def test_contrast_uses_wcag_luminance_and_honors_three_to_one_boundary(self):
        self.assertEqual(21.0, contrast_ratio("#000000", "#ffffff"))
        self.assertAlmostEqual(
            contrast_ratio("#777777", "#ffffff"),
            4.478089453577214,
        )
        self.assertGreaterEqual(contrast_ratio("#949494", "#ffffff"), 3.0)
        self.assertLess(contrast_ratio("#959595", "#ffffff"), 3.0)
        self.assertEqual(
            contrast_ratio("#14213d", "#fffaf2"),
            contrast_ratio("#fffaf2", "#14213d"),
        )

    def test_review_contexts_keep_structural_boundary_at_three_to_one(self):
        source = token_css()
        defaults = css_declarations(source, ":root")

        for context in ("blue", "dark", "warm", "green"):
            overrides = css_declarations(
                source,
                '[data-icon-theme="' + context + '"]',
            )
            stroke = overrides.get("--icon-stroke", defaults["--icon-stroke"])
            surface = overrides.get(
                "--icon-surface-main",
                defaults["--icon-surface-main"],
            )
            with self.subTest(context=context):
                self.assertGreaterEqual(contrast_ratio(stroke, surface), 3.0)


class DiagramCoreAssetValidatorCLITest(unittest.TestCase):
    def test_review_mode_reports_clean_four_icon_set(self):
        result = run_asset_validator("--review", "--json")

        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(56, report["catalog"])
        self.assertEqual(13, report["legacy_valid"])
        self.assertEqual(4, report["visual_review"])
        self.assertEqual(4, report["svg"])
        self.assertEqual(4, report["manifests"])
        self.assertEqual(0, report["errors"])

    def test_review_report_includes_real_metrics_and_contrast_checks(self):
        result = run_asset_validator("--review", "--json")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(0, report["approved"])
        self.assertEqual(52, report["planned"])
        self.assertEqual(
            {"agent": 17, "api": 15, "database": 15, "server": 18},
            report["paintable_elements_by_icon"],
        )
        self.assertEqual(
            {"agent": 3347, "api": 3061, "database": 3087, "server": 3538},
            report["raw_bytes_by_icon"],
        )
        self.assertEqual(
            {"agent": 885, "api": 826, "database": 813, "server": 846},
            report["gzip_bytes_by_icon"],
        )
        self.assertGreater(report["contrast_checks"], 0)
        self.assertEqual(0, report["warnings"])

    def test_review_rejects_later_context_override_with_low_contrast(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_root = copy_canonical_asset_root(temp_dir)
            tokens_path = asset_root / "tokens.css"
            tokens_path.write_text(
                tokens_path.read_text(encoding="utf-8")
                + """
[data-icon-theme="dark"] {
  --icon-stroke: #202838;
  --icon-surface-main: #202838;
}
""",
                encoding="utf-8",
            )

            result = run_asset_validator(
                "--review", "--json", "--asset-root", str(asset_root)
            )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        report = json.loads(result.stdout)
        self.assertGreater(report["errors"], 0)
        self.assertIn("structural contrast", "\n".join(report["error_details"]))

    def test_review_applies_later_root_override_in_static_cascade_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_root = copy_canonical_asset_root(temp_dir)
            tokens_path = asset_root / "tokens.css"
            tokens_path.write_text(
                tokens_path.read_text(encoding="utf-8")
                + """
:root {
  --icon-stroke: #202838;
}
""",
                encoding="utf-8",
            )

            result = run_asset_validator(
                "--review", "--json", "--asset-root", str(asset_root)
            )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        report = json.loads(result.stdout)
        self.assertIn("structural contrast", "\n".join(report["error_details"]))

    def test_review_rejects_context_mentions_in_unhandled_rules(self):
        rules = (
            """@scope ([data-icon-theme="dark"]) {
  :scope {
    --icon-stroke: #202838;
    --icon-surface-main: #202838;
  }
}
""",
            """.scope {
  [data-icon-theme="dark"] {
    --icon-stroke: #202838;
    --icon-surface-main: #202838;
  }
}
""",
        )
        for rule in rules:
            with self.subTest(rule=rule.splitlines()[0]):
                with tempfile.TemporaryDirectory() as temp_dir:
                    asset_root = copy_canonical_asset_root(temp_dir)
                    tokens_path = asset_root / "tokens.css"
                    tokens_path.write_text(
                        tokens_path.read_text(encoding="utf-8") + rule,
                        encoding="utf-8",
                    )

                    result = run_asset_validator(
                        "--review", "--json", "--asset-root", str(asset_root)
                    )

                    self.assertEqual(1, result.returncode)
                    self.assertEqual("", result.stderr)
                    report = json.loads(result.stdout)
                    self.assertIn(
                        "top-level",
                        "\n".join(report["error_details"]),
                    )

    def test_review_rejects_invalid_non_contrast_token_color(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_root = copy_canonical_asset_root(temp_dir)
            tokens_path = asset_root / "tokens.css"
            tokens_path.write_text(
                tokens_path.read_text(encoding="utf-8").replace(
                    "--icon-accent: #7c5ce7;",
                    "--icon-accent: not-a-color;",
                    1,
                ),
                encoding="utf-8",
            )

            result = run_asset_validator(
                "--review", "--json", "--asset-root", str(asset_root)
            )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        report = json.loads(result.stdout)
        self.assertIn(
            "expected #rgb, #rrggbb, or opaque rgb",
            "\n".join(report["error_details"]),
        )

    def test_strict_mode_fails_cleanly_until_all_benchmarks_are_approved(self):
        result = run_asset_validator("--strict", "--json")

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(0, report["approved"])
        self.assertEqual(4, report["visual_review"])
        self.assertGreater(report["errors"], 0)
        self.assertIn("approved", "\n".join(report["error_details"]))

    def test_human_summary_matches_json_counts(self):
        json_result = run_asset_validator("--review", "--json")
        human_result = run_asset_validator("--review")

        self.assertEqual(0, json_result.returncode, json_result.stderr)
        self.assertEqual(0, human_result.returncode, human_result.stderr)
        self.assertEqual("", human_result.stderr)
        self.assertEqual(
            "catalog=56 legacy_valid=13 approved=0 visual_review=4 "
            "planned=52 svg=4 manifests=4 "
            'paintable_elements_by_icon={"agent":17,"api":15,"database":15,"server":18} '
            'raw_bytes_by_icon={"agent":3347,"api":3061,"database":3087,"server":3538} '
            'gzip_bytes_by_icon={"agent":885,"api":826,"database":813,"server":846} '
            "contrast_checks=28 errors=0 warnings=0\n",
            human_result.stdout,
        )
        json_report = json.loads(json_result.stdout)
        human_report = {}
        for field in human_result.stdout.split():
            key, value = field.split("=", 1)
            human_report[key] = (
                json.loads(value) if key.endswith("_by_icon") else int(value)
            )
        self.assertEqual(json_report, human_report)

    def test_review_rejects_extra_svg_and_reports_actual_inventory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_root = copy_canonical_asset_root(temp_dir)
            shutil.copyfile(
                asset_root / "icons" / "agent.svg",
                asset_root / "icons" / "extra.svg",
            )

            result = run_asset_validator(
                "--review", "--json", "--asset-root", str(asset_root)
            )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(5, report["svg"])
        self.assertGreater(report["errors"], 0)
        self.assertIn("extra.svg", "\n".join(report["error_details"]))

    def test_review_rejects_missing_manifest_and_reports_actual_inventory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_root = copy_canonical_asset_root(temp_dir)
            (asset_root / "manifests" / "server.json").unlink()

            result = run_asset_validator(
                "--review", "--json", "--asset-root", str(asset_root)
            )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(3, report["manifests"])
        self.assertIn("server.json", "\n".join(report["error_details"]))

    def test_review_rejects_asset_file_symlinks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_root = copy_canonical_asset_root(temp_dir)
            external_svg = Path(temp_dir) / "external-agent.svg"
            shutil.copyfile(asset_root / "icons" / "agent.svg", external_svg)
            (asset_root / "icons" / "agent.svg").unlink()
            (asset_root / "icons" / "agent.svg").symlink_to(external_svg)

            result = run_asset_validator(
                "--review", "--json", "--asset-root", str(asset_root)
            )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        report = json.loads(result.stdout)
        self.assertIn("symbolic link", "\n".join(report["error_details"]))

    def test_review_rejects_symlinked_root_directories_and_key_files(self):
        cases = ("asset-root", "icons", "manifests", "catalog.json", "tokens.css")
        for target in cases:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                asset_root = copy_canonical_asset_root(temp_dir)
                cli_root = asset_root
                if target == "asset-root":
                    cli_root = temp_path / "linked-diagram-core"
                    cli_root.symlink_to(asset_root, target_is_directory=True)
                elif target in {"icons", "manifests"}:
                    original = asset_root / target
                    external = temp_path / ("external-" + target)
                    shutil.copytree(original, external)
                    shutil.rmtree(original)
                    original.symlink_to(external, target_is_directory=True)
                else:
                    original = asset_root / target
                    external = temp_path / ("external-" + target)
                    shutil.copyfile(original, external)
                    original.unlink()
                    original.symlink_to(external)

                result = run_asset_validator(
                    "--review", "--json", "--asset-root", str(cli_root)
                )

                self.assertEqual(1, result.returncode)
                self.assertEqual("", result.stderr)
                report = json.loads(result.stdout)
                self.assertGreater(report["errors"], 0)
                self.assertIn("symbolic link", "\n".join(report["error_details"]))

    def test_review_allows_a_symlinked_ancestor_of_the_real_asset_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            real_parent = temp_path / "real-parent"
            real_parent.mkdir()
            asset_root = real_parent / "diagram-core"
            shutil.copytree(ROOT / "assets" / "diagram-core", asset_root)
            linked_parent = temp_path / "linked-parent"
            linked_parent.symlink_to(real_parent, target_is_directory=True)
            cli_root = linked_parent / "diagram-core"
            self.assertFalse(cli_root.is_symlink())

            result = run_asset_validator(
                "--review", "--json", "--asset-root", str(cli_root)
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(0, json.loads(result.stdout)["errors"])

    def test_malformed_catalog_returns_structured_library_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_root = copy_canonical_asset_root(temp_dir)
            (asset_root / "catalog.json").write_text("{", encoding="utf-8")

            result = run_asset_validator(
                "--review", "--json", "--asset-root", str(asset_root)
            )
            human_result = run_asset_validator(
                "--review", "--asset-root", str(asset_root)
            )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        report = json.loads(result.stdout)
        self.assertGreater(report["errors"], 0)
        self.assertIn(
            "invalid JSON at line 1, column 2",
            "\n".join(report["error_details"]),
        )
        self.assertEqual(1, human_result.returncode)
        self.assertEqual(
            "catalog=0 legacy_valid=0 approved=0 visual_review=0 "
            "planned=0 svg=4 manifests=4 paintable_elements_by_icon={} "
            "raw_bytes_by_icon={} gzip_bytes_by_icon={} contrast_checks=0 "
            "errors=1 warnings=0\n",
            human_result.stdout,
        )
        self.assertIn("invalid JSON at line 1, column 2", human_result.stderr)
        self.assertNotIn("Traceback", human_result.stderr)

    def test_malformed_asset_classes_preserve_precise_library_errors(self):
        cases = (
            (
                "manifest",
                lambda root: mutate_json_file(
                    root / "manifests" / "agent.json",
                    lambda value: value.pop("parts"),
                ),
                "$.parts: required field is missing",
            ),
            (
                "SVG",
                lambda root: replace_file_text(
                    root / "icons" / "agent.svg",
                    "</svg>",
                    "<script/></svg>",
                ),
                "forbidden element <script>",
            ),
            (
                "token",
                lambda root: replace_file_text(
                    root / "tokens.css",
                    "--icon-status-error: #e65b65",
                    "--icon-status-error: not-a-color",
                ),
                "expected #rgb, #rrggbb, or opaque rgb()",
            ),
            (
                "attachment",
                lambda root: mutate_json_file(
                    root / "manifests" / "agent.json",
                    lambda value: value["attachments"]["receive"].__setitem__("x", 97),
                ),
                "$.attachments.receive.x: expected a finite number from 0 through 96",
            ),
            (
                "exception",
                lambda root: mutate_json_file(
                    root / "manifests" / "agent.json",
                    lambda value: value.__setitem__(
                        "exceptions",
                        [
                            {
                                "metric": "raw-size",
                                "reviewer": "qa",
                                "approved_on": "2026-07-16",
                            }
                        ],
                    ),
                ),
                "$.exceptions[0].reason: required field is missing",
            ),
            (
                "reference",
                lambda root: replace_file_text(
                    root / "icons" / "agent.svg",
                    "</svg>",
                    '<use href="#missing"/></svg>',
                ),
                "unresolved fragment #missing",
            ),
        )
        for label, mutate, expected_error in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                asset_root = copy_canonical_asset_root(temp_dir)
                mutate(asset_root)

                result = run_asset_validator(
                    "--review", "--json", "--asset-root", str(asset_root)
                )

                self.assertEqual(1, result.returncode)
                self.assertEqual("", result.stderr)
                report = json.loads(result.stdout)
                self.assertGreater(report["errors"], 0)
                self.assertIn(expected_error, "\n".join(report["error_details"]))

    def test_review_rejects_unexpected_approved_catalog_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_root = copy_canonical_asset_root(temp_dir)

            def approve_user(catalog):
                entry = next(icon for icon in catalog["icons"] if icon["id"] == "user")
                entry.update(
                    {
                        "structural_prototype": "actor-character",
                        "parts": ["shell"],
                        "supported_states": ["idle"],
                        "supported_actions": ["enter"],
                        "status": "approved",
                        "asset_revision": 1,
                    }
                )

            mutate_json_file(asset_root / "catalog.json", approve_user)
            result = run_asset_validator(
                "--review", "--json", "--asset-root", str(asset_root)
            )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(1, report["approved"])
        self.assertIn("user", "\n".join(report["error_details"]))

    def test_strict_mode_passes_after_all_four_benchmarks_are_promoted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_root = copy_canonical_asset_root(temp_dir)
            promote_benchmark_assets(asset_root)

            result = run_asset_validator(
                "--strict", "--json", "--asset-root", str(asset_root)
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(4, report["approved"])
        self.assertEqual(0, report["visual_review"])
        self.assertEqual(0, report["errors"])

    def test_json_output_is_deterministic_and_does_not_mutate_assets(self):
        asset_root = ROOT / "assets" / "diagram-core"
        before = asset_tree_snapshot(asset_root)

        first = run_asset_validator("--review", "--json")
        second = run_asset_validator("--review", "--json")

        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual("", first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(before, asset_tree_snapshot(asset_root))


if __name__ == "__main__":
    unittest.main()

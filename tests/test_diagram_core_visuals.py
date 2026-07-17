import copy
import hashlib
import http.server
import itertools
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock
from xml.etree import ElementTree

from PIL import Image

from anidiagram.diagram_core.tokens import contrast_ratio
from scripts import render_diagram_core_contact_sheet as contact_sheet_generator
from scripts import compare_diagram_core_contact_sheet as visual_comparator
from scripts.compare_diagram_core_contact_sheet import (
    VisualComparisonError,
    compare_images,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_diagram_core_contact_sheet.py"
TOKENS_PATH = ROOT / "assets" / "diagram-core" / "tokens.css"
ICONS = ("agent", "database", "api", "server")
SIZES = (48, 64, 96)
CONTEXTS = ("blue", "dark", "warm", "green")
ASSET_LOCAL_TOKENS = {"--icon-surface-contrast"}
CAPTURE_SIZE = (1248, 416)
FORBIDDEN_SVG_TAGS = {
    "animate",
    "animateMotion",
    "animateTransform",
    "filter",
    "foreignObject",
    "image",
    "script",
    "set",
}


def local_name(name):
    return name.rsplit("}", 1)[-1]


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


def inline_declarations(source):
    declarations = {}
    for statement in source.split(";"):
        if ":" not in statement:
            continue
        name, value = statement.split(":", 1)
        declarations[name.strip()] = value.strip()
    return declarations


class ReviewHTMLAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attributes = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attributes.append((tag, dict(attrs)))

    def handle_data(self, data):
        if data.strip():
            self.text.append(data.strip())


class StaticGridHTMLAudit(ReviewHTMLAudit):
    def __init__(self):
        super().__init__()
        self.regression_cells = []
        self.recognition_cells = []
        self.review_region_text = []
        self._review_region_depth = 0

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        attributes = dict(attrs)
        if attributes.get("data-icon-review-region") == "true":
            self._review_region_depth += 1
        elif self._review_region_depth:
            self._review_region_depth += 1
        if attributes.get("data-cell-kind") == "regression":
            self.regression_cells.append(attributes)
        if attributes.get("data-cell-kind") == "recognition":
            self.recognition_cells.append(attributes)

    def handle_startendtag(self, tag, attrs):
        ReviewHTMLAudit.handle_starttag(self, tag, attrs)

    def handle_endtag(self, tag):
        if self._review_region_depth:
            self._review_region_depth -= 1

    def handle_data(self, data):
        super().handle_data(data)
        if self._review_region_depth and data.strip():
            self.review_region_text.append(data.strip())


def geometry_signature(element):
    ignored = {
        "data-state-mark",
        "display",
        "fill",
        "stroke",
        "stroke-width",
        "stroke-linecap",
        "stroke-linejoin",
        "data-stroke-role",
    }
    return (
        local_name(element.tag),
        tuple(
            sorted(
                (local_name(name), value)
                for name, value in element.attrib.items()
                if local_name(name) not in ignored
            )
        ),
        tuple(geometry_signature(child) for child in element),
    )


class DiagramCoreVisualReviewTest(unittest.TestCase):
    def assert_no_publish_residue(self, root):
        residues = [
            path
            for path in Path(root).rglob("*")
            if path.name.endswith((".tmp", ".bak")) or ".claim-" in path.name
        ]
        self.assertEqual([], residues)

    def write_snapshot_file(self, path, payload, mode, mtime_ns):
        path.write_bytes(payload)
        path.chmod(mode)
        os.utime(path, ns=(mtime_ns, mtime_ns))
        return (payload, mode, mtime_ns)

    def assert_file_snapshot(self, path, expected):
        payload, mode, mtime_ns = expected
        self.assertEqual(payload, path.read_bytes())
        info = path.stat()
        self.assertEqual(mode, info.st_mode & 0o777)
        self.assertEqual(mtime_ns, info.st_mtime_ns)

    def generator_command(self, output, html_output, recognition=True, icon="agent", extra=()):
        command = [
            sys.executable,
            str(SCRIPT),
            "--icons",
            icon,
            "--output",
            str(output),
            "--html-output",
            str(html_output),
        ]
        if recognition:
            command.append("--recognition")
        command.extend(extra)
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def generate(self, temp_dir):
        root = Path(temp_dir)
        output = root / "artifacts" / "agent-contact.svg"
        html_output = root / "review" / "agent-review.html"
        result = self.generator_command(output, html_output)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            "icons=1 cells=12 unique=12 sizes=48,64,96 "
            "contexts=blue,dark,warm,green pose=authored-rest\nOK\n",
            result.stdout,
        )
        self.assertTrue(output.is_file())
        self.assertTrue(html_output.is_file())
        return output, html_output

    def benchmark_generator_command(
        self,
        output,
        html_output,
        recognition_output,
        cell_index,
        icons=ICONS,
        extra=(),
    ):
        command = [
            sys.executable,
            str(SCRIPT),
            "--icons",
            ",".join(icons),
            "--output",
            str(output),
            "--html-output",
            str(html_output),
            "--recognition-output",
            str(recognition_output),
            "--cell-index",
            str(cell_index),
        ]
        command.extend(extra)
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def generate_benchmark(self, temp_dir):
        root = Path(temp_dir)
        output = root / "assets" / "diagram-core" / "previews" / "benchmark.svg"
        html_output = root / "gallery" / "diagram-core" / "index.html"
        recognition_output = root / "gallery" / "diagram-core" / "recognition.html"
        cell_index = root / "gallery" / "diagram-core" / "cell-index.json"
        result = self.benchmark_generator_command(
            output,
            html_output,
            recognition_output,
            cell_index,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            "icons=4 cells=48 unique=48 sizes=48,64,96 "
            "contexts=blue,dark,warm,green pose=authored-rest\nOK\n",
            result.stdout,
        )
        for path in (output, html_output, recognition_output, cell_index):
            self.assertTrue(path.is_file(), path)
            self.assertEqual(0o644, path.stat().st_mode & 0o777)
        return output, html_output, recognition_output, cell_index

    def test_benchmark_is_exact_ordered_48_cell_product_and_index_matches_dom(self):
        expected = [
            (icon_id, size, context)
            for context, icon_id, size in itertools.product(
                CONTEXTS,
                ICONS,
                SIZES,
            )
        ]
        self.assertEqual(48, len(expected))
        self.assertEqual(48, len(set(expected)))
        with tempfile.TemporaryDirectory() as temp_dir:
            output, html_output, _, cell_index = self.generate_benchmark(temp_dir)
            root = ElementTree.parse(output).getroot()
            self.assertEqual("diagram-core-regression-grid", root.attrib.get("id"))
            self.assertEqual("12", root.attrib.get("data-grid-columns"))
            self.assertEqual("4", root.attrib.get("data-grid-rows"))
            self.assertEqual("48", root.attrib.get("data-cell-count"))
            self.assertEqual("1248", root.attrib.get("width"))
            self.assertEqual("416", root.attrib.get("height"))
            cells = [
                element
                for element in root.iter()
                if element.attrib.get("data-cell-kind") == "regression"
            ]
            self.assertFalse(
                any(local_name(element.tag) == "text" for element in root.iter())
            )
            svg_ids = [
                element.attrib["id"]
                for element in root.iter()
                if "id" in element.attrib
            ]
            self.assertEqual(len(svg_ids), len(set(svg_ids)))
            actual = [
                (
                    cell.attrib["data-icon-id"],
                    int(cell.attrib["data-size"]),
                    cell.attrib["data-context"],
                )
                for cell in cells
            ]
            self.assertEqual(expected, actual)
            cell_ids = [cell.attrib["data-cell-id"] for cell in cells]
            self.assertEqual(48, len(set(cell_ids)))

            index = json.loads(cell_index.read_text(encoding="utf-8"))
            self.assertEqual(1, index["version"])
            self.assertEqual({"columns": 12, "rows": 4, "cells": 48}, index["grid"])
            self.assertEqual(
                [
                    {
                        "ordinal": ordinal,
                        "cell_id": cell_ids[ordinal],
                        "icon_id": icon_id,
                        "size": size,
                        "context": context,
                        "pose": "authored-rest",
                    }
                    for ordinal, (icon_id, size, context) in enumerate(expected)
                ],
                index["cells"],
            )

            audit = StaticGridHTMLAudit()
            audit.feed(html_output.read_text(encoding="utf-8"))
            self.assertEqual(cell_ids, [cell["data-cell-id"] for cell in audit.regression_cells])
            self.assertEqual([], audit.review_region_text)
            id_values = [
                attributes["id"]
                for _, attributes in audit.attributes
                if "id" in attributes
            ]
            self.assertEqual(len(id_values), len(set(id_values)))

            source = html_output.read_text(encoding="utf-8")
            locator = next(
                attributes
                for _, attributes in audit.attributes
                if attributes.get("id") == "diagram-core-regression-grid"
            )
            self.assertEqual("true", locator.get("data-icon-review-region"))
            self.assertTrue(
                locator.get("aria-label", "").strip()
                or locator.get("aria-labelledby", "").strip()
            )
            legends = {
                attributes.get("data-grid-legend")
                for _, attributes in audit.attributes
                if attributes.get("data-grid-legend")
            }
            self.assertEqual({"columns", "rows"}, legends)
            visible_text = " ".join(audit.text).lower()
            for label in ICONS + CONTEXTS:
                self.assertIn(label, visible_text)
            for size in SIZES:
                self.assertIn(str(size) + " px", visible_text)
            self.assertNotRegex(
                source[source.index('id="diagram-core-regression-grid"') :],
                r"<text\b",
            )

    def test_benchmark_and_static_pages_are_local_deterministic_and_noninteractive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self.generate_benchmark(temp_dir)
            first = tuple(path.read_bytes() for path in paths)
            self.generate_benchmark(temp_dir)
            self.assertEqual(first, tuple(path.read_bytes() for path in paths))

            svg_root = ElementTree.fromstring(first[0])
            for element in svg_root.iter():
                self.assertNotIn(local_name(element.tag), FORBIDDEN_SVG_TAGS)
                for name, value in element.attrib.items():
                    self.assertFalse(name.lower().startswith("on"))
                    if local_name(name).lower() == "href":
                        self.assertTrue(value.startswith("#"))
            for path, payload in zip(paths, first):
                if path.suffix == ".json":
                    json.loads(payload.decode("utf-8"))
                    continue
                lowered = payload.decode("utf-8").lower()
                network_surface = lowered.replace("http://www.w3.org/2000/svg", "")
                self.assertNotIn("http://", network_surface)
                self.assertNotIn("https://", network_surface)
                self.assertNotIn("//", network_surface)
                self.assertNotIn("@import", network_surface)
                self.assertNotIn("<script", lowered)
                self.assertNotRegex(lowered, r"\b(?:animation|transition)\s*:")
                self.assertNotRegex(lowered, r"\bon[a-z]+\s*=")

    def test_recognition_surfaces_keep_four_authored_rest_silhouettes(self):
        modes = ("label-hidden", "accent-off", "grayscale", "node-context")
        with tempfile.TemporaryDirectory() as temp_dir:
            _, _, recognition_output, _ = self.generate_benchmark(temp_dir)
            source = recognition_output.read_text(encoding="utf-8")
            audit = StaticGridHTMLAudit()
            audit.feed(source)
            self.assertEqual([], audit.review_region_text)
            self.assertEqual(16, len(audit.recognition_cells))
            for mode in modes:
                cells = [
                    cell
                    for cell in audit.recognition_cells
                    if cell["data-recognition-mode"] == mode
                ]
                self.assertEqual(4, len(cells), mode)
                self.assertEqual(set(ICONS), {cell["data-icon-id"] for cell in cells})
                self.assertEqual({"48"}, {cell["data-size"] for cell in cells})
                self.assertEqual(
                    {"authored-rest"},
                    {cell["data-pose"] for cell in cells},
                )
                self.assertTrue(all("data-state" not in cell for cell in cells))
                self.assertTrue(all(cell.get("aria-label", "").strip() for cell in cells))

            ids = [
                attributes["id"]
                for _, attributes in audit.attributes
                if "id" in attributes
            ]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertNotRegex(source.lower(), r"\bfilter\s*:")

    def test_static_benchmark_defers_semantic_state_geometry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output, _, _, _ = self.generate_benchmark(temp_dir)
            root = ElementTree.parse(output).getroot()
            cells = [
                element
                for element in root.iter()
                if element.attrib.get("data-cell-kind") == "regression"
                and element.attrib.get("data-size") == "48"
                and element.attrib.get("data-context") == "blue"
            ]
            self.assertEqual(set(ICONS), {cell.attrib["data-icon-id"] for cell in cells})
            for cell in cells:
                self.assertEqual("authored-rest", cell.attrib["data-pose"])
                self.assertNotIn("data-state", cell.attrib)
                wrapper = next(
                    element
                    for element in cell.iter()
                    if element.attrib.get("data-icon-source") == "diagram-core-v1"
                )
                self.assertNotIn("data-icon-state", wrapper.attrib)
                self.assertFalse(
                    any("data-state-mark" in element.attrib for element in wrapper.iter())
                )

    def test_contact_sheet_has_exact_unique_matrix_and_real_context_tokens(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output, _ = self.generate(temp_dir)
            root = ElementTree.parse(output).getroot()
            background = next(
                element.attrib["fill"]
                for element in root
                if local_name(element.tag) == "rect"
                and element.attrib.get("x") == "0"
                and element.attrib.get("y") == "0"
            )
            subtitle = next(
                element
                for element in root
                if local_name(element.tag) == "text"
                and (element.text or "").startswith("3 sizes")
            )
            self.assertGreaterEqual(
                contrast_ratio(subtitle.attrib["fill"], background),
                4.5,
            )
            cells = [
                element
                for element in root.iter()
                if element.attrib.get("data-cell-kind") == "main"
            ]
            self.assertEqual(12, len(cells))
            cell_ids = [cell.attrib["data-cell-id"] for cell in cells]
            self.assertEqual(12, len(set(cell_ids)))
            self.assertEqual(set(SIZES), {int(cell.attrib["data-size"]) for cell in cells})
            self.assertEqual(set(CONTEXTS), {cell.attrib["data-context"] for cell in cells})
            self.assertEqual({"authored-rest"}, {cell.attrib["data-pose"] for cell in cells})
            self.assertTrue(all("data-state" not in cell.attrib for cell in cells))
            self.assertEqual(
                {
                    (size, context)
                    for size in SIZES
                    for context in CONTEXTS
                },
                {
                    (
                        int(cell.attrib["data-size"]),
                        cell.attrib["data-context"],
                    )
                    for cell in cells
                },
            )
            style_text = "\n".join(
                element.text or ""
                for element in root.iter()
                if local_name(element.tag) == "style"
            )
            self.assertNotIn("data-state-mark", style_text)
            self.assertNotIn("data-icon-state", style_text)

            token_source = TOKENS_PATH.read_text(encoding="utf-8")
            defaults = css_declarations(token_source, ":root")
            for cell in cells:
                context = cell.attrib["data-context"]
                expected_tokens = dict(defaults)
                expected_tokens.update(
                    css_declarations(
                        token_source,
                        '[data-icon-theme="' + context + '"]',
                    )
                )
                expected_local_tokens = {
                    token: value
                    for token, value in expected_tokens.items()
                    if token in ASSET_LOCAL_TOKENS
                }
                expected_adapter_tokens = {
                    token: value
                    for token, value in expected_tokens.items()
                    if token not in ASSET_LOCAL_TOKENS
                }
                wrappers = [
                    element
                    for element in cell.iter()
                    if element.attrib.get("data-icon-source") == "diagram-core-v1"
                ]
                with self.subTest(cell=cell.attrib["data-cell-id"]):
                    self.assertEqual(1, len(wrappers))
                    wrapper = wrappers[0]
                    self.assertEqual("agent", wrapper.attrib["data-icon"])
                    self.assertNotIn("data-icon-state", wrapper.attrib)
                    self.assertEqual(
                        expected_local_tokens,
                        inline_declarations(cell.attrib.get("style", "")),
                    )
                    self.assertEqual(
                        expected_adapter_tokens,
                        inline_declarations(wrapper.attrib["style"]),
                    )
                    self.assertIn("__agent__root", wrapper.attrib["id"])
                    label = " ".join(
                        element.text or ""
                        for element in cell.iter()
                        if local_name(element.tag) == "text"
                    )
                    self.assertIn(cell.attrib["data-size"] + "px", label)
                    self.assertIn(context, label)
                    self.assertIn("rest", label)

            script_source = SCRIPT.read_text(encoding="utf-8")
            self.assertIn("render_preview_icon(", script_source)
            self.assertNotIn("icons/agent.svg", script_source)

    def test_recognition_rows_are_static_local_and_generation_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output, html_output = self.generate(temp_dir)
            first_svg = output.read_bytes()
            first_html = html_output.read_bytes()
            self.generate(temp_dir)
            self.assertEqual(first_svg, output.read_bytes())
            self.assertEqual(first_html, html_output.read_bytes())

            root = ElementTree.fromstring(first_svg)
            rows = [
                element
                for element in root.iter()
                if "data-recognition-row" in element.attrib
            ]
            self.assertEqual(
                {"accent-off", "grayscale"},
                {row.attrib["data-recognition-row"] for row in rows},
            )
            self.assertEqual(2, len(rows))
            for row in rows:
                mode = row.attrib["data-recognition-row"]
                cells = [
                    element
                    for element in row.iter()
                    if element.attrib.get("data-cell-kind") == "recognition"
                ]
                self.assertEqual(1, len(cells))
                for cell in cells:
                    self.assertEqual("authored-rest", cell.attrib["data-pose"])
                    self.assertNotIn("data-state", cell.attrib)
                    label = " ".join(
                        element.text or ""
                        for element in cell.iter()
                        if local_name(element.tag) == "text"
                    )
                    compact_mode = "off" if mode == "accent-off" else "gray"
                    self.assertEqual(
                        "48px · {0} · rest".format(compact_mode),
                        label,
                    )
                    wrappers = [
                        element
                        for element in cell.iter()
                        if element.attrib.get("data-icon-source") == "diagram-core-v1"
                    ]
                    self.assertEqual(1, len(wrappers))
                    tokens = inline_declarations(wrappers[0].attrib["style"])
                    local_tokens = inline_declarations(cell.attrib.get("style", ""))
                    self.assertEqual(
                        {"--icon-surface-contrast"},
                        set(local_tokens),
                    )
                    self.assertNotIn("--icon-surface-contrast", tokens)
                    if mode == "accent-off":
                        self.assertEqual(tokens["--icon-stroke"], tokens["--icon-accent"])
                        self.assertEqual(tokens["--icon-detail"], tokens["--icon-accent-secondary"])
                    else:
                        for color in tokens.values():
                            self.assertRegex(color, r"^#[0-9a-f]{6}$")
                            self.assertEqual(color[1:3], color[3:5])
                            self.assertEqual(color[3:5], color[5:7])

            for element in root.iter():
                self.assertNotIn(local_name(element.tag), FORBIDDEN_SVG_TAGS)
                for name, value in element.attrib.items():
                    self.assertFalse(name.lower().startswith("on"))
                    if local_name(name).lower() == "href":
                        self.assertTrue(value.startswith("#"))
                    for reference in re.findall(
                        r"url\(\s*['\"]?([^)'\"\s]+)",
                        value,
                        re.IGNORECASE,
                    ):
                        self.assertTrue(reference.startswith("#"))
                    self.assertNotIn("javascript:", value.lower())
                    self.assertNotIn("data:", value.lower())
            lowered = first_svg.decode("utf-8").lower()
            self.assertNotRegex(lowered, r"\b(?:animation|transition)\s*:")
            network_surface = lowered.replace(
                "http://www.w3.org/2000/svg",
                "",
            )
            self.assertNotIn("http://", network_surface)
            self.assertNotIn("https://", network_surface)
            self.assertNotIn("//", network_surface)
            self.assertNotIn("@import", network_surface)

    def test_committed_review_artifacts_match_a_fresh_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            output = (
                temp_root
                / "assets"
                / "diagram-core"
                / "previews"
                / "agent-contact-sheet.svg"
            )
            html_output = (
                temp_root
                / "gallery"
                / "diagram-core"
                / "agent-review.html"
            )
            result = self.generator_command(output, html_output)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                (
                    ROOT
                    / "assets"
                    / "diagram-core"
                    / "previews"
                    / "agent-contact-sheet.svg"
                ).read_bytes(),
                output.read_bytes(),
            )
            self.assertEqual(
                (
                    ROOT
                    / "gallery"
                    / "diagram-core"
                    / "agent-review.html"
                ).read_bytes(),
                html_output.read_bytes(),
            )

    def test_committed_benchmark_artifacts_match_a_fresh_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            generated = self.generate_benchmark(temp_dir)
            committed = (
                ROOT
                / "assets"
                / "diagram-core"
                / "previews"
                / "benchmark-contact-sheet.svg",
                ROOT / "gallery" / "diagram-core" / "index.html",
                ROOT / "gallery" / "diagram-core" / "recognition.html",
                ROOT / "gallery" / "diagram-core" / "cell-index.json",
            )
            for committed_path, generated_path in zip(committed, generated):
                with self.subTest(path=committed_path):
                    self.assertTrue(committed_path.is_file())
                    self.assertEqual(
                        committed_path.read_bytes(),
                        generated_path.read_bytes(),
                    )

    def test_review_html_is_semantic_accessible_and_references_only_local_sheet(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output, html_output = self.generate(temp_dir)
            source = html_output.read_text(encoding="utf-8")
            audit = ReviewHTMLAudit()
            audit.feed(source)

            html_attrs = next(attrs for tag, attrs in audit.attributes if tag == "html")
            self.assertEqual("en", html_attrs.get("lang"))
            for tag in ("title", "header", "main", "section", "h1", "h2", "figure", "img", "figcaption", "ul", "li"):
                self.assertIn(tag, audit.tags)
            self.assertEqual(1, audit.tags.count("h1"))
            self.assertGreaterEqual(audit.tags.count("h2"), 2)

            images = [attrs for tag, attrs in audit.attributes if tag == "img"]
            self.assertEqual(1, len(images))
            expected_reference = os.path.relpath(output, html_output.parent).replace(os.sep, "/")
            self.assertEqual(expected_reference, images[0].get("src"))
            self.assertTrue(images[0].get("alt", "").strip())
            self.assertFalse(Path(images[0]["src"]).is_absolute())
            self.assertNotIn("://", images[0]["src"])

            visible_text = " ".join(audit.text).lower()
            for phrase in (
                "48 px recognition",
                "silhouette and visual weight",
                "face readability",
                "accent-off recognition",
                "four contexts",
                "state deferral",
            ):
                self.assertIn(phrase, visible_text)
            lowered = source.lower()
            self.assertNotIn("<script", lowered)
            self.assertNotIn("<button", lowered)
            self.assertNotIn('role="button"', lowered)
            self.assertNotIn("onclick=", lowered)
            self.assertNotRegex(lowered, r"outline\s*:\s*none")
            self.assertNotRegex(lowered, r"(?:https?:)?//")
            self.assertNotRegex(lowered, r"\b(?:animation|transition|filter)\s*:")

            page_background = css_declarations(source, "body")["background"]
            for selector in ("body", ".eyebrow", ".lede, figcaption, .scope"):
                text_color = css_declarations(source, selector)["color"]
                with self.subTest(selector=selector):
                    self.assertGreaterEqual(
                        contrast_ratio(text_color, page_background),
                        4.5,
                    )

    def test_cli_rejects_non_agent_missing_recognition_and_unknown_parameters(self):
        self.assertTrue(SCRIPT.is_file(), "review generator script must exist")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cases = (
                ("database", True, ()),
                ("agent,database", True, ()),
                ("agent", False, ()),
                ("agent", True, ("--unknown",)),
            )
            for index, (icon, recognition, extra) in enumerate(cases):
                output = root / str(index) / "sheet.svg"
                html_output = root / str(index) / "review.html"
                result = self.generator_command(
                    output,
                    html_output,
                    recognition=recognition,
                    icon=icon,
                    extra=extra,
                )
                with self.subTest(icon=icon, recognition=recognition, extra=extra):
                    self.assertNotEqual(0, result.returncode)
                    self.assertFalse(output.exists())
                    self.assertFalse(html_output.exists())

    def test_benchmark_preflight_failure_never_modifies_any_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for label, existing in (("new", False), ("existing", True)):
                case = root / label
                output = case / "sheet.svg"
                html_output = case / "index.html"
                recognition_output = case / "recognition.html"
                cell_index = case / "cell-index.json"
                recognition_output.mkdir(parents=True)
                expected = {}
                if existing:
                    for path, payload in (
                        (output, b"old-svg"),
                        (html_output, b"old-index"),
                        (cell_index, b"old-json"),
                    ):
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(payload)
                        expected[path] = payload

                result = self.benchmark_generator_command(
                    output,
                    html_output,
                    recognition_output,
                    cell_index,
                )
                with self.subTest(existing=existing):
                    self.assertNotEqual(0, result.returncode)
                    for path in (output, html_output, cell_index):
                        if existing:
                            self.assertEqual(expected[path], path.read_bytes())
                        else:
                            self.assertFalse(path.exists())
                    self.assertTrue(recognition_output.is_dir())
                    self.assert_no_publish_residue(case)

    def test_agent_preflight_failure_preserves_existing_first_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "agent.svg"
            html_output = root / "agent.html"
            output.write_bytes(b"old-agent-svg")
            html_output.mkdir()

            result = self.generator_command(output, html_output)

            self.assertNotEqual(0, result.returncode)
            self.assertEqual(b"old-agent-svg", output.read_bytes())
            self.assertTrue(html_output.is_dir())
            self.assert_no_publish_residue(root)

    CAPTURE_SCRIPT = ROOT / "scripts" / "capture_diagram_core_contact_sheet.mjs"
    COMPARATOR_SCRIPT = ROOT / "scripts" / "compare_diagram_core_contact_sheet.py"

    def solid_image(self, size=(100, 100), color=(240, 240, 240, 255)):
        return Image.new("RGBA", size, color)

    def change_square(self, image, x, y, width, height, delta):
        pixels = image.load()
        for py in range(y, y + height):
            for px in range(x, x + width):
                red, green, blue, alpha = pixels[px, py]
                pixels[px, py] = (min(255, red + delta), green, blue, alpha)

    def sha256(self, path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def capture_metadata_path(self, path, repo_root=ROOT):
        absolute = Path(path).resolve()
        try:
            return absolute.relative_to(repo_root).as_posix()
        except ValueError:
            return str(absolute)

    def canonical_source_assets(self, repo_root=ROOT):
        paths = visual_comparator.SOURCE_ASSET_PATHS
        files = [
            {"path": relative, "sha256": self.sha256(repo_root / relative)}
            for relative in paths
        ]
        joint_payload = "".join(
            "{0}\0{1}\n".format(entry["path"], entry["sha256"])
            for entry in files
        ).encode("utf-8")
        return {
            "files": files,
            "joint_sha256": hashlib.sha256(joint_payload).hexdigest(),
        }

    def locked_playwright_version(self, repo_root=ROOT):
        lock = json.loads((repo_root / "package-lock.json").read_text(encoding="utf-8"))
        return lock["packages"]["node_modules/playwright"]["version"]

    def copy_capture_repository(self, target, include_script=False):
        repo_root = Path(target).resolve()
        relative_paths = (
            "package-lock.json",
            visual_comparator.INDEX_RELATIVE_PATH,
            *visual_comparator.SOURCE_ASSET_PATHS,
        )
        if include_script:
            relative_paths += ("scripts/capture_diagram_core_contact_sheet.mjs",)
        for relative_path in relative_paths:
            source = ROOT / relative_path
            destination = repo_root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        return repo_root

    def atomically_replace_identity(self, path, replace=os.replace):
        target = Path(path)
        replacement = target.with_name(".{0}.replacement".format(target.name))
        replacement.write_bytes(target.read_bytes())
        replace(str(replacement), str(target))

    def capture_command(self, input_path, output, metadata):
        return self.run_process_group(
            [
                "node",
                str(self.CAPTURE_SCRIPT),
                "--input",
                str(input_path),
                "--output",
                str(output),
                "--metadata",
                str(metadata),
            ],
            cwd=ROOT,
            timeout=30,
        )

    def run_process_group(self, command, cwd=ROOT, env=None, timeout=30):
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as error:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                stdout, stderr = process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate(timeout=1)
            raise subprocess.TimeoutExpired(
                error.cmd,
                error.timeout,
                output=stdout,
                stderr=stderr,
            ) from error
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)

    def capture_metadata_digest(self, metadata):
        payload = copy.deepcopy(metadata)
        payload.pop("approval", None)
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def write_capture_fixture(
        self,
        root,
        stem,
        color=(20, 30, 40, 255),
        source_digest=None,
        playwright_version=None,
        chromium_version="143.0.7499.4",
        approved=False,
        platform_os="linux",
        platform_arch="x64",
        image_size=CAPTURE_SIZE,
        repo_root=ROOT,
    ):
        image_path = root / (stem + ".png")
        metadata_path = root / (stem + ".json")
        self.solid_image(image_size, color).save(image_path)
        digest = self.sha256(image_path)
        metadata = {
            "schema": "anidiagram.diagram-core.capture",
            "version": 1,
            "browser": {
                "playwright_version": playwright_version
                or self.locked_playwright_version(repo_root),
                "chromium_version": chromium_version,
            },
            "platform": {"os": platform_os, "arch": platform_arch},
            "viewport": {"width": 1280, "height": 900, "device_scale_factor": 1},
            "locator": {
                "selector": "#diagram-core-regression-grid",
                "bounding_box": {
                    "x": 0,
                    "y": 0,
                    "width": image_size[0],
                    "height": image_size[1],
                },
                "cells": 48,
            },
            "capture": {
                "timestamp_utc": "2026-07-16T00:00:00.000Z",
                "external_requests": 0,
                "external_request_urls": [],
                "animation_count": 0,
                "transition_count": 0,
            },
            "input": {
                "path": "gallery/diagram-core/index.html",
                "sha256": self.sha256(repo_root / "gallery/diagram-core/index.html"),
            },
            "image": {
                "path": self.capture_metadata_path(image_path, repo_root),
                "sha256": digest,
                "width": image_size[0],
                "height": image_size[1],
            },
            "source_assets": self.canonical_source_assets(repo_root),
        }
        if source_digest is not None:
            metadata["source_assets"]["joint_sha256"] = source_digest
        if approved:
            capture_digest = self.capture_metadata_digest(metadata)
            metadata["approval"] = {
                "timestamp_utc": "2026-07-16T00:01:00.000Z",
                "reviewer": "reviewer",
                "note": "approved synthetic fixture",
                "candidate_sha256": digest,
                "baseline_sha256": digest,
                "capture_metadata_sha256": capture_digest,
                "playwright_version": metadata["browser"]["playwright_version"],
                "chromium_version": metadata["browser"]["chromium_version"],
                "source_assets_joint_sha256": metadata["source_assets"]["joint_sha256"],
            }
        metadata_path.write_text(
            json.dumps(metadata, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return image_path, metadata_path

    def comparator_command(self, *arguments):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run(
            [sys.executable, str(self.COMPARATOR_SCRIPT)] + list(arguments),
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_pixel_diff_uses_channel_tolerance_eight_and_ratio_one_percent(self):
        baseline = self.solid_image()
        candidate = baseline.copy()
        self.change_square(candidate, x=0, y=0, width=10, height=10, delta=9)
        report = compare_images(
            baseline,
            candidate,
            channel_tolerance=8,
            max_diff_ratio=0.01,
        )
        self.assertEqual(100, report.differing_pixels)
        self.assertEqual(0.01, report.diff_ratio)
        self.assertTrue(report.passed)

    def test_pixel_diff_ratio_below_equal_and_above_threshold(self):
        baseline = self.solid_image()
        for pixels, passed in ((99, True), (100, True), (101, False)):
            candidate = baseline.copy()
            for index in range(pixels):
                candidate.putpixel((index % 100, index // 100), (249, 240, 240, 255))
            with self.subTest(pixels=pixels):
                report = compare_images(baseline, candidate)
                self.assertEqual(pixels, report.differing_pixels)
                self.assertEqual(passed, report.passed)

    def test_pixel_channel_difference_eight_is_equal_and_nine_differs(self):
        baseline = self.solid_image((1, 1), (100, 100, 100, 100))
        for delta, expected in ((8, 0), (9, 1)):
            candidate = self.solid_image((1, 1), (100, 100, 100, 100 + delta))
            with self.subTest(delta=delta):
                self.assertEqual(
                    expected,
                    compare_images(baseline, candidate).differing_pixels,
                )

    def test_dimension_mismatch_fails_before_pixel_comparison(self):
        with self.assertRaisesRegex(VisualComparisonError, "dimensions"):
            compare_images(
                self.solid_image((100, 100), (0, 0, 0, 255)),
                self.solid_image((101, 100), (0, 0, 0, 255)),
            )

    def test_failed_comparison_writes_nonzero_heatmap(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir).resolve() / "diff.png"
            baseline = self.solid_image((10, 10), (0, 0, 0, 255))
            candidate = baseline.copy()
            candidate.putpixel((3, 4), (9, 0, 0, 255))
            report = compare_images(
                baseline,
                candidate,
                max_diff_ratio=0,
                diff_output=output,
            )
            self.assertFalse(report.passed)
            self.assertTrue(output.is_file())
            heatmap = Image.open(output).convert("RGBA")
            self.assertEqual((255, 0, 0, 255), heatmap.getpixel((3, 4)))
            self.assertEqual((0, 0, 0, 0), heatmap.getpixel((0, 0)))

    def test_public_compare_heatmap_never_clobbers_pre_publish_external_writer(self):
        for existing in (True, False):
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir).resolve()
                output = root / "diff.png"
                if existing:
                    self.write_snapshot_file(
                        output,
                        b"old-heatmap",
                        0o640,
                        1_600_000_000_000_000_000,
                    )
                external_snapshot = [None]
                injected = [False]
                real_rename = os.rename

                def claim_after_external_replace(source, destination):
                    if Path(source) == output and not injected[0]:
                        injected[0] = True
                        external = root / ".external"
                        external_snapshot[0] = self.write_snapshot_file(
                            external,
                            b"EXTERNAL-HEATMAP",
                            0o604,
                            1_700_000_000_000_000_000,
                        )
                        os.replace(str(external), str(output))
                    return real_rename(source, destination)

                with mock.patch.object(
                    visual_comparator.os,
                    "rename",
                    side_effect=claim_after_external_replace,
                ):
                    with self.assertRaises(VisualComparisonError):
                        compare_images(
                            self.solid_image((1, 1), (0, 0, 0, 255)),
                            self.solid_image((1, 1), (255, 0, 0, 255)),
                            max_diff_ratio=0,
                            diff_output=output,
                        )

                self.assertTrue(injected[0])
                self.assert_file_snapshot(output, external_snapshot[0])
                self.assert_no_publish_residue(root)

    def test_capture_source_and_lock_freeze_real_browser_contract(self):
        source = self.CAPTURE_SCRIPT.read_text(encoding="utf-8")
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
        self.assertTrue(package["private"])
        pinned = package["devDependencies"]["playwright"]
        self.assertRegex(pinned, r"^\d+\.\d+\.\d+$")
        self.assertEqual(
            pinned,
            lock["packages"]["node_modules/playwright"]["version"],
        )
        for required in (
            'from "playwright"',
            "chromium.launchServer",
            "const DEVICE_SCALE_FACTOR = 1",
            "deviceScaleFactor: DEVICE_SCALE_FACTOR",
            'reducedMotion: "reduce"',
            "width: 1280",
            "height: 900",
            'serviceWorkers: "block"',
            'const LOCATOR = "#diagram-core-regression-grid"',
            "document.fonts.ready",
            "animation: none !important",
            "transition: none !important",
            "position: fixed !important",
            "top: 0 !important",
            "left: 0 !important",
            "data-cell-kind=\"regression\"",
            "1248",
            "416",
            "source_assets",
            "joint_sha256",
            "catalog.json",
            "tokens.css",
            "manifests",
            "icons",
            "Content-Security-Policy",
            "default-src 'none'",
            "img-src 'none'",
            "object-src 'none'",
            "connect-src 'none'",
            "base-uri 'none'",
        ):
            self.assertIn(required, source)
        self.assertIn("context.route", source)
        self.assertNotIn('page.route("**/*"', source)
        self.assertIn("javaScriptEnabled: false", source)
        self.assertIn("route.fulfill", source)
        self.assertIn("locator.screenshot", source)

    def test_capture_stabilization_uses_two_bounded_compositor_frame_captures(self):
        module_url = self.CAPTURE_SCRIPT.as_uri()
        program = """
const { stabilizeStaticDocument } = await import(%s);
if (typeof stabilizeStaticDocument !== "function") {
  throw new Error("stabilization export missing");
}
const calls = [];
const session = {
  send: async (method, parameters) => {
    calls.push([method, parameters]);
    return { data: "ZnJhbWU=" };
  },
  detach: async () => { calls.push(["detach", null]); },
};
const page = {
  evaluate: async (callback) => {
    calls.push(["fonts.ready", null]);
    return callback.toString().includes("document.fonts.ready");
  },
  context: () => ({
    newCDPSession: async (target) => {
      if (target !== page) throw new Error("wrong CDP target");
      calls.push(["newCDPSession", null]);
      return session;
    },
  }),
};
await stabilizeStaticDocument(page, 50);
const frames = calls.filter(([method]) => method === "Page.captureScreenshot");
if (frames.length !== 2) throw new Error(`expected two frame captures; found ${frames.length}`);
if (calls[0][0] !== "fonts.ready" || calls[1][0] !== "newCDPSession") {
  throw new Error(`fonts must settle before frame capture: ${JSON.stringify(calls)}`);
}
if (!frames.every(([, parameters]) => parameters.fromSurface === true)) {
  throw new Error("frame captures must use the compositor surface");
}
if (calls.at(-1)[0] !== "detach") throw new Error("CDP session was not detached");

const emptyFramePage = {
  evaluate: async () => {},
  context: () => ({
    newCDPSession: async () => ({
      send: async () => ({ data: "" }),
      detach: async () => {},
    }),
  }),
};
let emptyFrameFailure;
try {
  await stabilizeStaticDocument(emptyFramePage, 50);
} catch (error) {
  emptyFrameFailure = error;
}
if (!emptyFrameFailure || !emptyFrameFailure.message.includes("frame capture")) {
  throw new Error(`empty frame capture was accepted: ${emptyFrameFailure && emptyFrameFailure.message}`);
}

const never = () => new Promise(() => {});
const hangingPage = {
  evaluate: async () => {},
  context: () => ({
    newCDPSession: async () => ({ send: never, detach: async () => {} }),
  }),
};
const started = Date.now();
let timeoutFailure;
try {
  await stabilizeStaticDocument(hangingPage, 20);
} catch (error) {
  timeoutFailure = error;
}
if (!timeoutFailure || !timeoutFailure.message.includes("timed out")) {
  throw new Error(`frame timeout missing: ${timeoutFailure && timeoutFailure.message}`);
}
if (Date.now() - started > 500) throw new Error("frame barrier exceeded its bound");
""" % json.dumps(module_url)

        result = subprocess.run(
            ["node", "--input-type=module", "--eval", program],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )

        self.assertEqual(0, result.returncode, result.stderr)

    def test_capture_cleanup_force_kills_browser_process_after_close_timeouts(self):
        module_url = self.CAPTURE_SCRIPT.as_uri()
        program = """
const { runCaptureSession, shutdownBrowser, withCaptureDeadline } = await import(%s);
if (typeof shutdownBrowser !== "function") throw new Error("shutdown export missing");
if (typeof withCaptureDeadline !== "function") throw new Error("deadline export missing");
if (typeof runCaptureSession !== "function") throw new Error("session orchestration export missing");
const never = () => new Promise(() => {});
const signals = [];
const browserServer = {
  kill: never,
  process: () => ({ pid: 424242 }),
};
const started = Date.now();
let deadlineFailure;
try {
  await withCaptureDeadline(never, 20);
} catch (error) {
  deadlineFailure = error;
}
if (!deadlineFailure || !deadlineFailure.message.includes("timed out")) {
  throw new Error(`production capture deadline missing: ${deadlineFailure && deadlineFailure.message}`);
}
let failure;
try {
  await shutdownBrowser({
    context: { close: never },
    browser: { close: never },
    browserServer,
  }, 20, (pid, signal) => signals.push([pid, signal]));
} catch (error) {
  failure = error;
}
if (!failure || !failure.message.includes("timed out")) {
  throw new Error(`bounded cleanup failure missing: ${failure && failure.message}`);
}
const forcedBrowserPid = process.platform === "win32" ? 424242 : -424242;
if (JSON.stringify(signals) !== JSON.stringify([[forcedBrowserPid, "SIGKILL"]])) {
  throw new Error(`forced process kill missing: ${JSON.stringify(signals)}`);
}
if (Date.now() - started > 500) throw new Error("cleanup exceeded its bound");

const orchestrationSignals = [];
const orchestrationStarted = Date.now();
let orchestrationFailure;
try {
  await runCaptureSession(
    never,
    () => ({
      context: { close: never },
      browser: { close: never },
      browserServer: { kill: never, process: () => ({ pid: 515151 }) },
    }),
    20,
    20,
    (pid, signal) => orchestrationSignals.push([pid, signal]),
  );
} catch (error) {
  orchestrationFailure = error;
}
if (!orchestrationFailure || !orchestrationFailure.message.includes("timed out")) {
  throw new Error(`session orchestration failure missing: ${orchestrationFailure && orchestrationFailure.message}`);
}
const forcedSessionPid = process.platform === "win32" ? 515151 : -515151;
if (JSON.stringify(orchestrationSignals) !== JSON.stringify([[forcedSessionPid, "SIGKILL"]])) {
  throw new Error(`session cleanup was repeated: ${JSON.stringify(orchestrationSignals)}`);
}
if (Date.now() - orchestrationStarted > 500) {
  throw new Error("session plus cleanup exceeded its shared bound");
}
""" % json.dumps(module_url)

        result = subprocess.run(
            ["node", "--input-type=module", "--eval", program],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )

        self.assertEqual(0, result.returncode, result.stderr)

    def test_capture_absolute_deadline_bounds_launch_and_remaining_session_budget(self):
        module_url = self.CAPTURE_SCRIPT.as_uri()
        program = """
const {
  createOperationDeadline,
  launchBrowserServer,
  runCaptureSession,
} = await import(%s);
if (typeof createOperationDeadline !== "function") {
  throw new Error("absolute operation deadline export missing");
}
if (typeof launchBrowserServer !== "function") {
  throw new Error("deadline-aware browser launch export missing");
}
const never = () => new Promise(() => {});
const started = Date.now();
const deadline = createOperationDeadline(30);
let launchOptions;
let launchFailure;
let lateServerKills = 0;
try {
  await launchBrowserServer(deadline, async (options) => {
    launchOptions = options;
    await new Promise((resolve) => setTimeout(resolve, 60));
    return {
      kill: async () => { lateServerKills += 1; },
      process: () => ({ pid: 626262, exitCode: null, signalCode: null }),
    };
  });
} catch (error) {
  launchFailure = error;
}
if (!launchFailure || !launchFailure.message.includes("timed out")) {
  throw new Error(`hanging launch escaped deadline: ${launchFailure && launchFailure.message}`);
}
if (!launchOptions || !(launchOptions.timeout > 0 && launchOptions.timeout <= 30)) {
  throw new Error(`launch did not consume remaining budget: ${JSON.stringify(launchOptions)}`);
}
if (Date.now() - started > 500) throw new Error("launch deadline exceeded its bound");
await new Promise((resolve) => setTimeout(resolve, 80));
if (lateServerKills !== 1) {
  throw new Error(`late browser server was orphaned: kills=${lateServerKills}`);
}

const sharedDeadline = createOperationDeadline(50);
await new Promise((resolve) => setTimeout(resolve, 25));
let sessionFailure;
const sessionStarted = Date.now();
try {
  await runCaptureSession(
    never,
    () => ({}),
    sharedDeadline,
    20,
  );
} catch (error) {
  sessionFailure = error;
}
if (!sessionFailure || !sessionFailure.message.includes("timed out")) {
  throw new Error(`session escaped remaining budget: ${sessionFailure && sessionFailure.message}`);
}
if (Date.now() - sessionStarted > 300) {
  throw new Error("session received a fresh operation timeout");
}
""" % json.dumps(module_url)

        result = subprocess.run(
            ["node", "--input-type=module", "--eval", program],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        source = self.CAPTURE_SCRIPT.read_text(encoding="utf-8")
        deadline_index = source.index("const operationDeadline = createOperationDeadline")
        launch_index = source.index("await launchBrowserServer(operationDeadline")
        session_index = source.index("operationDeadline,", launch_index)
        self.assertLess(deadline_index, launch_index)
        self.assertLess(launch_index, session_index)

    def test_capture_subprocess_timeout_kills_entire_process_group(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            child_pid_path = Path(temp_dir) / "child.pid"
            child_program = (
                "import signal,time;"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN);"
                "time.sleep(60)"
            )
            parent_program = (
                "import pathlib,signal,subprocess,sys,time;"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN);"
                "child=subprocess.Popen([sys.executable,'-c',sys.argv[2]]);"
                "pathlib.Path(sys.argv[1]).write_text(str(child.pid));"
                "time.sleep(60)"
            )

            with self.assertRaises(subprocess.TimeoutExpired):
                self.run_process_group(
                    [
                        sys.executable,
                        "-c",
                        parent_program,
                        str(child_pid_path),
                        child_program,
                    ],
                    timeout=0.2,
                )

            child_pid = int(child_pid_path.read_text(encoding="utf-8"))
            for _ in range(50):
                try:
                    os.kill(child_pid, 0)
                except ProcessLookupError:
                    break
                threading.Event().wait(0.02)
            else:
                self.fail("timed-out capture process group left a child process alive")

    def test_capture_cli_requires_all_three_paths(self):
        result = subprocess.run(
            ["node", str(self.CAPTURE_SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("--input", result.stderr)
        self.assertIn("--output", result.stderr)
        self.assertIn("--metadata", result.stderr)

    def test_capture_blocks_secondary_local_file_requests_without_outputs(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="diagram-core-capture-", dir=build_root) as temp_dir:
            root = Path(temp_dir).resolve()
            malicious_input = root / "malicious.html"
            malicious_input.write_text(
                '<!doctype html><html><body><img src="file:///etc/hosts"></body></html>',
                encoding="utf-8",
            )
            output = root / "candidate.png"
            metadata = root / "candidate.json"
            result = self.capture_command(malicious_input, output, metadata)
            self.assertEqual(1, result.returncode)
            self.assertIn("external requests are forbidden", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(metadata.exists())

    def test_capture_allows_input_url_only_for_main_navigation(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="diagram-core-self-", dir=build_root) as temp_dir:
            root = Path(temp_dir).resolve()
            malicious_input = root / "self-resource.html"
            malicious_input.write_text(
                '<!doctype html><html><body><img src="self-resource.html"></body></html>',
                encoding="utf-8",
            )
            output = root / "candidate.png"
            metadata = root / "candidate.json"
            result = self.capture_command(malicious_input, output, metadata)
            self.assertEqual(1, result.returncode)
            self.assertIn("external requests are forbidden", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(metadata.exists())

    def test_capture_blocks_embedded_data_resources_without_outputs(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="diagram-core-data-", dir=build_root) as temp_dir:
            root = Path(temp_dir).resolve()
            malicious_input = root / "malicious-data.html"
            malicious_input.write_text(
                "<!doctype html><style>"
                "#diagram-core-regression-grid{background-image:url(data:image/png;base64,AA==)}"
                "</style><div id=\"diagram-core-regression-grid\"></div>",
                encoding="utf-8",
            )
            output = root / "candidate.png"
            metadata = root / "candidate.json"
            result = self.capture_command(malicious_input, output, metadata)
            self.assertEqual(1, result.returncode)
            self.assertIn("external requests are forbidden", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(metadata.exists())

    def test_capture_blocks_data_import_without_outputs(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="diagram-core-import-", dir=build_root) as temp_dir:
            root = Path(temp_dir).resolve()
            malicious_input = root / "malicious-import.html"
            malicious_input.write_text(
                "<!doctype html><style>"
                '@import "data:text/css,body%7Bcolor%3Ared%7D";'
                "#diagram-core-regression-grid{width:1248px;height:416px}"
                "</style><div id=\"diagram-core-regression-grid\"></div>"
                "<script>for(let i=0;i<48;i++){const c=document.createElement('i');"
                "c.dataset.cellKind='regression';document.querySelector("
                "'#diagram-core-regression-grid').append(c)}</script>",
                encoding="utf-8",
            )
            output = root / "candidate.png"
            metadata = root / "candidate.json"
            result = self.capture_command(malicious_input, output, metadata)
            self.assertEqual(1, result.returncode)
            self.assertIn("external requests are forbidden", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(metadata.exists())

    def test_capture_rejects_unsafe_html_presentation_resource_schemes(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        unsafe_references = (
            "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
            "width='8' height='8'%3E%3Crect width='8' height='8' fill='red'/%3E%3C/svg%3E",
            "blob:file:///diagram-core-probe",
            "http://127.0.0.1:9/diagram-core-probe.svg",
            "file:///etc/hosts",
            "//127.0.0.1:9/diagram-core-probe.svg",
            "diagram-core-relative-probe.svg",
        )
        source = (ROOT / "gallery/diagram-core/index.html").read_text(encoding="utf-8")
        self.assertIn("</svg>", source)
        for index, reference in enumerate(unsafe_references):
            with self.subTest(reference=reference):
                with tempfile.TemporaryDirectory(
                    prefix="diagram-core-presentation-{0}-".format(index),
                    dir=build_root,
                ) as temp_dir:
                    root = Path(temp_dir).resolve()
                    malicious_input = root / "presentation-resource.html"
                    probe = (
                        '<table background="{0}" style="width:104px;height:104px">'
                        "<tr><td>resource probe</td></tr></table>"
                    ).format(reference)
                    malicious_input.write_text(
                        source.replace("</body>", probe + "</body>", 1),
                        encoding="utf-8",
                    )
                    output = root / "candidate.png"
                    metadata = root / "candidate.json"

                    result = self.capture_command(malicious_input, output, metadata)

                    self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                    self.assertIn("forbidden", result.stderr)
                    self.assertFalse(output.exists())
                    self.assertFalse(metadata.exists())

    def test_capture_rejects_foreign_object_even_without_resource_attributes(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="diagram-core-foreign-object-",
            dir=build_root,
        ) as temp_dir:
            root = Path(temp_dir).resolve()
            input_path = root / "foreign-object.html"
            source = (ROOT / "gallery/diagram-core/index.html").read_text(encoding="utf-8")
            probe = (
                '<foreignObject x="0" y="0" width="104" height="104">'
                '<div xmlns="http://www.w3.org/1999/xhtml">static probe</div>'
                "</foreignObject>"
            )
            input_path.write_text(
                source.replace("</svg>", probe + "</svg>", 1),
                encoding="utf-8",
            )
            output = root / "candidate.png"
            metadata = root / "candidate.json"

            result = self.capture_command(input_path, output, metadata)

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertIn("forbidden", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(metadata.exists())

    def test_capture_preserves_strict_same_document_svg_fragments(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="diagram-core-local-fragment-",
            dir=build_root,
        ) as temp_dir:
            root = Path(temp_dir).resolve()
            input_path = root / "local-fragment.html"
            source = (ROOT / "gallery/diagram-core/index.html").read_text(encoding="utf-8")
            probe = (
                '<defs><linearGradient id="local-paint">'
                '<stop offset="0" stop-color="#fff"/>'
                '<stop offset="1" stop-color="#eee"/>'
                '</linearGradient><g id="local-shape">'
                '<rect width="1" height="1" fill="url(#local-paint)"/>'
                "</g></defs>"
                '<use href="#local-shape" x="1247" y="415"/>'
            )
            input_path.write_text(
                source.replace("</svg>", probe + "</svg>", 1),
                encoding="utf-8",
            )
            output = root / "candidate.png"
            metadata = root / "candidate.json"

            result = self.capture_command(input_path, output, metadata)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("cells=48 dpr=1 requests=0 animations=0", result.stdout)
            self.assertTrue(output.is_file())
            self.assertTrue(metadata.is_file())

    def test_capture_rejects_unsafe_svg_presentation_url_attributes(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        source = (ROOT / "gallery/diagram-core/index.html").read_text(encoding="utf-8")
        data_url = (
            "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
            "width='8' height='8'%3E%3Crect width='8' height='8' fill='red'/%3E%3C/svg%3E"
        )
        for attribute in (
            "fill",
            "stroke",
            "filter",
            "clip-path",
            "mask",
            "marker-start",
            "marker-mid",
            "marker-end",
            "cursor",
        ):
            with self.subTest(attribute=attribute):
                with tempfile.TemporaryDirectory(
                    prefix="diagram-core-svg-presentation-",
                    dir=build_root,
                ) as temp_dir:
                    root = Path(temp_dir).resolve()
                    input_path = root / "svg-presentation-resource.html"
                    probe = '<rect width="8" height="8" {0}="url({1}#probe)"/>'.format(
                        attribute,
                        data_url,
                    )
                    input_path.write_text(
                        source.replace("</svg>", probe + "</svg>", 1),
                        encoding="utf-8",
                    )
                    output = root / "candidate.png"
                    metadata = root / "candidate.json"

                    result = self.capture_command(input_path, output, metadata)

                    self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                    self.assertIn("forbidden", result.stderr)
                    self.assertFalse(output.exists())
                    self.assertFalse(metadata.exists())

    def test_capture_rejects_css_escaped_resource_functions(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        source = (ROOT / "gallery/diagram-core/index.html").read_text(encoding="utf-8")
        data_url = (
            "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
            "width='8' height='8'%3E%3Crect width='8' height='8' fill='red'/%3E%3C/svg%3E"
        )
        probes = (
            '<rect width="8" height="8" fill="u\\72l({0}#probe)"/>'.format(data_url),
            '<rect width="8" height="8" style="fill:u\\72l({0}#probe)"/>'.format(
                data_url
            ),
        )
        for index, probe in enumerate(probes):
            with self.subTest(index=index):
                with tempfile.TemporaryDirectory(
                    prefix="diagram-core-css-escape-",
                    dir=build_root,
                ) as temp_dir:
                    root = Path(temp_dir).resolve()
                    input_path = root / "css-escaped-resource.html"
                    input_path.write_text(
                        source.replace("</svg>", probe + "</svg>", 1),
                        encoding="utf-8",
                    )
                    output = root / "candidate.png"
                    metadata = root / "candidate.json"

                    result = self.capture_command(input_path, output, metadata)

                    self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                    self.assertIn("forbidden", result.stderr)
                    self.assertFalse(output.exists())
                    self.assertFalse(metadata.exists())

    def test_capture_rejects_browser_normalized_multiline_inline_css_url(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        source = (ROOT / "gallery/diagram-core/index.html").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory(
            prefix="diagram-core-css-continuation-",
            dir=build_root,
        ) as temp_dir:
            root = Path(temp_dir).resolve()
            input_path = root / "multiline-css-resource.html"
            probe = (
                '<rect x="0" y="0" width="104" height="104" '
                'style="fill:url(&quot;da\\\n'
                "ta:image/svg+xml,%3Csvg%20xmlns=%27http://www.w3.org/2000/svg%27%20"
                "width=%271%27%20height=%271%27%3E%3Crect%20width=%271%27%20"
                'height=%271%27%20fill=%27red%27/%3E%3C/svg%3E&quot;)"/>'
            )
            self.assertIn("\\\n", probe)
            input_path.write_text(
                source.replace("</svg>", probe + "</svg>", 1),
                encoding="utf-8",
            )
            output = root / "candidate.png"
            metadata = root / "candidate.json"

            result = self.capture_command(input_path, output, metadata)

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertIn("forbidden", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(metadata.exists())

    def test_capture_rejects_pixel_changing_closed_declarative_shadow_root(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        source = (ROOT / "gallery/diagram-core/index.html").read_text(encoding="utf-8")
        source = source.replace(
            'id="diagram-core-regression-grid"',
            'id="diagram-core-shadow-inner-grid"',
            1,
        ).replace(
            '<svg xmlns="http://www.w3.org/2000/svg"',
            '<div id="diagram-core-regression-grid" '
            'style="display:block;width:1248px;height:416px;position:relative">'
            '<svg xmlns="http://www.w3.org/2000/svg"',
            1,
        )
        shadow_overlay = (
            '</svg><span><template shadowrootmode="closed">'
            '<style>:host{display:block;position:absolute;inset:0;z-index:999;'
            'background:#ff00ff}img{display:block;width:100%;height:100%}</style>'
            '<img alt="" src="data:image/png;base64,'
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/'
            'h6mO9QAAAABJRU5ErkJggg==">'
            "</template></span></div>"
        )
        source = source.replace("</svg>", shadow_overlay, 1)
        with tempfile.TemporaryDirectory(
            prefix="diagram-core-closed-shadow-",
            dir=build_root,
        ) as temp_dir:
            root = Path(temp_dir).resolve()
            input_path = root / "closed-shadow-resource.html"
            input_path.write_text(source, encoding="utf-8")
            output = root / "candidate.png"
            metadata = root / "candidate.json"

            result = self.capture_command(input_path, output, metadata)

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertIn("forbidden", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(metadata.exists())

    def test_capture_rejects_svg_smil_elements_missing_from_web_animations(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        source = (ROOT / "gallery/diagram-core/index.html").read_text(encoding="utf-8")
        probes = {
            "animate": (
                '<g><rect width="8" height="8" fill="red"/>'
                '<animate attributeName="opacity" values="1;0;1" dur="1s" '
                'repeatCount="indefinite"/></g>'
            ),
            "animateMotion": (
                '<g><rect width="8" height="8" fill="red"/>'
                '<animateMotion path="M0 0 L16 0" dur="1s" '
                'repeatCount="indefinite"/></g>'
            ),
            "animateTransform": (
                '<g><rect width="8" height="8" fill="red"/>'
                '<animateTransform attributeName="transform" type="rotate" '
                'from="0" to="360" dur="1s" repeatCount="indefinite"/></g>'
            ),
            "set": (
                '<g><rect width="8" height="8" fill="red"/>'
                '<set attributeName="opacity" to="0" begin="0s" dur="indefinite"/></g>'
            ),
            "animateColor": (
                '<g><rect width="8" height="8" fill="red"/>'
                '<animateColor attributeName="fill" from="red" to="blue" '
                'dur="1s" repeatCount="indefinite"/></g>'
            ),
            "discard": (
                '<g><rect width="8" height="8" fill="red"/>'
                '<discard begin="0s"/></g>'
            ),
        }
        for name, probe in probes.items():
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory(
                    prefix="diagram-core-smil-{0}-".format(name.lower()),
                    dir=build_root,
                ) as temp_dir:
                    root = Path(temp_dir).resolve()
                    input_path = root / "smil.html"
                    input_path.write_text(
                        source.replace("</svg>", probe + "</svg>", 1),
                        encoding="utf-8",
                    )
                    output = root / "candidate.png"
                    metadata = root / "candidate.json"

                    result = self.capture_command(input_path, output, metadata)

                    self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                    self.assertIn("forbidden", result.stderr)
                    self.assertFalse(output.exists())
                    self.assertFalse(metadata.exists())

    def test_capture_rejects_empty_resource_references(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        source = (ROOT / "gallery/diagram-core/index.html").read_text(encoding="utf-8")
        probes = (
            '<use href="" x="0" y="0"/>',
            '<rect width="8" height="8" fill="url(\'\')"/>',
        )
        for index, probe in enumerate(probes):
            with self.subTest(index=index):
                with tempfile.TemporaryDirectory(
                    prefix="diagram-core-empty-resource-",
                    dir=build_root,
                ) as temp_dir:
                    root = Path(temp_dir).resolve()
                    input_path = root / "empty-resource.html"
                    input_path.write_text(
                        source.replace("</svg>", probe + "</svg>", 1),
                        encoding="utf-8",
                    )
                    output = root / "candidate.png"
                    metadata = root / "candidate.json"

                    result = self.capture_command(input_path, output, metadata)

                    self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                    self.assertIn("forbidden", result.stderr)
                    self.assertFalse(output.exists())
                    self.assertFalse(metadata.exists())

    def test_capture_rejects_missing_duplicate_and_rebased_fragments(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        source = (ROOT / "gallery/diagram-core/index.html").read_text(encoding="utf-8")
        probes = (
            '<use href="#missing-local-shape"/>',
            '<g id="duplicate-local-shape"/><g id="duplicate-local-shape"/>'
            '<use href="#duplicate-local-shape"/>',
            '<g id="rebased-local-shape" xml:base="#rebased">'
            '<use href="#rebased-local-shape"/></g>',
        )
        for index, probe in enumerate(probes):
            with self.subTest(index=index):
                with tempfile.TemporaryDirectory(
                    prefix="diagram-core-invalid-fragment-",
                    dir=build_root,
                ) as temp_dir:
                    root = Path(temp_dir).resolve()
                    input_path = root / "invalid-fragment.html"
                    input_path.write_text(
                        source.replace("</svg>", probe + "</svg>", 1),
                        encoding="utf-8",
                    )
                    output = root / "candidate.png"
                    metadata = root / "candidate.json"

                    result = self.capture_command(input_path, output, metadata)

                    self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                    self.assertIn("forbidden", result.stderr)
                    self.assertFalse(output.exists())
                    self.assertFalse(metadata.exists())

    def test_capture_rejects_self_deleting_data_resource_script_without_outputs(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="diagram-core-script-", dir=build_root) as temp_dir:
            root = Path(temp_dir).resolve()
            malicious_input = root / "self-deleting-script.html"
            source = (ROOT / "gallery" / "diagram-core" / "index.html").read_text(
                encoding="utf-8"
            )
            probe = (
                "<script>const probe=document.createElement('img');"
                "probe.src='data:image/png;base64,iVBORw0KGgo=';"
                "document.body.append(probe);probe.remove()</script>"
            )
            self.assertIn("</body>", source)
            malicious_input.write_text(
                source.replace("</body>", probe + "</body>", 1),
                encoding="utf-8",
            )
            output = root / "candidate.png"
            metadata = root / "candidate.json"

            result = self.capture_command(malicious_input, output, metadata)

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertIn("forbidden", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(metadata.exists())

    def test_capture_rejects_data_srcset_without_outputs(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="diagram-core-srcset-", dir=build_root) as temp_dir:
            root = Path(temp_dir).resolve()
            malicious_input = root / "data-srcset.html"
            source = (ROOT / "gallery/diagram-core/index.html").read_text(encoding="utf-8")
            probe = '<img alt="" srcset="data:image/png;base64,iVBORw0KGgo= 1x">'
            malicious_input.write_text(
                source.replace("</body>", probe + "</body>", 1),
                encoding="utf-8",
            )
            output = root / "candidate.png"
            metadata = root / "candidate.json"

            result = self.capture_command(malicious_input, output, metadata)

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertIn("forbidden", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(metadata.exists())

    def test_capture_rejects_data_adopted_stylesheet_without_outputs(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="diagram-core-adopted-", dir=build_root) as temp_dir:
            root = Path(temp_dir).resolve()
            malicious_input = root / "adopted-style.html"
            source = (ROOT / "gallery/diagram-core/index.html").read_text(encoding="utf-8")
            probe = (
                "<script>const sheet=new CSSStyleSheet();"
                "sheet.replaceSync('#diagram-core-regression-grid{"
                "background-image:url(data:image/png;base64,iVBORw0KGgo=)}');"
                "document.adoptedStyleSheets=[...document.adoptedStyleSheets,sheet]</script>"
            )
            malicious_input.write_text(
                source.replace("</body>", probe + "</body>", 1),
                encoding="utf-8",
            )
            output = root / "candidate.png"
            metadata = root / "candidate.json"

            result = self.capture_command(malicious_input, output, metadata)

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertIn("forbidden", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(metadata.exists())

    def test_capture_rejects_real_popup_http_target_without_outputs(self):
        hits = []

        class PopupHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                hits.append(self.path)
                body = b"<!doctype html><title>popup</title>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format_string, *arguments):
                del format_string, arguments

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), PopupHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            build_root = ROOT / "build"
            build_root.mkdir(exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="diagram-core-popup-", dir=build_root) as temp_dir:
                root = Path(temp_dir).resolve()
                malicious_input = root / "popup.html"
                source = (ROOT / "gallery/diagram-core/index.html").read_text(encoding="utf-8")
                popup_url = "http://127.0.0.1:{0}/popup".format(server.server_port)
                probe = "<script>window.open({0}, '_blank')</script>".format(
                    json.dumps(popup_url)
                )
                malicious_input.write_text(
                    source.replace("</body>", probe + "</body>", 1),
                    encoding="utf-8",
                )
                output = root / "candidate.png"
                metadata = root / "candidate.json"

                result = self.capture_command(malicious_input, output, metadata)

                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn("forbidden", result.stderr)
                self.assertFalse(output.exists())
                self.assertFalse(metadata.exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertEqual([], hits, "popup HTTP request must be blocked before reaching server")

    def test_capture_rejects_late_scheduled_request_without_outputs(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="diagram-core-late-", dir=build_root) as temp_dir:
            root = Path(temp_dir).resolve()
            malicious_input = root / "late-request.html"
            source = (ROOT / "gallery/diagram-core/index.html").read_text(encoding="utf-8")
            probe = (
                "<script>setTimeout(()=>fetch('data:text/plain,late'),10000)</script>"
            )
            malicious_input.write_text(
                source.replace("</body>", probe + "</body>", 1),
                encoding="utf-8",
            )
            output = root / "candidate.png"
            metadata = root / "candidate.json"

            result = self.capture_command(malicious_input, output, metadata)

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertIn("forbidden", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(metadata.exists())

    def test_capture_pair_publish_rolls_back_when_second_install_fails(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="diagram-core-publish-", dir=build_root) as temp_dir:
            root = Path(temp_dir).resolve()
            output = root / "candidate.png"
            metadata = root / "candidate.json"
            output.write_bytes(b"old-image")
            module_url = self.CAPTURE_SCRIPT.as_uri()
            program = """
import { link, rename, readFile, readdir } from "node:fs/promises";
const { publishCapture } = await import(%s);
let calls = 0;
const injectedLink = async (source, target) => {
  calls += 1;
  if (calls === 2) throw new Error("injected second install failure");
  return link(source, target);
};
let failed = false;
try {
  await publishCapture([
    { target: %s, payload: Buffer.from("new-image") },
    { target: %s, payload: Buffer.from("new-metadata") },
  ], { move: rename, link: injectedLink });
} catch (error) {
  failed = error.message.includes("injected second install failure");
}
if (!failed) throw new Error("publish did not expose injected failure");
if ((await readFile(%s, "utf8")) !== "old-image") throw new Error("image rollback failed");
try {
  await readFile(%s);
  throw new Error("metadata was partially published");
} catch (error) {
  if (error.code !== "ENOENT") throw error;
}
const residue = (await readdir(%s)).filter((name) => name.endsWith(".tmp"));
if (residue.length !== 0) throw new Error(`temporary residue: ${residue.join(",")}`);
""" % tuple(
                json.dumps(value)
                for value in (
                    module_url,
                    str(output),
                    str(metadata),
                    str(output),
                    str(metadata),
                    str(root),
                )
            )
            result = subprocess.run(
                ["node", "--input-type=module", "--eval", program],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            self.assertEqual(0, result.returncode, result.stderr)

    def test_capture_publish_preserves_existing_target_modes(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="diagram-core-mode-", dir=build_root) as temp_dir:
            root = Path(temp_dir).resolve()
            output = root / "candidate.png"
            metadata = root / "candidate.json"
            output.write_bytes(b"old-image")
            metadata.write_bytes(b"old-metadata")
            output.chmod(0o4600)
            metadata.chmod(0o1640)
            module_url = self.CAPTURE_SCRIPT.as_uri()
            program = """
import { stat } from "node:fs/promises";
const { publishCapture } = await import(%s);
await publishCapture([
  { target: %s, payload: Buffer.from("new-image") },
  { target: %s, payload: Buffer.from("new-metadata") },
]);
const imageMode = (await stat(%s)).mode & 0o7777;
const metadataMode = (await stat(%s)).mode & 0o7777;
if (imageMode !== 0o4600) throw new Error(`image mode changed to ${imageMode.toString(8)}`);
if (metadataMode !== 0o1640) throw new Error(`metadata mode changed to ${metadataMode.toString(8)}`);
""" % tuple(
                json.dumps(value)
                for value in (
                    module_url,
                    str(output),
                    str(metadata),
                    str(output),
                    str(metadata),
                )
            )

            result = subprocess.run(
                ["node", "--input-type=module", "--eval", program],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assert_no_publish_residue(root)

    def test_capture_publish_rejects_external_image_rewrite_after_first_replace(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="diagram-core-final-cas-", dir=build_root) as temp_dir:
            root = Path(temp_dir).resolve()
            output = root / "candidate.png"
            metadata = root / "candidate.json"
            output.write_bytes(b"old-image")
            metadata.write_bytes(b"old-metadata")
            module_url = self.CAPTURE_SCRIPT.as_uri()
            program = """
import { link, rename, readFile, readdir, writeFile } from "node:fs/promises";
const { publishCapture } = await import(%s);
let calls = 0;
const injectedLink = async (source, target) => {
  const result = await link(source, target);
  calls += 1;
  if (calls === 1) {
    const external = %s;
    await writeFile(external, "EXTERNAL-IMAGE");
    await rename(external, %s);
  }
  return result;
};
let failure;
try {
  await publishCapture([
    { target: %s, payload: Buffer.from("new-image") },
    { target: %s, payload: Buffer.from("new-metadata") },
  ], { move: rename, link: injectedLink });
} catch (error) {
  failure = error;
}
if (!failure || !failure.message.includes("rollback was incomplete")) {
  throw new Error(`stale publish was reported successful: ${failure && failure.message}`);
}
if (!failure.message.includes("claim preserved")) {
  throw new Error(`preserved claim was not reported: ${failure.message}`);
}
if ((await readFile(%s, "utf8")) !== "EXTERNAL-IMAGE") {
  throw new Error("external image update was overwritten");
}
if ((await readFile(%s, "utf8")) !== "old-metadata") {
  throw new Error("metadata was not rolled back");
}
const names = await readdir(%s, { recursive: true });
const backups = names.filter((name) => name.endsWith("/payload"));
const temporary = names.filter((name) => name.endsWith(".tmp"));
if (backups.length !== 1) throw new Error(`expected one backup; found ${backups}`);
if ((await readFile(%s + "/" + backups[0], "utf8")) !== "old-image") {
  throw new Error("preserved backup does not contain the original image");
}
if (temporary.length !== 0) throw new Error(`temporary residue: ${temporary}`);
""" % tuple(
                json.dumps(value)
                for value in (
                    module_url,
                    str(root / ".external-image"),
                    str(output),
                    str(output),
                    str(metadata),
                    str(output),
                    str(metadata),
                    str(root),
                    str(root),
                )
            )

            result = subprocess.run(
                ["node", "--input-type=module", "--eval", program],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )

            self.assertEqual(0, result.returncode, result.stderr)

    def test_capture_publish_rejects_external_metadata_update_before_replace(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="diagram-core-cas-", dir=build_root) as temp_dir:
            root = Path(temp_dir).resolve()
            output = root / "candidate.png"
            metadata = root / "candidate.json"
            output.write_bytes(b"old-image")
            metadata.write_bytes(b"old-metadata")
            module_url = self.CAPTURE_SCRIPT.as_uri()
            program = """
import { link, rename, readFile, writeFile } from "node:fs/promises";
const { publishCapture } = await import(%s);
let calls = 0;
const injectedLink = async (source, target) => {
  calls += 1;
  if (calls === 1) {
    const result = await link(source, target);
    await writeFile(%s, "EXTERNAL-METADATA");
    return result;
  }
  return link(source, target);
};
let failure;
try {
  await publishCapture([
    { target: %s, payload: Buffer.from("new-image") },
    { target: %s, payload: Buffer.from("new-metadata") },
  ], { move: rename, link: injectedLink });
} catch (error) {
  failure = error;
}
if (!failure) throw new Error("external update was overwritten");
if ((await readFile(%s, "utf8")) !== "old-image") throw new Error("image rollback failed");
if ((await readFile(%s, "utf8")) !== "EXTERNAL-METADATA") {
  throw new Error("external metadata update was not preserved");
}
""" % tuple(
                json.dumps(value)
                for value in (
                    module_url,
                    str(metadata),
                    str(output),
                    str(metadata),
                    str(output),
                    str(metadata),
                )
            )
            result = subprocess.run(
                ["node", "--input-type=module", "--eval", program],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            self.assertEqual(0, result.returncode, result.stderr)

    def test_capture_publish_is_no_clobber_at_claim_install_and_rollback_boundaries(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="diagram-core-no-clobber-",
            dir=build_root,
        ) as temp_dir:
            root = Path(temp_dir).resolve()
            module_url = self.CAPTURE_SCRIPT.as_uri()
            program = """
import {
  chmod,
  link,
  readFile,
  readdir,
  rename,
  stat,
  utimes,
  writeFile,
} from "node:fs/promises";
const { publishCapture } = await import(%s);
const root = %s;
const state = async (target) => {
  const info = await stat(target, { bigint: true });
  return {
    payload: await readFile(target, "utf8"),
    mode: Number(info.mode & 0o7777n),
    mtimeNs: info.mtimeNs,
  };
};
const assertState = async (target, expected, label) => {
  const actual = await state(target);
  if (
    actual.payload !== expected.payload
    || actual.mode !== expected.mode
    || actual.mtimeNs !== expected.mtimeNs
  ) throw new Error(`${label} changed: ${JSON.stringify(actual, (_, value) =>
    typeof value === "bigint" ? value.toString() : value)}`);
};
const writeExternal = async (target, payload, mode, seconds) => {
  await writeFile(target, payload);
  await chmod(target, mode);
  await utimes(target, seconds, seconds);
  return state(target);
};
const assertMissing = async (target, label) => {
  try {
    await stat(target);
    throw new Error(`${label} unexpectedly exists`);
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
};
const assertNoResidue = async (caseRoot) => {
  const names = await readdir(caseRoot, { recursive: true });
  const residue = names.filter((name) => /(?:\\.tmp|\\.bak|claim)/u.test(name));
  if (residue.length !== 0) throw new Error(`publish residue: ${residue.join(",")}`);
};

{
  const caseRoot = `${root}/claim-race`;
  await import("node:fs/promises").then(({ mkdir }) => mkdir(caseRoot));
  const image = `${caseRoot}/candidate.png`;
  const metadata = `${caseRoot}/candidate.json`;
  await writeFile(image, "old-image");
  await writeFile(metadata, "old-metadata");
  let externalState;
  let injected = false;
  const move = async (source, target) => {
    if (source === image && !injected) {
      injected = true;
      const external = `${caseRoot}/.external`;
      externalState = await writeExternal(external, "EXTERNAL-CLAIM", 0o604, 1700000001);
      await rename(external, image);
    }
    return rename(source, target);
  };
  let failure;
  try {
    await publishCapture([
      { target: image, payload: Buffer.from("new-image") },
      { target: metadata, payload: Buffer.from("new-metadata") },
    ], { move, link });
  } catch (error) {
    failure = error;
  }
  if (!injected || !failure) throw new Error("claim race returned success");
  await assertState(image, externalState, "claim-race external target");
  if ((await readFile(metadata, "utf8")) !== "old-metadata") {
    throw new Error("claim-race peer changed");
  }
  await assertNoResidue(caseRoot);
}

{
  const caseRoot = `${root}/install-race`;
  await import("node:fs/promises").then(({ mkdir }) => mkdir(caseRoot));
  const image = `${caseRoot}/candidate.png`;
  const metadata = `${caseRoot}/candidate.json`;
  let externalState;
  let injected = false;
  const install = async (source, target) => {
    if (target === image && !injected) {
      injected = true;
      externalState = await writeExternal(image, "EXTERNAL-INSTALL", 0o640, 1700000002);
    }
    return link(source, target);
  };
  let failure;
  try {
    await publishCapture([
      { target: image, payload: Buffer.from("new-image") },
      { target: metadata, payload: Buffer.from("new-metadata") },
    ], { move: rename, link: install });
  } catch (error) {
    failure = error;
  }
  if (!injected || !failure) throw new Error("absent-target install race returned success");
  await assertState(image, externalState, "install-race external target");
  await assertMissing(metadata, "install-race metadata");
  await assertNoResidue(caseRoot);
}

{
  const caseRoot = `${root}/rollback-race`;
  await import("node:fs/promises").then(({ mkdir }) => mkdir(caseRoot));
  const image = `${caseRoot}/candidate.png`;
  const metadata = `${caseRoot}/candidate.json`;
  await writeExternal(image, "old-image", 0o600, 1600000000);
  let moveCalls = 0;
  let externalState;
  const move = async (source, target) => {
    if (source === image) {
      moveCalls += 1;
      if (moveCalls === 2) {
        const external = `${caseRoot}/.external`;
        externalState = await writeExternal(external, "EXTERNAL-ROLLBACK", 0o604, 1700000003);
        await rename(external, image);
      }
    }
    return rename(source, target);
  };
  let installs = 0;
  const install = async (source, target) => {
    installs += 1;
    if (installs === 2) throw new Error("force rollback");
    return link(source, target);
  };
  let failure;
  try {
    await publishCapture([
      { target: image, payload: Buffer.from("new-image") },
      { target: metadata, payload: Buffer.from("new-metadata") },
    ], { move, link: install });
  } catch (error) {
    failure = error;
  }
  if (!failure || !failure.message.includes("rollback was incomplete")) {
    throw new Error(`rollback race was not reported: ${failure && failure.message}`);
  }
  if (!failure.message.includes("preserved")) {
    throw new Error(`rollback recovery path missing: ${failure.message}`);
  }
  await assertState(image, externalState, "rollback-race external target");
  await assertMissing(metadata, "rollback-race metadata");
}
""" % (json.dumps(module_url), json.dumps(str(root)))

            result = subprocess.run(
                ["node", "--input-type=module", "--eval", program],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            self.assertEqual(0, result.returncode, result.stderr)

    def test_capture_eexist_same_inode_is_an_external_ownership_conflict(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="diagram-core-eexist-ownership-",
            dir=build_root,
        ) as temp_dir:
            root = Path(temp_dir).resolve()
            image = root / "candidate.png"
            metadata = root / "candidate.json"
            self.write_snapshot_file(
                image,
                b"old-image",
                0o640,
                1_600_000_000_000_000_000,
            )
            metadata_snapshot = self.write_snapshot_file(
                metadata,
                b"old-metadata",
                0o600,
                1_600_000_001_000_000_000,
            )
            program = """
import { link, readFile, readdir, rename, stat } from "node:fs/promises";
const { publishCapture } = await import(%s);
const image = %s;
const metadata = %s;
let injected = false;
let externalState;
const linkThenEexist = async (source, target) => {
  if (target === image && !injected) {
    injected = true;
    await link(source, target);
    const info = await stat(target, { bigint: true });
    externalState = {
      payload: await readFile(target, "utf8"),
      mode: Number(info.mode & 0o7777n),
      mtimeNs: info.mtimeNs,
    };
  }
  return link(source, target);
};
let failure;
try {
  await publishCapture([
    { target: image, payload: Buffer.from("new-image") },
    { target: metadata, payload: Buffer.from("new-metadata") },
  ], { move: rename, link: linkThenEexist });
} catch (error) {
  failure = error;
}
if (!injected || !failure) throw new Error("EEXIST ownership race returned success");
if (!failure.message.includes("EEXIST")) {
  throw new Error(`EEXIST conflict was not reported: ${failure.message}`);
}
if (!failure.message.includes("rollback was incomplete")
    || !failure.message.includes("recovery claim preserved")) {
  throw new Error(`ownership claim was not reported: ${failure.message}`);
}
const current = await stat(image, { bigint: true });
if ((await readFile(image, "utf8")) !== externalState.payload
    || Number(current.mode & 0o7777n) !== externalState.mode
    || current.mtimeNs !== externalState.mtimeNs) {
  throw new Error("external same-inode link was changed or deleted");
}
if ((await readFile(metadata, "utf8")) !== "old-metadata") {
  throw new Error("unpublished peer metadata changed");
}
const names = await readdir(%s, { recursive: true });
const claims = names.filter((name) => name.endsWith("/payload"));
const temporary = names.filter((name) => name.endsWith(".tmp"));
if (claims.length !== 1) throw new Error(`expected one recovery claim: ${claims}`);
if ((await readFile(%s + "/" + claims[0], "utf8")) !== "old-image") {
  throw new Error("recovery claim does not contain the displaced image");
}
if (temporary.length !== 0) throw new Error(`temporary residue: ${temporary}`);
""" % tuple(
                json.dumps(value)
                for value in (
                    self.CAPTURE_SCRIPT.as_uri(),
                    str(image),
                    str(metadata),
                    str(root),
                    str(root),
                )
            )

            result = subprocess.run(
                ["node", "--input-type=module", "--eval", program],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assert_file_snapshot(metadata, metadata_snapshot)

    def test_capture_post_link_mode_change_is_detected_without_resetting_external_mode(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="diagram-core-post-link-mode-",
            dir=build_root,
        ) as temp_dir:
            root = Path(temp_dir).resolve()
            image = root / "candidate.png"
            metadata = root / "candidate.json"
            self.write_snapshot_file(
                image,
                b"old-image",
                0o640,
                1_600_000_000_000_000_000,
            )
            metadata_snapshot = self.write_snapshot_file(
                metadata,
                b"old-metadata",
                0o600,
                1_600_000_001_000_000_000,
            )
            program = """
import { chmod, link, readFile, readdir, rename, stat } from "node:fs/promises";
const { publishCapture } = await import(%s);
const image = %s;
const metadata = %s;
let injected = false;
let externalState;
const linkThenChmod = async (source, target) => {
  const result = await link(source, target);
  if (target === image && !injected) {
    injected = true;
    await chmod(target, 0o604);
    const info = await stat(target, { bigint: true });
    externalState = {
      payload: await readFile(target, "utf8"),
      mode: Number(info.mode & 0o7777n),
      mtimeNs: info.mtimeNs,
    };
  }
  return result;
};
let failure;
try {
  await publishCapture([
    { target: image, payload: Buffer.from("new-image") },
    { target: metadata, payload: Buffer.from("new-metadata") },
  ], { move: rename, link: linkThenChmod });
} catch (error) {
  failure = error;
}
if (!injected || !failure) throw new Error("post-link chmod returned stale success");
if (!failure.message.includes("rollback was incomplete")
    || !failure.message.includes("recovery claim preserved")) {
  throw new Error(`post-link mode conflict was not reported: ${failure.message}`);
}
const current = await stat(image, { bigint: true });
if ((await readFile(image, "utf8")) !== externalState.payload
    || Number(current.mode & 0o7777n) !== 0o604
    || Number(current.mode & 0o7777n) !== externalState.mode
    || current.mtimeNs !== externalState.mtimeNs) {
  throw new Error("external post-link mode change was reset");
}
if ((await readFile(metadata, "utf8")) !== "old-metadata") {
  throw new Error("unpublished peer metadata changed");
}
const names = await readdir(%s, { recursive: true });
const claims = names.filter((name) => name.endsWith("/payload"));
const temporary = names.filter((name) => name.endsWith(".tmp"));
if (claims.length !== 1) throw new Error(`expected one recovery claim: ${claims}`);
if ((await readFile(%s + "/" + claims[0], "utf8")) !== "old-image") {
  throw new Error("recovery claim does not contain the displaced image");
}
if (temporary.length !== 0) throw new Error(`temporary residue: ${temporary}`);
""" % tuple(
                json.dumps(value)
                for value in (
                    self.CAPTURE_SCRIPT.as_uri(),
                    str(image),
                    str(metadata),
                    str(root),
                    str(root),
                )
            )

            result = subprocess.run(
                ["node", "--input-type=module", "--eval", program],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assert_file_snapshot(metadata, metadata_snapshot)

    def test_capture_rechecks_both_outputs_after_claim_cleanup(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="diagram-core-post-commit-recheck-",
            dir=build_root,
        ) as temp_dir:
            root = Path(temp_dir).resolve()
            image = root / "candidate.png"
            metadata = root / "candidate.json"
            image.write_bytes(b"old-image")
            metadata.write_bytes(b"old-metadata")
            program = """
import {
  chmod,
  link,
  readFile,
  readdir,
  rename,
  rmdir,
  stat,
  utimes,
  writeFile,
} from "node:fs/promises";
const { publishCapture } = await import(%s);
const image = %s;
const metadata = %s;
let cleanupCalls = 0;
let externalState;
const cleanupThenReplace = async (directory) => {
  await rmdir(directory);
  cleanupCalls += 1;
  if (cleanupCalls === 1) {
    const external = %s;
    await writeFile(external, "EXTERNAL-AFTER-COMMIT");
    await chmod(external, 0o604);
    await utimes(external, 1700000010, 1700000010);
    await rename(external, image);
    const info = await stat(image, { bigint: true });
    externalState = {
      payload: await readFile(image, "utf8"),
      mode: Number(info.mode & 0o7777n),
      mtimeNs: info.mtimeNs,
    };
  }
};
let failure;
try {
  await publishCapture([
    { target: image, payload: Buffer.from("new-image") },
    { target: metadata, payload: Buffer.from("new-metadata") },
  ], { move: rename, link, rmdir: cleanupThenReplace });
} catch (error) {
  failure = error;
}
if (cleanupCalls !== 2 || !failure) {
  throw new Error("post-cleanup external replacement returned stale success");
}
if (!failure.message.includes("post-commit external change")
    || !failure.message.includes("committed outputs retained")) {
  throw new Error(`post-commit change was not reported clearly: ${failure.message}`);
}
const current = await stat(image, { bigint: true });
if ((await readFile(image, "utf8")) !== externalState.payload
    || Number(current.mode & 0o7777n) !== externalState.mode
    || current.mtimeNs !== externalState.mtimeNs) {
  throw new Error("post-commit external output was overwritten");
}
if ((await readFile(metadata, "utf8")) !== "new-metadata") {
  throw new Error("committed peer metadata was rolled back");
}
const names = await readdir(%s, { recursive: true });
const residue = names.filter((name) => /(?:\\.tmp|\\.bak|claim)/u.test(name));
if (residue.length !== 0) throw new Error(`post-commit residue: ${residue}`);
""" % tuple(
                json.dumps(value)
                for value in (
                    self.CAPTURE_SCRIPT.as_uri(),
                    str(image),
                    str(metadata),
                    str(root / ".external"),
                    str(root),
                )
            )

            result = subprocess.run(
                ["node", "--input-type=module", "--eval", program],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            self.assertEqual(0, result.returncode, result.stderr)

    def test_capture_claim_snapshot_failure_restores_or_reports_preserved_claim(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="diagram-core-claim-snapshot-",
            dir=build_root,
        ) as temp_dir:
            root = Path(temp_dir).resolve()
            program = """
import {
  chmod,
  link,
  mkdir,
  readFile,
  readdir,
  rename,
  stat,
  utimes,
  writeFile,
} from "node:fs/promises";
const { publishCapture } = await import(%s);
const root = %s;
const state = async (target) => {
  const info = await stat(target, { bigint: true });
  return {
    payload: await readFile(target, "utf8"),
    mode: Number(info.mode & 0o7777n),
    mtimeNs: info.mtimeNs,
  };
};
const writeState = async (target, payload, mode, seconds) => {
  await writeFile(target, payload);
  await chmod(target, mode);
  await utimes(target, seconds, seconds);
  return state(target);
};
const assertState = async (target, expected, label) => {
  const actual = await state(target);
  if (
    actual.payload !== expected.payload
    || actual.mode !== expected.mode
    || actual.mtimeNs !== expected.mtimeNs
  ) throw new Error(`${label} changed`);
};
for (const conflict of [false, true]) {
  const caseRoot = `${root}/${conflict ? "conflict" : "restore"}`;
  await mkdir(caseRoot);
  const image = `${caseRoot}/candidate.png`;
  const metadata = `${caseRoot}/candidate.json`;
  const originalImage = await writeState(image, "old-image", 0o640, 1600000000);
  const originalMetadata = await writeState(
    metadata,
    "old-metadata",
    0o600,
    1600000001,
  );
  let externalState;
  let injected = false;
  const failClaimSnapshot = async () => {
    if (injected) throw new Error("claim snapshot hook called twice");
    injected = true;
    if (conflict) {
      externalState = await writeState(
        image,
        "EXTERNAL-SNAPSHOT-RACE",
        0o604,
        1700000000,
      );
    }
    throw new Error("injected claim snapshot failure");
  };
  let failure;
  try {
    await publishCapture([
      { target: image, payload: Buffer.from("new-image") },
      { target: metadata, payload: Buffer.from("new-metadata") },
    ], { move: rename, link, snapshot: failClaimSnapshot });
  } catch (error) {
    failure = error;
  }
  if (!injected || !failure) {
    throw new Error(`claim snapshot failure was ignored: conflict=${conflict}`);
  }
  await assertState(
    image,
    conflict ? externalState : originalImage,
    `image conflict=${conflict}`,
  );
  await assertState(metadata, originalMetadata, `metadata conflict=${conflict}`);
  const names = await readdir(caseRoot, { recursive: true });
  const temporary = names.filter((name) => /(?:\\.tmp|\\.bak)$/u.test(name));
  if (temporary.length !== 0) throw new Error(`temporary residue: ${temporary}`);
  const claims = names.filter(
    (name) => name.includes(".claim-") && name.endsWith("payload"),
  );
  if (conflict) {
    if (!failure.message.includes("recovery claim preserved")) {
      throw new Error(`claim recovery path was not reported: ${failure.message}`);
    }
    if (claims.length !== 1) throw new Error(`expected one preserved claim: ${claims}`);
    if ((await readFile(`${caseRoot}/${claims[0]}`, "utf8")) !== "old-image") {
      throw new Error("preserved claim payload changed");
    }
  } else if (claims.length !== 0) {
    throw new Error(`restored claim residue: ${claims}`);
  }
}
""" % (
                json.dumps(self.CAPTURE_SCRIPT.as_uri()),
                json.dumps(str(root)),
            )

            result = subprocess.run(
                ["node", "--input-type=module", "--eval", program],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            self.assertEqual(0, result.returncode, result.stderr)

    def test_capture_commit_cleanup_failure_never_rolls_back_published_pair(self):
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="diagram-core-commit-barrier-",
            dir=build_root,
        ) as temp_dir:
            root = Path(temp_dir).resolve()
            output = root / "candidate.png"
            metadata = root / "candidate.json"
            output.write_bytes(b"old-image")
            metadata.write_bytes(b"old-metadata")
            program = """
import { link, readFile, readdir, rename, rmdir } from "node:fs/promises";
const { publishCapture } = await import(%s);
let cleanupCalls = 0;
const failSecondClaimDirectoryCleanup = async (directory) => {
  cleanupCalls += 1;
  if (cleanupCalls === 2) throw new Error("injected committed cleanup failure");
  return rmdir(directory);
};
let failure;
try {
  await publishCapture([
    { target: %s, payload: Buffer.from("new-image") },
    { target: %s, payload: Buffer.from("new-metadata") },
  ], { move: rename, link, rmdir: failSecondClaimDirectoryCleanup });
} catch (error) {
  failure = error;
}
if (!failure || !failure.message.includes("committed outputs retained")) {
  throw new Error(`commit cleanup did not report retained outputs: ${failure && failure.message}`);
}
if ((await readFile(%s, "utf8")) !== "new-image") {
  throw new Error("committed image was rolled back");
}
if ((await readFile(%s, "utf8")) !== "new-metadata") {
  throw new Error("committed metadata was rolled back");
}
const residue = (await readdir(%s, { recursive: true })).filter((name) => name.includes("claim"));
if (residue.length !== 1) throw new Error(`cleanup residue was not preserved: ${residue}`);
""" % tuple(
                json.dumps(value)
                for value in (
                    self.CAPTURE_SCRIPT.as_uri(),
                    str(output),
                    str(metadata),
                    str(output),
                    str(metadata),
                    str(root),
                )
            )

            result = subprocess.run(
                ["node", "--input-type=module", "--eval", program],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )

            self.assertEqual(0, result.returncode, result.stderr)

    def test_capture_rolls_back_pair_when_repo_provenance_changes_during_publish(self):
        provenance_paths = (
            "package-lock.json",
            visual_comparator.INDEX_RELATIVE_PATH,
            visual_comparator.SOURCE_ASSET_PATHS[0],
        )
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        for relative_path in provenance_paths:
            with self.subTest(relative_path=relative_path):
                with tempfile.TemporaryDirectory(
                    prefix="diagram-core-js-provenance-",
                    dir=build_root,
                ) as temp_dir:
                    repo_root = self.copy_capture_repository(
                        Path(temp_dir) / "repo",
                        include_script=True,
                    )
                    output = repo_root / "build/candidate.png"
                    metadata = repo_root / "build/candidate.json"
                    output.parent.mkdir(parents=True)
                    output.write_bytes(b"old-image")
                    metadata.write_bytes(b"old-metadata")
                    provenance = repo_root / relative_path
                    replacement = provenance.with_name(
                        ".{0}.replacement".format(provenance.name)
                    )
                    replacement.write_bytes(provenance.read_bytes())
                    module_url = (
                        repo_root / "scripts/capture_diagram_core_contact_sheet.mjs"
                    ).as_uri()
                    program = """
import { link, readFile, readdir, rename } from "node:fs/promises";
const captureModule = await import(%s);
if (typeof captureModule.capture !== "function") {
  throw new Error("capture export missing");
}
let installCalls = 0;
const injectedLink = async (source, target) => {
  const result = await link(source, target);
  installCalls += 1;
  if (installCalls === 1) await rename(%s, %s);
  return result;
};
let failure;
try {
  await captureModule.capture({
    input: %s,
    output: %s,
    metadata: %s,
  }, { move: rename, link: injectedLink });
} catch (error) {
  failure = error;
}
if (!failure || !failure.message.includes("changed during capture")) {
  throw new Error(`stale capture did not fail safely: ${failure && failure.message}`);
}
if ((await readFile(%s, "utf8")) !== "old-image") throw new Error("image rollback failed");
if ((await readFile(%s, "utf8")) !== "old-metadata") {
  throw new Error("metadata rollback failed");
}
const residue = (await readdir(%s)).filter(
  (name) => name.endsWith(".tmp") || name.endsWith(".bak") || name.includes("claim"),
);
if (residue.length !== 0) throw new Error(`publish residue: ${residue.join(",")}`);
""" % tuple(
                        json.dumps(value)
                        for value in (
                            module_url,
                            str(replacement),
                            str(provenance),
                            str(repo_root / visual_comparator.INDEX_RELATIVE_PATH),
                            str(output),
                            str(metadata),
                            str(output),
                            str(metadata),
                            str(output.parent),
                        )
                    )

                    result = self.run_process_group(
                        ["node", "--input-type=module", "--eval", program],
                        cwd=ROOT,
                        timeout=30,
                    )

                    self.assertEqual(0, result.returncode, result.stderr)

    def test_capture_schema_rejects_boolean_and_float_integer_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            image, metadata_path = self.write_capture_fixture(root, "candidate")
            original = json.loads(metadata_path.read_text(encoding="utf-8"))
            cases = (
                (("version",), True),
                (("version",), 1.0),
                (("viewport", "width"), 1280.0),
                (("viewport", "height"), True),
                (("viewport", "device_scale_factor"), True),
                (("locator", "cells"), 48.0),
                (("locator", "bounding_box", "x"), False),
                (("locator", "bounding_box", "y"), 0.0),
                (("locator", "bounding_box", "width"), 1248.0),
                (("locator", "bounding_box", "height"), 416.0),
                (("capture", "external_requests"), False),
                (("capture", "animation_count"), 0.0),
                (("capture", "transition_count"), False),
                (("image", "width"), 1248.0),
                (("image", "height"), 416.0),
            )
            for keys, invalid_value in cases:
                payload = copy.deepcopy(original)
                target = payload
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = invalid_value
                with self.subTest(field=".".join(keys), value=invalid_value):
                    with self.assertRaises(VisualComparisonError):
                        visual_comparator._validate_capture_metadata(
                            payload,
                            image,
                            "candidate",
                        )

    def test_accept_rejects_self_consistent_ten_by_ten_capture_without_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            candidate, candidate_metadata = self.write_capture_fixture(
                root,
                "candidate",
                image_size=(10, 10),
            )
            baseline = root / "baseline.png"
            baseline_metadata = root / "baseline.json"

            with self.assertRaises(VisualComparisonError):
                visual_comparator.accept_candidate(
                    candidate,
                    candidate_metadata,
                    baseline,
                    baseline_metadata,
                    "reviewer",
                    "reject noncanonical dimensions",
                )

            self.assertFalse(baseline.exists())
            self.assertFalse(baseline_metadata.exists())

    def test_comparison_rejects_metadata_mismatch_and_hash_tampering(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            baseline, baseline_metadata = self.write_capture_fixture(
                root, "baseline", approved=True
            )
            candidate, candidate_metadata = self.write_capture_fixture(root, "candidate")
            candidate_payload = json.loads(candidate_metadata.read_text(encoding="utf-8"))
            original_joint = candidate_payload["source_assets"]["joint_sha256"]
            original_playwright = candidate_payload["browser"]["playwright_version"]
            original_chromium = candidate_payload["browser"]["chromium_version"]
            candidate_payload["source_assets"]["joint_sha256"] = "d" * 64
            candidate_metadata.write_text(json.dumps(candidate_payload), encoding="utf-8")
            mismatch = self.comparator_command(
                "--baseline", str(baseline),
                "--baseline-metadata", str(baseline_metadata),
                "--candidate", str(candidate),
                "--candidate-metadata", str(candidate_metadata),
            )
            self.assertNotEqual(0, mismatch.returncode)
            self.assertIn("source asset digest", mismatch.stderr)

            candidate_payload["source_assets"]["joint_sha256"] = original_joint
            candidate_payload["browser"]["playwright_version"] = "different"
            candidate_metadata.write_text(json.dumps(candidate_payload), encoding="utf-8")
            playwright_mismatch = self.comparator_command(
                "--baseline", str(baseline),
                "--baseline-metadata", str(baseline_metadata),
                "--candidate", str(candidate),
                "--candidate-metadata", str(candidate_metadata),
            )
            self.assertNotEqual(0, playwright_mismatch.returncode)
            self.assertIn("Playwright", playwright_mismatch.stderr)

            candidate_payload["browser"]["playwright_version"] = original_playwright
            candidate_payload["browser"]["chromium_version"] = "different"
            candidate_metadata.write_text(json.dumps(candidate_payload), encoding="utf-8")
            browser_mismatch = self.comparator_command(
                "--baseline", str(baseline),
                "--baseline-metadata", str(baseline_metadata),
                "--candidate", str(candidate),
                "--candidate-metadata", str(candidate_metadata),
            )
            self.assertNotEqual(0, browser_mismatch.returncode)
            self.assertIn("Chromium", browser_mismatch.stderr)

            candidate_payload["browser"]["chromium_version"] = original_chromium
            candidate_payload["image"]["sha256"] = "0" * 64
            candidate_metadata.write_text(json.dumps(candidate_payload), encoding="utf-8")
            tampered = self.comparator_command(
                "--baseline", str(baseline),
                "--baseline-metadata", str(baseline_metadata),
                "--candidate", str(candidate),
                "--candidate-metadata", str(candidate_metadata),
            )
            self.assertNotEqual(0, tampered.returncode)
            self.assertIn("candidate image SHA-256", tampered.stderr)

    def test_normal_compare_writes_diff_without_mutating_baseline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            baseline, baseline_metadata = self.write_capture_fixture(
                root, "baseline", approved=True
            )
            candidate, candidate_metadata = self.write_capture_fixture(
                root, "candidate", color=(80, 30, 40, 255)
            )
            before = baseline.read_bytes(), baseline_metadata.read_bytes()
            diff = root / "heatmap.png"
            result = self.comparator_command(
                "--baseline", str(baseline),
                "--baseline-metadata", str(baseline_metadata),
                "--candidate", str(candidate),
                "--candidate-metadata", str(candidate_metadata),
                "--diff-output", str(diff),
            )
            self.assertEqual(1, result.returncode)
            self.assertTrue(diff.is_file())
            self.assertEqual(before, (baseline.read_bytes(), baseline_metadata.read_bytes()))

    def test_normal_compare_passes_matching_synthetic_captures(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            baseline, baseline_metadata = self.write_capture_fixture(
                root, "baseline", approved=True
            )
            candidate, candidate_metadata = self.write_capture_fixture(root, "candidate")
            before = baseline.read_bytes(), baseline_metadata.read_bytes()
            result = self.comparator_command(
                "--baseline", str(baseline),
                "--baseline-metadata", str(baseline_metadata),
                "--candidate", str(candidate),
                "--candidate-metadata", str(candidate_metadata),
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("differing_pixels=0", result.stdout)
            self.assertIn("diff_ratio=0.00000000", result.stdout)
            self.assertIn("passed=true", result.stdout)
            self.assertEqual(before, (baseline.read_bytes(), baseline_metadata.read_bytes()))

    def test_normal_compare_rejects_non_linux_approved_baseline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            baseline, baseline_metadata = self.write_capture_fixture(
                root,
                "baseline",
                approved=True,
                platform_os="darwin",
                platform_arch="arm64",
            )
            candidate, candidate_metadata = self.write_capture_fixture(
                root,
                "candidate",
                platform_os="darwin",
                platform_arch="arm64",
            )

            with self.assertRaisesRegex(VisualComparisonError, "linux"):
                visual_comparator.compare_capture_files(
                    baseline,
                    baseline_metadata,
                    candidate,
                    candidate_metadata,
                )

    def test_normal_compare_rejects_repo_replacement_before_return(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            repo_root = self.copy_capture_repository(root / "repo")
            fixtures = root / "fixtures"
            fixtures.mkdir()
            baseline, baseline_metadata = self.write_capture_fixture(
                fixtures,
                "baseline",
                approved=True,
                repo_root=repo_root,
            )
            candidate, candidate_metadata = self.write_capture_fixture(
                fixtures,
                "candidate",
                repo_root=repo_root,
            )
            replaced = repo_root / visual_comparator.SOURCE_ASSET_PATHS[0]
            real_compare = visual_comparator.compare_images

            def compare_then_replace(*arguments, **keywords):
                report = real_compare(*arguments, **keywords)
                self.atomically_replace_identity(replaced)
                return report

            with mock.patch.object(visual_comparator, "REPO_ROOT", repo_root), mock.patch.object(
                visual_comparator,
                "compare_images",
                side_effect=compare_then_replace,
            ):
                with self.assertRaises(VisualComparisonError):
                    visual_comparator.compare_capture_files(
                        baseline,
                        baseline_metadata,
                        candidate,
                        candidate_metadata,
                    )

    def test_normal_compare_repo_race_does_not_publish_stale_heatmap(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            repo_root = self.copy_capture_repository(root / "repo")
            fixtures = root / "fixtures"
            fixtures.mkdir()
            baseline, baseline_metadata = self.write_capture_fixture(
                fixtures,
                "baseline",
                approved=True,
                repo_root=repo_root,
            )
            candidate, candidate_metadata = self.write_capture_fixture(
                fixtures,
                "candidate",
                color=(90, 30, 40, 255),
                repo_root=repo_root,
            )
            diff_output = root / "existing.diff.png"
            original_diff = self.write_snapshot_file(
                diff_output,
                b"old-diff-output",
                0o640,
                1_625_000_000_000_000_000,
            )
            replaced = repo_root / visual_comparator.SOURCE_ASSET_PATHS[0]
            real_compare = visual_comparator.compare_images

            def compare_then_replace(*arguments, **keywords):
                report = real_compare(*arguments, **keywords)
                self.atomically_replace_identity(replaced)
                return report

            with mock.patch.object(visual_comparator, "REPO_ROOT", repo_root), mock.patch.object(
                visual_comparator,
                "compare_images",
                side_effect=compare_then_replace,
            ):
                with self.assertRaises(VisualComparisonError):
                    visual_comparator.compare_capture_files(
                        baseline,
                        baseline_metadata,
                        candidate,
                        candidate_metadata,
                        diff_output=diff_output,
                    )

            self.assert_file_snapshot(diff_output, original_diff)
            self.assert_no_publish_residue(root)

    def test_heatmap_rolls_back_when_repo_changes_after_publish(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            repo_root = self.copy_capture_repository(root / "repo")
            fixtures = root / "fixtures"
            fixtures.mkdir()
            baseline, baseline_metadata = self.write_capture_fixture(
                fixtures,
                "baseline",
                approved=True,
                repo_root=repo_root,
            )
            candidate, candidate_metadata = self.write_capture_fixture(
                fixtures,
                "candidate",
                color=(90, 30, 40, 255),
                repo_root=repo_root,
            )
            diff_output = root / "existing.diff.png"
            original_diff = self.write_snapshot_file(
                diff_output,
                b"old-diff-output",
                0o600,
                1_626_000_000_000_000_000,
            )
            source_asset = repo_root / visual_comparator.SOURCE_ASSET_PATHS[0]
            real_link = os.link
            real_compare = visual_comparator.compare_images
            injected = [False]

            def validate_with_small_decoded_image(
                metadata,
                image_path,
                label,
                require_approval=False,
                repository_provenance=None,
            ):
                del metadata, require_approval
                snapshot = visual_comparator._read_file_snapshot(
                    image_path,
                    "{0} image".format(label),
                )
                return visual_comparator.ValidatedCapture(
                    snapshot,
                    hashlib.sha256(snapshot.payload).hexdigest(),
                    self.solid_image((1, 1), (0, 0, 0, 255)),
                    repository_provenance,
                )

            def stage_small_failed_heatmap(*arguments, **keywords):
                del arguments
                return real_compare(
                    self.solid_image((1, 1), (0, 0, 0, 255)),
                    self.solid_image((1, 1), (255, 0, 0, 255)),
                    channel_tolerance=keywords["channel_tolerance"],
                    max_diff_ratio=keywords["max_diff_ratio"],
                    diff_output=keywords["diff_output"],
                )

            def publish_heatmap_then_change_source(source, target):
                result = real_link(source, target)
                if Path(target) == diff_output and not injected[0]:
                    injected[0] = True
                    self.atomically_replace_identity(source_asset)
                return result

            with mock.patch.object(
                visual_comparator,
                "REPO_ROOT",
                repo_root,
            ), mock.patch.object(
                visual_comparator,
                "_validate_capture_metadata",
                side_effect=validate_with_small_decoded_image,
            ), mock.patch.object(
                visual_comparator,
                "compare_images",
                side_effect=stage_small_failed_heatmap,
            ), mock.patch.object(
                visual_comparator.os,
                "link",
                side_effect=publish_heatmap_then_change_source,
            ):
                with self.assertRaises(VisualComparisonError):
                    visual_comparator.compare_capture_files(
                        baseline,
                        baseline_metadata,
                        candidate,
                        candidate_metadata,
                        diff_output=diff_output,
                    )

            self.assertTrue(injected[0])
            self.assert_file_snapshot(diff_output, original_diff)
            self.assert_no_publish_residue(root)

    def test_heatmap_publish_is_no_clobber_for_existing_and_absent_targets(self):
        for existing in (True, False):
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir).resolve()
                target = root / "heatmap.png"
                staged = root / ".heatmap.png.staged.tmp"
                staged.write_bytes(b"new-heatmap")
                original_snapshot = None
                if existing:
                    self.write_snapshot_file(
                        target,
                        b"old-heatmap",
                        0o640,
                        1_600_000_000_000_000_000,
                    )
                    original_snapshot = visual_comparator._output_snapshot(target)
                real_move = os.rename
                real_link = os.link
                external_snapshot = [None]
                injected = [False]

                def move_with_claim_race(source, destination):
                    if Path(source) == target and not injected[0]:
                        injected[0] = True
                        external = root / ".external"
                        external_snapshot[0] = self.write_snapshot_file(
                            external,
                            b"EXTERNAL-HEATMAP-CLAIM",
                            0o604,
                            1_700_000_000_000_000_000,
                        )
                        os.replace(str(external), str(target))
                    return real_move(source, destination)

                def link_with_install_race(source, destination):
                    if Path(destination) == target and not injected[0]:
                        injected[0] = True
                        external_snapshot[0] = self.write_snapshot_file(
                            target,
                            b"EXTERNAL-HEATMAP-INSTALL",
                            0o600,
                            1_700_000_001_000_000_000,
                        )
                    return real_link(source, destination)

                operations = {
                    "move": move_with_claim_race if existing else real_move,
                    "link": real_link if existing else link_with_install_race,
                }
                with self.assertRaises(Exception):
                    visual_comparator._publish_staged_heatmap(
                        target,
                        staged,
                        original_snapshot,
                        lambda: None,
                        operations=operations,
                    )

                self.assertTrue(injected[0])
                self.assert_file_snapshot(target, external_snapshot[0])
                self.assert_no_publish_residue(root)

    def test_python_publishers_treat_eexist_same_inode_as_external_ownership(self):
        for publisher in ("approval", "heatmap"):
            with self.subTest(publisher=publisher), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir).resolve()
                target = root / "published.png"
                self.write_snapshot_file(
                    target,
                    b"old-payload",
                    0o640,
                    1_600_000_000_000_000_000,
                )
                peer = root / "published.json"
                peer_snapshot = None
                if publisher == "approval":
                    peer_snapshot = self.write_snapshot_file(
                        peer,
                        b"old-peer",
                        0o600,
                        1_600_000_001_000_000_000,
                    )
                staged = root / ".heatmap.staged.tmp"
                if publisher == "heatmap":
                    staged.write_bytes(b"new-payload")
                target_snapshot = visual_comparator._output_snapshot(target)
                external_snapshot = [None]
                injected = [False]

                def link_then_eexist(source, destination):
                    if Path(destination) == target and not injected[0]:
                        injected[0] = True
                        os.link(source, destination)
                        info = target.stat()
                        external_snapshot[0] = (
                            target.read_bytes(),
                            info.st_mode & 0o777,
                            info.st_mtime_ns,
                        )
                    return os.link(source, destination)

                with self.assertRaises(Exception) as caught:
                    if publisher == "approval":
                        visual_comparator._publish_approval(
                            target,
                            b"new-payload",
                            peer,
                            b"new-peer",
                            operations={"move": os.rename, "link": link_then_eexist},
                        )
                    else:
                        visual_comparator._publish_staged_heatmap(
                            target,
                            staged,
                            target_snapshot,
                            lambda: None,
                            operations={"move": os.rename, "link": link_then_eexist},
                        )

                self.assertTrue(injected[0])
                self.assertIn("File exists", str(caught.exception))
                self.assertIn("rollback was incomplete", str(caught.exception))
                self.assertIn("recovery claim preserved", str(caught.exception))
                self.assert_file_snapshot(target, external_snapshot[0])
                if publisher == "approval":
                    self.assert_file_snapshot(peer, peer_snapshot)
                self.assertFalse(staged.exists())
                claims = [
                    path
                    for path in root.rglob("payload")
                    if ".claim-" in str(path.parent)
                ]
                self.assertEqual(1, len(claims))
                self.assertEqual(b"old-payload", claims[0].read_bytes())
                temporary = [
                    path
                    for path in root.rglob("*")
                    if path.name.endswith((".tmp", ".bak"))
                ]
                self.assertEqual([], temporary)

    def test_python_publishers_detect_post_link_chmod_without_resetting_mode(self):
        for publisher in ("approval", "heatmap"):
            with self.subTest(publisher=publisher), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir).resolve()
                target = root / "published.png"
                self.write_snapshot_file(
                    target,
                    b"old-payload",
                    0o640,
                    1_600_000_000_000_000_000,
                )
                peer = root / "published.json"
                peer_snapshot = None
                if publisher == "approval":
                    peer_snapshot = self.write_snapshot_file(
                        peer,
                        b"old-peer",
                        0o600,
                        1_600_000_001_000_000_000,
                    )
                staged = root / ".heatmap.staged.tmp"
                if publisher == "heatmap":
                    staged.write_bytes(b"new-payload")
                target_snapshot = visual_comparator._output_snapshot(target)
                external_snapshot = [None]
                injected = [False]

                def link_then_chmod(source, destination):
                    result = os.link(source, destination)
                    if Path(destination) == target and not injected[0]:
                        injected[0] = True
                        target.chmod(0o604)
                        info = target.stat()
                        external_snapshot[0] = (
                            target.read_bytes(),
                            info.st_mode & 0o777,
                            info.st_mtime_ns,
                        )
                    return result

                with self.assertRaises(Exception) as caught:
                    if publisher == "approval":
                        visual_comparator._publish_approval(
                            target,
                            b"new-payload",
                            peer,
                            b"new-peer",
                            operations={"move": os.rename, "link": link_then_chmod},
                        )
                    else:
                        visual_comparator._publish_staged_heatmap(
                            target,
                            staged,
                            target_snapshot,
                            lambda: None,
                            operations={"move": os.rename, "link": link_then_chmod},
                        )

                self.assertTrue(injected[0])
                self.assertIn("rollback was incomplete", str(caught.exception))
                self.assertIn("recovery claim preserved", str(caught.exception))
                self.assert_file_snapshot(target, external_snapshot[0])
                self.assertEqual(0o604, target.stat().st_mode & 0o777)
                if publisher == "approval":
                    self.assert_file_snapshot(peer, peer_snapshot)
                self.assertFalse(staged.exists())
                claims = [
                    path
                    for path in root.rglob("payload")
                    if ".claim-" in str(path.parent)
                ]
                self.assertEqual(1, len(claims))
                self.assertEqual(b"old-payload", claims[0].read_bytes())
                temporary = [
                    path
                    for path in root.rglob("*")
                    if path.name.endswith((".tmp", ".bak"))
                ]
                self.assertEqual([], temporary)

    def test_python_publishers_recheck_targets_after_claim_cleanup(self):
        for publisher in ("approval", "heatmap"):
            with self.subTest(publisher=publisher), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir).resolve()
                target = root / "published.png"
                target.write_bytes(b"old-payload")
                peer = root / "published.json"
                if publisher == "approval":
                    peer.write_bytes(b"old-peer")
                staged = root / ".heatmap.staged.tmp"
                if publisher == "heatmap":
                    staged.write_bytes(b"new-payload")
                target_snapshot = visual_comparator._output_snapshot(target)
                cleanup_calls = [0]
                external_snapshot = [None]

                def cleanup_then_replace(directory):
                    os.rmdir(directory)
                    cleanup_calls[0] += 1
                    if cleanup_calls[0] == 1:
                        external = root / ".external"
                        external_snapshot[0] = self.write_snapshot_file(
                            external,
                            b"EXTERNAL-AFTER-COMMIT",
                            0o604,
                            1_700_000_010_000_000_000,
                        )
                        os.replace(str(external), str(target))

                with self.assertRaisesRegex(
                    VisualComparisonError,
                    "post-commit external change",
                ) as caught:
                    if publisher == "approval":
                        visual_comparator._publish_approval(
                            target,
                            b"new-payload",
                            peer,
                            b"new-peer",
                            operations={
                                "move": os.rename,
                                "link": os.link,
                                "rmdir": cleanup_then_replace,
                            },
                        )
                    else:
                        visual_comparator._publish_staged_heatmap(
                            target,
                            staged,
                            target_snapshot,
                            lambda: None,
                            operations={
                                "move": os.rename,
                                "link": os.link,
                                "rmdir": cleanup_then_replace,
                            },
                        )

                expected_cleanups = 2 if publisher == "approval" else 1
                self.assertEqual(expected_cleanups, cleanup_calls[0])
                self.assertIn("committed outputs retained", str(caught.exception))
                self.assert_file_snapshot(target, external_snapshot[0])
                if publisher == "approval":
                    self.assertEqual(b"new-peer", peer.read_bytes())
                self.assertFalse(staged.exists())
                self.assert_no_publish_residue(root)

    def test_heatmap_rollback_never_overwrites_external_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            target = root / "heatmap.png"
            staged = root / ".heatmap.png.staged.tmp"
            original = self.write_snapshot_file(
                target,
                b"old-heatmap",
                0o640,
                1_600_000_000_000_000_000,
            )
            del original
            staged.write_bytes(b"new-heatmap")
            target_snapshot = visual_comparator._output_snapshot(target)
            real_move = os.rename
            move_calls = [0]
            external_snapshot = [None]

            def move_with_rollback_race(source, destination):
                if Path(source) == target:
                    move_calls[0] += 1
                    if move_calls[0] == 2:
                        external = root / ".external"
                        external_snapshot[0] = self.write_snapshot_file(
                            external,
                            b"EXTERNAL-HEATMAP-ROLLBACK",
                            0o604,
                            1_700_000_002_000_000_000,
                        )
                        os.replace(str(external), str(target))
                return real_move(source, destination)

            verify_calls = [0]

            def fail_after_install():
                verify_calls[0] += 1
                if verify_calls[0] == 3:
                    raise VisualComparisonError("force heatmap rollback")

            with self.assertRaisesRegex(
                VisualComparisonError,
                "rollback was incomplete",
            ) as caught:
                visual_comparator._publish_staged_heatmap(
                    target,
                    staged,
                    target_snapshot,
                    fail_after_install,
                    operations={"move": move_with_rollback_race, "link": os.link},
                )

            self.assertIn("preserved", str(caught.exception))
            self.assert_file_snapshot(target, external_snapshot[0])

    def test_approval_publish_is_no_clobber_for_existing_and_absent_targets(self):
        for existing in (True, False):
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir).resolve()
                baseline = root / "baseline.png"
                metadata = root / "baseline.json"
                if existing:
                    baseline.write_bytes(b"old-image")
                    metadata.write_bytes(b"old-metadata")
                real_move = os.rename
                real_link = os.link
                injected = [False]
                external_snapshot = [None]

                def move_with_claim_race(source, destination):
                    if Path(source) == baseline and not injected[0]:
                        injected[0] = True
                        external = root / ".external"
                        external_snapshot[0] = self.write_snapshot_file(
                            external,
                            b"EXTERNAL-APPROVAL-CLAIM",
                            0o604,
                            1_700_000_003_000_000_000,
                        )
                        os.replace(str(external), str(baseline))
                    return real_move(source, destination)

                def link_with_install_race(source, destination):
                    if Path(destination) == baseline and not injected[0]:
                        injected[0] = True
                        external_snapshot[0] = self.write_snapshot_file(
                            baseline,
                            b"EXTERNAL-APPROVAL-INSTALL",
                            0o600,
                            1_700_000_004_000_000_000,
                        )
                    return real_link(source, destination)

                operations = {
                    "move": move_with_claim_race if existing else real_move,
                    "link": real_link if existing else link_with_install_race,
                }
                with self.assertRaises(Exception):
                    visual_comparator._publish_approval(
                        baseline,
                        b"new-image",
                        metadata,
                        b"new-metadata",
                        operations=operations,
                    )

                self.assertTrue(injected[0])
                self.assert_file_snapshot(baseline, external_snapshot[0])
                if existing:
                    self.assertEqual(b"old-metadata", metadata.read_bytes())
                else:
                    self.assertFalse(metadata.exists())
                self.assert_no_publish_residue(root)

    def test_approval_rollback_never_overwrites_external_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            baseline = root / "baseline.png"
            metadata = root / "baseline.json"
            self.write_snapshot_file(
                baseline,
                b"old-image",
                0o640,
                1_600_000_000_000_000_000,
            )
            real_move = os.rename
            move_calls = [0]
            external_snapshot = [None]

            def move_with_rollback_race(source, destination):
                if Path(source) == baseline:
                    move_calls[0] += 1
                    if move_calls[0] == 2:
                        external = root / ".external"
                        external_snapshot[0] = self.write_snapshot_file(
                            external,
                            b"EXTERNAL-APPROVAL-ROLLBACK",
                            0o604,
                            1_700_000_005_000_000_000,
                        )
                        os.replace(str(external), str(baseline))
                return real_move(source, destination)

            link_calls = [0]

            def fail_second_install(source, destination):
                link_calls[0] += 1
                if link_calls[0] == 2:
                    raise OSError("force approval rollback")
                return os.link(source, destination)

            with self.assertRaisesRegex(
                VisualComparisonError,
                "rollback was incomplete",
            ) as caught:
                visual_comparator._publish_approval(
                    baseline,
                    b"new-image",
                    metadata,
                    b"new-metadata",
                    operations={
                        "move": move_with_rollback_race,
                        "link": fail_second_install,
                    },
                )

            self.assertIn("preserved", str(caught.exception))
            self.assert_file_snapshot(baseline, external_snapshot[0])
            self.assertFalse(metadata.exists())

    def test_approval_claim_snapshot_failure_restores_or_reports_preserved_claim(self):
        for conflict in (False, True):
            with self.subTest(conflict=conflict), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir).resolve()
                baseline = root / "baseline.png"
                metadata = root / "baseline.json"
                original_baseline = self.write_snapshot_file(
                    baseline,
                    b"old-image",
                    0o640,
                    1_600_000_000_000_000_000,
                )
                original_metadata = self.write_snapshot_file(
                    metadata,
                    b"old-metadata",
                    0o600,
                    1_600_000_001_000_000_000,
                )
                external_snapshot = [None]
                injected = [False]

                def fail_claim_snapshot(path):
                    del path
                    if injected[0]:
                        raise AssertionError("claim snapshot hook called twice")
                    injected[0] = True
                    if conflict:
                        external_snapshot[0] = self.write_snapshot_file(
                            baseline,
                            b"EXTERNAL-SNAPSHOT-RACE",
                            0o604,
                            1_700_000_000_000_000_000,
                        )
                    raise OSError("injected claim snapshot failure")

                with self.assertRaises(Exception) as caught:
                    visual_comparator._publish_approval(
                        baseline,
                        b"new-image",
                        metadata,
                        b"new-metadata",
                        operations={
                            "move": os.rename,
                            "link": os.link,
                            "snapshot": fail_claim_snapshot,
                        },
                    )

                self.assertTrue(injected[0])
                self.assert_file_snapshot(
                    baseline,
                    external_snapshot[0] if conflict else original_baseline,
                )
                self.assert_file_snapshot(metadata, original_metadata)
                temporary = [
                    path
                    for path in root.rglob("*")
                    if path.name.endswith((".tmp", ".bak"))
                ]
                self.assertEqual([], temporary)
                claims = [
                    path
                    for path in root.rglob("payload")
                    if ".claim-" in str(path.parent)
                ]
                if conflict:
                    self.assertIn("recovery claim preserved", str(caught.exception))
                    self.assertEqual(1, len(claims))
                    self.assertEqual(b"old-image", claims[0].read_bytes())
                else:
                    self.assertEqual([], claims)

    def test_approval_commit_cleanup_failure_never_rolls_back_published_pair(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            baseline = root / "baseline.png"
            metadata = root / "baseline.json"
            baseline.write_bytes(b"old-image")
            metadata.write_bytes(b"old-metadata")
            real_rmdir = os.rmdir
            cleanup_calls = [0]

            def fail_second_claim_directory_cleanup(directory):
                cleanup_calls[0] += 1
                if cleanup_calls[0] == 2:
                    raise OSError("injected committed cleanup failure")
                return real_rmdir(directory)

            with self.assertRaisesRegex(
                VisualComparisonError,
                "committed outputs retained",
            ):
                visual_comparator._publish_approval(
                    baseline,
                    b"new-image",
                    metadata,
                    b"new-metadata",
                    operations={
                        "move": os.rename,
                        "link": os.link,
                        "rmdir": fail_second_claim_directory_cleanup,
                    },
                )

            self.assertEqual(b"new-image", baseline.read_bytes())
            self.assertEqual(b"new-metadata", metadata.read_bytes())
            claim_residue = [path for path in root.rglob("*") if "claim" in path.name]
            self.assertEqual(1, len(claim_residue))

    def test_accept_rechecks_lock_index_and_source_before_output_publish(self):
        provenance_paths = (
            "package-lock.json",
            visual_comparator.INDEX_RELATIVE_PATH,
            visual_comparator.SOURCE_ASSET_PATHS[0],
        )
        for relative_path in provenance_paths:
            with self.subTest(relative_path=relative_path):
                with tempfile.TemporaryDirectory() as temp_dir:
                    root = Path(temp_dir).resolve()
                    repo_root = self.copy_capture_repository(root / "repo")
                    fixtures = root / "fixtures"
                    fixtures.mkdir()
                    candidate, candidate_metadata = self.write_capture_fixture(
                        fixtures,
                        "candidate",
                        repo_root=repo_root,
                    )
                    baseline = root / "baseline.png"
                    baseline_metadata = root / "baseline.json"
                    baseline_snapshot = self.write_snapshot_file(
                        baseline,
                        b"old-baseline-image",
                        0o640,
                        1_630_000_000_000_000_000,
                    )
                    metadata_snapshot = self.write_snapshot_file(
                        baseline_metadata,
                        b"old-baseline-metadata",
                        0o600,
                        1_630_000_001_000_000_000,
                    )
                    target = repo_root / relative_path
                    real_stage = visual_comparator._stage_approval_payload
                    injected = [False]

                    def stage_then_replace(*arguments, **keywords):
                        result = real_stage(*arguments, **keywords)
                        if not injected[0]:
                            injected[0] = True
                            self.atomically_replace_identity(target)
                        return result

                    with mock.patch.object(
                        visual_comparator,
                        "REPO_ROOT",
                        repo_root,
                    ), mock.patch.object(
                        visual_comparator,
                        "_stage_approval_payload",
                        side_effect=stage_then_replace,
                    ):
                        with self.assertRaises(VisualComparisonError):
                            visual_comparator.accept_candidate(
                                candidate,
                                candidate_metadata,
                                baseline,
                                baseline_metadata,
                                "reviewer",
                                "repository identity must remain current",
                            )

                    self.assertTrue(injected[0])
                    self.assert_file_snapshot(baseline, baseline_snapshot)
                    self.assert_file_snapshot(baseline_metadata, metadata_snapshot)
                    self.assert_no_publish_residue(root)

    def test_accept_rolls_back_pair_when_source_changes_after_first_replace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            repo_root = self.copy_capture_repository(root / "repo")
            fixtures = root / "fixtures"
            fixtures.mkdir()
            candidate, candidate_metadata = self.write_capture_fixture(
                fixtures,
                "candidate",
                repo_root=repo_root,
            )
            baseline = root / "baseline.png"
            baseline_metadata = root / "baseline.json"
            baseline_snapshot = self.write_snapshot_file(
                baseline,
                b"old-baseline-image",
                0o640,
                1_640_000_000_000_000_000,
            )
            metadata_snapshot = self.write_snapshot_file(
                baseline_metadata,
                b"old-baseline-metadata",
                0o600,
                1_640_000_001_000_000_000,
            )
            source_asset = repo_root / visual_comparator.SOURCE_ASSET_PATHS[0]
            real_link = os.link
            injected = [False]

            def install_then_change_source(source, target):
                result = real_link(source, target)
                if Path(target) == baseline and not injected[0]:
                    injected[0] = True
                    self.atomically_replace_identity(source_asset)
                return result

            with mock.patch.object(
                visual_comparator,
                "REPO_ROOT",
                repo_root,
            ), mock.patch.object(
                visual_comparator.os,
                "link",
                side_effect=install_then_change_source,
            ):
                with self.assertRaises(VisualComparisonError):
                    visual_comparator.accept_candidate(
                        candidate,
                        candidate_metadata,
                        baseline,
                        baseline_metadata,
                        "reviewer",
                        "rollback stale provenance",
                    )

            self.assertTrue(injected[0])
            self.assertEqual(baseline_snapshot[0], baseline.read_bytes())
            self.assertEqual(baseline_snapshot[1], baseline.stat().st_mode & 0o777)
            self.assertEqual(metadata_snapshot[0], baseline_metadata.read_bytes())
            self.assertEqual(
                metadata_snapshot[1],
                baseline_metadata.stat().st_mode & 0o777,
            )
            self.assert_no_publish_residue(root)

    def test_accept_rolls_back_pair_when_source_changes_after_second_replace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            repo_root = self.copy_capture_repository(root / "repo")
            fixtures = root / "fixtures"
            fixtures.mkdir()
            candidate, candidate_metadata = self.write_capture_fixture(
                fixtures,
                "candidate",
                repo_root=repo_root,
            )
            baseline = root / "baseline.png"
            baseline_metadata = root / "baseline.json"
            baseline_snapshot = self.write_snapshot_file(
                baseline,
                b"old-baseline-image",
                0o640,
                1_650_000_000_000_000_000,
            )
            metadata_snapshot = self.write_snapshot_file(
                baseline_metadata,
                b"old-baseline-metadata",
                0o600,
                1_650_000_001_000_000_000,
            )
            source_asset = repo_root / visual_comparator.SOURCE_ASSET_PATHS[0]
            real_link = os.link
            injected = [False]

            def install_then_change_source(source, target):
                result = real_link(source, target)
                if Path(target) == baseline_metadata and not injected[0]:
                    injected[0] = True
                    self.atomically_replace_identity(source_asset)
                return result

            with mock.patch.object(
                visual_comparator,
                "REPO_ROOT",
                repo_root,
            ), mock.patch.object(
                visual_comparator.os,
                "link",
                side_effect=install_then_change_source,
            ):
                with self.assertRaises(VisualComparisonError):
                    visual_comparator.accept_candidate(
                        candidate,
                        candidate_metadata,
                        baseline,
                        baseline_metadata,
                        "reviewer",
                        "rollback final stale provenance",
                    )

            self.assertTrue(injected[0])
            self.assertEqual(baseline_snapshot[0], baseline.read_bytes())
            self.assertEqual(baseline_snapshot[1], baseline.stat().st_mode & 0o777)
            self.assertEqual(metadata_snapshot[0], baseline_metadata.read_bytes())
            self.assertEqual(
                metadata_snapshot[1],
                baseline_metadata.stat().st_mode & 0o777,
            )
            self.assert_no_publish_residue(root)

    def test_normal_compare_rejects_symlink_diff_output_even_when_images_pass(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            baseline, baseline_metadata = self.write_capture_fixture(
                root, "baseline", approved=True
            )
            candidate, candidate_metadata = self.write_capture_fixture(root, "candidate")
            referent = root / "outside-diff.png"
            referent.write_bytes(b"unchanged")
            diff_output = root / "diff-link.png"
            try:
                diff_output.symlink_to(referent)
            except (NotImplementedError, OSError):
                self.skipTest("symlinks are unavailable")
            result = self.comparator_command(
                "--baseline", str(baseline),
                "--baseline-metadata", str(baseline_metadata),
                "--candidate", str(candidate),
                "--candidate-metadata", str(candidate_metadata),
                "--diff-output", str(diff_output),
            )
            self.assertEqual(2, result.returncode)
            self.assertIn("symlink", result.stderr)
            self.assertEqual(b"unchanged", referent.read_bytes())

    def test_accept_requires_stripped_reviewer_and_note_and_publishes_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            candidate, candidate_metadata = self.write_capture_fixture(root, "candidate")
            baseline = root / "approved" / "baseline.png"
            baseline_metadata = root / "approved" / "baseline.json"
            for arguments, label in (
                (("--reviewer", "   ", "--approval-note", "valid"), "reviewer"),
                (("--reviewer", "valid", "--approval-note", "  "), "approval note"),
            ):
                result = self.comparator_command(
                    "--accept",
                    *arguments,
                    "--candidate", str(candidate),
                    "--candidate-metadata", str(candidate_metadata),
                    "--baseline", str(baseline),
                    "--baseline-metadata", str(baseline_metadata),
                )
                self.assertNotEqual(0, result.returncode)
                self.assertIn(label, result.stderr)
                self.assertFalse(baseline.exists())
                self.assertFalse(baseline_metadata.exists())

            accepted = self.comparator_command(
                "--accept",
                "--reviewer", "  coolbat  ",
                "--approval-note", "  approved exact candidate  ",
                "--candidate", str(candidate),
                "--candidate-metadata", str(candidate_metadata),
                "--baseline", str(baseline),
                "--baseline-metadata", str(baseline_metadata),
            )
            self.assertEqual(0, accepted.returncode, accepted.stderr)
            self.assertEqual(candidate.read_bytes(), baseline.read_bytes())
            approval = json.loads(baseline_metadata.read_text(encoding="utf-8"))
            self.assertEqual("coolbat", approval["approval"]["reviewer"])
            self.assertEqual(
                "approved exact candidate", approval["approval"]["note"]
            )
            self.assertEqual(self.sha256(candidate), approval["approval"]["baseline_sha256"])
            self.assertEqual([], list(root.rglob("*.tmp")))

    def test_accept_rejects_non_linux_capture(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            candidate, candidate_metadata = self.write_capture_fixture(root, "candidate")
            payload = json.loads(candidate_metadata.read_text(encoding="utf-8"))
            payload["platform"] = {"os": "darwin", "arch": "arm64"}
            candidate_metadata.write_text(json.dumps(payload), encoding="utf-8")

            result = self.comparator_command(
                "--accept",
                "--reviewer", "reviewer",
                "--approval-note", "linux captures only",
                "--candidate", str(candidate),
                "--candidate-metadata", str(candidate_metadata),
                "--baseline", str(root / "baseline.png"),
                "--baseline-metadata", str(root / "baseline.json"),
            )

            self.assertEqual(2, result.returncode, result.stdout + result.stderr)
            self.assertIn("linux", result.stderr.lower())
            self.assertFalse((root / "baseline.png").exists())
            self.assertFalse((root / "baseline.json").exists())

    def test_approval_publish_rejects_external_image_rewrite_after_first_replace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            baseline = root / "baseline.png"
            baseline_metadata = root / "baseline.json"
            baseline.write_bytes(b"old-baseline-image")
            baseline_metadata.write_bytes(b"old-baseline-metadata")
            real_link = os.link
            injected = [False]

            def install_then_rewrite_first_target(source, target):
                result = real_link(source, target)
                if Path(target) == baseline and not injected[0]:
                    injected[0] = True
                    external = root / ".external-baseline"
                    external.write_bytes(b"EXTERNAL-IMAGE")
                    os.replace(str(external), str(baseline))
                return result

            with mock.patch.object(
                visual_comparator.os,
                "link",
                side_effect=install_then_rewrite_first_target,
            ):
                with self.assertRaisesRegex(
                    VisualComparisonError,
                    "rollback was incomplete",
                ) as caught:
                    visual_comparator._publish_approval(
                        baseline,
                        b"new-baseline-image",
                        baseline_metadata,
                        b"new-baseline-metadata",
                    )

            self.assertTrue(injected[0])
            self.assertIn("claim preserved", str(caught.exception))
            self.assertEqual(b"EXTERNAL-IMAGE", baseline.read_bytes())
            self.assertEqual(b"old-baseline-metadata", baseline_metadata.read_bytes())
            backups = [
                path
                for path in root.rglob("payload")
                if "claim" in path.parent.name
            ]
            self.assertEqual(1, len(backups))
            self.assertEqual(b"old-baseline-image", backups[0].read_bytes())
            self.assertEqual(
                [],
                [path for path in root.iterdir() if path.name.endswith(".tmp")],
            )

    def test_accept_uses_candidate_bytes_frozen_during_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            candidate, candidate_metadata = self.write_capture_fixture(root, "candidate")
            original = candidate.read_bytes()
            replacement = root / "replacement.png"
            self.solid_image((10, 10), (220, 10, 10, 255)).save(replacement)
            replacement_payload = replacement.read_bytes()
            baseline = root / "baseline.png"
            baseline_metadata = root / "baseline.json"
            real_validate = visual_comparator._validate_capture_metadata

            def replace_after_validation(
                metadata,
                image_path,
                label,
                require_approval=False,
                repository_provenance=None,
            ):
                result = real_validate(
                    metadata,
                    image_path,
                    label,
                    require_approval,
                    repository_provenance,
                )
                if label == "candidate":
                    Path(image_path).write_bytes(replacement_payload)
                return result

            with mock.patch.object(
                visual_comparator,
                "_validate_capture_metadata",
                side_effect=replace_after_validation,
            ):
                visual_comparator.accept_candidate(
                    candidate,
                    candidate_metadata,
                    baseline,
                    baseline_metadata,
                    "reviewer",
                    "frozen candidate bytes",
                )

            self.assertEqual(original, baseline.read_bytes())

    def test_accept_rolls_back_both_files_if_second_replace_succeeds_then_raises(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            candidate, candidate_metadata = self.write_capture_fixture(root, "candidate")
            baseline, baseline_metadata = self.write_capture_fixture(
                root,
                "baseline",
                color=(70, 80, 90, 255),
                approved=True,
            )
            before = baseline.read_bytes(), baseline_metadata.read_bytes()
            real_link = os.link
            calls = 0

            def second_install_succeeds_then_raises(source, target):
                nonlocal calls
                calls += 1
                result = real_link(source, target)
                if calls == 2:
                    raise OSError("injected failure after metadata install")
                return result

            with mock.patch.object(
                visual_comparator.os,
                "link",
                side_effect=second_install_succeeds_then_raises,
            ):
                with self.assertRaisesRegex(OSError, "after metadata install"):
                    visual_comparator.accept_candidate(
                        candidate,
                        candidate_metadata,
                        baseline,
                        baseline_metadata,
                        "reviewer",
                        "approval note",
                    )

            self.assertEqual(before, (baseline.read_bytes(), baseline_metadata.read_bytes()))
            self.assertEqual([], list(root.rglob("*.tmp")))

    def test_accept_rejects_path_aliases_and_symlink_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            candidate, candidate_metadata = self.write_capture_fixture(root, "candidate")
            alias = self.comparator_command(
                "--accept",
                "--reviewer", "reviewer",
                "--approval-note", "note",
                "--candidate", str(candidate),
                "--candidate-metadata", str(candidate_metadata),
                "--baseline", str(candidate),
                "--baseline-metadata", str(root / "baseline.json"),
            )
            self.assertNotEqual(0, alias.returncode)
            self.assertIn("alias", alias.stderr)

            symlink = root / "candidate-link.png"
            try:
                symlink.symlink_to(candidate)
            except (NotImplementedError, OSError):
                self.skipTest("symlinks are unavailable")
            rejected = self.comparator_command(
                "--accept",
                "--reviewer", "reviewer",
                "--approval-note", "note",
                "--candidate", str(symlink),
                "--candidate-metadata", str(candidate_metadata),
                "--baseline", str(root / "baseline.png"),
                "--baseline-metadata", str(root / "baseline.json"),
            )
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn("symlink", rejected.stderr)

    def test_direct_target_symlink_is_rejected_without_touching_referent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            external = root / "external.svg"
            external.write_bytes(b"external-original")
            output = root / "sheet.svg"
            output.symlink_to(external)
            html_output = root / "index.html"
            recognition_output = root / "recognition.html"
            cell_index = root / "cell-index.json"

            result = self.benchmark_generator_command(
                output,
                html_output,
                recognition_output,
                cell_index,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertTrue(output.is_symlink())
            self.assertEqual(b"external-original", external.read_bytes())
            for path in (html_output, recognition_output, cell_index):
                self.assertFalse(path.exists())
            self.assert_no_publish_residue(root)

    def test_parent_symlink_alias_is_rejected_before_any_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            real_parent = root / "real"
            real_parent.mkdir()
            alias_parent = root / "alias"
            alias_parent.symlink_to(real_parent, target_is_directory=True)
            output = root / "sheet.svg"
            html_output = real_parent / "review.html"
            recognition_output = alias_parent / "review.html"
            cell_index = root / "cell-index.json"

            result = self.benchmark_generator_command(
                output,
                html_output,
                recognition_output,
                cell_index,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertFalse(output.exists())
            self.assertFalse(html_output.exists())
            self.assertFalse(cell_index.exists())
            self.assertTrue(alias_parent.is_symlink())
            self.assert_no_publish_residue(root)

    def test_hardlink_alias_is_rejected_without_partial_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "sheet.svg"
            html_output = root / "index.html"
            recognition_output = root / "recognition.html"
            cell_index = root / "cell-index.json"
            html_output.write_bytes(b"shared-original")
            os.link(html_output, recognition_output)

            result = self.benchmark_generator_command(
                output,
                html_output,
                recognition_output,
                cell_index,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertEqual(b"shared-original", html_output.read_bytes())
            self.assertEqual(b"shared-original", recognition_output.read_bytes())
            self.assertTrue(os.path.samefile(html_output, recognition_output))
            self.assertFalse(output.exists())
            self.assertFalse(cell_index.exists())
            self.assert_no_publish_residue(root)

    def test_publish_replace_failure_rolls_back_bytes_modes_and_new_files(self):
        publisher = getattr(contact_sheet_generator, "_publish_outputs", None)
        self.assertIsNotNone(publisher, "generator must expose transactional publisher")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "one.svg"
            second = root / "two.html"
            third = root / "three.html"
            fourth = root / "four.json"
            first.write_bytes(b"old-one")
            third.write_bytes(b"old-three")
            first.chmod(0o640)
            third.chmod(0o600)
            real_replace = os.replace
            calls = 0

            def fail_third_replace(source, target):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("simulated third replace failure")
                return real_replace(source, target)

            outputs = (
                (first, b"new-one"),
                (second, b"new-two"),
                (third, b"new-three"),
                (fourth, b"new-four"),
            )
            with mock.patch.object(
                contact_sheet_generator.os,
                "replace",
                side_effect=fail_third_replace,
            ):
                with self.assertRaisesRegex(OSError, "third replace"):
                    publisher(outputs)

            self.assertGreaterEqual(calls, 3)
            self.assertEqual(b"old-one", first.read_bytes())
            self.assertEqual(0o640, first.stat().st_mode & 0o777)
            self.assertFalse(second.exists())
            self.assertEqual(b"old-three", third.read_bytes())
            self.assertEqual(0o600, third.stat().st_mode & 0o777)
            self.assertFalse(fourth.exists())
            self.assert_no_publish_residue(root)

    def test_failure_does_not_touch_unattempted_externally_updated_target(self):
        publisher = contact_sheet_generator._publish_outputs
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            targets = tuple(root / name for name in (
                "one.svg",
                "two.html",
                "three.html",
                "four.json",
            ))
            originals = tuple(
                self.write_snapshot_file(
                    path,
                    "old-{0}".format(index).encode("ascii"),
                    0o640 + index,
                    1_600_000_000_000_000_000 + index * 1_000_000_000,
                )
                for index, path in enumerate(targets)
            )
            external_snapshot = None
            real_replace = os.replace
            calls = 0

            def fail_third_before_replace(source, target):
                nonlocal calls, external_snapshot
                calls += 1
                if calls == 3:
                    external_snapshot = self.write_snapshot_file(
                        targets[3],
                        b"EXTERNAL-UPDATE",
                        0o604,
                        1_700_000_000_000_000_000,
                    )
                    raise OSError("third replace failed before publish")
                return real_replace(source, target)

            outputs = tuple(
                (path, "new-{0}".format(index).encode("ascii"))
                for index, path in enumerate(targets)
            )
            with mock.patch.object(
                contact_sheet_generator.os,
                "replace",
                side_effect=fail_third_before_replace,
            ):
                with self.assertRaisesRegex(OSError, "before publish"):
                    publisher(outputs)

            for path, expected in zip(targets[:3], originals[:3]):
                self.assert_file_snapshot(path, expected)
            self.assertIsNotNone(external_snapshot)
            self.assert_file_snapshot(targets[3], external_snapshot)
            self.assert_no_publish_residue(root)

    def test_publish_rejects_same_stat_external_update_before_next_replace(self):
        publisher = contact_sheet_generator._publish_outputs
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            targets = tuple(root / name for name in (
                "one.svg",
                "two.html",
                "three.html",
                "four.json",
            ))
            originals = tuple(
                self.write_snapshot_file(
                    path,
                    payload,
                    0o640 + index,
                    1_605_000_000_000_000_000 + index * 1_000_000_000,
                )
                for index, (path, payload) in enumerate(zip(
                    targets,
                    (b"AAAA", b"BBBB", b"CCCC", b"DDDD"),
                ))
            )
            real_replace = os.replace
            external_snapshot = None
            injected = False

            def inject_same_stat_update_after_first_publish(source, target):
                nonlocal external_snapshot, injected
                if Path(target) == targets[0] and not injected:
                    injected = True
                    external_snapshot = self.write_snapshot_file(
                        targets[1],
                        b"XXXX",
                        originals[1][1],
                        originals[1][2],
                    )
                return real_replace(source, target)

            outputs = tuple(
                (path, "new-{0}".format(index).encode("ascii"))
                for index, path in enumerate(targets)
            )
            with mock.patch.object(
                contact_sheet_generator.os,
                "replace",
                side_effect=inject_same_stat_update_after_first_publish,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "existing output changed before publish",
                ):
                    publisher(outputs)

            self.assertTrue(injected)
            self.assertIsNotNone(external_snapshot)
            self.assert_file_snapshot(targets[0], originals[0])
            self.assert_file_snapshot(targets[1], external_snapshot)
            for path, expected in zip(targets[2:], originals[2:]):
                self.assert_file_snapshot(path, expected)
            self.assert_no_publish_residue(root)

    def test_rollback_conflict_preserves_external_update_and_old_backup(self):
        publisher = contact_sheet_generator._publish_outputs
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            targets = tuple(root / name for name in (
                "one.svg",
                "two.html",
                "three.html",
                "four.json",
            ))
            originals = tuple(
                self.write_snapshot_file(
                    path,
                    "old-{0}".format(index).encode("ascii"),
                    0o640 + index,
                    1_610_000_000_000_000_000 + index * 1_000_000_000,
                )
                for index, path in enumerate(targets)
            )
            external_snapshot = None
            real_replace = os.replace
            calls = 0

            def corrupt_first_then_fail_third(source, target):
                nonlocal calls, external_snapshot
                calls += 1
                if calls == 3:
                    external_snapshot = self.write_snapshot_file(
                        targets[0],
                        b"EXTERNAL-FIRST",
                        0o604,
                        1_710_000_000_000_000_000,
                    )
                    raise OSError("third replace exposed rollback conflict")
                return real_replace(source, target)

            outputs = tuple(
                (path, "new-{0}".format(index).encode("ascii"))
                for index, path in enumerate(targets)
            )
            with mock.patch.object(
                contact_sheet_generator.os,
                "replace",
                side_effect=corrupt_first_then_fail_third,
            ):
                with self.assertRaises(Exception) as caught:
                    publisher(outputs)

            self.assertIsInstance(caught.exception, RuntimeError)
            self.assertIn("rollback was incomplete", str(caught.exception))
            self.assertIsNotNone(external_snapshot)
            self.assert_file_snapshot(targets[0], external_snapshot)
            for path, expected in zip(targets[1:], originals[1:]):
                self.assert_file_snapshot(path, expected)
            backups = [path for path in root.iterdir() if path.name.endswith(".bak")]
            self.assertEqual(1, len(backups))
            self.assert_file_snapshot(backups[0], originals[0])
            message = str(caught.exception)
            self.assertIn(str(targets[0]), message)
            self.assertIn(str(backups[0]), message)
            self.assertEqual(
                [],
                [path for path in root.iterdir() if path.name.endswith(".tmp")],
            )

    def test_replace_that_succeeds_then_raises_is_safely_rolled_back(self):
        publisher = contact_sheet_generator._publish_outputs
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "one.svg"
            second = root / "two.html"
            third = root / "three.html"
            fourth = root / "four.json"
            first_snapshot = self.write_snapshot_file(
                first,
                b"old-one",
                0o640,
                1_620_000_000_000_000_000,
            )
            third_snapshot = self.write_snapshot_file(
                third,
                b"old-three",
                0o600,
                1_620_000_001_000_000_000,
            )
            fourth_snapshot = self.write_snapshot_file(
                fourth,
                b"old-four",
                0o604,
                1_620_000_002_000_000_000,
            )
            real_replace = os.replace
            calls = 0

            def fail_after_third_replace(source, target):
                nonlocal calls
                calls += 1
                result = real_replace(source, target)
                if calls == 3:
                    raise OSError("third replace raised after publish")
                return result

            outputs = (
                (first, b"new-one"),
                (second, b"new-two"),
                (third, b"new-three"),
                (fourth, b"new-four"),
            )
            with mock.patch.object(
                contact_sheet_generator.os,
                "replace",
                side_effect=fail_after_third_replace,
            ):
                with self.assertRaisesRegex(OSError, "after publish"):
                    publisher(outputs)

            self.assert_file_snapshot(first, first_snapshot)
            self.assertFalse(second.exists())
            self.assert_file_snapshot(third, third_snapshot)
            self.assert_file_snapshot(fourth, fourth_snapshot)
            self.assert_no_publish_residue(root)


if __name__ == "__main__":
    unittest.main()

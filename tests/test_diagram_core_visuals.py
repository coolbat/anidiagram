import copy
import itertools
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock
from xml.etree import ElementTree

from anidiagram.diagram_core.tokens import contrast_ratio
from scripts import render_diagram_core_contact_sheet as contact_sheet_generator


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_diagram_core_contact_sheet.py"
TOKENS_PATH = ROOT / "assets" / "diagram-core" / "tokens.css"
ICONS = ("agent", "database", "api", "server")
SIZES = (48, 64, 96)
CONTEXTS = ("blue", "dark", "warm", "green")
STATES = ("idle", "active", "processing", "success", "warning", "error")
ASSET_LOCAL_TOKENS = {"--icon-surface-contrast"}
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
            if path.name.endswith((".tmp", ".bak"))
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
            "icons=1 cells=72 unique=72 sizes=48,64,96 "
            "contexts=blue,dark,warm,green states=6\nOK\n",
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
            "icons=4 cells=288 unique=288 sizes=48,64,96 "
            "contexts=blue,dark,warm,green states=6\nOK\n",
            result.stdout,
        )
        for path in (output, html_output, recognition_output, cell_index):
            self.assertTrue(path.is_file(), path)
            self.assertEqual(0o644, path.stat().st_mode & 0o777)
        return output, html_output, recognition_output, cell_index

    def test_benchmark_is_exact_ordered_288_cell_product_and_index_matches_dom(self):
        expected = [
            (icon_id, size, context, state)
            for context, state, icon_id, size in itertools.product(
                CONTEXTS,
                STATES,
                ICONS,
                SIZES,
            )
        ]
        self.assertEqual(288, len(expected))
        self.assertEqual(288, len(set(expected)))
        with tempfile.TemporaryDirectory() as temp_dir:
            output, html_output, _, cell_index = self.generate_benchmark(temp_dir)
            root = ElementTree.parse(output).getroot()
            self.assertEqual("diagram-core-regression-grid", root.attrib.get("id"))
            self.assertEqual("12", root.attrib.get("data-grid-columns"))
            self.assertEqual("24", root.attrib.get("data-grid-rows"))
            self.assertEqual("288", root.attrib.get("data-cell-count"))
            self.assertEqual("1248", root.attrib.get("width"))
            self.assertEqual("2496", root.attrib.get("height"))
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
                    cell.attrib["data-state"],
                )
                for cell in cells
            ]
            self.assertEqual(expected, actual)
            cell_ids = [cell.attrib["data-cell-id"] for cell in cells]
            self.assertEqual(288, len(set(cell_ids)))

            index = json.loads(cell_index.read_text(encoding="utf-8"))
            self.assertEqual(1, index["version"])
            self.assertEqual({"columns": 12, "rows": 24, "cells": 288}, index["grid"])
            self.assertEqual(
                [
                    {
                        "ordinal": ordinal,
                        "cell_id": cell_ids[ordinal],
                        "icon_id": icon_id,
                        "size": size,
                        "context": context,
                        "state": state,
                    }
                    for ordinal, (icon_id, size, context, state) in enumerate(expected)
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
            for label in ICONS + CONTEXTS + STATES:
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

    def test_recognition_surfaces_keep_four_silhouettes_and_six_state_geometries(self):
        modes = ("label-hidden", "accent-off", "grayscale", "node-context")
        with tempfile.TemporaryDirectory() as temp_dir:
            _, _, recognition_output, _ = self.generate_benchmark(temp_dir)
            source = recognition_output.read_text(encoding="utf-8")
            audit = StaticGridHTMLAudit()
            audit.feed(source)
            self.assertEqual([], audit.review_region_text)
            self.assertEqual(96, len(audit.recognition_cells))
            for mode in modes:
                cells = [
                    cell
                    for cell in audit.recognition_cells
                    if cell["data-recognition-mode"] == mode
                ]
                self.assertEqual(24, len(cells), mode)
                self.assertEqual(
                    set(itertools.product(ICONS, STATES)),
                    {
                        (cell["data-icon-id"], cell["data-state"])
                        for cell in cells
                    },
                )
                self.assertEqual({"48"}, {cell["data-size"] for cell in cells})
                self.assertTrue(all(cell.get("aria-label", "").strip() for cell in cells))

            ids = [
                attributes["id"]
                for _, attributes in audit.attributes
                if "id" in attributes
            ]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertNotRegex(source.lower(), r"\bfilter\s*:")

    def test_each_icon_has_six_distinct_rendered_state_geometry_signatures(self):
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
            for icon_id in ICONS:
                signatures = {}
                for state in STATES:
                    cell = next(
                        cell
                        for cell in cells
                        if cell.attrib["data-icon-id"] == icon_id
                        and cell.attrib["data-state"] == state
                    )
                    wrapper = next(
                        element
                        for element in cell.iter()
                        if element.attrib.get("data-icon-source") == "diagram-core-v1"
                    )
                    state_marks = [
                        element
                        for element in wrapper.iter()
                        if element.attrib.get("data-state-mark") == state
                    ]
                    self.assertEqual(1, len(state_marks), (icon_id, state))
                    signatures[state] = geometry_signature(copy.deepcopy(state_marks[0]))
                self.assertEqual(6, len(set(signatures.values())), icon_id)

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
            self.assertEqual(72, len(cells))
            cell_ids = [cell.attrib["data-cell-id"] for cell in cells]
            self.assertEqual(72, len(set(cell_ids)))
            self.assertEqual(set(SIZES), {int(cell.attrib["data-size"]) for cell in cells})
            self.assertEqual(set(CONTEXTS), {cell.attrib["data-context"] for cell in cells})
            self.assertEqual(set(STATES), {cell.attrib["data-state"] for cell in cells})
            self.assertEqual(
                {
                    (size, context, state)
                    for size in SIZES
                    for context in CONTEXTS
                    for state in STATES
                },
                {
                    (
                        int(cell.attrib["data-size"]),
                        cell.attrib["data-context"],
                        cell.attrib["data-state"],
                    )
                    for cell in cells
                },
            )
            style_text = "\n".join(
                element.text or ""
                for element in root.iter()
                if local_name(element.tag) == "style"
            )
            self.assertEqual(
                "none",
                css_declarations(style_text, "[data-state-mark]")["display"],
            )
            for state in STATES:
                selector = '[data-icon-state="{0}"] [data-state-mark="{0}"]'.format(
                    state
                )
                self.assertEqual(
                    "inline",
                    css_declarations(style_text, selector)["display"],
                )

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
                    self.assertEqual(cell.attrib["data-state"], wrapper.attrib["data-icon-state"])
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
                    self.assertIn(cell.attrib["data-state"], label)

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
                self.assertEqual(set(STATES), {cell.attrib["data-state"] for cell in cells})
                self.assertEqual(6, len(cells))
                for cell in cells:
                    label = " ".join(
                        element.text or ""
                        for element in cell.iter()
                        if local_name(element.tag) == "text"
                    )
                    compact_mode = "off" if mode == "accent-off" else "gray"
                    self.assertEqual(
                        "48px · {0} · {1}".format(compact_mode, cell.attrib["data-state"]),
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
                "six state marks",
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

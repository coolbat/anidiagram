import os
import re
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

from anidiagram.diagram_core.tokens import contrast_ratio


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_diagram_core_contact_sheet.py"
TOKENS_PATH = ROOT / "assets" / "diagram-core" / "tokens.css"
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


class DiagramCoreVisualReviewTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

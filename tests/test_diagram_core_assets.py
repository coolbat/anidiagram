import copy
import gzip
import json
import math
import random
import re
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

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
from anidiagram.diagram_core.tokens import (
    contrast_ratio,
    icon_tokens_for_style,
    relative_luminance,
    token_css,
)
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]

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

STATE_MARK_GEOMETRY = (
    ("idle", "dot"),
    ("active", "ring"),
    ("processing", "split-arc"),
    ("success", "check"),
    ("warning", "triangle"),
    ("error", "X"),
)


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


class DiagramCoreTokenTest(unittest.TestCase):
    def test_token_css_defines_approved_defaults_and_four_review_contexts(self):
        source = token_css()

        self.assertTrue(REQUIRED_ICON_TOKENS.issubset(declared_tokens(source)))
        root_tokens = css_declarations(source, ":root")
        for token, value in APPROVED_ICON_DEFAULTS.items():
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


if __name__ == "__main__":
    unittest.main()

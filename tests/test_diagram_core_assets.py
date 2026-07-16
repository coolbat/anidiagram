import copy
import gzip
import json
import math
import random
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from anidiagram.diagram_core.asset_loader import (
    AssetValidationError,
    load_asset,
    load_svg_source,
)
from anidiagram.diagram_core.manifest import (
    ManifestValidationError,
    load_manifest,
    validate_manifest_dict,
)


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


if __name__ == "__main__":
    unittest.main()

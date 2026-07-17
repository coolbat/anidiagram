import copy
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from anidiagram.diagram_core.adapter import (
    namespace_svg_instance,
    render_approved_icon,
    render_preview_icon,
)
from anidiagram.diagram_core.asset_loader import AssetValidationError, load_asset
from anidiagram.diagram_core.instance_ids import (
    decode_instance_key,
    instance_key,
    part_dom_id,
)


ROOT = Path(__file__).resolve().parents[1]
PART_CHECKER = ROOT / "scripts" / "check_diagram_core_parts.py"
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
URL_REFERENCE = re.compile(
    r"url\s*\(\s*(?:['\"])?#([^\s)'\"]+)(?:['\"])?\s*\)",
    re.IGNORECASE,
)
TOKEN_VALUES = {
    "--icon-status-warning": "#f3a53a",
    "--icon-status-error": "#e65b65",
    "--icon-surface-main": "#fffaf2",
    "--icon-accent-secondary": "#45c5bd",
    "--icon-status-idle": "#94a3b8",
    "--icon-stroke": "#14213d",
    "--icon-status-success": "#35b66f",
    "--icon-detail": "#64748b",
    "--icon-status-active": "#38bdf8",
    "--icon-surface-secondary": "#eef1f5",
    "--icon-surface-recessed": "#dfe5ec",
    "--icon-accent": "#7c5ce7",
}

CANONICAL_BENCHMARK_PARTS = {
    "agent": (
        "body",
        "shell",
        "face-screen",
        "eye-left",
        "eye-right",
        "mouth",
        "antenna",
        "core",
        "indicator",
    ),
    "database": (
        "body",
        "shell",
        "top-ring",
        "layer-top",
        "layer-middle",
        "layer-bottom",
        "core",
        "indicator",
    ),
    "api": (
        "body",
        "shell",
        "header",
        "input-interface",
        "output-interface",
        "processor",
        "indicator-group",
    ),
    "server": (
        "body",
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


def run_part_checker(*arguments):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, str(PART_CHECKER), *arguments],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def load_part_checker_module():
    spec = importlib.util.spec_from_file_location("diagram_core_part_checker", PART_CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def adapter_asset_tree_snapshot(asset_root):
    return {
        path.relative_to(asset_root).as_posix(): (
            path.read_bytes(),
            path.stat().st_mode,
            path.stat().st_mtime_ns,
        )
        for path in sorted(asset_root.rglob("*"))
        if path.is_file()
    }


def local_name(name):
    return name.rsplit("}", 1)[-1]


def parse_single_root(markup):
    return ElementTree.fromstring(markup)


def parse_svg_fragment(markup):
    return ElementTree.fromstring(
        '<svg xmlns="{0}">{1}</svg>'.format(SVG_NAMESPACE, markup)
    )


def synthetic_agent_svg():
    parts = (
        "shell",
        "face-screen",
        "eye-left",
        "eye-right",
        "mouth",
        "antenna",
        "core",
        "indicator",
    )
    children = []
    for index, part in enumerate(parts):
        children.append(
            '  <g data-part="{0}"><circle cx="{1}" cy="48" r="2" '
            'fill="var(--icon-surface-main, #fffaf2)" '
            'stroke="var(--icon-stroke, #14213d)"/></g>'.format(
                part,
                12 + index * 10,
            )
        )
    return (
        '<svg xmlns="{0}" viewBox="0 0 96 96" role="img" '
        'focusable="false" aria-label="Synthetic agent icon" data-icon="agent">\n'
        '  <g data-part="body">\n{1}\n  </g>\n</svg>\n'
    ).format(SVG_NAMESPACE, "\n".join(children))


class SyntheticAgentBundle:
    def __init__(self, root):
        self.root = Path(root)
        self.catalog_path = self.root / "catalog.json"
        self.manifest_path = self.root / "manifests" / "agent.json"
        self.icon_path = self.root / "icons" / "agent.svg"
        self.tokens_path = self.root / "tokens.css"
        self._catalog = json.loads(
            (ROOT / "assets" / "diagram-core" / "catalog.json").read_text(
                encoding="utf-8"
            )
        )

    def write(self, status="visual-review"):
        (self.root / "icons").mkdir(parents=True, exist_ok=True)
        (self.root / "manifests").mkdir(parents=True, exist_ok=True)
        catalog = copy.deepcopy(self._catalog)
        entry = next(icon for icon in catalog["icons"] if icon["id"] == "agent")
        entry["status"] = status
        self.catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        manifest = {
            "id": entry["id"],
            "system": "diagram-core-v1",
            "asset_revision": entry["asset_revision"],
            "viewBox": "0 0 96 96",
            "category": entry["category"],
            "semantic_kind": entry["semantic_kind"],
            "structural_prototype": entry["structural_prototype"],
            "parts": entry["parts"],
            "attachments": {
                "receive": {"x": 18, "y": 48},
                "send": {"x": 78, "y": 48},
                "status": {"x": 48, "y": 74},
            },
            "states": entry["supported_states"],
            "actions": entry["supported_actions"],
            "status": status,
        }
        self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.icon_path.write_text(synthetic_agent_svg(), encoding="utf-8")
        declarations = "\n".join(
            "  {0}: {1};".format(token, value)
            for token, value in sorted(TOKEN_VALUES.items())
        )
        self.tokens_path.write_text(
            ":root {\n" + declarations + "\n}\n",
            encoding="utf-8",
        )
        return self


def referenced_ids(root):
    references = {"href": [], "url": [], "aria": []}
    for element in root.iter():
        for raw_name, value in element.attrib.items():
            name = local_name(raw_name).lower()
            if name == "href":
                if value.startswith("#"):
                    references["href"].append(value[1:])
            if name in {"aria-labelledby", "aria-describedby"}:
                references["aria"].extend(value.split())
            references["url"].extend(URL_REFERENCE.findall(value))
        if element.text:
            references["url"].extend(URL_REFERENCE.findall(element.text))
    return references


class DiagramCoreInstanceIdTest(unittest.TestCase):
    def test_instance_keys_are_collision_safe_and_have_no_dom_separator(self):
        values = (
            "db.a",
            "db-a",
            "db a",
            "DB-A",
            "数据库 1",
            "数据库-1",
            "agent🙂left",
            "agent🙂🔥left",
            "1agent",
            "_n1agent",
        )

        keys = tuple(instance_key(value) for value in values)

        self.assertEqual(len(values), len(set(keys)))
        self.assertTrue(all("__" not in key for key in keys))

    def test_instance_keys_round_trip_ascii_unicode_emoji_and_adjacent_escapes(self):
        values = (
            "Agent42",
            "007",
            "数据库🙂",
            "a._-🙂Z",
            "é",
            "e\u0301",
            "🙂🔥🧠",
        )

        for value in values:
            with self.subTest(value=value):
                key = instance_key(value)
                self.assertEqual(value, decode_instance_key(key))

        self.assertEqual("Agent42", instance_key("Agent42"))
        self.assertTrue(instance_key("007").startswith("_n"))

    def test_instance_keys_reject_empty_controls_surrogates_and_non_strings(self):
        invalid_values = (
            None,
            7,
            "",
            "line\nbreak",
            "delete\x7f",
            "next\u0085line",
            "high\ud800surrogate",
            "low\udfffsurrogate",
        )

        for value in invalid_values:
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    instance_key(value)

    def test_part_dom_ids_have_exactly_three_strict_reversible_segments(self):
        identifier = part_dom_id("数据库.1", "agent", "eye-left")

        key, icon_id, part_name = identifier.split("__")
        self.assertEqual("数据库.1", decode_instance_key(key))
        self.assertEqual("agent", icon_id)
        self.assertEqual("eye-left", part_name)
        self.assertEqual(2, identifier.count("__"))

        invalid_pairs = (
            ("", "root"),
            ("Agent", "root"),
            ("agent_1", "root"),
            ("agent", ""),
            ("agent", "Root"),
            ("agent", "eye--left"),
            ("agent", "eye_left"),
        )
        for icon_id, part_name in invalid_pairs:
            with self.subTest(icon_id=icon_id, part_name=part_name):
                with self.assertRaises(ValueError):
                    part_dom_id("instance", icon_id, part_name)


class DiagramCoreAdapterTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.bundle = SyntheticAgentBundle(self.temp_dir.name).write()
        loaded = load_asset("agent", {"visual-review"}, self.bundle.root)
        self.assertEqual(
            (
                "body",
                "shell",
                "face-screen",
                "eye-left",
                "eye-right",
                "mouth",
                "antenna",
                "core",
                "indicator",
            ),
            loaded.public_parts,
        )

    def test_preview_clones_canonical_children_and_is_deterministic(self):
        source_before = self.bundle.icon_path.read_bytes()

        markup = render_preview_icon(
            "agent",
            "数据库.1",
            size=64,
            x=12.5,
            y=-0.0,
            tokens=TOKEN_VALUES,
            asset_root=self.bundle.root,
        )
        second_markup = render_preview_icon(
            "agent",
            "数据库.1",
            size=64,
            x=12.5,
            y=-0.0,
            tokens=TOKEN_VALUES,
            asset_root=self.bundle.root,
        )

        self.assertEqual(markup, second_markup)
        self.assertEqual(source_before, self.bundle.icon_path.read_bytes())
        root = parse_single_root(markup)
        self.assertEqual("g", local_name(root.tag))
        self.assertFalse(any(local_name(element.tag) == "svg" for element in root.iter()))
        self.assertEqual(part_dom_id("数据库.1", "agent", "root"), root.attrib["id"])
        self.assertEqual("agent", root.attrib["data-icon"])
        self.assertNotIn("data-icon-state", root.attrib)
        self.assertEqual("diagram-core-v1", root.attrib["data-icon-source"])
        self.assertEqual("2", root.attrib["data-asset-revision"])
        self.assertEqual("true", root.attrib["aria-hidden"])
        self.assertEqual(
            "translate(12.5 0) scale(0.666666666666667)",
            root.attrib["transform"],
        )
        self.assertNotIn("aria-label", root.attrib)
        self.assertNotIn("role", root.attrib)
        self.assertNotIn("viewBox", root.attrib)
        self.assertEqual(
            ";".join(
                "{0}:{1}".format(token, value)
                for token, value in sorted(TOKEN_VALUES.items())
            ),
            root.attrib["style"],
        )

        parts = {
            element.attrib["data-part"]: element.attrib["id"]
            for element in root.iter()
            if "data-part" in element.attrib
        }
        self.assertEqual(9, len(parts))
        for part_name, identifier in parts.items():
            self.assertEqual(
                part_dom_id("数据库.1", "agent", part_name),
                identifier,
            )
        identifiers = [
            element.attrib["id"] for element in root.iter() if "id" in element.attrib
        ]
        self.assertEqual(10, len(identifiers))
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertTrue(all(identifier.count("__") == 2 for identifier in identifiers))

    def test_repeated_instances_have_disjoint_root_and_part_ids(self):
        first_markup = render_preview_icon(
            "agent",
            "agent.left",
            asset_root=self.bundle.root,
        )
        second_markup = render_preview_icon(
            "agent",
            "agent-left",
            asset_root=self.bundle.root,
        )
        document = parse_svg_fragment(first_markup + second_markup)
        roots = list(document)

        self.assertEqual(2, len(roots))
        id_sets = [
            {element.attrib["id"] for element in root.iter() if "id" in element.attrib}
            for root in roots
        ]
        self.assertTrue(id_sets[0])
        self.assertTrue(id_sets[1])
        self.assertTrue(id_sets[0].isdisjoint(id_sets[1]))
        all_ids = id_sets[0] | id_sets[1]
        self.assertEqual(20, len(all_ids))
        self.assertTrue(all(identifier.count("__") == 2 for identifier in all_ids))
        for root, instance_id in zip(roots, ("agent.left", "agent-left")):
            for element in root.iter():
                part_name = element.attrib.get("data-part")
                if part_name is not None:
                    self.assertEqual(
                        part_dom_id(instance_id, "agent", part_name),
                        element.attrib["id"],
                    )

    def test_preview_and_approved_entry_points_enforce_distinct_status_gates(self):
        render_preview_icon("agent", "review", asset_root=self.bundle.root)
        with self.assertRaises(AssetValidationError):
            render_approved_icon("agent", "scene", asset_root=self.bundle.root)

        self.bundle.write(status="approved")
        render_preview_icon("agent", "review", asset_root=self.bundle.root)
        render_approved_icon("agent", "scene", asset_root=self.bundle.root)

        self.bundle.write(status="deprecated")
        with self.assertRaises(AssetValidationError):
            render_preview_icon("agent", "review", asset_root=self.bundle.root)
        with self.assertRaises(AssetValidationError):
            render_approved_icon("agent", "scene", asset_root=self.bundle.root)

    def test_explicit_state_identity_numbers_and_size_fail_closed(self):
        invalid_states = ("idle", "", "Processing", "not-supported", "idle\n")
        for state in invalid_states:
            with self.subTest(state=repr(state)):
                with self.assertRaises(ValueError):
                    render_preview_icon(
                        "agent",
                        "state-test",
                        state=state,
                        asset_root=self.bundle.root,
                    )

        invalid_identities = (
            ("", "instance"),
            ("Agent", "instance"),
            ("agent_1", "instance"),
            ("agent", ""),
            ("agent", "line\nbreak"),
            ("agent", "bad\ud800instance"),
        )
        for icon_id, instance_id in invalid_identities:
            with self.subTest(icon_id=icon_id, instance_id=repr(instance_id)):
                with self.assertRaises(ValueError):
                    render_preview_icon(
                        icon_id,
                        instance_id,
                        asset_root=self.bundle.root,
                    )

        invalid_numbers = (
            {"x": None},
            {"x": True},
            {"x": float("nan")},
            {"x": float("inf")},
            {"y": float("-inf")},
            {"size": False},
            {"size": float("nan")},
            {"size": float("inf")},
            {"size": 0},
            {"size": -1},
        )
        for values in invalid_numbers:
            with self.subTest(values=repr(values)):
                with self.assertRaises(ValueError):
                    render_preview_icon(
                        "agent",
                        "number-test",
                        asset_root=self.bundle.root,
                        **values
                    )

    def test_token_keys_and_opaque_values_fail_closed(self):
        render_preview_icon(
            "agent",
            "tokens",
            tokens={"--icon-accent": "rgb(1, 2, 3)"},
            asset_root=self.bundle.root,
        )
        invalid_tokens = (
            [],
            {"--unknown-token": "#fff"},
            {"--icon-accent": None},
            {"--icon-accent": "red"},
            {"--icon-accent": "rgba(1, 2, 3, 0.5)"},
            {"--icon-accent": "#fff;stroke:red"},
            {"--icon-accent": "rgb(256, 0, 0)"},
        )
        for tokens in invalid_tokens:
            with self.subTest(tokens=repr(tokens)):
                with self.assertRaises(ValueError):
                    render_preview_icon(
                        "agent",
                        "tokens",
                        tokens=tokens,
                        asset_root=self.bundle.root,
                    )

    def test_canonical_benchmarks_render_authored_rest_pose_through_preview_adapter(self):
        asset_root = ROOT / "assets" / "diagram-core"
        for icon_id, expected_parts in CANONICAL_BENCHMARK_PARTS.items():
            with self.subTest(icon_id=icon_id):
                instance_id = "canonical-{0}".format(icon_id)
                markup = render_preview_icon(
                    icon_id,
                    instance_id,
                    size=48,
                    asset_root=asset_root,
                )
                self.assertEqual(
                    markup,
                    render_preview_icon(
                        icon_id,
                        instance_id,
                        size=48,
                        asset_root=asset_root,
                    ),
                )
                root = parse_single_root(markup)
                self.assertEqual(icon_id, root.attrib["data-icon"])
                self.assertNotIn("data-icon-state", root.attrib)
                self.assertEqual("diagram-core-v1", root.attrib["data-icon-source"])
                self.assertEqual(
                    expected_parts,
                    tuple(
                        element.attrib["data-part"]
                        for element in root.iter()
                        if "data-part" in element.attrib
                    ),
                )
                self.assertFalse(
                    any("data-state-mark" in element.attrib for element in root.iter())
                )

    def test_new_canonical_benchmarks_have_disjoint_repeated_instance_ids(self):
        asset_root = ROOT / "assets" / "diagram-core"
        for icon_id in ("database", "api", "server"):
            first_instance = icon_id + ".left"
            second_instance = icon_id + "-left"
            document = parse_svg_fragment(
                render_preview_icon(
                    icon_id,
                    first_instance,
                    asset_root=asset_root,
                )
                + render_preview_icon(
                    icon_id,
                    second_instance,
                    asset_root=asset_root,
                )
            )
            roots = list(document)
            self.assertEqual(2, len(roots))
            id_sets = [
                {
                    element.attrib["id"]
                    for element in root.iter()
                    if "id" in element.attrib
                }
                for root in roots
            ]
            with self.subTest(icon_id=icon_id):
                self.assertTrue(id_sets[0].isdisjoint(id_sets[1]))
                self.assertEqual(
                    len(CANONICAL_BENCHMARK_PARTS[icon_id]) + 1,
                    len(id_sets[0]),
                )
                self.assertEqual(len(id_sets[0]), len(id_sets[1]))
            for root, instance_id in zip(
                roots,
                (first_instance, second_instance),
            ):
                for element in root.iter():
                    part_name = element.attrib.get("data-part")
                    if part_name is not None:
                        self.assertEqual(
                            part_dom_id(instance_id, icon_id, part_name),
                            element.attrib["id"],
                        )

    def test_canonical_visual_review_benchmarks_are_rejected_by_approved_adapter(self):
        asset_root = ROOT / "assets" / "diagram-core"
        for icon_id in CANONICAL_BENCHMARK_PARTS:
            with self.subTest(icon_id=icon_id):
                render_preview_icon(icon_id, "preview-" + icon_id, asset_root=asset_root)
                with self.assertRaises(AssetValidationError):
                    render_approved_icon(
                        icon_id,
                        "approved-" + icon_id,
                        asset_root=asset_root,
                    )


class DiagramCoreNamespacingTest(unittest.TestCase):
    def namespacing_source(self):
        return ElementTree.fromstring(
            """<g xmlns="http://www.w3.org/2000/svg"
 xmlns:xlink="http://www.w3.org/1999/xlink"
 aria-labelledby="shell hint" aria-describedby="description">
  <defs>
    <linearGradient id="paint"><stop offset="0"/></linearGradient>
    <clipPath id="clip"><rect width="10" height="10"/></clipPath>
  </defs>
  <style>.painted { fill: url(&quot;#paint&quot;); }</style>
  <g id="shell" data-part="shell" aria-labelledby="hint">
    <path id="shape" class="painted" fill="url('#paint')"
      clip-path="url( #clip )" style="stroke:url(#paint)"/>
    <use id="shape-copy" href="#shape" xlink:href="#shape"/>
  </g>
  <g id="hint"><circle r="1"/></g>
  <g id="description"><circle r="1"/></g>
  <g data-part="indicator"><circle r="1"/></g>
</g>"""
        )

    def styled_namespacing_source(self):
        return ElementTree.fromstring(
            """<g xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="gradient"><stop offset="0"/></linearGradient></defs>
  <style>/* #paint { comment-brace } */
.painted, [data-part="indicator"] {
  fill: url(&quot;#gradient&quot;);
  --backup-paint: url(#gradient);
  stroke: #abc;
  --label: &quot;#paint { declaration-string }&quot;;
}
:root .painted { color: #123456; }
#paint:hover { opacity: 0.75; }
  </style>
  <g id="paint"><path class="painted"/></g>
  <g data-part="indicator"><circle r="1"/></g>
</g>"""
        )

    def test_namespacing_clone_rewrites_every_reference_with_instance_scope(self):
        source = self.namespacing_source()
        source_before = ElementTree.tostring(source, encoding="unicode")

        first = namespace_svg_instance(source, "agent.left", "agent")
        second = namespace_svg_instance(source, "agent-left", "agent")

        self.assertEqual(source_before, ElementTree.tostring(source, encoding="unicode"))
        first_ids = {
            element.attrib["id"] for element in first.iter() if "id" in element.attrib
        }
        second_ids = {
            element.attrib["id"] for element in second.iter() if "id" in element.attrib
        }
        self.assertTrue(first_ids)
        self.assertTrue(second_ids)
        self.assertTrue(first_ids.isdisjoint(second_ids))
        self.assertTrue(
            all(identifier.count("__") == 2 for identifier in first_ids | second_ids)
        )
        self.assertEqual(part_dom_id("agent.left", "agent", "root"), first.attrib["id"])
        self.assertEqual(part_dom_id("agent-left", "agent", "root"), second.attrib["id"])

        for clone, other_ids in ((first, second_ids), (second, first_ids)):
            ids = {element.attrib["id"] for element in clone.iter() if "id" in element.attrib}
            references = referenced_ids(clone)
            self.assertGreaterEqual(len(references["href"]), 2)
            self.assertGreaterEqual(len(references["url"]), 4)
            self.assertGreaterEqual(len(references["aria"]), 4)
            for reference_kind, targets in references.items():
                with self.subTest(reference_kind=reference_kind):
                    self.assertTrue(targets)
                    self.assertTrue(set(targets).issubset(ids))
                    self.assertTrue(set(targets).isdisjoint(other_ids))
            for element in clone.iter():
                part_name = element.attrib.get("data-part")
                if part_name is not None:
                    self.assertEqual(
                        part_dom_id(
                            decode_instance_key(clone.attrib["id"].split("__", 1)[0]),
                            "agent",
                            part_name,
                        ),
                        element.attrib["id"],
                    )

    def test_style_selectors_are_scoped_and_namespaced_per_instance(self):
        source = self.styled_namespacing_source()
        first = namespace_svg_instance(source, "instance.one", "agent")
        second = namespace_svg_instance(source, "instance-one", "agent")
        parent = ElementTree.Element("{{{0}}}svg".format(SVG_NAMESPACE))
        parent.extend((first, second))

        styles = [
            element.text
            for element in parent.iter()
            if local_name(element.tag) == "style"
        ]
        self.assertEqual(2, len(styles))
        first_root_id = part_dom_id("instance.one", "agent", "root")
        second_root_id = part_dom_id("instance-one", "agent", "root")
        first_paint_id = part_dom_id("instance.one", "agent", "paint")
        second_paint_id = part_dom_id("instance-one", "agent", "paint")
        first_gradient_id = part_dom_id("instance.one", "agent", "gradient")
        second_gradient_id = part_dom_id("instance-one", "agent", "gradient")

        expected = (
            (styles[0], first_root_id, first_paint_id, first_gradient_id, second_root_id),
            (styles[1], second_root_id, second_paint_id, second_gradient_id, first_root_id),
        )
        for style, root_id, paint_id, gradient_id, other_root_id in expected:
            with self.subTest(root_id=root_id):
                self.assertIsNotNone(style)
                self.assertTrue(style.strip().startswith("@scope (#{0}) {{".format(root_id)))
                self.assertEqual(1, style.count("@scope"))
                self.assertIn(":scope .painted", style)
                self.assertNotIn(":root", style)
                self.assertIn("#{0}:hover".format(paint_id), style)
                self.assertIn('url("#{0}")'.format(gradient_id), style)
                self.assertIn("url(#{0})".format(gradient_id), style)
                self.assertNotIn(other_root_id, style)
                self.assertIn(".painted, [data-part=\"indicator\"]", style)
                self.assertIn("stroke: #abc", style)
                self.assertIn("color: #123456", style)
                self.assertIn('"#paint { declaration-string }"', style)
                self.assertIn("/* #paint { comment-brace } */", style)
                self.assertEqual(
                    2,
                    referenced_ids(
                        first if root_id == first_root_id else second
                    )["url"].count(gradient_id),
                )

        first_ids = {
            element.attrib["id"] for element in first.iter() if "id" in element.attrib
        }
        second_ids = {
            element.attrib["id"] for element in second.iter() if "id" in element.attrib
        }
        self.assertTrue(first_ids.isdisjoint(second_ids))
        self.assertTrue(set(referenced_ids(first)["url"]).issubset(first_ids))
        self.assertTrue(set(referenced_ids(second)["url"]).issubset(second_ids))

    def test_style_scoping_fails_closed_for_unsupported_at_rules(self):
        source = ElementTree.fromstring(
            """<g xmlns="http://www.w3.org/2000/svg">
  <style>@media (min-width: 1px) { .painted { fill: #abc; } }</style>
  <path class="painted"/>
</g>"""
        )

        with self.assertRaisesRegex(ValueError, "CSS at-rule"):
            namespace_svg_instance(source, "instance", "agent")

    def test_namespacing_rejects_external_unresolved_duplicate_and_invalid_ids(self):
        cases = (
            ('<g xmlns="{0}"><use href="https://example.test/a.svg#x"/></g>', "external href"),
            ('<g xmlns="{0}"><path fill="url(https://example.test/a.svg#x)"/></g>', "external url"),
            ('<g xmlns="{0}"><use href="#missing"/></g>', "unresolved href"),
            ('<g xmlns="{0}" aria-labelledby="missing"><path/></g>', "unresolved aria"),
            ('<g xmlns="{0}"><path id="same"/><path id="same"/></g>', "duplicate id"),
            ('<g xmlns="{0}"><path id="Bad_ID"/></g>', "invalid id"),
            ('<g xmlns="{0}"><path data-part="Bad_ID"/></g>', "invalid part"),
        )
        for source, label in cases:
            with self.subTest(label=label):
                root = ElementTree.fromstring(source.format(SVG_NAMESPACE))
                with self.assertRaises(ValueError):
                    namespace_svg_instance(root, "instance", "agent")


class DiagramCorePartCheckerCLITest(unittest.TestCase):
    def test_proves_two_instances_per_icon(self):
        result = run_part_checker(
            "--icons",
            "agent,database,api,server",
            "--instances",
            "2",
            "--json",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(8, report["instances"])
        self.assertEqual(0, report["duplicate_ids"])
        self.assertEqual(0, report["unresolved_refs"])
        self.assertEqual(0, report["missing_parts"])

    def test_normalizes_comma_whitespace(self):
        result = run_part_checker(
            "--icons", " agent, database ", "--instances", "1", "--json"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(2, report["icons"])
        self.assertEqual(2, report["instances"])

    def test_invalid_icons_and_instance_counts_are_usage_errors(self):
        cases = (
            ("empty icon", ("--icons", "agent,,api", "--instances", "1")),
            ("duplicate icon", ("--icons", "agent, agent", "--instances", "1")),
            ("unknown icon", ("--icons", "unknown", "--instances", "1")),
            ("zero instances", ("--icons", "agent", "--instances", "0")),
            ("negative instances", ("--icons", "agent", "--instances", "-1")),
            ("instances cap", ("--icons", "agent", "--instances", "65")),
        )
        for label, arguments in cases:
            with self.subTest(label=label):
                result = run_part_checker(*arguments)
                self.assertEqual(2, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertIn("usage:", result.stderr)

    def test_output_inspection_scopes_references_and_checks_exact_part_ids(self):
        checker = load_part_checker_module()
        instance_id = "first"
        root_id = part_dom_id(instance_id, "agent", "root")
        shell_id = part_dom_id(instance_id, "agent", "shell")
        other_id = part_dom_id("second", "agent", "shell")
        root = ElementTree.fromstring(
            '<g xmlns="{0}" id="{1}" aria-labelledby="{2}">'
            '<g data-part="shell" id="{3}"/>'
            "</g>".format(SVG_NAMESPACE, root_id, other_id, shell_id)
        )

        inspection = checker._inspect_instance(
            root, "agent", instance_id, ("shell",)
        )

        self.assertEqual(1, inspection["unresolved_refs"])
        self.assertEqual(0, inspection["missing_parts"])
        root[0].set("id", root_id)
        inspection = checker._inspect_instance(
            root, "agent", instance_id, ("shell",)
        )
        self.assertGreater(inspection["missing_parts"], 0)

    def test_asset_validation_failure_is_structured_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_root = Path(temp_dir) / "diagram-core"
            shutil.copytree(ROOT / "assets" / "diagram-core", asset_root)
            manifest_path = asset_root / "manifests" / "agent.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.pop("parts")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = run_part_checker(
                "--icons",
                "agent",
                "--instances",
                "1",
                "--json",
                "--asset-root",
                str(asset_root),
            )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        report = json.loads(result.stdout)
        self.assertIn("$.parts", "\n".join(report["error_details"]))

    def test_human_json_determinism_parity_and_no_asset_mutation(self):
        asset_root = ROOT / "assets" / "diagram-core"
        before = adapter_asset_tree_snapshot(asset_root)
        arguments = (
            "--icons", "agent,database,api,server", "--instances", "2"
        )

        first = run_part_checker(*arguments, "--json")
        second = run_part_checker(*arguments, "--json")
        human = run_part_checker(*arguments)

        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual(0, human.returncode, human.stderr)
        self.assertEqual("", first.stderr)
        self.assertEqual("", human.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(
            "icons=4 instances=8 duplicate_ids=0 unresolved_refs=0 "
            "missing_parts=0\n",
            human.stdout,
        )
        json_report = json.loads(first.stdout)
        human_counts = dict(field.split("=", 1) for field in human.stdout.split())
        self.assertEqual(
            {key: str(json_report[key]) for key in human_counts},
            human_counts,
        )
        self.assertEqual(before, adapter_asset_tree_snapshot(asset_root))

    def test_asset_validation_failure_human_output_has_no_traceback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_root = Path(temp_dir) / "diagram-core"
            shutil.copytree(ROOT / "assets" / "diagram-core", asset_root)
            manifest_path = asset_root / "manifests" / "agent.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.pop("parts")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = run_part_checker(
                "--icons",
                "agent",
                "--instances",
                "1",
                "--asset-root",
                str(asset_root),
            )

        self.assertEqual(1, result.returncode)
        self.assertEqual(
            "icons=1 instances=0 duplicate_ids=0 unresolved_refs=0 missing_parts=0\n",
            result.stdout,
        )
        self.assertIn("$.parts", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()

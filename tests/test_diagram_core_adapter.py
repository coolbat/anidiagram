import copy
import json
import re
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
        "{1}\n</svg>\n"
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
            state="processing",
            size=64,
            x=12.5,
            y=-0.0,
            tokens=TOKEN_VALUES,
            asset_root=self.bundle.root,
        )
        second_markup = render_preview_icon(
            "agent",
            "数据库.1",
            state="processing",
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
        self.assertEqual("processing", root.attrib["data-icon-state"])
        self.assertEqual("diagram-core-v1", root.attrib["data-icon-source"])
        self.assertEqual("1", root.attrib["data-asset-revision"])
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
        self.assertEqual(8, len(parts))
        for part_name, identifier in parts.items():
            self.assertEqual(
                part_dom_id("数据库.1", "agent", part_name),
                identifier,
            )
        identifiers = [
            element.attrib["id"] for element in root.iter() if "id" in element.attrib
        ]
        self.assertEqual(9, len(identifiers))
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertTrue(all(identifier.count("__") == 2 for identifier in identifiers))

    def test_repeated_instances_have_disjoint_root_and_part_ids(self):
        first_markup = render_preview_icon(
            "agent",
            "agent.left",
            state="idle",
            asset_root=self.bundle.root,
        )
        second_markup = render_preview_icon(
            "agent",
            "agent-left",
            state="success",
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
        self.assertEqual(18, len(all_ids))
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

    def test_state_identity_numbers_and_size_fail_closed(self):
        invalid_states = (None, "", "Processing", "not-supported", "idle\n")
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


if __name__ == "__main__":
    unittest.main()

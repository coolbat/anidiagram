import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree

from anidiagram.diagram_core.asset_loader import load_asset
from anidiagram.diagram_core.catalog import catalog_entry


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets" / "diagram-core"
ICON_IDS = ("operator", "memory", "tool", "token", "search")

EXPECTED = {
    "operator": {
        "prototype": "operator-console",
        "parts": ("body", "shell", "head", "panel", "cursor", "indicator"),
        "actions": ("receive", "operate", "confirm", "send"),
    },
    "memory": {
        "prototype": "stacked-memory",
        "parts": ("body", "shell", "drawer-top", "drawer-bottom", "card", "indicator"),
        "actions": ("receive", "write", "recall", "send"),
    },
    "tool": {
        "prototype": "pipeline-tool",
        "parts": ("body", "shell", "handle", "mechanism", "core", "indicator"),
        "actions": ("receive", "activate", "process", "send"),
    },
    "token": {
        "prototype": "metered-token",
        "parts": ("body", "shell", "tick-group", "core", "indicator"),
        "actions": ("receive", "count", "process", "send"),
    },
    "search": {
        "prototype": "search-instrument",
        "parts": ("body", "lens", "handle", "scan", "target", "indicator"),
        "actions": ("receive", "scan", "locate", "send"),
    },
}

PAINTABLE_TAGS = {
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


class DiagramCoreM1CompatSliceOneTest(unittest.TestCase):
    def test_catalog_and_manifests_promote_the_five_icons_atomically(self):
        for icon_id in ICON_IDS:
            with self.subTest(icon_id=icon_id):
                expected = EXPECTED[icon_id]
                entry = catalog_entry(icon_id)
                manifest = json.loads(
                    (ASSET_ROOT / "manifests" / (icon_id + ".json")).read_text(
                        encoding="utf-8"
                    )
                )

                self.assertEqual("visual-review", entry.status)
                self.assertEqual(1, entry.asset_revision)
                self.assertEqual(expected["prototype"], entry.structural_prototype)
                self.assertEqual(expected["parts"], entry.parts)
                self.assertEqual((), entry.supported_states)
                self.assertEqual(expected["actions"], entry.supported_actions)
                self.assertEqual(icon_id, manifest["id"])
                self.assertEqual("diagram-core-v1", manifest["system"])
                self.assertEqual("0 0 96 96", manifest["viewBox"])
                self.assertEqual(1, manifest["asset_revision"])
                self.assertEqual(expected["prototype"], manifest["structural_prototype"])
                self.assertEqual(list(expected["parts"]), manifest["parts"])
                self.assertEqual([], manifest["states"])
                self.assertEqual(list(expected["actions"]), manifest["actions"])
                self.assertEqual("visual-review", manifest["status"])

    def test_canonical_svgs_are_compact_shared_style_and_legible_at_48px(self):
        required_shared_tokens = {
            "--icon-surface-main",
            "--icon-stroke",
            "--icon-accent-secondary",
        }
        for icon_id in ICON_IDS:
            with self.subTest(icon_id=icon_id):
                expected = EXPECTED[icon_id]
                asset = load_asset(icon_id, allow_statuses={"visual-review"})
                root = asset.root
                source = asset.svg_source
                public_parts = tuple(
                    element.attrib["data-part"]
                    for element in root.iter()
                    if "data-part" in element.attrib
                )
                paintables = [
                    element
                    for element in root.iter()
                    if local_name(element.tag) in PAINTABLE_TAGS
                ]

                self.assertEqual("0 0 96 96", root.attrib["viewBox"])
                self.assertEqual(icon_id, root.attrib["data-icon"])
                self.assertEqual(expected["parts"], public_parts)
                self.assertLessEqual(len(paintables), 24)
                self.assertGreaterEqual(len(paintables), 7)
                self.assertLessEqual(asset.metrics.raw_size_bytes, 12 * 1024)
                self.assertLessEqual(asset.metrics.gzip_size_bytes, 6 * 1024)
                self.assertTrue(all(token in source for token in required_shared_tokens))
                self.assertNotIn("data-icon-state", source)
                self.assertNotIn("data-state-mark", source)
                for element in paintables:
                    stroke = element.attrib.get("stroke", "none")
                    if stroke != "none":
                        self.assertIn(
                            element.attrib.get("stroke-width"),
                            {"1.375", "2.125"},
                        )

    def test_motion_catalog_declares_declarative_showcase_recipes(self):
        motion_catalog = json.loads(
            (ROOT / "runtime" / "motion-catalog.json").read_text(encoding="utf-8")
        )
        definitions = {
            item["icon"]: item
            for item in motion_catalog["diagram_core_presentations"]
            if item["icon"] in ICON_IDS
        }

        self.assertEqual(set(ICON_IDS), set(definitions))
        for icon_id in ICON_IDS:
            with self.subTest(icon_id=icon_id):
                definition = definitions[icon_id]
                tracks = definition["recipe"]["tracks"]
                targets = tuple(
                    part
                    for track in tracks
                    for part in track["parts"]
                )

                self.assertEqual(icon_id + ".showcase-loop-v1", definition["id"])
                self.assertEqual(icon_id + "-showcase-loop-v1", definition["runtime_id"])
                self.assertEqual("presentation", definition["kind"])
                self.assertEqual("showcase", definition["profile"])
                self.assertEqual("diagram-core-v1", definition["icon_system"])
                self.assertEqual("authored-rest-pose", definition["rest_pose"])
                self.assertEqual("scene-controlled", definition["repeat_policy"])
                self.assertEqual("restore-rest-pose", definition["cancel_behavior"])
                self.assertEqual("static-rest", definition["reduced_motion_behavior"])
                self.assertEqual("visual-review", definition["status"])
                self.assertTrue(1600 <= definition["duration_ms"] <= 2400)
                self.assertTrue(0.8 <= definition["repeat_delay"] <= 1.4)
                self.assertTrue(3 <= len(set(targets)) <= 5)
                self.assertEqual(len(targets), len(set(targets)))
                self.assertTrue(set(targets).issubset(definition["required_parts"]))
                self.assertTrue(set(definition["required_parts"]).issubset(EXPECTED[icon_id]["parts"]))
                for track in tracks:
                    self.assertEqual(1, len(track["parts"]))
                    self.assertGreaterEqual(len(track["steps"]), 2)
                    final = track["steps"][-1]
                    self.assertLessEqual(final["at"] + final["duration"], definition["rest_at"])
                    self.assertTrue(
                        all(
                            value in (0, 1)
                            or (name == "rotate" and value % 360 == 0)
                            for name, value in final["to"].items()
                        ),
                        "the final authored step must be visually equivalent to the neutral rest pose",
                    )

    def test_tool_is_a_top_handle_pipeline_module_without_ear_arms(self):
        asset = load_asset("tool", allow_statuses={"visual-review"})
        parts = {
            element.attrib["data-part"]: element
            for element in asset.root.iter()
            if "data-part" in element.attrib
        }
        handle_rect = next(
            child for child in parts["handle"] if local_name(child.tag) == "rect"
        )
        shell_rect = next(
            child for child in parts["shell"] if local_name(child.tag) == "rect"
        )

        self.assertNotIn("arm-left", parts)
        self.assertNotIn("arm-right", parts)
        self.assertLess(float(handle_rect.attrib["y"]), float(shell_rect.attrib["y"]))
        self.assertLess(float(handle_rect.attrib["width"]), float(shell_rect.attrib["width"]))
        self.assertGreaterEqual(len(list(parts["mechanism"])), 5)

        motion_catalog = json.loads(
            (ROOT / "runtime" / "motion-catalog.json").read_text(encoding="utf-8")
        )
        definition = next(
            item
            for item in motion_catalog["diagram_core_presentations"]
            if item["icon"] == "tool"
        )
        tracks = {
            track["parts"][0]: track
            for track in definition["recipe"]["tracks"]
        }
        self.assertEqual({"handle", "mechanism", "core", "indicator"}, set(tracks))
        self.assertLess(tracks["handle"]["steps"][0]["to"]["y"], 0)
        self.assertIn("rotate", tracks["mechanism"]["steps"][0]["to"])
        self.assertGreater(tracks["core"]["steps"][0]["to"]["scale"], 1)

    def test_operator_is_a_person_behind_a_foreground_console(self):
        asset = load_asset("operator", allow_statuses={"visual-review"})
        parts = {
            element.attrib["data-part"]: element
            for element in asset.root.iter()
            if "data-part" in element.attrib
        }
        head_circle = next(
            child for child in parts["head"] if local_name(child.tag) == "circle"
        )
        panel_rect = next(
            child for child in parts["panel"] if local_name(child.tag) == "rect"
        )

        self.assertNotIn("head-dot", parts)
        self.assertFalse(
            any(local_name(child.tag) == "rect" for child in parts["shell"]),
            "the person silhouette must not be a device-like enclosing rectangle",
        )
        self.assertLess(float(head_circle.attrib["cy"]), float(panel_rect.attrib["y"]))
        self.assertGreater(
            float(panel_rect.attrib["width"]),
            2 * float(head_circle.attrib["r"]),
        )

        motion_catalog = json.loads(
            (ROOT / "runtime" / "motion-catalog.json").read_text(encoding="utf-8")
        )
        definition = next(
            item
            for item in motion_catalog["diagram_core_presentations"]
            if item["icon"] == "operator"
        )
        tracks = {
            track["parts"][0]: track
            for track in definition["recipe"]["tracks"]
        }
        self.assertEqual({"head", "panel", "cursor", "indicator"}, set(tracks))
        self.assertLess(tracks["head"]["steps"][0]["to"]["y"], 0)

    def test_review_validator_derives_the_implemented_inventory_from_catalog(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_diagram_core_assets.py"),
                "--review",
                "--json",
            ],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        report = json.loads(completed.stdout)
        implemented = {
            path.stem for path in (ASSET_ROOT / "manifests").glob("*.json")
        }
        self.assertEqual(len(implemented), report["visual_review"])
        self.assertEqual(56 - len(implemented), report["planned"])
        self.assertEqual(len(implemented), report["svg"])
        self.assertEqual(len(implemented), report["manifests"])
        self.assertEqual(implemented, set(report["paintable_elements_by_icon"]))
        self.assertTrue(set(ICON_IDS).issubset(implemented))
        self.assertEqual(0, report["errors"])


if __name__ == "__main__":
    unittest.main()

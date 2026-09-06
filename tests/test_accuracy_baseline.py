"""Independent accuracy regressions with small, portable source/diagram oracles.

SVG DOM geometry is checked separately by scripts/verify_accuracy_labels.mjs.
These tests cannot establish arbitrary architectural semantic correctness.
"""

import json
from pathlib import Path
import runpy
import unittest
from xml.etree import ElementTree

from anidiagram.reader import reader_data
from anidiagram.renderer_svg import render_svg
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "accuracy"
SVG = {"svg": "http://www.w3.org/2000/svg"}


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class AccuracyBaselineTest(unittest.TestCase):
    def test_readable_labels_preserve_the_short_quality_condition(self):
        spec = load_fixture("short-label.diagram.json")
        style = load_style()
        style.setdefault("edge", {})["label_placement"] = "avoid-nodes"

        root = ElementTree.fromstring(render_svg(compile_scene(spec), style))
        label = root.find(".//svg:text[@class='edge-label']", SVG)

        self.assertIsNotNone(label)
        self.assertEqual(spec["edges"][0]["label"], "".join(label.itertext()).strip())

    def test_important_conditions_and_protocols_survive_scene_compilation(self):
        for name in ("short-label.diagram.json", "detour-label.diagram.json", "directions.diagram.json"):
            spec = load_fixture(name)
            scene = compile_scene(spec)
            for authored, compiled in zip(spec["edges"], scene.edges):
                with self.subTest(fixture=name, edge=authored["semantic_relation_id"]):
                    self.assertEqual(authored.get("condition"), compiled.condition)
                    self.assertEqual(authored.get("protocol"), compiled.protocol)
                    self.assertEqual(authored["direction"], compiled.direction)

    def test_return_direction_is_preserved_in_reader_and_svg_markers(self):
        spec = load_fixture("directions.diagram.json")
        scene = compile_scene(spec)
        root = ElementTree.fromstring(render_svg(scene, load_style()))
        rendered = root.findall(".//svg:g[@class='edge']", SVG)
        reader_edges = reader_data(scene)["edges"]

        for authored, group, reader in zip(spec["edges"], rendered, reader_edges):
            with self.subTest(edge=authored["semantic_relation_id"]):
                self.assertEqual((authored["from"], authored["to"], authored["direction"]),
                                 (reader["from"], reader["to"], reader["direction"]))
                path = group.find("svg:path[@class='edge-draw']", SVG)
                self.assertEqual(authored["direction"] == "bidirectional", "marker-start" in path.attrib)
                self.assertEqual(authored["direction"] != "undirected", "marker-end" in path.attrib)


class ManualSourceTruthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = runpy.run_path(str(FIXTURES / "delivery_source.py"))

    def test_quality_errors_prevent_both_callbacks_and_preserve_last_good(self):
        report = self.source["QualityAnalyzer"].analyze(1)
        outputs = {"svg": "last-good"}
        calls = []

        def render():
            calls.append("render")
            return "new-artifact"

        def commit(artifact):
            calls.append("commit")
            outputs["svg"] = artifact

        with self.assertRaises(self.source["DeliveryError"]):
            self.source["entry"](report, render, commit)

        self.assertEqual([], calls)
        self.assertEqual({"svg": "last-good"}, outputs)

    def test_quality_pass_returns_the_callee_receipt_to_its_caller(self):
        report = self.source["QualityAnalyzer"].analyze(0)
        receipt = {"committed": "new-artifact"}

        actual = self.source["entry"](report, lambda: "new-artifact", lambda artifact: receipt)

        self.assertIs(receipt, actual)
        self.assertIn("analyze", self.source["QualityAnalyzer"].__dict__)
        self.assertNotIn("analyze", self.source["DeliveryCoordinator"].__dict__)

    def test_plain_export_has_partial_writes_after_a_later_render_fails(self):
        outputs = {"svg": "old-svg", "html": "old-html"}

        def failed_html():
            raise RuntimeError("HTML renderer failed")

        with self.assertRaisesRegex(RuntimeError, "HTML renderer failed"):
            self.source["export_direct"]([("svg", lambda: "new-svg"), ("html", failed_html)], outputs)

        self.assertEqual({"svg": "new-svg", "html": "old-html"}, outputs)


if __name__ == "__main__":
    unittest.main()

"""Static exports must not depend on a browser finishing their entrance."""

import unittest
import xml.etree.ElementTree as ET

from anidiagram.presets import compile_preset
from anidiagram.renderer_svg import render_svg
from anidiagram.styles import load_style
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NS = {"s": "http://www.w3.org/2000/svg"}


class StaticExportTests(unittest.TestCase):
    def test_complete_scene_without_running_smil(self):
        spec = compile_preset("agent-memory")
        spec["motion"] = {"profile": "normal", "sequence": "layered"}
        root = ET.fromstring(render_svg(spec, load_style(ROOT / "styles/minimal-light.json")))
        elements = [element for element in root if element.get("class") in {"node motion-node", "group", "title", "subtitle"}]
        self.assertTrue(elements)
        for element in elements:
            with self.subTest(element=element.get("id") or element.get("class")):
                self.assertEqual(element.get("opacity", "1"), "1")
                self.assertFalse(any(child.get("attributeName") == "opacity" and child.get("values", "").startswith("0;") for child in element))
        for edge in root.findall("s:g[@class='edge']", NS):
            draw = edge.find("s:path[@class='edge-draw']", NS)
            self.assertEqual(draw.get("stroke-dashoffset"), "0")
            self.assertIsNone(draw.find("s:animate", NS))
            self.assertEqual(edge.find("s:text[@class='edge-label']", NS).get("opacity"), "1")


if __name__ == "__main__":
    unittest.main()

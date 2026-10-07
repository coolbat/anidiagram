import json
from pathlib import Path
import tempfile
import unittest

from anidiagram.composition import STYLE_ALIASES, STYLES
from anidiagram.renderer_svg import render_svg
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style, validate_style_profile


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "minimal.diagram.json"


class StyleProfilesTest(unittest.TestCase):
    def test_retired_minimal_light_is_an_alias_of_openai_minimal(self):
        canonical = load_style(ROOT / "styles" / "openai-minimal.json")
        self.assertEqual(canonical, load_style(ROOT / "styles" / "minimal-light.json"))
        self.assertEqual(canonical, load_style())
        self.assertEqual("openai-minimal", STYLE_ALIASES["minimal-light"])
        self.assertIn("minimal-light", STYLES)
        catalog = json.loads((ROOT / "styles" / "catalog.json").read_text(encoding="utf-8"))
        self.assertNotIn("minimal-light", catalog["styles"])
        self.assertEqual(12, len(catalog["styles"]))

    def test_alias_profiles_cannot_carry_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "alias.json"
            path.write_text(json.dumps({"name": "alias", "alias_of": "openai-minimal", "canvas": {}}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_style(path)

    def test_group_surface_tokens_are_validated_and_rendered(self):
        self.assertTrue(validate_style_profile({"group": {"fill_opacity": 2}}))
        self.assertTrue(validate_style_profile({"group": {"stroke_dasharray": 4}}))
        self.assertFalse(validate_style_profile({"group": {"fill_opacity": 0.07, "stroke_dasharray": "none"}}))

        spec = json.loads(FIXTURE.read_text(encoding="utf-8"))
        spec["groups"] = [{"id": "g", "label": "Group", "bounds": [40, 160, 400, 200], "role": "process"}]
        svg = render_svg(compile_scene(spec), load_style(ROOT / "styles" / "flat-icon.json"))
        self.assertIn('fill-opacity="0.07"', svg)
        self.assertIn('stroke-dasharray="none"', svg)

    def test_light_styles_are_visually_distinct(self):
        flat = load_style(ROOT / "styles" / "flat-icon.json")
        notion = load_style(ROOT / "styles" / "notion-clean.json")
        self.assertEqual("#ffffff", flat["roles"]["process"]["text"])
        self.assertEqual(0, flat["node"]["stroke_width"])
        self.assertEqual(0, notion["node"]["stroke_width"])
        self.assertEqual(0, notion["effects"]["frame_opacity"])


if __name__ == "__main__":
    unittest.main()

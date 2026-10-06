import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DifyGalleryHeroTest(unittest.TestCase):
    def test_homepage_hero_uses_both_dify_styles(self):
        html = (ROOT / "gallery/index.html").read_text()
        hero = re.search(r'<section class="hero"[^>]*>(.*?)</section>', html, re.S).group(1)
        self.assertIn("Dify", hero)
        self.assertIn('data-preview-url="cases/dify/dify-en.html"', hero)
        self.assertIn('data-preview-url="cases/dify/dify-deep-tech-en.html"', hero)
        self.assertNotIn("agent-runtime-flow", hero)
        self.assertLess(html.index('class="hero"'), html.index("Public Icon Systems"))

    def test_hero_manifest_preserves_old_example_as_legacy(self):
        manifest = json.loads((ROOT / "gallery/showcase_manifest.json").read_text())
        self.assertEqual("dify", manifest["hero"]["id"])
        self.assertEqual(["minimal-light", "deep-tech"], [entry["style"] for entry in manifest["hero_variants"]])
        self.assertEqual("agent-runtime-flow", manifest["legacy_hero"]["id"])
        self.assertTrue((ROOT / manifest["legacy_hero"]["html"]).is_file())
        page = (ROOT / "gallery/hero/index.html").read_text()
        self.assertIn("../cases/dify/dify-en.html", page)
        self.assertIn("../cases/dify/dify-deep-tech-en.html", page)


if __name__ == "__main__":
    unittest.main()

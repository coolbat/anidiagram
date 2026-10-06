"""Assert that the public preview shows icon motion, not just moving edges."""
import hashlib
import json
from pathlib import Path
import unittest
from PIL import Image
from build import STYLES, page_source, variant_stem

HERE = Path(__file__).resolve().parent
PUBLIC = HERE.parents[2] / "gallery/cases/dify"


class DifyMotionTests(unittest.TestCase):
    def test_case_pages_expose_motion_and_static_controls(self):
        for style, language in [(s, l) for s in STYLES for l in ("zh-CN", "en")]:
            html = page_source(language, style)
            self.assertIn('id="preview-motion"', html)
            self.assertIn('data-motion-src=', html)
            self.assertIn('src="preview-motion.js"', html)

    def test_each_encoded_preview_animates_all_ten_icon_regions(self):
        for stem in (variant_stem(l, s) for s in STYLES for l in ("zh-CN", "en")):
            receipt = json.loads((PUBLIC / f"{stem}-motion.json").read_text())
            image_path = PUBLIC / f"{stem}-motion.webp"
            self.assertEqual(receipt["html_sha256"], hashlib.sha256((PUBLIC / f"{stem}.html").read_bytes()).hexdigest())
            self.assertEqual(receipt["webp_sha256"], hashlib.sha256(image_path.read_bytes()).hexdigest())
            self.assertEqual(len(receipt["icon_regions"]), 10)
            self.assertLess(image_path.stat().st_size, 1024 * 1024)
            with Image.open(image_path) as image:
                self.assertEqual(image.size, (900, 1130))
                self.assertEqual(image.n_frames, 24)
                for node, region in receipt["icon_regions"].items():
                    frames = set()
                    for index in range(image.n_frames):
                        image.seek(index)
                        frames.add(hashlib.sha256(image.convert("RGB").crop(tuple(region)).tobytes()).hexdigest())
                    self.assertGreater(len(frames), 4, f"Frozen icon: {stem}/{node}")


if __name__ == "__main__":
    unittest.main()

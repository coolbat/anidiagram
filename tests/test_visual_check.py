import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from anidiagram.visual_check import parse_viewports, visual_check


class VisualCheckTest(unittest.TestCase):
    def test_viewport_bounds_and_duplicates(self):
        self.assertEqual([{"width": 1440, "height": 900}], parse_viewports("1440x900"))
        for value in ("", "0x900", "10000x900", "1440*900", "1440x900,1440x900"):
            with self.assertRaises(ValueError):
                parse_viewports(value)

    def test_missing_browser_is_skipped_and_never_visual_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "sample.html"
            content = b"<!doctype html><svg></svg>"
            source.write_bytes(content)
            with patch("anidiagram.visual_check.shutil.which", return_value=None):
                result = visual_check(source)
            self.assertFalse(result["ok"])
            self.assertEqual("skipped", result["status"])
            receipt = json.loads(Path(result["receipt"]).read_text())
            self.assertEqual("pending", receipt["visual_review"])
            self.assertEqual([], receipt["captures"])
            self.assertEqual(content, source.read_bytes())

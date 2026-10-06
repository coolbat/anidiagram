"""Gallery cards must show the real runtime, with complete static fallbacks."""

import hashlib
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class PreviewParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.previews = []
        self.images = []
        self.image_sizes = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-preview-url" in attrs:
            self.previews.append(attrs["data-preview-url"])
        if tag == "img":
            self.images.append(attrs["src"])
            self.image_sizes.append((attrs.get("width"), attrs.get("height")))


class GalleryPreviewTest(unittest.TestCase):
    def test_committed_preview_assets_match_sources(self):
        gallery = ROOT / "gallery"
        manifest = json.loads((gallery / "preview-manifest.json").read_text())
        self.assertEqual(64, len(manifest["previews"]))
        for entry in manifest["previews"]:
            for kind in ("html", "svg", "poster"):
                self.assertEqual(entry[kind + "_sha256"],
                                 hashlib.sha256((gallery / entry[kind]).read_bytes()).hexdigest(), entry[kind])
            tree = ET.fromstring((gallery / entry["poster"]).read_bytes())
            self.assertFalse(any(el.tag.rsplit("}", 1)[-1] in
                                 {"animate", "animateMotion", "animateTransform", "set"}
                                 for el in tree.iter()), entry["poster"])
        for suffix in ("js", "css"):
            self.assertEqual((gallery / f"preview-motion.{suffix}").read_bytes(),
                             (ROOT / "runtime" / f"gallery-preview.{suffix}").read_bytes())

    def test_all_public_gallery_surfaces_have_live_previews(self):
        for name, count in {
            "index.html": 33, "styles/index.html": 13, "layouts/index.html": 16,
            "hero/index.html": 2, "icon-systems/index.html": 2,
            "character-themes.html": 3, "runtime-motion.html": 28,
        }.items():
            with self.subTest(page=name):
                page = ROOT / "gallery" / name
                content = page.read_text()
                parser = PreviewParser()
                parser.feed(content)
                self.assertEqual(count, len(parser.previews))
                self.assertIn("preview-motion.js", content)
                self.assertIn("preview-motion.css", content)
                self.assertIn("data-preview-toggle", content)
                for target in parser.previews + parser.images:
                    self.assertTrue((page.parent / target).is_file(), target)
                for image in parser.images:
                    self.assertTrue(image.endswith((".preview.svg", "-static.svg")), image)
                self.assertTrue(all(width and height for width, height in parser.image_sizes))

    def test_static_posters_are_complete_and_do_not_mutate_diagrams(self):
        from gallery_previews import write_static_poster
        source = ROOT / "gallery/styles/minimal-light.svg"
        original = source.read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            poster = Path(temporary) / "poster.svg"
            write_static_poster(source, poster)
            first = poster.read_bytes()
            write_static_poster(source, poster)
            self.assertEqual(first, poster.read_bytes())
            tree = ET.fromstring(first)
            self.assertFalse(any(el.tag.rsplit("}", 1)[-1] in
                                 {"animate", "animateMotion", "animateTransform", "set"}
                                 for el in tree.iter()))
            nodes = [el for el in tree.iter() if "node" in el.get("class", "").split()]
            self.assertEqual(5, len(nodes))
            self.assertTrue(all(node.get("opacity") == "1" for node in nodes))
            self.assertIn("animation: none !important", first.decode())
        self.assertEqual(original, source.read_bytes())

    def test_preview_builder_is_reproducible_and_records_source_hashes(self):
        from gallery_previews import write_preview_assets
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / "index.html").write_text(
                '<a data-preview-url="demo.html"><img src="demo.preview.svg"></a>')
            svg = (ROOT / "gallery/styles/minimal-light.svg").read_bytes()
            (output / "demo.svg").write_bytes(svg)
            html = b"<html>existing diagram</html>"
            (output / "demo.html").write_bytes(html)
            write_preview_assets(output)
            manifest = json.loads((output / "preview-manifest.json").read_text())
            entry = manifest["previews"][0]
            self.assertEqual("demo.html", entry["html"])
            self.assertEqual(hashlib.sha256(html).hexdigest(), entry["html_sha256"])
            self.assertEqual(hashlib.sha256(svg).hexdigest(), entry["svg_sha256"])
            first = (output / "preview-manifest.json").read_bytes()
            write_preview_assets(output)
            self.assertEqual(first, (output / "preview-manifest.json").read_bytes())

    def test_existing_static_poster_is_reused_without_mutating_case_bundle(self):
        from gallery_previews import live_preview, write_preview_assets
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / "index.html").write_text(live_preview("demo.svg", "demo.html", "Dify", poster="demo-static.svg"))
            svg = (ROOT / "gallery/cases/dify/dify-static.svg").read_bytes()
            (output / "demo.svg").write_bytes(svg)
            (output / "demo-static.svg").write_bytes(svg)
            (output / "demo.html").write_text("<html>existing diagram</html>")
            write_preview_assets(output)
            self.assertEqual(svg, (output / "demo-static.svg").read_bytes())
            self.assertFalse((output / "demo.preview.svg").exists())
            manifest = json.loads((output / "preview-manifest.json").read_text())
            self.assertEqual("demo-static.svg", manifest["previews"][0]["poster"])


if __name__ == "__main__":
    unittest.main()

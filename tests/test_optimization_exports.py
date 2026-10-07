"""Real browser frames retain native dimensions and complete content at t=0."""

import shutil
import tempfile
import unittest
from pathlib import Path

from anidiagram.exporters import _capture_browser_runtime, _playwright_node_env
from anidiagram.renderer_html_runtime import render_html_runtime
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]


class OptimizationBrowserExportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from PIL import Image
        except ImportError:
            raise unittest.SkipTest("Pillow is required to inspect captured pixels")
        cls.Image = Image
        cls.gsap = ROOT / "node_modules/gsap/dist/gsap.min.js"
        if not shutil.which("node") or not cls.gsap.is_file():
            raise unittest.SkipTest("Local Node.js and GSAP are required for the browser export regression")
        _, _, reason = _playwright_node_env()
        if reason:
            raise unittest.SkipTest(reason)

    def test_frame_capture_preserves_dimensions_and_endpoint_text_from_first_frame(self):
        scene = compile_scene({
            "version": "0.2",
            "canvas": {"width": 640, "height": 360},
            "title": {"text": "Capture regression"},
            "motion": {"profile": "normal"},
            "nodes": [
                {"id": "source", "label": "Source", "caption": "Visible input", "position": [60, 180], "size": [180, 90], "fill": "#ffffff"},
                {"id": "target", "label": "Target", "caption": "Visible output", "position": [380, 180], "size": [180, 90], "fill": "#ffffff"},
            ],
            "edges": [{"from": "source", "to": "target", "route": "straight"}],
        })
        style = load_style(ROOT / "styles/minimal-light.json")
        html = render_html_runtime(scene, style, dependency_mode="inline", dependency_source=self.gsap)
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            html_path = temporary / "capture.html"
            html_path.write_text(html, encoding="utf-8")
            frames = temporary / "frames"
            frames.mkdir()
            result = _capture_browser_runtime(
                scene=scene,
                html_path=html_path,
                frames_dir=frames,
                pdf_path=None,
                format_name="webp",
                frames=2,
                fps=24,
                scale=2,
            )
            self.assertEqual("written", result["status"], result.get("reason"))
            for index in range(2):
                with self.Image.open(frames / f"frame-{index:04d}.png") as image:
                    self.assertEqual((1280, 720), image.size, "viewer fit must not shrink exported frames")
                    for node in scene.nodes:
                        x, y = node.position
                        width, height = node.size
                        # Exclude card borders and the inter-node arrow. Dark
                        # pixels in this white interior are the endpoint text.
                        text_region = image.convert("RGB").crop((
                            int((x + 16) * 2), int((y + 12) * 2),
                            int((x + width - 16) * 2), int((y + height - 12) * 2),
                        ))
                        pixels = text_region.load()
                        dark_pixels = sum(
                            max(pixels[column, row]) < 100
                            for row in range(text_region.height)
                            for column in range(text_region.width)
                        )
                        with self.subTest(frame=index, endpoint=node.node_id):
                            self.assertGreater(dark_pixels, 150, "entrance must not hide endpoint text in captured frames")


if __name__ == "__main__":
    unittest.main()

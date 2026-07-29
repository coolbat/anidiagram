import json
import re
import tempfile
import unittest
from pathlib import Path

from anidiagram.planner import compile_plan
from anidiagram.renderer_html_runtime import render_html_runtime
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]


class ProductizationTest(unittest.TestCase):
    def _scene(self):
        plan = json.loads(
            (ROOT / "examples" / "contracts" / "production-request-path.plan.json").read_text(encoding="utf-8")
        )
        return compile_scene(compile_plan(plan))

    def _manifest(self, html: str):
        source = re.search(
            r'<script type="application/json" id="anidiagram-motion-manifest">\s*(.*?)\s*</script>',
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(source)
        return json.loads(source.group(1))

    def test_runtime_dependency_modes_are_explicit_and_versioned(self):
        scene = self._scene()
        cdn = render_html_runtime(scene, load_style(), dependency_mode="cdn")
        self.assertIn("gsap@3.15.0/dist/gsap.min.js", cdn)
        self.assertNotIn("gsap@3/dist/gsap.min.js", cdn)

        static = render_html_runtime(scene, load_style(), dependency_mode="none")
        self.assertNotIn("cdn.jsdelivr.net/npm/gsap", static)
        self.assertIn('id="runtime-warning"', static)

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "gsap.min.js"
            source.write_text('window.gsap = { marker: "</script>" };', encoding="utf-8")
            inline = render_html_runtime(
                scene,
                load_style(),
                dependency_mode="inline",
                dependency_source=source,
            )
        self.assertIn('data-runtime-dependency="gsap@3.15.0"', inline)
        self.assertIn("<\\/script>", inline)

    def test_auto_locale_produces_chinese_accessible_controls(self):
        scene = self._scene()
        object.__setattr__(scene, "title", type(scene.title)("中文智能体架构", "因果执行流程"))
        html = render_html_runtime(scene, load_style(), dependency_mode="none")

        self.assertIn('<html lang="zh-CN">', html)
        self.assertIn('role="toolbar" aria-label="图表播放与视图控制"', html)
        self.assertIn('id="runtime-status"', html)
        self.assertIn('tabindex="0" aria-label="可缩放和平移的动画图表"', html)

    def test_long_node_text_uses_cross_platform_svg_fitting(self):
        html = render_html_runtime(self._scene(), load_style(), dependency_mode="none")

        self.assertRegex(
            html,
            r'<tspan[^>]+class="node-title"[^>]+textLength="[0-9.]+"[^>]+lengthAdjust="spacingAndGlyphs"',
        )

    def test_timeline_and_hybrid_manifests_are_explicit_without_changing_ambient(self):
        scene = self._scene()
        ambient = self._manifest(render_html_runtime(scene, load_style(), dependency_mode="none"))
        timeline = self._manifest(
            render_html_runtime(scene, load_style(), dependency_mode="none", runtime_mode="timeline")
        )
        hybrid = self._manifest(
            render_html_runtime(scene, load_style(), dependency_mode="none", runtime_mode="hybrid")
        )

        self.assertEqual("ambient", ambient["mode"])
        self.assertEqual("independent-icon-loops", ambient["sequence"])
        self.assertNotIn("choreographer", ambient)
        self.assertEqual("timeline", timeline["mode"])
        self.assertEqual("causal-edge-steps", timeline["sequence"])
        self.assertTrue(timeline["choreographer"]["autoplay"])
        self.assertEqual(len(scene.edges), len(timeline["choreographer"]["steps"]))
        self.assertEqual("hybrid", hybrid["mode"])
        self.assertEqual("ambient", hybrid["choreographer"]["initial_state"])
        self.assertFalse(hybrid["choreographer"]["autoplay"])


if __name__ == "__main__":
    unittest.main()

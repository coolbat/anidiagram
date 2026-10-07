"""Browser evidence for signal semantics, scheduling and motion budgets."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from anidiagram.exporters import _playwright_node_env
from anidiagram.renderer_html_runtime import render_html_runtime
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style

ROOT = Path(__file__).resolve().parents[1]


class MotionV2BrowserTests(unittest.TestCase):
    def test_semantic_arrivals_budgets_mode_switching_and_seek(self):
        gsap = ROOT / 'node_modules/gsap/dist/gsap.min.js'
        if not shutil.which('node') or not gsap.is_file():
            self.skipTest('Local Node.js and GSAP required')
        _, _, reason = _playwright_node_env()
        if reason:
            self.skipTest(reason)
        spec = {
            'version': '0.3', 'canvas': {'width': 1180, 'height': 640},
            'title': {'text': 'Motion v2 regression'}, 'motion': {'profile': 'expressive'},
            'nodes': [{'id': f'n{i}', 'label': f'Node {i}', 'icon': 'api', 'position': [70+i*140, 160+(i%2)*180], 'size': [105, 75]} for i in range(7)],
            'edges': [{'from': f'n{i}', 'to': f'n{i+1}', 'semantic_kind': kind, 'importance': 'primary' if i<5 else 'supporting'} for i, kind in enumerate(['request','response','async','stream','reject','async-message'])],
        }
        scene = compile_scene(spec)
        with tempfile.TemporaryDirectory() as temporary:
            for mode in ['ambient', 'event-driven']:
                Path(temporary, f'motion-{mode}.html').write_text(render_html_runtime(scene, load_style(ROOT/'styles/minimal-light.json'), runtime_mode=mode, dependency_mode='inline', dependency_source=gsap))
            result = subprocess.run(['node', str(ROOT/'scripts/verify_motion_v2.mjs'), temporary], cwd=ROOT, text=True, capture_output=True, timeout=60)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertTrue(json.loads(result.stdout)['ok'])


if __name__ == '__main__':
    unittest.main()

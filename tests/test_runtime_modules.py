import json
from pathlib import Path
import unittest
from anidiagram.renderer_html_runtime import _runtime_source, render_html_runtime
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style
ROOT=Path(__file__).resolve().parents[1]
class RuntimeModulesTest(unittest.TestCase):
    def test_assembled_html_has_each_module_once_and_no_unresolved_marker(self):
        modules=json.loads((ROOT/'runtime/modules.json').read_text());source=_runtime_source()
        for section in ('before','core','extensions','after'):
            for name in modules[section]:self.assertEqual(1,source.count((ROOT/'runtime'/name).read_text()),name)
        self.assertNotIn('/* ANIDIAGRAM_CORE */',source);self.assertNotIn('/* ANIDIAGRAM_EXTENSIONS */',source)
        self.assertLess(source.index('function play()'),source.index('Object.assign(window.AniDiagramRuntime'))
    def test_viewer_theme_and_grouped_controls_follow_scene(self):
        scene=compile_scene({'version':'0.2','canvas':{'width':640,'height':360},'title':{'text':'Theme'},'nodes':[{'id':'a','label':'A','position':[60,150],'size':[120,80]}],'edges':[]})
        html=render_html_runtime(scene,load_style(ROOT/'styles/minimal-light.json'),dependency_mode='none')
        self.assertIn('--surface: #ffffff',html);self.assertEqual(3,html.count('class="toolbar-group"'));self.assertIn('id="copy-link"',html);self.assertIn('id="narration"',html)
    def test_recording_is_portable_and_tracks_its_source(self):
        import hashlib
        meta=json.loads((ROOT/'gallery/narration/recording.json').read_text())
        self.assertEqual(7,meta['duration_seconds']);self.assertEqual(168,meta['frames'])
        self.assertEqual(meta['source_plan_sha256'],hashlib.sha256((ROOT/meta['source_plan']).read_bytes()).hexdigest())
        self.assertEqual(meta['sha256'],hashlib.sha256((ROOT/'gallery/narration/explanation.mp4').read_bytes()).hexdigest())
        self.assertIn('data-runtime-dependency="gsap@',(ROOT/'gallery/narration/production-request.html').read_text())

import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

from anidiagram.cli import main
from anidiagram.quality import quality_report
from anidiagram.renderer_html_runtime import render_html_runtime
from anidiagram.renderer_svg import render_svg
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style, validate_style_profile


FIXTURE = Path(__file__).parent / 'fixtures' / 'accuracy' / 'detour-label.diagram.json'


class ReadableLabelsTest(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads(FIXTURE.read_text())
        self.style = load_style()
        self.style['edge']['label_placement'] = 'avoid-nodes'

    def test_visible_table_preserves_conditions_protocol_and_escaping(self):
        self.spec['edges'][0]['condition'] = 'errors < 1 && ready'
        self.spec['edges'][0]['protocol'] = 'HTTP <script>'
        scene = compile_scene(self.spec)
        html = render_html_runtime(scene, self.style, dependency_mode='none')
        self.assertIn('id="relation-table"', html)
        self.assertIn('errors &lt; 1 &amp;&amp; ready', html)
        self.assertIn('HTTP &lt;script&gt;', html)
        self.assertIn('staged-render', html)
        self.assertIn('Semantic review: pending', html)
        self.assertNotIn('id="relation-table"', render_html_runtime(scene, load_style(), dependency_mode='none'))

    def test_cli_option_and_receipt_record(self):
        with tempfile.TemporaryDirectory() as temporary, redirect_stdout(io.StringIO()):
            main(['--spec', str(FIXTURE), '--readable-labels', '--outdir', temporary,
                  '--formats', 'html,svg,quality', '--runtime-dependency', 'none', '--deliver'])
            receipt = json.loads((Path(temporary) / 'diagram.delivery.json').read_text())
            self.assertIn('readable_labels', json.dumps(receipt))
            self.assertIn('data-label-placement="placed"', (Path(temporary) / 'diagram.svg').read_text())

    def test_unsupported_native_exports_do_not_claim_readable_mode(self):
        with tempfile.TemporaryDirectory() as temporary, redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main(['--spec', str(FIXTURE), '--readable-labels', '--outdir', temporary, '--formats', 'png'])
        self.assertEqual(2, error.exception.code)

    def test_unplaceable_text_remains_present_and_quality_blocks_delivery(self):
        self.spec['edges'][0]['label'] = '完整标签' * 100
        scene = compile_scene(self.spec)
        self.assertIn(self.spec['edges'][0]['label'], render_svg(scene, self.style))
        report = quality_report(scene, self.style)
        self.assertGreater(report['summary']['errors'], 0)
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            spec = folder / 'input.json'
            spec.write_text(json.dumps(self.spec))
            target = folder / 'diagram.svg'
            target.write_text('last known good')
            with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                main(['--spec', str(spec), '--readable-labels', '--deliver', '--outdir', temporary, '--formats', 'svg'])
            self.assertEqual('last known good', target.read_text())

    def test_debug_viewer_also_keeps_the_visible_relation_table(self):
        from anidiagram.exporters import write_viewer
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'viewer.html'
            write_viewer(compile_scene(self.spec), self.style, path)
            self.assertTrue('id="relation-table"' in path.read_text())

    def test_style_placement_enum(self):
        self.assertFalse(validate_style_profile(self.style))
        self.style['edge']['label_placement'] = 'hide-it'
        self.assertTrue(validate_style_profile(self.style))

"""Portable positive/negative browser gates; no historical pilot artifacts required."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

from anidiagram.renderer_html_runtime import render_html_runtime
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style
from anidiagram.visual_check import visual_check

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--outdir', default='build/ci/accuracy')
args = parser.parse_args()
outdir = Path(args.outdir).resolve()
outdir.mkdir(parents=True, exist_ok=True)
style = load_style()
style['edge']['label_placement'] = 'avoid-nodes'
results = []


def probe(name, html, expected, codes=()):
    target = outdir / name / 'diagram.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding='utf-8')
    result = visual_check(target, viewports='1440x900', strict_labels=True)
    receipt = json.loads(Path(result['receipt']).read_text())
    found = {issue['code'] for check in receipt['checks'] for issue in check.get('rendered_readability', {}).get('issues', [])}
    assert result['status'] == expected and set(codes) <= found, (name, result, found)
    results.append({'name': name, 'expected': expected, 'status': result['status'], 'issues': sorted(found)})


for fixture in ('short-label', 'detour-label', 'reverse-label', 'directions'):
    spec_path = ROOT / 'tests' / 'fixtures' / 'accuracy' / (fixture + '.diagram.json')
    spec = json.loads(spec_path.read_text())
    scene = compile_scene(spec)
    html = render_html_runtime(scene, style, dependency_mode='inline', dependency_source=ROOT / 'node_modules/gsap/dist/gsap.min.js')
    probe(fixture, html, 'passed')
    # A separately authored oracle reads the source fixture, not our embedded metadata.
    oracle = subprocess.run(['node', str(ROOT / 'scripts/verify_accuracy_labels.mjs'), str(spec_path)],
                            capture_output=True, text=True, check=False)
    assert oracle.returncode == 0, (fixture, oracle.stdout, oracle.stderr)
    (outdir / fixture / 'independent.json').write_text(oracle.stdout)
    if fixture != 'directions':
        old = subprocess.run(['node', str(ROOT / 'scripts/verify_accuracy_labels.mjs'), str(spec_path), '--legacy'],
                             capture_output=True, text=True, check=False)
        assert old.returncode == 1 and json.loads(old.stdout)['issues'], (fixture, old.stdout, old.stderr)
        (outdir / fixture / 'legacy-negative.json').write_text(old.stdout)

    if fixture == 'detour-label':
        # Mutations happen in isolated test artifact strings, never in the user's page/source.
        probe('hidden-label', html.replace('</head>', '<style>.edge-label{display:none}</style></head>'), 'failed', ['label-not-visible'])
        probe('tiny-label', html.replace('</head>', '<style>.edge-label{font-size:4px!important}</style></head>'), 'failed', ['label-too-small'])
        probe('overlap-label', html.replace('class="edge-label"', 'transform="translate(60 150)" class="edge-label"'), 'failed', ['label-node-overlap'])
        wrong = re.sub(r'(<path class="edge-draw"[^>]*?) marker-end="[^"]+"', r'\1', html, count=1)
        assert wrong != html
        probe('wrong-arrow', wrong, 'failed', ['arrow-direction'])
        changed = html.replace('<td>quality.summary.errors == 0</td>', '<td>quality.summary.errors &gt; 0</td>')
        assert changed != html
        probe('changed-condition', changed, 'failed', ['relation-field'])
        probe('hidden-table', html.replace('</head>', '<style>#relation-table{display:none}</style></head>'), 'failed', ['relation-table-missing-or-hidden'])
        probe('console-error', html.replace('</body>', '<script>console.error("injected test error")</script></body>'), 'failed')
        probe('missing-expectations', html.replace('id="anidiagram-readability-data"', 'id="removed-for-negative-test"'), 'failed', ['missing-readability-expectations'])
        enlarged = html.replace('</head>', '<style>#viewport svg{width:2400px!important}.stage{overflow:hidden!important}</style></head>')
        probe('clipped-canvas', enlarged, 'failed')

report = {'ok': True, 'cases': results, 'scope': 'Synthetic oracles: label fidelity, conditions in table, endpoint/arrow geometry; no claim of repository comprehension accuracy.'}
(outdir / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))

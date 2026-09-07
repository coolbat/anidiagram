#!/usr/bin/env python3
"""Exercise the real Skills installer in fresh project-local directories only."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = 'skills@1.5.24'


def run(command, cwd, **kwargs):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                            env={**os.environ, 'DISABLE_TELEMETRY': '1'}, timeout=180, **kwargs)
    if result.returncode:
        raise RuntimeError(f'{command[0]} exited {result.returncode}: {result.stderr}\n{result.stdout}')
    return result


def verify(directory, *, with_browser=False):
    source = directory / 'source snapshot'
    source.mkdir()
    # Like a repository download: include source and intended edits, not ignored
    # node_modules/venvs/outputs or machine-specific state from this checkout.
    entries = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).decode().split('\0')
    for name in sorted(set(entries) - {''}):
        original = ROOT / name
        if original.is_symlink():
            raise RuntimeError(f'Packaging test does not follow source symlinks: {name}')
        if not original.is_file():
            continue
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, target)
    results = []
    for mode in ('copy', 'symlink'):
        project = directory / (mode + ' consumer')
        project.mkdir()
        args = ['npx', '--yes', INSTALLER, 'add', str(source), '--skill', 'anidiagram',
                '-a', 'codex', 'claude-code', 'cursor', '-y']
        if mode == 'copy':
            args.append('--copy')
        install = run(args, project)
        (project / 'installer.log').write_text(install.stdout + install.stderr)
        # A copied install must not fall back to the original source checkout.
        moved = source.with_name('source temporarily unavailable')
        source.rename(moved)
        try:
            for agent, container in (('codex', '.agents'), ('claude-code', '.claude'), ('cursor', '.agents')):
                skill = project / container / 'skills/anidiagram'
                assert skill.is_symlink() == (mode == 'symlink' and agent == 'claude-code'), f'unexpected {mode} layout for {agent}'
                launcher = skill / 'scripts/run_anidiagram.py'
                command = [sys.executable, '-I', str(launcher)]
                diagnostic = json.loads(run(command + ['--doctor'], project).stdout)
                assert diagnostic['ok'] and diagnostic['skill_root'] == str(skill.resolve()), diagnostic
                assert not diagnostic['capabilities']['browser'], 'isolated install unexpectedly contains browser dependencies'
                output = f'outputs/{agent}'
                result = json.loads(run(command + ['--spec', str(skill / 'tests/fixtures/accuracy/detour-label.diagram.json'),
                                 '--readable-labels', '--formats', 'svg,html,quality', '--runtime-dependency', 'none',
                                 '--outdir', output, '--deliver'], project).stdout)
                assert result['ok'], result
                receipt = json.loads((project / output / 'diagram.delivery.json').read_text())
                assert receipt['status'] == 'committed' and receipt['validation']['quality']['errors'] == 0, receipt
                assert set(receipt['artifacts']) == set(result['outputs']), receipt
                for name, artifact in result['outputs'].items():
                    path = Path(artifact['path'])
                    assert path.parent == (project / output).resolve(), artifact
                    assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact['sha256'], artifact
                    assert receipt['artifacts'][name]['sha256'] == artifact['sha256'], receipt
                source_record = receipt['input']['source']
                assert hashlib.sha256(Path(source_record['path']).read_bytes()).hexdigest() == source_record['sha256'], receipt
                assert not (skill / 'outputs').exists(), 'generated files leaked into installed skill'
                results.append({'agent': agent, 'mode': mode, 'ok': True,
                                'skill_root': str(skill.resolve()), 'output': str(project / output)})
        finally:
            moved.rename(source)
    browser = {'status': 'not-requested'}
    if with_browser:
        project = directory / 'copy consumer'
        skill = project / '.claude/skills/anidiagram'
        command = [sys.executable, '-I', str(skill / 'scripts/run_anidiagram.py')]
        setup = run(['npm', 'ci', '--prefix', str(skill), '--ignore-scripts'], project)
        chromium = run(['node', str(skill / 'node_modules/playwright/cli.js'), 'install', 'chromium'], project)
        (project / 'browser-setup.log').write_text(setup.stdout + setup.stderr + chromium.stdout + chromium.stderr)
        diagnostic = json.loads(run(command + ['--doctor', '--require', 'browser'], project).stdout)
        assert diagnostic['ok'], diagnostic
        output = project / 'outputs/browser'
        result = json.loads(run(command + ['--spec', str(skill / 'tests/fixtures/accuracy/detour-label.diagram.json'),
                            '--readable-labels', '--formats', 'svg,html,quality', '--runtime-dependency', 'inline',
                            '--runtime-source', diagnostic['dependencies']['browser']['gsap'],
                            '--outdir', 'outputs/browser', '--deliver'], project).stdout)
        assert result['ok'], result
        (output / 'doctor.json').write_text(json.dumps(diagnostic, indent=2) + '\n')
        browser = json.loads(run(command + ['visual-check', 'outputs/browser/diagram.html', '--strict-labels'], project).stdout)
        assert browser['ok'] and browser['status'] == 'passed', browser
        assert browser['visual_review'] == 'pending', 'automated check must not fabricate human approval'
    report = {'ok': True, 'installer': INSTALLER, 'cases': results, 'browser': browser,
              'limits': 'Installer layouts and bundled CLI only; no external agent model was run. Basic cases run without browser packages; browser setup is opt-in. Installation paths are temporary and cleaned after the test; retained outputs are evidence copies.'}
    (directory / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outdir', help='Retain diagnostics in a new unique child directory; default cleans up its own temporary files.')
    parser.add_argument('--with-browser', action='store_true', help='Also install npm dependencies into one temporary Skill, install Chromium in the Playwright cache, and run strict browser acceptance.')
    args = parser.parse_args()
    evidence = None
    if args.outdir:
        parent = Path(args.outdir).resolve()
        parent.mkdir(parents=True, exist_ok=True)
        evidence = Path(tempfile.mkdtemp(prefix='skill-install-', dir=parent))
    # Keep the actual installation outside the checkout even when diagnostics
    # go into build/ or outputs/. Node resolves ancestor node_modules directories;
    # testing beneath the development checkout would silently borrow its tools.
    with tempfile.TemporaryDirectory(prefix='anidiagram-skill-install-') as temporary:
        directory = Path(temporary).resolve()
        try:
            verify(directory, with_browser=args.with_browser)
        except Exception as exc:
            (directory / 'failure.json').write_text(json.dumps({'ok': False, 'error': str(exc)}, indent=2) + '\n')
            raise
        finally:
            if evidence:
                for name in ('summary.json', 'failure.json'):
                    if (directory / name).is_file():
                        shutil.copy2(directory / name, evidence / name)
                for mode in ('copy', 'symlink'):
                    project = directory / (mode + ' consumer')
                    saved = evidence / mode
                    saved.mkdir()
                    for name in ('installer.log', 'browser-setup.log'):
                        if (project / name).is_file():
                            shutil.copy2(project / name, saved / name)
                    if (project / 'outputs').is_dir():
                        shutil.copytree(project / 'outputs', saved / 'outputs')
                print(f'Installation diagnostics: {evidence}', file=sys.stderr)


if __name__ == '__main__':
    main()

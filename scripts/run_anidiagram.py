#!/usr/bin/env python3
"""Portable Skill entry point. Resolve bundled code, never change the caller's cwd.

Run with ``python3 -I /absolute/skill/scripts/run_anidiagram.py ...``.
Only --doctor belongs to this wrapper; all other arguments/exit codes are the CLI's.
No automatic downloads, installation, Git checkout or environment mutation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
SKILL_ROOT = Path(__file__).resolve().parents[1]
CORE_FILES = ('SKILL.md', 'src/anidiagram/__init__.py', 'src/anidiagram/cli.py',
              'schemas/diagram-plan-v0.2.schema.json', 'styles/catalog.json',
              'runtime/anidiagram-runtime.js')
CORE_DIRECTORIES = ('assets', 'runtime', 'schemas', 'styles')


def missing_core_files():
    return ([name for name in CORE_FILES if not (SKILL_ROOT / name).is_file()] +
            [name + '/' for name in CORE_DIRECTORIES if not (SKILL_ROOT / name).is_dir()])


def browser_dependencies():
    node = shutil.which('node')
    result = {'node': node, 'playwright': None, 'chromium': None, 'gsap': None,
              'runtime_verification': 'not-run'}
    if not node:
        return result
    # Start resolution at the installed Skill. Node may reuse ancestor packages;
    # report their absolute paths so availability is not mistaken for isolation.
    script = r'''
const {createRequire} = require('node:module');
const fs = require('node:fs');
const req = createRequire(process.argv[1]);
const result = {playwright: null, chromium: null, gsap: null};
try {
  result.playwright = req.resolve('playwright');
  const executable = req('playwright').chromium.executablePath();
  if (fs.existsSync(executable)) result.chromium = executable;
} catch {}
try { result.gsap = req.resolve('gsap/dist/gsap.min.js'); } catch {}
process.stdout.write(JSON.stringify(result));
'''
    try:
        process = subprocess.run([node, '-e', script, str(SKILL_ROOT / 'package.json')],
                                 capture_output=True, text=True, timeout=10, check=False)
        if process.returncode == 0:
            result.update(json.loads(process.stdout))
        else:
            result['diagnostic'] = 'Node dependency probe failed; check the installed Node version.'
    except (OSError, ValueError, subprocess.TimeoutExpired):
        result['diagnostic'] = 'Node dependency probe unavailable or timed out.'
    return result


def doctor(required='core'):
    missing = missing_core_files()
    browser = browser_dependencies()
    try:
        pillow = importlib.util.find_spec('PIL') is not None
    except (ImportError, ValueError):
        pillow = False
    ffmpeg = shutil.which('ffmpeg')
    core = not missing and sys.version_info >= (3, 9)
    capabilities = {'core': core, 'repository_evidence': core and bool(shutil.which('git')),
                    'browser': core and bool(browser['playwright'] and browser['chromium']),
                    'inline_html': core and bool(browser['gsap']),
                    'raster': core and pillow,
                    'video': core and bool(browser['playwright'] and browser['chromium'] and ffmpeg)}
    return {'schema': {'name': 'AniDiagramSkillDoctor', 'version': '0.1'},
            'ok': capabilities[required], 'required': required, 'skill_root': str(SKILL_ROOT),
            'working_directory': str(Path.cwd().resolve()),
            'engine': str(SKILL_ROOT / 'src/anidiagram/cli.py'),
            'python': {'executable': sys.executable, 'version': sys.version.split()[0]},
            'missing_core_files': missing, 'capabilities': capabilities,
            'dependencies': {'git': shutil.which('git'), 'browser': browser, 'pillow': pillow, 'ffmpeg': ffmpeg},
            'limits': 'Availability only, not browser launch, render success, or semantic approval. No dependencies were installed.',
            'setup_guide': str(SKILL_ROOT / 'docs/agent-skill.md')}


def main():
    arguments = sys.argv[1:]
    if arguments and arguments[0] == '--doctor':
        parser = argparse.ArgumentParser(description='Read-only Skill dependency check; never installs tools.')
        parser.add_argument('--doctor', action='store_true')
        parser.add_argument('--require', default='core', choices=('core', 'repository_evidence', 'browser', 'inline_html', 'raster', 'video'))
        args = parser.parse_args(arguments)
        report = doctor(args.require)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report['ok'] else 2
    missing = missing_core_files()
    if missing or sys.version_info < (3, 9):
        print(json.dumps({'ok': False, 'error': {'code': 'skill_install_incomplete',
              'message': 'Use Python 3.9+ and install the whole AniDiagram Skill directory, not SKILL.md alone.',
              'missing': missing}}, ensure_ascii=False), file=sys.stderr)
        return 2
    sys.path.insert(0, str(SKILL_ROOT / 'src'))
    from anidiagram.cli import main as cli_main
    cli_main(arguments)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

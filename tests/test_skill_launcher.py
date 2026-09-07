"""Run a copied Skill from a foreign project without an installed AniDiagram CLI."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SkillLauncherTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='anidiagram skill ')
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.base = Path(cls.temporary.name)
        cls.skill = cls.base / 'installed skill'
        for directory in ('src', 'assets', 'styles', 'schemas', 'runtime'):
            shutil.copytree(ROOT / directory, cls.skill / directory,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        (cls.skill / 'scripts').mkdir()
        cls.launcher = cls.skill / 'scripts/run_anidiagram.py'
        if (ROOT / 'scripts/run_anidiagram.py').exists():
            shutil.copy2(ROOT / 'scripts/run_anidiagram.py', cls.launcher)
        shutil.copy2(ROOT / 'SKILL.md', cls.skill / 'SKILL.md')
        shutil.copy2(ROOT / 'package.json', cls.skill / 'package.json')

    def setUp(self):
        self.project = Path(tempfile.mkdtemp(prefix='consumer ', dir=self.base))

    def run_skill(self, *args, launcher=None, env=None):
        return subprocess.run([sys.executable, '-I', str(launcher or self.launcher), *args],
                              cwd=self.project, capture_output=True, text=True,
                              env=env, timeout=30)

    def test_copy_renders_into_consumer_with_no_installed_cli_or_pythonpath(self):
        (self.project / 'anidiagram.py').write_text('raise RuntimeError("wrong module")')
        before = {str(p.relative_to(self.skill)) for p in self.skill.rglob('*')}
        result = self.run_skill('--preset', 'agent-memory', '--formats', 'svg,html,quality',
                                '--outdir', 'my diagrams', '--runtime-dependency', 'none', '--deliver')
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report['ok'])
        self.assertTrue((self.project / 'my diagrams/diagram.delivery.json').is_file())
        self.assertEqual(before, {str(p.relative_to(self.skill)) for p in self.skill.rglob('*')})

    def test_symlink_preserves_relative_input_and_output_paths(self):
        link = self.project / 'skill link'
        link.symlink_to(self.skill, target_is_directory=True)
        shutil.copy2(ROOT / 'tests/fixtures/accuracy/detour-label.diagram.json', self.project / 'input.json')
        result = self.run_skill('--spec', 'input.json', '--readable-labels', '--formats', 'svg,html,quality',
                                '--runtime-dependency', 'none', '--outdir', 'output', '--deliver',
                                launcher=link / 'scripts/run_anidiagram.py')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue('id="relation-table"' in (self.project / 'output/diagram.html').read_text())

    def test_doctor_is_read_only_and_reports_missing_optional_tools(self):
        result = self.run_skill('--doctor', env={**os.environ, 'PATH': ''})
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(str(self.skill.resolve()), report['skill_root'])
        self.assertEqual(str(self.project.resolve()), report['working_directory'])
        self.assertTrue(report['capabilities']['core'])
        self.assertFalse(report['capabilities']['browser'])
        self.assertFalse(report['capabilities']['video'])
        self.assertEqual([], list(self.project.iterdir()))

    def test_missing_required_browser_never_passes_doctor(self):
        result = self.run_skill('--doctor', '--require', 'browser', env={**os.environ, 'PATH': ''})
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertFalse(json.loads(result.stdout)['ok'])

    def test_incomplete_install_does_not_fall_back_to_another_engine(self):
        partial = self.project / 'partial skill/scripts'
        partial.mkdir(parents=True)
        self.assertTrue(self.launcher.is_file(), 'portable launcher is missing')
        shutil.copy2(self.launcher, partial / self.launcher.name)
        result = self.run_skill('--doctor', launcher=partial / self.launcher.name)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertTrue(json.loads(result.stdout)['missing_core_files'])

    def test_accuracy_command_preserves_strict_exit_code_and_local_report(self):
        shutil.copy2(ROOT / 'tests/fixtures/accuracy/detour-label.diagram.json', self.project / 'input.json')
        facts = {'version': '0.1', 'claims': [{'id': 'unresolved', 'subject': 'source',
                 'predicate': 'behavior', 'object': 'Unverified project behavior',
                 'condition': '', 'source_refs': [], 'confidence': 'unknown'}]}
        (self.project / 'facts.json').write_text(json.dumps(facts))
        result = self.run_skill('accuracy-check', 'input.json', '--facts', 'facts.json', '--strict', '--out', 'accuracy.json')
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertFalse(json.loads((self.project / 'accuracy.json').read_text())['ready'])

    def test_invalid_input_preserves_cli_error(self):
        result = self.run_skill('--not-a-real-option')
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn('unrecognized arguments', result.stderr)

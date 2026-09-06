import copy
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

from anidiagram.cli import main
from anidiagram.planner import compile_plan
from anidiagram.renderer_html_runtime import render_html_runtime
from anidiagram.repository_evidence import EvidenceError, validate_repository
from anidiagram.schema import compile_scene, DiagramScriptValidationError
from anidiagram.styles import load_style

ROOT = Path(__file__).resolve().parents[1]


class RepositoryEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Evidence Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("remote", "add", "origin", "git@github.com:example/demo.git")
        (self.root / "module.py").write_text("# source\nvalue = 1\n")
        (self.root / "linked.py").symlink_to("module.py")
        self.git("add", "module.py", "linked.py")
        self.git("commit", "-qm", "fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.ref = {"url": "https://github.com/example/demo", "revision": self.revision,
                    "path": "module.py", "line": 1, "end_line": 2}
        self.plan = json.loads((ROOT / "examples/contracts/production-request-path.plan.json").read_text())
        self.plan["semantic"]["sources"] = [{"id": "code", "type": "repository", "repository": self.ref}]
        self.plan["semantic"]["entities"][0]["source_refs"] = ["code"]

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], text=True, stderr=subprocess.PIPE)

    def test_reads_pinned_blob_even_when_worktree_changes(self):
        spec = compile_plan(self.plan)
        (self.root / "module.py").write_text("uncommitted\n")
        scene = compile_scene(spec, repo_root=self.root)
        self.assertEqual("references-verified", scene.source_evidence["status"])
        source = scene.source_evidence["sources"][0]
        self.assertEqual(19, source["bytes"])
        self.assertIn(self.revision + "/module.py#L1-L2", source["href"])
        html = render_html_runtime(scene, load_style())
        self.assertIn(source["href"], html)
        self.assertIn("architectural claims still need review", html)

    def test_plain_provenance_still_needs_no_git(self):
        self.plan["semantic"]["sources"][0].pop("repository")
        spec = compile_plan(self.plan)
        self.assertNotIn("evidence", spec)
        self.assertEqual({}, compile_scene(spec).source_evidence)

    def test_invalid_paths_and_lines_rejected(self):
        for change in ({"path": "../secret"}, {"path": "/etc/passwd"}, {"path": ".git/config"},
                       {"path": "foo\\bar"}, {"line": True}, {"line": 3}, {"path": "linked.py"},
                       {"path": "missing.py"}, {"revision": "main"}, {"url": "https://github.com/wrong/repo"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                plan = copy.deepcopy(self.plan)
                plan["semantic"]["sources"][0]["repository"].update(change)
                compile_scene(compile_plan(plan), repo_root=self.root)

    def test_cannot_claim_verification_without_repository(self):
        spec = compile_plan(self.plan)
        with self.assertRaisesRegex(DiagramScriptValidationError, "repo-root"):
            compile_scene(spec)
        spec["evidence"]["verified"] = True
        with self.assertRaisesRegex(DiagramScriptValidationError, "verified status"):
            compile_scene(spec, repo_root=self.root)

    def test_delivery_includes_receipt_and_failure_preserves_last_good(self):
        source = self.root / "plan.json"
        source.write_text(json.dumps(self.plan))
        args = ["--plan", str(source), "--repo-root", str(self.root), "--outdir", str(self.root),
                "--basename", "proof", "--formats", "svg,html,quality", "--deliver"]
        with redirect_stdout(io.StringIO()):
            main(args)
        receipt = json.loads((self.root / "proof.delivery.json").read_text())
        self.assertEqual(self.revision, receipt["evidence"]["sources"][0]["repository"]["revision"])
        before = (self.root / "proof.html").read_bytes()
        self.ref["line"] = 100
        self.ref["end_line"] = 101
        source.write_text(json.dumps(self.plan))
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            main(args)
        self.assertEqual(2, raised.exception.code)
        self.assertEqual(before, (self.root / "proof.html").read_bytes())

    def test_script_evidence_revalidates_source_shape(self):
        for change in ({"type": None}, {"type": "invalid type"}, {"title": []}, {"uri": 1}, {"note": {}}):
            spec = compile_plan(self.plan)
            spec["evidence"]["sources"][0].update(change)
            with self.subTest(change=change), self.assertRaises(DiagramScriptValidationError):
                compile_scene(spec, repo_root=self.root)
        spec = compile_plan(self.plan)
        subject = next(iter(spec["evidence"]["subjects"]))
        spec["evidence"]["subjects"][subject].append("code")
        with self.assertRaisesRegex(DiagramScriptValidationError, "unique"):
            compile_scene(spec, repo_root=self.root)

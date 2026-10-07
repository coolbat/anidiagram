import hashlib
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from anidiagram.cli import main


ROOT = Path(__file__).resolve().parents[1]


class AtomicDeliveryTest(unittest.TestCase):
    def _run(self, outdir: Path, spec_path: Path, basename: str = "minimal", extra=None):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            arguments = [
                "--spec",
                str(spec_path),
                "--style",
                str(ROOT / "styles" / "minimal-light.json"),
                "--outdir",
                str(outdir),
                "--basename",
                basename,
                "--formats",
                "svg,quality",
                "--deliver",
            ]
            main(arguments + list(extra or []))
        return json.loads(stdout.getvalue())

    def _assert_no_private_delivery_files(self, outdir: Path, basename: str = "minimal"):
        self.assertEqual([], list(outdir.glob(f".{basename}.deliver-*")))

    def test_cli_delivers_all_artifacts_and_sha256_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp)
            spec_path = ROOT / "tests" / "fixtures" / "minimal.diagram.json"
            old_paths = {
                "svg": outdir / "minimal.svg",
                "quality": outdir / "minimal.quality.json",
                "receipt": outdir / "minimal.delivery.json",
            }
            for path in old_paths.values():
                path.write_bytes(b"last-good")

            result = self._run(outdir, spec_path)
            receipt_path = old_paths["receipt"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

            self.assertTrue(result["ok"])
            self.assertEqual("committed", result["delivery"]["status"])
            self.assertEqual(
                {"name": "AniDiagramDeliveryReceipt", "version": "0.1"},
                receipt["schema"],
            )
            self.assertEqual(
                hashlib.sha256(spec_path.read_bytes()).hexdigest(),
                receipt["input"]["source"]["sha256"],
            )
            self.assertEqual("spec", receipt["input"]["source"]["kind"])
            self.assertEqual("DiagramScript", receipt["input"]["specification"]["schema"])
            self.assertEqual("0.1", receipt["input"]["specification"]["version"])
            self.assertEqual("openai-minimal", receipt["input"]["style"]["name"])
            self.assertEqual(0, receipt["validation"]["quality"]["errors"])
            self.assertEqual(["svg", "quality"], list(receipt["artifacts"]))
            for format_name, artifact in receipt["artifacts"].items():
                path = Path(artifact["path"])
                self.assertTrue(path.is_file())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), artifact["sha256"])
                self.assertEqual(path.stat().st_size, artifact["bytes"])
                self.assertEqual(artifact["sha256"], result["outputs"][format_name]["sha256"])
                self.assertNotIn(".deliver-", result["outputs"][format_name]["path"])
            self.assertEqual(
                hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
                result["delivery"]["receipt"]["sha256"],
            )
            self._assert_no_private_delivery_files(outdir)

    def test_compiled_spec_is_committed_in_the_same_transaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp)
            spec_out = outdir / "production.diagram.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(
                    [
                        "--plan",
                        str(ROOT / "examples" / "contracts" / "production-request-path.plan.json"),
                        "--outdir",
                        str(outdir),
                        "--basename",
                        "production",
                        "--formats",
                        "svg,quality",
                        "--spec-out",
                        str(spec_out),
                        "--deliver",
                    ]
                )

            result = json.loads(stdout.getvalue())
            receipt = json.loads((outdir / "production.delivery.json").read_text(encoding="utf-8"))
            artifact = receipt["artifacts"]["compiled_specification"]

            self.assertTrue(result["ok"])
            self.assertTrue(spec_out.is_file())
            self.assertEqual(hashlib.sha256(spec_out.read_bytes()).hexdigest(), artifact["sha256"])
            self.assertEqual(artifact, result["delivery"]["supplemental_artifacts"]["compiled_specification"])
            self._assert_no_private_delivery_files(outdir, "production")

    def test_inline_runtime_dependency_is_frozen_before_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp)
            runtime_source = outdir / "gsap.min.js"
            frozen_bytes = b"window.gsap = { frozen: true };"
            runtime_source.write_bytes(frozen_bytes)

            def write_frozen_html(_scene, _style, path, **kwargs):
                runtime_source.write_bytes(b"mutated after delivery started")
                dependency_source = kwargs["dependency_source"]
                self.assertNotEqual(runtime_source, dependency_source)
                self.assertEqual(frozen_bytes, dependency_source.read_bytes())
                path.write_text("<!doctype html><title>frozen</title>", encoding="utf-8")
                return {"format": "html", "path": str(path), "status": "written"}

            stdout = io.StringIO()
            with patch("anidiagram.cli.write_html", side_effect=write_frozen_html), redirect_stdout(stdout):
                main(
                    [
                        "--spec",
                        str(ROOT / "tests" / "fixtures" / "minimal.diagram.json"),
                        "--outdir",
                        str(outdir),
                        "--basename",
                        "runtime",
                        "--formats",
                        "html",
                        "--runtime-dependency",
                        "inline",
                        "--runtime-source",
                        str(runtime_source),
                        "--deliver",
                    ]
                )

            result = json.loads(stdout.getvalue())
            receipt = json.loads((outdir / "runtime.delivery.json").read_text(encoding="utf-8"))
            dependency = receipt["request"]["render_options"]["runtime_source"]

            self.assertTrue(result["ok"])
            self.assertEqual(hashlib.sha256(frozen_bytes).hexdigest(), dependency["sha256"])
            self.assertEqual(len(frozen_bytes), dependency["bytes"])
            self._assert_no_private_delivery_files(outdir, "runtime")

    def test_quality_failure_preserves_last_good_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp)
            spec = json.loads((ROOT / "tests" / "fixtures" / "minimal.diagram.json").read_text(encoding="utf-8"))
            spec["nodes"][1]["position"] = [90, 155]
            spec_path = outdir / "overlap.diagram.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            targets = [
                outdir / "minimal.svg",
                outdir / "minimal.quality.json",
                outdir / "minimal.delivery.json",
            ]
            for index, path in enumerate(targets):
                path.write_bytes(f"last-good-{index}".encode())
            before = {path: path.read_bytes() for path in targets}
            stderr = io.StringIO()

            with self.assertRaises(SystemExit) as raised, redirect_stderr(stderr):
                self._run(outdir, spec_path)

            error = json.loads(stderr.getvalue())
            self.assertEqual(3, raised.exception.code)
            self.assertFalse(error["ok"])
            self.assertEqual("quality", error["delivery"]["stage"])
            self.assertGreater(error["validation"]["quality"]["errors"], 0)
            self.assertEqual("node_overlap", error["diagnostics"]["issues"][0]["code"])
            self.assertEqual(before, {path: path.read_bytes() for path in targets})
            self._assert_no_private_delivery_files(outdir)

    def test_skipped_export_preserves_last_good_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp)
            spec_path = ROOT / "tests" / "fixtures" / "minimal.diagram.json"
            targets = [
                outdir / "minimal.svg",
                outdir / "minimal.quality.json",
                outdir / "minimal.delivery.json",
            ]
            for index, path in enumerate(targets):
                path.write_bytes(f"last-good-{index}".encode())
            before = {path: path.read_bytes() for path in targets}

            def skip_svg(_scene, _style, path):
                return {"format": "svg", "path": str(path), "status": "skipped", "reason": "test skip"}

            stderr = io.StringIO()
            with patch.dict("anidiagram.cli.EXPORTERS", {"svg": skip_svg}), redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    self._run(outdir, spec_path)

            error = json.loads(stderr.getvalue())
            self.assertEqual(3, raised.exception.code)
            self.assertEqual("render", error["delivery"]["stage"])
            self.assertIn("test skip", error["error"]["message"])
            self.assertEqual(before, {path: path.read_bytes() for path in targets})
            self._assert_no_private_delivery_files(outdir)

    def test_commit_failure_rolls_back_every_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp)
            spec_path = ROOT / "tests" / "fixtures" / "minimal.diagram.json"
            targets = [
                outdir / "minimal.svg",
                outdir / "minimal.quality.json",
                outdir / "minimal.delivery.json",
            ]
            for index, path in enumerate(targets):
                path.write_bytes(f"last-good-{index}".encode())
            before = {path: path.read_bytes() for path in targets}
            real_replace = os.replace
            failed = False

            def fail_quality_commit(source, target):
                nonlocal failed
                source_path = Path(source)
                target_path = Path(target)
                if (
                    not failed
                    and source_path.name == "minimal.quality.json"
                    and target_path == targets[1].resolve()
                ):
                    failed = True
                    raise OSError("injected commit failure")
                return real_replace(source, target)

            stderr = io.StringIO()
            with patch(
                "anidiagram.delivery.os.replace",
                side_effect=fail_quality_commit,
            ), redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    self._run(outdir, spec_path)

            error = json.loads(stderr.getvalue())
            self.assertEqual(3, raised.exception.code)
            self.assertEqual("commit", error["delivery"]["stage"])
            self.assertEqual(before, {path: path.read_bytes() for path in targets})
            self._assert_no_private_delivery_files(outdir)

    def test_rollback_failure_retains_private_recovery_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp)
            spec_path = ROOT / "tests" / "fixtures" / "minimal.diagram.json"
            targets = [
                outdir / "minimal.svg",
                outdir / "minimal.quality.json",
                outdir / "minimal.delivery.json",
            ]
            for index, path in enumerate(targets):
                path.write_bytes(f"last-good-{index}".encode())
            real_replace = os.replace
            commit_failed = False

            def fail_commit_and_quality_restore(source, target):
                nonlocal commit_failed
                source_path = Path(source)
                target_path = Path(target)
                if (
                    not commit_failed
                    and source_path.name == "minimal.quality.json"
                    and target_path == targets[1].resolve()
                ):
                    commit_failed = True
                    raise OSError("injected commit failure")
                if (
                    commit_failed
                    and source_path.parent.name == ".backup"
                    and target_path == targets[1].resolve()
                ):
                    raise OSError("injected rollback failure")
                return real_replace(source, target)

            stderr = io.StringIO()
            with patch(
                "anidiagram.delivery.os.replace",
                side_effect=fail_commit_and_quality_restore,
            ), redirect_stderr(stderr):
                with self.assertRaises(SystemExit):
                    self._run(outdir, spec_path)

            error = json.loads(stderr.getvalue())
            recovery_path = Path(error["delivery"]["recovery_path"])
            backup = recovery_path / ".backup" / "001-minimal.quality.json"

            self.assertTrue(recovery_path.is_dir())
            self.assertEqual(b"last-good-1", backup.read_bytes())
            self.assertIn("rollback errors", error["error"]["message"])


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_icon_system_release_evidence as release_evidence


ROOT = Path(__file__).resolve().parents[1]


class ReleaseWorkflowContractTest(unittest.TestCase):
    def _read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_pr_and_main_workflow_enforces_current_public_contracts(self):
        workflow = self._read(".github/workflows/test.yml")

        for command in (
            "PYTHONPATH=src python3 -m unittest discover -s tests",
            "PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --strict --json",
            "node --check runtime/anidiagram-runtime.js",
            "node --check runtime/illustrated-performance-v6-runtime.js",
            "node --check runtime/edge-motion-v1-runtime.js",
            "node --check runtime/choreographer-v1-runtime.js",
            "examples/illustrated-2.5-showcase.diagram.json",
            "examples/illustrated-2.5-release-case.diagram.json",
            "verify_character_motion_rest.mjs",
            "verify_character_reduced_motion.mjs",
            "56 illustrated",
            "13 illustrated",
            "illustrated-2.5-release-case.html 13 13 2",
            "examples/contracts/production-request-path.plan.json",
            "verify_stage_motion_modes.mjs",
            "verify_choreographer.mjs",
            "verify_readme_showcase_round_1.mjs",
            "scripts/check_asset_budget.py",
            "--runtime-mode timeline",
            "--runtime-mode hybrid",
        ):
            with self.subTest(command=command):
                self.assertIn(command, workflow)

        self.assertIn("npm ci", workflow)
        self.assertIn("playwright install --with-deps chromium", workflow)
        self.assertIn('python-version: ["3.9", "3.11", "3.14"]', workflow)
        self.assertIn("python3 -m pip wheel . --no-deps --wheel-dir build/wheels", workflow)
        self.assertIn("--runtime-dependency none", workflow)

    def test_contract_job_installs_node_dependencies_before_unit_tests(self):
        workflow = self._read(".github/workflows/test.yml")
        contract_job = workflow.split("  runtime-browser:", 1)[0]

        self.assertIn("npm ci", contract_job)
        self.assertLess(
            contract_job.index("npm ci"),
            contract_job.index("PYTHONPATH=src python3 -m unittest discover -s tests"),
        )

    def test_manual_release_evidence_workflow_retains_the_formal_matrix(self):
        workflow = self._read(".github/workflows/icon-system-release-evidence.yml")

        for contract in (
            "workflow_dispatch:",
            "python3 -m pip install -e \".[raster]\"",
            "npm ci",
            "playwright install --with-deps chromium",
            'system: ["diagram-core-v1", "illustrated-2.5"]',
            'shard: ["static", "webp", "gif", "apng", "mp4", "pdf", "lottie", "quality"]',
            '--system "${{ matrix.system }}" --shard "${{ matrix.shard }}"',
            "actions/download-artifact@v4",
            "merge-multiple: true",
            "scripts/build_icon_system_release_evidence.py --merge-fragments",
            "scripts/build_icon_system_release_evidence.py --verify",
            "actions/upload-artifact@v4",
            "outputs/release-evidence/icon-systems",
            "retention-days: 14",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, workflow)

        build_step = workflow.split("- name: Build one public icon-system evidence fragment", 1)[1].split(
            "- name: Upload public icon-system evidence fragment", 1
        )[0]
        self.assertIn("timeout-minutes: 20", build_step)

    def test_release_evidence_fragments_merge_in_public_system_order(self):
        capture = {"renderer": "browser", "fps": 24, "frames": 108, "scale": 2.0}
        formats = list(release_evidence.EXPORT_FORMATS)
        fragments = [
            {
                "schema": "public-icon-system-export-evidence-fragment-v1",
                "capture": capture,
                "formats": formats,
                "system": {"id": "illustrated-2.5"},
            },
            {
                "schema": "public-icon-system-export-evidence-fragment-v1",
                "capture": capture,
                "formats": formats,
                "system": {"id": "diagram-core-v1"},
            },
        ]

        merged = release_evidence._merge_fragment_documents(fragments)

        self.assertEqual("public-icon-system-export-evidence-v1", merged["schema"])
        self.assertEqual(["diagram-core-v1", "illustrated-2.5"], [item["id"] for item in merged["systems"]])

    def test_release_evidence_fragments_require_both_public_systems(self):
        fragment = {
            "schema": "public-icon-system-export-evidence-fragment-v1",
            "capture": {"renderer": "browser", "fps": 24, "frames": 108, "scale": 2.0},
            "formats": list(release_evidence.EXPORT_FORMATS),
            "system": {"id": "diagram-core-v1"},
        }

        with self.assertRaisesRegex(ValueError, "expected fragments"):
            release_evidence._merge_fragment_documents([fragment])

    def test_release_evidence_format_shards_partition_the_formal_matrix(self):
        flattened = [
            format_name
            for formats in release_evidence.FORMAT_SHARDS.values()
            for format_name in formats
        ]

        self.assertEqual(list(release_evidence.EXPORT_FORMATS), flattened)
        self.assertEqual(len(flattened), len(set(flattened)))

    def test_release_evidence_format_shards_merge_into_complete_system_results(self):
        capture = {"renderer": "browser", "fps": 24, "frames": 108, "scale": 2.0}
        with tempfile.TemporaryDirectory() as directory:
            outdir = Path(directory)
            fragments = []
            for case in release_evidence.CASES:
                case_outdir = outdir / case["id"]
                case_outdir.mkdir()
                for shard_id, formats in release_evidence.FORMAT_SHARDS.items():
                    outputs = {format_name: {"status": "written"} for format_name in formats}
                    result_path = case_outdir / f"result-{shard_id}.json"
                    result_path.write_text(
                        json.dumps({"ok": True, "icon_system": case["icon_system"], "outputs": outputs}),
                        encoding="utf-8",
                    )
                    fragments.append(
                        {
                            "schema": release_evidence.SHARD_SCHEMA,
                            "shard": shard_id,
                            "capture": capture,
                            "formats": list(formats),
                            "system": {
                                "id": case["id"],
                                "icon_system": case["icon_system"],
                                "result": {"path": str(result_path)},
                                "artifacts": outputs,
                            },
                        }
                    )

            merged = release_evidence._merge_shard_fragment_documents(fragments, outdir)

            self.assertEqual(2, len(merged["systems"]))
            for system in merged["systems"]:
                self.assertEqual(list(release_evidence.EXPORT_FORMATS), list(system["artifacts"]))
                result = json.loads((outdir / system["id"] / "result.json").read_text(encoding="utf-8"))
                self.assertEqual(set(release_evidence.EXPORT_FORMATS), set(result["outputs"]))

    def test_release_status_documents_ci_scope_and_retention(self):
        status = self._read("docs/icon-system-release-status.md")

        self.assertIn(".github/workflows/test.yml", status)
        self.assertIn(".github/workflows/icon-system-release-evidence.yml", status)
        self.assertIn("14 days", status)
        self.assertIn("workflow_dispatch", status)


if __name__ == "__main__":
    unittest.main()

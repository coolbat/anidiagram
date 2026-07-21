import unittest
from pathlib import Path


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
            "examples/illustrated-2.3-showcase.diagram.json",
            "verify_character_motion_rest.mjs",
            "verify_character_reduced_motion.mjs",
            "16 illustrated",
            "examples/contracts/production-request-path.plan.json",
            "verify_stage_motion_modes.mjs",
        ):
            with self.subTest(command=command):
                self.assertIn(command, workflow)

        self.assertIn("npm ci", workflow)
        self.assertIn("playwright install --with-deps chromium", workflow)

    def test_manual_release_evidence_workflow_retains_the_formal_matrix(self):
        workflow = self._read(".github/workflows/icon-system-release-evidence.yml")

        for contract in (
            "workflow_dispatch:",
            "python3 -m pip install -e \".[raster]\"",
            "npm ci",
            "playwright install --with-deps chromium",
            "scripts/build_icon_system_release_evidence.py",
            "scripts/build_icon_system_release_evidence.py --verify",
            "actions/upload-artifact@v4",
            "outputs/release-evidence/icon-systems",
            "retention-days: 14",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, workflow)

    def test_release_status_documents_ci_scope_and_retention(self):
        status = self._read("docs/icon-system-release-status.md")

        self.assertIn(".github/workflows/test.yml", status)
        self.assertIn(".github/workflows/icon-system-release-evidence.yml", status)
        self.assertIn("14 days", status)
        self.assertIn("workflow_dispatch", status)


if __name__ == "__main__":
    unittest.main()

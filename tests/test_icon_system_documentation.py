import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class IconSystemDocumentationTest(unittest.TestCase):
    def _read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_current_and_legacy_defaults_are_scoped(self):
        for relative in (
            "README.md",
            "README.zh-CN.md",
            "SKILL.md",
            "docs/icon-system-release-status.md",
        ):
            source = self._read(relative)
            with self.subTest(relative=relative):
                self.assertIn("composition-v1", source)
                self.assertIn("diagram-core-v1", source)
                self.assertIn("showcase-v1", source)
                self.assertIn("illustrated-character-v1", source)
                self.assertIn("expressive", source.lower())

        self.assertIn("composition-v1 default", self._read("README.md"))
        self.assertIn("composition-v1 默认", self._read("README.zh-CN.md"))
        self.assertNotIn("Diagram Core 默认值", self._read("README.zh-CN.md"))
        self.assertIn("Direct manually authored DiagramScript v0.4", self._read("SKILL.md"))

        adr = self._read("docs/decisions/ADR-001-separate-semantic-content-from-presentation.md")
        self.assertIn("illustrated` (implementation", adr)
        self.assertIn("retain the\n  `diagram-core-v1` omission default", adr)

    def test_illustrated_25_public_contract_is_current_and_composition_default(self):
        for relative in (
            "README.md",
            "README.zh-CN.md",
            "SKILL.md",
            "docs/diagram-script.md",
            "docs/html-runtime.md",
            "docs/icon-system-release-status.md",
        ):
            source = self._read(relative)
            with self.subTest(relative=relative):
                self.assertIn("2.5.0", source)
                self.assertIn("illustrated-performance-v6", source)

        status = self._read("docs/icon-system-release-status.md")
        self.assertIn("Yes, for composition-v1", status)
        self.assertIn("No; select explicitly", status)
        self.assertIn("56 performances", status)
        self.assertIn("v6/v7 review contracts", status)

    def test_fifty_six_item_runtime_gates_are_documented(self):
        for relative in (
            "SKILL.md",
            "docs/html-runtime.md",
            "docs/icon-system-release-status.md",
        ):
            source = self._read(relative)
            with self.subTest(relative=relative):
                self.assertIn("verify_character_motion_rest.mjs", source)
                self.assertIn("verify_character_reduced_motion.mjs", source)
                self.assertIn("verify_stage_motion_modes.mjs", source)
                self.assertGreaterEqual(source.count("56 illustrated"), 2)

    def test_closeout_record_contains_observed_pass_evidence(self):
        evidence = self._read("docs/release-evidence.md")
        self.assertIn("Evidence E-COMP-01 — passed", evidence)
        self.assertIn("176/176 Python tests passed", evidence)
        self.assertIn("minimum of 3 distinct states for Diagram Core", evidence)
        self.assertIn("Blocker class: none", evidence)

    def test_showcase_motion_is_not_documented_as_a_motion_policy_profile(self):
        readme = self._read("README.md")
        policy = readme.split("### Motion Policy", 1)[1].split("### Node Motion Types", 1)[0]
        self.assertIn("`motion_policy.profile=unrestricted`", policy)
        self.assertNotIn("| `showcase-v1` |", policy)

        readme_zh = self._read("README.zh-CN.md")
        policy_zh = readme_zh.split("### 动效预算", 1)[1].split("### 节点动效", 1)[0]
        self.assertIn("`motion_policy.profile=unrestricted`", policy_zh)
        self.assertNotIn("| `showcase-v1` |", policy_zh)


if __name__ == "__main__":
    unittest.main()

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

from anidiagram.diagram_core.catalog import (
    CATALOG_IDS,
    CATALOG_STATUSES,
    CATALOG_SYSTEM_ID,
    LEGACY_VALID_ICON_IDS,
    approved_icon_ids,
    catalog_entry,
    diagram_script_valid_icon_ids,
    legacy_valid_icon_ids,
    load_catalog,
)
from anidiagram.schema import KNOWN_ICONS, compile_scene, validate_scene


ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = ROOT / "scripts" / "sync_diagram_script_icons.py"

EXPECTED_BY_CATEGORY = {
    "actors": (
        "user", "developer", "operator", "agent", "agent-team",
        "assistant", "human-reviewer",
    ),
    "ai-models": (
        "ai-model", "llm", "neural-network", "reasoning",
        "embedding", "memory", "tool", "token",
    ),
    "data-knowledge": (
        "database", "vector-database", "data-warehouse",
        "document-store", "knowledge-base", "dataset", "search",
    ),
    "files-content": (
        "file", "folder", "document", "pdf", "image",
        "audio", "video", "code-file", "output",
    ),
    "network-interfaces": (
        "api", "webhook", "http-request", "gateway",
        "load-balancer", "message-queue", "shield",
    ),
    "compute-runtime": (
        "server", "server-cluster", "cloud",
        "container", "function", "edge-node",
    ),
    "development-delivery": (
        "source-code", "git-repository", "branch",
        "pull-request", "ci-cd", "deployment",
    ),
    "operations-observability": (
        "task", "scheduler", "monitoring", "logs", "alert", "debug",
    ),
}

EXPECTED_BENCHMARKS = {
    "agent": {
        "prototype": "actor-character",
        "parts": (
            "shell", "face-screen", "eye-left", "eye-right", "mouth",
            "antenna", "core", "indicator",
        ),
        "actions": ("enter", "receive", "process", "send"),
    },
    "database": {
        "prototype": "stacked-storage",
        "parts": (
            "shell", "top-ring", "layer-top", "layer-middle",
            "layer-bottom", "core", "indicator",
        ),
        "actions": ("receive", "write", "index", "search", "send"),
    },
    "api": {
        "prototype": "interface-module",
        "parts": (
            "shell", "header", "input-interface", "output-interface",
            "processor", "indicator-group",
        ),
        "actions": ("receive", "process", "send", "stream"),
    },
    "server": {
        "prototype": "compute-device",
        "parts": (
            "shell", "tray-top", "tray-bottom", "indicator-top",
            "indicator-bottom", "vent-top", "vent-bottom", "base",
        ),
        "actions": ("enter", "receive", "process", "send"),
    },
}

EXPECTED_STATES = (
    "idle", "active", "processing", "success", "warning", "error",
)

REQUIRED_ICON_FIELDS = {
    "id",
    "category",
    "semantic_kind",
    "structural_prototype",
    "aliases",
    "parts",
    "supported_states",
    "supported_actions",
    "status",
    "asset_revision",
}


def catalog_fixture_with_status(catalog, icon_id, status):
    return replace(
        catalog,
        entries=tuple(
            replace(entry, status=status) if entry.icon_id == icon_id else entry
            for entry in catalog.entries
        ),
    )


def scene_spec_with_icon(icon_id):
    return {
        "version": "0.3",
        "nodes": [
            {
                "id": "icon-node",
                "label": "Icon node",
                "position": [100, 100],
                "size": [160, 80],
                "icon": icon_id,
            }
        ],
    }


def run_schema_sync(script_path, *arguments):
    return subprocess.run(
        [sys.executable, str(script_path), *arguments],
        cwd=script_path.parents[1],
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )


def copy_sync_fixture(temp_dir, icon_ids):
    fixture_root = Path(temp_dir)
    scripts_dir = fixture_root / "scripts"
    schemas_dir = fixture_root / "schemas"
    scripts_dir.mkdir()
    schemas_dir.mkdir()
    script_path = scripts_dir / SYNC_SCRIPT.name
    schema_path = schemas_dir / "diagram-script-v0.3.schema.json"
    shutil.copyfile(SYNC_SCRIPT, script_path)

    source_path = ROOT / "schemas" / schema_path.name
    lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)
    for index, line in enumerate(lines):
        if '"icon": {"enum":' in line:
            newline = "\n" if line.endswith("\n") else ""
            lines[index] = f'    "icon": {{"enum": {json.dumps(icon_ids)}}},{newline}'
            break
    else:
        raise AssertionError("DiagramScript icon enum line is missing")
    with schema_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("".join(lines))
    return script_path, schema_path


class DiagramCoreCatalogTest(unittest.TestCase):
    def test_catalog_freezes_exact_inventory_and_category_counts(self):
        catalog = load_catalog()
        actual = {
            category: tuple(
                entry.icon_id
                for entry in catalog.entries
                if entry.category == category
            )
            for category in EXPECTED_BY_CATEGORY
        }

        self.assertEqual(EXPECTED_BY_CATEGORY, actual)
        self.assertEqual([7, 8, 7, 9, 7, 6, 6, 6], [len(ids) for ids in actual.values()])
        self.assertEqual(56, len(catalog.entries))
        self.assertEqual(56, len({entry.icon_id for entry in catalog.entries}))
        self.assertEqual(
            frozenset(icon_id for ids in EXPECTED_BY_CATEGORY.values() for icon_id in ids),
            CATALOG_IDS,
        )

    def test_catalog_metadata_and_records_match_the_public_contract(self):
        raw = json.loads(
            (ROOT / "assets" / "diagram-core" / "catalog.json").read_text(encoding="utf-8")
        )
        schema = json.loads(
            (ROOT / "schemas" / "diagram-core-catalog-v1.schema.json").read_text(encoding="utf-8")
        )

        self.assertEqual(
            {
                "system": "diagram-core-v1",
                "public_name": "AniDiagram Diagram Core Icon System v1.0",
                "catalog_revision": 1,
                "icons": raw["icons"],
            },
            raw,
        )
        self.assertTrue(all(set(record) == REQUIRED_ICON_FIELDS for record in raw["icons"]))
        self.assertEqual(sorted(REQUIRED_ICON_FIELDS), sorted(schema["$defs"]["icon"]["required"]))
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["$defs"]["icon"]["additionalProperties"])

    def test_catalog_starts_only_benchmarks_in_visual_review(self):
        catalog = load_catalog()
        status = {entry.icon_id: entry.status for entry in catalog.entries}

        self.assertEqual(
            {"agent", "database", "api", "server"},
            {icon_id for icon_id, value in status.items() if value == "visual-review"},
        )
        self.assertEqual(52, sum(value == "planned" for value in status.values()))
        self.assertTrue(set(status.values()).issubset(CATALOG_STATUSES))

    def test_semantics_aliases_and_planned_capabilities_are_not_inferred(self):
        catalog = load_catalog()
        planned = [entry for entry in catalog.entries if entry.status == "planned"]
        aliases = [alias for entry in catalog.entries for alias in entry.aliases]

        self.assertTrue(all(entry.semantic_kind == entry.icon_id for entry in catalog.entries))
        self.assertEqual([], aliases)
        self.assertEqual(len(aliases), len(set(aliases)))
        self.assertFalse(set(aliases) & CATALOG_IDS)
        self.assertEqual(52, len(planned))
        self.assertTrue(all(entry.structural_prototype == "unassigned" for entry in planned))
        self.assertTrue(all(entry.parts == () for entry in planned))
        self.assertTrue(all(entry.supported_states == () for entry in planned))
        self.assertTrue(all(entry.supported_actions == () for entry in planned))
        self.assertTrue(all(entry.asset_revision == 0 for entry in planned))

    def test_benchmarks_freeze_exact_prototypes_parts_states_and_actions(self):
        catalog = load_catalog()

        for icon_id, expected in EXPECTED_BENCHMARKS.items():
            with self.subTest(icon_id=icon_id):
                entry = catalog_entry(icon_id, catalog)
                self.assertIsNotNone(entry)
                self.assertEqual(expected["prototype"], entry.structural_prototype)
                self.assertEqual(expected["parts"], entry.parts)
                self.assertEqual(EXPECTED_STATES, entry.supported_states)
                self.assertEqual(expected["actions"], entry.supported_actions)
                self.assertEqual("visual-review", entry.status)
                self.assertEqual(1, entry.asset_revision)

    def test_all_legacy_ids_are_members_but_validity_follows_approval(self):
        catalog = load_catalog()
        promoted = catalog_fixture_with_status(catalog, "server", "approved")

        self.assertEqual(13, len(LEGACY_VALID_ICON_IDS))
        self.assertTrue(LEGACY_VALID_ICON_IDS.issubset(CATALOG_IDS))
        self.assertEqual(LEGACY_VALID_ICON_IDS, legacy_valid_icon_ids(promoted))
        self.assertEqual(frozenset({"server"}), approved_icon_ids(promoted))
        self.assertEqual(
            LEGACY_VALID_ICON_IDS | {"server"},
            diagram_script_valid_icon_ids(promoted),
        )

    def test_current_known_icons_are_exactly_the_legacy_compatibility_set(self):
        self.assertEqual(set(LEGACY_VALID_ICON_IDS), KNOWN_ICONS)
        self.assertEqual(frozenset(), approved_icon_ids())
        self.assertNotIn("server", KNOWN_ICONS)

    def test_planned_catalog_icons_are_not_implemented(self):
        for icon_id in ("user", "llm", "pdf", "scheduler"):
            with self.subTest(icon_id=icon_id):
                self.assertEqual("planned", catalog_entry(icon_id).status)
                result = validate_scene(scene_spec_with_icon(icon_id))
                issue = result["error"]["issues"][0]
                self.assertEqual("$.nodes[0].icon", issue["path"])
                self.assertEqual("icon_not_implemented", issue["code"])

    def test_visual_review_server_is_not_yet_valid(self):
        self.assertEqual("visual-review", catalog_entry("server").status)
        result = validate_scene(scene_spec_with_icon("server"))
        issue = result["error"]["issues"][0]

        self.assertEqual("$.nodes[0].icon", issue["path"])
        self.assertEqual("icon_not_implemented", issue["code"])
        self.assertNotIn("server", KNOWN_ICONS)

    def test_unknown_icon_remains_an_enum_error(self):
        result = validate_scene(scene_spec_with_icon("not-a-real-icon"))
        issue = result["error"]["issues"][0]

        self.assertEqual("$.nodes[0].icon", issue["path"])
        self.assertEqual("enum", issue["code"])

    def test_all_legacy_ids_remain_valid_during_review(self):
        for icon_id in sorted(LEGACY_VALID_ICON_IDS):
            with self.subTest(icon_id=icon_id):
                scene = compile_scene(scene_spec_with_icon(icon_id))
                self.assertEqual(icon_id, scene.nodes[0].icon)

    def test_schema_sync_check_reports_clean_without_writing(self):
        schema_path = ROOT / "schemas" / "diagram-script-v0.3.schema.json"
        before = schema_path.read_bytes()
        completed = run_schema_sync(SYNC_SCRIPT, "--check")

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("icons=13 status=clean\n", completed.stdout)
        self.assertEqual("", completed.stderr)
        self.assertEqual(before, schema_path.read_bytes())

    def test_schema_sync_check_exits_nonzero_without_rewriting_drift(self):
        current = json.loads(
            (ROOT / "schemas" / "diagram-script-v0.3.schema.json").read_text(encoding="utf-8")
        )["$defs"]["icon"]["enum"]
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path, schema_path = copy_sync_fixture(temp_dir, current + ["server"])
            before = schema_path.read_bytes()
            completed = run_schema_sync(script_path, "--check")

            self.assertEqual(1, completed.returncode)
            self.assertEqual("icons=13 status=drift\n", completed.stdout)
            self.assertEqual("", completed.stderr)
            self.assertEqual(before, schema_path.read_bytes())

    def test_schema_sync_write_is_deterministic_and_idempotent(self):
        current = json.loads(
            (ROOT / "schemas" / "diagram-script-v0.3.schema.json").read_text(encoding="utf-8")
        )["$defs"]["icon"]["enum"]
        drifted = [icon_id for icon_id in current if icon_id != "token"] + ["server"]
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path, schema_path = copy_sync_fixture(temp_dir, drifted)

            first = run_schema_sync(script_path, "--write")
            first_bytes = schema_path.read_bytes()
            second = run_schema_sync(script_path, "--write")
            checked = run_schema_sync(script_path, "--check")
            written = json.loads(first_bytes.decode("utf-8"))["$defs"]["icon"]["enum"]

            self.assertEqual(0, first.returncode, first.stderr)
            self.assertEqual("icons=13 status=written\n", first.stdout)
            self.assertEqual("", first.stderr)
            self.assertEqual(sorted(KNOWN_ICONS), written)
            self.assertNotIn("server", written)
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertEqual("icons=13 status=clean\n", second.stdout)
            self.assertEqual(first_bytes, schema_path.read_bytes())
            self.assertEqual(0, checked.returncode, checked.stderr)
            self.assertEqual("icons=13 status=clean\n", checked.stdout)

    def test_schema_sync_actions_are_required_and_mutually_exclusive(self):
        missing = run_schema_sync(SYNC_SCRIPT)
        conflicting = run_schema_sync(SYNC_SCRIPT, "--check", "--write")

        self.assertEqual(2, missing.returncode)
        self.assertIn("--check", missing.stderr)
        self.assertIn("--write", missing.stderr)
        self.assertEqual("", missing.stdout)
        self.assertEqual(2, conflicting.returncode)
        self.assertIn("not allowed with argument", conflicting.stderr)
        self.assertEqual("", conflicting.stdout)

    def test_public_models_and_id_sets_are_immutable(self):
        catalog = load_catalog()
        entry = catalog.entries[0]

        self.assertIsInstance(catalog.entries, tuple)
        self.assertIsInstance(entry.aliases, tuple)
        self.assertIsInstance(CATALOG_IDS, frozenset)
        self.assertIsInstance(CATALOG_STATUSES, frozenset)
        self.assertIsInstance(approved_icon_ids(catalog), frozenset)
        with self.assertRaises(FrozenInstanceError):
            entry.status = "approved"
        with self.assertRaises(FrozenInstanceError):
            catalog.catalog_revision = 2

    def test_loader_uses_injected_asset_root_and_reports_precise_invalid_paths(self):
        source = json.loads(
            (ROOT / "assets" / "diagram-core" / "catalog.json").read_text(encoding="utf-8")
        )
        cases = (
            (
                "invalid status",
                lambda raw: raw["icons"][0].__setitem__("status", "draft"),
                r"\$\.icons\[0\]\.status",
            ),
            (
                "missing field",
                lambda raw: raw["icons"][0].pop("semantic_kind"),
                r"\$\.icons\[0\]\.semantic_kind",
            ),
            (
                "alias collides with id",
                lambda raw: raw["icons"][0].__setitem__("aliases", ["agent"]),
                r"\$\.icons\[0\]\.aliases\[0\]",
            ),
        )

        for label, mutate, error_path in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                raw = json.loads(json.dumps(source))
                mutate(raw)
                path = Path(temp_dir) / "catalog.json"
                path.write_text(json.dumps(raw), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, error_path):
                    load_catalog(asset_root=Path(temp_dir))


if __name__ == "__main__":
    unittest.main()

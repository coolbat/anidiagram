import hashlib
import json
import unittest
from pathlib import Path

from anidiagram.illustrated_registry import illustrated_icon_ids
from scripts.build_illustrated_expansion_batch_4_case import build_case
from scripts.render_illustrated_expansion_batch_4_case import (
    build_case_manifest,
    render_case_html,
    render_case_svg,
)


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "examples" / "cloud-native-knowledge-retrieval-illustrated-2.4-candidate.plan.json"
CANDIDATE_ICONS = {"vector-database", "knowledge-base", "gateway", "container"}


class IllustratedExpansionBatch4CaseTest(unittest.TestCase):
    def test_real_case_approval_is_archived_after_explicit_public_promotion(self):
        acceptance = json.loads(
            (ROOT / "assets" / "illustrated" / "reviews" / "2.4.0-motion-acceptance.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("real-case-confirmed-public-registration-pending", acceptance["status"])
        self.assertEqual("confirmed", acceptance["motion_acceptance"]["status"])
        self.assertEqual(CANDIDATE_ICONS, set(acceptance["motion_acceptance"]["approved_icons"]))
        self.assertEqual("confirmed", acceptance["real_case_acceptance"]["status"])
        self.assertEqual("2026-07-22", acceptance["real_case_acceptance"]["accepted_at"])
        review_record = acceptance["real_case_acceptance"]["record"]
        review_path = ROOT / review_record["path"]
        self.assertEqual(review_record["sha256"], hashlib.sha256(review_path.read_bytes()).hexdigest())
        self.assertFalse(acceptance["public_showcase"]["public_registry_changed"])
        self.assertEqual(56, len(illustrated_icon_ids()))
        self.assertTrue(CANDIDATE_ICONS.issubset(illustrated_icon_ids()))

    def test_plan_keeps_semantics_separate_from_candidate_presentation(self):
        plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        semantic = plan["semantic"]
        self.assertEqual("0.2", plan["version"])
        self.assertEqual("architecture", semantic["intent"]["diagram_kind"])
        self.assertEqual(9, len(semantic["entities"]))
        self.assertEqual(7, len(semantic["relations"]))
        self.assertEqual(2, len(semantic["groups"]))
        self.assertEqual(2, len(semantic["flows"]))
        self.assertEqual("illustrated", plan["presentation"]["icon_system"])
        self.assertEqual("2.4.0-candidate", plan["presentation"]["icon_system_version"])
        self.assertEqual("deep-tech", plan["presentation"]["style"])
        self.assertEqual("swimlane", plan["presentation"]["layout"])
        self.assertEqual("showcase-v1", plan["presentation"]["motion"])
        self.assertNotIn("position", json.dumps(semantic))
        self.assertNotIn("duration", json.dumps(semantic))

    def test_review_spec_uses_seven_candidate_instances_and_all_edges_move(self):
        plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        spec = build_case(plan)
        icon_nodes = [node for node in spec["nodes"] if node.get("icon")]
        self.assertTrue(spec["candidate_review_only"])
        self.assertEqual("2.4.0-candidate", spec["resolved_presentation"]["icon_system"]["version"])
        self.assertEqual("illustrated-performance-v5-review", spec["candidate_motion_contract"])
        self.assertEqual(9, len(spec["nodes"]))
        self.assertEqual(7, len(icon_nodes))
        self.assertEqual(CANDIDATE_ICONS, {node["icon"] for node in icon_nodes})
        self.assertEqual(
            {"knowledge-base": 2, "container": 2, "vector-database": 2, "gateway": 1},
            {icon: sum(node["icon"] == icon for node in icon_nodes) for icon in CANDIDATE_ICONS},
        )
        self.assertEqual(7, len(spec["edges"]))
        self.assertTrue(all(edge["motion"]["enabled"] for edge in spec["edges"]))

    def test_case_page_emits_all_icon_and_edge_runtime_entries(self):
        spec = build_case(json.loads(PLAN_PATH.read_text(encoding="utf-8")))
        manifest = build_case_manifest(spec)
        svg = render_case_svg(spec)
        html = render_case_html(svg, manifest)
        self.assertEqual(7, len(manifest["icons"]))
        self.assertEqual(7, len(manifest["edges"]))
        self.assertEqual(list(range(7)), manifest["stage"]["active_edge_indices"])
        self.assertEqual([0, 2], manifest["stage"]["readable_edge_indices"])
        self.assertEqual("motion-manifest-0.2", manifest["version"])
        self.assertEqual("edge-motion-v1", manifest["edge_motion_contract"])
        self.assertEqual("1.0.0", manifest["edge_motion_version"])
        self.assertTrue(all(edge["effect"] == "packet-flow" for edge in manifest["edges"]))
        self.assertTrue(all(edge["motion_kind"] == "packet" for edge in manifest["edges"]))
        self.assertEqual(2, len({manifest["edges"][index]["flow_id"] for index in manifest["stage"]["readable_edge_indices"]}))
        self.assertEqual(7, html.count('class="semantic-icon semantic-icon-illustrated"'))
        self.assertEqual(7, html.count('class="edge"'))
        self.assertEqual(7, html.count('data-motion-enabled="true"'))
        selectors = [selector for entry in manifest["icons"] for selector in entry["parts"].values()]
        self.assertEqual(len(selectors), len(set(selectors)))
        self.assertTrue(all(html.count(f'id="{selector[1:]}"') == 1 for selector in selectors))

    def test_public_23_release_record_remains_byte_exact(self):
        path = ROOT / "assets" / "illustrated" / "releases" / "2.3.0.json"
        self.assertEqual(
            "54851a06e6cf446c058d47b5aac563d399134bfc9e25cb409ba51f82e2cc8aed",
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )

    def test_real_case_review_record_confirms_visual_approval_without_public_promotion(self):
        review = json.loads(
            (ROOT / "assets" / "illustrated" / "reviews" / "2.4.0-real-case-review.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("confirmed-public-registration-pending", review["status"])
        self.assertEqual("2026-07-22", review["accepted_at"])
        self.assertEqual("confirmed", review["human_visual_acceptance"]["status"])
        self.assertEqual(7, review["human_visual_acceptance"]["accepted_icon_instances"])
        self.assertEqual(7, review["human_visual_acceptance"]["accepted_animated_edges"])
        self.assertEqual("passed", review["automated_acceptance"]["status"])
        self.assertEqual(7, review["case"]["icon_instances"])
        self.assertEqual(7, review["case"]["animated_edges"])
        self.assertEqual("showcase-v1", review["case"]["motion"])
        self.assertEqual("edge-motion-v1", review["case"]["edge_motion_contract"])
        self.assertEqual("1.0.0", review["case"]["edge_motion_version"])
        self.assertEqual("packet-flow", review["case"]["edge_effect"])
        self.assertEqual("one-edge-per-semantic-flow", review["case"]["readable_selection"])
        self.assertFalse(review["public_showcase"]["public_registry_changed"])
        self.assertFalse(review["public_showcase"]["public_motion_contract_changed"])
        self.assertIn("public-registration approval", review["approval_boundary"])


if __name__ == "__main__":
    unittest.main()

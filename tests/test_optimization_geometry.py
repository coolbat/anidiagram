"""Regression cases for the geometry blind spots in the October review."""

import unittest

from anidiagram.quality import quality_report
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style


def node(node_id, x, y, width=100, height=70, **kwargs):
    return {"id": node_id, "label": node_id, "position": [x, y], "size": [width, height], **kwargs}


def report(nodes=(), edges=(), groups=(), style=None):
    return quality_report(compile_scene({
        "version": "0.4", "canvas": {"width": 1800, "height": 1100},
        "nodes": list(nodes) or [node("standalone", 1300, 950)],
        "edges": list(edges), "groups": list(groups),
    }), style)


def codes(result):
    return {item["code"] for item in result["issues"]}


class OptimizationGeometryTest(unittest.TestCase):
    def test_legacy_scene_without_style_uses_renderer_default_text_region(self):
        scene = compile_scene({
            "version": "0.1", "nodes": [
                node("legacy", 100, 100, 150, 80, label="A B C D E F G H I J", icon="agent", step=1),
            ],
        })
        self.assertIsNone(scene.icon_system)
        self.assertEqual(quality_report(scene, load_style()), quality_report(scene))
        self.assertIn("text_overflow", codes(quality_report(scene)))

    def test_c5_original_layered_geometry_reports_overlap_and_crossing(self):
        # Frozen positions from ae244fb's default compilation of the enterprise
        # RAG Plan. Do not regenerate this fixture with the repaired layout.
        positions = [
            ("knowledge-owner", 70, 431), ("source-files", 350, 431),
            ("document-library", 630, 506), ("cloud-intake", 910, 506),
            ("ingestion-toolchain", 1190, 506), ("vector-database", 1470, 206),
            ("rag-api", 70, 581), ("policy-guard", 350, 581),
            ("rag-agent", 1470, 356), ("retriever", 1470, 506),
            ("conversation-memory", 1470, 806), ("grounded-answer", 1470, 656),
        ]
        result = report(
            [node(name, x, y, 220, 108) for name, x, y in positions],
            [{"from": "policy-guard", "to": "rag-agent", "route": "straight"},
             {"from": "rag-agent", "to": "conversation-memory", "route": "straight"}],
            [{"id": "ingestion", "bounds": [44, 164, 1672, 476]},
             {"id": "runtime", "bounds": [44, 314, 1672, 626]}],
        )
        self.assertIn("group_overlap", codes(result))
        self.assertIn("edge_segment_node_collision", codes(result))
        self.assertFalse(result["ok"])
        self.assertGreater(result["summary"]["warnings"], 0)

    def test_explicit_parent_containment_is_not_an_overlap(self):
        result = report(groups=[
            {"id": "system", "bounds": [40, 100, 600, 400]},
            {"id": "child", "parent": "system", "bounds": [70, 160, 200, 150]},
        ])
        self.assertNotIn("group_overlap", codes(result))
        self.assertFalse(result["advisories"])

    def test_unowned_containment_is_ambiguous_not_an_error(self):
        result = report(groups=[
            {"id": "system", "bounds": [40, 100, 600, 400]},
            {"id": "child", "bounds": [70, 160, 200, 150]},
        ])
        self.assertTrue(result["ok"])
        self.assertIn("group_containment_unverified", {i["code"] for i in result["advisories"]})

    def test_child_protruding_from_declared_parent_is_an_error(self):
        result = report(groups=[
            {"id": "system", "bounds": [40, 100, 300, 300]},
            {"id": "child", "parent": "system", "bounds": [250, 160, 200, 150]},
        ])
        self.assertIn("group_out_of_parent_bounds", codes(result))

    def test_shared_membership_overlap_is_ambiguous(self):
        result = report([node("shared", 280, 200)], groups=[
            {"id": "a", "bounds": [100, 100, 400, 400], "members": ["shared"]},
            {"id": "b", "bounds": [250, 100, 400, 400], "members": ["shared"]},
        ])
        self.assertTrue(result["ok"])
        self.assertIn("group_shared_membership_overlap", {i["code"] for i in result["advisories"]})

    def test_membership_checks_explicit_owner_not_nearest_group(self):
        groups = [{"id": "lane", "bounds": [100, 150, 300, 240], "members": ["outside"]}]
        result = report([node("outside", 350, 250)], groups=groups)
        self.assertIn("node_out_of_group", codes(result))
        groups[0].pop("members")
        self.assertNotIn("node_out_of_group", codes(report([node("outside", 350, 250)], groups=groups)))

    def test_member_covering_swimlane_title_is_reported(self):
        result = report([node("member", 112, 162)], groups=[
            {"id": "lane", "label": "Operations", "bounds": [100, 150, 300, 240], "members": ["member"]},
        ])
        self.assertIn("node_group_title_collision", codes(result))

    def test_generated_straight_route_crossing_counts_as_warning(self):
        result = report([node("a", 50, 200), node("blocker", 300, 200), node("b", 550, 200)],
                        [{"from": "a", "to": "b", "route": "straight"}])
        self.assertIn("edge_segment_node_collision", codes(result))
        issue = next(i for i in result["issues"] if i["code"] == "edge_segment_node_collision")
        self.assertEqual("warning", issue["severity"])
        self.assertEqual("blocker", issue["subject"]["blocking_node"])
        self.assertTrue(result["ok"])

    def test_authored_route_crossing_is_promoted_without_blocking_delivery(self):
        result = report([node("a", 50, 200), node("blocker", 300, 200), node("b", 550, 200)],
                        [{"from": "a", "to": "b", "route": "points", "points": [[150, 235], [550, 235]]}])
        self.assertIn("edge_segment_node_collision", codes(result))
        self.assertTrue(result["ok"])

    def test_endpoint_nodes_and_tangent_routes_do_not_collide(self):
        result = report([node("a", 50, 200), node("blocker", 300, 235), node("b", 550, 200)],
                        [{"from": "a", "to": "b", "route": "straight"}])
        self.assertNotIn("edge_segment_node_collision", codes(result))

    def test_decision_empty_corner_is_not_a_node_collision(self):
        result = report([node("a", 50, 200), node("diamond", 300, 230, shape="decision"), node("b", 550, 200)],
                        [{"from": "a", "to": "b", "route": "points", "points": [[150, 235], [320, 235], [320, 190], [550, 190], [550, 235]]}])
        self.assertNotIn("edge_segment_node_collision", codes(result))
        self.assertNotIn("edge_node_collision", codes(result))

    def test_orthogonal_route_uses_bends_not_endpoint_chord(self):
        result = report([node("a", 50, 200), node("blocker", 340, 330), node("b", 650, 500)],
                        [{"from": "a", "to": "b", "route": "hv"}])
        self.assertNotIn("edge_segment_node_collision", codes(result))

    def test_curved_route_detects_actual_curve_and_excludes_empty_chord(self):
        endpoints = [node("a", 50, 100), node("b", 650, 500)]
        edges = [{"from": "a", "to": "b", "route": "curved"}]
        curved = report(endpoints + [node("blocker", 277, 195, 16, 16)], edges)
        self.assertIn("edge_segment_node_collision", codes(curved))
        chord = report(endpoints + [node("blocker", 277, 235, 16, 16)], edges)
        self.assertNotIn("edge_segment_node_collision", codes(chord))

    def test_edge_crossing_group_title_is_visible_in_summary(self):
        result = report([node("a", 50, 150), node("b", 550, 150)],
                        [{"from": "a", "to": "b", "route": "straight"}],
                        [{"id": "g", "label": "Heading", "bounds": [300, 160, 200, 240]}])
        self.assertIn("edge_group_title_collision", codes(result))

    def test_another_edge_crossing_visible_label_is_reported(self):
        result = report(
            [node("a", 50, 200), node("b", 650, 200), node("c", 380, 80), node("d", 380, 400)],
            [{"from": "a", "to": "b", "route": "straight", "label": "payload"},
             {"from": "c", "to": "d", "route": "straight"}],
        )
        self.assertIn("edge_label_collision", codes(result))

    def test_hidden_label_does_not_create_a_phantom_collision(self):
        result = report(
            [node("a", 50, 200), node("b", 200, 200), node("c", 130, 80), node("d", 130, 400)],
            [{"from": "a", "to": "b", "route": "straight", "label": "hidden long payload"},
             {"from": "c", "to": "d", "route": "straight"}],
        )
        self.assertNotIn("edge_label_collision", codes(result))

    def test_diagonal_is_advisory_not_invalid_geometry(self):
        result = report([node("a", 50, 150), node("b", 650, 550)],
                        [{"from": "a", "to": "b", "route": "straight"}])
        self.assertTrue(result["ok"])
        self.assertIn("long_diagonal_edge", {i["code"] for i in result["advisories"]})

    def test_node_badge_checks_rendered_text_not_entire_text_region(self):
        crowded = report([node("long", 100, 200, 100, 45, label="Long title words", step=1)])
        self.assertIn("badge_label_collision", codes(crowded))
        roomy = report([node("short", 100, 200, 300, 100, label="OK", step=1)])
        self.assertNotIn("badge_label_collision", codes(roomy))

    def test_edge_badge_and_own_left_anchored_label_are_separated(self):
        result = report([node("a", 50, 200), node("b", 650, 200)],
                        [{"from": "a", "to": "b", "route": "straight", "label": "payload", "step": 1}],
                        style=load_style())
        self.assertNotIn("badge_label_collision", codes(result))


if __name__ == "__main__":
    unittest.main()

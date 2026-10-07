import unittest

from anidiagram.quality import quality_report
from anidiagram.schema import compile_scene


class QualityDiagnosticsTest(unittest.TestCase):
    def test_overlap_issue_exposes_actionable_subject_evidence_and_fixes(self):
        scene = compile_scene(
            {
                "version": "0.4",
                "canvas": {"width": 640, "height": 360},
                "nodes": [
                    {"id": "source", "label": "Source", "position": [100, 150], "size": [160, 80]},
                    {"id": "target", "label": "Target", "position": [220, 170], "size": [160, 80]},
                ],
            }
        )

        issue = quality_report(scene)["issues"][0]

        self.assertEqual("node_overlap", issue["code"])
        self.assertEqual({"node_ids": ["source", "target"]}, issue["subject"])
        self.assertEqual([100, 150, 260, 230], issue["evidence"]["source_rect"])
        self.assertEqual([220, 170, 380, 250], issue["evidence"]["target_rect"])
        self.assertEqual([40, 60], issue["evidence"]["overlap"])
        self.assertEqual(
            ["move_node", "adjust_layout_spacing", "resize_node"],
            issue["supported_fixes"],
        )

    def test_explicit_route_detects_a_segment_crossing_an_unrelated_node(self):
        scene = compile_scene(
            {
                "version": "0.4",
                "canvas": {"width": 760, "height": 420},
                "nodes": [
                    {"id": "source", "label": "Source", "position": [60, 170], "size": [140, 76]},
                    {"id": "obstacle", "label": "Obstacle", "position": [310, 155], "size": [140, 106]},
                    {"id": "target", "label": "Target", "position": [560, 170], "size": [140, 76]},
                ],
                "edges": [
                    {
                        "from": "source",
                        "to": "target",
                        "route": "points",
                        "points": [[200, 208], [560, 208]],
                    }
                ],
            }
        )

        report = quality_report(scene)
        issues = [
            issue for issue in report["issues"] if issue["code"] == "edge_segment_node_collision"
        ]

        self.assertEqual(1, len(issues))
        self.assertEqual({"errors": 0, "warnings": 1, "issues": 1}, report["summary"])
        self.assertTrue(report["ok"])  # Authored routes remain deliverable with diagnostics.
        self.assertEqual(
            {"edge_index": 0, "source": "source", "target": "target", "blocking_node": "obstacle"},
            issues[0]["subject"],
        )
        self.assertEqual(0, issues[0]["evidence"]["segment_index"])
        self.assertEqual([[212, 208], [548, 208]], issues[0]["evidence"]["segment"])
        self.assertEqual(
            ["reroute_edge_points", "move_blocking_node", "change_layout"],
            issues[0]["supported_fixes"],
        )

    def test_warns_when_a_meaningful_straight_edge_label_will_be_hidden(self):
        scene = compile_scene(
            {
                "version": "0.4",
                "canvas": {"width": 640, "height": 360},
                "nodes": [
                    {"id": "source", "label": "Source", "position": [80, 150], "size": [140, 76]},
                    {"id": "target", "label": "Target", "position": [250, 150], "size": [140, 76]},
                ],
                "edges": [
                    {"from": "source", "to": "target", "route": "straight", "label": "validated payload"}
                ],
            }
        )

        report = quality_report(scene)
        issues = [issue for issue in report["advisories"] if issue["code"] == "edge_label_hidden"]

        self.assertEqual(1, len(issues))
        self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, report["summary"])
        self.assertEqual(
            {"edge_index": 0, "source": "source", "target": "target"},
            issues[0]["subject"],
        )
        self.assertEqual("validated payload", issues[0]["evidence"]["label"])
        self.assertLess(issues[0]["evidence"]["available_width"], issues[0]["evidence"]["required_width"])
        self.assertEqual(
            ["increase_node_spacing", "shorten_edge_label", "change_edge_route"],
            issues[0]["supported_fixes"],
        )


if __name__ == "__main__":
    unittest.main()

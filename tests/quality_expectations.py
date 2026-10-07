"""Explicit diagnostic debt for authored examples after the October A2 audit.

These snapshots preserve each known issue's identity; they are not evidence of
visual acceptance. Any extra or missing issue fails, as does changed severity.
New geometry behavior is tested independently in test_optimization_geometry.
"""

import json
from pathlib import Path


BASELINE = Path(__file__).parent / "fixtures" / "quality-diagnostics-2026-10.json"


def diagnostic_fingerprints(report):
    return sorted(
        ({"code": issue["code"], "severity": issue["severity"], "subject": issue["subject"]}
         for issue in report["issues"]),
        key=lambda item: json.dumps(item, sort_keys=True),
    )


def baseline_key(test, case=""):
    return f"{type(test).__name__}.{test._testMethodName}" + (f"/{case}" if case else "")


def assert_quality_baseline(test, report, case=""):
    expected = json.loads(BASELINE.read_text(encoding="utf-8"))[baseline_key(test, case)]
    test.assertEqual(expected, diagnostic_fingerprints(report), case)
    errors = sum(item["severity"] == "error" for item in expected)
    warnings = sum(item["severity"] == "warning" for item in expected)
    test.assertEqual({"errors": errors, "warnings": warnings, "issues": len(expected)}, report["summary"], case)
    test.assertEqual(errors == 0, report["ok"], case)

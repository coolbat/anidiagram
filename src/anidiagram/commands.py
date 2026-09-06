"""Additional read/review commands, isolated from the existing render CLI."""

import argparse
import json
import sys

from .delivery import DeliveryError


def main(argv):
    parser = argparse.ArgumentParser(prog="anidiagram")
    commands = parser.add_subparsers(dest="command", required=True)
    compare = commands.add_parser("compare", help="Compare two DiagramPlan 0.2 documents.")
    compare.add_argument("base")
    compare.add_argument("head")
    compare.add_argument("--out", required=True, help="Output HTML; receipt is committed beside it.")
    compare.add_argument("--receipt")
    compare.add_argument("--repo-root")
    compare.add_argument("--json", action="store_true", help="Print a machine-readable result (the default).")
    visual = commands.add_parser("visual-check", help="Capture fixed viewports of a frozen standalone HTML artifact.")
    visual.add_argument("artifact")
    visual.add_argument("--outdir")
    visual.add_argument("--viewports", default="1440x900,1600x1000,1920x1080,2048x1320")
    visual.add_argument("--json", action="store_true")
    visual.add_argument("--strict-labels", action="store_true", help="Also require complete, non-overlapping labels, relation fields and correct arrow geometry.")
    accuracy = commands.add_parser("accuracy-check", help="Check pinned facts without conflating references with semantic proof.")
    accuracy.add_argument("input", help="Plan 0.2 or DiagramScript input.")
    accuracy.add_argument("--facts", required=True)
    accuracy.add_argument("--review", help="Independent review record bound to input/facts hashes.")
    accuracy.add_argument("--repo-root")
    accuracy.add_argument("--out", help="Optional transactional JSON report; never replaces inputs.")
    accuracy.add_argument("--strict", action="store_true", help="Fail on unresolved required claims as well as contradictions.")
    accuracy.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "compare":
            from .compare import deliver_comparison
            result = deliver_comparison(args.base, args.head, args.out, receipt=args.receipt, repo_root=args.repo_root)
        elif args.command == "accuracy-check":
            from .accuracy import accuracy_command
            result = accuracy_command(args.input, args.facts, repo_root=args.repo_root,
                                      review_path=args.review, output=args.out, strict=args.strict)
        else:
            from .visual_check import visual_check
            result = visual_check(args.artifact, outdir=args.outdir, viewports=args.viewports, strict_labels=args.strict_labels)
    except DeliveryError as error:
        print(json.dumps(error.to_result(), ensure_ascii=False), file=sys.stderr)
        raise SystemExit(3) from error
    except (ValueError, OSError) as error:
        print(json.dumps({"ok": False, "error": {"code": args.command + "_failed", "message": str(error)}}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2) from error
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(2 if result.get("status") == "skipped" else 1)

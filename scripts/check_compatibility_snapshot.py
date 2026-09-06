"""Record or compare legacy compiler/render output without rewriting examples."""

import argparse
import hashlib
import json
from pathlib import Path

from anidiagram.planner import compile_plan
from anidiagram.presets import compile_preset, preset_names
from anidiagram.quality import quality_report
from anidiagram.renderer_html_runtime import render_html_runtime
from anidiagram.renderer_svg import render_svg
from anidiagram.schema import DiagramScriptValidationError, compile_scene
from anidiagram.styles import load_style

ROOT = Path(__file__).resolve().parents[1]


def snapshot():
    cases = {"preset/" + name: compile_preset(name) for name in preset_names()}
    for directory in (ROOT / "tests/fixtures", ROOT / "examples/contracts"):
        for path in sorted(directory.glob("*.json")):
            data = json.loads(path.read_text())
            if "semantic" in data or "layout_strategy" in data:
                cases[str(path.relative_to(ROOT))] = compile_plan(data)
            elif "nodes" in data and "version" in data:
                cases[str(path.relative_to(ROOT))] = data
    # Explicitly include the approved Illustrated surface and the Chinese path.
    for relative in ("examples/illustrated-2.5-showcase.diagram.json",
                     "examples/zh-CN/enterprise-agent-platform.plan.json"):
        path = ROOT / relative
        data = json.loads(path.read_text())
        cases[relative] = compile_plan(data) if "semantic" in data else data
    result = {}
    for name, spec in cases.items():
        try:
            scene = compile_scene(spec)
        except DiagramScriptValidationError as error:
            result[name] = {"validation_error": error.to_result()}
            continue
        style = load_style(ROOT / "styles" / f"{scene.style.name or 'minimal-light'}.json")
        outputs = {"spec": spec, "quality": quality_report(scene, style),
                   "svg": render_svg(scene, style), "html": render_html_runtime(scene, style)}
        result[name] = {
            key: hashlib.sha256((value if isinstance(value, str) else
                                json.dumps(value, sort_keys=True)).encode()).hexdigest()
            for key, value in outputs.items()
        }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    current = snapshot()
    if args.record:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(current, indent=2) + "\n")
        print(f"Recorded {len(current)} cases, four output hashes each.")
    else:
        before = json.loads(args.receipt.read_text())
        changed = [key for key in sorted(set(before) | set(current)) if before.get(key) != current.get(key)]
        print(json.dumps({"ok": not changed, "cases": len(current), "changed": changed}, indent=2))
        raise SystemExit(bool(changed))

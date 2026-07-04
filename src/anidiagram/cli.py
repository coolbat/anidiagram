"""Command-line interface for the clean-room renderer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Union

from .renderer_svg import render_html, render_svg
from .schema import DiagramScriptValidationError, compile_scene
from .styles import load_style


def read_json(path: Union[str, Path]) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Render DiagramScript JSON to animated SVG.")
    parser.add_argument("--spec", required=True, help="Path to DiagramScript JSON.")
    parser.add_argument("--style", help="Optional style profile JSON.")
    parser.add_argument("--outdir", required=True, help="Output directory.")
    parser.add_argument("--basename", default="diagram", help="Output basename.")
    parser.add_argument("--html", action="store_true", help="Also write a self-contained HTML viewer.")
    args = parser.parse_args(argv)

    spec_path = Path(args.spec)
    spec = read_json(spec_path)
    try:
        scene = compile_scene(spec)
    except DiagramScriptValidationError as exc:
        print(
            json.dumps({"ok": False, "error": exc.to_result()}, ensure_ascii=False, indent=2),
            file=sys.stderr,
        )
        raise SystemExit(2)

    style_path = args.style
    if not style_path and scene.style.name:
        candidate = spec_path.resolve().parents[1] / "styles" / f"{scene.style.name}.json"
        if candidate.is_file():
            style_path = candidate
    style = load_style(style_path)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    svg = render_svg(scene, style)
    svg_path = outdir / f"{args.basename}.svg"
    svg_path.write_text(svg, encoding="utf-8")

    result = {
        "ok": True,
        "schema": {"name": "DiagramScript", "version": scene.version},
        "style": style.get("name", scene.style.name or "minimal-light"),
        "outputs": {
            "svg": {"format": "svg", "path": str(svg_path.resolve())},
        },
        "stats": scene.stats(),
    }
    if args.html:
        title = scene.title.text or args.basename
        html_path = outdir / f"{args.basename}.html"
        html_path.write_text(render_html(svg, title), encoding="utf-8")
        result["outputs"]["html"] = {"format": "html", "path": str(html_path.resolve())}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

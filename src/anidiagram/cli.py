"""Command-line interface for the clean-room renderer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .renderer_svg import render_html, render_svg
from .styles import load_style


def read_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render DiagramScript JSON to animated SVG.")
    parser.add_argument("--spec", required=True, help="Path to DiagramScript JSON.")
    parser.add_argument("--style", help="Optional style profile JSON.")
    parser.add_argument("--outdir", required=True, help="Output directory.")
    parser.add_argument("--basename", default="diagram", help="Output basename.")
    parser.add_argument("--html", action="store_true", help="Also write a self-contained HTML viewer.")
    args = parser.parse_args(argv)

    spec = read_json(args.spec)
    style_path = args.style
    if not style_path and spec.get("style"):
        candidate = Path(args.spec).resolve().parents[1] / "styles" / f"{spec['style']}.json"
        if candidate.is_file():
            style_path = candidate
    style = load_style(style_path)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    svg = render_svg(spec, style)
    svg_path = outdir / f"{args.basename}.svg"
    svg_path.write_text(svg, encoding="utf-8")

    result = {"svg": str(svg_path), "style": style.get("name", "minimal-light")}
    if args.html:
        title = str((spec.get("title") or {}).get("text", args.basename))
        html_path = outdir / f"{args.basename}.html"
        html_path.write_text(render_html(svg, title), encoding="utf-8")
        result["html"] = str(html_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Batch render AniDiagram examples and built-in presets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anidiagram.exporters import write_html, write_quality, write_svg
from anidiagram.presets import compile_preset, preset_names
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style


def main() -> None:
    parser = argparse.ArgumentParser(description="Render all AniDiagram preset gallery assets.")
    parser.add_argument("--outdir", default="gallery", help="Gallery output directory.")
    parser.add_argument("--quality", action="store_true", help="Also write quality reports.")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cards = []
    for name in preset_names():
        spec = compile_preset(name)
        scene = compile_scene(spec)
        style = load_style(ROOT / "styles" / f"{scene.style.name}.json")
        svg_path = outdir / f"{name}.svg"
        html_path = outdir / f"{name}.html"
        write_svg(scene, style, svg_path)
        write_html(scene, style, html_path)
        if args.quality:
            write_quality(scene, outdir / f"{name}.quality.json")
        cards.append((name, svg_path.name, html_path.name, scene.title.subtitle))
    write_index(outdir, cards)
    print(json.dumps({"ok": True, "outdir": str(outdir.resolve()), "count": len(cards)}, indent=2))


def write_index(outdir: Path, cards: list) -> None:
    body = "\n".join(
        f'<article><a href="{html}"><img src="{svg}" alt="{name} preset"></a><h2>{name}</h2><p>{subtitle}</p></article>'
        for name, svg, html, subtitle in cards
    )
    (outdir / "index.html").write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AniDiagram Gallery</title>
  <style>
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: #f8fafc; color: #111827; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    h1 {{ font-size: 32px; margin: 0 0 20px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; }}
    article {{ border: 1px solid #e5e7eb; border-radius: 8px; background: #ffffff; overflow: hidden; }}
    img {{ display: block; width: 100%; height: auto; }}
    h2 {{ font-size: 18px; margin: 12px 14px 4px; }}
    p {{ margin: 0 14px 14px; color: #4b5563; }}
  </style>
</head>
<body>
  <main>
    <h1>AniDiagram Gallery</h1>
    <section class="grid">
{body}
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

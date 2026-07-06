"""Command-line interface for AniDiagram."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .exporters import (
    write_apng,
    write_gif,
    write_html,
    write_lottie,
    write_mp4,
    write_pdf,
    write_png,
    write_quality,
    write_svg,
    write_webp,
)
from .planner import brief_to_plan, compile_plan
from .presets import compile_preset, preset_names
from .schema import DiagramScriptValidationError, compile_scene
from .styles import load_style


EXPORTERS = {
    "svg": write_svg,
    "html": write_html,
    "png": write_png,
    "gif": write_gif,
    "pdf": write_pdf,
    "webp": write_webp,
    "mp4": write_mp4,
    "apng": write_apng,
    "lottie": write_lottie,
    "quality": write_quality,
}
FORMAT_EXTENSIONS = {
    "svg": ".svg",
    "html": ".html",
    "png": ".png",
    "gif": ".gif",
    "pdf": ".pdf",
    "webp": ".webp",
    "mp4": ".mp4",
    "apng": ".apng",
    "lottie": ".lottie.json",
    "quality": ".quality.json",
}


def read_json(path: Union[str, Path]) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Render DiagramScript JSON or clean-room presets.")
    source = parser.add_mutually_exclusive_group(required=False)
    source.add_argument("--spec", help="Path to DiagramScript JSON.")
    source.add_argument("--preset", choices=preset_names(), help="Render a built-in preset.")
    source.add_argument("--brief", help="Path to a natural-language brief to compile into DiagramScript.")
    source.add_argument("--text", help="Inline natural-language brief to compile into DiagramScript.")
    parser.add_argument("--list-presets", action="store_true", help="Print available preset names and exit.")
    parser.add_argument("--title", help="Override title when rendering a preset.")
    parser.add_argument("--style", help="Optional style profile JSON or bundled style name.")
    parser.add_argument("--outdir", default="outputs", help="Output directory.")
    parser.add_argument("--basename", default="diagram", help="Output basename.")
    parser.add_argument("--formats", help="Comma-separated formats: svg,html,png,gif,pdf,webp,mp4,apng,lottie,quality.")
    parser.add_argument("--all", action="store_true", help="Write every supported output format.")
    parser.add_argument("--html", action="store_true", help="Also write a self-contained HTML viewer.")
    parser.add_argument("--quality", action="store_true", help="Also write a quality report JSON.")
    parser.add_argument("--result", help="Optional path for the structured CLI result JSON.")
    parser.add_argument("--plan-out", help="Optional path for a generated DiagramPlan JSON when using --brief or --text.")
    parser.add_argument("--spec-out", help="Optional path for a generated DiagramScript JSON when using --brief or --text.")
    args = parser.parse_args(argv)

    if args.list_presets:
        print(json.dumps({"presets": preset_names()}, ensure_ascii=False, indent=2))
        return
    if not args.spec and not args.preset and not args.brief and not args.text:
        parser.error("one of --spec, --preset, --brief, or --text is required")

    spec_path = Path(args.spec) if args.spec else None
    source_kind = "spec"
    generated_plan: Optional[Dict[str, Any]] = None
    if spec_path:
        spec = read_json(spec_path)
    elif args.preset:
        source_kind = "preset"
        spec = compile_preset(args.preset, title=args.title or "")
    else:
        source_kind = "brief"
        brief_text = Path(args.brief).read_text(encoding="utf-8") if args.brief else args.text
        generated_plan = brief_to_plan(
            brief_text or "",
            title=args.title or "",
            style=style_name_from_arg(args.style) or "sketch-board",
        )
        spec = compile_plan(generated_plan)
        if args.plan_out:
            write_json(args.plan_out, generated_plan)
        if args.spec_out:
            write_json(args.spec_out, spec)
    try:
        scene = compile_scene(spec)
    except DiagramScriptValidationError as exc:
        result = {"ok": False, "error": exc.to_result()}
        _emit_result(result, args.result, stderr=True)
        raise SystemExit(2)

    style = load_style(resolve_style_path(args.style, scene.style.name, spec_path))
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    formats = _requested_formats(args)
    outputs: Dict[str, Dict[str, Any]] = {}
    for format_name in formats:
        output_path = outdir / f"{args.basename}{FORMAT_EXTENSIONS[format_name]}"
        if format_name == "quality":
            outputs[format_name] = write_quality(scene, output_path)
        else:
            outputs[format_name] = EXPORTERS[format_name](scene, style, output_path)

    result = {
        "ok": True,
        "schema": {"name": "DiagramScript", "version": scene.version},
        "source": source_kind,
        "preset": scene.preset,
        "style": style.get("name", scene.style.name or "minimal-light"),
        "outputs": outputs,
        "stats": scene.stats(),
    }
    if generated_plan is not None:
        result["plan"] = {
            "schema": {"name": "DiagramPlan", "version": generated_plan["version"]},
            "layout_strategy": generated_plan["layout_strategy"],
        }
    _emit_result(result, args.result)


def resolve_style_path(style_arg: Optional[str], scene_style: Optional[str], spec_path: Optional[Path]) -> Optional[Path]:
    value = style_arg or scene_style
    if not value:
        return None
    direct = Path(value)
    if direct.is_file():
        return direct
    candidates = []
    if spec_path:
        candidates.append(spec_path.resolve().parents[1] / "styles" / f"{value}.json")
    candidates.extend(
        [
            Path.cwd() / "styles" / f"{value}.json",
            Path(__file__).resolve().parents[2] / "styles" / f"{value}.json",
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return direct


def style_name_from_arg(style_arg: Optional[str]) -> Optional[str]:
    if not style_arg:
        return None
    path = Path(style_arg)
    if path.suffix == ".json":
        return path.stem
    return style_arg


def write_json(path: Union[str, Path], data: Dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _requested_formats(args: argparse.Namespace) -> List[str]:
    if args.all:
        return list(EXPORTERS.keys())
    requested = ["svg"]
    if args.formats:
        requested = [item.strip() for item in args.formats.split(",") if item.strip()]
    if args.html and "html" not in requested:
        requested.append("html")
    if args.quality and "quality" not in requested:
        requested.append("quality")
    unknown = [item for item in requested if item not in EXPORTERS]
    if unknown:
        raise SystemExit(f"unsupported format(s): {', '.join(unknown)}")
    return _dedupe(requested)


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _emit_result(result: Dict[str, Any], result_path: Optional[str], stderr: bool = False) -> None:
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if result_path:
        Path(result_path).write_text(payload + "\n", encoding="utf-8")
    print(payload, file=sys.stderr if stderr else sys.stdout)


if __name__ == "__main__":
    main()

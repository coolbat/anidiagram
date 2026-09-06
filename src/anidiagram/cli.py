"""Command-line interface for AniDiagram."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .delivery import DeliveryError, canonical_json_bytes, deliver_artifacts, source_record
from .exporters import (
    BROWSER_CAPTURE_FORMATS,
    write_apng,
    write_browser_capture,
    write_gif,
    write_html,
    write_lottie,
    write_mp4,
    write_pdf,
    write_png,
    write_quality,
    write_svg,
    write_viewer,
    write_webp,
)
from .planner import brief_to_plan, compile_plan
from .presets import compile_preset, preset_names
from .quality import quality_report
from .schema import DiagramScriptValidationError, compile_scene
from .styles import deep_merge, load_style
from .resources import resource_root


EXPORTERS = {
    "svg": write_svg,
    "html": write_html,
    "viewer": write_viewer,
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
    "viewer": ".viewer.html",
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


def _compile_cli_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return compile_plan(plan)
    except ValueError as error:
        print(json.dumps({"ok": False, "error": {"code": "diagram_plan_validation_failed", "message": str(error)}}), file=sys.stderr)
        raise SystemExit(2) from error


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Render DiagramScript JSON or clean-room presets.")
    source = parser.add_mutually_exclusive_group(required=False)
    source.add_argument("--spec", help="Path to DiagramScript JSON.")
    source.add_argument("--plan", help="Path to DiagramPlan JSON to validate and compile.")
    source.add_argument("--preset", choices=preset_names(), help="Render a built-in preset.")
    source.add_argument("--brief", help="Path to a natural-language brief to compile into DiagramScript.")
    source.add_argument("--text", help="Inline natural-language brief to compile into DiagramScript.")
    parser.add_argument("--list-presets", action="store_true", help="Print available preset names and exit.")
    parser.add_argument("--title", help="Override title when rendering a preset.")
    parser.add_argument("--repo-root", help="Local Git top-level for verifying explicitly authored repository sources.")
    parser.add_argument("--style", help="Optional style profile JSON or bundled style name.")
    parser.add_argument("--outdir", default="outputs", help="Output directory.")
    parser.add_argument("--basename", default="diagram", help="Output basename.")
    parser.add_argument("--formats", help="Comma-separated formats: svg,html,viewer,png,gif,pdf,webp,mp4,apng,lottie,quality. html-runtime is accepted as a legacy alias for html.")
    parser.add_argument("--html-runtime", choices=["gsap"], help="High-fidelity runtime backend for html output.")
    parser.add_argument(
        "--runtime-dependency",
        choices=["cdn", "inline", "none"],
        default="cdn",
        help="How HTML loads GSAP: exact-version CDN, inline local source, or static fallback.",
    )
    parser.add_argument("--runtime-source", help="Local gsap.min.js path required by --runtime-dependency inline.")
    parser.add_argument(
        "--diagram-locale",
        choices=["auto", "en", "zh-CN"],
        default="auto",
        help="Diagram content language; auto detects Chinese text.",
    )
    parser.add_argument(
        "--viewer-locale",
        choices=["auto", "en", "zh-CN"],
        default="auto",
        help="HTML viewer language; auto detects Chinese titles.",
    )
    parser.add_argument(
        "--runtime-mode",
        choices=["ambient", "timeline", "hybrid"],
        default="ambient",
        help="Explicit runtime scheduler mode.",
    )
    parser.add_argument(
        "--export-renderer",
        choices=["python", "browser"],
        default="python",
        help="Renderer for PNG/GIF/PDF/WebP/MP4/APNG/Lottie. 'browser' records the high-fidelity html output.",
    )
    parser.add_argument("--export-scale", type=float, default=2.0, help="Browser export device scale factor.")
    parser.add_argument("--export-fps", type=int, default=24, help="Browser export frame rate for animated formats.")
    parser.add_argument("--export-frames", type=int, help="Browser export frame count for animated formats.")
    parser.add_argument("--export-quality", type=int, default=80, help="Animated WebP quality from 1 to 100.")
    parser.add_argument(
        "--export-loop-blend-frames",
        type=int,
        default=0,
        help="Crossfade this many final browser frames into frame zero for a seamless loop.",
    )
    parser.add_argument("--all", action="store_true", help="Write every supported output format.")
    parser.add_argument("--html", action="store_true", help="Also write the high-fidelity HTML runtime output.")
    parser.add_argument("--viewer", action="store_true", help="Also write the debug HTML viewer output.")
    parser.add_argument("--quality", action="store_true", help="Also write a quality report JSON.")
    parser.add_argument(
        "--deliver",
        action="store_true",
        help="Validate and transactionally replace all requested artifacts with a SHA-256 receipt.",
    )
    parser.add_argument(
        "--receipt",
        help="Optional delivery receipt path; must be in --outdir and requires --deliver.",
    )
    parser.add_argument("--result", help="Optional path for the structured CLI result JSON.")
    parser.add_argument("--plan-out", help="Optional path for a generated DiagramPlan JSON when using --brief or --text.")
    parser.add_argument("--spec-out", help="Optional path for a compiled DiagramScript JSON when using --plan, --brief, or --text.")
    args = parser.parse_args(argv)

    if args.receipt and not args.deliver:
        parser.error("--receipt requires --deliver")

    if args.list_presets:
        print(json.dumps({"presets": preset_names()}, ensure_ascii=False, indent=2))
        return
    if not args.spec and not args.plan and not args.preset and not args.brief and not args.text:
        parser.error("one of --spec, --plan, --preset, --brief, or --text is required")

    spec_path = Path(args.spec) if args.spec else None
    source_path: Optional[Path] = None
    source_bytes: bytes
    source_kind = "spec"
    generated_plan: Optional[Dict[str, Any]] = None
    if spec_path:
        source_path = spec_path
        source_bytes = spec_path.read_bytes()
        spec = json.loads(source_bytes.decode("utf-8"))
    elif args.plan:
        source_kind = "plan"
        source_path = Path(args.plan)
        source_bytes = source_path.read_bytes()
        generated_plan = json.loads(source_bytes.decode("utf-8"))
        spec = _compile_cli_plan(generated_plan)
    elif args.preset:
        source_kind = "preset"
        source_bytes = canonical_json_bytes({"preset": args.preset, "title": args.title or ""})
        spec = compile_preset(args.preset, title=args.title or "")
    else:
        source_kind = "brief"
        if args.brief:
            source_path = Path(args.brief)
            source_bytes = source_path.read_bytes()
            brief_text = source_bytes.decode("utf-8")
        else:
            brief_text = args.text or ""
            source_bytes = brief_text.encode("utf-8")
        generated_plan = brief_to_plan(
            brief_text or "",
            title=args.title or "",
            style=style_name_from_arg(args.style),
            language=args.diagram_locale,
        )
        spec = _compile_cli_plan(generated_plan)
    if args.diagram_locale != "auto":
        spec = dict(spec)
        spec["locale"] = args.diagram_locale
    additional_artifacts: Dict[str, Any] = {}
    if args.deliver:
        if args.plan_out and generated_plan is not None and source_kind == "brief":
            additional_artifacts["compiled_plan"] = (Path(args.plan_out), json_output_bytes(generated_plan))
        if args.spec_out and source_kind in {"plan", "brief"}:
            additional_artifacts["compiled_specification"] = (Path(args.spec_out), json_output_bytes(spec))
    try:
        scene = compile_scene(spec, repo_root=args.repo_root)
    except DiagramScriptValidationError as exc:
        result = {"ok": False, "error": exc.to_result()}
        _emit_result(result, args.result, stderr=True)
        raise SystemExit(2)

    if not args.deliver:
        if args.plan_out and generated_plan is not None and source_kind == "brief":
            write_json(args.plan_out, generated_plan)
        if args.spec_out and source_kind in {"plan", "brief"}:
            write_json(args.spec_out, spec)

    style = load_style(resolve_style_path(args.style, scene.style.name, spec_path))
    if scene.icon_system:
        style = deep_merge(style, {"icon_system": scene.icon_system})
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    formats = _requested_formats(args)
    if args.deliver and args.result:
        result_path = Path(args.result).resolve()
        receipt_path = (
            Path(args.receipt) if args.receipt else outdir / f"{args.basename}.delivery.json"
        ).resolve()
        delivery_targets = {
            (outdir / f"{args.basename}{FORMAT_EXTENSIONS[format_name]}").resolve()
            for format_name in formats
        }
        delivery_targets.add(receipt_path)
        delivery_targets.update(target.resolve() for target, _data in additional_artifacts.values())
        if result_path in delivery_targets:
            parser.error("--result must not overwrite a delivered artifact or receipt")
    frozen_runtime_source: Optional[bytes] = None
    if args.deliver and args.runtime_dependency == "inline" and args.runtime_source:
        frozen_runtime_source = Path(args.runtime_source).read_bytes()
    if args.deliver:
        try:
            outputs, delivery = deliver_artifacts(
                outdir=outdir,
                basename=args.basename,
                formats=formats,
                extensions=FORMAT_EXTENSIONS,
                source=source_record(source_kind, source_bytes, source_path),
                specification=spec,
                style=style,
                render_options=_render_options(args, frozen_runtime_source),
                quality=quality_report(scene, style),
                render=lambda stage_dir: _render_outputs(
                    scene,
                    style,
                    args,
                    formats,
                    stage_dir,
                    frozen_runtime_source=frozen_runtime_source,
                ),
                receipt_path=Path(args.receipt) if args.receipt else None,
                additional_artifacts=additional_artifacts,
                evidence=scene.source_evidence,
            )
        except DeliveryError as exc:
            _emit_result(exc.to_result(), args.result, stderr=True)
            raise SystemExit(3)
    else:
        try:
            outputs = _render_outputs(scene, style, args, formats, outdir)
        except ValueError as exc:
            parser.error(str(exc))

    result = {
        "ok": True,
        "schema": {"name": "DiagramScript", "version": scene.version},
        "source": source_kind,
        "locale": scene.locale,
        "preset": scene.preset,
        "icon_system": scene.icon_system or style.get("icon_system"),
        "style": style.get("name", scene.style.name or "minimal-light"),
        "outputs": outputs,
        "stats": scene.stats(),
    }
    if args.deliver:
        result["delivery"] = delivery
    if generated_plan is not None:
        result["plan"] = {
            "schema": {"name": "DiagramPlan", "version": generated_plan["version"]},
        }
        if generated_plan.get("version") == "0.1":
            result["plan"]["layout_strategy"] = generated_plan["layout_strategy"]
        else:
            result["plan"]["resolved_presentation"] = scene.resolved_presentation
    _emit_result(result, args.result)


def _render_outputs(
    scene: Any,
    style: Dict[str, Any],
    args: argparse.Namespace,
    formats: List[str],
    outdir: Path,
    *,
    frozen_runtime_source: Optional[bytes] = None,
) -> Dict[str, Dict[str, Any]]:
    outputs: Dict[str, Dict[str, Any]] = {}
    runtime_source = Path(args.runtime_source) if args.runtime_source else None
    if frozen_runtime_source is not None:
        runtime_source = outdir / ".runtime-source.js"
        runtime_source.write_bytes(frozen_runtime_source)
    for format_name in formats:
        output_path = outdir / f"{args.basename}{FORMAT_EXTENSIONS[format_name]}"
        if format_name == "quality":
            outputs[format_name] = write_quality(scene, style, output_path)
        elif format_name == "html":
            outputs[format_name] = write_html(
                scene,
                style,
                output_path,
                runtime=args.html_runtime or "gsap",
                dependency_mode=args.runtime_dependency,
                dependency_source=runtime_source,
                locale=args.viewer_locale,
                runtime_mode=args.runtime_mode,
            )
        elif args.export_renderer == "browser" and format_name in BROWSER_CAPTURE_FORMATS:
            outputs[format_name] = write_browser_capture(
                scene,
                style,
                output_path,
                format_name,
                runtime=args.html_runtime or "gsap",
                frames=args.export_frames,
                fps=args.export_fps,
                scale=args.export_scale,
                loop_blend_frames=args.export_loop_blend_frames,
                quality=args.export_quality,
            )
        else:
            outputs[format_name] = EXPORTERS[format_name](scene, style, output_path)
    return outputs


def _render_options(args: argparse.Namespace, frozen_runtime_source: Optional[bytes] = None) -> Dict[str, Any]:
    options = {
        "html_runtime": args.html_runtime or "gsap",
        "runtime_dependency": args.runtime_dependency,
        "runtime_mode": args.runtime_mode,
        "export_renderer": args.export_renderer,
        "export_scale": args.export_scale,
        "export_fps": args.export_fps,
        "export_frames": args.export_frames,
        "export_quality": args.export_quality,
        "export_loop_blend_frames": args.export_loop_blend_frames,
        "diagram_locale": args.diagram_locale,
        "viewer_locale": args.viewer_locale,
    }
    if frozen_runtime_source is not None:
        options["runtime_source"] = source_record(
            "runtime-dependency",
            frozen_runtime_source,
            Path(args.runtime_source),
        )
    return options


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
            resource_root("styles") / f"{value}.json",
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
    Path(path).write_bytes(json_output_bytes(data))


def json_output_bytes(data: Dict[str, Any]) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _requested_formats(args: argparse.Namespace) -> List[str]:
    if args.all:
        return list(EXPORTERS.keys())
    requested = ["svg"]
    if args.formats:
        requested = [_canonical_format(item.strip()) for item in args.formats.split(",") if item.strip()]
        if not requested:
            raise SystemExit("at least one output format is required")
    if args.html and "html" not in requested:
        requested.append("html")
    if args.viewer and "viewer" not in requested:
        requested.append("viewer")
    if args.quality and "quality" not in requested:
        requested.append("quality")
    unknown = [item for item in requested if item not in EXPORTERS]
    if unknown:
        raise SystemExit(f"unsupported format(s): {', '.join(unknown)}")
    return _dedupe(requested)


def _canonical_format(value: str) -> str:
    if value in {"html-runtime", "runtime-html", "runtime"}:
        return "html"
    return value


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

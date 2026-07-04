"""Export helpers for SVG, raster, animation, and interchange formats."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .model import Edge, Node, Point, Scene
from .quality import quality_report
from .renderer_svg import render_html, render_svg
from .styles import role_style


PointList = List[Point]


def write_svg(scene: Scene, style: Dict[str, Any], path: Path) -> Dict[str, str]:
    path.write_text(render_svg(scene, style), encoding="utf-8")
    return _done("svg", path)


def write_html(scene: Scene, style: Dict[str, Any], path: Path) -> Dict[str, str]:
    svg = render_svg(scene, style)
    path.write_text(render_html(svg, scene.title.text), encoding="utf-8")
    return _done("html", path)


def write_quality(scene: Scene, path: Path) -> Dict[str, Any]:
    report = quality_report(scene)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    result = _done("quality", path)
    result["summary"] = report["summary"]
    result["ok"] = report["ok"]
    return result


def write_lottie(scene: Scene, style: Dict[str, Any], path: Path) -> Dict[str, str]:
    data = {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": 120,
        "w": scene.canvas.width,
        "h": scene.canvas.height,
        "nm": scene.title.text,
        "ddd": 0,
        "assets": [],
        "layers": _lottie_layers(scene, style),
        "meta": {"g": "AniDiagram clean-room lottie exporter"},
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return _done("lottie", path)


def write_png(scene: Scene, style: Dict[str, Any], path: Path) -> Dict[str, str]:
    image = _render_frame(scene, style)
    if image is None:
        return _skipped("png", path, "Pillow is not installed")
    image.save(path, format="PNG")
    return _done("png", path)


def write_pdf(scene: Scene, style: Dict[str, Any], path: Path) -> Dict[str, str]:
    image = _render_frame(scene, style)
    if image is None:
        return _skipped("pdf", path, "Pillow is not installed")
    image.convert("RGB").save(path, format="PDF")
    return _done("pdf", path)


def write_gif(scene: Scene, style: Dict[str, Any], path: Path, frames: int = 16) -> Dict[str, str]:
    images = _render_frames(scene, style, frames)
    if not images:
        return _skipped("gif", path, "Pillow is not installed")
    images[0].save(path, save_all=True, append_images=images[1:], duration=90, loop=0, format="GIF")
    return _done("gif", path)


def write_apng(scene: Scene, style: Dict[str, Any], path: Path, frames: int = 16) -> Dict[str, str]:
    images = _render_frames(scene, style, frames)
    if not images:
        return _skipped("apng", path, "Pillow is not installed")
    try:
        images[0].save(path, save_all=True, append_images=images[1:], duration=90, loop=0, format="PNG")
    except Exception as exc:
        return _skipped("apng", path, str(exc))
    return _done("apng", path)


def write_webp(scene: Scene, style: Dict[str, Any], path: Path, frames: int = 16) -> Dict[str, str]:
    images = _render_frames(scene, style, frames)
    if not images:
        return _skipped("webp", path, "Pillow is not installed")
    try:
        images[0].save(path, save_all=True, append_images=images[1:], duration=90, loop=0, format="WEBP")
    except Exception as exc:
        return _skipped("webp", path, str(exc))
    return _done("webp", path)


def write_mp4(scene: Scene, style: Dict[str, Any], path: Path, frames: int = 24) -> Dict[str, str]:
    images = _render_frames(scene, style, frames)
    if not images:
        return _skipped("mp4", path, "Pillow is not installed")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return _skipped("mp4", path, "ffmpeg is not installed")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for index, image in enumerate(images):
            image.save(tmp_path / f"frame-{index:04d}.png", format="PNG")
        command = [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-framerate",
            "12",
            "-i",
            str(tmp_path / "frame-%04d.png"),
            "-pix_fmt",
            "yuv420p",
            str(path),
        ]
        completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if completed.returncode != 0:
            return _skipped("mp4", path, completed.stderr.strip() or "ffmpeg failed")
    return _done("mp4", path)


def _render_frames(scene: Scene, style: Dict[str, Any], frames: int) -> List[Any]:
    images = []
    for frame in range(frames):
        image = _render_frame(scene, style, frame=frame, frames=frames)
        if image is None:
            return []
        images.append(image)
    return images


def _render_frame(scene: Scene, style: Dict[str, Any], frame: int = 0, frames: int = 1) -> Optional[Any]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None

    canvas = style.get("canvas", {})
    background = canvas.get("background", "#ffffff")
    grid = canvas.get("grid", "#edf2f7")
    muted = canvas.get("muted", "#5b6778")
    image = Image.new("RGBA", (scene.canvas.width, scene.canvas.height), background)
    draw = ImageDraw.Draw(image)
    for x in range(0, scene.canvas.width, 32):
        draw.line((x, 0, x, scene.canvas.height), fill=grid, width=1)
    for y in range(0, scene.canvas.height, 32):
        draw.line((0, y, scene.canvas.width, y), fill=grid, width=1)
    font = ImageFont.load_default()
    title_font = ImageFont.load_default()
    draw.text((90, 64), scene.title.text, fill=canvas.get("text", "#172033"), font=title_font)
    draw.text((74, 112), scene.title.subtitle, fill=muted, font=font)

    for group in scene.groups:
        x, y, w, h = group.bounds
        role = role_style(style, group.role)
        draw.rounded_rectangle((x, y, x + w, y + h), radius=22, outline=group.stroke or role.get("stroke", "#94a3b8"), width=2)
        draw.text((x + 18, y + 18), group.label, fill=muted, font=font)

    node_map = {node.node_id: node for node in scene.nodes}
    for edge_index, edge in enumerate(scene.edges):
        points = _edge_points(edge, node_map)
        role = role_style(style, edge.role)
        stroke = edge.stroke or role.get("stroke", "#64748b")
        draw.line(points, fill=stroke, width=max(1, int(edge.width or style.get("edge", {}).get("width", 2.4))))
        if edge.label:
            sx, sy = points[0]
            ex, ey = points[-1]
            draw.text(((sx + ex) / 2, (sy + ey) / 2 - 16), edge.label, fill=muted, font=font)
        if frames > 1 and edge.motion.enabled:
            point = points[(frame + edge_index) % len(points)]
            draw.ellipse((point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5), fill=stroke)

    for node in scene.nodes:
        x, y = node.position
        w, h = node.size
        role = role_style(style, node.role)
        fill = node.fill or role.get("fill", "#f8fafc")
        stroke = node.stroke or role.get("stroke", "#94a3b8")
        text = role.get("text", canvas.get("text", "#172033"))
        draw.rounded_rectangle((x, y, x + w, y + h), radius=int(node.radius or style.get("node", {}).get("radius", 14)), fill=fill, outline=stroke, width=int(node.stroke_width or 2))
        if node.step is not None:
            draw.ellipse((x + 4, y + 4, x + 32, y + 32), fill=stroke)
            draw.text((x + 14, y + 12), str(node.step), fill=fill, font=font)
        draw.text((x + 14, y + h / 2 - 12), node.label, fill=text, font=font)
        draw.text((x + 14, y + h / 2 + 8), node.caption, fill=text, font=font)
    return image


def _edge_points(edge: Edge, nodes: Dict[str, Node]) -> PointList:
    if len(edge.points) >= 2:
        return list(edge.points)
    source = nodes.get(edge.source)
    target = nodes.get(edge.target)
    if not source or not target:
        return [(0, 0), (0, 0)]
    start = _anchor(source, target)
    end = _anchor(target, source)
    sx, sy = start
    ex, ey = end
    if edge.route == "hv":
        return [start, (ex, sy), end]
    if edge.route == "vh":
        return [start, (sx, ey), end]
    if edge.route == "orthogonal":
        mid = (sx + ex) / 2
        return [start, (mid, sy), (mid, ey), end]
    return [start, end]


def _anchor(source: Node, target: Node) -> Point:
    sx, sy = source.position
    sw, sh = source.size
    tx, ty = target.position
    tw, th = target.size
    scx, scy = sx + sw / 2, sy + sh / 2
    tcx, tcy = tx + tw / 2, ty + th / 2
    if abs(tcx - scx) >= abs(tcy - scy):
        return (sx + sw if tcx >= scx else sx, scy)
    return (scx, sy + sh if tcy >= scy else sy)


def _lottie_layers(scene: Scene, style: Dict[str, Any]) -> List[Dict[str, Any]]:
    layers = []
    for index, node in enumerate(scene.nodes, start=1):
        role = role_style(style, node.role)
        x, y = node.position
        w, h = node.size
        layers.append(
            {
                "ddd": 0,
                "ind": index,
                "ty": 4,
                "nm": node.label,
                "ks": {"o": {"k": 100}, "r": {"k": 0}, "p": {"k": [x + w / 2, y + h / 2, 0]}, "a": {"k": [0, 0, 0]}, "s": {"k": [100, 100, 100]}},
                "shapes": [
                    {"ty": "rc", "s": {"k": [w, h]}, "p": {"k": [0, 0]}, "r": {"k": node.radius or 14}},
                    {"ty": "fl", "c": {"k": _hex_to_lottie(role.get("fill", "#f8fafc"))}, "o": {"k": 100}},
                    {"ty": "st", "c": {"k": _hex_to_lottie(role.get("stroke", "#94a3b8"))}, "w": {"k": node.stroke_width or 2}},
                ],
                "ip": 0,
                "op": 120,
                "st": 0,
                "bm": 0,
            }
        )
    return layers


def _hex_to_lottie(value: str) -> List[float]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        return [0.5, 0.5, 0.5, 1]
    return [int(value[0:2], 16) / 255, int(value[2:4], 16) / 255, int(value[4:6], 16) / 255, 1]


def _done(format_name: str, path: Path) -> Dict[str, str]:
    return {"format": format_name, "path": str(path.resolve()), "status": "written"}


def _skipped(format_name: str, path: Path, reason: str) -> Dict[str, str]:
    return {"format": format_name, "path": str(path.resolve()), "status": "skipped", "reason": reason}

"""Export helpers for SVG, raster, animation, and interchange formats."""

from __future__ import annotations

import base64
import hashlib
import inspect
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .effects import canonical_edge_effect, channel_effect, effect_active
from .model import Edge, Node, Point, Scene
from .quality import quality_report
from .renderer_html_runtime import render_html_runtime
from .renderer_svg import CONTINUOUS_EDGE_MOTION, PARTICLE_EDGE_MOTION, particle_radii, policy_allows, render_html, render_svg
from .styles import role_style


PointList = List[Point]
BROWSER_CAPTURE_FORMATS = {"png", "gif", "pdf", "webp", "mp4", "apng", "lottie"}
DEFAULT_BROWSER_CAPTURE_FPS = 24
DEFAULT_BROWSER_CAPTURE_FRAMES = 48
GSAP_BROWSER_CAPTURE_VERSION = "3.15.0"
BROWSER_CAPTURE_CONTRACT_VERSION = "browser-capture-v1"
_GSAP_FLOATING_CDN_URL = "https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"
_GSAP_CAPTURE_CDN_URL = (
    f"https://cdn.jsdelivr.net/npm/gsap@{GSAP_BROWSER_CAPTURE_VERSION}/dist/gsap.min.js"
)


def write_svg(scene: Scene, style: Dict[str, Any], path: Path) -> Dict[str, str]:
    path.write_text(render_svg(scene, style), encoding="utf-8")
    return _done("svg", path)


def write_viewer(scene: Scene, style: Dict[str, Any], path: Path) -> Dict[str, str]:
    svg = render_svg(scene, style)
    path.write_text(render_html(svg, scene.title.text), encoding="utf-8")
    return _done("viewer", path)


def write_html(scene: Scene, style: Dict[str, Any], path: Path, runtime: str = "gsap") -> Dict[str, str]:
    path.write_text(render_html_runtime(scene, style, runtime=runtime), encoding="utf-8")
    return _done("html", path)


def write_html_runtime(scene: Scene, style: Dict[str, Any], path: Path, runtime: str = "gsap") -> Dict[str, str]:
    return write_html(scene, style, path, runtime=runtime)


def write_quality(scene: Scene, style: Dict[str, Any], path: Path) -> Dict[str, Any]:
    report = quality_report(scene, style)
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


def write_browser_capture(
    scene: Scene,
    style: Dict[str, Any],
    path: Path,
    format_name: str,
    runtime: str = "gsap",
    frames: Optional[int] = None,
    fps: int = DEFAULT_BROWSER_CAPTURE_FPS,
    scale: float = 2.0,
    loop_blend_frames: int = 0,
) -> Dict[str, Any]:
    """Write visual export formats by recording the high-fidelity HTML runtime."""

    if format_name not in BROWSER_CAPTURE_FORMATS:
        return _skipped(format_name, path, "browser capture does not support this format")
    frame_count = 1 if format_name in {"png", "pdf"} else max(1, frames or DEFAULT_BROWSER_CAPTURE_FRAMES)
    fps = max(1, int(fps))
    scale = max(1.0, float(scale))

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        html_path = tmp_path / "runtime.html"
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        html_source = browser_capture_html(scene, style, runtime)
        html_path.write_text(html_source, encoding="utf-8")

        capture = _capture_browser_runtime(
            scene=scene,
            html_path=html_path,
            frames_dir=frames_dir,
            pdf_path=path if format_name == "pdf" else None,
            format_name=format_name,
            frames=frame_count,
            fps=fps,
            scale=scale,
        )
        if capture["status"] == "skipped":
            return _skipped(format_name, path, capture["reason"])

        frame_paths = [frames_dir / f"frame-{index:04d}.png" for index in range(frame_count)]
        applied_loop_blend = 0
        if format_name not in {"png", "pdf"}:
            applied_loop_blend = _blend_loop_seam(frame_paths, loop_blend_frames)
        if format_name == "png":
            shutil.copyfile(frame_paths[0], path)
        elif format_name == "pdf":
            pass
        elif format_name == "mp4":
            mp4_result = _write_mp4_from_frame_paths(frame_paths, path, fps)
            if mp4_result["status"] == "skipped":
                return mp4_result
        elif format_name == "lottie":
            lottie_result = _write_browser_lottie(scene, frame_paths, path, fps, scale)
            if lottie_result["status"] == "skipped":
                return lottie_result
        else:
            packaged = _write_browser_image_sequence(format_name, frame_paths, path, fps, style)
            if packaged["status"] == "skipped":
                return packaged

    result = _done(format_name, path)
    result["renderer"] = "browser"
    result["fps"] = fps
    result["frames"] = frame_count
    result["scale"] = scale
    result["loop_blend_frames"] = applied_loop_blend
    if runtime == "gsap":
        result["runtime_dependency"] = f"gsap@{GSAP_BROWSER_CAPTURE_VERSION}"
    if format_name == "webp":
        result["capture_contract"] = BROWSER_CAPTURE_CONTRACT_VERSION
        result["input_sha256"] = webp_browser_capture_input_sha256(
            scene,
            style,
            runtime=runtime,
            frames=frame_count,
            fps=fps,
            scale=scale,
            loop_blend_frames=loop_blend_frames,
        )
    return result


def browser_capture_html(scene: Scene, style: Dict[str, Any], runtime: str = "gsap") -> str:
    return _pin_browser_capture_dependencies(
        render_html_runtime(scene, style, runtime=runtime),
        runtime,
    )


def webp_browser_capture_input_sha256(
    scene: Scene,
    style: Dict[str, Any],
    runtime: str = "gsap",
    frames: int = DEFAULT_BROWSER_CAPTURE_FRAMES,
    fps: int = DEFAULT_BROWSER_CAPTURE_FPS,
    scale: float = 2.0,
    loop_blend_frames: int = 0,
) -> str:
    try:
        from PIL import __version__ as pillow_version
    except ImportError:
        pillow_version = "unavailable"
    payload = {
        "contract": BROWSER_CAPTURE_CONTRACT_VERSION,
        "html": browser_capture_html(scene, style, runtime),
        "format": "webp",
        "frames": int(frames),
        "fps": int(fps),
        "scale": float(scale),
        "loop_blend_frames": int(loop_blend_frames),
        "capture_script": _browser_capture_script(),
        "blend_implementation": inspect.getsource(_blend_loop_seam),
        "packaging_implementation": inspect.getsource(_write_browser_image_sequence),
        "pillow_version": pillow_version,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _pin_browser_capture_dependencies(html_source: str, runtime: str) -> str:
    if runtime != "gsap":
        return html_source
    if _GSAP_FLOATING_CDN_URL not in html_source:
        raise RuntimeError("GSAP browser capture dependency marker changed")
    return html_source.replace(_GSAP_FLOATING_CDN_URL, _GSAP_CAPTURE_CDN_URL, 1)


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
    gif_images = [_flatten_frame_for_gif(image, style) for image in images]
    gif_images[0].save(
        path,
        save_all=True,
        append_images=gif_images[1:],
        duration=90,
        loop=0,
        format="GIF",
        optimize=False,
        disposal=2,
    )
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


def _write_mp4_from_frame_paths(frame_paths: List[Path], path: Path, fps: int) -> Dict[str, str]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return _skipped("mp4", path, "ffmpeg is not installed")
    if not frame_paths:
        return _skipped("mp4", path, "no browser frames were captured")
    command = [
        ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-framerate",
        str(max(1, fps)),
        "-i",
        str(frame_paths[0].parent / "frame-%04d.png"),
        "-pix_fmt",
        "yuv420p",
        str(path),
    ]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if completed.returncode != 0:
        return _skipped("mp4", path, completed.stderr.strip() or "ffmpeg failed")
    return _done("mp4", path)


def _blend_loop_seam(frame_paths: List[Path], blend_frames: int) -> int:
    """Crossfade the tail into frame zero so looping media has no hard cut."""

    try:
        from PIL import Image
    except Exception:
        return 0
    applied = min(max(0, int(blend_frames)), max(0, len(frame_paths) - 1))
    if applied == 0:
        return 0
    with Image.open(frame_paths[0]) as source:
        first = source.convert("RGBA")
    try:
        for offset, frame_path in enumerate(frame_paths[-applied:]):
            with Image.open(frame_path) as source:
                current = source.convert("RGBA")
            try:
                alpha = (offset + 1) / applied
                blended = Image.blend(current, first, alpha)
                try:
                    blended.save(frame_path, format="PNG")
                finally:
                    blended.close()
            finally:
                current.close()
    finally:
        first.close()
    return applied


def _write_browser_image_sequence(format_name: str, frame_paths: List[Path], path: Path, fps: int, style: Dict[str, Any]) -> Dict[str, str]:
    try:
        from PIL import Image
    except Exception:
        return _skipped(format_name, path, "Pillow is not installed")
    if not frame_paths:
        return _skipped(format_name, path, "no browser frames were captured")
    images = [Image.open(frame_path).convert("RGBA") for frame_path in frame_paths]
    duration_ms = max(1, int(round(1000 / max(1, fps))))
    try:
        if format_name == "gif":
            gif_images = [_flatten_frame_for_gif(image, style) for image in images]
            gif_images[0].save(
                path,
                save_all=True,
                append_images=gif_images[1:],
                duration=duration_ms,
                loop=0,
                format="GIF",
                optimize=False,
                disposal=2,
            )
        elif format_name == "apng":
            images[0].save(path, save_all=True, append_images=images[1:], duration=duration_ms, loop=0, format="PNG")
        elif format_name == "webp":
            images[0].save(path, save_all=True, append_images=images[1:], duration=duration_ms, loop=0, format="WEBP")
        else:
            return _skipped(format_name, path, "browser image sequence does not support this format")
    except Exception as exc:
        return _skipped(format_name, path, str(exc))
    finally:
        for image in images:
            image.close()
    return _done(format_name, path)


def _write_browser_lottie(scene: Scene, frame_paths: List[Path], path: Path, fps: int, scale: float) -> Dict[str, str]:
    if not frame_paths:
        return _skipped("lottie", path, "no browser frames were captured")
    width = max(1, int(round(scene.canvas.width * scale)))
    height = max(1, int(round(scene.canvas.height * scale)))
    assets = []
    layers = []
    for index, frame_path in enumerate(frame_paths):
        asset_id = f"frame_{index:04d}"
        payload = base64.b64encode(frame_path.read_bytes()).decode("ascii")
        assets.append({"id": asset_id, "w": width, "h": height, "u": "", "p": f"data:image/png;base64,{payload}", "e": 1})
        layers.append(
            {
                "ddd": 0,
                "ind": index + 1,
                "ty": 2,
                "nm": f"browser-frame-{index:04d}",
                "refId": asset_id,
                "ks": {
                    "o": {"k": 100},
                    "r": {"k": 0},
                    "p": {"k": [0, 0, 0]},
                    "a": {"k": [0, 0, 0]},
                    "s": {"k": [100, 100, 100]},
                },
                "ip": index,
                "op": index + 1,
                "st": 0,
                "sr": 1,
                "bm": 0,
            }
        )
    data = {
        "v": "5.7.4",
        "fr": max(1, fps),
        "ip": 0,
        "op": len(frame_paths),
        "w": width,
        "h": height,
        "nm": f"{scene.title.text} browser capture",
        "ddd": 0,
        "assets": assets,
        "layers": layers,
        "meta": {"g": "AniDiagram browser-captured lottie exporter", "renderer": "browser"},
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return _done("lottie", path)


def _capture_browser_runtime(
    scene: Scene,
    html_path: Path,
    frames_dir: Path,
    pdf_path: Optional[Path],
    format_name: str,
    frames: int,
    fps: int,
    scale: float,
) -> Dict[str, str]:
    node, env, reason = _playwright_node_env()
    if reason:
        return {"status": "skipped", "reason": reason}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        script_path = tmp_path / "capture-runtime.js"
        config_path = tmp_path / "capture-config.json"
        script_path.write_text(_browser_capture_script(), encoding="utf-8")
        config = {
            "htmlPath": str(html_path.resolve()),
            "outputDir": str(frames_dir.resolve()),
            "pdfPath": str(pdf_path.resolve()) if pdf_path else "",
            "format": format_name,
            "frames": frames,
            "fps": fps,
            "scale": scale,
            "width": scene.canvas.width,
            "height": scene.canvas.height,
            "warmupMs": 850,
            "staticSettleMs": 2400,
            "timeoutMs": 30000,
        }
        config_path.write_text(json.dumps(config), encoding="utf-8")
        timeout = _browser_capture_timeout_seconds(frames, fps, scale)
        completed = subprocess.run(
            [node, str(script_path), str(config_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            timeout=timeout,
        )
    if completed.returncode != 0:
        reason_text = (completed.stderr or completed.stdout).strip() or "browser capture failed"
        return {"status": "skipped", "reason": reason_text}
    return {"status": "written", "reason": ""}


def _browser_capture_timeout_seconds(frames: int, fps: int, scale: float) -> int:
    """Budget a whole browser capture, including per-frame SVG screenshots.

    Screenshot encoding cost grows with both the number of frames and output
    pixel density. Keep a generous fixed startup allowance, then scale the
    deadline so slower CI runners do not terminate otherwise healthy formal
    export captures.
    """

    frame_count = max(1, int(frames))
    frame_rate = max(1, int(fps))
    pixel_scale = max(1.0, float(scale))
    playback_seconds = math.ceil(frame_count / frame_rate)
    screenshot_seconds = math.ceil(frame_count * pixel_scale * 0.65)
    return max(90, 45 + playback_seconds + screenshot_seconds)


def _playwright_node_env() -> Tuple[str, Dict[str, str], str]:
    node = shutil.which("node")
    if not node:
        return "", {}, "Node.js is not installed; browser capture requires Node Playwright"
    env = os.environ.copy()
    node_paths = [item for item in env.get("NODE_PATH", "").split(os.pathsep) if item]
    local_node_modules = Path.cwd() / "node_modules"
    if local_node_modules.is_dir():
        node_paths.append(str(local_node_modules.resolve()))
    playwright_bin = shutil.which("playwright")
    if playwright_bin:
        resolved = Path(playwright_bin).resolve()
        if resolved.name == "cli.js" and resolved.parent.name == "playwright":
            node_paths.append(str(resolved.parent.parent))
    if node_paths:
        env["NODE_PATH"] = os.pathsep.join(_dedupe_paths(node_paths))
    probe = subprocess.run(
        [node, "-e", "require.resolve('playwright')"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    if probe.returncode != 0:
        return "", {}, "Node Playwright is not installed; install Playwright and Chromium to use --export-renderer browser"
    return node, env, ""


def _dedupe_paths(values: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _browser_capture_script() -> str:
    return r"""
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

async function main() {
  const config = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({
      viewport: { width: config.width, height: config.height },
      deviceScaleFactor: config.scale
    });
    page.setDefaultTimeout(config.timeoutMs || 30000);
    await page.goto(pathToFileURL(config.htmlPath).href, { waitUntil: "load" });
    await page.waitForSelector("svg");
    await page.waitForLoadState("networkidle", { timeout: config.timeoutMs || 30000 }).catch(() => {});
    await page.waitForTimeout(config.warmupMs || 800);
    const runtimeState = await page.evaluate(() => {
      const manifestElement = document.getElementById("anidiagram-motion-manifest");
      let manifestIcons = 0;
      try {
        manifestIcons = manifestElement ? (JSON.parse(manifestElement.textContent || "{}").icons || []).length : 0;
      } catch (error) {}
      return {
        manifestIcons,
        timelines: (window.__ANIDIAGRAM_TIMELINES__ || []).length,
        gsapLoaded: Boolean(window.gsap)
      };
    });
    if (runtimeState.manifestIcons > 0 && !runtimeState.gsapLoaded) {
      throw new Error("GSAP did not load, so high-fidelity runtime capture cannot proceed");
    }
    if (runtimeState.manifestIcons > 0 && runtimeState.timelines === 0) {
      throw new Error("AniDiagram runtime did not start any high-fidelity timelines");
    }
    await page.evaluate(() => {
      const svg = document.querySelector("svg");
      if (svg && svg.setCurrentTime) {
        try {
          svg.setCurrentTime(0);
          svg.unpauseAnimations();
        } catch (error) {}
      }
      if (window.AniDiagramRuntime && window.AniDiagramRuntime.restart) {
        window.AniDiagramRuntime.restart();
      }
    });
    if (config.format === "png" || config.format === "pdf") {
      await page.waitForTimeout(config.staticSettleMs || 2200);
      await page.addStyleTag({ content: ".title-sweep { display: none !important; }" });
      await page.evaluate(() => {
        const svg = document.querySelector("svg");
        if (svg && svg.pauseAnimations) {
          try {
            svg.pauseAnimations();
          } catch (error) {}
        }
        if (window.gsap && window.gsap.globalTimeline) {
          window.gsap.globalTimeline.pause();
        }
      });
    }
    if (config.format === "pdf") {
      await page.addStyleTag({ content: `
        @page { size: ${config.width}px ${config.height}px; margin: 0; }
        html, body, main { margin: 0 !important; padding: 0 !important; min-height: 0 !important; background: transparent !important; display: block !important; }
        .toolbar { display: none !important; }
        .stage { border: 0 !important; border-radius: 0 !important; overflow: visible !important; width: ${config.width}px !important; min-height: 0 !important; background: transparent !important; }
        .viewport { transform: none !important; width: ${config.width}px !important; }
        svg { width: ${config.width}px !important; height: ${config.height}px !important; }
      `});
      await page.pdf({
        path: config.pdfPath,
        width: `${config.width}px`,
        height: `${config.height}px`,
        printBackground: true,
        margin: { top: 0, right: 0, bottom: 0, left: 0 }
      });
      return;
    }
    const svg = page.locator("svg").first();
    const fps = Math.max(1, config.fps || 24);
    const frameDelay = 1000 / fps;
    await page.evaluate(() => {
      const svgElement = document.querySelector("svg");
      if (svgElement && svgElement.pauseAnimations) {
        try {
          svgElement.pauseAnimations();
        } catch (error) {}
      }
      (window.__ANIDIAGRAM_TIMELINES__ || []).forEach((tl) => {
        if (!tl) return;
        if (typeof tl.pause === "function") tl.pause();
      });
      if (window.gsap && window.gsap.globalTimeline) {
        window.gsap.globalTimeline.pause();
      }
    });
    for (let index = 0; index < Math.max(1, config.frames || 1); index += 1) {
      const frameSeconds = index / fps;
      await page.evaluate((seconds) => {
        const svgElement = document.querySelector("svg");
        if (svgElement && svgElement.setCurrentTime) {
          try {
            svgElement.setCurrentTime(seconds);
          } catch (error) {}
        }
        (window.__ANIDIAGRAM_TIMELINES__ || []).forEach((tl) => {
          if (!tl || typeof tl.totalTime !== "function") return;
          const delaySeconds = typeof tl.delay === "function" ? Number(tl.delay()) || 0 : 0;
          const durationSeconds = typeof tl.duration === "function" ? Number(tl.duration()) || 0 : 0;
          const repeatDelaySeconds = typeof tl.repeatDelay === "function" ? Number(tl.repeatDelay()) || 0 : 0;
          const cycleSeconds = Math.max(0.001, durationSeconds + repeatDelaySeconds);
          const localSeconds = Math.max(0, seconds - delaySeconds);
          tl.totalTime(localSeconds % cycleSeconds, false);
          if (typeof tl.pause === "function") tl.pause();
        });
      }, frameSeconds);
      await page.waitForTimeout(Math.min(40, frameDelay));
      const file = path.join(config.outputDir, `frame-${String(index).padStart(4, "0")}.png`);
      await svg.screenshot({ path: file, animations: "allow" });
    }
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
"""


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
    draw = ImageDraw.Draw(image, "RGBA")
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

    for node in scene.nodes:
        x, y = node.position
        w, h = node.size
        role = role_style(style, node.role)
        fill = node.fill or role.get("fill", "#f8fafc")
        stroke = node.stroke or role.get("stroke", "#94a3b8")
        text = role.get("text", canvas.get("text", "#172033"))
        stroke_width = int(node.stroke_width or 2)
        if node.shape == "decision":
            cx, cy = x + w / 2, y + h / 2
            draw.polygon([(cx, y), (x + w, cy), (cx, y + h), (x, cy)], fill=fill, outline=stroke)
            if stroke_width > 1:
                draw.line([(cx, y), (x + w, cy), (cx, y + h), (x, cy), (cx, y)], fill=stroke, width=stroke_width)
        else:
            draw.rounded_rectangle((x, y, x + w, y + h), radius=int(node.radius or style.get("node", {}).get("radius", 14)), fill=fill, outline=stroke, width=stroke_width)
        if node.step is not None:
            draw.ellipse((x + 4, y + 4, x + 32, y + 32), fill=stroke)
            draw.text((x + 14, y + 12), str(node.step), fill=fill, font=font)
        text_x = x + 14 if node.shape != "decision" else x + 34
        draw.text((text_x, y + h / 2 - 12), node.label, fill=text, font=font)
        draw.text((text_x, y + h / 2 + 8), node.caption, fill=text, font=font)
    if frames > 1 and scene.motion.profile != "off":
        _draw_raster_particles(draw, scene, style, node_map, frame, frames)
    return image


def _flatten_frame_for_gif(image: Any, style: Dict[str, Any]) -> Any:
    from PIL import Image

    background = style.get("canvas", {}).get("background", "#ffffff")
    if image.mode == "RGBA":
        base = Image.new("RGBA", image.size, background)
        return Image.alpha_composite(base, image).convert("RGB")
    return image.convert("RGB")


def _draw_raster_particles(draw: Any, scene: Scene, style: Dict[str, Any], nodes: Dict[str, Node], frame: int, frames: int) -> None:
    intensity = max(0.25, min(1.8, scene.motion.intensity))
    edge_width = float(style.get("edge", {}).get("width", 2.4))
    policy = scene.motion_policy
    edge_motion_rank = 0
    particle_motion_rank = 0
    for edge_index, edge in enumerate(scene.edges):
        if not edge.motion.enabled:
            continue
        edge_effect = canonical_edge_effect(channel_effect(scene.motion, style, "edge", edge.effect))
        if not effect_active(scene.motion, edge_effect):
            continue
        edge_mode = edge_effect.preset
        active_rank: Optional[int] = None
        particle_rank: Optional[int] = None
        if edge_mode in CONTINUOUS_EDGE_MOTION:
            edge_motion_rank += 1
            active_rank = edge_motion_rank
        if edge_mode in PARTICLE_EDGE_MOTION:
            particle_motion_rank += 1
            particle_rank = particle_motion_rank
        if not policy_allows(active_rank, policy.max_active_flow_edges):
            continue
        points = _edge_points(edge, nodes)
        if len(points) < 2:
            continue
        role = role_style(style, edge.role)
        stroke = edge.stroke or role.get("stroke", "#64748b")
        color = _hex_to_rgba(stroke, 235)
        phase = (frame / max(1, frames) + edge_index * 0.071 + edge.motion.delay * 0.03) % 1.0
        if edge_mode == "stream-flow":
            for dash_index in range(9):
                start_progress = (phase + dash_index / 9) % 1.0
                end_progress = (start_progress + 0.035) % 1.0
                if end_progress < start_progress:
                    continue
                start = _point_along_polyline(points, start_progress)
                end = _point_along_polyline(points, end_progress)
                draw.line((start, end), fill=color, width=max(2, round(edge_width * 0.86)))
            continue
        if edge_mode not in PARTICLE_EDGE_MOTION:
            continue
        if not policy_allows(particle_rank, policy.max_particle_edges):
            continue
        particle_shape = "solid-dot"
        radii = particle_radii(edge_mode, particle_shape, edge_effect, policy)
        for trail_index, radius in enumerate(radii):
            progress = (phase - trail_index * 0.055) % 1.0
            x, y = _point_along_polyline(points, progress)
            scaled_radius = max(edge_width + 1.0, radius * intensity)
            particle_color = (
                _hex_to_rgba(stroke, (235, 150, 92, 48)[trail_index])
                if edge_mode == "comet-flow"
                else color
            )
            draw.ellipse(
                (x - scaled_radius, y - scaled_radius, x + scaled_radius, y + scaled_radius),
                fill=particle_color,
            )


def _point_along_polyline(points: PointList, progress: float) -> Point:
    if len(points) == 1:
        return points[0]
    segments = []
    total = 0.0
    for start, end in zip(points, points[1:]):
        length = math.hypot(end[0] - start[0], end[1] - start[1])
        if length <= 0:
            continue
        segments.append((start, end, length))
        total += length
    if not segments or total <= 0:
        return points[0]
    target = (progress % 1.0) * total
    walked = 0.0
    for start, end, length in segments:
        if walked + length >= target:
            local = (target - walked) / length
            return (start[0] + (end[0] - start[0]) * local, start[1] + (end[1] - start[1]) * local)
        walked += length
    return segments[-1][1]


def _hex_to_rgba(value: str, alpha: int) -> Tuple[int, int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        return (100, 116, 139, alpha)
    try:
        return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), alpha)
    except ValueError:
        return (100, 116, 139, alpha)


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

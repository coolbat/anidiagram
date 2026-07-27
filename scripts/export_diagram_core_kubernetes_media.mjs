#!/usr/bin/env node
import { execFile } from "node:child_process";
import { mkdtemp, mkdir, rm, stat } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { promisify } from "node:util";
import { fileURLToPath, pathToFileURL } from "node:url";

import { chromium } from "playwright";


const execFileAsync = promisify(execFile);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");


function argument(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : fallback;
}


function positiveNumber(name, fallback) {
  const value = Number(argument(name, fallback));
  if (!Number.isFinite(value) || value <= 0) throw new Error(`${name} must be a positive number`);
  return value;
}


async function runFfmpeg(arguments_) {
  try {
    await execFileAsync("ffmpeg", ["-y", "-loglevel", "error", ...arguments_], {
      maxBuffer: 8 * 1024 * 1024,
    });
  } catch (error) {
    const detail = String(error.stderr || error.stdout || error.message).trim();
    throw new Error(`ffmpeg failed: ${detail}`);
  }
}


async function packageAnimatedWebp(framesDirectory, output, fps) {
  const source = `
import sys
from pathlib import Path
from PIL import Image

frames = []
for frame_path in sorted(Path(sys.argv[1]).glob("frame-*.png")):
    with Image.open(frame_path) as image:
        frames.append(image.convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS))
if not frames:
    raise SystemExit("no PNG frames found")
try:
    frames[0].save(
        sys.argv[2],
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=max(1, round(1000 / int(sys.argv[3]))),
        loop=0,
        quality=78,
        method=6,
    )
finally:
    for frame in frames:
        frame.close()
`;
  try {
    await execFileAsync("python3", ["-c", source, framesDirectory, output, String(fps)], {
      maxBuffer: 8 * 1024 * 1024,
    });
  } catch (error) {
    const detail = String(error.stderr || error.stdout || error.message).trim();
    throw new Error(`Pillow WebP packaging failed: ${detail}`);
  }
}


async function captureFrames({ input, framesDirectory, fps, frames }) {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({
      viewport: { width: 1600, height: 900 },
      deviceScaleFactor: 1,
    });
    page.setDefaultTimeout(30_000);
    const browserErrors = [];
    page.on("pageerror", (error) => browserErrors.push(error.message));
    page.on("console", (message) => {
      if (message.type() === "error") browserErrors.push(message.text());
    });
    await page.goto(pathToFileURL(input).href, { waitUntil: "load" });
    await page.waitForFunction(() => (
      Boolean(window.gsap)
      && Boolean(window.AniDiagramRuntime)
      && (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === 19
      && (window.__ANIDIAGRAM_STAGE_TIMELINES__ || []).length === 23
    ));
    await page.addStyleTag({ content: `
      html, body, main { width: 1600px !important; height: 900px !important; margin: 0 !important; padding: 0 !important; overflow: hidden !important; }
      body { min-width: 0 !important; background: #050816 !important; }
      header, .legend { display: none !important; }
      #stage { width: 1600px !important; height: 900px !important; border: 0 !important; border-radius: 0 !important; box-shadow: none !important; }
      #viewport, #viewport svg { width: 1600px !important; height: 900px !important; transform: none !important; }
    ` });
    await page.evaluate(() => {
      const svg = document.querySelector("#viewport svg");
      if (svg?.pauseAnimations) svg.pauseAnimations();
      (window.__ANIDIAGRAM_TIMELINES__ || []).forEach((timeline) => timeline?.pause?.());
      window.gsap?.globalTimeline?.pause?.();
    });
    const svg = page.locator("#viewport svg");
    for (let index = 0; index < frames; index += 1) {
      const seconds = index / fps;
      await page.evaluate((time) => {
        const svgElement = document.querySelector("#viewport svg");
        if (svgElement?.setCurrentTime) svgElement.setCurrentTime(time);
        (window.__ANIDIAGRAM_TIMELINES__ || []).forEach((timeline) => {
          if (!timeline || typeof timeline.totalTime !== "function") return;
          const delay = typeof timeline.delay === "function" ? Number(timeline.delay()) || 0 : 0;
          const duration = typeof timeline.duration === "function" ? Number(timeline.duration()) || 0 : 0;
          const repeatDelay = typeof timeline.repeatDelay === "function" ? Number(timeline.repeatDelay()) || 0 : 0;
          const cycle = Math.max(0.001, duration + repeatDelay);
          const localTime = Math.max(0, time - delay);
          timeline.totalTime(localTime % cycle, false);
          timeline.pause?.();
        });
      }, seconds);
      await svg.screenshot({
        path: path.join(framesDirectory, `frame-${String(index).padStart(4, "0")}.png`),
        animations: "allow",
      });
    }
    if (browserErrors.length) throw new Error(`browser capture errors: ${browserErrors.join(" | ")}`);
  } finally {
    await browser.close();
  }
}


async function main() {
  const input = path.resolve(argument(
    "--input",
    path.join(ROOT, "gallery", "diagram-core", "kubernetes-production-deep-tech.html"),
  ));
  const outputDirectory = path.resolve(argument(
    "--outdir",
    path.join(ROOT, "outputs", "diagram-core"),
  ));
  const basename = argument("--basename", "kubernetes-production-deep-tech");
  const fps = Math.round(positiveNumber("--fps", 24));
  const seconds = positiveNumber("--seconds", 4);
  const frames = Math.max(1, Math.round(fps * seconds));
  const temporaryDirectory = await mkdtemp(path.join(os.tmpdir(), "anidiagram-k8s-export-"));
  const framesDirectory = path.join(temporaryDirectory, "frames");
  await mkdir(framesDirectory);
  await mkdir(outputDirectory, { recursive: true });
  const framePattern = path.join(framesDirectory, "frame-%04d.png");
  const outputs = {
    gif: path.join(outputDirectory, `${basename}.gif`),
    webp: path.join(outputDirectory, `${basename}.webp`),
    mp4: path.join(outputDirectory, `${basename}.mp4`),
  };
  try {
    await captureFrames({ input, framesDirectory, fps, frames });
    await runFfmpeg([
      "-framerate", String(fps), "-i", framePattern,
      "-vf", "fps=12,scale=960:540:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=192:stats_mode=diff[p];[s1][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle",
      "-loop", "0", outputs.gif,
    ]);
    await packageAnimatedWebp(framesDirectory, outputs.webp, fps);
    await runFfmpeg([
      "-framerate", String(fps), "-i", framePattern,
      "-c:v", "libx264", "-preset", "medium", "-crf", "20",
      "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", outputs.mp4,
    ]);
    const result = {
      source: input,
      fps,
      seconds,
      frames,
      outputs: Object.fromEntries(await Promise.all(
        Object.entries(outputs).map(async ([format, output]) => [
          format,
          { path: output, bytes: (await stat(output)).size },
        ]),
      )),
    };
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } finally {
    await rm(temporaryDirectory, { recursive: true, force: true });
  }
}


main().catch((error) => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 1;
});

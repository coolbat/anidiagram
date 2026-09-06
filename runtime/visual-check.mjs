/* Browser evidence for one frozen standalone HTML; stdout is a JSON receipt. */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const [artifact, destination, dimensions] = process.argv.slice(2);
const viewports = JSON.parse(dimensions);
let chromium;
for (const location of [import.meta.url, path.join(process.cwd(), "package.json")]) {
  try { chromium = createRequire(location)("playwright").chromium; break; } catch { /* Try the caller's dependency installation. */ }
}
if (!chromium) {
  console.log(JSON.stringify({ status: "skipped", reason: "Playwright is unavailable; install the project's browser test dependencies.", captures: [], checks: [] }));
} else {
  let browser;
  const checks = [], captures = [];
  try {
    browser = await chromium.launch({ headless: true });
    for (const viewport of viewports) {
      for (const colorScheme of ["light", "dark"]) {
        const page = await browser.newPage({ viewport, colorScheme, reducedMotion: "reduce", deviceScaleFactor: 1 });
        const errors = [];
        page.on("pageerror", error => errors.push(error.message));
        await page.goto(pathToFileURL(artifact).href, { waitUntil: "load", timeout: 20000 });
        await page.waitForSelector("svg", { timeout: 10000 });
        await page.evaluate(async () => { await document.fonts.ready; await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))); });
        const measured = await page.evaluate(() => {
          const doc = document.documentElement, stage = document.getElementById("stage"), svg = document.querySelector("svg");
          const bounds = svg.getBoundingClientRect(), container = stage?.getBoundingClientRect();
          const contained = !container || (bounds.left >= container.left - 1 && bounds.top >= container.top - 1 && bounds.right <= container.right + 1 && bounds.bottom <= container.bottom + 1);
          const warning = document.getElementById("runtime-warning");
          return { width: innerWidth, height: innerHeight, scroll_width: doc.scrollWidth, scroll_height: doc.scrollHeight,
                   document_contained: doc.scrollWidth <= innerWidth && doc.scrollHeight <= innerHeight,
                   stage_content_contained: contained, background: getComputedStyle(document.body).backgroundColor,
                   runtime_available: Boolean(window.AniDiagramRuntime), gsap_available: Boolean(window.gsap),
                   dependency_warning: warning && !warning.hidden ? warning.textContent : null,
                   reader_available: Boolean(window.AniDiagramReader) };
        });
        const name = `${viewport.width}x${viewport.height}-${colorScheme}.png`;
        await page.screenshot({ path: path.join(destination, name), animations: "disabled" });
        const ok = measured.document_contained && measured.stage_content_contained && !errors.length;
        checks.push({ viewport, color_scheme_preference: colorScheme, ...measured, errors, ok });
        captures.push({ path: name, viewport, color_scheme_preference: colorScheme });
        await page.close();
      }
    }
    console.log(JSON.stringify({ status: checks.every(check => check.ok) ? "passed" : "failed", checks, captures }));
  } catch (error) {
    console.log(JSON.stringify({ status: browser ? "failed" : "skipped", reason: error.message, checks, captures }));
  } finally {
    await browser?.close();
  }
}

#!/usr/bin/env node
// HTTP is intentional: same-origin iframe previews mirror GitHub Pages behavior.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const output = path.join(root, "outputs/gallery-motion");
fs.mkdirSync(output, {recursive: true});
const types = {".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".json": "application/json"};
const server = http.createServer((request, response) => {
  const file = path.resolve(root, "." + decodeURIComponent(new URL(request.url, "http://localhost").pathname));
  if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    response.writeHead(404); response.end(); return;
  }
  response.setHeader("Content-Type", types[path.extname(file)] || "application/octet-stream");
  fs.createReadStream(file).pipe(response);
});
await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const base = `http://127.0.0.1:${server.address().port}/gallery/`;
const browser = await chromium.launch({headless: true, ...(process.env.ANIDIAGRAM_BROWSER_CHANNEL ? {channel: process.env.ANIDIAGRAM_BROWSER_CHANNEL} : {})});
const report = {cases: [], surfaces: [], errors: [], checks: {}};
try {
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}, reducedMotion: "no-preference"});
  const page = await context.newPage();
  page.on("pageerror", error => report.errors.push(error.message));
  const manifest = JSON.parse(fs.readFileSync(path.join(root, "gallery/preview-manifest.json")));
  const seen = new Set();
  for (const surface of ["index.html", "styles/index.html", "layouts/index.html", "hero/index.html", "icon-systems/index.html", "character-themes.html", "runtime-motion.html"]) {
    await page.goto(base + surface);
    const cards = page.locator(".motion-preview");
    const count = await cards.count();
    assert(count > 0, `${surface}: no previews`);
    const first = cards.first();
    await first.scrollIntoViewIfNeeded();
    await page.waitForFunction(() => document.querySelector('.motion-preview[data-ready="true"]'));
    await page.locator("[data-preview-toggle]").click();
    assert.equal(await page.locator("iframe").count(), 0, `${surface}: pause leaked an iframe`);
    await page.locator("[data-preview-toggle]").click();
    for (let index = 0; index < count; index += 1) {
      const card = cards.nth(index);
      const target = await card.locator("a").getAttribute("data-preview-url");
      const relative = new URL(target, base + surface).pathname.slice(new URL(base).pathname.length);
      if (seen.has(relative)) continue;
      await card.scrollIntoViewIfNeeded();
      await page.waitForFunction(element => element.dataset.ready === "true", await card.elementHandle());
      const frame = await card.locator("iframe").elementHandle().then(handle => handle.contentFrame());
      const motion = await frame.evaluate(async () => {
        const manifest = JSON.parse(document.getElementById("anidiagram-motion-manifest").textContent);
        const icons = manifest.icons.filter(icon => icon.performance || icon.recipe);
        await new Promise(resolve => setTimeout(resolve, Math.max(0, ...icons.map(icon => Number(icon.delay) || 0)) * 1000));
        const parts = icons.map(icon => Object.values(icon.parts || {}).map(selector => document.querySelector(selector)).filter(Boolean));
        const states = parts.map(() => new Set());
        const timelines = window.__ANIDIAGRAM_TIMELINES__ || [];
        const start = timelines.map(timeline => timeline.totalTime());
        for (let sample = 0; sample < 8; sample += 1) {
          parts.forEach((elements, index) => states[index].add(elements.map(element => element.outerHTML).join("")));
          await new Promise(resolve => setTimeout(resolve, 300));
        }
        const svg = document.querySelector("#viewport > svg");
        const box = svg.getBoundingClientRect();
        return {
          nodes: document.querySelectorAll(".node").length, icons: icons.length,
          changedIcons: states.filter(values => values.size > 1).length,
          frozenIcons: icons.filter((_, index) => states[index].size < 2).map(icon => icon.node_id),
          running: timelines.filter((timeline, index) => timeline.totalTime() > start[index]).length,
          completedTitleEntry: icons.length === 0 && manifest.stage?.title_sweep === true
            && timelines.some(timeline => timeline.__anidiagramStage === "title-entry" && timeline.progress() === 1),
          iconTimelines: (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length,
          fits: box.x >= -1 && box.y >= -1 && box.right <= innerWidth + 1 && box.bottom <= innerHeight + 1,
        };
      });
      assert.equal(motion.changedIcons, motion.icons, `${relative}: frozen icon parts ${motion.frozenIcons}`);
      assert(motion.running > 0 || motion.completedTitleEntry, `${relative}: no playing timelines or completed title entry`);
      assert(motion.fits, `${relative}: diagram clipped by preview`);
      // Dense four-column grids can legitimately show more than eight cards.
      // Check viewport intersection, not an arbitrary cap on visible diagrams.
      const offscreen = await page.locator("iframe").evaluateAll(frames => frames.filter(frame => {
        const box = frame.getBoundingClientRect();
        return box.bottom < -1 || box.top > innerHeight + 1 || box.right < -1 || box.left > innerWidth + 1;
      }).map(frame => frame.src));
      assert.deepEqual(offscreen, [], `${surface}: off-screen runtimes were not released`);
      report.cases.push({html: relative, ...motion});
      seen.add(relative);
      console.log(`verified ${seen.size}/${manifest.previews.length}: ${relative} (${motion.changedIcons}/${motion.icons} icons)`);
    }
    for (const width of [1440, 390]) {
      await page.setViewportSize({width, height: 1000});
      await page.emulateMedia({reducedMotion: "reduce"});
      await page.waitForFunction(() => !document.querySelector("iframe"));
      assert(await page.locator("[data-preview-toggle]").isDisabled());
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${surface}: overflow at ${width}`);
      await page.screenshot({path: path.join(output, surface.replaceAll("/", "-") + `-${width}.png`)});
      await page.emulateMedia({reducedMotion: "no-preference"});
      await first.scrollIntoViewIfNeeded();
      await page.waitForFunction(element => element.dataset.ready === "true", await first.elementHandle());
      const resizedFrame = await first.locator("iframe").elementHandle().then(handle => handle.contentFrame());
      assert(await resizedFrame.evaluate(() => {
        const box = document.querySelector("#viewport > svg").getBoundingClientRect();
        return box.x >= -1 && box.y >= -1 && box.right <= innerWidth + 1 && box.bottom <= innerHeight + 1;
      }), `${surface}: live preview clipped at ${width}`);
    }
    await page.setViewportSize({width: 1440, height: 1000});
    await page.emulateMedia({reducedMotion: "no-preference"});
    report.surfaces.push({surface, count, pauseResume: true, reducedMotion: true, desktopMobile: true});
  }
  assert.equal(seen.size, manifest.previews.length);
  assert(manifest.previews.every(entry => seen.has(entry.html)));
  // Fail closed when runtime dependency loading fails; never hide the poster.
  const blocked = await context.newPage();
  await blocked.route("**/*gsap*", route => route.abort());
  await blocked.goto(base + "styles/index.html");
  await blocked.waitForSelector(".preview-status:not([hidden])");
  assert.equal(await blocked.locator('.motion-preview[data-ready="true"]').count(), 0);
  assert(await blocked.locator(".motion-preview img").first().isVisible());
  await blocked.close();
  const noJS = await browser.newContext({javaScriptEnabled: false, reducedMotion: "reduce"});
  const still = await noJS.newPage();
  await still.goto(base + "index.html");
  assert.equal(await still.locator("iframe").count(), 0);
  assert.equal(await still.locator("[data-preview-toggle]").isVisible(), false);
  const firstImage = still.locator(".motion-preview img").first();
  await firstImage.evaluate(image => image.decode());
  const a = await firstImage.screenshot();
  await still.waitForTimeout(500);
  const b = await firstImage.screenshot();
  assert(a.equals(b), "static fallback animates without JavaScript");
  report.checks = {dependencyFailureFallback: true, noJSFallback: true, unchangedStaticPixels: true};
  assert.deepEqual(report.errors, []);
  report.ok = true;
} catch (error) {
  report.ok = false;
  report.failure = error.stack;
  throw error;
} finally {
  fs.writeFileSync(path.join(output, "verification.json"), JSON.stringify(report, null, 2) + "\n");
  await browser.close();
  await new Promise(resolve => server.close(resolve));
}
console.log(JSON.stringify({ok: report.ok, cases: report.cases.length, icons: report.cases.reduce((sum, entry) => sum + entry.changedIcons, 0), surfaces: report.surfaces.length, checks: report.checks}));

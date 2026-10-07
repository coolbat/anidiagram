#!/usr/bin/env node
// Real viewport and animation checks; generated files remain under outputs/.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";

const root = path.resolve(import.meta.dirname, "..");
const out = path.resolve(process.argv[2] || path.join(root, "outputs/optimization-2026-10-07/viewer"));
fs.mkdirSync(out, { recursive: true });
const cases = [
  ["agent", ["--plan", "examples/agent-loop-internals.plan.json"]],
  ["rag", ["--plan", "examples/enterprise-rag-production-illustrated.plan.json"]],
  ["swimlane", ["--preset", "swimlane", "--style", "dark-luxury"]],
  ["reader", ["--plan", "examples/contracts/production-request-path.plan.json", "--reader"]],
  ["readable", ["--plan", "examples/contracts/production-request-path.plan.json", "--readable-labels"]],
  ["fallback", ["--preset", "agent-memory", "--runtime-dependency", "none"]],
  ["portable", ["--preset", "agent-memory", "--formats", "svg,viewer,quality"]],
];
for (const [name, args] of cases) {
  execFileSync("python3", ["scripts/run_anidiagram.py", "--outdir", out, "--basename", name,
    "--formats", "svg,html,quality", "--runtime-dependency", "inline",
    "--runtime-source", "node_modules/gsap/dist/gsap.min.js", ...args], { cwd: root, stdio: "pipe" });
}
const browser = await chromium.launch({ headless: true });
const results = [];
try {
  for (const size of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    for (const [name] of cases) {
      const page = await browser.newPage({ viewport: size });
      const errors = [];
      page.on("pageerror", error => errors.push(error.message));
      await page.goto(pathToFileURL(path.join(out, name + (name === "portable" ? ".viewer.html" : ".html"))).href);
      await page.waitForTimeout(80);
      const bounds = () => page.evaluate(() => {
        const stage = document.getElementById("stage"), svg = stage.querySelector("svg");
        const s = stage.getBoundingClientRect(), r = svg.getBoundingClientRect();
        return { stage: { x: s.x, y: s.y, w: s.width, h: s.height }, svg: { x: r.x, y: r.y, w: r.width, h: r.height },
          nativeScroll: stage.dataset.readableScroll === "true", bodyWidth: document.body.scrollWidth,
          viewportWidth: innerWidth, viewportHeight: innerHeight };
      });
      const checkFit = value => {
        if (value.nativeScroll) {
          assert.equal(name, "readable");
          return; // Explicit readable-label mode retains native-size scrolling.
        }
        assert.notEqual(name, "readable", "readable-labels lost its explicit native-size mode");
        const { stage: s, svg: r } = value;
        assert(r.x >= s.x - 1 && r.y >= s.y - 1 && r.x + r.w <= s.x + s.w + 1 && r.y + r.h <= s.y + s.h + 1,
          `${name} clipped at ${size.width}: ${JSON.stringify(value)}`);
        assert(Math.abs((r.x + r.w / 2) - (s.x + s.w / 2)) < 2, `${name} not horizontally centered`);
        assert(Math.abs((r.y + r.h / 2) - (s.y + s.h / 2)) < 2, `${name} not vertically centered`);
        assert(s.y + s.h <= value.viewportHeight + 1, `${name} stage exceeds viewport`);
        assert(value.bodyWidth <= value.viewportWidth + 1, `${name} horizontal page overflow`);
      };
      checkFit(await bounds());
      await page.locator("#zoom-in").click();
      await page.locator("#stage").focus();
      await page.keyboard.press("ArrowRight");
      await page.locator("#reset").click();
      checkFit(await bounds());
      await page.setViewportSize({ width: size.width + 90, height: size.height - 70 });
      await page.waitForTimeout(80);
      checkFit(await bounds());
      if (name === "agent") {
        await page.waitForTimeout(1250);
        await page.locator("#toggle").click();
        await page.locator("#toggle").click();
        assert.equal(await page.evaluate(() => Array.from(document.querySelectorAll("g.node, g.group, g.edge"))
          .filter(el => Number(getComputedStyle(el).opacity) < 0.99).length), 0, "resume replayed a finished entrance");
        await page.locator("#restart").click();
        const entrance = await page.evaluate(() => {
          window.AniDiagramEntrance.pause();
          const nodes = Array.from(document.querySelectorAll("g.node"));
          const edges = Array.from(document.querySelectorAll("g.edge"));
          const animations = [...document.querySelectorAll("g.node, g.group, g.edge, .edge-draw")].flatMap(el => el.getAnimations());
          const violations = [];
          for (let time = 0; time <= 1200; time += 40) {
            animations.forEach(animation => { animation.currentTime = time; });
            for (const edge of edges) {
              if (Number(getComputedStyle(edge).opacity) < 0.01) continue;
              for (const id of [edge.dataset.source, edge.dataset.target]) {
                const node = document.getElementById("node-" + id);
                if (!node || Number(getComputedStyle(node).opacity) < 0.99) violations.push({ time, id });
              }
            }
          }
          const total = Math.max(...animations.map(animation => animation.effect.getComputedTiming().endTime));
          window.AniDiagramEntrance.clear();
          return { violations, total, nodes: nodes.length, animations: animations.length };
        });
        assert(entrance.animations > entrance.nodes && entrance.total <= 1200, JSON.stringify(entrance));
        assert.deepEqual(entrance.violations, [], "edge appeared before its endpoints");
        await page.waitForTimeout(1250);
        const state = await page.evaluate(() => ({
          hidden: Array.from(document.querySelectorAll("g.node, g.group, g.edge")).filter(el => Number(getComputedStyle(el).opacity) < 0.99).length,
          artifacts: document.querySelectorAll(".runtime-group-field").length,
        }));
        assert.equal(state.hidden, 0, "entrance must finish within 1.2 seconds");
        assert.equal(state.artifacts, 0, "blurred group fields remain");
      }
      assert.deepEqual(errors, [], `${name} page errors`);
      await page.setViewportSize(size);
      await page.waitForTimeout(1250);
      await page.screenshot({ path: path.join(out, `${name}-${size.width}.png`) });
      results.push({ name, size, ok: true });
      await page.close();
    }
  }
  const reduced = await browser.newPage({ reducedMotion: "reduce" });
  await reduced.goto(pathToFileURL(path.join(out, "agent.html")).href);
  assert.equal(await reduced.evaluate(() => document.querySelectorAll("g.node, g.group, g.edge").length > 0 &&
    Array.from(document.querySelectorAll("g.node, g.group, g.edge")).every(el => Number(getComputedStyle(el).opacity) === 1)), true);
  assert.equal(await reduced.evaluate(() => (window.__ANIDIAGRAM_TIMELINES__ || []).length), 0);
  await reduced.close();
} finally {
  await browser.close();
  fs.writeFileSync(path.join(out, "browser-results.json"), JSON.stringify(results, null, 2) + "\n");
}
console.log(`Verified ${results.length} viewport/reset/resize cases.`);

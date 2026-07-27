#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";


function assert(condition, message) {
  if (!condition) throw new Error(message);
}


async function main() {
  const outdir = process.argv[2] ? path.resolve(process.argv[2]) : null;
  if (!outdir || !fs.existsSync(path.join(outdir, "manifest.json"))) {
    throw new Error("usage: verify_readme_showcase_round_1.mjs <output-directory>");
  }

  const manifest = JSON.parse(fs.readFileSync(path.join(outdir, "manifest.json"), "utf8"));
  const report = {
    cases: manifest.cases.length,
    nodes: 0,
    edges: 0,
    active_runtime_edges: 0,
    console_errors: [],
    overflow: [],
  };
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    let currentCase = "review-page";
    page.on("console", (message) => {
      if (message.type() === "error") report.console_errors.push(`${currentCase}: ${message.text()}`);
    });
    page.on("pageerror", (error) => report.console_errors.push(`${currentCase}: ${error.message}`));

    const reviewPath = path.join(outdir, "readme-showcase-round-1.html");
    const reviewResponse = await page.goto(pathToFileURL(reviewPath).href, { waitUntil: "load" });
    assert(reviewResponse === null || reviewResponse.ok(), "review page failed to load");
    await page.waitForFunction(() => Array.from(document.images).every((image) => image.complete));
    const review = await page.evaluate(() => ({
      articles: document.querySelectorAll("article").length,
      images: Array.from(document.images).map((image) => [image.naturalWidth, image.naturalHeight]),
      pageOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      cardOverflow: Array.from(document.querySelectorAll("article"))
        .filter((article) => article.scrollWidth > article.clientWidth)
        .map((article) => article.dataset.case),
    }));
    assert(review.articles === manifest.cases.length, `review articles: ${review.articles}/${manifest.cases.length}`);
    assert(review.images.length === manifest.cases.length, `review images: ${review.images.length}/${manifest.cases.length}`);
    review.images.forEach(([width, height], index) => {
      const expected = manifest.cases[index].canvas;
      if (width !== expected.width || height !== expected.height) {
        report.overflow.push(
          `review image ${index + 1}: ${width}x${height}, expected ${expected.width}x${expected.height}`
        );
      }
    });
    if (review.pageOverflow) report.overflow.push("review page: horizontal overflow");
    review.cardOverflow.forEach((caseId) => report.overflow.push(`${caseId}: card overflow`));

    for (const entry of manifest.cases) {
      currentCase = entry.id;
      await page.goto(pathToFileURL(path.join(outdir, `${entry.id}.html`)).href, { waitUntil: "load" });
      await page.waitForFunction(() => (
        Boolean(window.AniDiagramRuntime)
        && Array.isArray(window.__ANIDIAGRAM_TIMELINES__)
        && document.querySelector("svg")
      ));
      await page.waitForTimeout(120);
      const state = await page.evaluate(() => {
        const svg = document.querySelector("svg");
        const svgRect = svg.getBoundingClientRect();
        const outside = Array.from(document.querySelectorAll("g.node")).flatMap((node) => {
          const rect = node.getBoundingClientRect();
          const inside = rect.width > 0 && rect.height > 0
            && rect.left >= svgRect.left - 1
            && rect.top >= svgRect.top - 1
            && rect.right <= svgRect.right + 1
            && rect.bottom <= svgRect.bottom + 1;
          return inside ? [] : [node.id || node.dataset.nodeId || "unknown-node"];
        });
        const motion = JSON.parse(document.getElementById("anidiagram-motion-manifest").textContent);
        const activeEdges = (window.__ANIDIAGRAM_STAGE_TIMELINES__ || [])
          .filter((timeline) => timeline.__anidiagramStage === "edge-motion").length;
        return {
          width: Number(svg.getAttribute("width")),
          height: Number(svg.getAttribute("height")),
          iconSystem: svg.dataset.iconSystem,
          motionProfile: svg.dataset.motionProfile,
          nodes: document.querySelectorAll("g.node").length,
          edges: document.querySelectorAll("g.edge").length,
          icons: motion.icons.length,
          motionEdges: motion.edges.length,
          activeEdges,
          outside,
          pageOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
        };
      });
      assert(
        state.width === entry.canvas.width && state.height === entry.canvas.height,
        `${entry.id}: SVG is ${state.width}x${state.height}, expected ${entry.canvas.width}x${entry.canvas.height}`
      );
      assert(state.motionProfile === "showcase-v1", `${entry.id}: motion profile is ${state.motionProfile}`);
      assert(state.nodes === state.icons, `${entry.id}: nodes/icons ${state.nodes}/${state.icons}`);
      assert(state.edges === state.motionEdges, `${entry.id}: edges/manifest ${state.edges}/${state.motionEdges}`);
      assert(state.activeEdges === state.edges, `${entry.id}: active edges ${state.activeEdges}/${state.edges}`);
      report.nodes += state.nodes;
      report.edges += state.edges;
      report.active_runtime_edges += state.activeEdges;
      state.outside.forEach((nodeId) => report.overflow.push(`${entry.id}: ${nodeId} outside SVG`));
      if (state.pageOverflow) report.overflow.push(`${entry.id}: horizontal overflow`);
    }
  } finally {
    await browser.close();
  }

  assert(report.console_errors.length === 0, `console errors:\n${report.console_errors.join("\n")}`);
  assert(report.overflow.length === 0, `overflow:\n${report.overflow.join("\n")}`);
  process.stdout.write(`${JSON.stringify(report)}\n`);
}


main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});

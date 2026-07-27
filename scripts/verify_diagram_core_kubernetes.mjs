#!/usr/bin/env node
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

import { chromium } from "playwright";


const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const argument = (name) => {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : null;
};
const EXPECTED_STYLE = argument("--style") || "diagram-core-light";
const STYLE_EXPECTATIONS = Object.freeze({
  "diagram-core-light": Object.freeze({ filename: "kubernetes-production.html", canvasFill: "#fffdf8", colorScheme: "light" }),
  "deep-tech": Object.freeze({ filename: "kubernetes-production-deep-tech.html", canvasFill: "#050816", colorScheme: "dark" }),
});
if (!STYLE_EXPECTATIONS[EXPECTED_STYLE]) {
  throw new Error(`Unsupported Kubernetes template style: ${EXPECTED_STYLE}`);
}
const pageArgument = argument("--page");
const PAGE_PATH = pageArgument
  ? path.resolve(pageArgument)
  : path.join(ROOT, "gallery", "diagram-core", STYLE_EXPECTATIONS[EXPECTED_STYLE].filename);
const screenshotSuffix = EXPECTED_STYLE === "deep-tech" ? "-deep-tech" : "";
const SCREENSHOT_PATH = path.join(ROOT, "build", `diagram-core-kubernetes-production${screenshotSuffix}.png`);
const TIMEOUT_MS = 12_000;
const EXPECTED = Object.freeze({ nodes: 19, icons: 19, expressiveEdges: 22, readableEdges: 2 });


function fail(message) {
  throw new Error(`Diagram Core Kubernetes verification failed: ${message}`);
}


async function openPage(browser, { reducedMotion = "no-preference", query = "" } = {}) {
  const context = await browser.newContext({
    viewport: { width: 1600, height: 1080 },
    reducedMotion,
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  page.setDefaultTimeout(TIMEOUT_MS);
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  const url = pathToFileURL(PAGE_PATH);
  url.search = query;
  await page.goto(url.href, { waitUntil: "load" });
  await page.waitForFunction(() => Boolean(window.AniDiagramRuntime));
  return { context, page, errors };
}


async function structuralReport(page) {
  return page.evaluate(() => {
    const svg = document.querySelector("#viewport svg");
    const nodes = [...document.querySelectorAll("[data-architecture-node]")];
    const nodeBoxes = nodes.map((node) => {
      const box = node.getBBox();
      return { id: node.dataset.architectureNode, x: box.x, y: box.y, width: box.width, height: box.height };
    });
    const overlaps = [];
    for (let left = 0; left < nodeBoxes.length; left += 1) {
      for (let right = left + 1; right < nodeBoxes.length; right += 1) {
        const a = nodeBoxes[left];
        const b = nodeBoxes[right];
        const overlapX = Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x);
        const overlapY = Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y);
        if (overlapX > 0.5 && overlapY > 0.5) overlaps.push(`${a.id}:${b.id}`);
      }
    }
    const ids = [...document.querySelectorAll("[id]")].map((element) => element.id);
    const duplicateIds = ids.filter((id, index) => ids.indexOf(id) !== index);
    const manifest = JSON.parse(document.getElementById("anidiagram-motion-manifest").textContent);
    return {
      nodes: nodes.length,
      iconSources: document.querySelectorAll('[data-icon-source="diagram-core-v1"]').length,
      releases: document.querySelectorAll('[data-diagram-core-release="1.0.0"]').length,
      presentations: document.querySelectorAll('[data-icon-presentation="showcase"]').length,
      edges: document.querySelectorAll("g.edge > path.edge-base").length,
      edgeLabels: document.querySelectorAll("g.edge .edge-label").length,
      nodeDomains: [...new Set(nodes.map((node) => node.dataset.nodeDomain))].sort(),
      edgeDomains: [...new Set([...document.querySelectorAll("g.edge")].map((edge) => edge.dataset.edgeDomain))].sort(),
      nodeStrokeColors: [...new Set(nodes.map((node) => node.querySelector(":scope > rect")?.getAttribute("stroke")))].sort(),
      edgeStrokeColors: [...new Set([...document.querySelectorAll("g.edge > path.edge-base")].map((edge) => edge.getAttribute("stroke")))].sort(),
      groups: document.querySelectorAll("g.group").length,
      overlaps,
      duplicateIds: [...new Set(duplicateIds)],
      outside: nodeBoxes.filter((box) => box.x < 0 || box.y < 0 || box.x + box.width > 1600 || box.y + box.height > 900),
      iconSystem: svg.dataset.iconSystem,
      release: svg.dataset.diagramCoreRelease,
      templateStyle: svg.dataset.templateStyle,
      viewerTemplateStyle: document.getElementById("viewer").dataset.templateStyle,
      canvasFill: svg.querySelector(":scope > rect")?.getAttribute("fill"),
      colorScheme: document.querySelector('meta[name="color-scheme"]')?.content,
      diagramTitle: document.getElementById("diagram-title")?.textContent,
      diagramSummary: document.getElementById("diagram-summary")?.textContent,
      manifest,
    };
  });
}


function assertStructure(report) {
  if (report.nodes !== EXPECTED.nodes) fail(`expected ${EXPECTED.nodes} nodes, got ${report.nodes}`);
  if (report.iconSources !== EXPECTED.nodes || report.presentations !== EXPECTED.nodes) {
    fail(`expected ${EXPECTED.nodes} Diagram Core instances, got sources=${report.iconSources} presentations=${report.presentations}`);
  }
  if (report.releases !== EXPECTED.nodes + 1) fail(`release binding count is ${report.releases}, expected ${EXPECTED.nodes + 1}`);
  if (report.edges < 18 || report.groups !== 5) fail(`unexpected architecture density: edges=${report.edges} groups=${report.groups}`);
  if (report.edgeLabels !== 2) fail(`expected two narrative edge labels, got ${report.edgeLabels}`);
  if (report.overlaps.length) fail(`architecture nodes overlap: ${report.overlaps.join(",")}`);
  if (report.outside.length) fail(`architecture nodes leave the viewBox: ${report.outside.map((entry) => entry.id).join(",")}`);
  if (report.duplicateIds.length) fail(`duplicate SVG/DOM ids: ${report.duplicateIds.join(",")}`);
  if (report.iconSystem !== "diagram-core-v1" || report.release !== "1.0.0") fail("SVG release binding is missing");
  if (report.templateStyle !== EXPECTED_STYLE || report.viewerTemplateStyle !== EXPECTED_STYLE) {
    fail(`${EXPECTED_STYLE} template binding is missing`);
  }
  const styleExpectation = STYLE_EXPECTATIONS[EXPECTED_STYLE];
  if (report.canvasFill !== styleExpectation.canvasFill) fail(`unexpected canvas fill: ${report.canvasFill}`);
  if (report.colorScheme !== styleExpectation.colorScheme) fail(`unexpected color scheme: ${report.colorScheme}`);
  if (EXPECTED_STYLE === "deep-tech") {
    const expectedDomains = ["control-plane", "delivery", "observability", "workload-plane"];
    const expectedColors = ["#34d399", "#60a5fa", "#a78bfa", "#fb7185"];
    if (JSON.stringify(report.nodeDomains) !== JSON.stringify(expectedDomains)) {
      fail(`unexpected node color domains: ${report.nodeDomains.join(",")}`);
    }
    if (JSON.stringify(report.edgeDomains) !== JSON.stringify(expectedDomains)) {
      fail(`unexpected edge color domains: ${report.edgeDomains.join(",")}`);
    }
    if (JSON.stringify(report.nodeStrokeColors) !== JSON.stringify(expectedColors)) {
      fail(`unexpected node color palette: ${report.nodeStrokeColors.join(",")}`);
    }
    if (JSON.stringify(report.edgeStrokeColors) !== JSON.stringify(expectedColors)) {
      fail(`unexpected edge color palette: ${report.edgeStrokeColors.join(",")}`);
    }
  }
  if (report.diagramTitle !== "Kubernetes Production Architecture") fail(`unexpected diagram title: ${report.diagramTitle}`);
  if (report.diagramSummary !== "All nodes alive · all data paths flowing") fail(`unexpected diagram summary: ${report.diagramSummary}`);
  if (report.manifest.icon_system !== "diagram-core-v1" || report.manifest.diagram_core_release !== "1.0.0") {
    fail("motion manifest release binding is missing");
  }
  if (report.manifest.style !== EXPECTED_STYLE) fail(`unexpected manifest style: ${report.manifest.style}`);
  if (report.manifest.icons.length !== EXPECTED.icons) fail(`manifest animates ${report.manifest.icons.length} nodes`);
}


async function timelineReport(page) {
  return page.evaluate(() => ({
    icon: (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length,
    edge: (window.__ANIDIAGRAM_STAGE_TIMELINES__ || []).filter((timeline) => timeline.__anidiagramStage === "edge-packet").length,
    title: (window.__ANIDIAGRAM_STAGE_TIMELINES__ || []).filter((timeline) => timeline.__anidiagramStage === "title-entry").length,
    total: (window.__ANIDIAGRAM_TIMELINES__ || []).length,
  }));
}


async function waitForMode(page, iconCount, edgeCount) {
  await page.waitForFunction(
    ({ iconCount, edgeCount }) => {
      const icons = (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length;
      const edges = (window.__ANIDIAGRAM_STAGE_TIMELINES__ || []).filter((timeline) => timeline.__anidiagramStage === "edge-packet").length;
      return icons === iconCount && edges === edgeCount;
    },
    { iconCount, edgeCount },
  );
}


async function verifyMotionModes(page) {
  await waitForMode(page, EXPECTED.icons, EXPECTED.expressiveEdges);
  const expressive = await timelineReport(page);
  if (expressive.title !== 1) fail(`expected one title entry timeline, got ${expressive.title}`);

  await page.click("#motion-readable");
  await waitForMode(page, EXPECTED.icons, EXPECTED.readableEdges);
  const readable = await timelineReport(page);

  await page.click("#motion-off");
  await waitForMode(page, 0, 0);
  const off = await timelineReport(page);
  if (off.total !== 0) fail(`Off mode kept ${off.total} timelines alive`);

  await page.click("#motion-expressive");
  await waitForMode(page, EXPECTED.icons, EXPECTED.expressiveEdges);
  const restored = await timelineReport(page);
  return { expressive, readable, off, restored };
}


async function verifyIconContainment(page) {
  const clipped = await page.evaluate(() => {
    const timelines = window.__ANIDIAGRAM_ICON_TIMELINES__ || [];
    const manifest = JSON.parse(document.getElementById("anidiagram-motion-manifest").textContent);
    const failures = new Set();
    timelines.forEach((timeline, index) => {
      timeline.pause();
      const node = document.querySelector(`[data-architecture-node="${manifest.icons[index].node_id}"]`);
      const card = node.querySelector("rect").getBoundingClientRect();
      const root = node.querySelector('[data-icon-source="diagram-core-v1"]');
      for (let sample = 0; sample <= 40; sample += 1) {
        timeline.seek(timeline.duration() * sample / 40, false);
        const box = root.getBoundingClientRect();
        if (box.left < card.left - 1 || box.right > card.right + 1 || box.top < card.top - 1 || box.bottom > card.bottom + 1) {
          failures.add(manifest.icons[index].node_id);
        }
      }
      timeline.restart();
    });
    return [...failures];
  });
  if (clipped.length) fail(`animated icons clip their cards: ${clipped.join(",")}`);
}


async function framePerformance(page) {
  return page.evaluate(() => new Promise((resolve) => {
    const frames = [];
    let previous = performance.now();
    function sample(now) {
      frames.push(now - previous);
      previous = now;
      if (frames.length >= 150) {
        const sorted = frames.slice(10).sort((a, b) => a - b);
        const p95 = sorted[Math.max(0, Math.ceil(sorted.length * 0.95) - 1)] || 0;
        resolve({ p95, frames: sorted.length });
        return;
      }
      requestAnimationFrame(sample);
    }
    requestAnimationFrame(sample);
  }));
}


async function verifyStaticFallback(browser, options, expectedClass = null) {
  const opened = await openPage(browser, options);
  try {
    await opened.page.waitForTimeout(150);
    const report = await timelineReport(opened.page);
    if (report.total !== 0) fail(`static fallback kept ${report.total} timelines alive`);
    if (expectedClass) {
      const present = await opened.page.evaluate((name) => document.documentElement.classList.contains(name), expectedClass);
      if (!present) fail(`static fallback is missing ${expectedClass} marker`);
    }
    if (opened.errors.length) fail(`static fallback emitted browser errors: ${opened.errors.join(" | ")}`);
    return report;
  } finally {
    await opened.context.close();
  }
}


async function main() {
  const browser = await chromium.launch({ headless: true });
  try {
    const opened = await openPage(browser);
    let structure;
    let modes;
    let performance;
    try {
      structure = await structuralReport(opened.page);
      assertStructure(structure);
      modes = await verifyMotionModes(opened.page);
      await verifyIconContainment(opened.page);
      performance = await framePerformance(opened.page);
      if (performance.p95 > 33.3) fail(`p95 frame time ${performance.p95.toFixed(2)} ms exceeds 33.3 ms`);
      await opened.page.locator("#stage").screenshot({ path: SCREENSHOT_PATH });
      if (opened.errors.length) fail(`browser emitted errors: ${opened.errors.join(" | ")}`);
    } finally {
      await opened.context.close();
    }
    await verifyStaticFallback(browser, { query: "?no-gsap=1" }, "no-gsap");
    await verifyStaticFallback(browser, { reducedMotion: "reduce" });
    process.stdout.write(
      `style=${EXPECTED_STYLE} nodes=${structure.nodes} icons=${modes.expressive.icon} expressive_edges=${modes.expressive.edge} readable_edges=${modes.readable.edge} off=${modes.off.total} reduced=0 no_gsap=0 p95=${performance.p95.toFixed(2)}ms screenshot=${SCREENSHOT_PATH}\nOK\n`,
    );
  } finally {
    await browser.close();
  }
}


main().catch((error) => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 1;
});

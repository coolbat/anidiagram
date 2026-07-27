#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { chromium } from "playwright";


function assert(condition, message) {
  if (!condition) throw new Error(message);
}


async function main() {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  const manifestPath = process.argv[2]
    ? path.resolve(process.argv[2])
    : path.join(root, "gallery", "showcase_manifest.json");
  if (!fs.existsSync(manifestPath)) {
    throw new Error("usage: verify_public_showcase.mjs [showcase-manifest.json]");
  }

  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  const entries = [manifest.hero, ...manifest.styles, ...manifest.layouts];
  const report = {
    cases: entries.length,
    nodes: 0,
    edges: 0,
    active_runtime_edges: 0,
    automatic_icon_performances: 0,
    console_errors: [],
    overflow: [],
  };

  assert(entries.length === 29, `public Showcase cases: ${entries.length}/29`);
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
    let currentCase = "gallery";
    page.on("console", (message) => {
      if (message.type() === "error") report.console_errors.push(`${currentCase}: ${message.text()}`);
    });
    page.on("pageerror", (error) => report.console_errors.push(`${currentCase}: ${error.message}`));

    for (const entry of entries) {
      currentCase = entry.id || entry.style || entry.preset;
      const htmlPath = path.join(root, entry.html);
      const response = await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
      assert(response === null || response.ok(), `${currentCase}: page failed to load`);
      await page.waitForFunction(() => (
        Boolean(window.AniDiagramRuntime)
        && Array.isArray(window.__ANIDIAGRAM_TIMELINES__)
        && document.querySelector("svg")
      ));
      await page.waitForTimeout(140);

      const state = await page.evaluate(() => {
        const svg = document.querySelector("svg");
        const viewBox = svg.viewBox.baseVal;
        const outside = Array.from(document.querySelectorAll("g.node")).flatMap((node) => {
          const box = node.getBBox();
          const inside = box.width > 0 && box.height > 0
            && box.x >= viewBox.x - 1
            && box.y >= viewBox.y - 1
            && box.x + box.width <= viewBox.x + viewBox.width + 1
            && box.y + box.height <= viewBox.y + viewBox.height + 1;
          return inside ? [] : [node.id || node.dataset.nodeId || "unknown-node"];
        });
        const motion = JSON.parse(document.getElementById("anidiagram-motion-manifest").textContent);
        const activeEdges = (window.__ANIDIAGRAM_STAGE_TIMELINES__ || [])
          .filter((timeline) => timeline.__anidiagramStage === "edge-motion").length;
        return {
          iconSystem: svg.dataset.iconSystem,
          iconSystemVersion: svg.dataset.iconSystemVersion,
          motionProfile: svg.dataset.motionProfile,
          manifestIconSystem: motion.icon_system,
          manifestIconSystemVersion: motion.icon_system_version,
          nodes: document.querySelectorAll("g.node").length,
          edges: document.querySelectorAll("g.edge").length,
          icons: motion.icons.length,
          automaticPerformances: motion.icons.filter((icon) => Boolean(icon.performance)).length,
          motionEdges: motion.edges.length,
          activeEdges,
          outside,
          pageOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
        };
      });

      assert(state.iconSystem === "illustrated", `${currentCase}: SVG icon system is ${state.iconSystem}`);
      assert(state.iconSystemVersion === "2.5.0", `${currentCase}: SVG icon version is ${state.iconSystemVersion}`);
      assert(state.manifestIconSystem === "illustrated", `${currentCase}: manifest icon system is ${state.manifestIconSystem}`);
      assert(state.manifestIconSystemVersion === "2.5.0", `${currentCase}: manifest icon version is ${state.manifestIconSystemVersion}`);
      assert(state.motionProfile === "showcase-v1", `${currentCase}: motion profile is ${state.motionProfile}`);
      assert(state.nodes === state.icons, `${currentCase}: nodes/icons ${state.nodes}/${state.icons}`);
      assert(state.nodes === state.automaticPerformances, `${currentCase}: automatic performances ${state.automaticPerformances}/${state.nodes}`);
      assert(state.edges === state.motionEdges, `${currentCase}: edges/manifest ${state.edges}/${state.motionEdges}`);
      assert(state.activeEdges === state.edges, `${currentCase}: active edges ${state.activeEdges}/${state.edges}`);

      report.nodes += state.nodes;
      report.edges += state.edges;
      report.active_runtime_edges += state.activeEdges;
      report.automatic_icon_performances += state.automaticPerformances;
      state.outside.forEach((nodeId) => report.overflow.push(`${currentCase}: ${nodeId} outside SVG`));
      if (state.pageOverflow) report.overflow.push(`${currentCase}: horizontal overflow`);
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

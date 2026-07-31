#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";


function assert(condition, message) {
  if (!condition) throw new Error(message);
}


async function main() {
  const htmlPath = process.argv[2] ? path.resolve(process.argv[2]) : null;
  if (!htmlPath || !fs.existsSync(htmlPath)) {
    throw new Error("usage: verify_chinese_architecture.mjs <diagram.html>");
  }

  const errors = [];
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } });
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
    await page.waitForFunction(() => Boolean(window.AniDiagramRuntime) && document.querySelector("svg"));
    await page.waitForTimeout(160);

    const report = await page.evaluate(() => {
      const svg = document.querySelector("svg");
      const cjk = /[\u3400-\u9fff]/;
      const textOverflow = Array.from(document.querySelectorAll("g.node")).flatMap((node) => {
        const surface = node.querySelector(".node-surface");
        const text = node.querySelector(".node-text-block");
        if (!surface || !text) return [node.id || "unknown-node"];
        const outer = surface.getBBox();
        const inner = text.getBBox();
        const inside = inner.x >= outer.x - 1
          && inner.y >= outer.y - 1
          && inner.x + inner.width <= outer.x + outer.width + 1
          && inner.y + inner.height <= outer.y + outer.height + 1;
        return inside ? [] : [node.id || "unknown-node"];
      });
      const chineseText = Array.from(svg.querySelectorAll("text"))
        .filter((element) => cjk.test(element.textContent || ""));
      const emptyGlyphBoxes = chineseText
        .filter((element) => element.getBBox().width <= 0 || element.getBBox().height <= 0)
        .map((element) => (element.textContent || "").trim());
      const edgeLabels = Array.from(svg.querySelectorAll(".edge-label"))
        .filter((element) => (element.textContent || "").trim())
        .map((element) => ({text: (element.textContent || "").trim(), box: element.getBBox()}));
      const labelCollisions = [];
      for (let left = 0; left < edgeLabels.length; left += 1) {
        for (let right = left + 1; right < edgeLabels.length; right += 1) {
          const a = edgeLabels[left];
          const b = edgeLabels[right];
          const overlaps = a.box.x < b.box.x + b.box.width + 2
            && a.box.x + a.box.width + 2 > b.box.x
            && a.box.y < b.box.y + b.box.height + 2
            && a.box.y + a.box.height + 2 > b.box.y;
          if (overlaps) labelCollisions.push(`${a.text} / ${b.text}`);
        }
      }
      const manifest = JSON.parse(document.getElementById("anidiagram-motion-manifest").textContent || "{}");
      const nodeSurfaces = new Map(
        Array.from(svg.querySelectorAll("g.node")).map((node) => [
          node.id.replace(/^node-/, ""),
          node.querySelector(".node-surface")?.getBBox(),
        ])
      );
      const sampledPaths = Array.from(svg.querySelectorAll("g.edge")).map((group, index) => {
        const path = group.querySelector(".edge-base");
        const length = path?.getTotalLength() || 0;
        const points = [];
        for (let distance = 0; distance <= length; distance += 3) {
          const point = path.getPointAtLength(Math.min(distance, length));
          points.push({x: point.x, y: point.y});
        }
        return {entry: manifest.edges?.[index] || {}, points};
      });
      const edgeNodeCrossings = sampledPaths.flatMap(({entry, points}, index) => {
        const excluded = new Set([entry.source, entry.target]);
        return Array.from(nodeSurfaces.entries()).flatMap(([nodeId, box]) => {
          if (!box || excluded.has(nodeId)) return [];
          const crosses = points.some((point) => (
            point.x > box.x + 2 && point.x < box.x + box.width - 2
            && point.y > box.y + 2 && point.y < box.y + box.height - 2
          ));
          return crosses ? [`edge-${index + 1} / ${nodeId}`] : [];
        });
      });
      const sharedEdgeRuns = [];
      for (let left = 0; left < sampledPaths.length; left += 1) {
        const leftKeys = new Set(sampledPaths[left].points.map((point) => `${Math.round(point.x / 3)},${Math.round(point.y / 3)}`));
        for (let right = left + 1; right < sampledPaths.length; right += 1) {
          const shared = sampledPaths[right].points.reduce(
            (count, point) => count + (leftKeys.has(`${Math.round(point.x / 3)},${Math.round(point.y / 3)}`) ? 1 : 0),
            0,
          );
          if (shared >= 5) sharedEdgeRuns.push(`edge-${left + 1} / edge-${right + 1}: ${shared}`);
        }
      }
      const sample = svg.querySelector(".node-title") || svg.querySelector(".title");
      const groupBoxes = Array.from(svg.querySelectorAll("g.group"))
        .map((group) => group.getBBox());
      const groupLeft = Math.min(...groupBoxes.map((box) => box.x));
      const groupRight = Math.max(...groupBoxes.map((box) => box.x + box.width));
      const canvasWidth = svg.viewBox.baseVal.width;
      return {
        htmlLocale: document.documentElement.lang,
        svgLocale: svg.getAttribute("lang"),
        dataLocale: svg.dataset.locale,
        fontFamily: sample ? getComputedStyle(sample).fontFamily : "",
        title: svg.querySelector("#diagram-title")?.textContent || "",
        nodes: svg.querySelectorAll("g.node").length,
        edges: svg.querySelectorAll("g.edge").length,
        groups: svg.querySelectorAll("g.group").length,
        chineseTextElements: chineseText.length,
        textOverflow,
        emptyGlyphBoxes,
        labelCollisions,
        edgeNodeCrossings,
        sharedEdgeRuns,
        horizontalMargins: {
          left: groupLeft,
          right: canvasWidth - groupRight,
        },
        pageOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      };
    });

    assert(errors.length === 0, `console errors: ${errors.join("; ")}`);
    assert(report.htmlLocale === "zh-CN", `HTML locale is ${report.htmlLocale}`);
    assert(report.svgLocale === "zh-CN", `SVG locale is ${report.svgLocale}`);
    assert(report.dataLocale === "zh-CN", `SVG data locale is ${report.dataLocale}`);
    assert(report.title === "企业级智能体平台架构", `unexpected title: ${report.title}`);
    assert(report.nodes === 8, `nodes: ${report.nodes}/8`);
    assert(report.edges === 11, `edges: ${report.edges}/11`);
    assert(report.groups === 3, `groups: ${report.groups}/3`);
    assert(report.chineseTextElements >= 20, `Chinese text elements: ${report.chineseTextElements}`);
    assert(/Noto Sans CJK SC|Noto Sans SC|Source Han Sans SC|PingFang SC/.test(report.fontFamily), `CJK font stack missing: ${report.fontFamily}`);
    assert(report.textOverflow.length === 0, `text overflow: ${report.textOverflow.join(", ")}`);
    assert(report.emptyGlyphBoxes.length === 0, `empty glyph boxes: ${report.emptyGlyphBoxes.join(", ")}`);
    assert(report.labelCollisions.length === 0, `edge label collisions: ${report.labelCollisions.join(", ")}`);
    assert(report.edgeNodeCrossings.length === 0, `edges cross unrelated nodes: ${report.edgeNodeCrossings.join(", ")}`);
    assert(report.sharedEdgeRuns.length === 0, `shared edge runs: ${report.sharedEdgeRuns.join(", ")}`);
    assert(
      Math.abs(report.horizontalMargins.left - report.horizontalMargins.right) <= 1,
      `diagram is not horizontally centered: ${JSON.stringify(report.horizontalMargins)}`,
    );
    assert(!report.pageOverflow, "horizontal page overflow");

    process.stdout.write(`${JSON.stringify({...report, consoleErrors: errors})}\n`);
  } finally {
    await browser.close();
  }
}


main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});

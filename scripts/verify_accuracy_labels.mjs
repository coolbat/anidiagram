#!/usr/bin/env node

// Independent browser oracle: measure rendered text, node surfaces and paths.
// Usage: node scripts/verify_accuracy_labels.mjs <diagram.json> [artifact.svg|html] [--legacy]
// Without an artifact, render the fixture with the opt-in readable-label style.
// This checks rendering fidelity only; it does not prove source-code semantics.
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";
import { chromium } from "playwright";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const legacy = args.includes("--legacy");
const positional = args.filter((arg) => arg !== "--legacy");
if (!positional[0] || positional.length > 2) {
  throw new Error("usage: verify_accuracy_labels.mjs <diagram.json> [artifact.svg|html] [--legacy]");
}
const specPath = path.resolve(positional[0]);
const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
let generated;
if (!positional[1]) {
  const result = spawnSync(process.env.PYTHON || "python3", ["-c", `
import json, sys
from anidiagram.quality import quality_report
from anidiagram.renderer_svg import render_svg
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style
spec = json.load(sys.stdin)
style = load_style()
if sys.argv[1] != "legacy":
    style.setdefault("edge", {})["label_placement"] = "avoid-nodes"
scene = compile_scene(spec)
print(json.dumps({"svg": render_svg(scene, style), "quality": quality_report(scene, style)}))
`, legacy ? "legacy" : "readable"], {
    cwd: root,
    env: {...process.env, PYTHONPATH: [path.join(root, "src"), process.env.PYTHONPATH].filter(Boolean).join(path.delimiter)},
    input: JSON.stringify(spec), encoding: "utf8", maxBuffer: 16 * 1024 * 1024,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(result.stderr || "fixture rendering failed");
  generated = JSON.parse(result.stdout);
}

const browser = await chromium.launch({headless: true});
try {
  const page = await browser.newPage({viewport: {width: 1600, height: 1400}});
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await page.route(/^https?:/, (route) => route.abort());
  if (positional[1]) {
    await page.goto(pathToFileURL(path.resolve(positional[1])).href, {waitUntil: "load"});
  } else {
    await page.setContent(generated.svg, {waitUntil: "load"});
  }
  await page.evaluate(async () => {
    await document.fonts.ready;
    const svg = document.querySelector("svg");
    if (svg?.pauseAnimations) {
      svg.pauseAnimations();
      svg.setCurrentTime(60);
    }
  });
  const report = await page.evaluate((authored) => {
    const svg = document.querySelector("svg");
    if (!svg) throw new Error("rendered artifact contains no SVG");
    const normalize = (text) => (text || "").replace(/\s+/g, " ").trim();
    const boxOf = (element) => {
      const box = element.getBoundingClientRect();
      return {x: box.x, y: box.y, width: box.width, height: box.height};
    };
    const overlaps = (a, b) => a.x < b.x + b.width && a.x + a.width > b.x
      && a.y < b.y + b.height && a.y + a.height > b.y;
    const visible = (element) => {
      for (let item = element; item; item = item.parentElement) {
        const style = getComputedStyle(item);
        if (style.display === "none" || style.visibility === "hidden" || Number(style.opacity) === 0) return false;
      }
      return true;
    };
    const nodes = authored.nodes.map((node) => {
      const element = document.getElementById(`node-${node.id}`);
      const surface = element?.querySelector(".node-surface");
      if (!surface) throw new Error(`missing rendered node surface: ${node.id}`);
      return {id: node.id, box: boxOf(surface)};
    });
    const groups = [...svg.querySelectorAll("g.edge")];
    const issues = [];
    if (groups.length !== authored.edges.length) issues.push({code: "edge-count", actual: groups.length, expected: authored.edges.length});
    const edges = authored.edges.map((edge, index) => {
      const id = edge.semantic_relation_id || `edge:${index}`;
      const group = groups[index];
      if (!group) return {id, missing: true};
      const text = group.querySelector(".edge-label");
      const label = normalize(text?.textContent);
      const labelBox = text ? boxOf(text) : null;
      if (label !== normalize(edge.label)) issues.push({id, code: "label-content", expected: edge.label, actual: label});
      if (edge.label && (!text || !visible(text) || !labelBox.width || !labelBox.height)) issues.push({id, code: "label-not-visible"});
      const collisions = label ? nodes.filter((node) => overlaps(labelBox, node.box)).map((node) => node.id) : [];
      if (collisions.length) issues.push({id, code: "label-node-overlap", nodes: collisions});
      if (labelBox && label && !(() => {
        const canvas = boxOf(svg);
        return labelBox.x >= canvas.x && labelBox.y >= canvas.y
          && labelBox.x + labelBox.width <= canvas.x + canvas.width
          && labelBox.y + labelBox.height <= canvas.y + canvas.height;
      })()) issues.push({id, code: "label-outside-canvas"});

      const line = group.querySelector(".edge-draw");
      if (!line) throw new Error(`missing edge path: ${id}`);
      const length = line.getTotalLength();
      const transform = line.getScreenCTM();
      const endpoint = (at) => {
        const point = line.getPointAtLength(at);
        const screen = new DOMPoint(point.x, point.y).matrixTransform(transform);
        return {x: screen.x, y: screen.y};
      };
      const start = endpoint(0);
      const end = endpoint(length);
      const boundaryDistance = (point, box) => {
        const right = box.x + box.width;
        const bottom = box.y + box.height;
        if (point.x >= box.x && point.x <= right && point.y >= box.y && point.y <= bottom) {
          return Math.min(point.x - box.x, right - point.x, point.y - box.y, bottom - point.y);
        }
        return Math.hypot(Math.max(box.x - point.x, 0, point.x - right), Math.max(box.y - point.y, 0, point.y - bottom));
      };
      const scale = Math.max(Math.hypot(transform.a, transform.b), Math.hypot(transform.c, transform.d));
      const source = nodes.find((node) => node.id === edge.from);
      const target = nodes.find((node) => node.id === edge.to);
      const sourceDistance = boundaryDistance(start, source.box);
      const targetDistance = boundaryDistance(end, target.box);
      if (sourceDistance > 14 * scale) issues.push({id, code: "path-start-wrong-node", distance: sourceDistance});
      if (targetDistance > 14 * scale) issues.push({id, code: "path-end-wrong-node", distance: targetDistance});
      const direction = edge.direction || "forward";
      const markerStart = line.getAttribute("marker-start");
      const markerEnd = line.getAttribute("marker-end");
      if (Boolean(markerStart) !== (direction === "bidirectional") || Boolean(markerEnd) !== (direction !== "undirected")) {
        issues.push({id, code: "arrow-direction", direction, markerStart, markerEnd});
      }
      for (const markerRef of [markerStart, markerEnd].filter(Boolean)) {
        const markerId = /^url\(#(.+)\)$/.exec(markerRef)?.[1];
        const marker = markerId ? document.getElementById(markerId) : null;
        if (!marker?.querySelector("path")) issues.push({id, code: "missing-arrow-marker", markerRef});
        else if (marker.getAttribute("orient") !== (direction === "bidirectional" ? "auto-start-reverse" : "auto")) {
          issues.push({id, code: "arrow-orientation", markerRef});
        }
      }
      return {id, label, labelBox, collisions, direction, markerStart, markerEnd, start, end};
    });
    for (let i = 0; i < edges.length; i += 1) {
      for (let j = i + 1; j < edges.length; j += 1) {
        if (edges[i].label && edges[j].label && overlaps(edges[i].labelBox, edges[j].labelBox)) {
          issues.push({code: "label-label-overlap", edges: [edges[i].id, edges[j].id]});
        }
      }
    }
    return {edges, issues};
  }, spec);
  const output = {ok: !report.issues.length && !errors.length,
    mode: positional[1] ? "supplied-artifact" : legacy ? "legacy" : "avoid-nodes",
    fixture: path.basename(specPath), quality: generated?.quality, ...report, browserErrors: errors};
  process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
  if (!output.ok) process.exitCode = 1;
} finally {
  await browser.close();
}

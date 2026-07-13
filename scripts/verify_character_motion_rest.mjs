#!/usr/bin/env node
import fs from "node:fs";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);

function loadPlaywright() {
  let localError;
  try {
    return require("playwright");
  } catch (error) {
    localError = error;
  }

  try {
    const globalRoot = execFileSync("npm", ["root", "-g"], { encoding: "utf-8" }).trim();
    if (!globalRoot) throw new Error("npm root -g returned an empty path");
    return createRequire(path.join(globalRoot, "package.json"))("playwright");
  } catch (globalError) {
    throw new Error(
      `Unable to resolve Playwright. Install it locally with \`npm install --save-dev playwright\` or globally with \`npm install -g playwright\`. Local resolution: ${localError.message}. Global resolution: ${globalError.message}`
    );
  }
}

const FULL_GALLERY_CHARACTER_COUNT = 13;

async function readCharacterManifest(page) {
  const source = await page.evaluate(() => document.getElementById("anidiagram-motion-manifest")?.textContent);
  if (!source) throw new Error("missing Motion Manifest: #anidiagram-motion-manifest");

  let manifest;
  try {
    manifest = JSON.parse(source);
  } catch (error) {
    throw new Error(`invalid Motion Manifest JSON: ${error.message}`);
  }
  if (!manifest || typeof manifest !== "object" || Array.isArray(manifest)) {
    throw new Error("invalid Motion Manifest: expected an object");
  }
  if (manifest.icon_system !== "illustrated-character-v1") {
    throw new Error(`expected Motion Manifest icon_system illustrated-character-v1; received ${String(manifest.icon_system)}`);
  }
  if (!Array.isArray(manifest.icons)) {
    throw new Error("invalid Motion Manifest: expected icons array");
  }
  return manifest;
}

function characterEntries(manifest, expectedCount) {
  const entries = manifest.icons;
  if (entries.length !== expectedCount) {
    throw new Error(`expected ${expectedCount} illustrated-character entries; received ${entries.length}`);
  }
  const nodeIds = new Set();
  const icons = new Set();
  for (const entry of entries) {
    if (
      !entry
      || typeof entry.node_id !== "string"
      || typeof entry.icon !== "string"
      || typeof entry.performance !== "string"
      || !Number.isFinite(entry.rest_at)
      || !entry.parts
      || typeof entry.parts.root !== "string"
    ) {
      throw new Error("invalid illustrated-character Motion Manifest entry");
    }
    if (nodeIds.has(entry.node_id) || icons.has(entry.icon)) {
      throw new Error(`duplicate illustrated-character Motion Manifest entry: ${entry.node_id}/${entry.icon}`);
    }
    nodeIds.add(entry.node_id);
    icons.add(entry.icon);
  }
  return entries;
}

async function main() {
  const htmlPath = process.argv[2];
  if (!htmlPath || !fs.existsSync(htmlPath)) {
    throw new Error("usage: verify_character_motion_rest.mjs <runtime.html>");
  }

  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
    await page.waitForSelector("svg");
    await page.waitForFunction(() => Boolean(window.AniDiagramRuntime) && Boolean(window.gsap) && Array.isArray(window.__ANIDIAGRAM_TIMELINES__));
    const manifest = await readCharacterManifest(page);
    const expectedEntries = characterEntries(manifest, FULL_GALLERY_CHARACTER_COUNT);

    const result = await page.evaluate((characterEntries) => {
      const timelines = (window.__ANIDIAGRAM_TIMELINES__ || []).filter((timeline) => timeline.__anidiagramCharacter);
      const failures = [];

      if (timelines.length !== characterEntries.length) {
        failures.push(`expected ${characterEntries.length} character timelines; received ${timelines.length}`);
      }

      const entriesByNode = new Map(characterEntries.map((entry) => [entry.node_id, entry]));
      const approximately = (actual, expected) => Math.abs(Number(actual) - expected) < 0.001;
      const screenAnchor = (element) => {
        const matrix = element.getScreenCTM();
        return matrix ? [matrix.a, matrix.b, matrix.c, matrix.d, matrix.e, matrix.f] : null;
      };
      const sameAnchor = (before, after) => Boolean(before && after) && before.every((value, index) => approximately(value, after[index]));
      for (const timeline of timelines) {
        const metadata = timeline.__anidiagramCharacter;
        const entry = entriesByNode.get(metadata.nodeId);
        if (!entry) {
          failures.push(`unexpected character timeline for ${metadata.nodeId}`);
          continue;
        }
        if (metadata.performance !== entry.performance || metadata.restAt !== entry.rest_at) {
          failures.push(`metadata mismatch for ${metadata.nodeId}`);
          continue;
        }
        if (!(metadata.restAt > 0) || !(metadata.restAt < timeline.duration())) {
          failures.push(`invalid restAt for ${metadata.nodeId}: ${metadata.restAt} / ${timeline.duration()}`);
          continue;
        }

        const root = document.querySelector(entry.parts.root);
        if (!root) {
          failures.push(`missing root ${entry.parts.root} for ${metadata.nodeId}`);
          continue;
        }
        const anchorBefore = screenAnchor(root);
        timeline.pause();
        timeline.seek(metadata.restAt, false);
        const anchorAfter = screenAnchor(root);
        if (!sameAnchor(anchorBefore, anchorAfter)) {
          failures.push(`root anchor changed for ${metadata.nodeId}: ${JSON.stringify({ before: anchorBefore, after: anchorAfter })}`);
        }
        for (const [partName, selector] of Object.entries(entry.parts || {})) {
          if (partName === "root") continue;
          const element = document.querySelector(selector);
          if (!element) {
            failures.push(`missing ${selector} for ${metadata.nodeId}`);
            continue;
          }
          const expectedOpacity = Number(element.dataset.restOpacity);
          const properties = {
            x: Number(window.gsap.getProperty(element, "x")),
            y: Number(window.gsap.getProperty(element, "y")),
            rotation: Number(window.gsap.getProperty(element, "rotation")),
            scaleX: Number(window.gsap.getProperty(element, "scaleX")),
            scaleY: Number(window.gsap.getProperty(element, "scaleY")),
            opacity: Number(window.getComputedStyle(element).opacity),
          };
          if (
            !approximately(properties.x, 0)
            || !approximately(properties.y, 0)
            || !approximately(properties.rotation, 0)
            || !approximately(properties.scaleX, 1)
            || !approximately(properties.scaleY, 1)
            || !approximately(properties.opacity, expectedOpacity)
          ) {
            failures.push(`${metadata.nodeId} ${selector} did not return to rest: ${JSON.stringify(properties)}`);
          }
        }
      }
      return { failures, expected: characterEntries.length, actual: timelines.length };
    }, expectedEntries);

    if (result.failures.length) {
      throw new Error(result.failures.join("\n"));
    }
    process.stdout.write(`verified character rest state for ${result.actual}/${result.expected} timelines\n`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});

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
  const expectedCount = Number(process.argv[3]);
  if (!htmlPath || !fs.existsSync(htmlPath) || !Number.isInteger(expectedCount) || expectedCount < 1) {
    throw new Error("usage: verify_character_reduced_motion.mjs <runtime.html> <expected-character-icon-count>");
  }
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
    await page.waitForSelector("svg");
    await page.waitForFunction(() => Boolean(window.AniDiagramRuntime) && Array.isArray(window.__ANIDIAGRAM_TIMELINES__));
    const manifest = await readCharacterManifest(page);
    const expectedEntries = characterEntries(manifest, expectedCount);
    const { timelines, roots } = await page.evaluate((entries) => ({
      timelines: window.__ANIDIAGRAM_TIMELINES__.length,
      roots: entries.filter((entry) => document.querySelector(entry.parts.root)).length,
    }), expectedEntries);
    if (timelines !== 0) {
      throw new Error(`expected zero timelines under reduced motion; received ${timelines}`);
    }
    if (roots !== expectedEntries.length) {
      throw new Error(`expected ${expectedEntries.length} rendered illustrated-character roots; received ${roots}`);
    }
    process.stdout.write(`verified reduced motion for ${roots}/${expectedEntries.length} illustrated-character entries\n`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});

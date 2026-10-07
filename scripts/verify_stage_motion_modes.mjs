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

async function snapshot(page) {
  return page.evaluate(() => {
    const timelines = window.__ANIDIAGRAM_TIMELINES__ || [];
    const stageKinds = timelines.map((timeline) => timeline.__anidiagramStage).filter(Boolean);
    return {
      mode: document.getElementById("viewer")?.className || "",
      total: timelines.length,
      characters: timelines.filter((timeline) => timeline.__anidiagramCharacter || timeline.__anidiagramPresentation).length,
      titleEntries: stageKinds.filter((kind) => kind === "title-entry").length,
      edgePackets: stageKinds.filter((kind) => kind === "edge-motion").length,
      edgeIndices: timelines.filter((timeline) => timeline.__anidiagramStage === "edge-motion").map((timeline) => timeline.__anidiagramEdgeIndex),
      edgeEffects: timelines.filter((timeline) => timeline.__anidiagramStage === "edge-motion").map((timeline) => timeline.__anidiagramEdgeEffect),
      edgeKinds: timelines.filter((timeline) => timeline.__anidiagramStage === "edge-motion").map((timeline) => timeline.__anidiagramEdgeKind),
      generated: document.querySelectorAll(".runtime-generated, .edge-motion-v1-generated").length,
      edgeGenerated: document.querySelectorAll(".edge-motion-v1-generated").length,
      logicalPackets: document.querySelectorAll(".runtime-edge-packet").length,
      logicalComets: document.querySelectorAll(".runtime-edge-comet").length,
      cometPartCounts: Array.from(document.querySelectorAll(".runtime-edge-comet")).map((element) => element.querySelectorAll("circle").length),
      cometRecipes: Array.from(document.querySelectorAll(".runtime-edge-comet")).map((element) => ({
        radii: Array.from(element.querySelectorAll("circle")).map((part) => Number(part.getAttribute("r"))),
        strokes: Array.from(element.querySelectorAll("circle")).map((part) => part.getAttribute("stroke")),
      })),
      generatedKeys: Array.from(document.querySelectorAll(".runtime-generated")).map((element) => `${element.tagName}:${element.className.baseVal || element.className}`),
    };
  });
}

async function selectMode(page, mode) {
  await page.locator(`.motion-choice[data-motion="${mode}"]`).click();
  await page.waitForFunction((expected) => document.getElementById("viewer")?.classList.contains(`motion-${expected}`), mode);
  return snapshot(page);
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function main() {
  const htmlPath = process.argv[2];
  if (!htmlPath || !fs.existsSync(htmlPath)) {
    throw new Error("usage: verify_stage_motion_modes.mjs <runtime.html> [expected-characters] [expected-edges] [expected-readable-edges]");
  }
  const expectedCharacterArg = process.argv[3] === undefined ? null : Number(process.argv[3]);
  const expectedEdgeArg = process.argv[4] === undefined ? null : Number(process.argv[4]);
  const expectedReadableArg = process.argv[5] === undefined ? null : Number(process.argv[5]);
  for (const [label, value] of [["characters", expectedCharacterArg], ["edges", expectedEdgeArg], ["readable edges", expectedReadableArg]]) {
    if (value !== null && (!Number.isInteger(value) || value < 0)) {
      throw new Error(`expected ${label} must be a non-negative integer`);
    }
  }
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({ headless: true, ...(process.env.ANIDIAGRAM_BROWSER_CHANNEL ? {channel: process.env.ANIDIAGRAM_BROWSER_CHANNEL} : {}) });
  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
    await page.waitForSelector("svg");
    await page.waitForFunction(() => Boolean(window.AniDiagramRuntime) && Boolean(window.gsap) && Array.isArray(window.__ANIDIAGRAM_TIMELINES__));
    const manifest = await page.evaluate(() => JSON.parse(document.getElementById("anidiagram-motion-manifest").textContent));
    const expectedCharacters = manifest.stage.active_icon_node_ids?.length ?? manifest.icons.length;
    const totalEdges = await page.locator("g.edge").count();
    if (expectedCharacterArg !== null) {
      assert(manifest.icons.length === expectedCharacterArg, `manifest characters: ${manifest.icons.length}/${expectedCharacterArg}`);
    }
    if (expectedEdgeArg !== null) {
      assert(totalEdges === expectedEdgeArg, `rendered edges: ${totalEdges}/${expectedEdgeArg}`);
    }
    const fallbackExpressive = Array.from({ length: Number.isInteger(manifest.stage.edge_limit) ? Math.min(totalEdges, manifest.stage.edge_limit) : totalEdges }, (_, index) => index);
    const fallbackReadable = Array.from({ length: Number.isInteger(manifest.stage.readable_edge_limit) ? Math.min(totalEdges, manifest.stage.readable_edge_limit) : Math.min(2, totalEdges) }, (_, index) => index);
    const expectedExpressiveIndices = manifest.stage.edge_flow
      ? (Array.isArray(manifest.stage.active_edge_indices) ? manifest.stage.active_edge_indices : fallbackExpressive)
      : [];
    const expectedReadableIndices = manifest.stage.edge_flow
      ? (Array.isArray(manifest.stage.readable_edge_indices) ? manifest.stage.readable_edge_indices : fallbackReadable)
      : [];
    const expectedExpressivePackets = expectedExpressiveIndices.length;
    const expectedReadablePackets = expectedReadableIndices.length;
    if (expectedReadableArg !== null) {
      assert(expectedReadablePackets === expectedReadableArg, `readable edges: ${expectedReadablePackets}/${expectedReadableArg}`);
    }
    const edgeEntries = Array.isArray(manifest.edges) ? manifest.edges : [];
    const packetCount = (indices) => indices.filter((index) => edgeEntries[index]?.motion_kind === "packet").length;
    const cometCount = (indices) => indices.filter((index) => edgeEntries[index]?.motion_kind === "comet").length;
    const expectedExpressiveLogicalPackets = packetCount(expectedExpressiveIndices);
    const expectedReadableLogicalPackets = packetCount(expectedReadableIndices);
    const expectedExpressiveLogicalComets = cometCount(expectedExpressiveIndices);
    const expectedReadableLogicalComets = cometCount(expectedReadableIndices);
    const assertCometRecipes = (state, label) => state.cometRecipes.forEach((recipe) => {
      assert(recipe.radii.length === 4, `${label} comet radii: ${recipe.radii}`);
      assert(recipe.radii.every((radius, index) => index === 0 || radius < recipe.radii[index - 1]), `${label} comet radii are not descending: ${recipe.radii}`);
      assert(recipe.strokes.every((stroke) => stroke === "none"), `${label} comet outlines: ${recipe.strokes}`);
    });

    // Expressive -> Readable -> Off -> Expressive
    const expressive = await snapshot(page);
    assert(expressive.characters === expectedCharacters, `expressive character timelines: ${expressive.characters}/${expectedCharacters}`);
    assert(expressive.titleEntries === (manifest.stage.title_sweep ? 1 : 0), `expressive title entries: ${expressive.titleEntries}`);
    assert(expressive.edgePackets === expectedExpressivePackets, `expressive edge packet timelines: ${expressive.edgePackets}/${expectedExpressivePackets}`);
    assert(JSON.stringify(expressive.edgeIndices) === JSON.stringify(expectedExpressiveIndices), `expressive edge indices: ${expressive.edgeIndices}/${expectedExpressiveIndices}`);
    assert(expressive.logicalPackets === expectedExpressiveLogicalPackets, `logical packet mismatch: ${expressive.logicalPackets}/${expectedExpressiveLogicalPackets}`);
    assert(expressive.logicalComets === expectedExpressiveLogicalComets, `logical comet mismatch: ${expressive.logicalComets}/${expectedExpressiveLogicalComets}`);
    assert(expressive.cometPartCounts.every((count) => count === 4), `comet part counts: ${expressive.cometPartCounts}`);
    assertCometRecipes(expressive, "expressive");
    const cycleCheck = await page.evaluate(() => {
      const edgeTimelines = (window.__ANIDIAGRAM_STAGE_TIMELINES__ || []).filter((timeline) => timeline.__anidiagramStage === "edge-motion");
      const titleTimelines = (window.__ANIDIAGRAM_STAGE_TIMELINES__ || []).filter((timeline) => timeline.__anidiagramStage === "title-entry");
      edgeTimelines.forEach((timeline) => {
        timeline.pause();
        const cycle = timeline.duration() + timeline.repeatDelay();
        timeline.totalTime(cycle * 2 + 0.1, false);
      });
      return {
        edgeRepeatDelays: edgeTimelines.map((timeline) => timeline.repeatDelay()),
        titleRepeats: titleTimelines.map((timeline) => timeline.repeat()),
        logicalPackets: document.querySelectorAll(".runtime-edge-packet").length,
        logicalComets: document.querySelectorAll(".runtime-edge-comet").length,
      };
    });
    assert(cycleCheck.edgeRepeatDelays.every((value) => Math.abs(value) < 0.001), `edge repeat delays: ${cycleCheck.edgeRepeatDelays}`);
    assert(cycleCheck.titleRepeats.every((value) => value === 0), `title repeats: ${cycleCheck.titleRepeats}`);
    assert(cycleCheck.logicalPackets === expectedExpressiveLogicalPackets, `duplicate packets after two cycles: ${cycleCheck.logicalPackets}/${expectedExpressiveLogicalPackets}`);
    assert(cycleCheck.logicalComets === expectedExpressiveLogicalComets, `duplicate comets after two cycles: ${cycleCheck.logicalComets}/${expectedExpressiveLogicalComets}`);

    await page.locator("#restart").click();
    const restarted = await snapshot(page);
    assert(restarted.titleEntries === expressive.titleEntries, `restart title entries: ${restarted.titleEntries}/${expressive.titleEntries}`);

    const readable = await selectMode(page, "readable");
    assert(readable.characters === expectedCharacters, `readable character timelines: ${readable.characters}/${expectedCharacters}`);
    assert(readable.titleEntries === 0, `readable title entries: ${readable.titleEntries}`);
    assert(readable.edgePackets === expectedReadablePackets, `readable edge packet timelines: ${readable.edgePackets}/${expectedReadablePackets}`);
    assert(JSON.stringify(readable.edgeIndices) === JSON.stringify(expectedReadableIndices), `readable edge indices: ${readable.edgeIndices}/${expectedReadableIndices}`);
    assert(readable.logicalPackets === expectedReadableLogicalPackets, `readable logical packet mismatch: ${readable.logicalPackets}/${expectedReadableLogicalPackets}`);
    assert(readable.logicalComets === expectedReadableLogicalComets, `readable logical comet mismatch: ${readable.logicalComets}/${expectedReadableLogicalComets}`);
    assert(readable.cometPartCounts.every((count) => count === 4), `readable comet part counts: ${readable.cometPartCounts}`);
    assertCometRecipes(readable, "readable");

    const off = await selectMode(page, "off");
    assert(off.total === 0, `off timelines: ${off.total}`);
    assert(off.generated === 0, `off runtime-generated elements: ${off.generated}`);
    const offState = await page.evaluate((entries) => {
      const failures = [];
      const approximately = (actual, expected) => Math.abs(Number(actual) - expected) < 0.001;
      for (const entry of entries) {
        for (const [partName, selector] of Object.entries(entry.parts || {})) {
          if (partName === "root") continue;
          const element = document.querySelector(selector);
          if (!element) {
            failures.push(`missing ${selector}`);
            continue;
          }
          const restOpacity = Number(element.dataset.restOpacity);
          const values = {
            x: Number(window.gsap.getProperty(element, "x")),
            y: Number(window.gsap.getProperty(element, "y")),
            rotation: Number(window.gsap.getProperty(element, "rotation")),
            scaleX: Number(window.gsap.getProperty(element, "scaleX")),
            scaleY: Number(window.gsap.getProperty(element, "scaleY")),
            opacity: Number(window.getComputedStyle(element).opacity),
            strokeDashoffset: Number(window.gsap.getProperty(element, "strokeDashoffset")),
          };
          if (!approximately(values.x, 0) || !approximately(values.y, 0) || !approximately(values.rotation, 0)
              || !approximately(values.scaleX, 1) || !approximately(values.scaleY, 1)
              || !approximately(values.opacity, restOpacity)
              || (Number.isFinite(values.strokeDashoffset) && !approximately(values.strokeDashoffset, 0))) {
            failures.push(`${selector}: ${JSON.stringify(values)}`);
          }
        }
      }
      return failures;
    }, manifest.icons);
    assert(offState.length === 0, `off character state is not canonical:\n${offState.join("\n")}`);

    const expressiveAgain = await selectMode(page, "expressive");
    assert(expressiveAgain.characters === expectedCharacters, `restored character timelines: ${expressiveAgain.characters}/${expectedCharacters}`);
    assert(expressiveAgain.edgePackets === expressive.edgePackets, `restored edge packets: ${expressiveAgain.edgePackets}/${expressive.edgePackets}`);
    assert(JSON.stringify(expressiveAgain.edgeIndices) === JSON.stringify(expectedExpressiveIndices), `restored edge indices: ${expressiveAgain.edgeIndices}/${expectedExpressiveIndices}`);
    assert(expressiveAgain.titleEntries === expressive.titleEntries, `restored title entries: ${expressiveAgain.titleEntries}/${expressive.titleEntries}`);
    assert(expressiveAgain.logicalPackets === expectedExpressiveLogicalPackets, "duplicate runtime-generated packet elements");
    assert(expressiveAgain.logicalComets === expectedExpressiveLogicalComets, "duplicate runtime-generated comet elements");
    assert(expressiveAgain.cometPartCounts.every((count) => count === 4), `restored comet part counts: ${expressiveAgain.cometPartCounts}`);
    assertCometRecipes(expressiveAgain, "restored");
    assert(expressiveAgain.edgeGenerated === expressive.edgeGenerated, `duplicate edge-motion elements: ${expressiveAgain.edgeGenerated}/${expressive.edgeGenerated}`);

    process.stdout.write(`verified stage modes Expressive -> Readable -> Off -> Expressive; characters=${expectedCharacters}; edges=${totalEdges}; readable=${readable.edgePackets}\n`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});

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
  const expectedMode = process.argv[3] || "timeline";
  if (!htmlPath || !fs.existsSync(htmlPath)) {
    throw new Error("usage: verify_choreographer.mjs <html-path> [timeline|hybrid]");
  }
  const browser = await chromium.launch({ headless: true });
  const errors = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
    await page.waitForFunction(() => Boolean(window.AniDiagramRuntime));
    await page.waitForTimeout(120);
    const initial = await page.evaluate(() => {
      const manifest = JSON.parse(document.getElementById("anidiagram-motion-manifest").textContent);
      return {
        mode: manifest.mode,
        steps: manifest.choreographer && manifest.choreographer.steps.length,
        controls: ["timeline-start", "timeline-previous", "timeline-next"].map(
          (id) => !document.getElementById(id).hidden
        ),
        choreographer: Boolean(window.__ANIDIAGRAM_CHOREOGRAPHER__),
        iconTimelines: (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length,
      };
    });
    assert(initial.mode === expectedMode, `mode ${initial.mode}/${expectedMode}`);
    assert(initial.steps > 0, "timeline has no causal steps");
    assert(initial.controls.every(Boolean), "timeline controls are hidden");
    if (expectedMode === "timeline") assert(initial.choreographer, "timeline did not autoplay");
    if (expectedMode === "hybrid") {
      assert(!initial.choreographer, "hybrid should begin in ambient mode");
      assert(initial.iconTimelines > 0, "hybrid ambient timelines are missing");
      await page.click("#timeline-start");
    }
    const stepped = await page.evaluate(() => {
      window.AniDiagramRuntime.pause();
      const step = window.AniDiagramRuntime.nextStep();
      return {
        step: step && step.index,
        current: window.__ANIDIAGRAM_CHOREOGRAPHER__.current,
        generatedEdges: document.querySelectorAll(".edge-motion-v1-generated").length,
      };
    });
    assert(stepped.step === 1 && stepped.current === 1, "next did not advance the visible first step");
    assert(stepped.generatedEdges === 0, "ambient edge loops leaked into choreographer mode");
    assert(errors.length === 0, `console errors: ${errors.join("; ")}`);
    process.stdout.write(`${JSON.stringify({ ok: true, mode: expectedMode, steps: initial.steps })}\n`);
  } finally {
    await browser.close();
  }
}


main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});

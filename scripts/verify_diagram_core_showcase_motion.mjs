#!/usr/bin/env node
import path from "node:path";
import process from "node:process";
import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";

import { chromium } from "playwright";


const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SHOWCASE_PATH = path.join(REPO_ROOT, "gallery", "diagram-core", "showcase.html");
const MOTION_CATALOG_PATH = path.join(REPO_ROOT, "runtime", "motion-catalog.json");
const ICONS = Object.freeze(["agent", "database", "api", "server"]);
const OPERATION_TIMEOUT_MS = 10_000;
const AMPLITUDE = Object.freeze({ translation: 4, rotation: 4, scale: 0.08 });
const SHOWCASE_DEFINITIONS = Object.freeze(
  JSON.parse(readFileSync(MOTION_CATALOG_PATH, "utf8")).diagram_core_presentations
);


function fail(message) {
  throw new Error(`Diagram Core showcase verification failed: ${message}`);
}


async function openPage(browser, reducedMotion = "no-preference", suffix = "") {
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    reducedMotion,
  });
  const page = await context.newPage();
  page.setDefaultTimeout(OPERATION_TIMEOUT_MS);
  const url = pathToFileURL(SHOWCASE_PATH);
  url.search = suffix;
  await page.goto(url.href, { waitUntil: "load" });
  return { context, page };
}


async function verifySemanticBoundary(page) {
  const boundary = await page.evaluate(() => ({
    presentations: document.querySelectorAll('[data-icon-presentation="showcase"]').length,
    states: document.querySelectorAll("[data-icon-state]").length,
    stateMarks: document.querySelectorAll("[data-state-mark]").length,
    cards: document.querySelectorAll("[data-showcase-card]").length,
    manifest: JSON.parse(document.getElementById("anidiagram-motion-manifest").textContent),
  }));
  if (boundary.presentations !== 4 || boundary.cards !== 4) {
    fail(`expected four showcase icons, got presentations=${boundary.presentations} cards=${boundary.cards}`);
  }
  if (boundary.states !== 0 || boundary.stateMarks !== 0) {
    fail(`semantic state leaked into v1 review: states=${boundary.states} marks=${boundary.stateMarks}`);
  }
  if (boundary.manifest.profile !== "showcase" || boundary.manifest.icons.length !== 4) {
    fail("motion manifest does not declare one four-icon showcase profile");
  }
  const manifestIcons = boundary.manifest.icons.map((entry) => entry.icon);
  if (JSON.stringify(manifestIcons) !== JSON.stringify(ICONS)) {
    fail(`unexpected manifest icon order: ${manifestIcons.join(",")}`);
  }
  for (const [index, definition] of SHOWCASE_DEFINITIONS.entries()) {
    const entry = boundary.manifest.icons[index];
    const expected = {
      icon: definition.icon,
      performance: definition.runtime_id,
      presentation_performance: definition.id,
      presentation_profile: definition.profile,
      rest_at: definition.rest_at,
      repeat_delay: definition.repeat_delay,
      duration_ms: definition.duration_ms,
      repeat_policy: definition.repeat_policy,
      cancel_behavior: definition.cancel_behavior,
      reduced_motion_behavior: definition.reduced_motion_behavior,
    };
    for (const [name, value] of Object.entries(expected)) {
      if (entry[name] !== value) {
        fail(`scene manifest ${entry.icon}.${name}=${entry[name]} does not match motion catalog ${value}`);
      }
    }
  }
}


async function verifyExpressiveMotion(page) {
  await page.waitForFunction(() => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === 4);
  const report = await page.evaluate(({ amplitude }) => {
    const manifest = JSON.parse(document.getElementById("anidiagram-motion-manifest").textContent);
    const timelines = window.__ANIDIAGRAM_ICON_TIMELINES__;
    const entries = manifest.icons.map((icon, index) => {
      const timeline = timelines[index];
      timeline.pause();
      const samples = Array.from(
        { length: 201 },
        (_, sampleIndex) => timeline.duration() * sampleIndex / 200
      );
      const peaks = { translation: 0, rotation: 0, scale: 0 };
      let maxMovingParts = 0;
      let minScale = 1;
      let maxScale = 1;
      let minBodyScale = 1;
      let maxBodyScale = 1;
      let clipped = false;
      for (const time of samples) {
        timeline.seek(Math.min(time, timeline.duration()), false);
        let movingParts = 0;
        for (const selector of Object.values(icon.parts)) {
          const part = document.querySelector(selector);
          const x = Number(window.gsap.getProperty(part, "x")) || 0;
          const y = Number(window.gsap.getProperty(part, "y")) || 0;
          const rotation = Number(window.gsap.getProperty(part, "rotation")) || 0;
          const scaleX = Number(window.gsap.getProperty(part, "scaleX")) || 1;
          const scaleY = Number(window.gsap.getProperty(part, "scaleY")) || 1;
          peaks.translation = Math.max(peaks.translation, Math.abs(x), Math.abs(y));
          peaks.rotation = Math.max(peaks.rotation, Math.abs(rotation));
          peaks.scale = Math.max(peaks.scale, Math.abs(scaleX - 1), Math.abs(scaleY - 1));
          minScale = Math.min(minScale, scaleX, scaleY);
          maxScale = Math.max(maxScale, scaleX, scaleY);
          if (selector === icon.parts.body) {
            minBodyScale = Math.min(minBodyScale, scaleX, scaleY);
            maxBodyScale = Math.max(maxBodyScale, scaleX, scaleY);
          }
          if ([x, y, rotation, scaleX - 1, scaleY - 1].some((value) => Math.abs(value) > 0.001)) {
            movingParts += 1;
          }
        }
        maxMovingParts = Math.max(maxMovingParts, movingParts);
        const body = document.querySelector(icon.parts.body).getBoundingClientRect();
        const card = document.querySelector(`[data-showcase-card="${icon.icon}"] rect`).getBoundingClientRect();
        if (body.left < card.left - 0.5 || body.right > card.right + 0.5 || body.top < card.top - 0.5 || body.bottom > card.bottom + 0.5) {
          clipped = true;
        }
      }
      const wallDuration = timeline.duration() / timeline.timeScale();
      const wallRepeatDelay = timeline.repeatDelay() / timeline.timeScale();
      const expressive = peaks.translation >= amplitude.translation
        || peaks.rotation >= amplitude.rotation
        || peaks.scale >= amplitude.scale;
      return {
        icon: icon.icon,
        peaks,
        expressive,
        clipped,
        wallDuration,
        timelineDuration: timeline.duration(),
        wallRepeatDelay,
        maxMovingParts,
        minScale,
        maxScale,
        minBodyScale,
        maxBodyScale,
        catalogDurationMs: icon.duration_ms,
        catalogRestAt: icon.rest_at,
        timelineRestAt: timeline.__anidiagramRestAt,
      };
    });
    return entries;
  }, { amplitude: AMPLITUDE });

  for (const entry of report) {
    if (!entry.expressive) fail(`${entry.icon} never crosses the expressive amplitude threshold`);
    if (entry.clipped) fail(`${entry.icon} clips its review card during a sampled motion phase`);
    if (entry.wallDuration < 1.6 || entry.wallDuration > 2.4) {
      fail(`${entry.icon} active duration ${entry.wallDuration.toFixed(3)}s is outside 1.6-2.4s`);
    }
    if (Math.abs(entry.wallDuration * 1000 - entry.catalogDurationMs) > 20) {
      fail(`${entry.icon} runtime duration does not match compiled duration_ms`);
    }
    if (entry.wallRepeatDelay < 0.8 || entry.wallRepeatDelay > 1.4) {
      fail(`${entry.icon} quiet interval ${entry.wallRepeatDelay.toFixed(3)}s is outside 0.8-1.4s`);
    }
    if (entry.timelineRestAt !== entry.catalogRestAt) {
      fail(`${entry.icon} runtime rest_at does not match the compiled scene manifest`);
    }
    if (entry.maxMovingParts > 4) {
      fail(`${entry.icon} drives ${entry.maxMovingParts} public parts at once; maximum is four`);
    }
    if (entry.minScale < 0.12 - 0.001 || entry.maxScale > 1.45 + 0.001) {
      fail(`${entry.icon} small-part scale range ${entry.minScale}-${entry.maxScale} is out of bounds`);
    }
    if (entry.peaks.translation > 10 + 0.01) {
      fail(`${entry.icon} translation peak ${entry.peaks.translation.toFixed(3)} exceeds 10 units`);
    }
    if (entry.peaks.rotation > 14 + 0.01) {
      fail(`${entry.icon} rotation peak ${entry.peaks.rotation.toFixed(3)} exceeds 14 degrees`);
    }
    if (entry.minBodyScale < 0.88 - 0.001 || entry.maxBodyScale > 1.16 + 0.001) {
      fail(`${entry.icon} body scale range ${entry.minBodyScale}-${entry.maxBodyScale} is out of bounds`);
    }
    if (entry.timelineRestAt > entry.timelineDuration + 0.001) {
      fail(`${entry.icon} rest_at exceeds the timeline duration`);
    }
  }
  return report;
}


async function verifyRestAndControls(page) {
  const assertRest = async (label) => {
    const dirty = await page.evaluate(() => {
      const selectors = JSON.parse(
        document.getElementById("anidiagram-motion-manifest").textContent
      ).icons.flatMap((icon) => Object.values(icon.parts));
      return selectors.filter((selector) => {
        const part = document.querySelector(selector);
        const values = [
          Number(window.gsap.getProperty(part, "x")) || 0,
          Number(window.gsap.getProperty(part, "y")) || 0,
          Number(window.gsap.getProperty(part, "rotation")) || 0,
          (Number(window.gsap.getProperty(part, "scaleX")) || 1) - 1,
          (Number(window.gsap.getProperty(part, "scaleY")) || 1) - 1,
        ];
        return values.some((value) => Math.abs(value) > 0.001);
      });
    });
    if (dirty.length) fail(`${label} did not restore authored rest for ${dirty.length} parts`);
  };

  await page.evaluate(() => {
    window.__ANIDIAGRAM_ICON_TIMELINES__.forEach((timeline) => {
      timeline.pause();
      timeline.seek(timeline.duration(), false);
    });
  });
  await assertRest("complete-cycle boundary");

  await page.evaluate(() => window.AniDiagramRuntime.stop());
  await assertRest("stop");
  const stopped = await page.evaluate(() => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length);
  if (stopped !== 0) fail(`stop left ${stopped} icon timelines`);

  await page.getByRole("button", { name: "Showcase" }).click();
  await page.waitForFunction(() => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === 4);
  await page.getByRole("button", { name: "Off" }).click();
  await assertRest("Off");
  const off = await page.evaluate(() => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length);
  if (off !== 0) fail(`Off left ${off} icon timelines`);

  await page.getByRole("button", { name: "Showcase" }).click();
  await page.waitForFunction(() => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === 4);
  await page.evaluate(() => {
    document.getElementById("restart").click();
    window.AniDiagramRuntime.pause();
  });
  await assertRest("Replay restart");
  const progress = await page.evaluate(() => window.__ANIDIAGRAM_ICON_TIMELINES__.map((timeline) => timeline.progress()));
  if (progress.some((value) => value > 0.15)) fail(`Replay did not restart all timelines: ${progress.join(",")}`);
  await page.evaluate(() => window.AniDiagramRuntime.stop());
  await assertRest("final stop");
}


async function verifyRepeatedInstanceIsolation(browser) {
  const { context, page } = await openPage(browser);
  try {
    await page.waitForFunction(() => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === 4);
    await page.evaluate(() => window.AniDiagramRuntime.stop());
    const setup = await page.evaluate(() => {
      const manifestElement = document.getElementById("anidiagram-motion-manifest");
      const manifest = JSON.parse(manifestElement.textContent);
      const original = manifest.icons[0];
      const originalRoot = document.querySelector(`[data-icon="${original.icon}"][data-icon-presentation="showcase"]`);
      const clone = originalRoot.cloneNode(true);
      const idMap = new Map();
      for (const element of [clone, ...clone.querySelectorAll("[id]")]) {
        if (!element.id) continue;
        const previous = element.id;
        const next = `${previous}__repeat`;
        idMap.set(previous, next);
        element.id = next;
      }
      clone.setAttribute("data-repeat-fixture", "agent");
      originalRoot.parentNode.appendChild(clone);
      const duplicate = JSON.parse(JSON.stringify(original));
      duplicate.node_id = `${original.node_id}-repeat`;
      duplicate.delay = 0;
      duplicate.parts = Object.fromEntries(
        Object.entries(original.parts).map(([name, selector]) => [
          name,
          `#${idMap.get(selector.slice(1))}`,
        ])
      );
      manifest.icons = [original, duplicate];
      manifestElement.textContent = JSON.stringify(manifest);
      const ids = [...document.querySelectorAll("[id]")].map((element) => element.id);
      return { duplicateIds: ids.length - new Set(ids).size };
    });
    if (setup.duplicateIds !== 0) fail(`repeat fixture created ${setup.duplicateIds} duplicate DOM ids`);

    await page.evaluate(() => window.AniDiagramRuntime.play());
    await page.waitForFunction(() => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === 2);
    const isolation = await page.evaluate(() => {
      const entries = JSON.parse(document.getElementById("anidiagram-motion-manifest").textContent).icons;
      const timelines = window.__ANIDIAGRAM_ICON_TIMELINES__;
      const moving = (entry) => Object.values(entry.parts).some((selector) => {
        const part = document.querySelector(selector);
        const values = [
          Number(window.gsap.getProperty(part, "x")) || 0,
          Number(window.gsap.getProperty(part, "y")) || 0,
          Number(window.gsap.getProperty(part, "rotation")) || 0,
          (Number(window.gsap.getProperty(part, "scaleX")) || 1) - 1,
          (Number(window.gsap.getProperty(part, "scaleY")) || 1) - 1,
        ];
        return values.some((value) => Math.abs(value) > 0.001);
      });
      timelines.forEach((timeline) => timeline.pause());
      timelines[0].seek(0, false);
      timelines[1].seek(0.4, false);
      const secondOnly = !moving(entries[0]) && moving(entries[1]);
      timelines[0].seek(0.4, false);
      timelines[1].seek(0, false);
      const firstOnly = moving(entries[0]) && !moving(entries[1]);
      return { firstOnly, secondOnly };
    });
    if (!isolation.firstOnly || !isolation.secondOnly) {
      fail(`repeated Agent instances are not isolated: ${JSON.stringify(isolation)}`);
    }
    await page.evaluate(() => window.AniDiagramRuntime.stop());
  } finally {
    await context.close();
  }
}


async function verifyTwentyIconPerformance(browser) {
  const { context, page } = await openPage(browser);
  try {
    await page.waitForFunction(() => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === 4);
    await page.evaluate(() => window.AniDiagramRuntime.stop());
    const setup = await page.evaluate(() => {
      const manifestElement = document.getElementById("anidiagram-motion-manifest");
      const manifest = JSON.parse(manifestElement.textContent);
      const originals = manifest.icons;
      const entries = [];
      for (const original of originals) {
        const originalRoot = document.querySelector(`[data-icon="${original.icon}"][data-icon-presentation="showcase"]`);
        entries.push(original);
        for (let copyIndex = 1; copyIndex < 5; copyIndex += 1) {
          const clone = originalRoot.cloneNode(true);
          const suffix = `__perf${copyIndex}`;
          const idMap = new Map();
          for (const element of [clone, ...clone.querySelectorAll("[id]")]) {
            if (!element.id) continue;
            const previous = element.id;
            const next = `${previous}${suffix}`;
            idMap.set(previous, next);
            element.id = next;
          }
          clone.setAttribute("data-performance-fixture", String(copyIndex));
          originalRoot.parentNode.appendChild(clone);
          const duplicate = JSON.parse(JSON.stringify(original));
          duplicate.node_id = `${original.node_id}-perf-${copyIndex}`;
          duplicate.delay = (copyIndex % 4) * 0.08;
          duplicate.parts = Object.fromEntries(
            Object.entries(original.parts).map(([name, selector]) => [
              name,
              `#${idMap.get(selector.slice(1))}`,
            ])
          );
          entries.push(duplicate);
        }
      }
      manifest.icons = entries;
      manifestElement.textContent = JSON.stringify(manifest);
      const ids = [...document.querySelectorAll("[id]")].map((element) => element.id);
      window.__DIAGRAM_CORE_LONG_TASKS__ = [];
      if (window.PerformanceObserver && PerformanceObserver.supportedEntryTypes.includes("longtask")) {
        const observer = new PerformanceObserver((list) => {
          window.__DIAGRAM_CORE_LONG_TASKS__.push(...list.getEntries().map((entry) => entry.duration));
        });
        observer.observe({ type: "longtask", buffered: false });
        window.__DIAGRAM_CORE_PERF_OBSERVER__ = observer;
      }
      return { entries: entries.length, duplicateIds: ids.length - new Set(ids).size };
    });
    if (setup.entries !== 20 || setup.duplicateIds !== 0) {
      fail(`20-icon fixture setup failed: ${JSON.stringify(setup)}`);
    }
    await page.evaluate(() => window.AniDiagramRuntime.play());
    await page.waitForFunction(() => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === 20);
    const measurement = await page.evaluate(() => new Promise((resolve) => {
      const intervals = [];
      const started = performance.now();
      let previous = started;
      const frame = (now) => {
        if (now > previous) intervals.push(now - previous);
        previous = now;
        if (now - started >= 5000) {
          resolve({
            intervals,
            longTasks: window.__DIAGRAM_CORE_LONG_TASKS__ || [],
          });
          return;
        }
        requestAnimationFrame(frame);
      };
      requestAnimationFrame(frame);
    }));
    const sorted = measurement.intervals.slice().sort((left, right) => left - right);
    const p95 = sorted[Math.max(0, Math.ceil(sorted.length * 0.95) - 1)] || 0;
    const runtimeLongTasks = measurement.longTasks.filter((duration) => duration > 50);
    if (runtimeLongTasks.length) {
      fail(`20-icon fixture recorded ${runtimeLongTasks.length} long tasks over 50 ms`);
    }
    if (p95 > 33.3) {
      fail(`20-icon fixture p95 frame time ${p95.toFixed(2)} ms exceeds 33.3 ms`);
    }
    await page.evaluate(() => {
      if (window.__DIAGRAM_CORE_PERF_OBSERVER__) window.__DIAGRAM_CORE_PERF_OBSERVER__.disconnect();
      window.AniDiagramRuntime.stop();
    });
    return { p95, frames: sorted.length };
  } finally {
    await context.close();
  }
}


async function verifyFallback(browser, reducedMotion, suffix, label) {
  const { context, page } = await openPage(browser, reducedMotion, suffix);
  try {
    await verifySemanticBoundary(page);
    const result = await page.evaluate(() => ({
      gsap: Boolean(window.gsap),
      timelines: (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length,
      icons: document.querySelectorAll('[data-icon-presentation="showcase"]').length,
    }));
    if (result.timelines !== 0 || result.icons !== 4) {
      fail(`${label} fallback returned timelines=${result.timelines} icons=${result.icons}`);
    }
    if (suffix && result.gsap) fail("no-GSAP fallback unexpectedly loaded GSAP");
  } finally {
    await context.close();
  }
}


async function main() {
  const browser = await chromium.launch({ headless: true });
  try {
    const { context, page } = await openPage(browser);
    let report;
    try {
      await verifySemanticBoundary(page);
      report = await verifyExpressiveMotion(page);
      await verifyRestAndControls(page);
    } finally {
      await context.close();
    }
    await verifyFallback(browser, "reduce", "", "reduced-motion");
    await verifyFallback(browser, "no-preference", "?no-gsap=1", "no-GSAP");
    await verifyRepeatedInstanceIsolation(browser);
    const performance = await verifyTwentyIconPerformance(browser);
    const peaks = report.map((entry) => entry.icon).join(",");
    process.stdout.write(`icons=4 timelines=4 expressive=${peaks} rest=clean reduced=0 no_gsap=0 repeat=isolated perf20_p95=${performance.p95.toFixed(2)}ms frames=${performance.frames}\nOK\n`);
  } finally {
    await browser.close();
  }
}


main().catch((error) => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 1;
});

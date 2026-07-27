#!/usr/bin/env node
import path from "node:path";
import process from "node:process";
import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";

import { chromium } from "playwright";


const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SHOWCASE_PATH = path.join(REPO_ROOT, "gallery", "diagram-core", "showcase.html");
const CATALOG_PATH = path.join(REPO_ROOT, "assets", "diagram-core", "catalog.json");
const MOTION_CATALOG_PATH = path.join(REPO_ROOT, "runtime", "motion-catalog.json");
const CATALOG_VISUAL_REVIEW_ICONS = Object.freeze(
  JSON.parse(readFileSync(CATALOG_PATH, "utf8")).icons
    .filter((entry) => entry.status === "visual-review")
    .map((entry) => entry.id)
);
const SHOWCASE_DEFINITIONS = Object.freeze(
  JSON.parse(readFileSync(MOTION_CATALOG_PATH, "utf8")).diagram_core_presentations
);
const ICONS = Object.freeze(
  SHOWCASE_DEFINITIONS.map((entry) => entry.icon)
);
const ICON_COUNT = ICONS.length;
const PERFORMANCE_ICON_COUNT = 20;
const OPERATION_TIMEOUT_MS = 10_000;
const AMPLITUDE = Object.freeze({ translation: 4, rotation: 4, scale: 0.08 });


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
  if (boundary.presentations !== ICON_COUNT || boundary.cards !== ICON_COUNT) {
    fail(`expected ${ICON_COUNT} showcase icons, got presentations=${boundary.presentations} cards=${boundary.cards}`);
  }
  if (boundary.states !== 0 || boundary.stateMarks !== 0) {
    fail(`semantic state leaked into v1 review: states=${boundary.states} marks=${boundary.stateMarks}`);
  }
  if (boundary.manifest.profile !== "showcase" || boundary.manifest.icons.length !== ICON_COUNT) {
    fail(`motion manifest does not declare one ${ICON_COUNT}-icon showcase profile`);
  }
  const manifestIcons = boundary.manifest.icons.map((entry) => entry.icon);
  if (JSON.stringify(manifestIcons) !== JSON.stringify(ICONS)) {
    fail(`unexpected manifest icon order: ${manifestIcons.join(",")}`);
  }
  const catalogIcons = [...CATALOG_VISUAL_REVIEW_ICONS].sort();
  const definitionIcons = [...new Set(SHOWCASE_DEFINITIONS.map((entry) => entry.icon))].sort();
  if (JSON.stringify(definitionIcons) !== JSON.stringify(catalogIcons)) {
    fail(`motion catalog visual-review set does not match catalog: ${definitionIcons.join(",")}`);
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
  await page.waitForFunction((count) => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === count, ICON_COUNT);
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
    const rotationLimit = entry.icon === "search" ? 360 : 14;
    if (entry.peaks.rotation > rotationLimit + 0.01) {
      fail(`${entry.icon} rotation peak ${entry.peaks.rotation.toFixed(3)} exceeds ${rotationLimit} degrees`);
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


async function verifySearchCircularWobble(page) {
  const report = await page.evaluate(() => {
    const manifest = JSON.parse(document.getElementById("anidiagram-motion-manifest").textContent);
    const searchIndex = manifest.icons.findIndex((entry) => entry.icon === "search");
    const search = manifest.icons[searchIndex];
    const timeline = window.__ANIDIAGRAM_ICON_TIMELINES__[searchIndex];
    const body = document.querySelector(search.parts.body);
    const lens = document.querySelector(search.parts.lens);
    const handle = document.querySelector(search.parts.handle);
    const expected = [
      [0.06, 0, -4],
      [0.115, 3, -3],
      [0.17, 4, 0],
      [0.225, 3, 3],
      [0.28, 0, 4],
      [0.335, -3, 3],
      [0.39, -4, 0],
      [0.445, -3, -3],
      [0.5, 0, -4],
      [0.58, 0, 0],
    ];
    timeline.pause();
    const samples = expected.map(([time, expectedX, expectedY]) => {
      timeline.seek(time, false);
      const number = (target, property) => Number(window.gsap.getProperty(target, property)) || 0;
      return {
        time,
        expectedX,
        expectedY,
        x: number(body, "x"),
        y: number(body, "y"),
        rotation: number(body, "rotation"),
        lensOwnMotion: Math.max(
          Math.abs(number(lens, "x")),
          Math.abs(number(lens, "y")),
          Math.abs(number(lens, "rotation")),
        ),
        handleOwnMotion: Math.max(
          Math.abs(number(handle, "x")),
          Math.abs(number(handle, "y")),
          Math.abs(number(handle, "rotation")),
        ),
      };
    });
    timeline.seek(timeline.__anidiagramRestAt, false);
    return samples;
  });

  for (const sample of report) {
    if (Math.abs(sample.x - sample.expectedX) > 0.06 || Math.abs(sample.y - sample.expectedY) > 0.06) {
      fail(`search circular wobble deviates at ${sample.time}s: got ${sample.x.toFixed(3)},${sample.y.toFixed(3)}`);
    }
    if (Math.abs(sample.rotation) > 0.01) {
      fail(`search whole body rotates instead of retaining orientation at ${sample.time}s`);
    }
    if (sample.lensOwnMotion > 0.01 || sample.handleOwnMotion > 0.01) {
      fail(`search lens or handle owns separate motion at ${sample.time}s`);
    }
  }
  return report;
}


async function verifyDatabaseLayerWave(page) {
  const report = await page.evaluate(() => {
    const manifest = JSON.parse(document.getElementById("anidiagram-motion-manifest").textContent);
    const databaseIndex = manifest.icons.findIndex((entry) => entry.icon === "database");
    const database = manifest.icons[databaseIndex];
    const timeline = window.__ANIDIAGRAM_ICON_TIMELINES__[databaseIndex];
    const layerNames = ["layerTop", "layerMiddle", "layerBottom"];
    const layers = layerNames.map((name) => document.querySelector(database.parts[name]));
    const samples = Array.from(
      { length: 401 },
      (_, sampleIndex) => timeline.duration() * sampleIndex / 400
    );
    const maxHorizontalShift = [0, 0, 0];
    const verticalPeak = [0, 0, 0];
    const maxVerticalShift = [0, 0, 0];
    const verticalPeakAt = [0, 0, 0];
    const minScaleX = [1, 1, 1];
    const maxScaleX = [1, 1, 1];
    timeline.pause();
    for (const time of samples) {
      timeline.seek(Math.min(time, timeline.duration()), false);
      layers.forEach((layer, index) => {
        const x = Math.abs(Number(window.gsap.getProperty(layer, "x")) || 0);
        const y = Number(window.gsap.getProperty(layer, "y")) || 0;
        const scaleX = Number(window.gsap.getProperty(layer, "scaleX")) || 1;
        maxHorizontalShift[index] = Math.max(maxHorizontalShift[index], x);
        maxVerticalShift[index] = Math.max(maxVerticalShift[index], y);
        minScaleX[index] = Math.min(minScaleX[index], scaleX);
        maxScaleX[index] = Math.max(maxScaleX[index], scaleX);
        if (y < verticalPeak[index]) {
          verticalPeak[index] = y;
          verticalPeakAt[index] = time;
        }
      });
    }
    timeline.seek(timeline.duration(), false);
    const finalPose = layers.map((layer) => ({
      x: Number(window.gsap.getProperty(layer, "x")) || 0,
      y: Number(window.gsap.getProperty(layer, "y")) || 0,
      scaleX: Number(window.gsap.getProperty(layer, "scaleX")) || 1,
    }));
    return {
      layerNames,
      maxHorizontalShift,
      verticalPeak,
      maxVerticalShift,
      verticalPeakAt,
      minScaleX,
      maxScaleX,
      finalPose,
    };
  });
  if (report.maxHorizontalShift.some((value) => value > 0.001)) {
    fail(`database separator layers drift horizontally: ${report.maxHorizontalShift.join(",")}`);
  }
  if (report.verticalPeak.some((value) => value < -2.1 || value > -1.5)
      || report.maxVerticalShift.some((value) => value > 0.001)) {
    fail(`database separator layer wave amplitude is out of bounds: ${report.verticalPeak.join(",")}`);
  }
  if (report.minScaleX.some((value) => value < 0.93 || value > 0.95)
      || report.maxScaleX.some((value) => value < 1.03 || value > 1.05)) {
    fail(`database separator layer scale wave is out of bounds: min=${report.minScaleX.join(",")} max=${report.maxScaleX.join(",")}`);
  }
  if (!(report.verticalPeakAt[0] < report.verticalPeakAt[1]
      && report.verticalPeakAt[1] < report.verticalPeakAt[2])) {
    fail(`database separator layer wave is not top-to-bottom: ${report.verticalPeakAt.join(",")}`);
  }
  if (report.finalPose.some(({ x, y, scaleX }) => (
    Math.abs(x) > 0.001 || Math.abs(y) > 0.001 || Math.abs(scaleX - 1) > 0.001
  ))) {
    fail(`database separator layers do not restore authored rest: ${JSON.stringify(report.finalPose)}`);
  }
  return report;
}


async function verifyDeclarativeRecipePolicy(browser) {
  const { context, page } = await openPage(browser);
  try {
    await page.waitForFunction((count) => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === count, ICON_COUNT);
    const report = await page.evaluate(() => {
      window.AniDiagramRuntime.stop();
      const manifestElement = document.getElementById("anidiagram-motion-manifest");
      const sourceManifest = JSON.parse(manifestElement.textContent);
      const original = sourceManifest.icons[0];
      const secondIcon = sourceManifest.icons[1];
      const bodyName = Object.prototype.hasOwnProperty.call(original.parts, "body")
        ? "body"
        : Object.keys(original.parts)[0];
      const body = document.querySelector(original.parts[bodyName]);
      const initialOpacity = Number(window.gsap.getProperty(body, "opacity"));
      const base = {
        ...original,
        performance: "__declarative-recipe-policy-test__",
        rest_at: 0.4,
        repeat_delay: 1,
        duration_ms: 667,
        recipe: {
          tracks: [{
            parts: [bodyName],
            steps: [{
              to: { y: -5, opacity: 0.45 },
              duration: 0.18,
              ease: "power2.out",
              at: 0,
            }],
          }],
        },
      };
      const run = (entry) => {
        window.AniDiagramRuntime.stop();
        manifestElement.textContent = JSON.stringify({
          version: "recipe-policy-test",
          mode: "ambient",
          profile: "showcase",
          icon_system: "diagram-core-v1",
          icons: [entry],
          edges: [],
          groups: [],
        });
        window.AniDiagramRuntime.play();
        return (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length;
      };
      const runBoundaryAttack = (entry) => {
        window.AniDiagramRuntime.stop();
        const bodyStyle = document.body.getAttribute("style");
        const bodyTransform = document.body.getAttribute("transform");
        const bodyComputedTransform = getComputedStyle(document.body).transform;
        manifestElement.textContent = JSON.stringify({
          version: "recipe-boundary-policy-test",
          mode: "ambient",
          profile: "showcase",
          icon_system: "diagram-core-v1",
          icons: [entry],
          edges: [],
          groups: [],
        });
        let error = null;
        try {
          window.AniDiagramRuntime.play();
          const timeline = (window.__ANIDIAGRAM_ICON_TIMELINES__ || [])[0];
          if (timeline) {
            timeline.pause();
            timeline.seek(Math.min(0.18, timeline.duration()), false);
          }
        } catch (caught) {
          error = `${caught.name}: ${caught.message}`;
        }
        const result = {
          timelines: (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length,
          error,
          bodyStyleChanged: document.body.getAttribute("style") !== bodyStyle,
          bodyTransformChanged: document.body.getAttribute("transform") !== bodyTransform,
          bodyComputedTransformChanged: getComputedStyle(document.body).transform !== bodyComputedTransform,
        };
        try {
          window.AniDiagramRuntime.stop();
        } catch (caught) {
          result.error = result.error || `${caught.name}: ${caught.message}`;
        }
        window.gsap.set(document.body, { clearProps: "all" });
        if (bodyStyle === null) document.body.removeAttribute("style");
        else document.body.setAttribute("style", bodyStyle);
        if (bodyTransform === null) document.body.removeAttribute("transform");
        else document.body.setAttribute("transform", bodyTransform);
        return result;
      };
      const validCount = run(base);
      const timeline = window.__ANIDIAGRAM_ICON_TIMELINES__[0];
      timeline.pause();
      timeline.seek(0.18, false);
      const activeY = Number(window.gsap.getProperty(body, "y"));
      const activeOpacity = Number(window.gsap.getProperty(body, "opacity"));
      timeline.seek(timeline.duration(), false);
      const restY = Number(window.gsap.getProperty(body, "y"));
      const restOpacity = Number(window.gsap.getProperty(body, "opacity"));

      const missingRecipe = { ...base };
      delete missingRecipe.recipe;
      const illegalProperty = JSON.parse(JSON.stringify(base));
      illegalProperty.recipe.tracks[0].steps[0].to.filter = 3;
      const illegalEase = JSON.parse(JSON.stringify(base));
      illegalEase.recipe.tracks[0].steps[0].ease = "steps(1)";
      const missingPart = JSON.parse(JSON.stringify(base));
      missingPart.recipe.tracks[0].parts = ["not-declared"];
      const beyondRest = JSON.parse(JSON.stringify(base));
      beyondRest.recipe.tracks[0].steps[0].at = 0.3;
      beyondRest.recipe.tracks[0].steps[0].duration = 0.2;
      const extraField = JSON.parse(JSON.stringify(base));
      extraField.recipe.tracks[0].steps[0].onComplete = "unsafe";
      const duplicateTrackTarget = JSON.parse(JSON.stringify(base));
      duplicateTrackTarget.parts.bodyAlias = duplicateTrackTarget.parts[bodyName];
      const duplicateTargetTrack = JSON.parse(
        JSON.stringify(duplicateTrackTarget.recipe.tracks[0])
      );
      duplicateTargetTrack.parts = ["bodyAlias"];
      duplicateTrackTarget.recipe.tracks.push(duplicateTargetTrack);
      const foreignSelector = JSON.parse(JSON.stringify(base));
      foreignSelector.parts = { evil: "body" };
      foreignSelector.recipe.tracks[0].parts = ["evil"];
      const prototypePart = JSON.parse(JSON.stringify(base));
      prototypePart.parts = JSON.parse(`{"__proto__":${JSON.stringify(original.parts[bodyName])}}`);
      prototypePart.recipe.tracks[0].parts = ["__proto__"];
      const malformedSelector = JSON.parse(JSON.stringify(base));
      malformedSelector.parts = { evil: "[" };
      malformedSelector.recipe.tracks[0].parts = ["evil"];
      const malformedRootSelector = JSON.parse(JSON.stringify(base));
      malformedRootSelector.root = "[";
      const crossInstance = JSON.parse(JSON.stringify(base));
      crossInstance.parts = {
        anchor: original.parts[bodyName],
        evil: secondIcon.parts.body,
      };
      crossInstance.recipe.tracks[0].parts = ["evil"];
      return {
        validCount,
        activeY,
        activeOpacity,
        initialOpacity,
        restY,
        restOpacity,
        invalidCounts: [
          run(missingRecipe),
          run(illegalProperty),
          run(illegalEase),
          run(missingPart),
          run(beyondRest),
          run(extraField),
          run(duplicateTrackTarget),
        ],
        boundaryAttacks: {
          foreignSelector: runBoundaryAttack(foreignSelector),
          prototypePart: runBoundaryAttack(prototypePart),
          malformedSelector: runBoundaryAttack(malformedSelector),
          malformedRootSelector: runBoundaryAttack(malformedRootSelector),
          crossInstance: runBoundaryAttack(crossInstance),
        },
      };
    });
    if (report.validCount !== 1 || report.activeY > -4.5 || report.activeOpacity > 0.5) {
      fail(`valid declarative recipe did not animate once: ${JSON.stringify(report)}`);
    }
    if (Math.abs(report.restY) > 0.001 || Math.abs(report.restOpacity - report.initialOpacity) > 0.001) {
      fail(`declarative recipe did not restore authored rest: ${JSON.stringify(report)}`);
    }
    const boundaryFailures = Object.entries(report.boundaryAttacks).filter(([, entry]) => (
      entry.timelines !== 0
      || entry.error !== null
      || entry.bodyStyleChanged
      || entry.bodyTransformChanged
      || entry.bodyComputedTransformChanged
    ));
    if (boundaryFailures.length) {
      fail(`declarative recipe selector boundary did not fail closed: ${JSON.stringify(boundaryFailures)}`);
    }
    if (report.invalidCounts.some((count) => count !== 0)) {
      fail(`missing or illegal declarative recipe did not fail closed: ${report.invalidCounts.join(",")}`);
    }
    return report;
  } finally {
    await context.close();
  }
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
  await page.waitForFunction((count) => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === count, ICON_COUNT);
  await page.getByRole("button", { name: "Off" }).click();
  await assertRest("Off");
  const off = await page.evaluate(() => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length);
  if (off !== 0) fail(`Off left ${off} icon timelines`);

  await page.getByRole("button", { name: "Showcase" }).click();
  await page.waitForFunction((count) => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === count, ICON_COUNT);
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
    await page.waitForFunction((count) => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === count, ICON_COUNT);
    await page.evaluate(() => window.AniDiagramRuntime.stop());
    const setup = await page.evaluate(() => {
      const manifestElement = document.getElementById("anidiagram-motion-manifest");
      const manifest = JSON.parse(manifestElement.textContent);
      manifest.icons = manifest.icons.flatMap((original) => {
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
        clone.setAttribute("data-repeat-fixture", original.icon);
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
        return [original, duplicate];
      });
      manifestElement.textContent = JSON.stringify(manifest);
      const ids = [...document.querySelectorAll("[id]")].map((element) => element.id);
      return { duplicateIds: ids.length - new Set(ids).size, entries: manifest.icons.length };
    });
    if (setup.duplicateIds !== 0) fail(`repeat fixture created ${setup.duplicateIds} duplicate DOM ids`);
    if (setup.entries !== ICON_COUNT * 2) fail(`repeat fixture expected ${ICON_COUNT * 2} entries, got ${setup.entries}`);

    await page.evaluate(() => {
      window.AniDiagramRuntime.play();
    });
    await page.waitForFunction((count) => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === count, ICON_COUNT * 2);
    const isolationJson = await page.evaluate(() => {
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
      const movingTime = (timeline, entry) => {
        for (let sample = 1; sample <= 100; sample += 1) {
          const time = timeline.duration() * sample / 100;
          timeline.seek(time, false);
          if (moving(entry)) return time;
        }
        return null;
      };
      const results = [];
      for (let pairIndex = 0; pairIndex < entries.length; pairIndex += 2) {
        const firstTime = movingTime(timelines[pairIndex], entries[pairIndex]);
        const secondTime = movingTime(timelines[pairIndex + 1], entries[pairIndex + 1]);
        timelines.forEach((timeline) => timeline.seek(0, false));
        if (secondTime !== null) timelines[pairIndex + 1].seek(secondTime, false);
        const secondOnly = !moving(entries[pairIndex]) && moving(entries[pairIndex + 1]);
        timelines.forEach((timeline) => timeline.seek(0, false));
        if (firstTime !== null) timelines[pairIndex].seek(firstTime, false);
        const firstOnly = moving(entries[pairIndex]) && !moving(entries[pairIndex + 1]);
        results.push({ icon: entries[pairIndex].icon, firstOnly, secondOnly, firstTime, secondTime });
      }
      return JSON.stringify(results);
    });
    const isolation = JSON.parse(isolationJson);
    if (isolation.length !== ICON_COUNT) {
      fail(`repeat isolation expected ${ICON_COUNT} per-icon results, got ${isolation.length}`);
    }
    const failures = isolation.filter((entry) => !entry.firstOnly || !entry.secondOnly);
    if (failures.length) {
      fail(`repeated icon instances are not isolated: ${JSON.stringify(failures)}`);
    }
    await page.evaluate(() => window.AniDiagramRuntime.stop());
  } finally {
    await context.close();
  }
}


async function verifyTwentyIconPerformance(browser) {
  const { context, page } = await openPage(browser);
  try {
    await page.waitForFunction((count) => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === count, ICON_COUNT);
    await page.evaluate(() => window.AniDiagramRuntime.stop());
    const setup = await page.evaluate((fixtureCount) => {
      const manifestElement = document.getElementById("anidiagram-motion-manifest");
      const manifest = JSON.parse(manifestElement.textContent);
      const originals = manifest.icons;
      const entries = [];
      for (let fixtureIndex = 0; fixtureIndex < fixtureCount; fixtureIndex += 1) {
        const original = originals[fixtureIndex % originals.length];
        if (fixtureIndex < originals.length) {
          entries.push(original);
          continue;
        }
        const originalRoot = document.querySelector(`[data-icon="${original.icon}"][data-icon-presentation="showcase"]`);
        const clone = originalRoot.cloneNode(true);
        const suffix = `__perf${fixtureIndex}`;
        const idMap = new Map();
        for (const element of [clone, ...clone.querySelectorAll("[id]")]) {
          if (!element.id) continue;
          const previous = element.id;
          const next = `${previous}${suffix}`;
          idMap.set(previous, next);
          element.id = next;
        }
        clone.setAttribute("data-performance-fixture", String(fixtureIndex));
        originalRoot.parentNode.appendChild(clone);
        const duplicate = JSON.parse(JSON.stringify(original));
        duplicate.node_id = `${original.node_id}-perf-${fixtureIndex}`;
        duplicate.delay = (fixtureIndex % 4) * 0.08;
        duplicate.parts = Object.fromEntries(
          Object.entries(original.parts).map(([name, selector]) => [
            name,
            `#${idMap.get(selector.slice(1))}`,
          ])
        );
        entries.push(duplicate);
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
    }, PERFORMANCE_ICON_COUNT);
    if (setup.entries !== PERFORMANCE_ICON_COUNT || setup.duplicateIds !== 0) {
      fail(`20-icon fixture setup failed: ${JSON.stringify(setup)}`);
    }
    await page.evaluate(() => window.AniDiagramRuntime.play());
    await page.waitForFunction((count) => (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).length === count, PERFORMANCE_ICON_COUNT);
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
    if (result.timelines !== 0 || result.icons !== ICON_COUNT) {
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
    let databaseLayerWave;
    let searchCircularWobble;
    try {
      await verifySemanticBoundary(page);
      report = await verifyExpressiveMotion(page);
      searchCircularWobble = await verifySearchCircularWobble(page);
      databaseLayerWave = await verifyDatabaseLayerWave(page);
      await verifyRestAndControls(page);
    } finally {
      await context.close();
    }
    await verifyFallback(browser, "reduce", "", "reduced-motion");
    await verifyFallback(browser, "no-preference", "?no-gsap=1", "no-GSAP");
    await verifyDeclarativeRecipePolicy(browser);
    await verifyRepeatedInstanceIsolation(browser);
    const performance = await verifyTwentyIconPerformance(browser);
    const peaks = report.map((entry) => entry.icon).join(",");
    const databaseLayerOrder = databaseLayerWave.layerNames.join(">");
    process.stdout.write(`icons=${ICON_COUNT} timelines=${ICON_COUNT} expressive=${peaks} recipe=allowlisted-fail-closed recipe_targets=unique selectors=instance-scoped search_path=clockwise-circle search_samples=${searchCircularWobble.length} database_layers=${databaseLayerOrder} database_layer_x=0 rest=clean reduced=0 no_gsap=0 repeat=isolated-all perf20_p95=${performance.p95.toFixed(2)}ms frames=${performance.frames}\nOK\n`);
  } finally {
    await browser.close();
  }
}


main().catch((error) => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 1;
});

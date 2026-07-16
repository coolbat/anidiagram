#!/usr/bin/env node
import { createHash, randomBytes } from "node:crypto";
import {
  chmod,
  lstat,
  mkdir,
  open,
  readFile,
  realpath,
  rename,
  rm,
  stat,
} from "node:fs/promises";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

import { chromium } from "playwright";


const LOCATOR = "#diagram-core-regression-grid";
const EXPECTED_CELLS = 288;
const EXPECTED_WIDTH = 1248;
const EXPECTED_HEIGHT = 2496;
const VIEWPORT = Object.freeze({ width: 1280, height: 900 });
const DEVICE_SCALE_FACTOR = 1;
const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);
const PLAYWRIGHT_VERSION = require("playwright/package.json").version;
const SOURCE_ASSET_PATHS = Object.freeze(
  [
    "assets/diagram-core/catalog.json",
    "assets/diagram-core/tokens.css",
    ...["agent", "api", "database", "server"].flatMap((iconId) => [
      `assets/diagram-core/icons/${iconId}.svg`,
      `assets/diagram-core/manifests/${iconId}.json`,
    ]),
  ].sort(),
);
const CAPTURE_STYLE = `
*, *::before, *::after {
  animation: none !important;
  animation-delay: 0s !important;
  animation-duration: 0s !important;
  transition: none !important;
  transition-delay: 0s !important;
  transition-duration: 0s !important;
  caret-color: transparent !important;
}
#diagram-core-regression-grid {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
}
`;


class UsageError extends Error {}


function usage() {
  return [
    "Usage: node scripts/capture_diagram_core_contact_sheet.mjs \\",
    "  --input gallery/diagram-core/index.html \\",
    "  --output build/diagram-core/benchmark.local.png \\",
    "  --metadata build/diagram-core/benchmark.local.capture.json",
  ].join("\n");
}


function parseArguments(argumentsList) {
  const values = new Map();
  const allowed = new Set(["--input", "--output", "--metadata"]);
  for (let index = 0; index < argumentsList.length; index += 2) {
    const option = argumentsList[index];
    const value = argumentsList[index + 1];
    if (!allowed.has(option) || value === undefined || value.startsWith("--")) {
      throw new UsageError(`invalid arguments\n${usage()}`);
    }
    if (values.has(option)) {
      throw new UsageError(`duplicate option: ${option}\n${usage()}`);
    }
    values.set(option, value);
  }
  for (const option of allowed) {
    if (!values.has(option)) {
      throw new UsageError(`missing required option: ${option}\n${usage()}`);
    }
  }
  return {
    input: path.resolve(REPO_ROOT, values.get("--input")),
    output: path.resolve(REPO_ROOT, values.get("--output")),
    metadata: path.resolve(REPO_ROOT, values.get("--metadata")),
  };
}


function sha256(payload) {
  return createHash("sha256").update(payload).digest("hex");
}


async function exists(target) {
  try {
    await lstat(target);
    return true;
  } catch (error) {
    if (error && error.code === "ENOENT") return false;
    throw error;
  }
}


async function assertNoSymlinkComponents(target) {
  const absolute = path.resolve(target);
  const parsed = path.parse(absolute);
  let current = parsed.root;
  for (const part of absolute.slice(parsed.root.length).split(path.sep).filter(Boolean)) {
    current = path.join(current, part);
    try {
      const info = await lstat(current);
      if (info.isSymbolicLink()) {
        throw new Error(`symlink path is not permitted: ${target}`);
      }
    } catch (error) {
      if (error && error.code === "ENOENT") continue;
      throw error;
    }
  }
}


async function requireRegularFile(target, label) {
  await assertNoSymlinkComponents(target);
  let info;
  try {
    info = await stat(target);
  } catch (error) {
    if (error && error.code === "ENOENT") {
      throw new Error(`${label} does not exist: ${target}`);
    }
    throw error;
  }
  if (!info.isFile()) throw new Error(`${label} must be a regular file: ${target}`);
  return info;
}


async function prepareOutput(target) {
  await assertNoSymlinkComponents(target);
  await mkdir(path.dirname(target), { recursive: true });
  await assertNoSymlinkComponents(path.dirname(target));
  if (await exists(target)) {
    const info = await stat(target);
    if (!info.isFile()) throw new Error(`output must be a regular file: ${target}`);
  }
}


async function pathsAlias(left, right) {
  if (path.resolve(left) === path.resolve(right)) return true;
  if (!(await exists(left)) || !(await exists(right))) return false;
  const [leftInfo, rightInfo] = await Promise.all([stat(left), stat(right)]);
  return leftInfo.dev === rightInfo.dev && leftInfo.ino === rightInfo.ino;
}


async function rejectAliases(entries) {
  for (let leftIndex = 0; leftIndex < entries.length; leftIndex += 1) {
    for (let rightIndex = leftIndex + 1; rightIndex < entries.length; rightIndex += 1) {
      if (await pathsAlias(entries[leftIndex][1], entries[rightIndex][1])) {
        throw new Error(
          `path alias is not permitted: ${entries[leftIndex][0]} and ${entries[rightIndex][0]}`,
        );
      }
    }
  }
}


async function stagePayload(target, payload, mode = 0o644) {
  const temporary = path.join(
    path.dirname(target),
    `.${path.basename(target)}.${process.pid}.${randomBytes(8).toString("hex")}.tmp`,
  );
  let handle;
  let completed = false;
  try {
    handle = await open(temporary, "wx", 0o600);
    await handle.writeFile(payload);
    await handle.sync();
    await handle.close();
    handle = undefined;
    await chmod(temporary, mode);
    completed = true;
    return temporary;
  } finally {
    if (handle) await handle.close().catch(() => {});
    if (!completed) await rm(temporary, { force: true }).catch(() => {});
  }
}


async function snapshotTarget(target) {
  if (!(await exists(target))) return null;
  await assertNoSymlinkComponents(target);
  const info = await stat(target);
  if (!info.isFile()) throw new Error(`output must be a regular file: ${target}`);
  const payload = await readFile(target);
  return { payload, mode: info.mode & 0o777, sha256: sha256(payload) };
}


async function restorePublishedEntry(entry, replace) {
  const current = await snapshotTarget(entry.target);
  const oldDigest = entry.snapshot && entry.snapshot.sha256;
  if (current && current.sha256 === entry.newDigest) {
    if (entry.snapshot === null) {
      await rm(entry.target);
      return;
    }
    const rollbackStage = await stagePayload(
      entry.target,
      entry.snapshot.payload,
      entry.snapshot.mode,
    );
    try {
      await replace(rollbackStage, entry.target);
    } finally {
      await rm(rollbackStage, { force: true }).catch(() => {});
    }
    return;
  }
  if (current === null && entry.snapshot === null) return;
  if (current && oldDigest && current.sha256 === oldDigest) return;
  throw new Error(`rollback conflict at ${entry.target}`);
}


export async function publishCapture(entries, replace = rename) {
  if (!Array.isArray(entries) || entries.length !== 2) {
    throw new Error("capture publish requires exactly image and metadata entries");
  }
  await rejectAliases(entries.map((entry, index) => [`capture output ${index}`, entry.target]));
  await Promise.all(entries.map((entry) => prepareOutput(entry.target)));
  const staged = [];
  try {
    for (const entry of entries) {
      const payload = Buffer.from(entry.payload);
      const snapshot = await snapshotTarget(entry.target);
      const temporary = await stagePayload(entry.target, payload);
      staged.push({
        target: entry.target,
        snapshot,
        temporary,
        attempted: false,
        newDigest: sha256(payload),
      });
    }
    for (const entry of staged) {
      entry.attempted = true;
      await replace(entry.temporary, entry.target);
      entry.temporary = null;
    }
  } catch (error) {
    const rollbackErrors = [];
    for (const entry of [...staged].reverse()) {
      if (!entry.attempted) continue;
      try {
        await restorePublishedEntry(entry, replace);
      } catch (rollbackError) {
        rollbackErrors.push(rollbackError.message);
      }
    }
    if (rollbackErrors.length !== 0) {
      throw new Error(
        `capture publish failed and rollback was incomplete: ${rollbackErrors.join("; ")}`,
        { cause: error },
      );
    }
    throw error;
  } finally {
    await Promise.all(
      staged
        .filter((entry) => entry.temporary)
        .map((entry) => rm(entry.temporary, { force: true }).catch(() => {})),
    );
  }
}


function relativeRepoPath(target) {
  const relative = path.relative(REPO_ROOT, target).split(path.sep).join("/");
  if (relative === ".." || relative.startsWith("../") || path.isAbsolute(relative)) {
    throw new Error(`path must remain inside repository: ${target}`);
  }
  return relative;
}


async function canonicalSourceAssets() {
  const files = [];
  for (const relativePath of SOURCE_ASSET_PATHS) {
    const absolutePath = path.join(REPO_ROOT, relativePath);
    await requireRegularFile(absolutePath, `canonical source asset ${relativePath}`);
    const payload = await readFile(absolutePath);
    files.push({ path: relativePath, sha256: sha256(payload) });
  }
  const joint = createHash("sha256");
  for (const file of files) {
    joint.update(file.path, "utf8");
    joint.update("\0", "utf8");
    joint.update(file.sha256, "ascii");
    joint.update("\n", "utf8");
  }
  return { files, joint_sha256: joint.digest("hex") };
}


function pngDimensions(payload) {
  const signature = "89504e470d0a1a0a";
  if (payload.length < 24 || payload.subarray(0, 8).toString("hex") !== signature) {
    throw new Error("Playwright screenshot is not a valid PNG");
  }
  return { width: payload.readUInt32BE(16), height: payload.readUInt32BE(20) };
}


async function computedMotionCounts(locator) {
  return locator.evaluate((root) => {
    const hasPositiveTime = (source) => source
      .split(",")
      .map((value) => value.trim())
      .some((value) => {
        if (value.endsWith("ms")) return Number.parseFloat(value) > 0;
        if (value.endsWith("s")) return Number.parseFloat(value) > 0;
        return false;
      });
    const elements = [root, ...root.querySelectorAll("*")];
    let animationCount = document
      .getAnimations({ subtree: true })
      .filter((animation) => {
        const target = animation.effect && animation.effect.target;
        return target === root || (target instanceof Node && root.contains(target));
      }).length;
    let transitionCount = 0;
    for (const element of elements) {
      const style = getComputedStyle(element);
      const animationsDeclared = style.animationName
        .split(",")
        .some((name) => name.trim() !== "none") && hasPositiveTime(style.animationDuration);
      if (animationsDeclared) animationCount += 1;
      if (hasPositiveTime(style.transitionDuration)) transitionCount += 1;
    }
    return { animationCount, transitionCount };
  });
}


async function capture(paths) {
  await requireRegularFile(paths.input, "input HTML");
  await rejectAliases([
    ["input", paths.input],
    ["output", paths.output],
    ["metadata", paths.metadata],
  ]);
  await Promise.all([prepareOutput(paths.output), prepareOutput(paths.metadata)]);
  const canonicalInput = await realpath(paths.input);
  relativeRepoPath(canonicalInput);
  const inputPayload = await readFile(canonicalInput);
  const sourceAssets = await canonicalSourceAssets();
  const externalRequests = new Set();
  const canonicalInputUrl = pathToFileURL(canonicalInput).href;
  const browser = await chromium.launch({ headless: true });
  let context;
  try {
    context = await browser.newContext({
      viewport: VIEWPORT,
      deviceScaleFactor: 1,
      reducedMotion: "reduce",
      serviceWorkers: "block",
    });
    const page = await context.newPage();
    const isAllowedMainNavigation = (request) => request.url() === canonicalInputUrl
      && request.isNavigationRequest()
      && request.frame() === page.mainFrame();
    page.on("request", (request) => {
      if (!isAllowedMainNavigation(request)) externalRequests.add(request.url());
    });
    await page.route("**/*", async (route) => {
      if (isAllowedMainNavigation(route.request())) {
        await route.continue();
        return;
      }
      externalRequests.add(route.request().url());
      await route.abort("blockedbyclient");
    });
    await page.goto(canonicalInputUrl, { waitUntil: "load" });
    const embeddedResourceUrls = await page.evaluate(() => {
      const resources = [
        ["img", "src"],
        ["script", "src"],
        ["link", "href"],
        ["iframe", "src"],
        ["audio", "src"],
        ["video", "src"],
        ["source", "src"],
        ["object", "data"],
        ["embed", "src"],
        ["image", "href"],
        ["use", "href"],
      ];
      const urls = [];
      for (const [tag, attribute] of resources) {
        for (const element of document.querySelectorAll(`${tag}[${attribute}]`)) {
          const value = element.getAttribute(attribute);
          if (!value || value.startsWith("#")) continue;
          urls.push(new URL(value, document.baseURI).href);
        }
      }
      const appendCssUrls = (source) => {
        const expression = /url\(\s*(["']?)(.*?)\1\s*\)/giu;
        for (const match of source.matchAll(expression)) {
          const value = match[2].trim();
          if (!value || value.startsWith("#")) continue;
          urls.push(new URL(value, document.baseURI).href);
        }
        const importExpression = /@import\s+(["'])(.*?)\1/giu;
        for (const match of source.matchAll(importExpression)) {
          const value = match[2].trim();
          if (!value || value.startsWith("#")) continue;
          urls.push(new URL(value, document.baseURI).href);
        }
      };
      for (const style of document.querySelectorAll("style")) {
        appendCssUrls(style.textContent || "");
      }
      for (const element of document.querySelectorAll("[style]")) {
        appendCssUrls(element.getAttribute("style") || "");
      }
      return urls;
    });
    for (const resourceUrl of embeddedResourceUrls) {
      if (resourceUrl !== canonicalInputUrl) externalRequests.add(resourceUrl);
    }
    if (externalRequests.size !== 0) {
      throw new Error(`external requests are forbidden: ${[...externalRequests].join(", ")}`);
    }
    await page.addStyleTag({ content: CAPTURE_STYLE });
    await page.evaluate(async () => {
      await document.fonts.ready;
      await new Promise((resolve) => requestAnimationFrame(() => resolve()));
      await new Promise((resolve) => requestAnimationFrame(() => resolve()));
    });

    const locator = page.locator(LOCATOR);
    const locatorCount = await locator.count();
    if (locatorCount !== 1) {
      throw new Error(`${LOCATOR} must match exactly once; found ${locatorCount}`);
    }
    const cells = await locator.locator('[data-cell-kind="regression"]').count();
    if (cells !== EXPECTED_CELLS) {
      throw new Error(`regression grid must contain ${EXPECTED_CELLS} cells; found ${cells}`);
    }
    const boundingBox = await locator.boundingBox();
    if (!boundingBox) throw new Error(`${LOCATOR} has no visible bounding box`);
    if (boundingBox.width !== EXPECTED_WIDTH || boundingBox.height !== EXPECTED_HEIGHT) {
      throw new Error(
        `regression grid dimensions must be ${EXPECTED_WIDTH}x${EXPECTED_HEIGHT}; `
        + `found ${boundingBox.width}x${boundingBox.height}`,
      );
    }
    const motion = await computedMotionCounts(locator);
    if (motion.animationCount !== 0 || motion.transitionCount !== 0) {
      throw new Error(
        `capture surface still has motion: animations=${motion.animationCount} `
        + `transitions=${motion.transitionCount}`,
      );
    }
    if (externalRequests.size !== 0) {
      throw new Error(`external requests are forbidden: ${[...externalRequests].join(", ")}`);
    }

    const screenshot = await locator.screenshot({ type: "png", animations: "disabled" });
    if (externalRequests.size !== 0) {
      throw new Error(`external requests are forbidden: ${[...externalRequests].join(", ")}`);
    }
    const dimensions = pngDimensions(screenshot);
    if (dimensions.width !== EXPECTED_WIDTH || dimensions.height !== EXPECTED_HEIGHT) {
      throw new Error(
        `screenshot dimensions must be ${EXPECTED_WIDTH}x${EXPECTED_HEIGHT}; `
        + `found ${dimensions.width}x${dimensions.height}`,
      );
    }
    const chromiumVersion = browser.version();
    const captureTimestamp = new Date().toISOString();
    const imageDigest = sha256(screenshot);
    const metadata = {
      schema: "anidiagram.diagram-core.capture",
      version: 1,
      browser: {
        playwright_version: PLAYWRIGHT_VERSION,
        chromium_version: chromiumVersion,
      },
      platform: { os: os.platform(), arch: os.arch() },
      viewport: {
        width: VIEWPORT.width,
        height: VIEWPORT.height,
        device_scale_factor: DEVICE_SCALE_FACTOR,
      },
      locator: {
        selector: LOCATOR,
        bounding_box: {
          x: boundingBox.x,
          y: boundingBox.y,
          width: boundingBox.width,
          height: boundingBox.height,
        },
        cells,
      },
      capture: {
        timestamp_utc: captureTimestamp,
        external_requests: externalRequests.size,
        external_request_urls: [...externalRequests].sort(),
        animation_count: motion.animationCount,
        transition_count: motion.transitionCount,
      },
      input: {
        path: relativeRepoPath(canonicalInput),
        sha256: sha256(inputPayload),
      },
      image: {
        path: relativeRepoPath(paths.output),
        sha256: imageDigest,
        width: dimensions.width,
        height: dimensions.height,
      },
      source_assets: sourceAssets,
    };
    await publishCapture([
      { target: paths.output, payload: screenshot },
      {
        target: paths.metadata,
        payload: Buffer.from(`${JSON.stringify(metadata, null, 2)}\n`, "utf8"),
      },
    ]);
    return { cells, requests: externalRequests.size, animations: motion.animationCount, metadata };
  } finally {
    if (context) await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}


async function main() {
  const paths = parseArguments(process.argv.slice(2));
  const result = await capture(paths);
  process.stdout.write(
    `cells=${result.cells} dpr=${DEVICE_SCALE_FACTOR} requests=${result.requests} `
    + `animations=${result.animations}\n`,
  );
}


const invokedAsScript = process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
if (invokedAsScript) {
  try {
    await main();
  } catch (error) {
    process.stderr.write(`error: ${error.message}\n`);
    process.exitCode = error instanceof UsageError ? 2 : 1;
  }
}

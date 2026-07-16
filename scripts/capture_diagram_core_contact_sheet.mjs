#!/usr/bin/env node
import { createHash, randomBytes } from "node:crypto";
import { constants as fsConstants } from "node:fs";
import {
  chmod,
  lstat,
  mkdir,
  open,
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
const PLAYWRIGHT_OPERATION_TIMEOUT_MS = 10_000;
const CLOSE_TIMEOUT_MS = 5_000;
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


function fileSignature(info) {
  return [
    info.dev,
    info.ino,
    info.size,
    info.mtimeNs,
    info.ctimeNs,
    info.mode,
  ].map((value) => value.toString()).join(":");
}


function replacementSignature(info) {
  return [
    info.dev,
    info.ino,
    info.size,
    info.mtimeNs,
    info.mode,
  ].map((value) => value.toString()).join(":");
}


async function readFileSnapshot(target, label) {
  await assertNoSymlinkComponents(target);
  let handle;
  try {
    const flags = fsConstants.O_RDONLY | (fsConstants.O_NOFOLLOW || 0);
    handle = await open(target, flags);
    const before = await handle.stat({ bigint: true });
    if ((before.mode & BigInt(fsConstants.S_IFMT)) !== BigInt(fsConstants.S_IFREG)) {
      throw new Error(`${label} must be a regular file: ${target}`);
    }
    const payload = await handle.readFile();
    const after = await handle.stat({ bigint: true });
    if (fileSignature(before) !== fileSignature(after) || BigInt(payload.length) !== after.size) {
      throw new Error(`${label} changed while it was read: ${target}`);
    }
    const current = await lstat(target, { bigint: true });
    if (current.isSymbolicLink() || fileSignature(current) !== fileSignature(after)) {
      throw new Error(`${label} changed while it was read: ${target}`);
    }
    return {
      path: target,
      payload,
      mode: Number(after.mode & BigInt(0o777)),
      signature: fileSignature(after),
      replacementSignature: replacementSignature(after),
    };
  } catch (error) {
    if (error && error.code === "ENOENT") {
      throw new Error(`${label} does not exist: ${target}`);
    }
    throw error;
  } finally {
    if (handle) await handle.close().catch(() => {});
  }
}


async function assertSnapshotCurrent(snapshot, label) {
  await assertNoSymlinkComponents(snapshot.path);
  let current;
  try {
    current = await lstat(snapshot.path, { bigint: true });
  } catch (error) {
    throw new Error(`${label} changed during capture: ${snapshot.path}`, { cause: error });
  }
  if (current.isSymbolicLink() || fileSignature(current) !== snapshot.signature) {
    throw new Error(`${label} changed during capture: ${snapshot.path}`);
  }
}


async function withTimeout(operation, label, timeoutMs = PLAYWRIGHT_OPERATION_TIMEOUT_MS) {
  let timeoutId;
  try {
    return await Promise.race([
      Promise.resolve().then(operation),
      new Promise((resolve, reject) => {
        timeoutId = setTimeout(
          () => reject(new Error(`${label} timed out after ${timeoutMs}ms`)),
          timeoutMs,
        );
      }),
    ]);
  } finally {
    if (timeoutId !== undefined) clearTimeout(timeoutId);
  }
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


async function stagePayload(target, payload, mode = 0o644, suffix = ".tmp") {
  const temporary = path.join(
    path.dirname(target),
    `.${path.basename(target)}.${process.pid}.${randomBytes(8).toString("hex")}${suffix}`,
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
  const snapshot = await readFileSnapshot(target, "output");
  return { ...snapshot, sha256: sha256(snapshot.payload) };
}


function snapshotsEqual(left, right) {
  if (left === null || right === null) return left === right;
  return left.signature === right.signature && left.payload.equals(right.payload);
}


async function assertTargetUnchanged(entry) {
  const current = await snapshotTarget(entry.target);
  if (!snapshotsEqual(current, entry.snapshot)) {
    throw new Error(`output changed before publish: ${entry.target}`);
  }
}


async function matchesPublishedPayload(entry) {
  const current = await snapshotTarget(entry.target);
  return current !== null
    && current.replacementSignature === entry.stagedSignature
    && current.payload.equals(entry.payload);
}


function preserveBackup(entry, reason) {
  if (entry.backup) {
    const backup = entry.backup;
    entry.backup = null;
    return `${reason}; original backup preserved at ${backup}`;
  }
  return reason;
}


async function restorePublishedEntry(entry, replace) {
  const current = await snapshotTarget(entry.target);
  if (snapshotsEqual(current, entry.snapshot)) return;
  if (!(await matchesPublishedPayload(entry))) {
    throw new Error(preserveBackup(
      entry,
      `rollback conflict at ${entry.target}: current output is neither original nor published`,
    ));
  }
  if (entry.snapshot === null) {
    await rm(entry.target);
    return;
  }
  if (!entry.backup || !(await exists(entry.backup))) {
    throw new Error(`rollback backup is missing for ${entry.target}`);
  }
  const backup = entry.backup;
  try {
    await replace(backup, entry.target);
    entry.backup = null;
  } catch (error) {
    const restored = await snapshotTarget(entry.target).catch(() => null);
    if (
      restored !== null
      && restored.replacementSignature === entry.backupSignature
      && restored.payload.equals(entry.snapshot.payload)
    ) {
      entry.backup = null;
      return;
    }
    throw new Error(preserveBackup(entry, error.message), { cause: error });
  }
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
      const stagedInfo = await lstat(temporary, { bigint: true });
      const record = {
        target: entry.target,
        payload,
        snapshot,
        temporary,
        backup: null,
        backupSignature: null,
        attempted: false,
        stagedSignature: replacementSignature(stagedInfo),
      };
      staged.push(record);
      if (snapshot !== null) {
        record.backup = await stagePayload(
          entry.target,
          snapshot.payload,
          snapshot.mode,
          ".bak",
        );
        record.backupSignature = replacementSignature(
          await lstat(record.backup, { bigint: true }),
        );
      }
    }
    for (const entry of staged) {
      await assertTargetUnchanged(entry);
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
        rollbackErrors.push(preserveBackup(entry, rollbackError.message));
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
    await Promise.all(
      staged
        .filter((entry) => entry.backup)
        .map((entry) => rm(entry.backup, { force: true }).catch(() => {})),
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
    const snapshot = await readFileSnapshot(
      absolutePath,
      `canonical source asset ${relativePath}`,
    );
    files.push({ path: relativePath, sha256: sha256(snapshot.payload) });
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
  return withTimeout(() => locator.evaluate((root) => {
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
  }), "motion inspection");
}


async function stabilizeStaticDocument(page) {
  await withTimeout(() => page.evaluate(async () => {
    await document.fonts.ready;
  }), "font stabilization");

  // Chromium suppresses requestAnimationFrame callbacks when the context was
  // created with javaScriptEnabled:false. Drive two bounded compositor/layout
  // turns from Playwright instead, without ever enabling page-authored script.
  for (let frame = 0; frame < 2; frame += 1) {
    await new Promise((resolve) => setTimeout(resolve, 17));
    await withTimeout(() => page.evaluate(() => {
      const root = document.documentElement;
      const style = getComputedStyle(root);
      const bounds = root.getBoundingClientRect();
      return [style.display, bounds.width, bounds.height];
    }), `static layout turn ${frame + 1}`);
  }
}


async function inspectStaticSurface(page) {
  return withTimeout(() => page.evaluate(() => {
    const violations = [];
    const record = (kind, value) => violations.push(`${kind}: ${value}`);
    const isLocalFragment = (value) => value.trim().startsWith("#");
    const inspectUrlValue = (kind, value) => {
      const normalized = (value || "").trim();
      if (normalized && !isLocalFragment(normalized)) record(kind, normalized);
    };
    const inspectCssText = (source, label) => {
      const css = source || "";
      const urlExpression = /url\(\s*(["']?)(.*?)\1\s*\)/giu;
      for (const match of css.matchAll(urlExpression)) {
        inspectUrlValue(`${label} url`, match[2]);
      }
      const importExpression = /@import\s+(?:url\(\s*)?(["']?)([^"'\s;)]+)\1/giu;
      for (const match of css.matchAll(importExpression)) {
        inspectUrlValue(`${label} import`, match[2]);
      }
    };
    const inspectSheet = (sheet, label) => {
      let rules;
      try {
        rules = sheet.cssRules;
      } catch (error) {
        record(`${label} stylesheet`, `inaccessible ${error.name || "error"}`);
        return;
      }
      for (const rule of rules || []) {
        inspectCssText(rule.cssText || "", label);
        if (rule.cssRules) {
          for (const nested of rule.cssRules) inspectCssText(nested.cssText || "", label);
        }
      }
    };

    for (const script of document.querySelectorAll("script")) {
      record("active element", `<script${script.src ? ` src=${script.src}` : ""}>`);
    }
    for (const element of document.querySelectorAll("iframe, frame, object, embed, portal")) {
      record("active element", `<${element.localName}>`);
    }
    for (const meta of document.querySelectorAll("meta[http-equiv]")) {
      if ((meta.getAttribute("http-equiv") || "").trim().toLowerCase() === "refresh") {
        record("active element", "<meta http-equiv=refresh>");
      }
    }
    for (const base of document.querySelectorAll("base[href]")) {
      record("active element", `<base href=${base.getAttribute("href") || ""}>`);
    }

    const urlAttributes = ["src", "srcset", "poster", "data", "href", "xlink:href"];
    for (const element of document.querySelectorAll("*")) {
      for (const attribute of element.attributes) {
        if (attribute.name.toLowerCase().startsWith("on")) {
          record("event attribute", `${element.localName}[${attribute.name}]`);
        }
      }
      for (const attribute of urlAttributes) {
        if (!element.hasAttribute(attribute)) continue;
        inspectUrlValue(`${element.localName}[${attribute}]`, element.getAttribute(attribute));
      }
      inspectCssText(element.getAttribute("style") || "", `${element.localName}[style]`);
    }
    for (const style of document.querySelectorAll("style")) {
      inspectCssText(style.textContent || "", "style element");
    }
    for (const [index, sheet] of [...document.styleSheets].entries()) {
      inspectSheet(sheet, `document stylesheet ${index}`);
    }
    for (const [index, sheet] of [...(document.adoptedStyleSheets || [])].entries()) {
      inspectSheet(sheet, `document adopted stylesheet ${index}`);
    }
    const elements = [...document.querySelectorAll("*")];
    for (const element of elements) {
      if (!element.shadowRoot) continue;
      for (const [index, sheet] of [...(element.shadowRoot.adoptedStyleSheets || [])].entries()) {
        inspectSheet(sheet, `${element.localName} adopted stylesheet ${index}`);
      }
    }
    return [...new Set(violations)].sort();
  }), "static surface inspection");
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
  const inputSnapshot = await readFileSnapshot(canonicalInput, "input HTML");
  const inputPayload = inputSnapshot.payload;
  const sourceAssets = await canonicalSourceAssets();
  const externalRequests = new Set();
  const canonicalInputUrl = pathToFileURL(canonicalInput).href;
  const browser = await chromium.launch({ headless: true });
  let context;
  let browserClosed = false;
  let screenshot;
  let boundingBox;
  let cells;
  let motion;
  let chromiumVersion;
  let dimensions;
  try {
    context = await browser.newContext({
      viewport: VIEWPORT,
      deviceScaleFactor: DEVICE_SCALE_FACTOR,
      reducedMotion: "reduce",
      serviceWorkers: "block",
      javaScriptEnabled: false,
    });
    const page = await context.newPage();
    page.setDefaultTimeout(PLAYWRIGHT_OPERATION_TIMEOUT_MS);
    page.setDefaultNavigationTimeout(PLAYWRIGHT_OPERATION_TIMEOUT_MS);
    let allowedMainNavigations = 0;
    const isCanonicalMainNavigation = (request) => request.url() === canonicalInputUrl
      && request.isNavigationRequest()
      && request.frame() === page.mainFrame();
    const watchPage = (candidate) => {
      candidate.on("worker", (worker) => {
        externalRequests.add(`worker:${worker.url() || "unknown"}`);
      });
      candidate.on("popup", (popup) => {
        externalRequests.add(`popup:${popup.url() || "pending"}`);
      });
    };
    watchPage(page);
    context.on("page", (popup) => {
      externalRequests.add(`popup:${popup.url() || "pending"}`);
      watchPage(popup);
    });
    context.on("serviceworker", (worker) => {
      externalRequests.add(`serviceworker:${worker.url() || "unknown"}`);
    });
    context.on("request", (request) => {
      if (!isCanonicalMainNavigation(request)) externalRequests.add(request.url());
    });
    await context.route("**/*", async (route) => {
      if (isCanonicalMainNavigation(route.request()) && allowedMainNavigations === 0) {
        allowedMainNavigations += 1;
        await route.fulfill({
          status: 200,
          contentType: "text/html; charset=utf-8",
          body: inputPayload,
        });
        return;
      }
      externalRequests.add(route.request().url());
      await route.abort("blockedbyclient");
    });
    await page.goto(canonicalInputUrl, {
      waitUntil: "load",
      timeout: PLAYWRIGHT_OPERATION_TIMEOUT_MS,
    });
    if (allowedMainNavigations !== 1) {
      throw new Error(`canonical input navigation must occur exactly once; found ${allowedMainNavigations}`);
    }
    const surfaceViolations = await inspectStaticSurface(page);
    for (const violation of surfaceViolations) externalRequests.add(violation);
    if (externalRequests.size !== 0) {
      throw new Error(
        `external requests are forbidden; active content is forbidden: `
        + `${[...externalRequests].join(", ")}`,
      );
    }
    await withTimeout(() => page.evaluate((captureStyle) => {
      const style = document.createElement("style");
      style.dataset.diagramCoreCaptureStyle = "";
      style.textContent = captureStyle;
      document.head.append(style);
    }, CAPTURE_STYLE), "capture style injection");
    await stabilizeStaticDocument(page);

    const locator = page.locator(LOCATOR);
    const locatorCount = await locator.count();
    if (locatorCount !== 1) {
      throw new Error(`${LOCATOR} must match exactly once; found ${locatorCount}`);
    }
    cells = await locator.locator('[data-cell-kind="regression"]').count();
    if (cells !== EXPECTED_CELLS) {
      throw new Error(`regression grid must contain ${EXPECTED_CELLS} cells; found ${cells}`);
    }
    boundingBox = await locator.boundingBox();
    if (!boundingBox) throw new Error(`${LOCATOR} has no visible bounding box`);
    if (boundingBox.width !== EXPECTED_WIDTH || boundingBox.height !== EXPECTED_HEIGHT) {
      throw new Error(
        `regression grid dimensions must be ${EXPECTED_WIDTH}x${EXPECTED_HEIGHT}; `
        + `found ${boundingBox.width}x${boundingBox.height}`,
      );
    }
    motion = await computedMotionCounts(locator);
    if (motion.animationCount !== 0 || motion.transitionCount !== 0) {
      throw new Error(
        `capture surface still has motion: animations=${motion.animationCount} `
        + `transitions=${motion.transitionCount}`,
      );
    }
    if (externalRequests.size !== 0) {
      throw new Error(`external requests are forbidden: ${[...externalRequests].join(", ")}`);
    }

    screenshot = await locator.screenshot({
      type: "png",
      animations: "disabled",
      timeout: PLAYWRIGHT_OPERATION_TIMEOUT_MS,
    });
    if (externalRequests.size !== 0) {
      throw new Error(`external requests are forbidden: ${[...externalRequests].join(", ")}`);
    }
    dimensions = pngDimensions(screenshot);
    if (dimensions.width !== EXPECTED_WIDTH || dimensions.height !== EXPECTED_HEIGHT) {
      throw new Error(
        `screenshot dimensions must be ${EXPECTED_WIDTH}x${EXPECTED_HEIGHT}; `
        + `found ${dimensions.width}x${dimensions.height}`,
      );
    }
    chromiumVersion = browser.version();
    await withTimeout(() => context.close(), "browser context close", CLOSE_TIMEOUT_MS);
    context = undefined;
    await withTimeout(() => browser.close(), "browser close", CLOSE_TIMEOUT_MS);
    browserClosed = true;
    if (allowedMainNavigations !== 1) {
      throw new Error(`canonical input navigation must occur exactly once; found ${allowedMainNavigations}`);
    }
    if (externalRequests.size !== 0) {
      throw new Error(
        `external requests are forbidden; active content is forbidden: `
        + `${[...externalRequests].join(", ")}`,
      );
    }
  } finally {
    if (context) {
      await withTimeout(
        () => context.close(),
        "browser context cleanup",
        CLOSE_TIMEOUT_MS,
      ).catch(() => {});
    }
    if (!browserClosed) {
      await withTimeout(
        () => browser.close(),
        "browser cleanup",
        CLOSE_TIMEOUT_MS,
      ).catch(() => {});
    }
  }

  const captureTimestamp = new Date().toISOString();
  await assertSnapshotCurrent(inputSnapshot, "input HTML");
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
    await new Promise((resolve) => {
      process.stderr.write(`error: ${error.message}\n`, resolve);
    });
    process.exit(error instanceof UsageError ? 2 : 1);
  }
}

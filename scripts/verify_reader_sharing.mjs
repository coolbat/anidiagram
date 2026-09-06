import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";

const source = path.resolve(process.argv[2]);
const output = path.dirname(source);
const original = fs.readFileSync(source);
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, acceptDownloads: true });
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(pathToFileURL(source).href);
  await page.waitForFunction(() => Boolean(window.AniDiagramReader));
  const exportBefore = await page.evaluate(async () => (await fetch(document.getElementById("download").href)).text());
  await page.locator("#reader-controls > summary").click();
  await page.selectOption("#reader-view", "compile");
  assert.equal(await page.locator("#reader-previous").isDisabled(), true);
  await page.locator("#reader-next").click();
  assert.deepEqual((await page.evaluate(() => window.AniDiagramReader.getSelection())).edges, ["plan-render"]);
  const link = await page.evaluate(() => window.AniDiagramReader.readingURL());
  await page.goto(link);
  await page.waitForFunction(() => window.AniDiagramReader?.getSelection().edges[0] === "plan-render");
  for (const format of ["svg", "png"]) {
    const [download] = await Promise.all([page.waitForEvent("download"), page.locator("#reader-share-" + format).click()]);
    await download.saveAs(path.join(output, "selection-card." + format));
  }
  const svg = fs.readFileSync(path.join(output, "selection-card.svg"), "utf8");
  const metadata = await page.evaluate(source => {
    const doc = new DOMParser().parseFromString(source, "image/svg+xml");
    if (doc.querySelector("parsererror")) throw new Error("Invalid SVG export");
    return JSON.parse(doc.querySelector("metadata").textContent);
  }, svg);
  assert.deepEqual(metadata.edges.map(edge => edge.id), ["plan-render"]);
  assert.deepEqual(metadata.nodes.map(node => node.id), ["compiler", "renderer"]);
  assert.match(metadata.graph_sha256, /^[a-f0-9]{64}$/);
  const png = fs.readFileSync(path.join(output, "selection-card.png"));
  assert.equal(png.subarray(1, 4).toString(), "PNG");
  assert.equal(png.readUInt32BE(16), 1200); assert.equal(png.readUInt32BE(20), 630);
  const sizes = [];
  for (const [width, height] of [[1440, 900], [1600, 1000], [1920, 1080], [2048, 1320]]) {
    await page.setViewportSize({ width, height });
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    const fits = await page.evaluate(() => {
      const diagram = document.querySelector("#viewport svg").getBoundingClientRect();
      const stage = document.getElementById("stage").getBoundingClientRect();
      return document.documentElement.scrollHeight <= innerHeight && document.documentElement.scrollWidth <= innerWidth && diagram.right <= stage.right && diagram.bottom <= stage.bottom;
    });
    assert.equal(fits, true, `expanded reader must fit ${width}x${height}`);
    sizes.push(`${width}x${height}`);
  }
  const exportAfter = await page.evaluate(async () => (await fetch(document.getElementById("download").href)).text());
  assert.equal(exportBefore, exportAfter);
  assert.deepEqual(errors, []);
  assert.deepEqual(fs.readFileSync(source), original);
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.screenshot({ path: path.join(output, "reader-expanded.png") });
  console.log(JSON.stringify({ ok: true, chapters: true, deep_link: true, svg: true, png: "1200x630", export_unchanged: true, expanded_viewports: sizes, errors }));
} finally { await browser.close(); }

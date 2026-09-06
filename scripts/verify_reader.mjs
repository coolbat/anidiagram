import assert from "node:assert/strict";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(pathToFileURL(path.resolve(process.argv[2])).href);
  await page.waitForFunction(() => Boolean(window.AniDiagramReader));
  await page.locator("#reader-controls > summary").click();
  await page.selectOption("#reader-source", "client");
  await page.selectOption("#reader-target", "telemetry");
  await page.locator('[data-reader-mode="route"]').click();
  const route = await page.evaluate(() => window.AniDiagramReader.getSelection());
  assert.deepEqual(route.nodes, ["client", "ingress", "workload", "telemetry"]);
  assert.deepEqual(route.edges, ["client-request", "ingress-route", "emit-telemetry"]);
  const link = await page.evaluate(() => window.AniDiagramReader.readingURL());
  await page.goto(link);
  await page.waitForFunction(() => window.AniDiagramReader?.getSelection().edges.length === 3);
  assert.deepEqual(await page.evaluate(() => window.AniDiagramReader.getSelection()), route);
  await page.selectOption("#reader-source", "telemetry");
  await page.selectOption("#reader-target", "client");
  assert.match(await page.locator("#reader-result").textContent(), /No authored directed route/);
  await page.locator('[data-reader-mode="upstream"]').click();
  assert.equal((await page.evaluate(() => window.AniDiagramReader.getSelection())).nodes.length, 4);
  await page.locator("#reader-clear").click();
  await page.locator("#reader-search").fill("workload");
  assert.deepEqual((await page.evaluate(() => window.AniDiagramReader.getSelection())).nodes, ["workload"]);
  const exported = await page.evaluate(async () => (await fetch(document.getElementById("download").href)).text());
  assert.ok(!exported.includes("reader-muted") && !exported.includes("reader-selection-style"));
  await page.locator('.motion-choice[data-motion="off"]').click();
  assert.equal(await page.locator("#viewer").getAttribute("class"), "motion-off");
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ ok: true, route: route.edges, deep_link: true, search: true, export_unpolluted: true, motion_controls: true, errors }));
} finally {
  await browser.close();
}

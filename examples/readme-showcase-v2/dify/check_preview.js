// Run with playwright-cli run-code --filename <this file> after starting the local preview server.
async (page) => {
  const base = new URL('.', page.url()).href;
  const out = 'outputs/readme-showcase-v2/dify/';
  const english = /\/(?:index\.en|dify-en)\./.test(page.url());
  const language = english ? 'en' : 'zh-CN';
  const index = english ? 'index.en.html' : 'index.html';
  const otherIndex = english ? 'index.html' : 'index.en.html';
  const stem = english ? 'dify-en' : 'dify';
  const prefix = english ? 'en-' : '';
  const evidence = english ? 'evidence.en.md' : 'evidence.md';
  const accuracy = english ? 'accuracy.en.json' : 'accuracy.json';
  const errors = [];
  const onError = error => errors.push(String(error));
  page.on('pageerror', onError);
  const captures = [];
  const hashes = {};
  for (const colorScheme of ['light', 'dark']) {
    for (const viewport of [{width: 1200, height: 1100}, {width: 390, height: 844}]) {
      await page.setViewportSize(viewport);
      await page.emulateMedia({colorScheme, reducedMotion: 'reduce'});
      await page.goto(base + index);
      await page.locator('figure img').evaluate(image => image.decode());
      const measured = await page.evaluate(() => {
        const image = document.querySelector('figure img');
        return {
          overflow: document.documentElement.scrollWidth > window.innerWidth,
          imageWidth: image.getBoundingClientRect().width,
          imageLoaded: image.complete && image.naturalWidth === 900,
          navLinks: Array.from(document.querySelectorAll('nav a'), link => ({
            label: link.textContent, href: link.getAttribute('href'), width: link.getBoundingClientRect().width,
            insideViewport: link.getBoundingClientRect().left >= 0 && link.getBoundingClientRect().right <= window.innerWidth
          })),
          headingFont: getComputedStyle(document.querySelector('h1')).fontSize,
          language: document.documentElement.lang,
        };
      });
      if (measured.overflow || !measured.imageLoaded || measured.navLinks.some(link => !link.insideViewport)) {
        throw new Error('Unusable README preview: ' + JSON.stringify(measured));
      }
      if (viewport.width === 1200 && measured.imageWidth !== 840) throw new Error('Desktop is not the planned README width');
      if (measured.language !== language) throw new Error('Wrong page language');
      const file = `${prefix}preview-${viewport.width === 390 ? 'mobile' : 'desktop'}-${colorScheme}.png`;
      await page.screenshot({path: out + file, fullPage: true});
      captures.push({viewport, colorScheme, screenshot: file, ...measured});
    }
  }
  const localLinks = [];
  for (const name of [index, otherIndex, stem + '.html', evidence, accuracy, stem + '-static.svg', 'showcase.css']) {
    const response = await page.request.get(base + name);
    if (response.status() !== 200) throw new Error('Broken local link: ' + name);
    localLinks.push({path: name, status: response.status()});
  }
  // Hash the actual bytes served to this browser; font measurements come from the actual SVG DOM.
  Object.assign(hashes, await page.evaluate(async names => {
    const entries = [];
    for (const name of names) {
      const body = await (await fetch(name)).arrayBuffer();
      const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', body));
      entries.push([name, Array.from(digest, value => value.toString(16).padStart(2, '0')).join('')]);
    }
    return Object.fromEntries(entries);
  }, [index, stem + '.html', stem + '-static.svg', 'showcase.css']));
  await page.emulateMedia({colorScheme: 'light', reducedMotion: 'no-preference'});
  await page.goto(base + stem + '-static.svg');
  const typography = await page.evaluate(() => ({
    node: parseFloat(getComputedStyle(document.querySelector('.node-title')).fontSize),
    relation: parseFloat(getComputedStyle(document.querySelector('.edge-label')).fontSize),
    svgWidth: document.querySelector('svg').viewBox.baseVal.width,
    nodes: document.querySelectorAll('.node').length,
    relations: document.querySelectorAll('.edge-label').length,
  }));
  typography.nodeAt840 = typography.node * 840 / typography.svgWidth;
  typography.relationAt840 = typography.relation * 840 / typography.svgWidth;
  if (typography.nodeAt840 < 14 || typography.relationAt840 < 12 || typography.nodes !== 10 || typography.relations !== 13) {
    throw new Error('Static diagram typography or visible content count failed');
  }
  // A static asset must be complete at rest and stay still, not rely on an animation's first frame.
  const staticState = await page.evaluate(() => ({
    hiddenNodes: Array.from(document.querySelectorAll('.node')).filter(node => Number(getComputedStyle(node).opacity) < 1).length,
    runningAnimations: document.getAnimations().filter(animation => animation.playState === 'running').length,
    smil: document.querySelectorAll('animate, animateTransform').length,
  }));
  if (staticState.hiddenNodes || staticState.runningAnimations || staticState.smil) throw new Error('Static SVG is not a complete still');
  await page.setViewportSize({width: 1200, height: 1100});
  await page.emulateMedia({colorScheme: 'light', reducedMotion: 'no-preference'});
  await page.goto(base + index);
  await page.locator('#reproduce summary').click();
  if (!(await page.locator('#reproduce').getAttribute('open') !== null)) throw new Error('Reproduction instructions are inaccessible');
  if (english && await page.locator('body').evaluate(body => /[\u3400-\u9fff]/.test(body.innerText.replaceAll('中文', '')))) throw new Error('Untranslated Chinese on English case page');
  await page.locator(`.languages a[href="${otherIndex}"]`).click();
  const otherLanguage = await page.locator('html').getAttribute('lang');
  if (otherLanguage !== (english ? 'zh-CN' : 'en')) throw new Error('Language switch failed');
  await page.locator(`.languages a[href="${index}"]`).click();
  if (page.url() !== base + index) throw new Error('Language switch did not return');
  await page.getByRole('link', {name: english ? 'Explore the diagram →' : '打开交互图 →', exact: true}).click();
  const interactiveNavigates = page.url() === base + stem + '.html';
  if (!interactiveNavigates) throw new Error('Interactive link failed');
  await page.locator('button[data-motion="off"]').click();
  await page.locator('#reader-controls summary').click();
  await page.locator('#reader-view').selectOption('query');
  const queryView = await page.locator('#reader-view').inputValue();
  const queryWorkerOpacity = await page.locator('[id="node-worker"]').evaluate(node => Number(getComputedStyle(node).opacity));
  if (queryWorkerOpacity > .2 || (await page.locator('#reader-result').textContent()).includes(english ? 'Indexer' : '索引 Worker')) throw new Error('Query view incorrectly includes indexing Worker');
  await page.screenshot({path: out + prefix + 'query-view.png', fullPage: false});
  await page.locator('#reader-view').selectOption('ingest');
  const ingestView = await page.locator('#reader-view').inputValue();
  const ingestWorkerOpacity = await page.locator('[id="node-worker"]').evaluate(node => Number(getComputedStyle(node).opacity));
  if (ingestWorkerOpacity < .99) throw new Error('Ingestion Worker is not visible');
  await page.screenshot({path: out + prefix + 'ingest-view.png', fullPage: false});
  if (queryView !== 'query' || ingestView !== 'ingest') throw new Error('Reader chapter switch failed');
  if (english && await page.locator('body').evaluate(body => /[\u3400-\u9fff]/.test(body.innerText))) throw new Error('Untranslated Chinese in English viewer');
  await page.goto(base + index);
  await page.locator('figure img').screenshot({path: out + stem + '-poster.png'});
  page.off('pageerror', onError);
  if (errors.length) throw new Error('Browser errors: ' + errors.join('; '));
  return {passed: true, language, languageSwitch: true, artifact_sha256: hashes, captures, localLinks, typography, staticState,
          interactiveNavigates, queryView, ingestView, queryWorkerOpacity, ingestWorkerOpacity, pageErrors: errors, semanticReview: 'pending',
          scope: 'Local README-width mock, not the live GitHub page. Mobile diagram is overview-only; full labels are available in the interactive viewer.'};
}

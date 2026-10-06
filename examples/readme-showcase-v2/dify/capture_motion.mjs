// Capture the delivered readable HTML, not a second render with different labels.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {chromium} from 'playwright';
import {auditLabels} from '../../../runtime/label-audit.mjs';

const [directory, stem, channel] = process.argv.slice(2);
const out = path.resolve(directory);
const input = path.join(out, `${stem}.html`);
const frames = path.join(out, `${stem}-frames`);
fs.mkdirSync(frames, {recursive: true});
const browser = await chromium.launch({headless: true, ...(channel ? {channel} : {})});
try {
  const page = await browser.newPage({viewport: {width: 1440, height: 1500}, reducedMotion: 'no-preference', colorScheme: 'light'});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(pathToFileURL(input).href);
  await page.waitForFunction(() => window.__ANIDIAGRAM_ICON_TIMELINES__?.length === 10 &&
    [...document.querySelectorAll('g.node[id]')].every(node => node.querySelector('.semantic-icon')));
  await page.evaluate(() => document.fonts.ready);
  const readability = await page.evaluate(auditLabels);
  if (readability.status !== 'passed') throw new Error(JSON.stringify(readability));
  await page.addStyleTag({content: `
    #stage { width:900px!important; height:1130px!important; max-height:none!important; overflow:visible!important; }
    #viewport { transform:none!important; width:900px!important; height:1130px!important; }
    #viewport > svg { width:900px!important; height:1130px!important; }
  `});
  const regions = await page.evaluate(() => {
    const root = document.querySelector('#viewport > svg');
    root.pauseAnimations(); root.setCurrentTime(10);
    window.gsap.globalTimeline.pause();
    window.__ANIDIAGRAM_TIMELINES__.forEach(t => t.pause());
    const b = root.getBoundingClientRect();
    return Object.fromEntries([...root.querySelectorAll('g.node[id]')].map(node => {
      const r = node.querySelector('.semantic-icon').getBoundingClientRect();
      return [node.id, [Math.floor(r.left-b.left), Math.floor(r.top-b.top), Math.ceil(r.right-b.left), Math.ceil(r.bottom-b.top)]];
    }));
  });
  const iconStates = new Map(Object.keys(regions).map(id => [id, new Set()]));
  for (let index = 0; index < 24; index++) {
    const states = await page.evaluate(seconds => {
      for (const timeline of window.__ANIDIAGRAM_TIMELINES__) {
        if (timeline.__anidiagramStage === 'title-entry') { timeline.progress(1).pause(); continue; }
        const cycle = timeline.duration() + timeline.repeatDelay();
        timeline.totalTime(Math.max(0, seconds - timeline.delay()) % Math.max(.001, cycle), false).pause();
      }
      return Object.fromEntries([...document.querySelectorAll('g.node[id]')].map(node => [node.id, node.querySelector('.semantic-icon').innerHTML]));
    }, 1 + index / 12);
    for (const [id, state] of Object.entries(states)) iconStates.get(id).add(state);
    await page.locator('#viewport > svg').screenshot({path: path.join(frames, `frame-${String(index).padStart(4, '0')}.png`), animations: 'allow'});
  }
  const changes = Object.fromEntries([...iconStates].map(([id, states]) => [id, states.size]));
  if (Object.keys(regions).length !== 10 || Object.values(changes).some(n => n < 5) || errors.length) {
    throw new Error(JSON.stringify({regions, changes, errors}));
  }
  fs.writeFileSync(path.join(out, `${stem}-motion.json`), JSON.stringify({
    capture_contract: 'dify-readable-runtime-v1', html: `${stem}.html`,
    html_sha256: createHash('sha256').update(fs.readFileSync(input)).digest('hex'),
    browser: browser.version(), frames: 24, fps: 12, width: 900, height: 1130,
    icon_regions: regions, distinct_icon_states: changes, readability: readability.status,
    semantic_review: 'pending', scope: 'Browser capture of the delivered HTML. Motion illustrates activity, not measured Dify execution or duration.'
  }, null, 2) + '\n');
} finally {
  await browser.close();
}

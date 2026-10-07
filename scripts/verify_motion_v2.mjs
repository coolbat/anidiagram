#!/usr/bin/env node
import assert from 'node:assert/strict';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {chromium} from 'playwright';

const directory = path.resolve(process.argv[2] || 'outputs/optimization-p1');
const browser = await chromium.launch({headless: true});
const errors = [];
const result = [];
try {
  for (const mode of ['ambient', 'event-driven']) {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(pathToFileURL(path.join(directory, `motion-${mode}.html`)).href);
    await page.waitForTimeout(100);
    const initial = await page.evaluate(() => {
      window.AniDiagramEntrance?.clear();
      window.AniDiagramRuntime.pause();
      const manifest = JSON.parse(document.getElementById('anidiagram-motion-manifest').textContent);
      return {manifest, all: __ANIDIAGRAM_TIMELINES__.length, edges: window.__ANIDIAGRAM_EDGE_MOTION_TIMELINES__?.length || 0, icons: __ANIDIAGRAM_ICON_TIMELINES__.length,
        speed: (window.__ANIDIAGRAM_EDGE_MOTION_TIMELINES__ || []).map(t => t.__anidiagramPathLength / t.__anidiagramTravelSeconds),
        periods: (window.__ANIDIAGRAM_EDGE_MOTION_TIMELINES__ || []).map(t => t.duration()),
        generated: document.querySelectorAll('.edge-motion-v1-generated').length,
        events: window.__ANIDIAGRAM_EVENT_DRIVEN__?.events || []};
    });
    assert.equal(initial.manifest.mode, mode);
    assert.equal(initial.manifest.stage.beat_seconds, 4);
    if (mode === 'ambient') {
      assert(initial.icons + initial.edges <= 5, 'default motion budget exceeded');
      assert(initial.speed.every(speed => Math.abs(speed - 180) < 0.001), 'packets move at unequal speeds');
      assert(initial.periods.every(period => period % 4 === 0), 'edge cycles do not align with beat');
      const hovered = await page.evaluate(() => {
        const manifest = JSON.parse(document.getElementById('anidiagram-motion-manifest').textContent);
        window.AniDiagramRuntime.resume();
        const edge = document.querySelectorAll('g.edge')[manifest.stage.hover_edge_indices[0]];
        edge.dispatchEvent(new Event('pointerenter'));
        const all = __ANIDIAGRAM_EDGE_MOTION_TIMELINES__;
        const running = all.filter(timeline => !timeline.paused()).length;
        const created = all.some(timeline => timeline.__anidiagramEdgeIndex === manifest.stage.hover_edge_indices[0]);
        window.AniDiagramRuntime.pause(); window.AniDiagramRuntime.resume();
        const resumed = __ANIDIAGRAM_EDGE_MOTION_TIMELINES__.filter(timeline => !timeline.paused()).length;
        edge.dispatchEvent(new Event('pointerleave'));
        return {running, created, resumed, resident: __ANIDIAGRAM_EDGE_MOTION_TIMELINES__.length};
      });
      assert(hovered.created, 'secondary edge did not replay on hover');
      assert(hovered.running <= 3 && hovered.resumed <= 3, 'hover exceeds resident edge budget');
      assert.equal(hovered.resident, initial.edges, 'hover leaked a duplicate timeline');
    } else {
      assert.equal(initial.all, 1, 'event mode must have one scheduler root');
      assert.equal(initial.icons, 0, 'ambient icon loops leaked into event mode');
      assert.equal(initial.edges, 0, 'ambient edge loops leaked into event mode');
      assert(initial.events.length >= 5, 'event mode omitted primary edges beyond simultaneous budget');
      assert(initial.events.every(event => Math.abs(event.feedback_end - event.arrival - 0.15) < 0.0001), 'arrival feedback duration');
      assert(initial.events[2].arrival - initial.events[2].start > initial.events[0].arrival, 'async departure was not delayed');
      assert(initial.events.slice(1).every((event, index) => event.start >= initial.events[index].end), 'target did not finish before next signal');
      const deterministic = await page.evaluate(() => {
        const state = __ANIDIAGRAM_EVENT_DRIVEN__;
        const first = state.events[0];
        const capture = seconds => {
          state.timeline.pause().totalTime(seconds, false);
          return [...document.querySelectorAll('#viewport svg g.node *, .edge-motion-v1-generated')].map(element => {
            const bounds = element.getBoundingClientRect();
            const style = getComputedStyle(element);
            return [element.id, ...['x', 'y', 'width', 'height'].map(key => Number(bounds[key].toFixed(3))), style.opacity, style.strokeDashoffset];
          });
        };
        const before = capture(first.arrival - 0.08);
        const arrival = capture(first.arrival + 0.075);
        const icon = capture(first.feedback_end + 0.3);
        capture(state.cycle - 0.1); capture(0);
        const again = capture(first.feedback_end + 0.3);
        return {stable: JSON.stringify(icon) === JSON.stringify(again), feedback: JSON.stringify(before) !== JSON.stringify(arrival), icon: JSON.stringify(arrival) !== JSON.stringify(icon), count: document.querySelectorAll('.edge-motion-v1-generated').length};
      });
      assert(deterministic.feedback && deterministic.icon, 'arrival and icon performance lack observable frames');
      assert(deterministic.stable, 'event timeline is not reproducible after backward seek');
      assert.equal(deterministic.count, initial.generated, 'seeking created duplicate particles');
      const semantics = await page.evaluate(() => {
        const state = __ANIDIAGRAM_EVENT_DRIVEN__, edges = document.querySelectorAll('g.edge');
        const at = time => state.timeline.pause().totalTime(time, false);
        const event = state.events[0], ring = edges[0].querySelector('.runtime-arrival-feedback');
        at(event.arrival + 0.075); const pulse = Number(getComputedStyle(ring).opacity);
        at(event.arrival + 0.16); const quiet = Number(getComputedStyle(ring).opacity);
        const asyncEvent = state.events[2], packet = edges[2].querySelector('.runtime-edge-packet');
        at(asyncEvent.start + 0.1); const waiting = Number(packet.getAttribute('opacity'));
        at(asyncEvent.start + 0.5); const departed = Number(packet.getAttribute('opacity'));
        const streamEvent = state.events[3], stream = edges[3].querySelector('.runtime-edge-stream');
        at(streamEvent.start + 0.2); const dashA = Number(stream.getAttribute('stroke-dashoffset'));
        at(streamEvent.start + 0.7); const dashB = Number(stream.getAttribute('stroke-dashoffset'));
        const failureEvent = state.events[4], failure = edges[4].querySelector('.runtime-edge-comet-head');
        at(failureEvent.arrival); const endpoint = {x: Number(failure.getAttribute('cx')), y: Number(failure.getAttribute('cy'))};
        at(failureEvent.arrival + 0.12); const bounce = Math.hypot(Number(failure.getAttribute('cx')) - endpoint.x, Number(failure.getAttribute('cy')) - endpoint.y);
        return {pulse, quiet, waiting, departed, streamSpeed: Math.abs(dashB-dashA)/0.5, bounce, failureColor: failure.getAttribute('fill')};
      });
      assert(semantics.pulse > 0 && semantics.quiet === 0, '150ms port feedback did not settle');
      assert.equal(semantics.waiting, 0, 'async signal departed before queue delay');
      assert(semantics.departed > 0, 'async signal never departed');
      assert(Math.abs(semantics.streamSpeed-180)<0.01, 'stream speed is not uniform');
      assert(semantics.bounce > 10 && semantics.failureColor === '#dc2626', 'failure lacks red rebound');
      const eventReplay = await page.evaluate(() => {
        window.AniDiagramRuntime.resume();
        const state = __ANIDIAGRAM_EVENT_DRIVEN__, edge = document.querySelectorAll('g.edge')[5];
        edge.dispatchEvent(new Event('pointerenter'));
        const paused = state.timeline.paused();
        const replay = __ANIDIAGRAM_TIMELINES__.filter(timeline => timeline.__anidiagramStage === 'event-hover').length;
        window.AniDiagramRuntime.pause(); window.AniDiagramRuntime.resume();
        const budgetHeld = state.timeline.paused();
        edge.dispatchEvent(new Event('pointerleave'));
        return {paused, replay, budgetHeld, roots: __ANIDIAGRAM_TIMELINES__.length};
      });
      assert(eventReplay.paused && eventReplay.budgetHeld, 'secondary event hover did not suspend resident scheduler');
      assert.equal(eventReplay.replay, 1, 'secondary event relationship did not replay');
      assert.equal(eventReplay.roots, 1, 'secondary event replay leaked a timeline');


    }
    for (let loop = 0; loop < 3; loop++) {
      for (const profile of ['off', 'readable', 'expressive']) {
        await page.locator(`.motion-choice[data-motion="${profile}"]`).click();
        const state = await page.evaluate(() => ({all: __ANIDIAGRAM_TIMELINES__.length, generated: document.querySelectorAll('.edge-motion-v1-generated').length, event: Boolean(window.__ANIDIAGRAM_EVENT_DRIVEN__)}));
        if (profile === 'off') { assert.equal(state.all, 0); assert.equal(state.generated, 0); }
        else { assert(state.all > 0); assert.equal(state.event, mode === 'event-driven'); }
      }
    }
    result.push({mode, budget: initial.icons + initial.edges, events: initial.events.length, generated: initial.generated});
    await page.close();
    const reduced = await browser.newPage({reducedMotion: 'reduce'});
    await reduced.goto(pathToFileURL(path.join(directory, `motion-${mode}.html`)).href);
    assert.equal(await reduced.evaluate(() => __ANIDIAGRAM_TIMELINES__.length), 0, 'reduced motion created a timeline');
    await reduced.close();
  }
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ok: true, results: result}));
} finally { await browser.close(); }

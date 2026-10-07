/* Event scheduling and ambient budgets share the existing semantic performances.
   Every arrival is a child timeline, making backwards and forwards export seeks
   reproducible; no setTimeout callbacks create or restart node animations. */
  let iconHover = null;
  const iconHoverBindings = new WeakSet();
  function clearIconHover() {
    if (!iconHover) return;
    settleCharacterTimelines(iconHover.timelines);
    iconHover.timelines.forEach(timeline => timeline.kill());
    iconHover.victims.forEach(timeline => { timeline.__anidiagramHoverSuspended = false; if (!runtimePaused && !iconHover.wasPaused.get(timeline)) timeline.resume(); });
    const removed = new Set(iconHover.timelines);
    window.__ANIDIAGRAM_ICON_TIMELINES__ = (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).filter(timeline => !removed.has(timeline));
    iconHover = null;
    syncTimelineStore();
  }
  function registerIconHover(manifest) {
    (manifest.icons || []).forEach(config => {
      const node = document.getElementById(`node-${config.node_id}`);
      if (!node || iconHoverBindings.has(node)) return;
      iconHoverBindings.add(node);
      node.addEventListener('pointerenter', () => {
        if (runtimePaused) return;
        if (currentMotionMode === 'off' || manifest.mode === 'event-driven' || manifest.mode === 'timeline' || window.__ANIDIAGRAM_CHOREOGRAPHER_ACTIVE__) return;
        if (!manifest.stage.hover_icon_node_ids.includes(config.node_id) || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return;
        clearIconHover();
        const resident = window.__ANIDIAGRAM_ICON_TIMELINES__ || [];
        const lastId = resident.at(-1)?.__anidiagramNodeId;
        const victims = resident.filter(timeline => timeline.__anidiagramNodeId === lastId);
        const wasPaused = new Map(victims.map(timeline => [timeline, timeline.paused()]));
        settleCharacterTimelines(victims); victims.forEach(timeline => { timeline.__anidiagramHoverSuspended = true; timeline.pause(); });
        const timelines = (playIcon({...config, delay: 0}) || []).map(timeline => {
          timeline.repeat(0).delay(0); timeline.__anidiagramNodeId = config.node_id; return timeline;
        });
        iconHover = {timelines, victims, wasPaused};
        window.__ANIDIAGRAM_ICON_TIMELINES__ = [...resident, ...timelines];
        syncTimelineStore();
      });
      node.addEventListener('pointerleave', clearIconHover);
    });
  }
  function playAmbientIcons(manifest) {
    if (!manifest.stage?.motion_budget_contract) return manifest.icons.flatMap(config => playIcon(config) || []);
    registerIconHover(manifest);
    const selected = new Set(manifest.stage.active_icon_node_ids || []);
    const cycle = window.AniDiagramEdgeMotion?.period() || manifest.stage.beat_seconds || 4;
    return manifest.icons.filter(config => selected.has(config.node_id)).flatMap(config => (playIcon({...config, delay: 0}) || []).map(timeline => {
      const scale = timeline.timeScale() || 1;
      const beats = Math.ceil(Math.max(cycle, timeline.duration() / scale) / cycle);
      timeline.repeat(-1).repeatDelay(Math.max(0, cycle * beats * scale - timeline.duration())).delay(0);
      timeline.__anidiagramNodeId = config.node_id;
      timeline.__anidiagramBeat = cycle;
      return timeline;
    }));
  }
  function playEventDriven(manifest, profile = 'expressive') {
    if (!window.gsap || !window.AniDiagramEdgeMotion || profile === 'off' || manifest.profile === 'off' || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return [];
    window.AniDiagramEdgeMotion.clear();
    registerEventHover(manifest);
    const selected = new Set(manifest.event_driven?.edge_indices || manifest.stage.active_edge_indices || []);
    const pending = (manifest.edges || []).filter(entry => selected.has(entry.index) && entry.active);
    const configs = new Map(manifest.icons.map(config => [config.node_id, config]));
    const readyAt = new Map();
    const events = [];
    const iconTimelines = [];
    const timeline = window.gsap.timeline({repeat: -1});
    let serial = 0;
    // Topological traversal where possible, bounded traversal for cycles. A
    // signal's target performance finishes before its outgoing signal departs.
    while (pending.length) {
      let next = pending.findIndex(entry => !pending.some(other => other !== entry && other.target === entry.source));
      if (next < 0) next = 0;
      const entry = pending.splice(next, 1)[0];
      const start = Math.max(serial, readyAt.get(entry.source) || 0);
      const edge = window.AniDiagramEdgeMotion.create(entry, {repeat: 0, delay: 0, mode: profile});
      if (!edge) continue;
      timeline.add(edge, start);
      const arrival = start + edge.__anidiagramArrivalAt;
      let end = arrival + 0.15;
      const config = configs.get(entry.target);
      const performances = manifest.stage.icon_limit > 0 && config && entry.signal_semantic !== 'failure' ? playIcon({...config, delay: 0}) || [] : [];
      iconTimelines.push(...performances);
      performances.forEach(performance => {
        performance.repeat(0).delay(0);
        timeline.add(performance, end);
      });
      end += Math.max(0, ...performances.map(performance => performance.totalDuration() / (performance.timeScale() || 1)));
      serial = Math.max(start + edge.duration(), end);
      readyAt.set(entry.target, serial);
      events.push({edge_index: entry.index, source: entry.source, target: entry.target, start, arrival, feedback_end: arrival + 0.15, end: serial, icon: performances.length > 0});
    }
    const beat = Number(manifest.stage.beat_seconds) || 4;
    const cycle = Math.max(beat, Math.ceil(timeline.duration() / beat) * beat);
    if (timeline.duration() < cycle) timeline.to({}, {duration: cycle - timeline.duration()});
    timeline.__anidiagramStage = 'event-driven';
    timeline.__anidiagramEvents = events;
    window.__ANIDIAGRAM_EVENT_DRIVEN__ = {timeline, events, cycle, iconTimelines};
    window.__ANIDIAGRAM_STAGE_TIMELINES__ = [timeline];
    window.__ANIDIAGRAM_ICON_TIMELINES__ = [];
    return syncTimelineStore();
  }

  let eventHover = null;
  const eventHoverBindings = new WeakSet();
  function clearEventHover() {
    if (!eventHover) return;
    const previous = eventHover;
    eventHover = null;
    previous.timeline.kill();
    settleCharacterTimelines(previous.icons);
    previous.edge.__anidiagramGenerated.forEach(element => element.remove());
    previous.parent.__anidiagramHoverSuspended = false;
    if (!previous.wasPaused && !runtimePaused) previous.parent.resume();
    window.__ANIDIAGRAM_STAGE_TIMELINES__ = (window.__ANIDIAGRAM_STAGE_TIMELINES__ || []).filter(timeline => timeline !== previous.timeline);
    syncTimelineStore();
  }
  function registerEventHover(manifest) {
    document.querySelectorAll('g.edge').forEach((group, index) => {
      if (eventHoverBindings.has(group)) return;
      eventHoverBindings.add(group);
      group.addEventListener('pointerenter', () => {
        if (runtimePaused || currentMotionMode === 'off' || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return;
        if (!manifest.stage.hover_edge_indices.includes(index) || !window.__ANIDIAGRAM_EVENT_DRIVEN__) return;
        clearEventHover();
        const parent = window.__ANIDIAGRAM_EVENT_DRIVEN__.timeline;
        const wasPaused = parent.paused();
        parent.__anidiagramHoverSuspended = true;
        parent.pause();
        const entry = manifest.edges[index];
        const edge = window.AniDiagramEdgeMotion.create(entry, {repeat: 0, delay: 0, mode: currentMotionMode});
        if (!edge) { parent.__anidiagramHoverSuspended = false; if (!wasPaused) parent.resume(); return; }
        const timeline = window.gsap.timeline();
        timeline.add(edge, 0);
        const config = manifest.icons.find(icon => icon.node_id === entry.target);
        const icons = manifest.stage.icon_limit > 0 && config && entry.signal_semantic !== 'failure' ? playIcon({...config, delay: 0}) || [] : [];
        icons.forEach(icon => { icon.repeat(0).delay(0); timeline.add(icon, edge.__anidiagramArrivalAt + 0.15); });
        timeline.__anidiagramStage = 'event-hover';
        eventHover = {parent, wasPaused, timeline, icons, edge};
        window.__ANIDIAGRAM_STAGE_TIMELINES__.push(timeline);
        syncTimelineStore();
      });
      group.addEventListener('pointerleave', clearEventHover);
    });
  }

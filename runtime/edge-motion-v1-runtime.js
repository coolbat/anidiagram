(function () {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const manifestElement = document.getElementById("anidiagram-motion-manifest");
  if (!manifestElement) return;
  let manifest;
  try { manifest = JSON.parse(manifestElement.textContent || "{}"); }
  catch (error) { console.warn("AniDiagram Edge Motion: invalid manifest", error); return; }
  if (manifest.edge_motion_contract !== "edge-motion-v1") return;
  window.__ANIDIAGRAM_EDGE_MOTION_MANIFEST__ = manifest;
  let currentMode = "expressive";
  const hoverBindings = new WeakSet();
  let hoverState = null;
  function createSvgElement(name, attributes) {
    const element = document.createElementNS(SVG_NS, name);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, String(value)));
    return element;
  }
  function groups() { return Array.from(document.querySelectorAll("#viewport svg g.edge, #stage svg g.edge")); }
  function basePath(group) { return group?.querySelector("path.edge-base, path[id$='-path']"); }
  function metrics(entry, group) {
    const base = basePath(group);
    const length = Math.max(1, base?.getTotalLength?.() || 1);
    return { length, duration: length / (Number(entry.speed_px_per_second) || 180), departure: Number(entry.departure_delay) || 0 };
  }
  function period(entries = manifest.edges || []) {
    const edgeGroups = groups();
    const beat = Number(manifest.stage?.beat_seconds) || 4;
    const longest = Math.max(beat, ...entries.map(entry => {
      const value = metrics(entry, edgeGroups[entry.index]);
      return value.duration + value.departure + 0.3;
    }));
    return Math.ceil(longest / beat) * beat;
  }
  function insertBeforeLabel(group, element) {
    const label = group.querySelector(".edge-label");
    if (label) group.insertBefore(element, label); else group.appendChild(element);
  }
  function clearHover() {
    if (!hoverState) return;
    hoverState.timeline.kill();
    hoverState.timeline.__anidiagramGenerated.forEach(element => element.remove());
    if (hoverState.victim) {
      hoverState.victim.__anidiagramHoverSuspended = false;
      hoverState.victim.__anidiagramGenerated.forEach(element => element.style.removeProperty("visibility"));
      if (!window.__ANIDIAGRAM_USER_PAUSED__ && !document.querySelector("#viewer.motion-off") && !hoverState.wasPaused) hoverState.victim.resume();
    }
    const removed = hoverState.timeline;
    hoverState = null;
    sync((window.__ANIDIAGRAM_EDGE_MOTION_TIMELINES__ || []).filter(timeline => timeline !== removed));
  }
  function clear() {
    clearHover();
    document.querySelectorAll(".edge-motion-v1-generated").forEach(element => element.remove());
    (window.__ANIDIAGRAM_EDGE_MOTION_TIMELINES__ || []).forEach(timeline => timeline.kill());
    window.__ANIDIAGRAM_EDGE_MOTION_TIMELINES__ = [];
  }
  function sync(timelines) {
    const previous = (window.__ANIDIAGRAM_STAGE_TIMELINES__ || []).filter(timeline => timeline.__anidiagramStage !== "edge-motion");
    window.__ANIDIAGRAM_EDGE_MOTION_TIMELINES__ = timelines;
    window.__ANIDIAGRAM_STAGE_TIMELINES__ = [...previous, ...timelines];
    window.__ANIDIAGRAM_TIMELINES__ = [...window.__ANIDIAGRAM_STAGE_TIMELINES__, ...(window.__ANIDIAGRAM_ICON_TIMELINES__ || [])];
    return timelines;
  }
  function create(entry, options = {}) {
    const group = options.group || groups()[entry.index];
    const base = basePath(group);
    if (!base || !window.gsap || !entry.active) return null;
    const path = base.getAttribute("d");
    if (!path) return null;
    const timing = metrics(entry, group);
    const { length, duration, departure } = timing;
    const stroke = entry.signal_color || entry.color || base.getAttribute("stroke") || "#38bdf8";
    const width = Math.max(1, Number.parseFloat(base.getAttribute("stroke-width") || "2.4"));
    const kind = entry.motion_kind || "packet";
    if (!["stream", "draw", "comet", "packet"].includes(kind)) return null;
    const generated = [];
    const add = (name, attributes) => {
      const element = createSvgElement(name, { ...attributes, class: `${attributes.class || ''} edge-motion-v1-generated`, "pointer-events": "none" });
      insertBeforeLabel(group, element); generated.push(element); return element;
    };
    const repeat = options.repeat === undefined ? -1 : options.repeat;
    const beat = Number(manifest.stage?.beat_seconds) || 4;
    const authoredDelay = Math.ceil((Number(entry.delay) || 0) / beat) * beat;
    const timeline = window.gsap.timeline({ repeat, delay: options.delay === undefined ? authoredDelay : options.delay });
    const visibleOpacity = (options.mode || currentMode) === "readable" ? 0.78 : 1;
    if (entry.signal_semantic === "async") {
      add("path", { class: "runtime-edge-async-line", d: path, fill: "none", stroke, "stroke-width": width, "stroke-dasharray": "5 7", opacity: 0.65 });
    }
    if (kind === "stream") {
      const stream = add("path", { class: "runtime-edge-stream", d: path, fill: "none", stroke, "stroke-width": Math.max(1.2, width * 0.86).toFixed(1), "stroke-linecap": "round", "stroke-dasharray": "8 14", opacity: visibleOpacity });
      // Dash distance / time uses the same physical speed as discrete packets.
      const cycle = options.period || period();
      timeline.fromTo(stream, { attr: { "stroke-dashoffset": 0 } }, { attr: { "stroke-dashoffset": -(Number(entry.speed_px_per_second) || 180) * cycle }, duration: cycle, ease: "none" }, 0);
    } else if (kind === "draw") {
      const draw = add("path", { class: "runtime-edge-draw", d: path, fill: "none", stroke, "stroke-width": width, "stroke-linecap": "round", "stroke-dasharray": length, "stroke-dashoffset": length });
      timeline.to(draw, { attr: { "stroke-dashoffset": 0 }, duration, ease: "none" }, departure);
    } else {
      const comet = kind === "comet" ? add("g", {class: "runtime-edge-comet"}) : null;
      const count = kind === "comet" ? 4 : 1;
      const parts = Array.from({length: count}, (_, index) => add("circle", {
        class: kind === "comet" ? `runtime-edge-comet-${index === 0 ? 'head' : 'tail'}` : "edge-particle runtime-edge-packet",
        cx: 0, cy: 0, r: Math.max(1.8, Math.max(4.8, width * 1.8) * Math.pow(0.66, index)), fill: stroke, stroke: "none", opacity: 0,
      }));
      if (comet) parts.forEach(part => comet.appendChild(part));
      const travel = { distance: 0, visibility: 0 };
      const place = () => parts.forEach((part, index) => {
        // Tail spacing is in pixels, so short and long routes have equal tails.
        const distance = travel.distance - index * 8;
        const point = base.getPointAtLength(Math.max(0, Math.min(length, distance)));
        part.setAttribute("cx", point.x.toFixed(2)); part.setAttribute("cy", point.y.toFixed(2));
        part.setAttribute("opacity", distance < 0 || distance > length ? "0" : (travel.visibility * Math.pow(0.57, index)).toFixed(3));
      });
      place();
      timeline.to(travel, { distance: length, duration, ease: "none", onUpdate: place }, departure)
        .to(travel, { visibility: visibleOpacity, duration: Math.min(0.08, duration / 4), onUpdate: place }, departure);
      if (entry.signal_semantic === "failure") {
        timeline.to(travel, { distance: Math.max(0, length - 18), duration: 0.12, ease: "power1.out", onUpdate: place }, departure + duration)
          .to(travel, { visibility: 0, duration: 0.08, onUpdate: place }, departure + duration + 0.12);
      } else {
        timeline.to(travel, { visibility: 0, duration: 0.08, onUpdate: place }, departure + duration);
      }
    }
    const arrival = departure + duration;
    if (options.feedback !== false && kind !== "draw") {
      const point = base.getPointAtLength(length);
      const ring = add("circle", { class: "runtime-arrival-feedback", cx: point.x, cy: point.y, r: 2, fill: "none", stroke, "stroke-width": Math.max(1.5, width), opacity: 0 });
      timeline.fromTo(ring, { attr: {r: 2}, opacity: 0.8 }, { attr: {r: 13}, opacity: 0, duration: 0.15, ease: "power1.out", immediateRender: false }, arrival);
    }
    const cycle = options.period || period();
    if (repeat !== 0 && timeline.duration() < cycle) timeline.to({}, { duration: cycle - timeline.duration() });
    timeline.__anidiagramStage = "edge-motion";
    timeline.__anidiagramEdgeIndex = entry.index;
    timeline.__anidiagramEdgeEffect = entry.effect;
    timeline.__anidiagramEdgeKind = kind;
    timeline.__anidiagramArrivalAt = arrival;
    timeline.__anidiagramTravelSeconds = duration;
    timeline.__anidiagramPathLength = length;
    timeline.__anidiagramGenerated = generated;
    return timeline;
  }
  function bindHover() {
    groups().forEach((group, index) => {
      if (hoverBindings.has(group)) return;
      hoverBindings.add(group);
      const enter = () => {
        if (window.__ANIDIAGRAM_USER_PAUSED__) return;
        if (!manifest.stage?.hover_edge_indices?.includes(index) || currentMode === "off" || window.__ANIDIAGRAM_CHOREOGRAPHER_ACTIVE__ || manifest.mode === "event-driven" || manifest.mode === "timeline") return;
        if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
        clearHover();
        const resident = window.__ANIDIAGRAM_EDGE_MOTION_TIMELINES__ || [];
        const limit = currentMode === "readable" ? manifest.stage.readable_edge_limit : manifest.stage.edge_limit;
        if (!limit) return;
        const victim = resident.length >= limit ? resident[resident.length - 1] : null;
        const wasPaused = victim?.paused();
        if (victim) { victim.__anidiagramHoverSuspended = true; victim.pause(); victim.__anidiagramGenerated.forEach(element => element.style.visibility = "hidden"); }
        const timeline = create(manifest.edges[index], { repeat: 0, delay: 0, mode: currentMode });
        if (!timeline) return;
        hoverState = {timeline, victim, wasPaused};
        sync([...resident, timeline]);
      };
      group.addEventListener("pointerenter", enter);
      group.addEventListener("pointerleave", clearHover);
      group.addEventListener("focusin", enter);
      group.addEventListener("focusout", clearHover);
    });
  }
  function play(mode = "expressive") {
    currentMode = mode;
    if (manifest.mode === "event-driven") return [];
    clear(); bindHover();
    const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (mode === "off" || reduced || !manifest.stage?.edge_flow || ["event-driven", "timeline"].includes(manifest.mode) || window.__ANIDIAGRAM_CHOREOGRAPHER_ACTIVE__) return sync([]);
    const indices = mode === "readable" ? manifest.stage.readable_edge_indices || [] : manifest.stage.active_edge_indices || [];
    const cycle = period();
    return sync(indices.map(index => create(manifest.edges[index], {mode, period: cycle})).filter(Boolean));
  }
  window.AniDiagramEdgeMotion = { play, clear, create, metrics, period };
})();

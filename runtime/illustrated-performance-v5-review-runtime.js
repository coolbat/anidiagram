(function () {
  const CHARACTER_REPEAT_DELAY = 0.8;
  const EDGE_PACKET_DURATION = 1.65;
  const EDGE_COMET_DURATION = 1.85;
  const EDGE_STREAM_DURATION = 1.35;
  const SVG_NS = "http://www.w3.org/2000/svg";
  const performances = Object.create(null);

  function getManifest() {
    const element = document.getElementById("anidiagram-motion-manifest");
    if (!element) return null;
    try {
      return JSON.parse(element.textContent || "{}");
    } catch (error) {
      console.warn("AniDiagram Batch 4 review runtime: invalid manifest", error);
      return null;
    }
  }

  function resolveParts(config) {
    const resolved = Object.create(null);
    if (!config || !config.parts || typeof config.parts !== "object") return null;
    for (const [name, selector] of Object.entries(config.parts)) {
      if (typeof selector !== "string" || !selector) return null;
      let element;
      try {
        element = document.querySelector(selector);
      } catch (error) {
        return null;
      }
      if (!(element instanceof Element)) return null;
      resolved[name] = element;
    }
    const root = resolved.root;
    if (!(root instanceof Element)) return null;
    if (Object.values(resolved).some((part) => part !== root && !root.contains(part))) return null;
    return resolved;
  }

  function hasParts(parts, required) {
    return required.every((name) => Boolean(parts[name]));
  }

  function setInitial(parts, gsap) {
    Object.values(parts).forEach((part) => {
      if (!part) return;
      part.style.transformBox = "";
      if (part.dataset.restOpacity === undefined) {
        const opacity = Number(gsap.getProperty(part, "opacity"));
        part.dataset.restOpacity = String(Number.isFinite(opacity) ? opacity : 1);
      }
    });
    gsap.set(Object.values(parts).filter(Boolean), { transformOrigin: "center center" });
  }

  function primeStrokeDraw(paths, gsap) {
    const lengths = new Map();
    paths.forEach((path) => {
      const length = Math.max(1, path.getTotalLength ? path.getTotalLength() : 64);
      lengths.set(path, length);
      gsap.set(path, { strokeDasharray: length, strokeDashoffset: length });
    });
    return lengths;
  }

  function finishCharacterAtRest(timeline, parts, restAt) {
    const targets = Object.entries(parts)
      .filter(([name, part]) => name !== "root" && Boolean(part))
      .map(([, part]) => part);
    const motionShell = parts.root.querySelector(".illustrated-character-motion-shell");
    timeline.set(targets, {
      opacity: (index, target) => {
        const authored = Number(target.dataset.restOpacity);
        return Number.isFinite(authored) ? authored : 1;
      },
      x: 0,
      y: 0,
      rotation: 0,
      scaleX: 1,
      scaleY: 1,
      strokeDashoffset: 0,
    }, restAt);
    if (motionShell) {
      timeline.set(motionShell, { scale: 1, transformOrigin: "center center" }, restAt)
        .to(motionShell, { scale: 1.012, duration: 0.22, ease: "sine.inOut" }, restAt + 0.04)
        .to(motionShell, { scale: 1, duration: 0.22, ease: "sine.inOut" }, restAt + 0.26);
    }
    return timeline;
  }

  function playIllustratedVectorDatabase({ config, parts, gsap }) {
    const required = ["wash", "vector-store-body", "vector-store-top", "vector-field", "vector-links", "vector-points"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const linkLength = primeStrokeDraw([parts["vector-links"]], gsap).get(parts["vector-links"]);
    gsap.set(parts["vector-store-top"], { transformOrigin: "center bottom" });
    gsap.set([parts["vector-field"], parts["vector-points"]], { transformOrigin: "center center" });
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.to(parts["vector-store-body"], { scaleY: 0.965, duration: 0.14, ease: "power2.in" }, 0)
      .to(parts["vector-store-top"], { y: -6, scaleX: 1.055, duration: 0.22, ease: "back.out(2.8)" }, 0.1)
      .to(parts["vector-store-body"], { scaleY: 1.015, duration: 0.18, ease: "back.out(2.6)" }, 0.16)
      .to(parts["vector-store-body"], { scaleY: 1, duration: 0.18, ease: "power2.out" }, 0.34)
      .fromTo(parts["vector-links"],
        { opacity: 0.18, strokeDashoffset: linkLength },
        { opacity: 1, strokeDashoffset: 0, duration: 0.52, ease: "power1.inOut" }, 0.28)
      .fromTo(parts["vector-points"],
        { opacity: 0.3, scale: 0.58 },
        { opacity: 1, scale: 1.38, duration: 0.28, ease: "back.out(3.2)" }, 0.62)
      .to(parts["vector-points"], { scale: 1, duration: 0.22, ease: "elastic.out(1, 0.42)" }, 0.9)
      .to(parts["vector-field"], { scale: 1.035, y: -1.5, duration: 0.2, ease: "sine.inOut" }, 0.88)
      .to(parts["vector-field"], { scale: 1, y: 0, duration: 0.22, ease: "sine.inOut" }, 1.08)
      .to(parts["vector-store-top"], { y: 0, scaleX: 1, duration: 0.26, ease: "power2.out" }, 1.12);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  function playIllustratedKnowledgeBase({ config, parts, gsap }) {
    const required = ["wash", "book-left", "book-right", "book-spine", "knowledge-links", "knowledge-points", "reference-lines"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const lengths = primeStrokeDraw([parts["knowledge-links"], parts["reference-lines"]], gsap);
    gsap.set(parts["book-left"], { transformOrigin: "right bottom" });
    gsap.set(parts["book-right"], { transformOrigin: "left bottom" });
    gsap.set(parts["knowledge-points"], { transformOrigin: "center center" });
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.to(parts["book-left"], { rotation: -6, x: -3, duration: 0.28, ease: "power2.out" }, 0)
      .to(parts["book-right"], { rotation: 6, x: 3, duration: 0.28, ease: "power2.out" }, 0)
      .to([parts["book-left"], parts["book-right"]], { rotation: 0, x: 0, duration: 0.3, ease: "back.out(2.4)" }, 0.28)
      .fromTo(parts["knowledge-links"],
        { opacity: 0.16, strokeDashoffset: lengths.get(parts["knowledge-links"]) },
        { opacity: 1, strokeDashoffset: 0, duration: 0.58, ease: "power1.inOut" }, 0.32)
      .fromTo(parts["knowledge-points"],
        { opacity: 0.25, scale: 0.58 },
        { opacity: 1, scale: 1.34, duration: 0.28, ease: "back.out(3.1)" }, 0.7)
      .to(parts["knowledge-points"], { scale: 1, duration: 0.2, ease: "elastic.out(1, 0.42)" }, 0.98)
      .fromTo(parts["reference-lines"],
        { opacity: 0.2, strokeDashoffset: lengths.get(parts["reference-lines"]) },
        { opacity: 1, strokeDashoffset: 0, duration: 0.34, ease: "power2.out" }, 0.92)
      .to(parts["book-spine"], { scaleY: 1.06, duration: 0.16, ease: "sine.inOut" }, 1.18)
      .to(parts["book-spine"], { scaleY: 1, duration: 0.2, ease: "sine.inOut" }, 1.34);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  function playIllustratedGateway({ config, parts, gsap }) {
    const required = ["wash", "gateway-shell", "gateway-opening", "policy-window", "traffic-rails", "request-token", "response-token"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const railLength = primeStrokeDraw([parts["traffic-rails"]], gsap).get(parts["traffic-rails"]);
    gsap.set([parts["request-token"], parts["response-token"], parts["policy-window"]], { transformOrigin: "center center" });
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.to(parts["gateway-shell"], { scaleX: 0.975, scaleY: 1.025, duration: 0.16, ease: "power2.inOut" }, 0)
      .to(parts["gateway-shell"], { scaleX: 1, scaleY: 1, duration: 0.2, ease: "back.out(2.4)" }, 0.16)
      .fromTo(parts["traffic-rails"],
        { opacity: 0.22, strokeDashoffset: railLength },
        { opacity: 1, strokeDashoffset: 0, duration: 0.46, ease: "power1.inOut" }, 0.16)
      .fromTo(parts["request-token"],
        { y: 15, opacity: 0.25, scale: 0.7 },
        { y: -10, opacity: 1, scale: 1.18, duration: 0.44, ease: "power2.inOut" }, 0.34)
      .fromTo(parts["response-token"],
        { y: -15, opacity: 0.25, scale: 0.7 },
        { y: 10, opacity: 1, scale: 1.18, duration: 0.44, ease: "power2.inOut" }, 0.48)
      .to([parts["request-token"], parts["response-token"]], { y: 0, scale: 1, duration: 0.28, ease: "power2.out" }, 0.92)
      .to(parts["policy-window"], { scale: 1.22, duration: 0.18, ease: "back.out(3)" }, 1.0)
      .to(parts["policy-window"], { scale: 1, duration: 0.22, ease: "power2.out" }, 1.18)
      .to(parts["gateway-opening"], { scaleY: 1.025, duration: 0.16, ease: "sine.inOut" }, 1.22)
      .to(parts["gateway-opening"], { scaleY: 1, duration: 0.2, ease: "sine.inOut" }, 1.38);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  function playIllustratedContainer({ config, parts, gsap }) {
    const required = ["wash", "container-shell", "container-lid", "container-side", "container-ribs", "isolation-frame", "app-module", "runtime-slots", "container-feet"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    gsap.set([parts["isolation-frame"], parts["app-module"], parts["runtime-slots"]], { transformOrigin: "center center" });
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.to(parts["container-shell"], { y: 3, scaleY: 0.965, duration: 0.14, ease: "power2.in" }, 0)
      .to(parts["container-lid"], { y: -5, x: 2, duration: 0.22, ease: "back.out(2.8)" }, 0.1)
      .to(parts["container-side"], { x: 3, duration: 0.22, ease: "power2.out" }, 0.14)
      .to(parts["container-shell"], { y: 0, scaleY: 1, duration: 0.22, ease: "back.out(2.4)" }, 0.22)
      .fromTo(parts["isolation-frame"],
        { opacity: 0.45, scale: 0.84 },
        { opacity: 1, scale: 1.08, duration: 0.28, ease: "back.out(2.8)" }, 0.38)
      .fromTo(parts["app-module"],
        { opacity: 0.28, scale: 0.58, y: 8 },
        { opacity: 1, scale: 1.2, y: 0, duration: 0.32, ease: "back.out(3.2)" }, 0.58)
      .to(parts["app-module"], { scale: 1, duration: 0.2, ease: "elastic.out(1, 0.4)" }, 0.9)
      .fromTo(parts["runtime-slots"],
        { opacity: 0.22, scaleX: 0.35 },
        { opacity: 1, scaleX: 1.28, duration: 0.3, ease: "back.out(3)" }, 0.84)
      .to(parts["runtime-slots"], { scaleX: 1, duration: 0.2, ease: "power2.out" }, 1.14)
      .to(parts["isolation-frame"], { scale: 1, duration: 0.2, ease: "sine.inOut" }, 1.16)
      .to([parts["container-lid"], parts["container-side"]], { x: 0, y: 0, duration: 0.26, ease: "power2.out" }, 1.24)
      .to(parts["container-feet"], { scaleY: 1.08, duration: 0.14, ease: "sine.inOut" }, 1.3)
      .to(parts["container-feet"], { scaleY: 1, duration: 0.18, ease: "sine.inOut" }, 1.44);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  performances["illustrated-vector-database-embed-index-retrieve-v1"] = playIllustratedVectorDatabase;
  performances["illustrated-knowledge-base-curate-connect-reference-v1"] = playIllustratedKnowledgeBase;
  performances["illustrated-gateway-admit-route-mediate-v1"] = playIllustratedGateway;
  performances["illustrated-container-package-isolate-run-v1"] = playIllustratedContainer;

  function clearStageEffects() {
    document.querySelectorAll(".runtime-generated").forEach((element) => element.remove());
    document.querySelectorAll("[data-edge-motion-v1-opacity]").forEach((element) => {
      const previous = element.dataset.edgeMotionV1Opacity;
      if (previous) element.setAttribute("opacity", previous);
      else element.removeAttribute("opacity");
      delete element.dataset.edgeMotionV1Opacity;
    });
  }

  function playStageEdge(config) {
    const path = document.querySelector(config.path);
    const group = path && path.closest("g.edge");
    if (!path || !group || !path.getTotalLength) return null;
    const color = config.color || "#22d3ee";
    const effect = config.effect || "packet-flow";
    const motionKind = config.motion_kind || (effect === "stream-flow" ? "stream" : effect === "comet-flow" ? "comet" : effect === "draw" ? "draw" : "packet");
    const length = Math.max(1, path.getTotalLength());
    let timeline;
    if (motionKind === "stream") {
      path.dataset.edgeMotionV1Opacity = path.getAttribute("opacity") || "";
      path.setAttribute("opacity", "0.24");
      const stream = path.cloneNode(false);
      stream.removeAttribute("id");
      stream.removeAttribute("marker-end");
      stream.setAttribute("class", "runtime-generated edge-motion-v1-generated runtime-edge-stream");
      stream.setAttribute("fill", "none");
      stream.setAttribute("stroke", color);
      stream.setAttribute("stroke-width", "3");
      stream.setAttribute("stroke-linecap", "round");
      stream.setAttribute("stroke-dasharray", "8 14");
      stream.setAttribute("opacity", "0.88");
      stream.setAttribute("pointer-events", "none");
      group.append(stream);
      timeline = window.gsap.timeline({ repeat: -1, repeatDelay: 0 });
      timeline.fromTo(stream, { strokeDashoffset: 0 }, {
        strokeDashoffset: -44,
        duration: Number(config.duration) || EDGE_STREAM_DURATION,
        ease: "none",
      }, 0);
    } else if (motionKind === "draw") {
      path.dataset.edgeMotionV1Opacity = path.getAttribute("opacity") || "";
      path.setAttribute("opacity", "0.18");
      const draw = path.cloneNode(false);
      draw.removeAttribute("id");
      draw.removeAttribute("marker-end");
      draw.setAttribute("class", "runtime-generated edge-motion-v1-generated runtime-edge-draw");
      draw.setAttribute("stroke-dasharray", String(length));
      draw.setAttribute("stroke-dashoffset", String(length));
      group.append(draw);
      timeline = window.gsap.timeline();
      timeline.to(draw, { strokeDashoffset: 0, duration: 0.9, ease: "power1.out" }, 0);
    } else if (motionKind === "comet") {
      const comet = document.createElementNS(SVG_NS, "g");
      comet.setAttribute("class", "runtime-generated edge-motion-v1-generated runtime-edge-comet");
      comet.setAttribute("pointer-events", "none");
      const radii = [5.8, 4.2, 3, 2];
      const opacities = [1, 0.62, 0.38, 0.2];
      const parts = radii.map((radius, index) => {
        const part = document.createElementNS(SVG_NS, "circle");
        part.setAttribute("class", index === 0 ? "runtime-edge-comet-head" : "runtime-edge-comet-tail");
        part.setAttribute("r", String(radius));
        part.setAttribute("fill", color);
        part.setAttribute("stroke", "none");
        part.setAttribute("opacity", "0");
        comet.append(part);
        return part;
      });
      group.append(comet);
      const progress = { value: 0 };
      const updateComet = () => {
        parts.forEach((part, index) => {
          const local = progress.value - index * 0.045;
          if (local < 0 || local > 1) {
            part.setAttribute("opacity", "0");
            return;
          }
          const point = path.getPointAtLength(length * local);
          const edgeFade = Math.min(1, local / 0.055, (1 - local) / 0.055);
          part.setAttribute("cx", point.x.toFixed(2));
          part.setAttribute("cy", point.y.toFixed(2));
          part.setAttribute("opacity", Math.max(0, opacities[index] * edgeFade).toFixed(2));
        });
      };
      updateComet();
      timeline = window.gsap.timeline({ repeat: -1, repeatDelay: 0 });
      timeline.to(progress, {
        value: 1,
        duration: Number(config.duration) || EDGE_COMET_DURATION,
        ease: "none",
        onUpdate: updateComet,
      }, 0);
    } else {
      const packet = document.createElementNS(SVG_NS, "circle");
      packet.setAttribute("class", "runtime-generated edge-motion-v1-generated runtime-edge-packet");
      packet.setAttribute("r", "5.5");
      packet.setAttribute("fill", color);
      packet.setAttribute("stroke", "none");
      packet.setAttribute("opacity", "0");
      packet.setAttribute("pointer-events", "none");
      group.append(packet);
      const progress = { value: 0 };
      const updatePacket = () => {
        const point = path.getPointAtLength(length * progress.value);
        packet.setAttribute("cx", point.x.toFixed(2));
        packet.setAttribute("cy", point.y.toFixed(2));
      };
      updatePacket();
      const duration = Number(config.duration) || EDGE_PACKET_DURATION;
      timeline = window.gsap.timeline({ repeat: -1, repeatDelay: 0 });
      timeline.to(progress, { value: 1, duration, ease: "none", onUpdate: updatePacket }, 0)
        .to(packet, { opacity: 1, duration: 0.12, ease: "power1.out" }, 0)
        .to(packet, { opacity: 0, duration: 0.12, ease: "power1.in" }, duration - 0.12);
    }
    if (config.delay) timeline.delay(config.delay);
    timeline.__anidiagramStage = "edge-motion";
    timeline.__anidiagramEdgeIndex = config.index;
    timeline.__anidiagramEdgeEffect = effect;
    timeline.__anidiagramEdgeKind = motionKind;
    return timeline;
  }

  function playStageEffects(manifest, mode) {
    if (!manifest || !manifest.stage || !manifest.stage.edge_flow) return [];
    const indices = mode === "readable"
      ? manifest.stage.readable_edge_indices || []
      : manifest.stage.active_edge_indices || [];
    const entries = new Map((manifest.edges || []).map((entry) => [entry.index, entry]));
    return indices.map((index) => playStageEdge(entries.get(index) || {})).filter(Boolean);
  }

  function settle(timeline) {
    if (!timeline || !timeline.__anidiagramCharacter) return;
    timeline.pause();
    timeline.seek(timeline.__anidiagramCharacter.restAt, false);
  }

  function syncStore(iconTimelines, stageTimelines) {
    window.__ANIDIAGRAM_ICON_TIMELINES__ = iconTimelines;
    window.__ANIDIAGRAM_STAGE_TIMELINES__ = stageTimelines;
    window.__ANIDIAGRAM_TIMELINES__ = [...iconTimelines, ...stageTimelines];
    return window.__ANIDIAGRAM_TIMELINES__;
  }

  function stop() {
    (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).forEach(settle);
    (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).forEach((timeline) => timeline.kill());
    (window.__ANIDIAGRAM_STAGE_TIMELINES__ || []).forEach((timeline) => timeline.kill());
    clearStageEffects();
    return syncStore([], []);
  }

  function play(mode = "expressive") {
    const manifest = getManifest();
    stop();
    if (!manifest || !Array.isArray(manifest.icons) || !window.gsap) return [];
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return [];
    const timelines = [];
    manifest.icons.forEach((config) => {
      const fn = performances[config.performance];
      const parts = resolveParts(config);
      if (!fn || !parts) return;
      const timeline = fn({ config, parts, gsap: window.gsap });
      if (!timeline) return;
      timeline.__anidiagramCharacter = {
        nodeId: config.node_id,
        performance: config.performance,
        restAt: config.rest_at,
      };
      if (config.delay) timeline.delay(config.delay);
      timelines.push(timeline);
    });
    return syncStore(timelines, playStageEffects(manifest, mode));
  }

  function pause() {
    (window.__ANIDIAGRAM_TIMELINES__ || []).forEach((timeline) => timeline.pause());
  }

  function resume() {
    (window.__ANIDIAGRAM_TIMELINES__ || []).forEach((timeline) => timeline.resume());
  }

  function restart() {
    (window.__ANIDIAGRAM_TIMELINES__ || []).forEach((timeline) => timeline.restart());
  }

  function wireViewer() {
    const viewer = document.getElementById("viewer");
    const stage = document.getElementById("stage");
    const viewport = document.getElementById("viewport");
    const svg = viewport && viewport.querySelector("svg");
    if (!viewer || !stage || !viewport || !svg) return;
    let scale = 1;
    let x = 0;
    let y = 0;
    let dragging = false;
    let lastX = 0;
    let lastY = 0;
    let paused = false;
    const applyTransform = () => {
      viewport.style.transform = `translate(${x}px, ${y}px) scale(${scale})`;
    };
    const toggle = document.getElementById("toggle");
    if (toggle) {
      toggle.addEventListener("click", () => {
        paused = !paused;
        if (paused) pause(); else resume();
        toggle.textContent = paused ? "Play" : "Pause";
      });
    }
    const restartButton = document.getElementById("restart");
    if (restartButton) restartButton.addEventListener("click", () => { restart(); paused = false; if (toggle) toggle.textContent = "Pause"; });
    document.querySelectorAll(".motion-choice").forEach((button) => {
      button.addEventListener("click", () => {
        const mode = button.dataset.motion;
        viewer.classList.remove("motion-expressive", "motion-readable", "motion-off");
        viewer.classList.add(`motion-${mode}`);
        document.querySelectorAll(".motion-choice").forEach((choice) => {
          choice.setAttribute("aria-pressed", String(choice.dataset.motion === mode));
        });
        if (mode === "off") stop(); else play(mode);
        paused = mode === "off";
        if (toggle) toggle.textContent = paused ? "Play" : "Pause";
      });
    });
    document.getElementById("zoom-in")?.addEventListener("click", () => { scale = Math.min(3, scale + 0.15); applyTransform(); });
    document.getElementById("zoom-out")?.addEventListener("click", () => { scale = Math.max(0.35, scale - 0.15); applyTransform(); });
    document.getElementById("reset")?.addEventListener("click", () => { scale = 1; x = 0; y = 0; applyTransform(); });
    stage.addEventListener("pointerdown", (event) => {
      dragging = true;
      lastX = event.clientX;
      lastY = event.clientY;
      stage.classList.add("dragging");
      stage.setPointerCapture(event.pointerId);
    });
    stage.addEventListener("pointermove", (event) => {
      if (!dragging) return;
      x += event.clientX - lastX;
      y += event.clientY - lastY;
      lastX = event.clientX;
      lastY = event.clientY;
      applyTransform();
    });
    stage.addEventListener("pointerup", () => { dragging = false; stage.classList.remove("dragging"); });
    const download = document.getElementById("download");
    if (download) {
      const blob = new Blob([new XMLSerializer().serializeToString(svg)], { type: "image/svg+xml" });
      download.href = URL.createObjectURL(blob);
    }
  }

  window.AniDiagramRuntime = { play, pause, resume, restart, stop };
  window.__ANIDIAGRAM_ICON_TIMELINES__ = [];
  window.__ANIDIAGRAM_STAGE_TIMELINES__ = [];
  window.__ANIDIAGRAM_TIMELINES__ = [];
  document.addEventListener("DOMContentLoaded", () => {
    wireViewer();
    play();
  });
})();

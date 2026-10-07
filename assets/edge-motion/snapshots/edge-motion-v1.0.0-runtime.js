(function () {
  const EDGE_PACKET_DURATION = 1.65;
  const EDGE_COMET_DURATION = 1.85;
  const EDGE_STREAM_DURATION = 1.35;
  const SVG_NS = "http://www.w3.org/2000/svg";
  const manifestElement = document.getElementById("anidiagram-motion-manifest");
  if (!manifestElement) return;
  let manifest;
  try {
    manifest = JSON.parse(manifestElement.textContent || "{}");
  } catch (error) {
    console.warn("AniDiagram Edge Motion v1: invalid manifest", error);
    return;
  }
  if (manifest.edge_motion_contract !== "edge-motion-v1") return;
  window.__ANIDIAGRAM_EDGE_MOTION_MANIFEST__ = manifest;
  const legacyManifest = JSON.parse(JSON.stringify(manifest));
  if (legacyManifest.stage) legacyManifest.stage.edge_flow = false;
  const edgeManifestSource = JSON.stringify(manifest);
  const legacyManifestSource = JSON.stringify(legacyManifest);
  manifestElement.textContent = legacyManifestSource;

  function createSvgElement(name, attributes) {
    const element = document.createElementNS(SVG_NS, name);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, String(value)));
    return element;
  }

  function insertBeforeLabel(group, element) {
    const label = group.querySelector(".edge-label");
    if (label) group.insertBefore(element, label);
    else group.appendChild(element);
  }

  function clear() {
    document.querySelectorAll(".edge-motion-v1-generated").forEach((element) => element.remove());
    document.querySelectorAll("[data-edge-motion-v1-opacity]").forEach((element) => {
      const previous = element.dataset.edgeMotionV1Opacity;
      if (previous) element.setAttribute("opacity", previous);
      else element.removeAttribute("opacity");
      delete element.dataset.edgeMotionV1Opacity;
    });
    (window.__ANIDIAGRAM_EDGE_MOTION_TIMELINES__ || []).forEach((timeline) => timeline.kill());
    window.__ANIDIAGRAM_EDGE_MOTION_TIMELINES__ = [];
  }

  function sync(timelines) {
    const previous = (window.__ANIDIAGRAM_STAGE_TIMELINES__ || []).filter(
      (timeline) => timeline.__anidiagramStage !== "edge-motion"
    );
    window.__ANIDIAGRAM_EDGE_MOTION_TIMELINES__ = timelines;
    window.__ANIDIAGRAM_STAGE_TIMELINES__ = [...previous, ...timelines];
    window.__ANIDIAGRAM_TIMELINES__ = [
      ...window.__ANIDIAGRAM_STAGE_TIMELINES__,
      ...(window.__ANIDIAGRAM_ICON_TIMELINES__ || []),
    ];
    return timelines;
  }

  function playEdge(entry, group, mode) {
    const base = group.querySelector("path.edge-base, path[id$='-path']");
    if (!base || !base.getTotalLength || !window.gsap) return null;
    const path = base.getAttribute("d");
    if (!path) return null;
    const length = Math.max(1, base.getTotalLength());
    const stroke = entry.color || base.getAttribute("stroke") || "#38bdf8";
    const width = Math.max(1, Number.parseFloat(base.getAttribute("stroke-width") || "2.4"));
    const kind = entry.motion_kind || "packet";
    const delay = Number(entry.delay) || 0;
    let timeline;
    if (kind === "stream") {
      const authoredLine = group.querySelector("path.edge-draw");
      if (authoredLine) {
        authoredLine.dataset.edgeMotionV1Opacity = authoredLine.getAttribute("opacity") || "";
        authoredLine.setAttribute("opacity", "0.24");
      }
      const stream = createSvgElement("path", {
        class: "runtime-edge-stream edge-motion-v1-generated",
        d: path,
        fill: "none",
        stroke,
        "stroke-width": Math.max(1.2, width * 0.86).toFixed(1),
        "stroke-linecap": "round",
        "stroke-dasharray": "8 14",
        opacity: mode === "readable" ? "0.68" : "0.88",
        "pointer-events": "none",
      });
      insertBeforeLabel(group, stream);
      timeline = window.gsap.timeline({ repeat: -1, repeatDelay: 0, delay });
      timeline.fromTo(stream, { attr: { "stroke-dashoffset": 0 } }, {
        attr: { "stroke-dashoffset": -44 },
        duration: Number(entry.duration) || EDGE_STREAM_DURATION,
        ease: "none",
      }, 0);
    } else if (kind === "draw") {
      const authoredLine = group.querySelector("path.edge-draw");
      if (authoredLine) {
        authoredLine.dataset.edgeMotionV1Opacity = authoredLine.getAttribute("opacity") || "";
        authoredLine.setAttribute("opacity", "0.18");
      }
      const draw = createSvgElement("path", {
        class: "runtime-edge-draw edge-motion-v1-generated",
        d: path,
        fill: "none",
        stroke,
        "stroke-width": width.toFixed(1),
        "stroke-linecap": "round",
        "stroke-dasharray": length.toFixed(2),
        "stroke-dashoffset": length.toFixed(2),
        "pointer-events": "none",
      });
      insertBeforeLabel(group, draw);
      timeline = window.gsap.timeline({ delay });
      timeline.to(draw, { attr: { "stroke-dashoffset": 0 }, duration: 0.9, ease: "power1.out" }, 0);
    } else if (kind === "comet") {
      const comet = createSvgElement("g", {
        class: "runtime-edge-comet edge-motion-v1-generated",
        "pointer-events": "none",
      });
      const radii = [Math.max(5.2, width * 1.9), Math.max(3.8, width * 1.42), Math.max(2.7, width), Math.max(1.8, width * 0.68)];
      const baseOpacities = mode === "readable" ? [0.82, 0.5, 0.3, 0.16] : [1, 0.62, 0.38, 0.2];
      const parts = radii.map((radius, index) => {
        const part = createSvgElement("circle", {
          class: index === 0 ? "runtime-edge-comet-head" : "runtime-edge-comet-tail",
          cx: "0",
          cy: "0",
          r: radius.toFixed(1),
          fill: stroke,
          stroke: "none",
          opacity: "0",
        });
        comet.appendChild(part);
        return part;
      });
      insertBeforeLabel(group, comet);
      const travel = { progress: 0 };
      const placeComet = () => {
        parts.forEach((part, index) => {
          const local = travel.progress - index * 0.045;
          if (local < 0 || local > 1) {
            part.setAttribute("opacity", "0");
            return;
          }
          const point = base.getPointAtLength(local * length);
          const edgeFade = Math.min(1, local / 0.055, (1 - local) / 0.055);
          part.setAttribute("cx", point.x.toFixed(2));
          part.setAttribute("cy", point.y.toFixed(2));
          part.setAttribute("opacity", Math.max(0, baseOpacities[index] * edgeFade).toFixed(2));
        });
      };
      placeComet();
      timeline = window.gsap.timeline({ repeat: -1, repeatDelay: 0, delay });
      timeline.to(travel, {
        progress: 1,
        duration: Number(entry.duration) || EDGE_COMET_DURATION,
        ease: "none",
        onUpdate: placeComet,
      }, 0);
    } else if (kind === "packet") {
      const packet = createSvgElement("circle", {
        class: "edge-particle runtime-edge-packet edge-motion-v1-generated",
        cx: "0",
        cy: "0",
        r: Math.max(4.8, width * 1.8).toFixed(1),
        fill: stroke,
        stroke: "none",
        opacity: "0",
        "pointer-events": "none",
      });
      insertBeforeLabel(group, packet);
      const travel = { distance: 0 };
      const placePacket = () => {
        const point = base.getPointAtLength(travel.distance);
        packet.setAttribute("cx", point.x.toFixed(2));
        packet.setAttribute("cy", point.y.toFixed(2));
      };
      placePacket();
      const duration = Number(entry.duration) || EDGE_PACKET_DURATION;
      timeline = window.gsap.timeline({ repeat: -1, repeatDelay: 0, delay });
      timeline.to(travel, { distance: length, duration, ease: "none", onUpdate: placePacket }, 0)
        .to(packet, { opacity: mode === "readable" ? 0.78 : 1, duration: 0.12, ease: "power1.out" }, 0)
        .to(packet, { opacity: 0, duration: 0.12, ease: "power1.in" }, duration - 0.12);
    } else {
      return null;
    }
    timeline.__anidiagramStage = "edge-motion";
    timeline.__anidiagramEdgeIndex = entry.index;
    timeline.__anidiagramEdgeEffect = entry.effect;
    timeline.__anidiagramEdgeKind = kind;
    return timeline;
  }

  function play(mode = "expressive") {
    clear();
    const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (mode === "off" || reduced || !manifest.stage || !manifest.stage.edge_flow) return sync([]);
    const indices = mode === "readable"
      ? manifest.stage.readable_edge_indices || []
      : manifest.stage.active_edge_indices || [];
    const groups = Array.from(document.querySelectorAll("#viewport svg g.edge, #stage svg g.edge"));
    const entries = new Map((manifest.edges || []).map((entry) => [entry.index, entry]));
    return sync(indices.map((index) => playEdge(entries.get(index) || {}, groups[index], mode)).filter(Boolean));
  }

  document.addEventListener("click", (event) => {
    if (!event.target.closest || !event.target.closest(".motion-choice")) return;
    manifestElement.textContent = legacyManifestSource;
    setTimeout(() => { manifestElement.textContent = edgeManifestSource; }, 0);
  }, true);

  document.addEventListener("DOMContentLoaded", () => {
    manifestElement.textContent = edgeManifestSource;
    play("expressive");
    document.querySelectorAll(".motion-choice").forEach((button) => {
      button.addEventListener("click", () => play(button.dataset.motion || "expressive"));
    });
  });
  window.AniDiagramEdgeMotion = { play, clear };
})();

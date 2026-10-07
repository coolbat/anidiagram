/* Decorative stage effects; assembled in the shared runtime closure. */
  function createSvgElement(name, attrs) {
    const el = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attrs || {}).forEach(([key, value]) => {
      el.setAttribute(key, String(value));
    });
    return el;
  }

  function numberAttr(el, name, fallback) {
    const value = Number.parseFloat(el.getAttribute(name) || "");
    return Number.isFinite(value) ? value : fallback;
  }

  const EDGE_PACKET_COUNT = 1;
  const EDGE_PACKET_REPEAT_DELAY = 0.0;
  const SHORT_EDGE_THRESHOLD = 120;
  let currentMotionMode = "expressive";

  function clearRuntimeStageEffects() {
    document.querySelectorAll(".runtime-generated").forEach((el) => el.remove());
    const highlight = document.querySelector("#viewport svg #title-highlight");
    if (highlight && highlight.dataset.runtimeTitleWidth) {
      highlight.setAttribute("x", highlight.dataset.runtimeTitleX || highlight.getAttribute("x") || "72");
      highlight.setAttribute("width", highlight.dataset.runtimeTitleWidth);
      highlight.style.removeProperty("opacity");
      highlight.style.removeProperty("transform");
      highlight.style.removeProperty("transform-origin");
    }
  }

  function playTitleSweep(svg, manifest, gsap) {
    if (!manifest.stage || !manifest.stage.title_sweep) return [];
    const highlight = svg.querySelector("#title-highlight");
    if (!highlight) return [];
    const x = numberAttr(highlight, "x", 72);
    const width = Math.max(120, numberAttr(highlight, "width", 360));
    highlight.dataset.runtimeTitleX = String(x);
    highlight.dataset.runtimeTitleWidth = String(width);
    gsap.set(highlight, { attr: { x, width }, scaleX: 0, opacity: 0.08, transformOrigin: "left center" });
    const tl = gsap.timeline();
    tl.to(highlight, { scaleX: 1, opacity: 0.16, duration: 0.55, ease: "power2.out" })
      .to(highlight, { opacity: 0, duration: 0.25, ease: "power1.out" });
    tl.__anidiagramStage = "title-entry";
    return [tl];
  }

  function playRuntimeEdgeFlow(svg, manifest, gsap, motionMode = "expressive") {
    if (manifest.edge_motion_contract === "edge-motion-v1") return [];
    if (!manifest.stage || !manifest.stage.edge_flow) return [];
    const edgeGroups = Array.from(svg.querySelectorAll("g.edge"));
    const edgeEntries = Array.isArray(manifest.edges) ? manifest.edges : [];
    const configuredIndices = motionMode === "readable"
      ? manifest.stage.readable_edge_indices
      : manifest.stage.active_edge_indices;
    let activeEdges;
    if (Array.isArray(configuredIndices)) {
      activeEdges = configuredIndices
        .filter((edgeIndex) => Number.isInteger(edgeIndex) && edgeIndex >= 0 && edgeGroups[edgeIndex])
        .map((edgeIndex) => ({ group: edgeGroups[edgeIndex], edgeIndex, entry: edgeEntries[edgeIndex] || {} }));
    } else {
      const requestedLimit = motionMode === "readable" ? manifest.stage.readable_edge_limit : manifest.stage.edge_limit;
      activeEdges = edgeGroups
        .map((group, edgeIndex) => ({ group, edgeIndex, entry: edgeEntries[edgeIndex] || {} }))
        .filter((item) => !Number.isInteger(requestedLimit) || item.edgeIndex < Math.max(0, requestedLimit));
    }
    const timelines = [];
    activeEdges.forEach(({ group, edgeIndex, entry }) => {
      const base = group.querySelector("path.edge-base");
      if (!base || !base.getTotalLength) return;
      const length = Math.max(1, base.getTotalLength());
      const path = base.getAttribute("d");
      if (!path) return;
      const stroke = base.getAttribute("stroke") || "#38bdf8";
      const width = Math.max(1, numberAttr(base, "stroke-width", 2.4));
      const label = group.querySelector(".edge-label");
      const effect = String(entry.effect || "signal-arrow").replace(/[^a-z0-9-]/gi, "-").toLowerCase();
      const dotEffect = effect === "signal-dot" || effect === "flow-dot";
      const dashEffect = effect === "dynamic-dash" || effect === "dash-flow" || effect === "trace" || effect === "draw";
      const flowDash = Math.max(2.4, width * 1.4);
      const flowGap = Math.max(12, width * 7);
      const shortEdge = length <= SHORT_EDGE_THRESHOLD;
      group.dataset.runtimeEdgeEffect = effect;
      group.dataset.runtimeEdgePacketShape = shortEdge ? "dot" : "segment";
      const flow = createSvgElement("path", {
        class: `edge-flow runtime-edge-flow runtime-edge-effect-${effect} runtime-generated`,
        d: path,
        fill: "none",
        stroke,
        "stroke-width": Math.max(1.2, width * 0.86).toFixed(1),
        "stroke-linecap": "round",
        "stroke-dasharray": `${flowDash.toFixed(1)} ${flowGap.toFixed(1)}`,
        "stroke-dashoffset": "0",
        opacity: motionMode === "readable" ? "0.09" : "0.20",
        "pointer-events": "none",
      });
      if (label) group.insertBefore(flow, label);
      else group.appendChild(flow);
      for (let particleIndex = 0; particleIndex < EDGE_PACKET_COUNT; particleIndex += 1) {
        const packetLength = dotEffect
          ? Math.max(1.8, width * 0.55)
          : dashEffect
            ? Math.max(8, Math.min(20, length * 0.18))
            : Math.max(13, Math.min(34, length * 0.42));
        const packetGap = Math.max(52, length + packetLength * 2.8);
        const packet = shortEdge
          ? createSvgElement("circle", {
              class: `edge-particle runtime-edge-particle runtime-edge-packet runtime-edge-short-packet runtime-edge-effect-${effect} runtime-generated`,
              cx: "0",
              cy: "0",
              r: Math.max(4.5, width * 2.2).toFixed(1),
              fill: stroke,
              opacity: "0",
              "pointer-events": "none",
            })
          : createSvgElement("path", {
              class: `edge-particle runtime-edge-particle runtime-edge-packet runtime-edge-effect-${effect} runtime-generated`,
              d: path,
              fill: "none",
              stroke: "#ffffff",
              "stroke-width": Math.max(4.2, width * (2.35 - particleIndex * 0.22)).toFixed(1),
              "stroke-linecap": "round",
              "stroke-linejoin": "round",
              "stroke-dasharray": `${packetLength.toFixed(1)} ${packetGap.toFixed(1)}`,
              "stroke-dashoffset": packetGap.toFixed(1),
              opacity: "0",
              "pointer-events": "none",
            });
        const core = shortEdge
          ? createSvgElement("circle", {
              class: `edge-particle runtime-edge-particle runtime-edge-packet-core runtime-edge-short-packet-core runtime-edge-effect-${effect} runtime-generated`,
              cx: "0",
              cy: "0",
              r: Math.max(3.0, width * 1.45).toFixed(1),
              fill: stroke,
              opacity: "0",
              "pointer-events": "none",
            })
          : createSvgElement("path", {
              class: `edge-particle runtime-edge-particle runtime-edge-packet-core runtime-edge-effect-${effect} runtime-generated`,
              d: path,
              fill: "none",
              stroke,
              "stroke-width": Math.max(2.6, width * (1.48 - particleIndex * 0.14)).toFixed(1),
              "stroke-linecap": "round",
              "stroke-linejoin": "round",
              "stroke-dasharray": `${(dotEffect ? Math.max(1.2, width * 0.35) : Math.max(6, packetLength * 0.62)).toFixed(1)} ${packetGap.toFixed(1)}`,
              "stroke-dashoffset": packetGap.toFixed(1),
              opacity: "0",
              "pointer-events": "none",
            });
        if (label) {
          group.insertBefore(packet, label);
          group.insertBefore(core, label);
        } else {
          group.appendChild(packet);
          group.appendChild(core);
        }
        const duration = 2.05 + ((edgeIndex + particleIndex) % 5) * 0.13;
        const semanticDelay = Number.isFinite(Number(entry.delay)) ? Number(entry.delay) : 0;
        const delay = semanticDelay;
        const tl = gsap.timeline({ repeat: -1, repeatDelay: EDGE_PACKET_REPEAT_DELAY, delay });
        tl.fromTo(
          flow,
          { attr: { "stroke-dashoffset": 0 } },
          { attr: { "stroke-dashoffset": -(flowDash + flowGap) }, duration, ease: "none" },
          0
        );
        if (shortEdge) {
          const travel = { distance: 0 };
          const placeDot = () => {
            const point = base.getPointAtLength(travel.distance);
            packet.setAttribute("cx", point.x.toFixed(2));
            packet.setAttribute("cy", point.y.toFixed(2));
            core.setAttribute("cx", point.x.toFixed(2));
            core.setAttribute("cy", point.y.toFixed(2));
          };
          placeDot();
          tl.to(travel, { distance: length, duration, ease: "none", onUpdate: placeDot }, 0);
        } else {
          tl.fromTo(
            [packet, core],
            { attr: { "stroke-dashoffset": packetGap + packetLength } },
            { attr: { "stroke-dashoffset": -(length + packetLength) }, duration, ease: "none" },
            0
          );
        }
        tl.to(packet, { opacity: motionMode === "readable" ? 0.62 : 0.86, duration: 0.14, ease: "power1.out" }, 0)
          .to(core, { opacity: motionMode === "readable" ? 0.82 : 1, duration: 0.14, ease: "power1.out" }, 0)
          .to([packet, core], { opacity: 0, duration: 0.14, ease: "power1.in" }, Math.max(0, duration - 0.14));
        tl.__anidiagramStage = "edge-packet";
        tl.__anidiagramEdgeIndex = edgeIndex;
        tl.__anidiagramEdgeEffect = effect;
        timelines.push(tl);
      }
    });
    return timelines;
  }

  function playRuntimeRelationCircles(svg, manifest, gsap) {
    if (manifest.stage?.motion_budget_contract) return [];
    if (!manifest.stage || !manifest.stage.relation_circles) return [];
    const timelines = [];
    const edgeGroups = Array.from(svg.querySelectorAll("g.edge"));
    const firstEdge = edgeGroups[0] || null;
    edgeGroups.forEach((group, edgeIndex) => {
      if (edgeIndex % 2 !== 0) return;
      const base = group.querySelector("path.edge-base");
      if (!base || !base.getBBox) return;
      const box = base.getBBox();
      const width = Math.max(44, box.width + 24);
      const height = Math.max(32, box.height + 20);
      if (width > 520 || height > 320) return;
      const stroke = base.getAttribute("stroke") || "#7aa8ff";
      const ring = createSvgElement("ellipse", {
        class: "runtime-relation-circle runtime-generated",
        cx: (box.x + box.width / 2).toFixed(1),
        cy: (box.y + box.height / 2).toFixed(1),
        rx: (width / 2).toFixed(1),
        ry: (height / 2).toFixed(1),
        fill: "none",
        stroke,
        "stroke-width": "1.5",
        "stroke-dasharray": "7 8",
        "stroke-dashoffset": "0",
        opacity: "0.18",
        "pointer-events": "none",
      });
      if (firstEdge) svg.insertBefore(ring, firstEdge);
      else svg.appendChild(ring);
      timelines.push(
        gsap.to(ring, {
          attr: { "stroke-dashoffset": -48 },
          opacity: 0.34,
          duration: 4.8 + (edgeIndex % 3) * 0.35,
          yoyo: true,
          repeat: -1,
          ease: "sine.inOut",
        })
      );
    });
    return timelines;
  }

  function playRuntimeGroupFields(svg, manifest, gsap) {
    if (!manifest.stage || !manifest.stage.group_fields) return [];
    return [];
  }

  function playStageEffects(manifest, motionMode = "expressive") {
    if (!window.gsap) return [];
    const svg = document.querySelector("#viewport svg");
    if (!svg) return [];
    clearRuntimeStageEffects();
    if (motionMode === "off") return [];
    return [
      ...(motionMode === "expressive" ? playTitleSweep(svg, manifest, window.gsap) : []),
      ...playRuntimeEdgeFlow(svg, manifest, window.gsap, motionMode),
      ...(motionMode === "expressive" ? playRuntimeRelationCircles(svg, manifest, window.gsap) : []),
      ...(motionMode === "expressive" ? playRuntimeGroupFields(svg, manifest, window.gsap) : []),
    ];
  }


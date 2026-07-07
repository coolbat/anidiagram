(function () {
  function getManifest() {
    const el = document.getElementById("anidiagram-motion-manifest");
    if (!el) return null;
    try {
      return JSON.parse(el.textContent || "{}");
    } catch (error) {
      console.warn("AniDiagram runtime: invalid motion manifest", error);
      return null;
    }
  }

  function resolveParts(parts) {
    const resolved = {};
    Object.entries(parts || {}).forEach(([key, selector]) => {
      resolved[key] = document.querySelector(selector);
    });
    return resolved;
  }

  function hasParts(parts, required) {
    return required.every((name) => Boolean(parts[name]));
  }

  function setInitial(parts, gsap) {
    Object.values(parts).forEach((part) => {
      if (part) part.style.transformBox = "";
    });
    gsap.set(Object.values(parts).filter(Boolean), { transformOrigin: "center center" });
  }

  function pathLengths(paths) {
    return new Map(paths.map((path) => [path, Math.max(1, path.getTotalLength ? path.getTotalLength() : 64)]));
  }

  function primeStrokeDraw(paths, gsap) {
    const lengths = pathLengths(paths);
    paths.forEach((path) => {
      const length = lengths.get(path);
      gsap.set(path, { strokeDasharray: length, strokeDashoffset: length });
    });
    return lengths;
  }

  function playTokenIntent({ parts, gsap }) {
    const required = ["shell", "core", "tickLeft", "tickRight", "tickTop", "tickBottom", "halo"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const ticks = [parts.tickLeft, parts.tickRight, parts.tickTop, parts.tickBottom];
    const lengths = primeStrokeDraw(ticks, gsap);
    gsap.set(parts.halo, { opacity: 0, scale: 0.6 });
    gsap.set(parts.core, { scale: 0.55, opacity: 0.35 });
    const tl = gsap.timeline({ repeat: -1, repeatDelay: 1.55 });
    tl.fromTo(parts.shell, { scale: 0.82, rotate: -8, opacity: 0.72 }, { scale: 1, rotate: 0, opacity: 0.96, duration: 0.22, ease: "back.out(3)" })
      .to(parts.core, { scale: 1.35, opacity: 0.95, duration: 0.16, ease: "power2.out" }, "-=0.08")
      .to(parts.core, { scale: 1, opacity: 0.72, duration: 0.16, ease: "power2.inOut" })
      .fromTo(ticks, { strokeDashoffset: (index, target) => lengths.get(target), opacity: 0 }, { strokeDashoffset: 0, opacity: 0.86, duration: 0.18, stagger: 0.035, ease: "power2.out" }, "-=0.08")
      .fromTo(parts.halo, { opacity: 0.55, scale: 0.55 }, { opacity: 0, scale: 1.55, duration: 0.34, ease: "power2.out" }, "-=0.02")
      .to(parts.shell, { scale: 0.98, duration: 0.45, ease: "power2.inOut" }, 1.05)
      .to(ticks, { opacity: 0.56, duration: 0.45 }, 1.05);
    return tl;
  }

  function playToolRun({ parts, gsap }) {
    const required = ["chip", "glyph", "connector", "spark1", "spark2", "flash"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const sparks = [parts.spark1, parts.spark2];
    const lengths = primeStrokeDraw(sparks, gsap);
    gsap.set(parts.flash, { opacity: 0, scale: 0.45 });
    const tl = gsap.timeline({ repeat: -1, repeatDelay: 1.55 });
    tl.to(parts.chip, { y: 2, scale: 0.96, duration: 0.12, ease: "power2.in" })
      .to(parts.chip, { y: -1, scale: 1.04, duration: 0.18, ease: "back.out(3)" })
      .to(parts.chip, { y: 0, scale: 1, duration: 0.16, ease: "power2.out" })
      .fromTo(parts.glyph, { scale: 0.82, opacity: 0.6 }, { scale: 1.12, opacity: 1, duration: 0.16, ease: "back.out(3)" }, 0.10)
      .to(parts.glyph, { scale: 1, opacity: 0.92, duration: 0.18, ease: "power2.out" })
      .fromTo(parts.connector, { x: -6, opacity: 0.35, scale: 0.55 }, { x: 4, opacity: 0.95, scale: 1.1, duration: 0.22, ease: "power2.out" }, 0.22)
      .to(parts.connector, { x: 0, scale: 1, opacity: 0.72, duration: 0.18, ease: "power2.out" })
      .fromTo(sparks, { strokeDashoffset: (index, target) => lengths.get(target), opacity: 0 }, { strokeDashoffset: 0, opacity: 0.95, duration: 0.16, stagger: 0.045, ease: "power2.out" }, 0.42)
      .fromTo(parts.flash, { opacity: 0.62, scale: 0.45 }, { opacity: 0, scale: 1.6, duration: 0.26, ease: "power2.out" }, 0.48)
      .to(sparks, { opacity: 0.42, duration: 0.5 }, 0.92);
    return tl;
  }

  function playOutputReveal({ parts, gsap }) {
    const required = ["card", "line1", "line2", "check", "flash"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const paths = [parts.line1, parts.line2, parts.check];
    const lengths = primeStrokeDraw(paths, gsap);
    gsap.set(parts.flash, { opacity: 0, scale: 0.45 });
    const tl = gsap.timeline({ repeat: -1, repeatDelay: 1.75 });
    tl.fromTo(parts.card, { y: 5, scale: 0.92, opacity: 0.75 }, { y: 0, scale: 1, opacity: 0.96, duration: 0.22, ease: "back.out(2.5)" })
      .fromTo([parts.line1, parts.line2], { strokeDashoffset: (index, target) => lengths.get(target), opacity: 0 }, { strokeDashoffset: 0, opacity: 0.86, duration: 0.22, stagger: 0.07, ease: "power2.out" }, 0.14)
      .fromTo(parts.check, { strokeDashoffset: lengths.get(parts.check), opacity: 0 }, { strokeDashoffset: 0, opacity: 1, duration: 0.26, ease: "power2.out" }, 0.42)
      .to(parts.card, { scale: 1.04, duration: 0.12, ease: "power2.out" }, 0.62)
      .to(parts.card, { scale: 1, duration: 0.18, ease: "power2.inOut" })
      .fromTo(parts.flash, { opacity: 0.65, scale: 0.5 }, { opacity: 0, scale: 1.65, duration: 0.28, ease: "power2.out" }, 0.58)
      .to([parts.line1, parts.line2, parts.check], { opacity: 0.68, duration: 0.55 }, 1.0);
    return tl;
  }

  function playApiRequestResponse({ parts, gsap }) {
    const required = ["leftEndpoint", "rightEndpoint", "requestToken", "responseToken", "targetRing", "status"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    gsap.set([parts.requestToken, parts.responseToken, parts.targetRing, parts.status], { opacity: 0, scale: 0.4 });
    const tl = gsap.timeline({ repeat: -1, repeatDelay: 1.65 });
    tl.to([parts.leftEndpoint, parts.rightEndpoint], { scaleY: 1.12, duration: 0.14, ease: "back.out(2)" })
      .fromTo(parts.requestToken, { x: -18, opacity: 0, scale: 0.4 }, { x: 18, opacity: 1, scale: 1, duration: 0.36, ease: "power2.out" }, "<")
      .to(parts.requestToken, { opacity: 0, scale: 0.35, duration: 0.12 })
      .fromTo(parts.targetRing, { scale: 0.4, opacity: 0.8 }, { scale: 1.8, opacity: 0, duration: 0.34, ease: "power2.out" }, "-=0.05")
      .fromTo(parts.responseToken, { x: 18, opacity: 0, scale: 0.4 }, { x: -18, opacity: 1, scale: 0.85, duration: 0.32, ease: "power2.inOut" }, "-=0.08")
      .to(parts.responseToken, { opacity: 0, scale: 0.35, duration: 0.12 })
      .fromTo(parts.status, { opacity: 0, scale: 0.5 }, { opacity: 1, scale: 1, duration: 0.2, ease: "back.out(2)" })
      .to(parts.status, { opacity: 0.35, duration: 0.5 })
      .to([parts.leftEndpoint, parts.rightEndpoint], { scaleY: 1, duration: 0.22, ease: "power2.out" }, "<");
    return tl;
  }

  function playSearchDiscover({ parts, gsap }) {
    const required = ["lens", "handle", "scan", "result1", "result2", "target"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    gsap.set([parts.scan, parts.result1, parts.result2, parts.target], { opacity: 0, scale: 0.35 });
    const tl = gsap.timeline({ repeat: -1, repeatDelay: 1.7 });
    tl.to([parts.lens, parts.handle], { rotate: -8, duration: 0.18, ease: "power2.out" })
      .fromTo(parts.scan, { opacity: 0, x: -10, y: -7, rotate: -14 }, { opacity: 0.9, x: 12, y: 9, rotate: 12, duration: 0.42, ease: "power2.inOut" })
      .to(parts.scan, { opacity: 0, duration: 0.12 })
      .fromTo(parts.result1, { opacity: 0, scale: 0.25, y: 2 }, { opacity: 0.95, scale: 1, y: 0, duration: 0.16, ease: "back.out(3)" }, "-=0.06")
      .fromTo(parts.result2, { opacity: 0, scale: 0.25, y: 2 }, { opacity: 0.72, scale: 0.82, y: 0, duration: 0.16, ease: "back.out(3)" }, "-=0.02")
      .fromTo(parts.target, { opacity: 0, scale: 0.45 }, { opacity: 0.88, scale: 1.18, duration: 0.22, ease: "back.out(2.5)" })
      .to(parts.target, { scale: 1, duration: 0.16, ease: "power2.out" })
      .to([parts.lens, parts.handle], { rotate: 0, duration: 0.26, ease: "power2.out" }, "<")
      .to([parts.result1, parts.result2, parts.target], { opacity: 0.28, duration: 0.55 });
    return tl;
  }

  function playDatabaseWrite({ parts, gsap }) {
    const required = ["lid", "body", "layer1", "layer2", "writeToken", "flash"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    gsap.set([parts.writeToken, parts.flash], { opacity: 0, scale: 0.35 });
    const tl = gsap.timeline({ repeat: -1, repeatDelay: 1.8 });
    tl.fromTo(parts.writeToken, { opacity: 0, x: -16, y: -18, scale: 0.35 }, { opacity: 1, x: 0, y: -3, scale: 1, duration: 0.28, ease: "power2.out" })
      .to(parts.writeToken, { y: 7, scale: 0.82, duration: 0.16, ease: "power2.in" })
      .to(parts.writeToken, { opacity: 0, scale: 0.25, duration: 0.1 })
      .to(parts.lid, { scaleY: 0.68, y: 3, duration: 0.14, ease: "power2.in" }, "-=0.14")
      .to(parts.body, { y: 2, scaleY: 0.96, duration: 0.14, ease: "power2.in" }, "<")
      .to(parts.lid, { scaleY: 1.1, y: -2, duration: 0.18, ease: "back.out(3)" })
      .to(parts.body, { y: 0, scaleY: 1, duration: 0.18, ease: "power2.out" }, "<")
      .fromTo(parts.layer1, { opacity: 0.32 }, { opacity: 1, duration: 0.12, ease: "power1.out" })
      .fromTo(parts.layer2, { opacity: 0.28 }, { opacity: 0.95, duration: 0.12, ease: "power1.out" }, "-=0.02")
      .fromTo(parts.flash, { opacity: 0, scale: 0.4 }, { opacity: 0.85, scale: 1.35, duration: 0.18, ease: "power2.out" })
      .to(parts.flash, { opacity: 0, scale: 1.85, duration: 0.26, ease: "power2.out" })
      .to([parts.layer1, parts.layer2], { opacity: 0.64, duration: 0.45 });
    return tl;
  }

  function playMemoryCommit({ parts, gsap }) {
    const required = ["backCard", "frontCard", "trace1", "trace2", "trace3", "dot", "commitToken", "flash"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const traces = [parts.trace1, parts.trace2, parts.trace3];
    gsap.set([parts.commitToken, parts.flash], { opacity: 0, scale: 0.35 });
    const tl = gsap.timeline({ repeat: -1, repeatDelay: 1.8 });
    tl.fromTo(parts.commitToken, { opacity: 0, x: -18, y: -15, scale: 0.35 }, { opacity: 1, x: -3, y: -4, scale: 1, duration: 0.24, ease: "power2.out" })
      .to(parts.commitToken, { x: 6, y: 10, scale: 0.72, duration: 0.18, ease: "power2.in" })
      .to(parts.commitToken, { opacity: 0, scale: 0.25, duration: 0.1 })
      .to(parts.frontCard, { y: 2, scale: 0.98, duration: 0.14, ease: "power2.in" }, "-=0.12")
      .to(parts.backCard, { x: 2, y: -2, duration: 0.14, ease: "power2.in" }, "<")
      .to(parts.frontCard, { y: -1, scale: 1.03, duration: 0.18, ease: "back.out(3)" })
      .to(parts.backCard, { x: 0, y: 0, duration: 0.18, ease: "power2.out" }, "<")
      .fromTo(traces, { opacity: 0.2, x: -5 }, { opacity: 0.95, x: 0, duration: 0.2, stagger: 0.05, ease: "power2.out" }, "-=0.02")
      .to(parts.dot, { scale: 1.45, opacity: 0.95, duration: 0.14, ease: "back.out(3)" }, "-=0.04")
      .to(parts.dot, { scale: 1, opacity: 0.72, duration: 0.18, ease: "power2.out" })
      .fromTo(parts.flash, { opacity: 0, scale: 0.45 }, { opacity: 0.75, scale: 1.2, duration: 0.16, ease: "power2.out" }, "-=0.12")
      .to(parts.flash, { opacity: 0, scale: 1.7, duration: 0.24, ease: "power2.out" })
      .to(traces, { opacity: 0.72, duration: 0.5 });
    return tl;
  }

  function playAgentThinkAct({ parts, gsap }) {
    const required = ["shell", "core", "thought1", "thought2", "thought3", "decisionToken"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const thoughts = [parts.thought1, parts.thought2, parts.thought3];
    gsap.set(parts.shell, { scale: 1, opacity: 0.92 });
    gsap.set(parts.core, { scale: 1, opacity: 0.78 });
    gsap.set(thoughts, { opacity: 0.42, scale: 0.92, x: 0, y: 0 });
    gsap.set(parts.decisionToken, { opacity: 0, scale: 0.35, x: 0, y: 0 });
    const tl = gsap.timeline({ repeat: -1, repeatDelay: 1.9 });
    tl.to(thoughts, {
        opacity: (index) => [0.9, 0.72, 0.82][index],
        x: (index) => [2.5, -3.5, 3][index],
        y: (index) => [-4, 2.5, -2][index],
        scale: (index) => [1.08, 0.95, 1.02][index],
        duration: 0.36,
        stagger: 0.07,
        ease: "sine.inOut",
      })
      .to(thoughts, {
        x: (index) => [6, -6, 3][index],
        y: (index) => [7, 5, -7][index],
        scale: 0.72,
        opacity: 0.86,
        duration: 0.26,
        stagger: 0.035,
        ease: "power2.in",
      })
      .to(parts.core, { scale: 1.48, opacity: 1, duration: 0.16, ease: "back.out(2.8)" }, "-=0.06")
      .to(parts.shell, { scale: 1.035, opacity: 1, duration: 0.16, ease: "power2.out" }, "<")
      .to(parts.core, { scale: 1, opacity: 0.82, duration: 0.22, ease: "power2.out" })
      .to(parts.shell, { scale: 1, opacity: 0.92, duration: 0.24, ease: "power2.out" }, "<")
      .fromTo(parts.decisionToken,
        { opacity: 0, scale: 0.35, x: 0, y: 0 },
        { opacity: 1, scale: 1.05, x: 13, y: -8, duration: 0.32, ease: "back.out(2.2)" },
        "-=0.08"
      )
      .to(parts.decisionToken, { opacity: 0, scale: 0.55, x: 24, y: -14, duration: 0.26, ease: "power1.in" })
      .to(thoughts, { x: 0, y: 0, scale: 1, opacity: 0.38, duration: 0.34, stagger: 0.03, ease: "power2.out" }, "-=0.14")
      .to(parts.core, { opacity: 0.72, duration: 0.42, ease: "sine.inOut" }, "-=0.14");
    return tl;
  }

  const performances = {
    "token-intent-v2": playTokenIntent,
    "tool-run-v2": playToolRun,
    "output-reveal-v2": playOutputReveal,
    "api-request-response-v2": playApiRequestResponse,
    "search-discover-v2": playSearchDiscover,
    "database-write-v2": playDatabaseWrite,
    "memory-commit-v2": playMemoryCommit,
    "agent-think-act-v2": playAgentThinkAct,
  };

  function playIcon(iconConfig) {
    if (!window.gsap) return null;
    const fn = performances[iconConfig.performance];
    if (!fn) return null;
    const parts = resolveParts(iconConfig.parts);
    const tl = fn({ config: iconConfig, parts, gsap: window.gsap });
    if (tl && iconConfig.delay) tl.delay(iconConfig.delay);
    return tl;
  }

  function play() {
    const manifest = getManifest();
    if (!manifest || !Array.isArray(manifest.icons)) return [];
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return [];
    if (!window.gsap) {
      console.warn("AniDiagram runtime: GSAP not loaded; high-fidelity motion disabled.");
      return [];
    }
    stop();
    const timelines = manifest.icons.map(playIcon).filter(Boolean);
    window.__ANIDIAGRAM_TIMELINES__ = timelines;
    return timelines;
  }

  function stop() {
    (window.__ANIDIAGRAM_TIMELINES__ || []).forEach((tl) => tl.kill());
    window.__ANIDIAGRAM_TIMELINES__ = [];
  }

  function pause() {
    (window.__ANIDIAGRAM_TIMELINES__ || []).forEach((tl) => tl.pause());
  }

  function resume() {
    (window.__ANIDIAGRAM_TIMELINES__ || []).forEach((tl) => tl.resume());
  }

  function restart() {
    (window.__ANIDIAGRAM_TIMELINES__ || []).forEach((tl) => tl.restart());
  }

  function wireViewer() {
    const stage = document.getElementById("stage");
    const viewer = document.getElementById("viewer");
    const viewport = document.getElementById("viewport");
    if (!stage || !viewer || !viewport) return;
    const svg = viewport.querySelector("svg");
    const download = document.getElementById("download");
    let scale = 1;
    let x = 0;
    let y = 0;
    let dragging = false;
    let lastX = 0;
    let lastY = 0;
    function applyTransform() {
      viewport.style.transform = `translate(${x}px, ${y}px) scale(${scale})`;
    }
    function setDownload() {
      if (!download || !svg) return;
      const blob = new Blob([new XMLSerializer().serializeToString(svg)], { type: "image/svg+xml" });
      download.href = URL.createObjectURL(blob);
    }
    const toggle = document.getElementById("toggle");
    if (toggle && svg) {
      toggle.addEventListener("click", (event) => {
        const paused = svg.animationsPaused && svg.animationsPaused();
        if (paused) {
          svg.unpauseAnimations();
          resume();
          event.currentTarget.textContent = "Pause";
        } else {
          svg.pauseAnimations();
          pause();
          event.currentTarget.textContent = "Play";
        }
      });
    }
    const restartButton = document.getElementById("restart");
    if (restartButton && svg) {
      restartButton.addEventListener("click", () => {
        svg.setCurrentTime(0);
        svg.unpauseAnimations();
        restart();
        if (toggle) toggle.textContent = "Pause";
      });
    }
    function setMotionMode(mode) {
      viewer.classList.remove("motion-full", "motion-subtle", "motion-off");
      viewer.classList.add(`motion-${mode}`);
      document.querySelectorAll(".motion-choice").forEach((button) => {
        button.setAttribute("aria-pressed", String(button.dataset.motion === mode));
      });
      if (!svg) return;
      if (mode === "off") {
        svg.pauseAnimations();
        pause();
        if (toggle) toggle.textContent = "Play";
      } else {
        svg.unpauseAnimations();
        resume();
        if (toggle) toggle.textContent = "Pause";
      }
    }
    document.querySelectorAll(".motion-choice").forEach((button) => {
      button.addEventListener("click", () => setMotionMode(button.dataset.motion));
    });
    const zoomIn = document.getElementById("zoom-in");
    const zoomOut = document.getElementById("zoom-out");
    const reset = document.getElementById("reset");
    if (zoomIn) zoomIn.addEventListener("click", () => { scale = Math.min(3, scale + 0.15); applyTransform(); });
    if (zoomOut) zoomOut.addEventListener("click", () => { scale = Math.max(0.35, scale - 0.15); applyTransform(); });
    if (reset) reset.addEventListener("click", () => { scale = 1; x = 0; y = 0; applyTransform(); });
    stage.addEventListener("pointerdown", (event) => {
      dragging = true;
      stage.classList.add("dragging");
      lastX = event.clientX;
      lastY = event.clientY;
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
    stage.addEventListener("pointerup", () => {
      dragging = false;
      stage.classList.remove("dragging");
    });
    setDownload();
    if (svg && svg.dataset.motionProfile === "off") setMotionMode("off");
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) setMotionMode("subtle");
  }

  window.AniDiagramRuntime = { play, pause, resume, restart, stop };
  document.addEventListener("DOMContentLoaded", () => {
    wireViewer();
    play();
  });
})();

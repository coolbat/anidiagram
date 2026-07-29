  function playChoreographer(manifest, autoplay = true) {
    if (!window.gsap || !manifest || !isPlainObject(manifest.choreographer)) return [];
    stop();
    if (window.AniDiagramEdgeMotion && window.AniDiagramEdgeMotion.clear) {
      window.AniDiagramEdgeMotion.clear();
    }
    const steps = Array.isArray(manifest.choreographer.steps) ? manifest.choreographer.steps : [];
    const edges = Array.from(document.querySelectorAll("g.edge"));
    const timeline = window.gsap.timeline({ paused: !autoplay });
    const stepStates = [];
    steps.forEach((step, index) => {
      const source = document.getElementById(`node-${step.source}`);
      const target = document.getElementById(`node-${step.target}`);
      const edge = edges[Number(step.edge_index)];
      const path = edge && (edge.querySelector(".edge-draw") || edge.querySelector(".edge-base"));
      const start = timeline.duration();
      timeline.addLabel(`step-${index}`, start);
      if (source) {
        timeline.to(source, {
          scale: 1.025,
          transformOrigin: "center center",
          duration: 0.18,
          ease: "power1.out",
        }, start);
      }
      if (path) {
        timeline.fromTo(path, {
          strokeDasharray: 1,
          strokeDashoffset: 1,
          opacity: 0.35,
        }, {
          strokeDashoffset: 0,
          opacity: 1,
          duration: 0.58,
          ease: "power1.inOut",
        }, start + 0.18);
      }
      if (source) timeline.to(source, { scale: 1, duration: 0.2 }, start + 0.58);
      if (target) {
        timeline.to(target, {
          scale: 1.035,
          transformOrigin: "center center",
          duration: 0.2,
          ease: "back.out(1.5)",
        }, start + 0.68);
        timeline.to(target, { scale: 1, duration: 0.24 }, start + 0.9);
      }
      const duration = Math.max(1.2, Number(step.duration) || 1.2);
      timeline.to({}, { duration: Math.max(0, start + duration - timeline.duration()) });
      stepStates.push({ index, start, end: start + duration, label: step.label || `Step ${index + 1}` });
    });
    timeline.addLabel("timeline-end", timeline.duration());
    timeline.__anidiagramChoreographer = true;
    window.__ANIDIAGRAM_CHOREOGRAPHER__ = { timeline, steps: stepStates, current: -1 };
    window.__ANIDIAGRAM_STAGE_TIMELINES__ = [timeline];
    window.__ANIDIAGRAM_ICON_TIMELINES__ = [];
    syncTimelineStore();
    if (autoplay) timeline.play(0);
    return [timeline];
  }

  function startChoreographer() {
    const manifest = getManifest();
    return playChoreographer(manifest, true);
  }

  function stepChoreographer(direction) {
    const state = window.__ANIDIAGRAM_CHOREOGRAPHER__;
    if (!state || !state.timeline || !state.steps.length) {
      playChoreographer(getManifest(), false);
    }
    const current = window.__ANIDIAGRAM_CHOREOGRAPHER__;
    if (!current || !current.steps.length) return null;
    const targetIndex = Math.max(0, Math.min(current.steps.length - 1, current.current + direction));
    const step = current.steps[targetIndex];
    current.current = targetIndex;
    current.timeline.pause(step.start);
    if (direction > 0) {
      current.timeline.tweenTo(step.end, { onComplete: () => current.timeline.pause() });
    }
    return step;
  }

  function enhanceProductViewer(originalManifest) {
    const viewer = document.getElementById("viewer");
    const stage = document.getElementById("stage");
    const viewport = document.getElementById("viewport");
    const status = document.getElementById("runtime-status");
    const warning = document.getElementById("runtime-warning");
    if (!viewer || !stage || !viewport) return;
    const notify = (message) => {
      if (status) status.textContent = message || viewer.dataset.labelReady || "Diagram ready";
    };
    const showWarning = (message) => {
      if (!warning) return;
      warning.textContent = message || "";
      warning.hidden = !message;
    };
    if (!window.gsap) showWarning(viewer.dataset.labelDependencyWarning);
    else showWarning("");

    const timelineStart = document.getElementById("timeline-start");
    const timelinePrevious = document.getElementById("timeline-previous");
    const timelineNext = document.getElementById("timeline-next");
    if (["timeline", "hybrid"].includes(originalManifest.mode)) {
      [timelineStart, timelinePrevious, timelineNext].forEach((button) => {
        if (button) button.hidden = false;
      });
      if (timelineStart) timelineStart.addEventListener("click", () => {
        startChoreographer();
        notify(timelineStart.textContent);
      });
      if (timelinePrevious) timelinePrevious.addEventListener("click", () => {
        const step = stepChoreographer(-1);
        if (step) notify(step.label);
      });
      if (timelineNext) timelineNext.addEventListener("click", () => {
        const step = stepChoreographer(1);
        if (step) notify(step.label);
      });
    }

    const toggle = document.getElementById("toggle");
    const restartButton = document.getElementById("restart");
    const zoomIn = document.getElementById("zoom-in");
    const zoomOut = document.getElementById("zoom-out");
    const reset = document.getElementById("reset");
    const svg = viewport.querySelector("svg");
    const localizeToggle = () => {
      if (!toggle || !svg) return;
      const paused = svg.animationsPaused && svg.animationsPaused();
      toggle.textContent = paused ? viewer.dataset.labelPlay || "Play" : viewer.dataset.labelPause || "Pause";
    };
    if (toggle) toggle.addEventListener("click", () => setTimeout(localizeToggle, 0));
    if (restartButton) restartButton.addEventListener("click", () => {
      setTimeout(localizeToggle, 0);
      notify(viewer.dataset.labelRestarted);
    });
    document.querySelectorAll(".motion-choice").forEach((button) => {
      button.addEventListener("click", () => {
        notify(button.textContent);
        if (originalManifest.mode === "timeline" && button.dataset.motion !== "off") {
          setTimeout(startChoreographer, 0);
        }
      });
    });

    let keyboardX = 0;
    let keyboardY = 0;
    const applyKeyboardPan = () => {
      viewport.style.translate = `${keyboardX}px ${keyboardY}px`;
    };
    stage.addEventListener("keydown", (event) => {
      if (["+", "="].includes(event.key)) {
        event.preventDefault();
        if (zoomIn) zoomIn.click();
      } else if (event.key === "-") {
        event.preventDefault();
        if (zoomOut) zoomOut.click();
      } else if (event.key === "0") {
        event.preventDefault();
        keyboardX = 0;
        keyboardY = 0;
        applyKeyboardPan();
        if (reset) reset.click();
      } else if (event.key === " " && toggle) {
        event.preventDefault();
        toggle.click();
      } else if (event.key.toLowerCase() === "r" && restartButton) {
        event.preventDefault();
        restartButton.click();
      } else if (event.key === "ArrowLeft") {
        event.preventDefault();
        keyboardX -= 24;
        applyKeyboardPan();
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        keyboardX += 24;
        applyKeyboardPan();
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        keyboardY -= 24;
        applyKeyboardPan();
      } else if (event.key === "ArrowDown") {
        event.preventDefault();
        keyboardY += 24;
        applyKeyboardPan();
      }
    });
  }

  const productManifestElement = document.getElementById("anidiagram-motion-manifest");
  let productManifest = null;
  if (productManifestElement) {
    try {
      productManifest = JSON.parse(productManifestElement.textContent || "{}");
    } catch (_error) {
      productManifest = null;
    }
  }
  if (productManifest && ["timeline", "hybrid"].includes(productManifest.mode)) {
    const ambientManifest = {
      ...productManifest,
      mode: "ambient",
      sequence: "independent-icon-loops",
    };
    delete ambientManifest.choreographer;
    productManifestElement.textContent = JSON.stringify(ambientManifest);
  }

  Object.assign(window.AniDiagramRuntime, {
    startChoreographer,
    nextStep: () => stepChoreographer(1),
    previousStep: () => stepChoreographer(-1),
  });

  document.addEventListener("DOMContentLoaded", () => {
    setTimeout(() => {
      if (productManifestElement && productManifest) {
        productManifestElement.textContent = JSON.stringify(productManifest);
      }
      enhanceProductViewer(productManifest || {});
      if (productManifest && productManifest.mode === "timeline") {
        playChoreographer(productManifest, productManifest.choreographer.autoplay !== false);
      }
    }, 0);
  });

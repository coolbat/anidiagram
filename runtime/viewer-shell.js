/* Viewer controls; assembled in the shared runtime closure. */
  function wireViewer() {
    const stage = document.getElementById("stage");
    const viewer = document.getElementById("viewer");
    const viewport = document.getElementById("viewport");
    if (!stage || !viewer || !viewport) return;
    const svg = viewport.querySelector("svg");
    const download = document.getElementById("download");
    window.__ANIDIAGRAM_VIEWPORT__ = window.AniDiagramViewport.mount(stage, viewport, svg);
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
      viewer.classList.remove("motion-expressive", "motion-readable", "motion-off");
      viewer.classList.add(`motion-${mode}`);
      document.querySelectorAll(".motion-choice").forEach((button) => {
        button.setAttribute("aria-pressed", String(button.dataset.motion === mode));
      });
      if (!svg) return;
      if (mode === "off") {
        svg.pauseAnimations();
        setRuntimeMotionMode("off");
        if (toggle) toggle.textContent = "Play";
      } else {
        svg.unpauseAnimations();
        setRuntimeMotionMode(mode);
        if (toggle) toggle.textContent = "Pause";
      }
    }
    document.querySelectorAll(".motion-choice").forEach((button) => {
      button.addEventListener("click", () => setMotionMode(button.dataset.motion));
    });
    const hint = document.getElementById("readable-hint");
    if (hint) hint.hidden = document.querySelectorAll("g.node").length <= 12;
    document.getElementById("copy-link")?.addEventListener("click", async () => {
      const status = document.getElementById("runtime-status");
      try { await navigator.clipboard.writeText(location.href); if (status) status.textContent = document.documentElement.lang === "zh-CN" ? "链接已复制" : "Link copied"; }
      catch (_) { if (status) status.textContent = document.documentElement.lang === "zh-CN" ? "复制失败，请复制地址栏" : "Copy failed; copy the address bar"; }
    });
    const nodes = Array.from(document.querySelectorAll("g.node")), edges = Array.from(document.querySelectorAll("g.edge"));
    const clearContext = () => document.querySelectorAll(".context-dim,.context-focus").forEach(el => el.classList.remove("context-dim", "context-focus"));
    function highlight(node) {
      if (window.__ANIDIAGRAM_CHOREOGRAPHER_ACTIVE__ || document.getElementById("diagram-reader")) return;
      const id = node.id.replace(/^node-/, ""), related = new Set([id]);
      const active = edges.filter(edge => edge.dataset.source === id || edge.dataset.target === id);
      active.forEach(edge => { related.add(edge.dataset.source); related.add(edge.dataset.target); });
      nodes.forEach(el => { el.classList.toggle("context-dim", !related.has(el.id.replace(/^node-/, ""))); el.classList.toggle("context-focus", el === node); });
      edges.forEach(el => el.classList.toggle("context-dim", !active.includes(el)));
    }
    nodes.forEach(node => {
      node.addEventListener("pointerenter", () => highlight(node));
      node.addEventListener("pointerleave", clearContext);
      node.addEventListener("focus", () => highlight(node));
      node.addEventListener("blur", clearContext);
    });
    setDownload();
    if (svg && svg.dataset.motionProfile === "off") setMotionMode("off");
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) setMotionMode("readable");
  }


/* A one-shot presentation entrance, independent of ambient icon scheduling. */
(function () {
  "use strict";
  let animations = [];
  function clear() { animations.forEach(animation => animation.cancel()); animations = []; }
  function play() {
    clear();
    const viewer = document.getElementById("viewer"), svg = document.querySelector("#viewport svg");
    if (!svg || !window.gsap || viewer?.classList.contains("motion-off") ||
        viewer?.classList.contains("motion-readable") || viewer?.dataset.runtimeMode === "timeline" ||
        matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const nodes = Array.from(svg.querySelectorAll("g.node"));
    const nodeEnds = new Map();
    const stagger = nodes.length > 1 ? Math.min(50, 500 / (nodes.length - 1)) : 0;
    function reveal(element, delay, duration) {
      const animation = element.animate([{ opacity: 0 }, { opacity: 1 }],
        { delay, duration, easing: "cubic-bezier(0.22,1,0.36,1)", fill: "backwards" });
      animations.push(animation);
    }
    svg.querySelectorAll("g.group").forEach(group => reveal(group, 0, 120));
    nodes.forEach((node, index) => {
      const start = 120 + index * stagger;
      nodeEnds.set(node.id.replace(/^node-/, ""), start + 220);
      reveal(node, start, 220);
    });
    svg.querySelectorAll("g.edge").forEach(edge => {
      const start = Math.max(nodeEnds.get(edge.dataset.source) || 840, nodeEnds.get(edge.dataset.target) || 840);
      // Hide the complete edge, including ambient packets, until both endpoints exist.
      reveal(edge, start, 220);
      const path = edge.querySelector(".edge-draw");
      if (path) animations.push(path.animate([{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }],
        { delay: start, duration: 220, easing: "ease-out", fill: "backwards" }));
    });
  }
  window.AniDiagramEntrance = {
    play, clear,
    pause() { animations.filter(animation => animation.playState === "running").forEach(animation => animation.pause()); },
    resume() { animations.filter(animation => animation.playState === "paused" &&
      animation.currentTime < animation.effect.getComputedTiming().endTime).forEach(animation => animation.play()); },
  };
  addEventListener("beforeprint", clear);
  matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change", event => { if (event.matches) clear(); });
})();

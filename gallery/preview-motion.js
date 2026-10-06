/* Display the existing diagram runtime only while its card is visible. */
(() => {
  "use strict";
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const controls = [...document.querySelectorAll("[data-preview-toggle]")];
  const cards = [...document.querySelectorAll(".motion-preview")].map(element => ({
    element, link: element.querySelector("[data-preview-url]"), visible: false,
    frame: null, timer: null, failed: false,
  }));
  let paused = false;

  function unload(card) {
    clearTimeout(card.timer);
    card.frame?.remove(); // Release the document, its GSAP ticker and all timers.
    card.frame = null;
    delete card.element.dataset.ready;
  }

  function fail(card, frame) {
    if (card.frame !== frame) return;
    card.failed = true;
    unload(card);
    card.element.querySelector(".preview-status").hidden = false;
  }

  function load(card) {
    const url = new URL(card.link.dataset.previewUrl, location.href);
    if (url.origin !== location.origin) return;
    const frame = document.createElement("iframe");
    card.frame = frame;
    frame.title = card.link.querySelector("img").alt + " — animated preview";
    frame.tabIndex = -1;
    frame.setAttribute("aria-hidden", "true");
    frame.addEventListener("error", () => fail(card, frame));
    frame.addEventListener("load", () => {
      if (card.frame !== frame) return;
      try {
        const win = frame.contentWindow;
        const doc = frame.contentDocument;
        const svg = doc.querySelector("#viewport > svg");
        const timelines = win.__ANIDIAGRAM_TIMELINES__ || [];
        if (!svg || !win.gsap || !timelines.length) return fail(card, frame);
        const style = doc.createElement("style");
        style.textContent = `
          html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; }
          #viewer { min-height: 0 !important; height: 100% !important; display: block !important; padding: 0; }
          #viewer > :not(#stage) { display: none !important; }
          #stage { width: 100%; height: 100% !important; min-height: 0 !important; overflow: hidden !important; border: 0; border-radius: 0; }
          #viewport { width: 100%; height: 100%; transform: none !important; }
          #viewport > svg { width: 100% !important; height: 100% !important; max-width: 100%; }
        `;
        doc.head.append(style);
        // Finish title/node entrance fades; keep original icon/edge timelines live.
        svg.setCurrentTime(Math.max(svg.getCurrentTime(), 8));
        card.element.dataset.ready = "true";
        clearTimeout(card.timer);
      } catch (_) {
        fail(card, frame);
      }
    });
    frame.src = url.href;
    card.timer = setTimeout(() => fail(card, frame), 15000);
    card.link.append(frame);
  }

  function sync() {
    const allowed = !paused && !reduced.matches && !document.hidden;
    for (const button of controls) {
      button.hidden = false;
      button.disabled = reduced.matches;
      button.textContent = reduced.matches ? "System: reduced motion" : paused ? "Play previews" : "Pause previews";
      button.setAttribute("aria-pressed", String(!paused && !reduced.matches));
    }
    for (const card of cards) {
      if (allowed && card.visible && !card.failed) {
        if (!card.frame) load(card);
      } else if (card.frame) unload(card);
    }
  }

  // No observer support: keep the complete static poster and Open HTML links.
  if (!("IntersectionObserver" in window)) return;
  const byElement = new Map(cards.map(card => [card.element, card]));
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) byElement.get(entry.target).visible = entry.isIntersecting;
    sync();
  }, {threshold: 0});
  cards.forEach(card => observer.observe(card.element));
  controls.forEach(button => button.addEventListener("click", () => { paused = !paused; sync(); }));
  reduced.addEventListener("change", sync);
  document.addEventListener("visibilitychange", sync);
  sync();
})();

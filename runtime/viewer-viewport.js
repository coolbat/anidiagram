/* Shared HTML/viewer camera. Authored SVG coordinates stay untouched. */
(function () {
  "use strict";
  window.AniDiagramViewport = {
    mount(stage, viewport, svg) {
      const nativeScroll = stage.dataset.readableScroll === "true";
      let scale = 1, x = 0, y = 0, fitted = true, pointer = null;
      const size = () => ({ width: svg.width.baseVal.value, height: svg.height.baseVal.value });
      function apply() {
        viewport.style.transform = `translate(${x}px, ${y}px) scale(${scale})`;
      }
      function fit() {
        const { width, height } = size();
        if (!(width > 0 && height > 0 && stage.clientWidth > 0 && stage.clientHeight > 0)) return;
        scale = nativeScroll ? 1 : Math.min((stage.clientWidth - 16) / width, (stage.clientHeight - 16) / height);
        scale = Math.max(0.01, scale);
        x = nativeScroll ? 0 : (stage.clientWidth - width * scale) / 2;
        y = nativeScroll ? 0 : (stage.clientHeight - height * scale) / 2;
        fitted = true;
        stage.scrollLeft = 0;
        stage.scrollTop = 0;
        apply();
      }
      function zoom(factor) {
        const next = Math.max(0.01, Math.min(8, scale * factor));
        const cx = stage.clientWidth / 2, cy = stage.clientHeight / 2;
        x = cx - (cx - x) * next / scale;
        y = cy - (cy - y) * next / scale;
        scale = next;
        fitted = false;
        apply();
      }
      function panBy(dx, dy) { x += dx; y += dy; fitted = false; apply(); }
      stage.addEventListener("pointerdown", event => {
        if (event.button !== 0 || event.target.closest("a, button, input, select")) return;
        pointer = { id: event.pointerId, x: event.clientX, y: event.clientY };
        stage.classList.add("dragging");
        stage.setPointerCapture(event.pointerId);
      });
      stage.addEventListener("pointermove", event => {
        if (!pointer || event.pointerId !== pointer.id) return;
        panBy(event.clientX - pointer.x, event.clientY - pointer.y);
        pointer.x = event.clientX;
        pointer.y = event.clientY;
      });
      const release = () => { pointer = null; stage.classList.remove("dragging"); };
      for (const type of ["pointerup", "pointercancel", "lostpointercapture"]) stage.addEventListener(type, release);
      document.getElementById("zoom-in")?.addEventListener("click", () => zoom(1.2));
      document.getElementById("zoom-out")?.addEventListener("click", () => zoom(1 / 1.2));
      document.getElementById("reset")?.addEventListener("click", fit);
      const observer = new ResizeObserver(() => { if (fitted) fit(); });
      observer.observe(stage);
      fit();
      return { fit, panBy, zoom,
        state: () => ({ scale, x, y }),
        setState(value) { scale = value.scale; x = value.x; y = value.y; fitted = false; apply(); },
        focusTransform(bounds) {
          if (nativeScroll) return { scale, x, y };
          const base = Math.min((stage.clientWidth - 16) / size().width, (stage.clientHeight - 16) / size().height);
          const next = Math.max(base, Math.min(base * 1.65, (stage.clientWidth - 48) / Math.max(1, bounds.width), (stage.clientHeight - 48) / Math.max(1, bounds.height)));
          // Keep the canvas covering the stage on each axis it overflows, so the
          // focus never exposes blank space beyond the diagram edge.
          const clamp = (offset, available, extent) => extent <= available
            ? (available - extent) / 2 : Math.min(0, Math.max(available - extent, offset));
          const { width, height } = size();
          return { scale: next,
            x: clamp(stage.clientWidth / 2 - (bounds.x + bounds.width / 2) * next, stage.clientWidth, width * next),
            y: clamp(stage.clientHeight / 2 - (bounds.y + bounds.height / 2) * next, stage.clientHeight, height * next) };
        },
      };
    },
  };
})();

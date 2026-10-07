(function () {
  "use strict";
  /* ANIDIAGRAM_CORE */
  window.AniDiagramRuntime = { play, pause, resume, restart, stop };
  /* ANIDIAGRAM_EXTENSIONS */
  document.addEventListener("DOMContentLoaded", () => {
    wireViewer();
    play();
    if (!window.__ANIDIAGRAM_CHOREOGRAPHER_ACTIVE__) window.AniDiagramEntrance?.play();
  });
})();

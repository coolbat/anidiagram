/* Scheduler and playback lifecycle; assembled in the shared runtime closure. */
  let runtimePaused = false; window.__ANIDIAGRAM_USER_PAUSED__ = false;
  let pausedPlayback = new Map();
  function play() {
    window.__ANIDIAGRAM_TIMELINES__ = window.__ANIDIAGRAM_TIMELINES__ || [];
    window.__ANIDIAGRAM_STAGE_TIMELINES__ = window.__ANIDIAGRAM_STAGE_TIMELINES__ || [];
    window.__ANIDIAGRAM_ICON_TIMELINES__ = window.__ANIDIAGRAM_ICON_TIMELINES__ || [];
    const manifest = getManifest();
    if (!manifest || !Array.isArray(manifest.icons)) return [];
    const mode = manifest.mode || "ambient";
    if (currentMotionMode === "off") { stop(); return []; }
    runtimePaused = false; window.__ANIDIAGRAM_USER_PAUSED__ = false;
    if (mode === "timeline") return playChoreographer(manifest, true);
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      stop();
      return [];
    }
    if (!window.gsap) {
      console.warn("AniDiagram runtime: GSAP not loaded; high-fidelity motion disabled.");
      return [];
    }
    stop();
    if (currentMotionMode === "off") return [];
    if (mode === "event-driven") return playEventDriven(manifest, currentMotionMode);
    window.__ANIDIAGRAM_STAGE_TIMELINES__ = playStageEffects(manifest, currentMotionMode);
    window.__ANIDIAGRAM_ICON_TIMELINES__ = playAmbientIcons(manifest);
    window.AniDiagramEdgeMotion?.play(currentMotionMode);
    return syncTimelineStore();
  }

  function syncTimelineStore() {
    window.__ANIDIAGRAM_STAGE_TIMELINES__ = window.__ANIDIAGRAM_STAGE_TIMELINES__ || [];
    window.__ANIDIAGRAM_ICON_TIMELINES__ = window.__ANIDIAGRAM_ICON_TIMELINES__ || [];
    window.__ANIDIAGRAM_TIMELINES__ = [
      ...window.__ANIDIAGRAM_STAGE_TIMELINES__,
      ...window.__ANIDIAGRAM_ICON_TIMELINES__,
    ];
    return window.__ANIDIAGRAM_TIMELINES__;
  }

  function settleCharacterTimelines(timelines) {
    (timelines || []).forEach((tl) => {
      if (tl.__anidiagramCharacter && Number.isFinite(tl.__anidiagramCharacter.restAt)) {
        tl.pause();
        tl.seek(tl.__anidiagramCharacter.restAt, false);
      } else if (Number.isFinite(tl.__anidiagramRestAt)) {
        tl.pause();
        tl.seek(tl.__anidiagramRestAt, false);
      }
    });
  }

  function stopStageTimelines() {
    (window.__ANIDIAGRAM_STAGE_TIMELINES__ || []).forEach((tl) => tl.kill());
    window.__ANIDIAGRAM_STAGE_TIMELINES__ = [];
    clearRuntimeStageEffects();
    syncTimelineStore();
  }

  function setRuntimeMotionMode(mode) {
    currentMotionMode = mode;
    window.AniDiagramEntrance?.clear();
    const manifest = getManifest();
    if (mode === "off") { stop(); return []; }
    runtimePaused = false; window.__ANIDIAGRAM_USER_PAUSED__ = false;
    if (manifest?.mode === "timeline") return playChoreographer(manifest, true);
    const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!manifest || !window.gsap || reduced || mode === "off") {
      stop();
      return [];
    }
    stop();
    if (manifest.mode === "event-driven") return playEventDriven(manifest, mode);
    window.__ANIDIAGRAM_ICON_TIMELINES__ = playAmbientIcons(manifest);
    window.__ANIDIAGRAM_STAGE_TIMELINES__ = playStageEffects(manifest, mode);
    window.AniDiagramEdgeMotion?.play(mode);

    return syncTimelineStore();
  }

  function stop() {
    pausedPlayback.clear();
    clearEventHover();
    clearIconHover();
    if (typeof clearChoreographerFocus === "function") clearChoreographerFocus();
    window.AniDiagramEdgeMotion?.clear();
    settleCharacterTimelines(window.__ANIDIAGRAM_EVENT_DRIVEN__?.iconTimelines || []);
    window.__ANIDIAGRAM_EVENT_DRIVEN__ = null;
    window.AniDiagramEntrance?.clear();
    settleCharacterTimelines(window.__ANIDIAGRAM_ICON_TIMELINES__ || []);
    (window.__ANIDIAGRAM_ICON_TIMELINES__ || []).forEach((tl) => tl.kill());
    (window.__ANIDIAGRAM_STAGE_TIMELINES__ || []).forEach((tl) => tl.kill());
    window.__ANIDIAGRAM_ICON_TIMELINES__ = [];
    window.__ANIDIAGRAM_STAGE_TIMELINES__ = [];
    window.__ANIDIAGRAM_TIMELINES__ = [];
    clearRuntimeStageEffects();
  }

  function pause() {
    const alreadyPaused = runtimePaused;
    runtimePaused = true; window.__ANIDIAGRAM_USER_PAUSED__ = true;
    window.AniDiagramEntrance?.pause();
    const all = [...(window.__ANIDIAGRAM_TIMELINES__ || [])];
    const scrub = window.__ANIDIAGRAM_CHOREOGRAPHER__?.scrub;
    if (scrub) all.push(scrub);
    all.forEach(timeline => {
      if (!alreadyPaused) pausedPlayback.set(timeline, timeline.paused());
      timeline.pause();
    });
  }

  function resume() {
    runtimePaused = false; window.__ANIDIAGRAM_USER_PAUSED__ = false;
    window.AniDiagramEntrance?.resume();
    const all = [...(window.__ANIDIAGRAM_TIMELINES__ || [])];
    const scrub = window.__ANIDIAGRAM_CHOREOGRAPHER__?.scrub;
    if (scrub) all.push(scrub);
    all.forEach(timeline => {
      if (!timeline.__anidiagramHoverSuspended && !pausedPlayback.get(timeline)) timeline.resume();
    });
    pausedPlayback.clear();
  }

  function restart() {
    window.__ANIDIAGRAM_CHOREOGRAPHER__?.scrub?.kill();
    if (window.__ANIDIAGRAM_CHOREOGRAPHER__) window.__ANIDIAGRAM_CHOREOGRAPHER__.scrub = null;
    pausedPlayback.clear();
    runtimePaused = false; window.__ANIDIAGRAM_USER_PAUSED__ = false;
    if (!window.__ANIDIAGRAM_CHOREOGRAPHER_ACTIVE__) window.AniDiagramEntrance?.play();
    (window.__ANIDIAGRAM_TIMELINES__ || []).forEach((tl) => tl.restart());
  }


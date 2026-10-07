/* Causal explanation and camera; assembled in the shared runtime closure. */
  function setChoreographerPlayback(playing) {
    const svg=document.querySelector('#viewport svg'), viewer=document.getElementById('viewer'), toggle=document.getElementById('toggle');
    if(svg) { if(playing)svg.unpauseAnimations?.();else svg.pauseAnimations?.(); }
    if(toggle&&viewer)toggle.textContent=playing?viewer.dataset.labelPause:viewer.dataset.labelPlay;
  }
  function clearChoreographerFocus() {
    const state = window.__ANIDIAGRAM_CHOREOGRAPHER__;
    if (state?.scrub) state.scrub.kill();
    window.__ANIDIAGRAM_CHOREOGRAPHER_ACTIVE__ = false;
    window.__ANIDIAGRAM_CHOREOGRAPHER__ = null;
    document.querySelectorAll('.narration-dim').forEach(el => {
      el.style.removeProperty('opacity'); el.classList.remove('narration-dim');
    });
    document.querySelectorAll('.context-dim,.context-focus').forEach(el => el.classList.remove('context-dim','context-focus'));
    (state?.restore || []).forEach(({el,style,transform}) => {
      if (style === null) el.removeAttribute('style'); else el.setAttribute('style',style);
      if (transform === null) el.removeAttribute('transform'); else el.setAttribute('transform',transform);
      if (el._gsap) el._gsap.uncache = 1;
    });
    const card = document.getElementById('narration');
    if (card) card.hidden = true;
    if (state) window.__ANIDIAGRAM_VIEWPORT__?.fit();
    if (state?.readerStyle) state.readerStyle.media = state.readerMedia;
  }

  function updateNarration(state, index) {
    if (!state || !state.steps.length) return;
    state.current = index;
    const step = state.steps[index], zh = document.documentElement.lang === 'zh-CN';
    const activeNodes = new Set([`node-${step.source}`, `node-${step.target}`]);
    document.querySelectorAll('g.node,g.edge').forEach(el => {
      const focus = activeNodes.has(el.id) || el === state.edges[Number(step.edge_index)];
      el.classList.add('narration-dim'); el.style.opacity = focus ? '1' : '.25';
    });
    const card = document.getElementById('narration');
    if (!card) return;
    card.hidden = false;
    document.getElementById('narration-count').textContent = zh ? `第 ${index + 1} / ${state.steps.length} 步` : `Step ${index + 1} / ${state.steps.length}`;
    document.getElementById('narration-label').textContent = step.label || `${step.source} → ${step.target}`;
    const route = document.getElementById('narration-route');
    if (route) {
      const path = `${step.source_label || step.source} → ${step.target_label || step.target}`;
      route.textContent = step.target_caption ? `${path} · ${step.target_caption}` : path;
    }
    const condition = document.getElementById('narration-condition');
    condition.hidden = !step.condition;
    condition.textContent = step.condition ? `${zh ? '条件' : 'Condition'}: ${step.condition}` : '';
    const sources = document.getElementById('narration-sources'); sources.replaceChildren();
    (step.source_refs || []).forEach(ref => {
      if (!ref || !/^https?:\/\//i.test(ref.href || '')) return;
      const link = document.createElement('a'); link.href = ref.href;
      link.textContent = ref.title || ref.id || (zh ? '源码' : 'Source');
      link.target = '_blank'; link.rel = 'noopener noreferrer'; sources.append(link);
    });
    document.querySelectorAll('.step-dot').forEach((dot, i) => {
      if (i === index) dot.setAttribute('aria-current', 'step'); else dot.removeAttribute('aria-current');
    });
  }

  function playChoreographer(manifest, autoplay = true) {
    if (!manifest || !isPlainObject(manifest.choreographer)) return [];
    stop();
    window.__ANIDIAGRAM_CHOREOGRAPHER_ACTIVE__ = true;
    const raw = Array.isArray(manifest.choreographer.steps) ? manifest.choreographer.steps : [];
    const state = { timeline: null, steps: [], edges: Array.from(document.querySelectorAll('g.edge')), current: -1, scrub: null };
    state.readerStyle=document.getElementById('reader-selection-style');
    state.readerMedia=state.readerStyle?.media || '';
    if(state.readerStyle)state.readerStyle.media='not all';
    state.restore = [...document.querySelectorAll('g.node,g.edge,.edge-draw,.edge-base')].map(el=>({el,style:el.getAttribute('style'),transform:el.getAttribute('transform')}));
    window.__ANIDIAGRAM_CHOREOGRAPHER__ = state;
    let cursor = 0;
    raw.forEach((step, index) => { const duration = Math.max(1.8, Number(step.duration) || 1.8); state.steps.push({ ...step, index, start: cursor, end: cursor + duration }); cursor += duration; });
    const progress = document.getElementById('narration-progress');
    if (progress) {
      progress.replaceChildren(); state.steps.forEach((step, index) => {
        const dot = document.createElement('button'); dot.type = 'button'; dot.className = 'step-dot';
        dot.setAttribute('aria-label', `${document.documentElement.lang === 'zh-CN' ? '步骤' : 'Step'} ${index + 1}: ${step.label || ''}`);
        dot.addEventListener('click', () => selectChoreographerStep(index)); progress.append(dot);
      });
    }
    if (!state.steps.length) { clearChoreographerFocus(); return []; }
    updateNarration(state, 0);
    window.__ANIDIAGRAM_VIEWPORT__?.fit();
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (!window.gsap || reduced || currentMotionMode === 'off') { setChoreographerPlayback(false); return []; }
    const camera = window.__ANIDIAGRAM_VIEWPORT__;
    const cameraState = camera?.state();
    const timeline = window.gsap.timeline({ paused: true, onComplete: () => setChoreographerPlayback(false), onUpdate: () => {
      const time = timeline.time();
      const index = Math.max(0, state.steps.findLastIndex(step => time >= step.start));
      if (index !== state.current) updateNarration(state, index);
    }});
    state.timeline = timeline;
    state.steps.forEach(step => {
      const source = document.getElementById(`node-${step.source}`), target = document.getElementById(`node-${step.target}`);
      const edge = state.edges[Number(step.edge_index)];
      const path = edge && (edge.querySelector('.edge-draw') || edge.querySelector('.edge-base'));
      timeline.addLabel(`step-${step.index}`, step.start);
      if (camera && cameraState && source && target) {
        const boxes = [source.getBBox(), target.getBBox()];
        if (path) boxes.push(path.getBBox());
        const left = Math.min(...boxes.map(box => box.x)), top = Math.min(...boxes.map(box => box.y));
        const right = Math.max(...boxes.map(box => box.x + box.width)), bottom = Math.max(...boxes.map(box => box.y + box.height));
        const bounds = { x: left - 24, y: top - 24, width: right - left + 48, height: bottom - top + 48 };
        timeline.to(cameraState, { ...camera.focusTransform(bounds), duration: .4, ease: 'power2.inOut', onUpdate: () => camera.setState(cameraState) }, step.start);
      }
      if (path) timeline.fromTo(path, { strokeDasharray: 1, strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: .58, ease: 'none' }, step.start+.18);
      if (target) { timeline.to(target, { scale: 1.025, transformOrigin: 'center center', duration: .075 }, step.start+.76); timeline.to(target, { scale: 1, duration: .075 }, step.start+.835); }
      timeline.to({}, { duration: step.end-step.start }, step.start);
    });
    timeline.addLabel('timeline-end', timeline.duration());
    timeline.__anidiagramChoreographer = true;
    window.__ANIDIAGRAM_STAGE_TIMELINES__ = [timeline]; window.__ANIDIAGRAM_ICON_TIMELINES__ = []; syncTimelineStore();
    setChoreographerPlayback(autoplay);
    if (autoplay) timeline.play(0);
    return [timeline];
  }

  function startChoreographer() { return playChoreographer(getManifest(), true); }
  function selectChoreographerStep(index, animate = false) {
    if (!window.__ANIDIAGRAM_CHOREOGRAPHER__) playChoreographer(getManifest(), false);
    const state = window.__ANIDIAGRAM_CHOREOGRAPHER__;
    if (!state?.steps.length) return null;
    const step = state.steps[Math.max(0, Math.min(state.steps.length - 1, index))];
    state.scrub?.kill();
    if (state.timeline) {
      state.timeline.pause(step.start);
      if (animate) state.scrub = state.timeline.tweenTo(step.end - .001, { onComplete: () => { state.timeline.pause();setChoreographerPlayback(false); } });
      else state.timeline.pause(Math.min(step.end-.001,step.start+.5));
    }
    setChoreographerPlayback(Boolean(animate && state.timeline));
    updateNarration(state, step.index); return step;
  }
  function stepChoreographer(direction) {
    if (!window.__ANIDIAGRAM_CHOREOGRAPHER__) playChoreographer(getManifest(), false);
    const state = window.__ANIDIAGRAM_CHOREOGRAPHER__;
    return state ? selectChoreographerStep(state.current + direction, direction > 0) : null;
  }

  function enhanceProductViewer(manifest) {
    const viewer = document.getElementById('viewer'), stage = document.getElementById('stage');
    if (!viewer || !stage) return;
    const notify = text => { const el=document.getElementById('runtime-status'); if(el)el.textContent=text||viewer.dataset.labelReady; };
    const warning=document.getElementById('runtime-warning');
    if (warning) { warning.hidden=Boolean(window.gsap); warning.textContent=window.gsap?'':viewer.dataset.labelDependencyWarning; }
    const explain=document.getElementById('timeline-start'), previous=document.getElementById('timeline-previous'), next=document.getElementById('timeline-next');
    if (manifest.choreographer?.steps?.length) {
      [explain,previous,next].forEach(el=>{ if(el)el.hidden=false; });
      explain?.addEventListener('click',()=>{startChoreographer();stage.focus();});
      previous?.addEventListener('click',()=>{ const step=stepChoreographer(-1); if(step)notify(step.label); });
      next?.addEventListener('click',()=>{ const step=stepChoreographer(1); if(step)notify(step.label); });
    }
    const toggle=document.getElementById('toggle'), svg=document.querySelector('#viewport svg');
    const localize=()=>{ if(toggle&&svg) toggle.textContent=svg.animationsPaused?.()?viewer.dataset.labelPlay:viewer.dataset.labelPause; };
    toggle?.addEventListener('click',()=>setTimeout(localize,0));
    document.getElementById('restart')?.addEventListener('click',()=>{ setTimeout(localize,0); notify(viewer.dataset.labelRestarted); });
    document.querySelectorAll('.motion-choice').forEach(button=>button.addEventListener('click',()=>{ setTimeout(localize,0); notify(button.textContent); }));
    stage.addEventListener('keydown',event=>{
      const controls={ '+':'zoom-in','=':'zoom-in','-':'zoom-out','0':'reset',' ':'toggle','r':'restart','R':'restart' };
      if(controls[event.key]) { event.preventDefault(); document.getElementById(controls[event.key])?.click(); }
      else if(['ArrowLeft','ArrowRight'].includes(event.key)) { event.preventDefault(); if(window.__ANIDIAGRAM_CHOREOGRAPHER_ACTIVE__)stepChoreographer(event.key==='ArrowRight'?1:-1); else window.__ANIDIAGRAM_VIEWPORT__?.panBy(event.key==='ArrowRight'?24:-24,0); }
      else if(['ArrowUp','ArrowDown'].includes(event.key)) { event.preventDefault(); window.__ANIDIAGRAM_VIEWPORT__?.panBy(0,event.key==='ArrowDown'?24:-24); }
    });
  }
  Object.assign(window.AniDiagramRuntime,{ startChoreographer, nextStep:()=>stepChoreographer(1),previousStep:()=>stepChoreographer(-1),selectStep:selectChoreographerStep });
  document.addEventListener('DOMContentLoaded',()=>enhanceProductViewer(getManifest()||{}));

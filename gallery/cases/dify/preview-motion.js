// Static-first progressive enhancement: no JS or reduced motion keeps the SVG.
(() => {
  const image = document.querySelector('figure img[data-motion-src]');
  const button = document.getElementById('preview-motion');
  if (!image || !button) return;
  const still = image.getAttribute('src');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  let playing = false;
  function setPlaying(value) {
    playing = value;
    image.src = playing ? image.dataset.motionSrc : still;
    button.textContent = playing ? button.dataset.pauseLabel : button.dataset.playLabel;
    button.setAttribute('aria-pressed', String(playing));
  }
  image.addEventListener('error', () => { if (playing) setPlaying(false); });
  button.hidden = false;
  button.addEventListener('click', () => setPlaying(!playing));
  reduced.addEventListener('change', () => setPlaying(!reduced.matches));
  setPlaying(!reduced.matches);
})();

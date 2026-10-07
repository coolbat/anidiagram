"""Shared landing-page markup and portable assets for the recorded sample."""
from pathlib import Path
import shutil

MARKUP = '''    <section class="narration-hero" aria-labelledby="narration-title">
      <h2 id="narration-title">Follow one request, step by step</h2>
      <p>A seven-second recording of the actual explanation mode: focus, camera movement, relation labels, and step controls. This is a generic architecture sample, not a verified production system.</p>
      <video controls muted loop playsinline preload="metadata" poster="narration/poster.png" style="display:block;width:100%;max-height:65vh;background:#fff;border:1px solid #e5e7eb;border-radius:12px" aria-label="Seven-second request-flow explanation">
        <source src="narration/explanation.mp4" type="video/mp4">
        <a href="narration/production-request.html">Open the interactive explanation</a>
      </video>
      <p class="links"><a href="narration/production-request.html">Try the interactive explanation</a><a href="narration/recording.json">Recording details</a><a href="#style-showcase">Explore styles</a><a href="#layout-showcase">Explore layouts</a></p>
    </section>
'''

def install_narration(outdir: Path) -> str:
    source=Path(__file__).resolve().parents[1]/'gallery'/'narration'
    if not (source/'explanation.mp4').is_file():
        raise FileNotFoundError('Build the gallery recording first: node scripts/build_gallery_narration.mjs')
    target=outdir/'narration'
    if source.resolve()!=target.resolve():shutil.copytree(source,target,dirs_exist_ok=True)
    return MARKUP

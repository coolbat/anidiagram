# Motion Research

AniDiagram keeps its renderer clean-room. The projects below were reviewed as
design references for animation vocabulary, not copied as source code or assets.

## Useful Patterns

- **Anime.js**: timeline thinking, staggered entry, easing, and looping motion
  over SVG/DOM targets.
- **Vivus**: SVG line drawing as a first-class animation style.
- **Lazy Line Painter**: path drawing, playback lifecycle, and SVG-specific
  event vocabulary.
- **mo.js**: bursts, ripples, and motion-graphics accents around important
  elements.
- **Motion**: modern JS animation API shape, especially declarative motion
  controls and spring-like feel.
- **Lottie Web**: portable animation export format and viewer ecosystem.
- **Flubber**: shape interpolation as a future direction for state transitions.
- **SVG.js**: lightweight SVG manipulation API and dependency-light design.

## AniDiagram Implementation Choices

Current implementation stays dependency-free in the primary SVG/HTML path:

- Node staggered entry.
- Node breathing/glow layer.
- Agent/output/risk burst rings.
- Group fade-in and moving dashed boundary.
- Edge draw-on animation using SVG `pathLength`, `stroke-dasharray`, and
  `stroke-dashoffset`.
- Edge flow dash animation.
- Multiple edge particles with staggered phase offsets.
- HTML viewer restart and reduced-motion handling.
- Scene-level motion profiles: `off`, `subtle`, `normal`, and `expressive`.
- GSAP-inspired sequencing controls: `simultaneous`, `step-stagger`, and
  `layered`.
- Channel-specific motion controls for node, edge, group, intensity, duration
  scale, and reduced-motion behavior.

If a future release imports a third-party runtime, add its copyright and license
notice to `REFERENCES.md` before shipping.

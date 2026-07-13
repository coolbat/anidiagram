# Illustrated Character v1 Theme Compatibility

This record evaluates bundled style tokens against the shared
`illustrated-character-v1` registry. Theme compatibility may change palette,
surface, edge, title, and background tokens; it must not fork character SVG
geometry or semantic performances.

## Supported character themes

| Theme | Decision | Notes |
| --- | --- | --- |
| `illustrated-character` | Pass, supported | Canonical light baseline with the clearest pastel hierarchy. |
| `deep-tech` | Pass, supported | Strong dark contrast; bright role borders keep the small character props legible. |
| `teaching-sketch-character` | Pass, supported | Softer instructional surface with stable frames and restrained edge motion. |

The supported comparison surface is `gallery/character-themes.html`. Each entry
links HTML, SVG, browser-captured animated WebP, and a clean quality report.

## Additional bundled-theme evaluation

| Theme | Decision | Contrast and hierarchy review | Evidence |
| --- | --- | --- | --- |
| `minimal-light` | Pass | Clear labels, restrained surfaces, and sufficient separation between character props and cards. | `outputs/illustrated-character-theme-candidates/minimal-light.html`, `.svg`, `.quality.json`, `.png` |
| `dark-luxury` | Pass | Dark surfaces preserve readable white labels and the pastel character palette remains visible without new geometry. | `outputs/illustrated-character-theme-candidates/dark-luxury.html`, `.svg`, `.quality.json`, `.png` |
| `blueprint` | Pass | Technical blue framing is coherent with character props; edge and group boundaries remain distinct. | `outputs/illustrated-character-theme-candidates/blueprint.html`, `.svg`, `.quality.json`, `.png` |
| `claude-warm` | Pass | Warm neutral canvas and varied role accents preserve icon/card hierarchy and label readability. | `outputs/illustrated-character-theme-candidates/claude-warm.html`, `.svg`, `.quality.json`, `.png` |
| `aurora-orb` | Tune, not promoted | Quality and clipping checks pass, but saturated card gradients compete with the flat character illustrations and weaken semantic focus. Tune surface intensity before promotion. | `outputs/illustrated-character-theme-candidates/aurora-orb.html`, `.svg`, `.quality.json`, `.png` |

## Review dimensions

- Contrast: title, labels, captions, and icon outlines remain readable.
- Clipping: character roots, props, packets, and confirmation marks stay inside
  their node regions.
- Hierarchy: character action remains primary; card surface and background stay
  supportive.
- Motion: one logical edge packet, entry-only title accent, stable node/group
  frames, and canonical Off/reduced-motion states.
- Geometry: every theme uses the same data-only character registry and runtime
  part IDs.

## Promotion rule

A candidate becomes a supported character theme only after its token changes,
quality report, Expressive/Readable/Off browser checks, and comparison artifact
are reviewed. Passing static quality alone is not sufficient.

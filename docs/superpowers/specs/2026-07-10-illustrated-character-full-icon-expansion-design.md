# Illustrated Character v1: Full Icon Expansion

## Goal

Extend the clean-room `illustrated-character-v1` system from its current three
covered icons (`agent`, `operator`, `database`) to every remaining valid
semantic icon: `api`, `search`, `tool`, `memory`, `output`, `file`, `folder`,
`cloud`, `shield`, and `token`.

The extension remains dependency-free: AniDiagram-owned SVG primitives,
Motion Manifest entries, and the existing GSAP runtime are the only production
surfaces. No third-party source code, artwork, runtime, or generated assets are
introduced.

## Confirmed visual language

Every expanded icon follows the three approved v1 examples:

- deep indigo outline (`#283047`), round joins and caps;
- two or three opaque pastel fill areas on a warm paper surface;
- one small narrative prop rather than abstract decoration;
- friendly, compact silhouette that still reads in a diagram node;
- no emoji, photo texture, glass effect, realistic shading, or generic card
  icon treatment.

The visual concepts are:

| Icon | Illustrated object |
| --- | --- |
| `search` | mint scout lens and star marker |
| `tool` | orange tool bucket and small wrench |
| `api` | lavender signal interface with request/receipt points |
| `memory` | stacked index cards and bookmark |
| `output` | open result envelope and completion card |
| `file` | folded note page and content lines |
| `folder` | two-tone filing folder and inserted sheet |
| `cloud` | cloud and uplink kite/data line |
| `shield` | guard badge with a small shield core |
| `token` | double-layer intent capsule |

## Motion contract

All character performances use the same quiet, semantic loop:

```text
prepare (0.12–0.20 s)
→ one semantic action (0.18–0.38 s)
→ confirmation (0.14–0.26 s)
→ canonical resting pose + 1.45–1.85 s pause
```

Only one primary action happens in each loop. Motion changes only opacity,
translation, scale, rotation, and existing stroke-draw properties. Every
timeline, including the three existing performances, returns every part to its
data-rendered opacity and zero transform before its repeat delay. This is a
deliberate compatibility tightening: the existing character performances must
replace their current dimmed confirmation rests with their original SVG
opacity. `prefers-reduced-motion: reduce` continues to create zero GSAP
timelines.

| Icon | Prepare | Semantic action | Confirm | Quiet performance ID |
| --- | --- | --- | --- | --- |
| `search` | lens leans | scan crosses lens | star marker pops | `search-scout-find-v1` |
| `tool` | lid lifts | wrench drops/turns | spark appears | `tool-kit-action-v1` |
| `api` | slots brighten | request point traverses | receipt/check lights | `api-signal-return-v1` |
| `memory` | cards offset | bookmark slides in | key line lights | `memory-index-commit-v1` |
| `output` | envelope opens | result card rises | check draws | `output-envelope-reveal-v1` |
| `file` | corner lifts | three lines draw | dot settles | `file-note-write-v1` |
| `folder` | tab rises | sheet slides in | folder closes | `folder-file-store-v1` |
| `cloud` | kite leans | data point rises | cloud light appears | `cloud-uplink-ready-v1` |
| `shield` | core focuses | scan arc crosses | check lights | `shield-guard-confirm-v1` |
| `token` | shell tightens | core lights | four ticks appear | `token-intent-ready-v1` |

Existing `agent`, `operator`, and `database` remain visually unchanged and
keep their current `brain-think-pulse-v1`, `operator-type-focus-v1`, and
`bucket-ingest-confirm-v1` performance IDs.

## Complete performance contract

This is the implementation source table for the character motion mapping. The
required parts are exactly the registry parts after `root`; the manifest must
not maintain a second divergent part list.

| Icon | Performance | Required parts |
| --- | --- | --- |
| `agent` | `brain-think-pulse-v1` | `brain-left`, `brain-right`, `chip`, `signal`, `spark` |
| `operator` | `operator-type-focus-v1` | `hair`, `face`, `glasses`, `hands`, `laptop`, `cursor` |
| `database` | `bucket-ingest-confirm-v1` | `hat`, `bucket`, `liquid`, `bead`, `check` |
| `search` | `search-scout-find-v1` | `lens`, `scan`, `marker`, `spark` |
| `tool` | `tool-kit-action-v1` | `bucket`, `lid`, `wrench`, `spark` |
| `api` | `api-signal-return-v1` | `interface`, `request`, `receipt`, `status` |
| `memory` | `memory-index-commit-v1` | `back-card`, `front-card`, `bookmark`, `key-line` |
| `output` | `output-envelope-reveal-v1` | `envelope`, `card`, `check`, `spark` |
| `file` | `file-note-write-v1` | `page`, `corner`, `line-1`, `line-2`, `line-3`, `dot` |
| `folder` | `folder-file-store-v1` | `folder`, `tab`, `sheet`, `seal` |
| `cloud` | `cloud-uplink-ready-v1` | `cloud`, `kite`, `data-dot`, `ready-light` |
| `shield` | `shield-guard-confirm-v1` | `shell`, `core`, `scan`, `check` |
| `token` | `token-intent-ready-v1` | `shell`, `core`, `tick-left`, `tick-right`, `tick-top`, `tick-bottom` |

## Architecture

### Registry and SVG renderer

`illustrated_character_icons.py` remains the data-only source of truth. Add
one `CharacterIconDefinition` per expanded icon with:

- semantic role;
- stable named `parts` (the root plus only the parts a runtime needs);
- normalized 100×100 clean-room primitives.

`renderer_illustrated_character.py` remains responsible only for serialization,
palette lookup, stable `icon_part_id` generation, and node-local transforms.
The existing `render_semantic_icon` routes every valid known icon to the
character renderer when `icon_system` is `illustrated-character-v1`.

### Motion manifest and runtime

Add a dedicated mapping for all 13 character performance IDs; do not overload
the existing legacy `ICON_PERFORMANCE_V2` mapping. In the character-system
branch, `CharacterIconDefinition.parts` is the sole source for the manifest
selector map; the performance mapping supplies only the performance ID. The
manifest must always serialize the resolved `icon_system` and emit every
declared character part as a stable CSS selector.

Add one GSAP function per new performance. Functions must use `setInitial`,
guard with `hasParts`, and create a timeline with `repeat: -1` plus a quiet
`repeatDelay`. The shared runtime behavior continues to suppress playback when
reduced motion is requested.

### Compatibility and errors

`illustrated-v1` remains an explicit legacy bubble mode. `semantic-line-v1`
remains an explicit legacy line mode. After this expansion, every schema-valid
icon is covered by `illustrated-character-v1`; therefore ordinary valid scene
quality reports under the default system produce no
`character_icon_fallback` warnings. The fallback mechanism remains in place for
future schema additions or a deliberately incomplete registry.

## Examples and review surface

Replace the temporary fallback demonstration in the character flow example
with a narrative using only covered character icons; it must contain no fallback
copy or fallback warning. Add an expanded illustrated-character gallery
example containing exactly all 13 `KNOWN_ICONS`. Browser-captured WebP outputs
are the visual review surface; their SVG and HTML siblings remain the
inspectable source artifacts.

## Acceptance criteria

1. `character_icon_ids()` equals the full schema icon set.
2. Every character definition has nonempty, unique parts. For all 13 icons,
   `set(manifest.parts)` equals `set(definition.parts)` and every selector maps
   to exactly one SVG ID in the generated HTML.
3. Default HTML runtime manifests map all 13 icons to the exact performance
   IDs in the complete performance contract; explicit legacy systems retain
   their existing behavior.
4. The runtime dispatch registers every performance in the complete contract,
   and every function uses its matching required-part guard.
5. Reduced-motion browser verification reports zero timelines for the gallery
   and flow examples.
6. The gallery's icon set equals `KNOWN_ICONS`; the flow contains no fallback
   label or fallback warning. Both reports have zero errors and zero fallback
   warnings. Existing schema invalid-icon errors remain unchanged.
7. Browser verification samples each timeline after its action phase and before
   the repeat delay, confirming every part has its source opacity and an
   identity transform. Full test suite, JavaScript syntax checks, browser
   capture, visual inspection, and `git diff --check` pass.

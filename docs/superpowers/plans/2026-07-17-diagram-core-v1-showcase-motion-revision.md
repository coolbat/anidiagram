# Diagram Core v1 Showcase Motion Revision Plan

## Status

- Product decision: approved by coolbat on 2026-07-17
- Supersedes: six-state portions of the 2026-07-16 Phase 0-1 plan after Checkpoint A
- Public system: `AniDiagram Diagram Core Icon System v1.0`
- Branch: `codex/diagram-core-v1-phase-0-1`
- Promotion state: four benchmark assets remain `visual-review`

## Goal

Ship four canonical authored-rest icons plus one commonly used, deliberately
expressive `showcase` presentation profile. Defer
`idle / active / processing / success / warning / error` until Phase 2 defines
the runtime-stage and execution-result flow.

## Model

```text
authored-rest-pose                       static SVG fallback
showcase                                 scene presentation profile, not State
agent.showcase-loop-v1                   presentation performance
database.showcase-loop-v1                presentation performance
api.showcase-loop-v1                     presentation performance
server.showcase-loop-v1                  presentation performance
semantic states                          Phase 2, currently unsupported
```

Presentation performances use the existing GSAP runtime. Canonical SVG contains
no animation, scripts, effects, external resources, or semantic state glyphs.
Missing GSAP, motion off, cancel, and reduced motion all resolve to the authored
rest pose.

## Non-negotiable compatibility

- `DEFAULT_ICON_SYSTEM` remains `illustrated-character-v1`.
- The existing 13 DiagramScript icon ids remain valid.
- `server` does not enter DiagramScript validation before the new Checkpoint B.
- The four benchmark catalog and manifests remain `visual-review`.
- The canonical 96 x 96 viewBox, stable public parts, effect attachments, and
  exact three-segment instance-id contract remain intact.
- No geometry is copied into Python, JavaScript, tests, or an SDK adapter.

## Tasks

### 1. Migrate the asset capability contract

- Increase `catalog_revision` from 1 to 2 and four `asset_revision` values from
  1 to 2.
- Set four catalog `supported_states` and manifest `states` arrays to empty.
- Remove the frozen six-state validators while retaining catalog/manifest parity.
- Make adapter state optional; only emit `data-icon-state` for a future supported
  semantic state.

### 2. Restore canonical SVG to one authored rest pose

- Remove root `data-icon-state` and every `data-state-mark` geometry.
- Keep one non-semantic indicator treatment and the future `status` attachment.
- Add a public `body` group where needed so runtime motion never overwrites the
  adapter placement transform.
- Remove state visibility CSS. State color tokens may remain only as explicitly
  reserved future tokens and must not count as current capabilities.

### 3. Replace the static gate

- Replace 72-cell Agent and 288-cell benchmark matrices with authored-rest
  matrices.
- Benchmark coverage is exactly 4 icons x 3 sizes x 4 contexts = 48 cells.
- Recognition coverage is exactly 4 modes x 4 icons = 16 cells.
- Keep the existing static capture fail-closed, JavaScript-disabled,
  animation-disabled, network-free, and byte-deterministic.

### 4. Implement the presentation performances

- Add four `kind: presentation` definitions to the motion catalog.
- Add four GSAP functions to the existing runtime, targeting only stable
  `data-part` selectors from the motion manifest.
- Use 6-10 unit translation, 8-14 degree rotation, or 0.88-1.16 body scale at
  peak. Small blink/pulse parts may use 0.12-1.45 when identity and clipping stay
  intact. Active motion is 1600-2400 ms followed by 800-1400 ms rest.
- Mark a canonical rest time and seek it before killing any showcase timeline.

### 5. Build the live review

- Generate `gallery/diagram-core/showcase.html` from canonical assets.
- Inline the pinned local GSAP build and repository runtime for deterministic,
  network-free review.
- Show only four large icons, staggered, with Pause, Replay, Showcase, and Off
  controls. Do not expose a second motion profile in the v1 review.

### 6. Verify motion separately from static capture

- Normal mode creates exactly four isolated showcase timelines.
- Peak inspection proves each icon has at least one meaningful part above the
  expressive amplitude threshold.
- Stop, restart, Off, and complete-cycle settle restore authored rest transforms.
- Reduced motion and no-GSAP modes create zero icon timelines and preserve all
  static geometry.
- No phase clips the review cell or changes the node/connection anchor geometry.

### 7. Reset approval evidence

- Append a scope amendment to the Checkpoint A record rather than rewriting
  history.
- Preserve approval for Agent silhouette, side ear caps, visual weight, and
  family baseline.
- Mark six-state approval and the old Checkpoint B candidate as superseded.
- Require new human approval for the 48-cell rest matrix and live showcase page.

### 8. Validate and stop at the new Checkpoint B

- Run strict asset, manifest, part, instance, static-capture, motion-runtime,
  reduced-motion, and full unittest gates.
- Do not promote assets, add Server to DiagramScript, switch the default system,
  or implement semantic states without explicit user approval.

## Acceptance surfaces

```text
Static rest/theme:  4 icons x 3 sizes x 4 contexts             = 48 cells
Recognition:        4 icons x 4 modes at 48 px                 = 16 cells
Motion storyboard:  4 icons x 3 sizes x light/dark x 4 phases = 96 cells
Live review:        4 icons at 144 px with runtime controls
```

The motion storyboard is a later baseline-promotion artifact. During the visual
candidate stage, deterministic timeline/DOM evidence plus the live review are
required; no motion baseline becomes approved without human review.

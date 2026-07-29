# Icon System Release Status

## Purpose

This page is the current-state index for AniDiagram icon-system identity,
defaults, motion contracts, and release boundaries. Historical plans, review
contracts, releases, and snapshots retain the facts of their own stage and are
not rewritten when the current release advances.

## Default scope

AniDiagram has three intentionally different omission behaviors:

| Input path | Default icon system | Default motion | Why |
| --- | --- | --- | --- |
| DiagramPlan v0.2 compiled through `composition-v1` to DiagramScript v0.4 | `illustrated` (2.5.0) | `showcase-v1` | Current semantic-first product path |
| Direct DiagramScript v0.4 without `composition_policy` | `diagram-core-v1` | `expressive` when motion is omitted | Manually authored v0.4 compatibility path |
| DiagramScript v0.1-v0.3 or a legacy style that omits `icon_system` | `illustrated-character-v1` | `expressive` when scene motion is omitted | Pixel-stable compatibility path |

Composition-v1 resolves `motion.profile=showcase-v1` together with
`motion_policy.profile=unrestricted`, `motion_area=unrestricted`, and
`pulse_mode=all`. `showcase-v1` is not a valid motion-policy budget profile.

`ambient` is the default HTML runtime mode. It is not an icon system or a
motion profile. The runtime toolbar's Expressive mode is also distinct from the
serialized `showcase-v1` composition profile. `timeline` and `hybrid` are
explicit Choreographer v1 modes and never replace ambient by omission.

## Current public systems

| Public id | Status | Assets | Motion behavior | Default? |
| --- | --- | ---: | --- | --- |
| `diagram-core-v1` | approved | 56 | All eligible Diagram Core performances run under `showcase-v1` | No; select explicitly |
| `illustrated` | approved, implementation version 2.5.0 | 56 | `illustrated-performance-v6`, automatic under public `showcase-v1` | Yes, for composition-v1 |
| `illustrated-character-v1` | supported legacy compatibility system | 13 | Character v1 semantic loops and Motion Coordination v1.2 | Only on the legacy omission path |
| `illustrated-v1` | explicit legacy compatibility system | legacy set | Legacy illustrated runtime mapping | No |
| `semantic-line-v1` | explicit legacy compatibility system | legacy set | Legacy semantic-line runtime mapping | No |

`illustrated-character-v2` is an accepted input alias for `illustrated`. New
plans and resolved DiagramScript output use the stable `illustrated` id and
record implementation version `2.5.0` separately.

## Illustrated 2.5.0

The approved registry contains 56 icons and has exact semantic-id parity with
Diagram Core v1. The first twenty 2.4.0 icons remain unchanged in identity;
2.5.0 adds the remaining people, AI/data, content/media, network/compute,
source/delivery, and runtime/operations families.

Current live sources:

- `assets/illustrated/catalog.json`
- `src/anidiagram/illustrated_registry.py`
- `assets/illustrated/template-mappings.json`
- `assets/illustrated/tokens-2.5.0.json`
- `assets/illustrated/motion-contracts/illustrated-performance-v6.json`
- `assets/illustrated/releases/2.5.0.json`
- `assets/illustrated/reviews/2.5.0-acceptance.json`

The public v6 contract contains all 56 performances and supersedes v5 for new
`illustrated` diagrams. The v6/v7 review contracts, batch approvals,
convention-alignment proof, 13 x 56 template matrix, and Governed RAG real-case
proof remain approval evidence and are not emitted as public motion contracts.
The 2.4.0 release and public v5 contract remain archived unchanged.

## Edge Motion 1.0.0

`edge-motion-v1` is the frozen, human-approved connection-edge contract for new
output. Runtime manifests record both `edge_motion_contract=edge-motion-v1` and
`edge_motion_version=1.0.0`.

Its four dynamic recipes are deliberately non-overlapping:

- `packet-flow`: one borderless solid packet on a static arrow;
- `comet-flow`: one borderless head with three shrinking fading echoes;
- `stream-flow`: one moving dashed stroke without particles;
- `draw`: one source-to-target reveal.

The canonical sources and release evidence are:

- `assets/edge-motion/edge-motion-v1.json`
- `src/anidiagram/edge_motion.py`
- `src/anidiagram/motion_manifest_v2.py`
- `runtime/edge-motion-v1-runtime.js`
- `assets/edge-motion/reviews/v1.0.0-acceptance.json`
- `assets/edge-motion/releases/v1.0.0.json`

Edge Motion and Illustrated are independently versioned. Illustrated 2.5.0 was
promoted only after its separate real-case and public-registration approvals.

## Choreographer v1

`runtime/choreographer-v1-runtime.js` is an additive scheduling layer for
explicit `timeline` and `hybrid` output. It leaves the frozen ambient runtime
and Edge Motion runtime sources byte-for-byte unchanged. Ordered scene edges
become causal source/edge/target steps with start, previous, and next controls.
Timeline begins the explanation immediately; hybrid begins in ambient and
switches only after user action.

The layer is independently syntax-checked and browser-verified by
`scripts/verify_choreographer.mjs`. It does not redefine Illustrated or Edge
Motion contract versions, and does not yet claim event-driven scheduling,
camera choreography, or node state machines.

## Immutable archive boundary

Do not update historical facts merely to match the current release. In
particular, preserve:

- releases 2.0.0, 2.1.0, 2.2.0, 2.3.0, and 2.4.0;
- `2.2.0.static-motion-review.json` and `2.3.0.static-motion-review.json`;
- motion contracts v1, v2, v2-review, v3, v3-review, v4, v4-review, v5,
  v5-review, v6-review, and v7-review;
- `2.3.0-static-acceptance.json`;
- versioned 2.0.0-2.3.0 snapshots and every `*.static-motion-review.*` snapshot;
- historical material under `docs/superpowers/specs/` and
  `docs/superpowers/plans/`.

Legacy example names and public compatibility ids are also retained. Current
documentation should scope them as legacy rather than rename or delete them.

## Verification gates

Diagram Core:

```bash
PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --strict --json
```

Expected contract: 56 approved assets, zero errors, and zero warnings.

Illustrated 2.5.0:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/illustrated-2.5-showcase.diagram.json \
  --outdir outputs/illustrated-2.5-showcase \
  --basename illustrated-2.5-showcase \
  --formats svg,html,quality
node --check runtime/anidiagram-runtime.js
node --check runtime/illustrated-performance-v6-runtime.js
node --check runtime/edge-motion-v1-runtime.js
node --check runtime/choreographer-v1-runtime.js
node scripts/verify_character_motion_rest.mjs \
  outputs/illustrated-2.5-showcase/illustrated-2.5-showcase.html 56 illustrated
node scripts/verify_character_reduced_motion.mjs \
  outputs/illustrated-2.5-showcase/illustrated-2.5-showcase.html 56 illustrated
node scripts/verify_stage_motion_modes.mjs \
  outputs/illustrated-2.5-showcase/illustrated-2.5-showcase.html
```

Standalone package, Choreographer, and committed visual-asset gates are also
part of the release contract:

```bash
python3 -m pip wheel . --no-deps --wheel-dir build/wheels
PYTHONPATH=src python3 scripts/check_asset_budget.py
node scripts/verify_choreographer.mjs build/ci/choreographer/timeline.html timeline
node scripts/verify_readme_showcase_round_1.mjs gallery/readme-showcase
```

The generated quality report must contain zero errors. Contract or renderer
changes also require the full Python test suite and a diff check:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
git diff --check
```

Generate and independently verify the two-system browser export matrix with:

```bash
PYTHONPATH=src python3 scripts/build_icon_system_release_evidence.py
PYTHONPATH=src python3 scripts/build_icon_system_release_evidence.py --verify
```

The formal capture contract is 10 formats at 24 FPS, 108 frames, and 2x scale.
Verification requires exact catalog and motion-manifest identity, clean quality,
browser renderer metadata, distinct whole frames, and visible per-icon pixel
changes in the frame-based Lottie capture.

## CI and evidence retention

`.github/workflows/test.yml` protects pull requests and `main` with three
levels of validation. The package matrix builds and smoke-renders the installed
wheel outside the checkout on Python 3.9, 3.11, and 3.14. The contract job runs
the complete Python suite, strict 56-icon Diagram Core validation, asset
budgets, JavaScript syntax checking, and a render smoke test. The browser job
regenerates the current Illustrated showcase, composition-v1 edge-flow proof,
and explicit timeline/hybrid pages, then checks all 56 Illustrated rest poses,
reduced motion, runtime mode switching, Choreographer controls, README text
containment, edge-label collisions, and nonzero edge-flow coverage in Chromium.

The formal two-system export matrix is intentionally not generated on every
pull request because the current evidence bundle is about 333 MB. Run
`.github/workflows/icon-system-release-evidence.yml` through
`workflow_dispatch` for a release candidate. It installs the pinned Playwright
runtime plus ffmpeg, builds four bounded `system x format-shard` fragments,
merges them back into the canonical two-system matrix, independently verifies
the complete result, and uploads `outputs/release-evidence/icon-systems` as a
commit-addressed GitHub Actions artifact retained for 14 days. Sharding changes
only CI scheduling; the formal contract remains 10 formats at 24 FPS, 108
frames, and 2x scale.

The latest retained remote evidence before 2.5.0 is GitHub Actions run
[`29909815356`](https://github.com/coolbat/anidiagram/actions/runs/29909815356)
for the 2.4.0 commit `2392226`. Its final 333,810,052-byte artifact passed both merge-time
and independent verification with two systems, ten formats, and zero issues,
and is retained through 2026-08-05 10:05:44 UTC. The artifact is CI evidence,
not a tracked source release or a replacement for the immutable approval
records.

The local 2.5.0 release evidence is
`outputs/release-evidence/icon-systems/public-icon-system-export-evidence.json`
(15,449 bytes, SHA-256
`6b7f446cbb4941d7b8f1d3135285fc151871ab2c3c284178fa92fb8047b662cb`).
It passed two systems x ten formats at browser 24 FPS, 108 frames, and 2x scale
with 56 automatic performances per system, at least three visible states per
icon, and zero issues. Remote retention for 2.5.0 begins after this source
release is pushed and the manual evidence workflow is dispatched.

## Updating this page

Update current status only after the new public catalog, acceptance record,
release record, renderer behavior, and verification evidence agree. Add a new
version or archived stage instead of rewriting an immutable release.

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
| DiagramPlan v0.2 compiled through `composition-v1` to DiagramScript v0.4 | `diagram-core-v1` | `showcase-v1` | Current semantic-first product path |
| Direct DiagramScript v0.4 without `composition_policy` | `diagram-core-v1` | `expressive` when motion is omitted | Manually authored v0.4 compatibility path |
| DiagramScript v0.1-v0.3 or a legacy style that omits `icon_system` | `illustrated-character-v1` | `expressive` when scene motion is omitted | Pixel-stable compatibility path |

Composition-v1 resolves `motion.profile=showcase-v1` together with
`motion_policy.profile=unrestricted`, `motion_area=unrestricted`, and
`pulse_mode=all`. `showcase-v1` is not a valid motion-policy budget profile.

`ambient` is the default HTML runtime mode. It is not an icon system or a
motion profile. The runtime toolbar's Expressive mode is also distinct from the
serialized `showcase-v1` composition profile.

## Current public systems

| Public id | Status | Assets | Motion behavior | Default? |
| --- | --- | ---: | --- | --- |
| `diagram-core-v1` | approved | 56 | All eligible Diagram Core performances run under `showcase-v1` | Yes, for composition-v1 |
| `illustrated` | approved, implementation version 2.3.0 | 16 | `illustrated-performance-v4`, automatic under public `showcase-v1` | No; select explicitly |
| `illustrated-character-v1` | supported legacy compatibility system | 13 | Character v1 semantic loops and Motion Coordination v1.2 | Only on the legacy omission path |
| `illustrated-v1` | explicit legacy compatibility system | legacy set | Legacy illustrated runtime mapping | No |
| `semantic-line-v1` | explicit legacy compatibility system | legacy set | Legacy semantic-line runtime mapping | No |

`illustrated-character-v2` is an accepted input alias for `illustrated`. New
plans and resolved DiagramScript output use the stable `illustrated` id and
record implementation version `2.3.0` separately.

## Illustrated 2.3.0

The approved assets are:

`agent`, `operator`, `tool`, `output`, `database`, `api`, `search`, `memory`,
`file`, `folder`, `cloud`, `shield`, `user`, `server`, `ai-model`, and
`message-queue`.

Current live sources:

- `assets/illustrated/catalog.json`
- `src/anidiagram/illustrated_registry.py`
- `assets/illustrated/template-mappings.json`
- `assets/illustrated/tokens-2.3.0.json`
- `assets/illustrated/motion-contracts/illustrated-performance-v4.json`
- `assets/illustrated/releases/2.3.0.json`
- `assets/illustrated/reviews/2.3.0-acceptance.json`

The public v4 contract contains all sixteen performances. It supersedes v3 for
new `illustrated` diagrams; it does not mutate v3 or the releases that depend on
v3. `illustrated-performance-v4-review` is immutable human-review evidence and
must not be emitted by new diagrams.

## Immutable archive boundary

Do not update historical facts merely to match the current release. In
particular, preserve:

- releases 2.0.0, 2.1.0, and 2.2.0;
- `2.2.0.static-motion-review.json` and `2.3.0.static-motion-review.json`;
- motion contracts v1, v2, v2-review, v3, v3-review, and v4-review;
- `2.3.0-static-acceptance.json`;
- versioned 2.0.0-2.2.0 snapshots and every `*.static-motion-review.*` snapshot;
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

Illustrated 2.3.0:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/illustrated-2.3-showcase.diagram.json \
  --outdir outputs/illustrated-2.3-showcase \
  --basename illustrated-2.3-showcase \
  --formats svg,html,quality
node --check runtime/anidiagram-runtime.js
node scripts/verify_character_motion_rest.mjs \
  outputs/illustrated-2.3-showcase/illustrated-2.3-showcase.html 16 illustrated
node scripts/verify_character_reduced_motion.mjs \
  outputs/illustrated-2.3-showcase/illustrated-2.3-showcase.html 16 illustrated
node scripts/verify_stage_motion_modes.mjs \
  outputs/illustrated-2.3-showcase/illustrated-2.3-showcase.html
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

`.github/workflows/test.yml` protects pull requests and `main` with two levels
of validation. The contract job runs the complete Python suite, strict 56-icon
Diagram Core validation, JavaScript syntax checking, and a render smoke test.
The browser job regenerates the current Illustrated showcase and a
composition-v1 edge-flow proof, then checks all sixteen Illustrated rest poses,
reduced motion, runtime mode switching, and nonzero edge-flow coverage in
Chromium.

The formal two-system export matrix is intentionally not generated on every
pull request because the current evidence bundle is about 333 MB. Run
`.github/workflows/icon-system-release-evidence.yml` through
`workflow_dispatch` for a release candidate. It installs the pinned Playwright
runtime plus ffmpeg, builds and independently verifies the complete matrix, and
uploads `outputs/release-evidence/icon-systems` as a commit-addressed GitHub
Actions artifact retained for 14 days. The artifact is CI evidence, not a
tracked source release or a replacement for the immutable approval records.

## Updating this page

Update current status only after the new public catalog, acceptance record,
release record, renderer behavior, and verification evidence agree. Add a new
version or archived stage instead of rewriting an immutable release.

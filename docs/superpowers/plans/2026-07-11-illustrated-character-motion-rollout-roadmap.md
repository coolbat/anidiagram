# Illustrated Character v1 Motion Coordination and Rollout Roadmap

> **Status:** Approved for task planning. Implementation has not started from
> this roadmap.
>
> **Source of truth:** This document owns the unfinished work that follows the
> initial `illustrated-character-v1` implementation and full 13-icon expansion.
> The two 2026-07-10 implementation plans remain historical implementation
> records and should not be reused as the active backlog.

## Goal

Ship `illustrated-character-v1` as AniDiagram's coherent default icon system,
with coordinated ambient motion, real Expressive/Readable/Off behavior, tested
theme compatibility, representative example coverage, and release-grade export
evidence.

## Confirmed Baseline

The following decisions are inputs to this roadmap and are not open for redesign
unless a later visual review explicitly rejects them:

- `illustrated-character-v1` remains the default icon system.
- `illustrated-v1` and `semantic-line-v1` remain explicit legacy choices.
- All 13 schema icons keep their existing clean-room character drawings and
  semantic `prepare -> action -> confirm -> quiet` performances.
- Character timelines keep a `0.8 s` repeat gap, a `0.44 s` idle breath, and a
  `1.012` breath scale.
- Character cards and authored root transforms remain stable; motion stays in
  local icon parts and the dedicated motion shell.
- Explicit `preset: none` disables icon motion. An empty effect object does not.
- Operating-system reduced motion creates no GSAP timelines.
- No third-party icon code, runtime package, or visual asset is introduced.

## Motion Coordination Contract v1.1

### Expressive

- Character performances remain the primary visual focus.
- A moving edge shows one semantic packet at a time. A white halo and colored
  core may form one packet, but duplicate packets and a competing full-edge dash
  are not both continuously prominent.
- Edge cycles include a short quiet interval instead of restarting immediately.
- Title highlight plays once on entry; it is not a frequent ambient loop.
- Group frames use `soft-reveal` by default. A continuous border scan must be an
  explicit, budgeted exception.

### Readable

- Readable must change runtime behavior, not only a CSS class.
- Character semantic performances may remain, with the confirmed timing intact.
- Decorative title sweep is disabled after the initial static title is visible.
- Edge packets are reduced to the policy-approved key paths; decorative packet
  layers, relation circles, group fields, and scanning borders are hidden.
- The scene remains understandable when motion is paused at any sampled frame.

### Off and reduced motion

- `Off` pauses and removes all GSAP-owned stage and icon motion while preserving
  the canonical static scene.
- `prefers-reduced-motion: reduce` creates no GSAP timelines and shows the same
  canonical static scene.

## Dependency Order

```text
Baseline ledger
  -> motion-mode tests
    -> Readable behavior
    -> edge rhythm
    -> title and border restraint
      -> motion catalog freeze
        -> theme integration and comparison
          -> example migration and gallery rebuild
            -> export matrix, docs, and release verification
```

## Phase 1: Motion Coordination v1.1

### Task 1: Record the implementation baseline and scoped change ledger

**Description:** Capture the files and contracts owned by this roadmap before
runtime work begins. Keep unrelated dirty-worktree changes outside every future
staging operation.

**Acceptance criteria:**

- [x] Current character runtime, manifest, examples, theme variants, tests, and
  generated proof paths are listed in the implementation handoff.
- [x] Files with overlapping pre-existing changes are identified before editing.
- [x] No unrelated gallery or user-authored changes are staged or reverted.

**Verification:**

- [x] `git status --short` and scoped `git diff -- <paths>` are reviewed.
- [x] Existing character tests pass before behavior changes.

**Dependencies:** None.

**Files likely inspected:** `runtime/anidiagram-runtime.js`,
`src/anidiagram/motion_manifest.py`, `src/anidiagram/renderer_html_runtime.py`,
`tests/test_render_svg.py`.

**Estimated scope:** S.

### Task 2: Define failing runtime-mode and stage-rhythm tests

**Description:** Add contract tests before changing stage motion. Tests must
distinguish Expressive, Readable, Off, and operating-system reduced motion.

**Acceptance criteria:**

- [x] Source tests assert the approved edge packet count, quiet interval, and
  one-shot title behavior.
- [x] A browser verifier confirms which timelines/elements remain in each mode.
- [x] The initial tests fail against the current runtime for the expected reasons.

**Verification:**

- [x] Focused unit tests fail before implementation and pass afterward.
- [x] The browser verifier exits nonzero when Readable behaves like Expressive.

**Dependencies:** Task 1.

**Files likely touched:** `tests/test_render_svg.py`,
`scripts/verify_stage_motion_modes.mjs`.

**Estimated scope:** M.

### Task 3: Make Readable a real runtime mode

**Description:** Replace the current class-only mode switch with explicit stage
and timeline behavior while preserving the confirmed character timing.

**Acceptance criteria:**

- [x] Switching to Readable removes decorative title and nonessential stage
  effects without restarting character timelines from an incorrect pose.
- [x] Switching back to Expressive restores the approved stage effects without
  duplicating runtime-generated SVG elements or timelines.
- [x] Off remains a canonical static scene and Restart respects the active mode.

**Verification:**

- [x] Browser mode verifier passes Expressive -> Readable -> Off -> Expressive.
- [x] Runtime-generated element and timeline counts remain stable after repeated
  mode switching.
- [x] `node --check runtime/anidiagram-runtime.js` passes.

**Dependencies:** Task 2.

**Files likely touched:** `runtime/anidiagram-runtime.js`,
`src/anidiagram/renderer_html_runtime.py`, `tests/test_render_svg.py`.

**Estimated scope:** M.

### Task 4: Simplify and retime expressive edge flow

**Description:** Make edge motion support the character action rather than form a
second competing animation system.

**Acceptance criteria:**

- [x] One logical packet travels on each policy-approved active edge at a time.
- [x] Each packet cycle includes a `0.6-0.8 s` quiet interval.
- [x] The continuous dash layer is either removed or visually subordinate to the
  packet, with edge labels remaining fully readable.
- [x] Edge counts respect `motion_policy` rather than animating every edge merely
  because the scene profile is Expressive.

**Verification:**

- [x] Unit tests assert packet count, repeat gap, and policy clamping.
- [x] Browser verifier samples at least two cycles without duplicate packets.
- [x] The 8-icon character flow has no overlap or clipping at packet endpoints.

**Dependencies:** Tasks 2 and 3.

**Files likely touched:** `runtime/anidiagram-runtime.js`,
`src/anidiagram/motion_manifest.py`, `tests/test_render_svg.py`,
`scripts/verify_stage_motion_modes.mjs`.

**Estimated scope:** M.

### Task 5: Make title motion an entry accent

**Description:** Convert `highlight-sweep` from a frequent ambient loop into a
restrained entry treatment.

**Acceptance criteria:**

- [x] The runtime title highlight plays once and settles into the authored title.
- [x] Readable and Off never leave the title partially collapsed or obscured.
- [x] Runtime cleanup and Restart restore the correct title geometry.
- [x] The implementation avoids continuously animating SVG `width` and `x`.

**Verification:**

- [x] Browser verifier confirms no title timeline repeat after the first pass.
- [x] Restart replays exactly one title entry.
- [x] Default, Deep Tech, and Teaching Sketch titles remain readable.

**Dependencies:** Task 3.

**Files likely touched:** `runtime/anidiagram-runtime.js`,
`tests/test_render_svg.py`, `scripts/verify_stage_motion_modes.mjs`.

**Estimated scope:** S.

### Task 6: Restrain group and node-frame motion for character themes

**Description:** Preserve stable cards and group frames around the animated
characters while retaining explicit border effects for specialized diagrams.

**Acceptance criteria:**

- [x] Character theme defaults use `soft-reveal` or `static` group motion.
- [x] `border-scan`, `marching-ants`, and `corner-pulse` remain explicit presets.
- [x] At most one continuous scanning group survives a focused/readable policy.
- [x] `icon-performance` does not cause whole-card float, glow, or ripple motion.

**Verification:**

- [x] Renderer and quality tests cover default restraint and explicit opt-in.
- [x] Character gallery and flow show stable node and group frames.

**Dependencies:** Tasks 2 and 3.

**Files likely touched:** `src/anidiagram/schema.py`,
`src/anidiagram/renderer_svg.py`, `src/anidiagram/quality.py`,
`tests/test_render_svg.py`.

**Estimated scope:** M.

### Checkpoint A: Motion coordination approval

- [x] Full Python test suite passes.
- [x] Runtime JavaScript and both browser verifiers pass.
- [x] Character rest-state and reduced-motion checks still pass for 13-icon and
  8-icon examples.
- [x] Expressive, Readable, and Off are visually distinct.
- [x] Human review approves the new edge/title/border balance before rollout.

## Phase 2: Catalog and Theme Rollout

### Task 7: Freeze the Character v1 motion catalog

**Description:** Extend the frozen catalog so the approved Character v1
performances and Motion Coordination v1.1 stage effects are reviewable without
overwriting legacy v2 entries.

**Acceptance criteria:**

- [x] All 13 Character v1 performance IDs, parts, phases, rest times, repeat gap,
  breath values, and stagger contract are represented.
- [x] Legacy v2 performances remain explicitly labeled and selectable.
- [x] Catalog change-control text names Expressive, Readable, Off, and reduced
  motion behavior.

**Verification:**

- [x] Catalog JSON validates and every referenced part exists in generated HTML.
- [x] Runtime motion catalog tests and gallery links pass.

**Dependencies:** Checkpoint A.

**Files likely touched:** `runtime/motion-catalog.json`,
`examples/runtime-motion-catalog.diagram.json`, `scripts/build_showcase.py`,
`tests/test_showcase_gallery.py`.

**Estimated scope:** M.

### Task 8: Officially integrate Deep Tech and Teaching Sketch Character

**Description:** Promote the two approved trial themes into supported character
theme combinations without changing the legacy `teaching-sketch` contract.

**Acceptance criteria:**

- [x] Deep Tech renders Character v1 through the default icon-system resolution.
- [x] `teaching-sketch-character` remains a distinct supported variant.
- [x] Role colors, outlines, labels, cards, edge packets, and title accents meet
  contrast and clipping requirements in both themes.

**Verification:**

- [x] Both themes render SVG, HTML, WebP, and clean quality reports.
- [x] Character rest, stage-mode, and reduced-motion browser checks pass.

**Dependencies:** Task 7.

**Files likely touched:** `styles/deep-tech.json`,
`styles/teaching-sketch-character.json`, `styles/catalog.json`,
`tests/test_render_svg.py`.

**Estimated scope:** M.

### Task 9: Generate a three-theme comparison page

**Description:** Provide one review surface for Default Character, Deep Tech,
and Teaching Sketch Character using identical icon and flow content.

**Acceptance criteria:**

- [x] The page embeds or links the same scene in all three themes.
- [x] Each theme exposes HTML, SVG, WebP, and quality evidence links.
- [x] The page labels motion mode and icon-system values explicitly.

**Verification:**

- [x] All links resolve locally and the page has no console errors.
- [x] Generated asset paths are covered by showcase tests.

**Dependencies:** Task 8.

**Files likely touched:** `scripts/build_showcase.py`,
`tests/test_showcase_gallery.py`, generated comparison assets under `gallery/`.

**Estimated scope:** M.

### Task 10: Test additional bundled theme compatibility

**Description:** Evaluate Character v1 against `minimal-light`, `dark-luxury`,
`blueprint`, `claude-warm`, and `aurora-orb` without automatically promoting
all of them to official combinations.

**Acceptance criteria:**

- [x] Each theme receives a documented pass, tune, or incompatible decision.
- [x] Decisions cover contrast, clipping, icon/card hierarchy, edge visibility,
  and title motion.
- [x] Only token-level adaptations are allowed; character SVG geometry is not
  forked per theme.

**Verification:**

- [x] Candidate outputs render with clean quality reports or an explicit known
  incompatibility note.
- [x] A human review checkpoint selects any additional official combinations.

**Dependencies:** Task 9.

**Files likely touched:** theme profiles selected by review, comparison manifest,
`tests/test_showcase_gallery.py`.

**Estimated scope:** M per compatibility batch.

### Checkpoint B: Theme and catalog approval

- [x] Catalog shows all current and legacy performances accurately.
- [x] Three-theme comparison page is browser-reviewed.
- [x] Additional theme decisions are recorded without multiplying icon geometry.
- [x] Gallery generation remains deterministic.

## Phase 3: Apply Character v1 to Existing Product Examples

### Task 11: Migrate representative architecture examples

**Description:** Apply the default Character v1 system to a small, representative
set before rebuilding the complete gallery.

**Target examples:** Agent Memory, High Fidelity Runtime, Loop Engineering, and
one example each from pipeline, layered, and sequence layouts.

**Acceptance criteria:**

- [x] Examples rely on the default icon system unless they intentionally prove a
  legacy mode.
- [x] Semantic icon choices match node meaning; no decorative substitutions.
- [x] Dense diagrams use Readable or focused motion budgets.
- [x] Labels, arrows, icons, and groups do not overlap.

**Verification:**

- [x] Every migrated example has clean quality output.
- [x] HTML review confirms the new stage rhythm and correct mode controls.
- [x] Static SVG remains understandable without runtime motion.

**Dependencies:** Checkpoint B.

**Files likely touched:** selected specs under `examples/`, corresponding tests,
and generated review outputs.

**Estimated scope:** M per example batch.

### Task 12: Rebuild the showcase gallery deliberately

**Description:** Regenerate gallery surfaces only after representative examples
are approved, preserving explicit legacy demonstrations.

**Acceptance criteria:**

- [x] Gallery manifest distinguishes default Character v1 from legacy icon modes.
- [x] Runtime motion, style, layout, and hero pages point to current artifacts.
- [x] Generated changes are reviewed for unintended mass churn before staging.

**Verification:**

- [x] `PYTHONPATH=src python3 scripts/build_showcase.py --quality` passes.
- [x] `PYTHONPATH=src python3 -m unittest tests.test_showcase_gallery` passes.
- [x] Gallery pages have no broken local asset links.

**Dependencies:** Task 11.

**Files likely touched:** `scripts/build_showcase.py`, gallery specs and manifests,
generated `gallery/` assets, `tests/test_showcase_gallery.py`.

**Estimated scope:** M.

### Checkpoint C: Product-surface approval

- [x] Representative architecture diagrams are readable in motion and at rest.
- [x] Gallery default and legacy modes are correctly labeled.
- [x] No unrelated generated churn is included in the scoped change set.

## Phase 4: Export, Documentation, and Release

### Task 13: Verify the complete export matrix

**Description:** Prove that Character v1 and Motion Coordination v1.1 survive all
supported outputs with the correct renderer ownership.

**Formats:** SVG, HTML, PNG, WebP, GIF, APNG, MP4, PDF, and browser-frame Lottie.

**Acceptance criteria:**

- [x] SVG provides a valid lightweight/static fallback where JavaScript runtime
  performances are unavailable.
- [x] Browser-backed animated formats capture the GSAP runtime rather than a
  duplicate SMIL animation layer.
- [x] Every written artifact is nonempty and every quality report is clean.
- [x] Unsupported optional tooling is reported as skipped, never silently passed.

**Verification:**

- [x] Export result JSON records renderer, status, frame count, FPS, and paths.
- [x] Animated outputs contain visible frame differences.
- [x] At least one light and one dark theme complete the full matrix.

**Dependencies:** Checkpoint C.

**Files likely touched:** `src/anidiagram/exporters.py`, export tests, generated
release-evidence outputs.

**Estimated scope:** M.

### Task 14: Synchronize English and Chinese documentation

**Description:** Document the final defaults, explicit legacy modes, motion-mode
behavior, theme choices, examples, and export limitations.

**Acceptance criteria:**

- [x] README and DiagramScript docs state that Character v1 is the default.
- [x] HTML runtime docs explain Expressive, Readable, Off, reduced motion, edge
  quiet gaps, one-shot title treatment, and border restraint.
- [x] Documentation links to the comparison page and canonical examples.
- [x] English and Chinese capability claims remain equivalent.

**Verification:**

- [x] Documentation commands run as written.
- [x] Tests that assert documented defaults and verifier commands pass.
- [x] `git diff --check` passes.

**Dependencies:** Task 13.

**Files likely touched:** `README.md`, `README.zh-CN.md`,
`docs/diagram-script.md`, `docs/html-runtime.md`.

**Estimated scope:** M.

### Task 15: Final verification and scoped version-control handoff

**Description:** Produce a clean, reviewable implementation handoff without
absorbing unrelated worktree changes.

**Acceptance criteria:**

- [x] Full tests, JavaScript syntax checks, browser verifiers, showcase build,
  export checks, and quality checks pass from the final source state.
- [x] Relevant changes are grouped into small, reviewable commits or an explicit
  unstaged handoff if overlapping user changes prevent safe staging.
- [x] Generated outputs are included only when they are intentional release or
  gallery evidence.
- [x] Remaining future runtime modes stay documented as roadmap items, not
  shipped capabilities.

**Verification:**

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
node --check runtime/anidiagram-runtime.js
node scripts/verify_character_motion_rest.mjs \
  outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html
node scripts/verify_character_reduced_motion.mjs \
  outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html 13
node scripts/verify_stage_motion_modes.mjs \
  outputs/illustrated-character-v1-flow/illustrated-character-v1-flow.html
PYTHONPATH=src python3 scripts/build_showcase.py --quality
git diff --check
```

**Dependencies:** Task 14.

**Files likely touched:** No new product file is required; this task verifies and
organizes the completed scoped work.

**Estimated scope:** S.

### Checkpoint D: Release candidate

- [x] All acceptance criteria in Tasks 1-15 are complete.
- [x] No feel-breaking motion regressions remain.
- [x] Browser-visible proof paths and final test commands are recorded.
- [x] The branch is ready for human review and the chosen git handoff.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Existing dirty worktree contains overlapping implementation and generated files | High | Start with the scoped ledger; inspect every diff; never stage or revert unrelated changes. |
| Expressive stage effects overpower character semantics | High | Enforce one-packet edge contract, title entry-only behavior, and browser mode tests. |
| Readable remains cosmetic rather than behavioral | High | Verify timeline and runtime-generated element counts in a real browser. |
| Theme adaptation forks character geometry | Medium | Restrict theme work to palette/style tokens and keep one character registry. |
| Gallery regeneration creates large unintended churn | Medium | Approve representative examples first and review generated diffs before staging. |
| Animated exports diverge from HTML runtime | High | Capture browser-owned runtime and assert visible frame differences plus renderer metadata. |
| Legacy modes regress while defaults change | Medium | Keep explicit legacy fixtures and catalog entries in unit and gallery tests. |

## Long-Horizon Document Decision

This roadmap **is intentionally a multi-session task list** because the work has
four dependent phases, fifteen testable tasks, multiple human visual-review
checkpoints, and a broad export matrix. A single short implementation plan would
not preserve enough execution state across sessions.

This roadmap is **not yet an unattended long-horizon execution contract**. Do
not create `docs/agent-loop-state.md`, `docs/release-evidence.md`, or a morning
handoff file solely because this roadmap exists. Those control surfaces become
necessary only if the user explicitly asks Codex to execute the roadmap
continuously or unattended across multiple milestones. At that point:

1. Freeze the approved milestone range and authority boundaries.
2. Create the long-horizon state and evidence documents.
3. Mark human visual approvals as `needs_decision` gates.
4. Keep publishing, pushing, merging, and deployment outside the run unless
   explicitly authorized.

## Recommended Immediate Sequence

Execute Tasks 1-2 first, then implement Tasks 3-6 as one Motion Coordination
v1.1 milestone. Stop at Checkpoint A for browser review before changing the
motion catalog, themes, examples, or generated gallery.

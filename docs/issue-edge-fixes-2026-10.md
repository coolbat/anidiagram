# Edge identity and endpoint review

Reviewed against `283a40c37efcb5ab05b7fd605fa337721aa7b7de` on 2026-10-14.

## Issue #10: edge identity depends on label placement

Confirmed for `data-relation-id` and `data-direction`: unlabelled edges and
legacy-label rendering omit them. `data-source` and `data-target` already exist
unconditionally. Failed label placement also already retains the relation ID;
the placement result contains `placed: false` rather than disappearing.

Emit the four identity attributes for every edge. Only label-placement metadata
depends on label placement. Missing semantic IDs use the same zero-based
`@edge:<index>` fallback as the visible HTML relation table.

The quality report checks the Scene before rendering, so an absent HTML
attribute is a rendered-artifact failure, not an invalid unlabelled relation.
The strict browser audit now rejects missing or mismatched identity attributes,
including on edges without labels. Negative browser fixtures remove the ID or
change the source and must fail with `edge-identity`.

## Issue #9: explicitly routed endpoints are shortened

Confirmed: both two-point and multi-segment authored routes are shortened by
12 pixels at each endpoint. Compiled Plan routes already end at boundary ports,
and Pillow exports already preserve explicit points. SVG must use those same
points. Preserve explicit route endpoints; retain the existing clearance for
automatically anchored edges without points. Quality geometry and SVG paths
continue to use the same route function.

The alleged horizontal arrival at a top-center port is not reproduced in the
final Plan output. The current visibility-grid router emits outward endpoint
stubs normal to the chosen side of the node.

## Issue #8: shared right-side skip-lane corridor

The cited `_apply_layered_loop_presentation` intermediate paths share a corridor,
but `compile_plan_v02` subsequently calls `route_compiled_edges` and replaces
them. That final router accounts for obstacles and existing-track congestion.
The three-skip-lane regression exercises the actual Plan compiler, checks that
the long vertical tracks are not shared by all three edges, and verifies normal
entry into node-side ports. This case passes before changing the renderer.

No speculative change to the intermediate corridor allocator is included.
A frozen input that reproduces overlap in the final router would be needed to
establish that separate routing bug.

## Compatibility checkpoint

The old optimization snapshot is retained as historical evidence. Before these
fixes, the recorded `283a40c` style migration already changes seven cases:
`minimal-light` aliases `openai-minimal`, and `notion-clean` / `flat-icon` are
redesigned. That migration is documented in the existing changelog and locked
down by the existing style-profile tests.

Comparing these fixes directly against `283a40c` across all 21 snapshot cases
shows identical compiled specification and quality hashes. Only SVG and HTML
hashes change in 18 cases, for unconditional edge identity and preservation of
explicit route endpoints. The new edge-fix checkpoint covers the current style
contract and these intentional renderer changes, without weakening the exact
hash comparison or rewriting the older checkpoint.

## Gallery verification exposed by the restored CI gate

The first full browser CI run reached the previously skipped Gallery check and
failed on the committed `flat-icon` preview. Its `motion-budget-v2` manifest
declares two ambient icons and four hover-only icons; the old checker required
all six to animate without interaction. This also reproduces locally with
unchanged Gallery HTML.

The checker now samples declared ambient icons for a complete beat and triggers
each declared hover-only icon separately. Every icon must belong to one tested
set, ambient icons must move, and each hover-only performance must move when
triggered. No Gallery assets or production runtime behavior are changed.

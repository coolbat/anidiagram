# Archify follow-ups: compatibility assessment and implementation

Baseline: `18cb0f35e41f907210852de5ca0edbe9adcc2970`; 302 Python tests pass.

The proposal is safe with additive, explicitly enabled extensions. Two proposed
structures need correction: DiagramPlan already owns `semantic.intent.diagram_kind`
and `semantic.sources` / `source_refs`. Reuse these rather than adding competing
top-level semantics. Existing source notes remain valid without a Git checkout.

Compatibility requirements:

- Existing Plan 0.1/0.2 and Script 0.1–0.4 retain their defaults, geometry, motion,
  SVG/HTML bytes, and quality behavior when new features are absent.
- Repository-backed sources explicitly opt into commit/file/line verification.
  Verification proves a reference exists, not that its architectural claim is true.
- New reader state is optional, outside motion scheduling and canonical exports.
- Compare and visual-check are separate commands. Validation fails before replacing
  output; the existing delivery transaction remains the commit mechanism.
- Type-specific semantic checks apply only when new `type_details` are supplied;
  existing free-form `diagram_kind` values continue to work.
- No third-party renderer, asset, or runtime is copied. No published release assets
  are regenerated in place.

Implementation sequence:

1. P0: revision-pinned repository sources → verified Scene evidence → HTML/receipt.
2. P1: semantic Plan comparison, presentation/geometry changes reported separately.
3. P1: optional authored node/route/reach reader, role filters and deep links.
4. P2: fixed-viewport visual evidence command and artifact-bound receipt.
5. P2: opt-in typed semantics with sequence, lifecycle, dataflow, workflow, architecture checks.
6. P3: curated guided views and exportable selection share cards.

Validation: legacy hash snapshot, focused failure/round-trip tests per slice,
full Python suite, strict Diagram Core assets, runtime motion browser gates,
reader interactions, installed-resource packaging, and real CLI delivery receipts.

## Completed implementation

All six slices were implemented as opt-in extensions, in the order above:

| Slice | Local commit | Result |
| --- | --- | --- |
| Evidence | `b562cef` | Local Git blob verification, pinned source links, evidence receipt |
| Comparison | `d7cbc1a` | Semantic/presentation/geometry delta and transactional HTML/JSON pair |
| Reader | `16e7ade` | Authored topology queries, search/roles, shareable reading state |
| Visual evidence | `b189311` | Frozen HTML capture, containment checks, sidecar receipts |
| Typed semantics | `c51afcb` | Five opt-in types validated against existing stable IDs |
| Chapters/cards | `3bd3bb1` | Curated chapters and selection SVG/1200×630 PNG export |

The final hardening pass also adds CI gates, an independent schema validator,
checked-in compatibility hashes, malformed-evidence tests, and usage documentation.
No dependency on Archify or additional engine runtime dependency was introduced.

## Verified locally on 2026-09-06

- Python 3.14.3: **328 tests passed**, up from the 302-test baseline.
- Legacy compatibility: **21 cases unchanged** for compiled specifications,
  SVG, HTML, and quality hashes (with the invalid legacy fixture retaining its
  original validation result). The baseline is checked into
  `tests/compatibility-baseline-18cb0f3.json` for future CI runs.
- Diagram Core: **56 approved assets, 0 errors, 0 warnings**; committed README
  and gallery asset budgets passed. Published visual assets were not rewritten.
- Illustrated browser gates: 56-icon showcase rest/reduced-motion and motion
  modes passed; the 13-node/13-edge real case also passed, including exactly
  2 active readable edges. The reader-enabled production request case retained
  4 character and 3 edge timelines and passed its motion-mode cycle.
- Reader: graph cycle/direction tests passed; real browser search, route/no-route,
  upstream, URL round trips, chapter navigation, and SVG/PNG downloads passed
  with **0 page errors**. Canonical SVG export and source HTML remained unchanged.
- Responsive reader: expanded controls and the diagram fit all four supported
  desktop viewports. The repository example's visual receipt has **8 successful
  captures**, no document overflow, and no stage clipping. A deliberately clipped
  negative fixture correctly failed. Human visual review remains **pending**.
- Six complete example deliveries passed with **0 quality errors**; all **30
  source/artifact hashes** matched their receipts. The real comparison reported
  1 semantic change, 1 presentation change, and 0 geometry changes.
- Independent JSON Schema validation passed for **15 schemas / 23 documents**,
  including plans, compiled specs, delivery, comparison, and visual receipts.
- A standalone wheel was built and tested outside the source checkout, including
  repository-evidence delivery and the packaged visual-check entry point.

CI configuration now contains the new gates, but remote CI, publishing, and
deployment have **not** been run. Local checks are not release approval.

## Artifacts and boundaries

- [Usage and contracts](./verified-reading.md)
- [Repository-backed reader example](../outputs/archify-followups/repository-reader.html)
- [Semantic comparison](../outputs/archify-followups/repository-delta.html)
- [Visual contact sheet](../outputs/archify-followups/repository-reader.visual.html)
- [Exported selection card](../outputs/archify-followups/selection-card.png)

Generated proof artifacts are local/ignored; recreate them with
`PYTHONPATH=src python3 scripts/build_verified_reading_proofs.py`.
The source example intentionally pins the original `18cb0f3` baseline and does
not claim to map the newly added implementation or verify its architectural claims.

Typed semantics provide constraints, metadata, readable facts, and sequence
numbering, not a new UML lifeline renderer. Source verification currently supports
one local GitHub repository per artifact and never fetches or executes source code.
Visual-check requires optional Node/Playwright/Chromium tooling; it reports
`skipped` instead of a false pass when unavailable. There are no new database,
service, publication, or production-state changes.

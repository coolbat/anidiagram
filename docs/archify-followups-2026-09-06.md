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

Progress and final evidence will be recorded here as each slice is verified.

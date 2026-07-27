# Prompt to Diagram Flow

AniDiagram treats source reading, semantic extraction, presentation resolution,
layout compilation, rendering, motion, export, and quality checks as one staged
product flow.

## Current contract

DiagramPlan v0.2 and DiagramScript v0.4 implement `composition-v1`. Meaning is
stored independently from four sibling presentation axes: icon system, visual
style, layout, and motion. DiagramPlan v0.1 and DiagramScript v0.1-v0.3 remain
supported as the legacy compatibility path.

See [the composition contract](./diagram-composition-contract.md),
[ADR-001](./decisions/ADR-001-separate-semantic-content-from-presentation.md),
and [the v0.2 schema](../schemas/diagram-plan-v0.2.schema.json).

## Pipeline

1. Read the user brief, article, document, or notes completely.
2. Build DiagramPlan v0.2 `semantic`: intent, entities, relations, groups,
   flows, importance, state, and source provenance.
3. Resolve the four presentation requests. User choices win; otherwise the
   model may choose style and layout, the icon default is `illustrated` 2.5.0,
   and the motion default is `showcase-v1`.
4. Record model-selected concrete values in `presentation_sources`; unresolved
   `auto` values receive deterministic compiler defaults.
5. Compile to DiagramScript v0.4. The compiler emits coordinates and a
   `resolved_presentation` record before any renderer runs.
6. Render SVG and high-fidelity HTML, then export requested media.
7. Require a clean quality report and inspect the browser runtime modes.

The renderer never chooses a style, layout, icon system, or motion profile. It
only consumes the resolved DiagramScript.

## CLI paths

Compile an authored semantic plan:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --plan examples/contracts/production-request-path.plan.json \
  --spec-out outputs/production-request-path.diagram.json \
  --outdir outputs \
  --basename production-request-path \
  --formats svg,html,quality
```

The deterministic local brief scaffold also defaults to DiagramPlan v0.2:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --brief examples/briefs/loop-engineering.txt \
  --outdir outputs \
  --basename loop-engineering \
  --formats svg,html,quality \
  --plan-out outputs/loop-engineering.plan.json \
  --spec-out outputs/loop-engineering.diagram.json
```

An LLM-facing Skill should author the v0.2 semantic plan directly because it
can understand domain-specific entity and relation kinds better than the local
model-free brief scaffold.

## Selection responsibility

- The model decides semantic structure and, when the user is silent, selects a
  suitable style and layout from the registered catalogs.
- The composition compiler validates references, resolves fallbacks, maps
  semantic kinds and roles to icon ids, and serializes concrete geometry.
- The icon system owns canonical SVG parts and semantic performances.
- The style owns color and surface tokens, not the icon-system identity.
- The motion system owns runtime recipes, rest poses, and reduced-motion
  behavior, not semantic meaning.

## Legacy path

Call `brief_to_plan(..., version="0.1")` when a consumer explicitly needs the
old `explainer-board` plan and DiagramScript v0.3 output. Existing v0.1-v0.3
specifications continue to use the previous style-bound icon-system resolution.
They are not silently migrated to Diagram Core.

## Next optimization slices

- Improve the 16 individual layout engines while preserving the same semantic
  contract.
- Expand semantic state and result mappings when process-stage diagrams are
  implemented.
- Add richer model-selection prompt fixtures and layout repair passes.
- Continue tuning individual icon and motion systems behind their stable ids.

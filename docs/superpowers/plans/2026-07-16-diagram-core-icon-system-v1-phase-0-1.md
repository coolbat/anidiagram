# Diagram Core Icon System v1 Phase 0–1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze the Diagram Core v1 asset contract and ship four manually approved, static, theme-aware benchmark icons—agent, database, api, and server—without changing AniDiagram’s default icon system or starting Phase 2 motion work.

**Architecture:** Root-level canonical SVG and JSON manifests remain the only hand-maintained asset source. Standard-library Python loaders validate and instance-scope those assets for the existing SVG renderer; the scene renderer uses approved Diagram Core assets explicitly and preserves the current renderer for unmigrated legacy icons. A deterministic 288-cell static matrix, a pinned Chromium capture, and a human approval record gate promotion from visual-review to approved.

**Tech Stack:** Python 3.9-compatible standard library, SVG 1.1, CSS custom properties with static fallbacks, JSON Schema documents plus strict Python validation, unittest, Pillow through the existing raster extra, Node.js, pinned Playwright Chromium, and GitHub Actions.

## Global Constraints

- Execute only Phase 0 and Phase 1 from the approved product and engineering specifications.
- Do not create runtime performances, diagram-core-performances.js, React components, or any of the remaining 52 SVG assets.
- Keep DEFAULT_ICON_SYSTEM equal to illustrated-character-v1. Diagram Core becomes the default only after the later 14-asset Phase 3 gate.
- Keep all four benchmark catalog entries and manifests at visual-review until the final contact sheet is explicitly approved by the user.
- Do not add server to DiagramScript validation before that approval.
- Keep the 13 legacy DiagramScript icon ids valid throughout the work.
- Never copy hand-maintained path geometry into Python, JavaScript, tests, or generated SDK code.
- Canonical SVG may contain static state marks but no animate elements, runtime particles, travelling payloads, scan effects, scripts, external resources, embedded raster data, text labels, or connection anchors.
- Phase 1 static states use data-icon-state and six distinct non-color-only marks: idle, active, processing, success, warning, and error. This is static rendering, not a Phase 2 performance implementation.
- New DOM ids use the exact three-segment contract instance-key__icon-id__part-name. Do not modify the legacy Character id contract during this phase.
- Python syntax and type annotations must remain valid on Python 3.9.
- Validation commands fail closed. Missing Pillow, Playwright, Chromium, assets, manifests, parts, or baselines must not be reported as a successful visual check.
- The current pre-change baseline is 82 passing unittest cases. Existing tests and gallery assertions must remain green.

---

## Source-of-Truth Sets

Keep these sets separate in code and tests:

~~~text
CATALOG_IDS                  = exactly 56 frozen ids
LEGACY_VALID_ICON_IDS        = exactly 13 current DiagramScript ids
APPROVED_DIAGRAM_CORE_IDS    = 0 before visual approval, exactly 4 afterward
DIAGRAMSCRIPT_VALID_ICON_IDS = LEGACY_VALID_ICON_IDS union APPROVED_DIAGRAM_CORE_IDS
~~~

At final Phase 1 acceptance:

~~~text
catalog ids            = 56
legacy valid ids       = 13
canonical SVG assets   = 4
asset manifests        = 4
approved core assets   = 4
DiagramScript valid ids= 14
~~~

## File Structure

### Canonical source and contracts

- Create assets/diagram-core/catalog.json — all 56 catalog records.
- Create assets/diagram-core/tokens.css — default tokens, four validation contexts, and static state selectors.
- Create assets/diagram-core/icons/agent.svg — canonical Agent geometry.
- Create assets/diagram-core/icons/database.svg — canonical Database geometry.
- Create assets/diagram-core/icons/api.svg — canonical API geometry.
- Create assets/diagram-core/icons/server.svg — canonical Server geometry.
- Create assets/diagram-core/manifests/agent.json — Agent capabilities and attachments.
- Create assets/diagram-core/manifests/database.json — Database capabilities and attachments.
- Create assets/diagram-core/manifests/api.json — API capabilities and attachments.
- Create assets/diagram-core/manifests/server.json — Server capabilities and attachments.
- Create schemas/diagram-core-catalog-v1.schema.json — frozen catalog shape.
- Create schemas/diagram-core-icon-manifest-v1.schema.json — frozen per-asset shape.

### Python adapter

- Create src/anidiagram/diagram_core/__init__.py — public constants and read-only APIs.
- Create src/anidiagram/diagram_core/catalog.py — catalog loader, lifecycle sets, and validation.
- Create src/anidiagram/diagram_core/manifest.py — manifest model and validation.
- Create src/anidiagram/diagram_core/asset_loader.py — source/install asset discovery and secure SVG loading.
- Create src/anidiagram/diagram_core/instance_ids.py — collision-safe instance key and part-id generation.
- Create src/anidiagram/diagram_core/tokens.py — style-profile-to-icon-token mapping and contrast helpers.
- Create src/anidiagram/diagram_core/adapter.py — canonical SVG instancing for preview and scene use.

### Validation, review, and generated evidence

- Create scripts/sync_diagram_script_icons.py — regenerate or check the v0.3 JSON Schema icon enum.
- Create scripts/validate_diagram_core_assets.py — aggregate strict structural validation.
- Create scripts/check_diagram_core_parts.py — repeated-instance and local-reference validation.
- Create scripts/render_diagram_core_contact_sheet.py — deterministic agent-only and four-icon review surfaces.
- Create scripts/capture_diagram_core_contact_sheet.mjs — pinned Chromium locator screenshot.
- Create scripts/compare_diagram_core_contact_sheet.py — one-percent pixel-diff gate and approval metadata.
- Create gallery/diagram-core/index.html — labeled, accessible static review page.
- Create gallery/diagram-core/agent-review.html — Agent-first visual checkpoint page.
- Create gallery/diagram-core/recognition.html — label-hidden and accent-off recognition page.
- Create gallery/diagram-core/cell-index.json — machine-readable 288-cell index.
- Create assets/diagram-core/previews/agent-contact-sheet.svg — committed Agent checkpoint.
- Create assets/diagram-core/previews/benchmark-contact-sheet.svg — committed final static matrix.
- Create assets/diagram-core/previews/baselines/benchmark.chromium-linux.png — approved visual baseline.
- Create assets/diagram-core/previews/baselines/benchmark.chromium-linux.json — approval and environment metadata.
- Create docs/diagram-core-phase-1-approval.md — human decisions, asset digests, and Phase 2 boundary.

### Existing integration points

- Modify src/anidiagram/schema.py — separate legacy validity from approved Diagram Core validity.
- Modify schemas/diagram-script-v0.3.schema.json — add server only after approval.
- Modify src/anidiagram/icon_system.py — accept diagram-core-v1 while preserving the old default.
- Modify src/anidiagram/styles.py and schemas/style-profile-v0.1.schema.json — validate the explicit system id.
- Modify src/anidiagram/renderer_svg.py — explicit canonical/legacy routing and Diagram Core sizing.
- Modify src/anidiagram/motion_manifest.py — keep Diagram Core icons static during Phase 1.
- Modify src/anidiagram/quality.py — explicit, deduplicated Diagram Core fallback warnings.
- Modify pyproject.toml — package canonical assets as generated wheel data without a second source tree.
- Create package.json and package-lock.json — pin visual-test Playwright tooling.
- Modify .github/workflows/test.yml — add asset and locked-browser visual gates.
- Modify tests/test_render_svg.py — bind legacy Character coverage assertions to the legacy 13-id set.
- Create tests/test_diagram_core_catalog.py.
- Create tests/test_diagram_core_assets.py.
- Create tests/test_diagram_core_adapter.py.
- Create tests/test_diagram_core_visuals.py.
- Modify docs/diagram-script.md and docs/html-runtime.md — document Phase 1 behavior without changing README defaults or examples.

## Chunk 1: Freeze the Data Contracts

### Task 1: Create the exact 56-id catalog and lifecycle model

**Files:**

- Create: assets/diagram-core/catalog.json
- Create: schemas/diagram-core-catalog-v1.schema.json
- Create: src/anidiagram/diagram_core/__init__.py
- Create: src/anidiagram/diagram_core/catalog.py
- Create: tests/test_diagram_core_catalog.py

- [ ] **Step 1: Write the failing catalog inventory tests**

Define the frozen ids directly in the test so accidental catalog edits cannot redefine the expectation:

~~~python
EXPECTED_BY_CATEGORY = {
    "actors": (
        "user", "developer", "operator", "agent", "agent-team",
        "assistant", "human-reviewer",
    ),
    "ai-models": (
        "ai-model", "llm", "neural-network", "reasoning",
        "embedding", "memory", "tool", "token",
    ),
    "data-knowledge": (
        "database", "vector-database", "data-warehouse",
        "document-store", "knowledge-base", "dataset", "search",
    ),
    "files-content": (
        "file", "folder", "document", "pdf", "image",
        "audio", "video", "code-file", "output",
    ),
    "network-interfaces": (
        "api", "webhook", "http-request", "gateway",
        "load-balancer", "message-queue", "shield",
    ),
    "compute-runtime": (
        "server", "server-cluster", "cloud",
        "container", "function", "edge-node",
    ),
    "development-delivery": (
        "source-code", "git-repository", "branch",
        "pull-request", "ci-cd", "deployment",
    ),
    "operations-observability": (
        "task", "scheduler", "monitoring", "logs", "alert", "debug",
    ),
}

def test_catalog_freezes_exact_inventory_and_category_counts(self):
    catalog = load_catalog()
    actual = {
        category: tuple(entry.icon_id for entry in catalog.entries if entry.category == category)
        for category in EXPECTED_BY_CATEGORY
    }
    self.assertEqual(EXPECTED_BY_CATEGORY, actual)
    self.assertEqual(56, len(catalog.entries))
    self.assertEqual(56, len({entry.icon_id for entry in catalog.entries}))

def test_catalog_starts_benchmarks_in_visual_review(self):
    catalog = load_catalog()
    status = {entry.icon_id: entry.status for entry in catalog.entries}
    self.assertEqual(
        {"agent", "database", "api", "server"},
        {icon_id for icon_id, value in status.items() if value == "visual-review"},
    )
    self.assertEqual(52, sum(value == "planned" for value in status.values()))

def test_valid_id_sets_follow_approval_without_changing_legacy_ids(self):
    catalog = load_catalog()
    promoted = catalog_fixture_with_status(catalog, "server", "approved")
    self.assertEqual(
        LEGACY_VALID_ICON_IDS,
        legacy_valid_icon_ids(promoted),
    )
    self.assertEqual(
        {"server"},
        set(approved_icon_ids(promoted)),
    )
    self.assertEqual(
        set(LEGACY_VALID_ICON_IDS) | {"server"},
        set(diagram_script_valid_icon_ids(promoted)),
    )
~~~

Also assert:

- category counts are 7, 8, 7, 9, 7, 6, 6, and 6;
- aliases never collide with another id or alias;
- all 13 legacy ids are catalog members;
- every record has id, category, semantic_kind, structural_prototype, aliases, parts, supported_states, supported_actions, status, and asset_revision;
- planned records use asset_revision 0 and benchmark records use asset_revision 1;
- status is one of planned, visual-review, approved, or deprecated.
- semantic_kind equals the canonical icon id for all 56 entries;
- the 52 planned entries use structural_prototype `unassigned` and expose no parts, states, or actions;
- the four benchmark entries freeze the exact prototypes, parts, six states, and actions listed below.

- [ ] **Step 2: Run the focused test and confirm red**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest tests.test_diagram_core_catalog
~~~

Expected: FAIL because the catalog module and catalog file do not exist.

- [ ] **Step 3: Implement the catalog schema, data, and standard-library loader**

Use immutable dataclasses and an injected root for tests:

~~~python
CATALOG_SYSTEM_ID = "diagram-core-v1"
CATALOG_STATUSES = frozenset(
    {"planned", "visual-review", "approved", "deprecated"}
)
LEGACY_VALID_ICON_IDS = frozenset(
    {
        "agent", "api", "cloud", "database", "file", "folder",
        "memory", "operator", "output", "search", "shield", "token", "tool",
    }
)

@dataclass(frozen=True)
class CatalogEntry:
    icon_id: str
    category: str
    semantic_kind: str
    structural_prototype: str
    aliases: Tuple[str, ...]
    parts: Tuple[str, ...]
    supported_states: Tuple[str, ...]
    supported_actions: Tuple[str, ...]
    status: str
    asset_revision: int
~~~

Catalog top-level fields are system, public_name, catalog_revision, and icons. Set public_name to AniDiagram Diagram Core Icon System v1.0 and catalog_revision to 1.

Phase 0 freezes only capabilities that are already evidenced:

- Set `semantic_kind` to the canonical icon id for all 56 entries. In v1 it is the stable semantic key, not a partially populated coarse ontology. The isolated `database: storage` example in the product PRD is superseded by this uniform rule.
- For the 52 planned entries, set `structural_prototype` to `unassigned` and keep `parts`, `supported_states`, and `supported_actions` empty. A roadmap concept is not an implemented Diagram Core capability.
- For the four visual-review benchmarks, freeze `structural_prototype` as `actor-character`, `stacked-storage`, `interface-module`, and `compute-device` for Agent, Database, API, and Server respectively.
- Freeze benchmark parts to these exact ordered tuples:

~~~text
agent    = shell, face-screen, eye-left, eye-right, mouth, antenna, core, indicator
database = shell, top-ring, layer-top, layer-middle, layer-bottom, core, indicator
api      = shell, header, input-interface, output-interface, processor, indicator-group
server   = shell, tray-top, tray-bottom, indicator-top, indicator-bottom, vent-top, vent-bottom, base
~~~

- Give all four benchmarks the ordered states `idle`, `active`, `processing`, `success`, `warning`, and `error`.
- Freeze actions as Agent `enter, receive, process, send`; Database `receive, write, index, search, send`; API `receive, process, send, stream`; and Server `enter, receive, process, send`.
- Use empty aliases everywhere because no alias has been explicitly approved. Do not infer aliases from labels, abbreviations, or legacy implementation names.

- [ ] **Step 4: Run the catalog tests and confirm green**

Run the Step 2 command.

Expected: PASS with exactly 56 entries and four visual-review benchmarks.

- [ ] **Step 5: Commit the catalog slice**

~~~bash
git add assets/diagram-core/catalog.json schemas/diagram-core-catalog-v1.schema.json src/anidiagram/diagram_core/__init__.py src/anidiagram/diagram_core/catalog.py tests/test_diagram_core_catalog.py
git commit -m "feat: freeze Diagram Core icon catalog"
~~~

### Task 2: Freeze and validate the Icon Asset Manifest and SVG safety contracts

**Files:**

- Create: schemas/diagram-core-icon-manifest-v1.schema.json
- Create: src/anidiagram/diagram_core/manifest.py
- Create: src/anidiagram/diagram_core/asset_loader.py
- Create: tests/test_diagram_core_assets.py

- [ ] **Step 1: Write failing in-memory contract tests**

Use temporary files so validation is proven before real icons exist:

~~~python
VALID_MANIFEST = {
    "id": "database",
    "system": "diagram-core-v1",
    "asset_revision": 1,
    "viewBox": "0 0 96 96",
    "category": "data-knowledge",
    "semantic_kind": "database",
    "structural_prototype": "stacked-storage",
    "parts": [
        "shell", "top-ring", "layer-top", "layer-middle",
        "layer-bottom", "core", "indicator"
    ],
    "attachments": {
        "receive": {"x": 48, "y": 8},
        "send": {"x": 88, "y": 48},
        "status": {"x": 48, "y": 78},
    },
    "states": ["idle", "active", "processing", "success", "warning", "error"],
    "actions": ["receive", "write", "index", "search", "send"],
    "status": "visual-review",
}

def test_manifest_accepts_frozen_contract(self):
    manifest = validate_manifest_dict(VALID_MANIFEST)
    self.assertEqual("database", manifest.icon_id)
    self.assertEqual("0 0 96 96", manifest.view_box)

def test_manifest_rejects_scene_selectors_and_out_of_bounds_attachments(self):
    invalid = copy.deepcopy(VALID_MANIFEST)
    invalid["parts"] = ["#database__shell"]
    invalid["attachments"]["send"]["x"] = 97
    with self.assertRaises(ManifestValidationError) as raised:
        validate_manifest_dict(invalid)
    self.assertEqual(
        {"$.parts[0]", "$.attachments.send.x"},
        {issue.path for issue in raised.exception.issues},
    )
~~~

Add SVG fixture tests that reject script, foreignObject, image, text, animate, external href, data URI, filter, author ids, anonymous public parts, non-scaling-stroke without an approved exception, and CSS variable references without literal fallbacks. Each temporary asset fixture must include its own minimal `tokens.css`; Task 2 must not depend on the repository-level token file created in Task 4.

Add catalog-to-manifest parity tests. For every implemented asset, `id`, `category`, `semantic_kind`, `structural_prototype`, `parts`, `states`, `actions`, `status`, and `asset_revision` must exactly match its catalog entry. A mismatch in any field fails closed with the catalog and manifest paths identified.

Freeze paintable tags as path, rect, circle, ellipse, line, polyline, polygon, and use. The 24-element limit counts only those tags; report total DOM elements separately.

- [ ] **Step 2: Run the focused tests and confirm red**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest tests.test_diagram_core_assets
~~~

Expected: FAIL because manifest.py and asset_loader.py do not exist.

- [ ] **Step 3: Implement strict standard-library validation**

Use json, gzip, pathlib, dataclasses, and xml.etree.ElementTree only. Do not add jsonschema or lxml as runtime dependencies.

Manifest rules:

- exact system id diagram-core-v1;
- integer asset_revision of at least 1 for implemented assets;
- exact viewBox 0 0 96 96;
- kebab-case unique public parts;
- finite attachment coordinates in the inclusive 0–96 range;
- six required static review states for benchmark assets;
- all duplicated catalog fields synchronized with its catalog entry: id, category, semantic_kind, structural_prototype, parts, states, actions, status, and asset_revision;
- optional exceptions require metric, reason, reviewer, and approved_on; a boolean waiver is invalid.

SVG rules:

- root svg has role=img, focusable=false, a nonempty aria-label, and data-icon matching the filename;
- no authored id attributes in canonical files;
- public data-part values are unique and exactly match the manifest;
- no JavaScript, animation, external references, embedded raster data, runtime text, or complex filters;
- every var reference has a literal fallback and names a token declared in tokens.css;
- raw file size is at most 12 KiB and gzip level-9 size is at most 6 KiB unless a complete approved exception exists;
- paintable element count is at most 24 unless a complete approved exception exists.

Provide asset_root parameters on load_catalog, load_manifest, load_svg_source, and load_asset so tests do not depend on the repository location. Freeze a read-only `LoadedAsset` result that exposes `manifest`, `svg_source`, `root`, `public_parts`, and `metrics`; `metrics` exposes forbidden, paintable, total-DOM, raw-size, and gzip-size counts. `load_asset(icon_id, allow_statuses, asset_root=None)` is the single aggregate validation entry point used by later tasks and returns only after catalog, manifest, SVG, token, status, and parity checks pass.

- [ ] **Step 4: Prove invalid fixtures fail for the intended reasons**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest tests.test_diagram_core_assets
~~~

Expected: PASS. Each invalid fixture reports its precise JSON or SVG path and no fixture is silently normalized.

- [ ] **Step 5: Commit the contract validator slice**

~~~bash
git add schemas/diagram-core-icon-manifest-v1.schema.json src/anidiagram/diagram_core/manifest.py src/anidiagram/diagram_core/asset_loader.py tests/test_diagram_core_assets.py
git commit -m "feat: validate Diagram Core asset contracts"
~~~

### Task 3: Separate catalog membership from DiagramScript validity

**Files:**

- Modify: src/anidiagram/schema.py
- Modify: tests/test_render_svg.py
- Modify: tests/test_diagram_core_catalog.py
- Create: scripts/sync_diagram_script_icons.py

- [ ] **Step 1: Write failing lifecycle and compatibility tests**

~~~python
def test_planned_catalog_icon_is_not_implemented(self):
    result = validate_scene(scene_spec_with_icon("user"))
    issue = result["error"]["issues"][0]
    self.assertEqual("$.nodes[0].icon", issue["path"])
    self.assertEqual("icon_not_implemented", issue["code"])

def test_visual_review_server_is_not_yet_valid(self):
    result = validate_scene(scene_spec_with_icon("server"))
    self.assertEqual(
        "icon_not_implemented",
        result["error"]["issues"][0]["code"],
    )

def test_unknown_icon_remains_an_enum_error(self):
    result = validate_scene(scene_spec_with_icon("not-a-real-icon"))
    self.assertEqual("enum", result["error"]["issues"][0]["code"])

def test_all_legacy_ids_remain_valid_during_review(self):
    for icon_id in sorted(LEGACY_VALID_ICON_IDS):
        with self.subTest(icon_id=icon_id):
            self.assertEqual(icon_id, compile_scene(scene_spec_with_icon(icon_id)).nodes[0].icon)
~~~

Change the old Character tests to assert character_icon_ids equals LEGACY_VALID_ICON_IDS. Change SvgRendererTest._scene_with_icons and the Character gallery exact-coverage assertions to iterate LEGACY_VALID_ICON_IDS as well. Do not let any legacy Character expected set follow the expanding KNOWN_ICONS value.

- [ ] **Step 2: Run the focused tests and confirm red**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest \
  tests.test_diagram_core_catalog \
  tests.test_render_svg.SvgRendererTest.test_character_registry_and_manifest_cover_every_known_icon \
  tests.test_render_svg.SvgRendererTest.test_illustrated_character_gallery_covers_every_known_icon_once
~~~

Expected: FAIL because schema.py cannot distinguish planned ids from unknown ids and the legacy tests still depend on KNOWN_ICONS.

- [ ] **Step 3: Implement the four-set lifecycle**

In schema.py:

~~~python
from .diagram_core.catalog import (
    LEGACY_VALID_ICON_IDS,
    approved_icon_ids,
    catalog_entry,
)

KNOWN_ICONS = set(LEGACY_VALID_ICON_IDS) | set(approved_icon_ids())

def _icon(data, key, path, issues):
    value = _string(data, key, path, issues, required=False)
    if value is None:
        return None
    if value in KNOWN_ICONS:
        return value
    if catalog_entry(value) is not None:
        issues.append(
            ValidationIssue(
                path,
                "icon is cataloged but its Diagram Core asset is not approved",
                "icon_not_implemented",
            )
        )
        return None
    issues.append(
        ValidationIssue(
            path,
            "expected one of: " + ", ".join(sorted(KNOWN_ICONS)),
            "enum",
        )
    )
    return None
~~~

The schema-sync script derives the v0.3 JSON Schema enum from KNOWN_ICONS. It supports:

~~~text
--write  update the schema file
--check  exit nonzero if the committed enum differs
~~~

At this point --check must confirm the current 13-id enum and must not add server.

- [ ] **Step 4: Run focused and full regressions**

Run:

~~~bash
PYTHONPATH=src python3 scripts/sync_diagram_script_icons.py --check
PYTHONPATH=src python3 -m unittest discover -s tests
~~~

Expected: schema sync reports icons=13 status=clean; all tests pass.

- [ ] **Step 5: Commit the lifecycle slice**

~~~bash
git add src/anidiagram/schema.py tests/test_render_svg.py tests/test_diagram_core_catalog.py scripts/sync_diagram_script_icons.py
git commit -m "feat: gate catalog icons by approval status"
~~~

## Chunk 2: Static Tokens, State Semantics, and Instancing

### Task 4: Define theme tokens and six static non-color-only states

**Files:**

- Create: assets/diagram-core/tokens.css
- Create: src/anidiagram/diagram_core/tokens.py
- Modify: tests/test_diagram_core_assets.py

- [ ] **Step 1: Write failing token and state-contract tests**

~~~python
REQUIRED_TOKENS = {
    "--icon-surface-main",
    "--icon-surface-secondary",
    "--icon-surface-recessed",
    "--icon-stroke",
    "--icon-detail",
    "--icon-accent",
    "--icon-accent-secondary",
    "--icon-status-idle",
    "--icon-status-active",
    "--icon-status-success",
    "--icon-status-warning",
    "--icon-status-error",
}

def test_token_css_defines_defaults_and_four_review_contexts(self):
    source = token_css()
    self.assertTrue(REQUIRED_TOKENS.issubset(declared_tokens(source)))
    for context in ("blue", "dark", "warm", "green"):
        self.assertIn('[data-icon-theme="' + context + '"]', source)

def test_static_state_selectors_cover_six_distinct_marks(self):
    source = token_css()
    for state in ("idle", "active", "processing", "success", "warning", "error"):
        self.assertIn('[data-icon-state="' + state + '"]', source)
        self.assertIn('[data-state-mark="' + state + '"]', source)

def test_style_mapping_uses_existing_canvas_role_and_title_tokens(self):
    style = load_style(ROOT / "styles" / "deep-tech.json")
    mapped = icon_tokens_for_style(style, "agent")
    self.assertEqual(style["canvas"]["text"], mapped["--icon-stroke"])
    self.assertEqual(style["canvas"]["muted"], mapped["--icon-detail"])
    self.assertEqual(style["roles"]["agent"]["stroke"], mapped["--icon-accent"])
~~~

- [ ] **Step 2: Run the focused tests and confirm red**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest tests.test_diagram_core_assets
~~~

Expected: FAIL because tokens.css and tokens.py do not exist.

- [ ] **Step 3: Implement token resolution and state selectors**

Use the approved default values and review contexts. The style adapter maps:

~~~text
surface-main      <- resolved role fill
surface-secondary <- canvas background
surface-recessed  <- canvas grid
stroke            <- canvas text
detail            <- canvas muted
accent            <- resolved role stroke
accent-secondary  <- title accent
status colors     <- explicit icon token override or approved defaults
~~~

tokens.css must:

- hide every data-state-mark by default;
- reveal exactly the mark matching the nearest data-icon-state;
- keep the authored idle mark visible in a standalone SVG with no external CSS;
- use shape-distinct marks: dot, ring, split arc, check, triangle, and X;
- disable transitions and animations in the review and reduced-motion modes;
- support data-icon-accent=off without removing structural boundaries or state marks.

The 3:1 check applies to the meaningful stroke or mark boundary against its adjacent surface. Status fills may supplement that boundary but cannot be the only carrier of state meaning.

- [ ] **Step 4: Test all bundled style profiles**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest tests.test_diagram_core_assets
~~~

Expected: PASS. Every bundled style produces all required icon tokens, and every benchmark review context has a structural boundary of at least 3:1.

- [ ] **Step 5: Commit the token slice**

~~~bash
git add assets/diagram-core/tokens.css src/anidiagram/diagram_core/tokens.py tests/test_diagram_core_assets.py
git commit -m "feat: define Diagram Core static state tokens"
~~~

### Task 5: Implement collision-safe instance ids and a preview-only SVG adapter

**Files:**

- Create: src/anidiagram/diagram_core/instance_ids.py
- Create: src/anidiagram/diagram_core/adapter.py
- Create: tests/test_diagram_core_adapter.py

- [ ] **Step 1: Write failing id, reference, and state tests**

~~~python
def test_safe_instance_ids_preserve_uniqueness(self):
    values = ("db.a", "db-a", "数据库 1", "db a", "DB-A")
    keys = {instance_key(value) for value in values}
    self.assertEqual(len(values), len(keys))

def test_repeated_icon_instances_have_unique_part_ids(self):
    first = render_preview_icon(
        "agent", "agent.left", state="idle", asset_root=self.fixture_root
    )
    second = render_preview_icon(
        "agent", "agent-left", state="success", asset_root=self.fixture_root
    )
    document = parse_svg_fragment(first + second)
    ids = [element.attrib["id"] for element in document.iter() if "id" in element.attrib]
    self.assertEqual(len(ids), len(set(ids)))
    self.assertTrue(
        all(identifier.count("__") == 2 for identifier in ids)
    )

def test_adapter_scopes_state_and_accessibility_to_the_instance_root(self):
    markup = render_preview_icon(
        "agent",
        "primary-agent",
        state="processing",
        size=64,
        asset_root=self.fixture_root,
    )
    root = parse_single_root(markup)
    self.assertEqual("processing", root.attrib["data-icon-state"])
    self.assertEqual("diagram-core-v1", root.attrib["data-icon-source"])
    self.assertEqual("true", root.attrib["aria-hidden"])
~~~

Also test that every local href, url fragment, aria-labelledby, and aria-describedby reference resolves inside the same instance and that two instances never select one another’s data-part elements.

Build `self.fixture_root` as a temporary, fully valid visual-review asset bundle containing catalog, manifest, SVG, and tokens. Its SVG uses minimal synthetic primitives and no copied canonical Agent path geometry. Task 5 tests the generic adapter contract; the real Agent geometry remains test-first work in Task 6.

- [ ] **Step 2: Run the focused test and confirm red**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest tests.test_diagram_core_adapter
~~~

Expected: FAIL because instance_ids.py and adapter.py do not exist.

- [ ] **Step 3: Implement a reversible collision-safe instance key**

Safe ASCII letters and digits remain readable. Encode every other Unicode code point with a length-delimited hexadecimal escape so db.a, db-a, db a, and non-ASCII ids cannot collapse onto one key. Prefix a key that would start with a digit.

~~~python
def part_dom_id(instance_id: str, icon_id: str, part_name: str) -> str:
    return "__".join(
        (
            instance_key(instance_id),
            validated_kebab_token(icon_id),
            validated_kebab_token(part_name),
        )
    )
~~~

Do not reuse the lossy legacy _fragment_id helper.

- [ ] **Step 4: Implement separate preview and approved-scene entry points**

~~~python
def render_preview_icon(
    icon_id,
    instance_id,
    state="idle",
    size=96,
    x=0,
    y=0,
    tokens=None,
    asset_root=None,
):
    return _render_icon(
        icon_id,
        instance_id,
        state,
        size,
        x,
        y,
        tokens,
        asset_root,
        allowed_statuses={"visual-review", "approved"},
    )

def render_approved_icon(
    icon_id,
    instance_id,
    state="idle",
    size=96,
    x=0,
    y=0,
    tokens=None,
    asset_root=None,
):
    return _render_icon(
        icon_id,
        instance_id,
        state,
        size,
        x,
        y,
        tokens,
        asset_root,
        allowed_statuses={"approved"},
    )
~~~

The adapter:

- parses canonical SVG rather than copying paths;
- removes the outer standalone svg only for embedded rendering;
- wraps children in a transformed g at the requested x, y, and size;
- adds one namespaced id to the root and to each public data-part;
- sets data-icon, data-icon-state, data-icon-source, and data-asset-revision;
- marks embedded icons aria-hidden=true because the node label owns the accessible name;
- injects resolved CSS custom properties on the instance root;
- leaves the canonical source unchanged.

- [ ] **Step 5: Run the adapter tests and confirm green**

Run the Step 2 command.

Expected: PASS, including repeated and Unicode instance ids.

- [ ] **Step 6: Commit the adapter slice**

~~~bash
git add src/anidiagram/diagram_core/instance_ids.py src/anidiagram/diagram_core/adapter.py tests/test_diagram_core_adapter.py
git commit -m "feat: instance Diagram Core SVG assets safely"
~~~

## Chunk 3: Agent-First Visual Checkpoint

### Task 6: Author and validate the Agent benchmark before the other icons

**Files:**

- Create: assets/diagram-core/icons/agent.svg
- Create: assets/diagram-core/manifests/agent.json
- Create: scripts/render_diagram_core_contact_sheet.py
- Create: assets/diagram-core/previews/agent-contact-sheet.svg
- Create: gallery/diagram-core/agent-review.html
- Modify: tests/test_diagram_core_assets.py
- Modify: tests/test_diagram_core_adapter.py
- Create: tests/test_diagram_core_visuals.py

- [ ] **Step 1: Write the failing Agent structure tests**

Freeze these public parts:

~~~python
AGENT_PARTS = {
    "shell",
    "face-screen",
    "eye-left",
    "eye-right",
    "mouth",
    "antenna",
    "core",
    "indicator",
}

def test_agent_asset_matches_manifest_and_visual_contract(self):
    asset = load_asset("agent", allow_statuses={"visual-review"})
    self.assertEqual(AGENT_PARTS, set(asset.manifest.parts))
    self.assertEqual(AGENT_PARTS, set(asset.public_parts))
    self.assertEqual("actor-character", asset.manifest.structural_prototype)
    self.assertEqual(
        {"enter", "receive", "process", "send"},
        set(asset.manifest.actions),
    )
    self.assertEqual(0, asset.metrics.forbidden_elements)
    self.assertLessEqual(asset.metrics.paintable_elements, 24)
~~~

Also assert the standalone root is accessible, all six state marks have distinct geometry signatures, and no port, hand, complex joint, text, or runtime effect part exists. Add machine checks that all paintable Agent geometry stays inside the 8–88 safe zone and that authored outer and inner stroke widths stay inside 2.0–2.25 px and 1.25–1.5 px respectively.

- [ ] **Step 2: Run the focused tests and confirm red**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest \
  tests.test_diagram_core_assets \
  tests.test_diagram_core_adapter \
  tests.test_diagram_core_visuals
~~~

Expected: FAIL because the Agent SVG, manifest, and review generator do not exist.

- [ ] **Step 3: Author the canonical Agent SVG and manifest**

Visual requirements:

- rounded capsule robot body;
- dark face screen;
- two simple eyes and one simple mouth;
- one short antenna;
- one chest status core;
- no floating ports, fingers, complex joints, or device sockets;
- neutral shell carries about 80 percent of the visual weight;
- theme accent and state colors remain limited to the core, indicator, or small details;
- subject stays inside the 8–88 safe zone;
- outer authored strokes are 2.0–2.25 px and inner strokes are 1.25–1.5 px on the 96 grid;
- no global non-scaling-stroke.

Use these attachment coordinates in the manifest:

~~~json
{
  "receive": {"x": 18, "y": 48},
  "send": {"x": 78, "y": 48},
  "status": {"x": 48, "y": 74}
}
~~~

All six static state shapes live inside data-part=indicator. Only the idle mark is visible when the standalone file is opened without tokens.css.

- [ ] **Step 4: Implement deterministic single-icon review generation**

The generator supports:

~~~text
--icons agent
--output assets/diagram-core/previews/agent-contact-sheet.svg
--html-output gallery/diagram-core/agent-review.html
--recognition
~~~

For Agent it renders:

~~~text
1 icon x 3 sizes x 4 contexts x 6 states = 72 cells
plus accent-off and grayscale recognition rows
~~~

The SVG output is byte-identical on repeated runs and contains no animation or network resource.

- [ ] **Step 5: Generate and validate the Agent review artifacts**

Run:

~~~bash
PYTHONPATH=src python3 scripts/render_diagram_core_contact_sheet.py \
  --icons agent \
  --output assets/diagram-core/previews/agent-contact-sheet.svg \
  --html-output gallery/diagram-core/agent-review.html \
  --recognition
PYTHONPATH=src python3 -m unittest \
  tests.test_diagram_core_assets \
  tests.test_diagram_core_adapter \
  tests.test_diagram_core_visuals
PYTHONPATH=src python3 -m unittest discover -s tests
~~~

Expected: the focused checks and the complete regression suite both pass.

~~~text
icons=1 cells=72 unique=72 sizes=48,64,96 contexts=blue,dark,warm,green states=6
OK
~~~

- [ ] **Step 6: Commit the Agent review candidate**

~~~bash
git add assets/diagram-core/icons/agent.svg assets/diagram-core/manifests/agent.json assets/diagram-core/previews/agent-contact-sheet.svg gallery/diagram-core/agent-review.html scripts/render_diagram_core_contact_sheet.py tests/test_diagram_core_assets.py tests/test_diagram_core_adapter.py tests/test_diagram_core_visuals.py
git commit -m "feat: add Agent static icon benchmark"
~~~

### Checkpoint A: Human Agent approval

- [ ] Open gallery/diagram-core/agent-review.html through a local static server and show assets/diagram-core/previews/agent-contact-sheet.svg to the user.
- [ ] Ask the user to judge 48 px recognition, silhouette, visual weight, face readability, accent-off recognition, all four contexts, and all six state marks.
- [ ] If rejected, revise the Agent SVG, its manifest, tokens, adapter or generator as required by the observed defect, then regenerate all Agent artifacts, rerun the complete Task 6 validation, and present the new digest. Do not modify unrelated runtime or renderer behavior.
- [ ] If approved, record reviewer coolbat, approval date, the Agent SVG SHA-256, manifest SHA-256, token SHA-256, and the exact reviewed artifact path in docs/diagram-core-phase-1-approval.md.
- [ ] Keep Agent status at visual-review; this checkpoint authorizes family expansion, not public DiagramScript promotion.
- [ ] Commit the durable decision:

~~~bash
git add docs/diagram-core-phase-1-approval.md
git commit -m "docs: record Agent static icon approval"
~~~

## Chunk 4: Complete and Validate the Four Static Benchmarks

### Task 7: Author Database, API, and Server from the approved Agent family baseline

**Files:**

- Create: assets/diagram-core/icons/database.svg
- Create: assets/diagram-core/icons/api.svg
- Create: assets/diagram-core/icons/server.svg
- Create: assets/diagram-core/manifests/database.json
- Create: assets/diagram-core/manifests/api.json
- Create: assets/diagram-core/manifests/server.json
- Modify: tests/test_diagram_core_assets.py
- Modify: tests/test_diagram_core_adapter.py

- [ ] **Step 1: Write failing asset-specific structure tests**

Freeze the public parts:

~~~python
EXPECTED_BENCHMARK_PARTS = {
    "agent": {
        "shell", "face-screen", "eye-left", "eye-right",
        "mouth", "antenna", "core", "indicator",
    },
    "database": {
        "shell", "top-ring", "layer-top", "layer-middle",
        "layer-bottom", "core", "indicator",
    },
    "api": {
        "shell", "header", "input-interface",
        "output-interface", "processor", "indicator-group",
    },
    "server": {
        "shell", "tray-top", "tray-bottom", "indicator-top",
        "indicator-bottom", "vent-top", "vent-bottom", "base",
    },
}

def test_benchmark_assets_have_exact_public_parts(self):
    for icon_id, expected in EXPECTED_BENCHMARK_PARTS.items():
        with self.subTest(icon_id=icon_id):
            asset = load_asset(icon_id, allow_statuses={"visual-review"})
            self.assertEqual(expected, set(asset.manifest.parts))
            self.assertEqual(expected, set(asset.public_parts))
~~~

Add tests for exact structural prototypes, action sets, attachment keys, six state marks, paintable-element budget, file-size budget, safe standalone rendering, and absence of floating ports on Agent, Database, and Server.

- [ ] **Step 2: Run focused tests and confirm red**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest \
  tests.test_diagram_core_assets \
  tests.test_diagram_core_adapter
~~~

Expected: FAIL because the three new SVG/manifest pairs do not exist.

- [ ] **Step 3: Author Database**

Visual contract:

- three simplified cylindrical layers;
- one top scan ring;
- one central state core;
- no repeated interface lights on every layer;
- no floating port;
- family stroke, corner, surface, state, and detail weights match Agent.

Manifest:

~~~text
prototype: stacked-storage
actions: receive, write, index, search, send
attachments:
  receive = 48,8
  send    = 88,48
  status  = 48,76
~~~

- [ ] **Step 4: Author API**

Visual contract:

- one interface card or compact module;
- short input and output structures physically attached to the body;
- one central processor;
- one top indicator group;
- no permanent direction arrow;
- no claim that left always means request or right always means response;
- interface parts are visual affordances, not scene connection anchors.

Manifest:

~~~text
prototype: interface-module
actions: receive, process, send, stream
attachments:
  receive = 8,48
  send    = 88,48
  status  = 48,22
~~~

- [ ] **Step 5: Author Server**

Visual contract:

- two simplified server trays;
- one indicator and a small vent group per tray;
- one lightweight base;
- no disk array, realistic fan, waveform screen, floating port, or complex rack detail;
- visual weight matches Agent, Database, and API at 48 px.

Manifest:

~~~text
prototype: compute-device
actions: enter, receive, process, send
attachments:
  receive = 8,36
  send    = 88,60
  status  = 76,24
~~~

- [ ] **Step 6: Run the focused tests and compare structural metrics**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest \
  tests.test_diagram_core_assets \
  tests.test_diagram_core_adapter
~~~

Expected: PASS. The four paintable counts, raw sizes, and gzip sizes are reported side by side and all remain within the approved limits without exceptions.

- [ ] **Step 7: Commit the three-asset slice**

~~~bash
git add assets/diagram-core/icons/database.svg assets/diagram-core/icons/api.svg assets/diagram-core/icons/server.svg assets/diagram-core/manifests/database.json assets/diagram-core/manifests/api.json assets/diagram-core/manifests/server.json tests/test_diagram_core_assets.py tests/test_diagram_core_adapter.py
git commit -m "feat: add Diagram Core static benchmarks"
~~~

### Task 8: Add strict asset and repeated-instance command-line validators

**Files:**

- Create: scripts/validate_diagram_core_assets.py
- Create: scripts/check_diagram_core_parts.py
- Modify: tests/test_diagram_core_assets.py
- Modify: tests/test_diagram_core_adapter.py

- [ ] **Step 1: Write failing CLI-result tests**

~~~python
def test_asset_validator_review_mode_reports_clean_four_icon_set(self):
    result = run_asset_validator("--review", "--json")
    self.assertEqual(0, result.returncode)
    report = json.loads(result.stdout)
    self.assertEqual(56, report["catalog"])
    self.assertEqual(13, report["legacy_valid"])
    self.assertEqual(4, report["visual_review"])
    self.assertEqual(4, report["svg"])
    self.assertEqual(4, report["manifests"])
    self.assertEqual(0, report["errors"])

def test_part_checker_proves_two_instances_per_icon(self):
    result = run_part_checker(
        "--icons", "agent,database,api,server",
        "--instances", "2",
        "--json",
    )
    self.assertEqual(0, result.returncode)
    report = json.loads(result.stdout)
    self.assertEqual(8, report["instances"])
    self.assertEqual(0, report["duplicate_ids"])
    self.assertEqual(0, report["unresolved_refs"])
    self.assertEqual(0, report["missing_parts"])
~~~

Also prove:

- --strict fails while the four assets remain visual-review;
- malformed catalog, manifest, SVG, token, attachment, exception, or reference fixtures return a nonzero exit;
- human-readable and JSON output contain the same counts.

- [ ] **Step 2: Run focused tests and confirm red**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest \
  tests.test_diagram_core_assets \
  tests.test_diagram_core_adapter
~~~

Expected: FAIL because the scripts do not exist.

- [ ] **Step 3: Implement the validators as thin library clients**

Do not duplicate validation logic in scripts. They call catalog.py, manifest.py, asset_loader.py, tokens.py, and adapter.py and serialize one report.

The asset report includes:

~~~text
catalog
legacy_valid
approved
visual_review
planned
svg
manifests
paintable_elements_by_icon
raw_bytes_by_icon
gzip_bytes_by_icon
contrast_checks
errors
warnings
~~~

Review mode accepts the exact four benchmark assets in visual-review. Strict mode requires those same four to be approved and is reserved for the post-approval gate.

- [ ] **Step 4: Run the review validators**

Run:

~~~bash
PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --review
PYTHONPATH=src python3 scripts/check_diagram_core_parts.py \
  --icons agent,database,api,server \
  --instances 2
~~~

Expected:

~~~text
catalog=56 legacy_valid=13 approved=0 visual_review=4 svg=4 manifests=4 errors=0 warnings=0
icons=4 instances=8 duplicate_ids=0 unresolved_refs=0 missing_parts=0
~~~

- [ ] **Step 5: Commit the validation CLI slice**

~~~bash
git add scripts/validate_diagram_core_assets.py scripts/check_diagram_core_parts.py tests/test_diagram_core_assets.py tests/test_diagram_core_adapter.py
git commit -m "test: enforce Diagram Core asset quality"
~~~

### Task 9: Generate the complete 288-cell matrix and static review pages

**Files:**

- Modify: scripts/render_diagram_core_contact_sheet.py
- Create: assets/diagram-core/previews/benchmark-contact-sheet.svg
- Create: gallery/diagram-core/index.html
- Create: gallery/diagram-core/recognition.html
- Create: gallery/diagram-core/cell-index.json
- Modify: tests/test_diagram_core_visuals.py

- [ ] **Step 1: Write failing Cartesian-product and determinism tests**

~~~python
ICONS = ("agent", "database", "api", "server")
SIZES = (48, 64, 96)
CONTEXTS = ("blue", "dark", "warm", "green")
STATES = ("idle", "active", "processing", "success", "warning", "error")

def test_contact_sheet_is_exact_288_cell_product(self):
    cells = build_contact_sheet_cells()
    expected = set(itertools.product(ICONS, SIZES, CONTEXTS, STATES))
    actual = {
        (cell.icon_id, cell.size, cell.context, cell.state)
        for cell in cells
    }
    self.assertEqual(expected, actual)
    self.assertEqual(288, len(cells))

def test_contact_sheet_generation_is_byte_deterministic(self):
    first = render_contact_sheet()
    second = render_contact_sheet()
    self.assertEqual(first, second)

def test_every_state_has_distinct_static_geometry(self):
    for icon_id in ICONS:
        signatures = {
            state: state_mark_signature(icon_id, state)
            for state in STATES
        }
        self.assertEqual(6, len(set(signatures.values())), icon_id)
~~~

Also assert:

- every generated instance id is globally unique;
- the recognition page hides all visible labels in the icon review region;
- accent-off and grayscale views retain all four silhouettes and six shapes;
- output contains no animation, transition, network URL, or runtime script;
- cell-index.json ordering is deterministic and matches the visual DOM order.

- [ ] **Step 2: Run focused tests and confirm red**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest tests.test_diagram_core_visuals
~~~

Expected: FAIL because the generator only supports the Agent checkpoint.

- [ ] **Step 3: Expand the generator without coupling it to the existing showcase builder**

Use a 12-column by 24-row matrix:

~~~text
columns = 4 icons x 3 sizes
rows    = 4 contexts x 6 states
cells   = 12 x 24 = 288
~~~

The regression crop contains no visible text, so font rasterization cannot affect icon pixels. The labeled index and row/column legends live outside that crop on index.html.

recognition.html adds:

- 48 px label-hidden silhouette row;
- accent-off row;
- grayscale row;
- four-icon same-node-context row for visual-weight comparison.

- [ ] **Step 4: Generate and verify committed review surfaces**

Run:

~~~bash
PYTHONPATH=src python3 scripts/render_diagram_core_contact_sheet.py \
  --icons agent,database,api,server \
  --output assets/diagram-core/previews/benchmark-contact-sheet.svg \
  --html-output gallery/diagram-core/index.html \
  --recognition-output gallery/diagram-core/recognition.html \
  --cell-index gallery/diagram-core/cell-index.json
PYTHONPATH=src python3 -m unittest tests.test_diagram_core_visuals
~~~

Expected:

~~~text
icons=4 cells=288 unique=288 sizes=48,64,96 contexts=blue,dark,warm,green states=6
OK
~~~

- [ ] **Step 5: Commit deterministic review artifacts**

~~~bash
git add scripts/render_diagram_core_contact_sheet.py assets/diagram-core/previews/benchmark-contact-sheet.svg gallery/diagram-core/index.html gallery/diagram-core/recognition.html gallery/diagram-core/cell-index.json tests/test_diagram_core_visuals.py
git commit -m "feat: build Diagram Core static review matrix"
~~~

## Chunk 5: Locked Visual Regression and Human Promotion Gate

### Task 10: Add a real browser pixel-diff gate

**Files:**

- Create: package.json
- Create: package-lock.json
- Create: scripts/capture_diagram_core_contact_sheet.mjs
- Create: scripts/compare_diagram_core_contact_sheet.py
- Modify: tests/test_diagram_core_visuals.py

- [ ] **Step 1: Write failing comparator and capture-contract tests**

Use synthetic Pillow images to freeze comparison behavior:

~~~python
def test_pixel_diff_uses_channel_tolerance_eight_and_ratio_one_percent(self):
    baseline = solid_image((100, 100), (240, 240, 240, 255))
    candidate = baseline.copy()
    change_square(candidate, x=0, y=0, width=10, height=10, delta=9)
    report = compare_images(
        baseline,
        candidate,
        channel_tolerance=8,
        max_diff_ratio=0.01,
    )
    self.assertEqual(100, report.differing_pixels)
    self.assertEqual(0.01, report.diff_ratio)
    self.assertTrue(report.passed)

def test_dimension_mismatch_fails_before_pixel_comparison(self):
    with self.assertRaisesRegex(VisualComparisonError, "dimensions"):
        compare_images(
            solid_image((100, 100), (0, 0, 0, 255)),
            solid_image((101, 100), (0, 0, 0, 255)),
        )
~~~

Source tests for the capture script assert:

- browser is Playwright Chromium from package-lock.json;
- deviceScaleFactor is 1;
- reduced motion is reduce;
- viewport and locator are fixed;
- animation and transition are disabled;
- document.fonts.ready and two animation frames complete before capture;
- no network request is permitted;
- the captured locator is #diagram-core-regression-grid.

- [ ] **Step 2: Run the focused tests and confirm red**

Run:

~~~bash
python3 -m pip install -e ".[raster]"
PYTHONPATH=src python3 -m unittest tests.test_diagram_core_visuals
~~~

Expected: FAIL because capture and comparison tools do not exist.

- [ ] **Step 3: Pin Playwright and its Chromium build**

Create this private tooling manifest first:

~~~json
{
  "name": "anidiagram-visual-tests",
  "private": true,
  "scripts": {
    "capture:diagram-core": "node scripts/capture_diagram_core_contact_sheet.mjs"
  },
  "devDependencies": {}
}
~~~

Then run once:

~~~bash
npm install --save-dev --save-exact playwright
npx playwright install chromium
~~~

Commit both package.json and package-lock.json. Future local and CI runs use npm ci, never an unpinned global browser package.

- [ ] **Step 4: Implement deterministic capture**

The capture script accepts:

~~~text
--input gallery/diagram-core/index.html
--output build/diagram-core/benchmark.chromium-linux.png
--metadata build/diagram-core/benchmark.chromium-linux.capture.json
~~~

It records:

- exact Playwright and Chromium versions;
- operating system and architecture;
- viewport 1280 x 900;
- device scale factor 1;
- locator bounding box;
- source asset joint SHA-256;
- capture timestamp;
- zero external requests;
- zero animations and transitions.

It screenshots only #diagram-core-regression-grid, whose dimensions and cells are fixed by the generator.

- [ ] **Step 5: Implement comparison and approval modes**

Normal compare:

~~~bash
PYTHONPATH=src python3 scripts/compare_diagram_core_contact_sheet.py \
  --baseline assets/diagram-core/previews/baselines/benchmark.chromium-linux.png \
  --baseline-metadata assets/diagram-core/previews/baselines/benchmark.chromium-linux.json \
  --candidate build/diagram-core/benchmark.chromium-linux.png \
  --candidate-metadata build/diagram-core/benchmark.chromium-linux.capture.json \
  --max-diff-ratio 0.01 \
  --channel-tolerance 8 \
  --diff-output build/diagram-core/benchmark.diff.png
~~~

Rules:

- dimensions must match;
- a pixel differs when any RGBA channel differs by more than 8;
- at most 1 percent of pixels may differ;
- asset digest and locked Chromium version must match the approved metadata;
- failure writes a heatmap and exits nonzero;
- normal compare cannot update a baseline.

Approval mode is a separate explicit command and requires a nonempty reviewer and note. It copies the candidate and writes approval metadata; it never runs automatically in tests or CI.

- [ ] **Step 6: Run unit tests and one unapproved capture**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest tests.test_diagram_core_visuals
node scripts/capture_diagram_core_contact_sheet.mjs \
  --input gallery/diagram-core/index.html \
  --output build/diagram-core/benchmark.local.png \
  --metadata build/diagram-core/benchmark.local.capture.json
~~~

Expected: tests pass and the capture command reports cells=288, dpr=1, requests=0, animations=0. Do not create the committed baseline yet.

- [ ] **Step 7: Commit visual tooling without an approved baseline**

~~~bash
git add package.json package-lock.json scripts/capture_diagram_core_contact_sheet.mjs scripts/compare_diagram_core_contact_sheet.py tests/test_diagram_core_visuals.py
git commit -m "test: add locked Diagram Core visual regression"
~~~

### Checkpoint B: Final static visual approval and lifecycle promotion

- [ ] Serve gallery/diagram-core/index.html and gallery/diagram-core/recognition.html locally and show both pages plus assets/diagram-core/previews/benchmark-contact-sheet.svg to the user.
- [ ] Review all 288 cells, 48 px label-hidden recognition, accent-off, grayscale, four-context readability, visual-weight consistency, API attached interfaces, non-port rules, and six distinct state shapes.
- [ ] If rejected, change only canonical SVG, manifest, token, adapter, or generator inputs; regenerate all artifacts, rerun review validators, and present the new joint digest. Do not promote statuses.
- [ ] After explicit visual approval, change exactly agent, database, api, and server to approved in catalog.json and the four manifests. Do not promote any other id, and do not commit yet.
- [ ] Regenerate the contact sheet after status promotion so the candidate metadata is computed from the final approved catalog/manifests rather than the earlier visual-review digest.
- [ ] Capture the normative Linux candidate using the Playwright version locked in package-lock.json. On a non-Linux host, run:

~~~bash
npm ci
PW_VERSION=$(node -p "require('playwright/package.json').version")
mkdir -p build/diagram-core
docker run --rm --ipc=host \
  --user "$(id -u):$(id -g)" \
  --env HOME=/tmp \
  --volume "$PWD:/work" \
  --workdir /work \
  "mcr.microsoft.com/playwright:v$PW_VERSION-noble" \
  node scripts/capture_diagram_core_contact_sheet.mjs \
    --input gallery/diagram-core/index.html \
    --output build/diagram-core/benchmark.chromium-linux.png \
    --metadata build/diagram-core/benchmark.chromium-linux.capture.json
~~~

- [ ] Show the exact Linux PNG and capture metadata to the user. Record a second explicit confirmation of that candidate digest; if it differs visually from the approved review surface, revise, regenerate, and repeat before accepting a baseline.
- [ ] Accept the exact approved candidate:

~~~bash
PYTHONPATH=src python3 scripts/compare_diagram_core_contact_sheet.py \
  --accept \
  --reviewer coolbat \
  --approval-note "Diagram Core v1 Phase 1 static benchmark approved" \
  --candidate build/diagram-core/benchmark.chromium-linux.png \
  --candidate-metadata build/diagram-core/benchmark.chromium-linux.capture.json \
  --baseline assets/diagram-core/previews/baselines/benchmark.chromium-linux.png \
  --baseline-metadata assets/diagram-core/previews/baselines/benchmark.chromium-linux.json
~~~

- [ ] Add the final approval date, reviewer, four SVG digests, four manifest digests, tokens digest, baseline digest, Chromium version, and artifact links to docs/diagram-core-phase-1-approval.md.
- [ ] Add an acceptance test requiring APPROVED_DIAGRAM_CORE_IDS to equal the four benchmark ids.
- [ ] Run:

~~~bash
PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --strict
PYTHONPATH=src python3 scripts/sync_diagram_script_icons.py --write
PYTHONPATH=src python3 scripts/sync_diagram_script_icons.py --check
PYTHONPATH=src python3 -m unittest discover -s tests
~~~

Expected:

~~~text
catalog=56 legacy_valid=13 approved=4 visual_review=0 svg=4 manifests=4 errors=0 warnings=0
icons=14 status=clean
OK
~~~

- [ ] Commit the approval atomically:

~~~bash
git add assets/diagram-core/catalog.json assets/diagram-core/manifests assets/diagram-core/previews/baselines schemas/diagram-script-v0.3.schema.json docs/diagram-core-phase-1-approval.md tests/test_diagram_core_catalog.py
git commit -m "feat: approve Diagram Core static benchmarks"
~~~

Do not continue to Task 11 until this checkpoint is approved and committed.

## Chunk 6: Approved Static Renderer Integration

### Task 11: Integrate approved assets without switching the default or starting motion

**Files:**

- Modify: src/anidiagram/icon_system.py
- Modify: src/anidiagram/styles.py
- Modify: schemas/style-profile-v0.1.schema.json
- Modify: src/anidiagram/renderer_svg.py
- Modify: src/anidiagram/motion_manifest.py
- Modify: src/anidiagram/quality.py
- Modify: tests/test_render_svg.py
- Modify: tests/test_diagram_core_adapter.py

- [ ] **Step 1: Write failing routing, fallback, and motion-boundary tests**

~~~python
def test_diagram_core_is_explicit_and_default_remains_legacy(self):
    self.assertEqual("illustrated-character-v1", DEFAULT_ICON_SYSTEM)
    self.assertIn("diagram-core-v1", SUPPORTED_ICON_SYSTEMS)

def test_explicit_diagram_core_renders_all_four_canonical_assets(self):
    style = deep_merge(load_style(), {"icon_system": "diagram-core-v1"})
    for icon_id in ("agent", "database", "api", "server"):
        with self.subTest(icon_id=icon_id):
            svg = render_svg(scene_with_icon(icon_id), style)
            self.assertIn('data-icon-source="diagram-core-v1"', svg)
            self.assertIn("__" + icon_id + "__root", svg)

def test_explicit_diagram_core_uses_named_legacy_fallback_once(self):
    style = deep_merge(load_style(), {"icon_system": "diagram-core-v1"})
    scene = scene_with_repeated_icon("cloud", count=2)
    svg = render_svg(scene, style)
    report = quality_report(scene, style)
    warnings = [
        issue for issue in report["issues"]
        if issue["code"] == "diagram_core_icon_fallback"
    ]
    self.assertEqual(1, len(warnings))
    self.assertIn('data-icon-source="legacy:illustrated-character-v1"', svg)

def test_diagram_core_phase_one_has_no_icon_performances(self):
    style = deep_merge(load_style(), {"icon_system": "diagram-core-v1"})
    manifest = build_motion_manifest(scene_with_icon("agent"), style)
    self.assertEqual("diagram-core-v1", manifest["icon_system"])
    self.assertEqual([], manifest["icons"])
~~~

Add a server test under the unchanged default style. Since server has no legacy implementation but is now valid, it must render its approved Diagram Core asset rather than a generic box. Existing legacy ids continue using their selected old renderer unless diagram-core-v1 is explicitly requested.

- [ ] **Step 2: Run focused tests and confirm red**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest \
  tests.test_diagram_core_adapter \
  tests.test_render_svg.SvgRendererTest.test_default_icon_system_is_illustrated_character_v1
~~~

Expected: new tests fail because the system id, explicit renderer branch, fallback warning, and motion guard are absent.

- [ ] **Step 3: Add the explicit style-system id**

Add diagram-core-v1 to SUPPORTED_ICON_SYSTEMS. Keep DEFAULT_ICON_SYSTEM unchanged.

Add icon_system enum support to both the top level and legacy effects.icon_system in schemas/style-profile-v0.1.schema.json so the published schema matches Python validation.

- [ ] **Step 4: Implement deliberate renderer routing**

Route in this order:

~~~text
1. approved Diagram Core asset and explicit diagram-core-v1
   -> canonical adapter
2. approved Diagram Core asset with no legacy implementation
   -> canonical adapter regardless of selected legacy system
3. explicit diagram-core-v1 for a legacy-valid but unmigrated icon
   -> illustrated-character-v1 renderer plus explicit source marker
4. explicit legacy system for a legacy-valid icon
   -> existing renderer unchanged
5. planned or visual-review catalog icon
   -> already blocked by DiagramScript validation
6. truly unknown icon
   -> already blocked by DiagramScript validation
~~~

Never rely on the current accidental fall-through to semantic-line or the generic square.

Diagram Core node rendering:

- uses the existing node box and text layout ownership;
- passes the static state idle from DiagramScript scenes; adding a node-state field is reserved for the Phase 2 contract;
- renders 48–64 px in normal nodes and may use up to 96 px only where the node has room;
- keeps node anchors and edge routes unchanged;
- embeds tokens.css once in the scene;
- applies per-role mapped variables on each instance;
- uses class diagram-core-icon, not semantic-icon, so the legacy global non-scaling-stroke rule cannot affect canonical assets.

- [ ] **Step 5: Add one high-signal fallback warning**

For explicit diagram-core-v1, deduplicate fallback warnings by icon id. The issue path points to the first use and the message includes the number of affected nodes.

Approved canonical icons produce no fallback warning. A catalog/manifest mismatch remains a hard asset-validation error, not a runtime fallback.

- [ ] **Step 6: Suppress Phase 1 icon performances**

In icon_performance_for_node:

~~~python
if icon_system in {"illustrated-character-v2", "diagram-core-v1"}:
    return None
~~~

This guard prevents old v2 performance ids from targeting new canonical parts. Do not compile Icon Asset Manifests into the Scene Motion Manifest in this task; that belongs to Phase 2.

- [ ] **Step 7: Run focused and full tests**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest \
  tests.test_diagram_core_adapter \
  tests.test_render_svg
PYTHONPATH=src python3 -m unittest discover -s tests
~~~

Expected: all tests pass; default Character examples and galleries remain unchanged; explicit Diagram Core renders four canonical assets; server never renders a generic square.

- [ ] **Step 8: Commit the static integration**

~~~bash
git add src/anidiagram/icon_system.py src/anidiagram/styles.py schemas/style-profile-v0.1.schema.json src/anidiagram/renderer_svg.py src/anidiagram/motion_manifest.py src/anidiagram/quality.py tests/test_render_svg.py tests/test_diagram_core_adapter.py
git commit -m "feat: integrate approved Diagram Core assets"
~~~

### Task 12: Package the canonical assets and prove installed-package loading

**Files:**

- Modify: pyproject.toml
- Modify: src/anidiagram/diagram_core/asset_loader.py
- Modify: tests/test_diagram_core_assets.py

- [ ] **Step 1: Write a failing wheel-content smoke test**

The test builds a wheel without network isolation, inspects it, installs it into a temporary virtual environment, changes outside the repository, and loads all four assets:

~~~python
def test_wheel_contains_and_loads_canonical_assets(self):
    wheel = build_local_wheel()
    names = wheel_member_names(wheel)
    for icon_id in ("agent", "database", "api", "server"):
        self.assertTrue(
            any(name.endswith("/share/anidiagram/diagram-core/icons/" + icon_id + ".svg") for name in names)
        )
        self.assertTrue(
            any(name.endswith("/share/anidiagram/diagram-core/manifests/" + icon_id + ".json") for name in names)
        )
    self.assert_installed_asset_loads(wheel, "server")
~~~

- [ ] **Step 2: Run the focused test and confirm red**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest \
  tests.test_diagram_core_assets.DiagramCoreAssetTest.test_wheel_contains_and_loads_canonical_assets
~~~

Expected: FAIL because root-level assets are not included in the wheel.

- [ ] **Step 3: Configure generated wheel data without a source mirror**

Use setuptools data-files to package the existing root-level source directly under:

~~~text
share/anidiagram/diagram-core/catalog.json
share/anidiagram/diagram-core/tokens.css
share/anidiagram/diagram-core/icons
share/anidiagram/diagram-core/manifests
~~~

The loader lookup order is:

~~~text
1. explicit asset_root argument
2. source checkout root assets/diagram-core
3. sysconfig data path share/anidiagram/diagram-core
~~~

If no valid root exists, raise DiagramCoreAssetNotFound with every checked path. Do not fall back to embedded Python strings or a second package copy.

- [ ] **Step 4: Build and test the installed wheel**

Run:

~~~bash
rm -rf build/diagram-core-wheel
python3 -m pip wheel . \
  --no-deps \
  --no-build-isolation \
  --wheel-dir build/diagram-core-wheel
PYTHONPATH=src python3 -m unittest \
  tests.test_diagram_core_assets.DiagramCoreAssetTest.test_wheel_contains_and_loads_canonical_assets
~~~

Expected: PASS. The temporary installed package loads catalog, tokens, all four manifests, and all four SVG files while its current directory is outside the repository.

- [ ] **Step 5: Commit packaging support**

~~~bash
git add pyproject.toml src/anidiagram/diagram_core/asset_loader.py tests/test_diagram_core_assets.py
git commit -m "build: package Diagram Core canonical assets"
~~~

## Chunk 7: Documentation, CI, and Phase 1 Handoff

### Task 13: Document the static contract, automate gates, and close Phase 1

**Files:**

- Modify: docs/diagram-script.md
- Modify: docs/html-runtime.md
- Modify: docs/diagram-core-phase-1-approval.md
- Modify: .github/workflows/test.yml
- Modify: tests/test_diagram_core_catalog.py
- Modify: tests/test_diagram_core_visuals.py

- [ ] **Step 1: Write failing documentation and workflow contract tests**

Assert:

- docs/diagram-script.md names diagram-core-v1, all four approved assets, server, icon_not_implemented, the unchanged default, and explicit legacy fallback;
- docs/html-runtime.md states Phase 1 Diagram Core has zero icon performances and static output is complete;
- the approval record links all canonical files, both review pages, the baseline, and the exact Phase 2 boundary;
- README and README.zh-CN still advertise the existing default and were not rewritten for Diagram Core;
- the workflow runs unittest, schema sync --check, strict asset validation, part checking, deterministic regeneration --check, npm ci, Playwright Chromium install, capture, and one-percent compare;
- the visual job cannot continue on missing browser or baseline.

- [ ] **Step 2: Run focused tests and confirm red**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest \
  tests.test_diagram_core_catalog \
  tests.test_diagram_core_visuals
~~~

Expected: FAIL because documentation and CI gates are incomplete.

- [ ] **Step 3: Document user-facing Phase 1 behavior**

docs/diagram-script.md covers:

- 56 cataloged ids versus 14 currently valid ids;
- the exact approved set agent, database, api, server;
- icon_not_implemented for cataloged but unapproved ids;
- diagram-core-v1 as an explicit opt-in;
- illustrated-character-v1 as the unchanged default;
- server’s canonical-only route;
- explicit fallback warnings for unmigrated legacy ids.

docs/html-runtime.md covers:

- canonical data-part and instance-key__icon-id__part-name ids;
- tokens and static state behavior;
- zero Diagram Core icon performances in Phase 1;
- no runtime asset-manifest compilation until Phase 2;
- static SVG completeness if JavaScript or GSAP is absent.

Do not change README examples or the public default claim before Phase 3.

- [ ] **Step 4: Complete the durable approval and handoff record**

docs/diagram-core-phase-1-approval.md contains:

- approved public name and system id;
- Agent checkpoint and final checkpoint dates;
- reviewer coolbat;
- joint and per-file SHA-256 values;
- exact Playwright and Chromium versions;
- viewport, device scale factor, channel tolerance 8, and max diff ratio 0.01;
- links to the 288-cell sheet, recognition page, PNG baseline, and metadata;
- approved public parts, actions, and attachments for all four icons;
- explicit statement that no Performance, Runtime adapter, React component, or remaining icon was implemented;
- Phase 2 inputs are the approved manifests and canonical SVG parts, not copied prose.

- [ ] **Step 5: Add CI structural and visual gates**

The Python job:

~~~bash
python3 -m pip install -e ".[raster]"
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 scripts/sync_diagram_script_icons.py --check
PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --strict
PYTHONPATH=src python3 scripts/check_diagram_core_parts.py --icons agent,database,api,server --instances 2
PYTHONPATH=src python3 scripts/render_diagram_core_contact_sheet.py --check
~~~

The visual job:

~~~bash
npm ci
npx playwright install --with-deps chromium
PYTHONPATH=src python3 scripts/render_diagram_core_contact_sheet.py --check
node scripts/capture_diagram_core_contact_sheet.mjs \
  --input gallery/diagram-core/index.html \
  --output build/diagram-core/benchmark.chromium-linux.png \
  --metadata build/diagram-core/benchmark.chromium-linux.capture.json
PYTHONPATH=src python3 scripts/compare_diagram_core_contact_sheet.py \
  --baseline assets/diagram-core/previews/baselines/benchmark.chromium-linux.png \
  --baseline-metadata assets/diagram-core/previews/baselines/benchmark.chromium-linux.json \
  --candidate build/diagram-core/benchmark.chromium-linux.png \
  --candidate-metadata build/diagram-core/benchmark.chromium-linux.capture.json \
  --max-diff-ratio 0.01 \
  --channel-tolerance 8 \
  --diff-output build/diagram-core/benchmark.diff.png
~~~

Upload the candidate, metadata, and diff heatmap on failure.

- [ ] **Step 6: Run the complete local acceptance matrix**

Run:

~~~bash
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 scripts/sync_diagram_script_icons.py --check
PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --strict
PYTHONPATH=src python3 scripts/check_diagram_core_parts.py \
  --icons agent,database,api,server \
  --instances 2
PYTHONPATH=src python3 scripts/render_diagram_core_contact_sheet.py --check
npm ci
npx playwright install chromium
node scripts/capture_diagram_core_contact_sheet.mjs \
  --input gallery/diagram-core/index.html \
  --output build/diagram-core/benchmark.chromium-linux.png \
  --metadata build/diagram-core/benchmark.chromium-linux.capture.json
PYTHONPATH=src python3 scripts/compare_diagram_core_contact_sheet.py \
  --baseline assets/diagram-core/previews/baselines/benchmark.chromium-linux.png \
  --baseline-metadata assets/diagram-core/previews/baselines/benchmark.chromium-linux.json \
  --candidate build/diagram-core/benchmark.chromium-linux.png \
  --candidate-metadata build/diagram-core/benchmark.chromium-linux.capture.json \
  --max-diff-ratio 0.01 \
  --channel-tolerance 8 \
  --diff-output build/diagram-core/benchmark.diff.png
python3 -m pip wheel . \
  --no-deps \
  --no-build-isolation \
  --wheel-dir build/diagram-core-wheel
~~~

Expected:

~~~text
unittest: OK
schema: icons=14 status=clean
assets: catalog=56 legacy_valid=13 approved=4 svg=4 manifests=4 errors=0 warnings=0
parts: icons=4 instances=8 duplicate_ids=0 unresolved_refs=0 missing_parts=0
contact sheet: cells=288 unique=288 status=clean
visual diff: ratio<=0.01 channel_tolerance=8 status=pass
wheel: built and installed-asset smoke test passed
~~~

- [ ] **Step 7: Review the final diff and scope**

Run:

~~~bash
git status --short
git diff --check
git diff --stat
rg -n "TO[D]O|T[B]D|place[Hh]older" \
  assets/diagram-core \
  src/anidiagram/diagram_core \
  docs/diagram-core-phase-1-approval.md
test ! -e runtime/diagram-core-performances.js
test -z "$(find . -path './node_modules' -prune -o -path './build' -prune -o -name '*.tsx' -print)"
~~~

Expected:

- no whitespace errors;
- no unresolved markers;
- no runtime performance file;
- no React source;
- no fifth canonical icon;
- build outputs remain ignored;
- README default examples remain unchanged.

- [ ] **Step 8: Commit Phase 1 closure**

~~~bash
git add docs/diagram-script.md docs/html-runtime.md docs/diagram-core-phase-1-approval.md .github/workflows/test.yml tests/test_diagram_core_catalog.py tests/test_diagram_core_visuals.py
git commit -m "docs: close Diagram Core static benchmark phase"
~~~

## Final Stop Condition

Stop after Task 13 when all automated checks pass and both human checkpoints are recorded. Report:

- branch and final commit;
- catalog, legacy-valid, approved, and DiagramScript-valid counts;
- four canonical SVG and manifest paths;
- contact-sheet, recognition, baseline, metadata, and approval-record paths;
- exact test, validator, visual-diff, and wheel results;
- confirmation that the default remains illustrated-character-v1;
- confirmation that Phase 2 motion, React, and the remaining 52 SVG assets were not started.

Wait for a separate explicit instruction before implementing Phase 2.

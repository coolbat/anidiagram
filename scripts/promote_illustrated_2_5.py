#!/usr/bin/env python3
"""Promote the approved Illustrated 2.5 review artifacts to a public release."""

from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anidiagram.illustrated_convention_alignment_review import (  # noqa: E402
    convention_alignment_icon_ids,
)
from anidiagram.illustrated_public_motion import (  # noqa: E402
    ILLUSTRATED_PUBLIC_ICON_PERFORMANCES,
    ILLUSTRATED_PUBLIC_MOTION_SPECS,
    ILLUSTRATED_PUBLIC_REST_AT,
)
from anidiagram.illustrated_registry import illustrated_definition, illustrated_icon_ids  # noqa: E402
from scripts.render_illustrated_release_preview import render_svg as render_release_preview  # noqa: E402


APPROVED_AT = "2026-07-24"
PUBLIC_CONTRACT = "illustrated-performance-v6"
REVIEW_CONTRACTS = ("illustrated-performance-v6-review", "illustrated-performance-v7-review")
CONVENTION_IDS = set(convention_alignment_icon_ids())
VALIDATION_RECORD = "assets/illustrated/reviews/2.5.0-validation.json"

ROLES = {
    "agent": "agent", "operator": "actor", "tool": "tool", "output": "output", "database": "memory",
    "api": "process", "search": "tool", "memory": "memory", "file": "source", "folder": "source",
    "cloud": "source", "shield": "risk", "user": "actor", "server": "process", "ai-model": "agent",
    "message-queue": "process", "vector-database": "memory", "knowledge-base": "memory", "gateway": "process",
    "container": "process", "developer": "actor", "agent-team": "agent", "assistant": "agent",
    "human-reviewer": "actor", "llm": "agent", "reasoning": "agent", "neural-network": "agent",
    "embedding": "process", "token": "neutral", "data-warehouse": "memory", "document-store": "memory",
    "dataset": "memory", "document": "source", "pdf": "source", "image": "source", "audio": "source",
    "video": "source", "code-file": "source", "webhook": "process", "http-request": "process",
    "load-balancer": "process", "server-cluster": "process", "function": "process", "edge-node": "process",
    "source-code": "source", "git-repository": "source", "branch": "source", "pull-request": "process",
    "ci-cd": "process", "deployment": "output", "task": "process", "scheduler": "process",
    "monitoring": "process", "logs": "source", "alert": "risk", "debug": "tool",
}


def _read(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _write(relative: str, value: dict) -> Path:
    path = ROOT / relative
    source = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != source:
            raise RuntimeError(f"{relative} is immutable; create a new release version")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def _write_current(relative: str, value: dict) -> Path:
    """Update an unversioned current pointer; frozen records use `_write`."""

    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _write_text(relative: str, source: str) -> Path:
    path = ROOT / relative
    if path.exists():
        if path.read_text(encoding="utf-8") != source:
            raise RuntimeError(f"{relative} is immutable; create a new release version")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_record(relative: str, *, statuses: tuple[str, ...] = ("approved",)) -> dict:
    record = _read(relative)
    if record.get("status") not in statuses:
        raise RuntimeError(f"{relative} is not approved")
    if record.get("human_visual_acceptance") != "confirmed":
        raise RuntimeError(f"{relative} is missing independent human visual acceptance")
    return record


def _require_final_gates() -> dict:
    batch5_static = _require_record(
        "assets/illustrated/reviews/2.5.0-batch-5-static-acceptance.json",
        statuses=("static-confirmed-motion-pending",),
    )
    batch5_motion = _require_record("assets/illustrated/reviews/2.5.0-batch-5-motion-acceptance.json")
    remaining_static = _require_record(
        "assets/illustrated/reviews/2.5.0-batches-6-10-static-acceptance.json",
        statuses=("static-confirmed-motion-pending",),
    )
    remaining_motion = _require_record("assets/illustrated/reviews/2.5.0-batches-6-10-motion-acceptance.json")
    convention = _require_record("assets/illustrated/reviews/2.5.0-convention-alignment-acceptance.json")
    template = _require_record("assets/illustrated/reviews/2.5.0-template-acceptance.json")
    final_matrix = _require_record("assets/illustrated/reviews/template-matrix-2.5.0-final.json")

    expected_counts = (
        (len(batch5_static.get("approved_icons", ())) == 6, "Batch 5 static acceptance must cover six icons"),
        (len(batch5_motion.get("approved_icons", ())) == 6, "Batch 5 motion acceptance must cover six icons"),
        (remaining_static.get("approved_icon_count") == 30, "Batches 6-10 static acceptance must cover thirty icons"),
        (remaining_motion.get("approved_icon_count") == 30, "Batches 6-10 motion acceptance must cover thirty icons"),
        (convention.get("approved_icon_count") == 12, "convention acceptance must cover twelve icons"),
        (template.get("style_count") == 13, "template acceptance must cover thirteen styles"),
        (final_matrix.get("icon_count") == 56, "final template matrix must cover 56 icons"),
        (final_matrix.get("instance_count") == 728, "final template matrix must contain 728 instances"),
    )
    for passed, message in expected_counts:
        if not passed:
            raise RuntimeError(message)

    validation = _read(VALIDATION_RECORD)
    if validation.get("status") != "verified" or validation.get("version") != "2.5.0":
        raise RuntimeError("Illustrated 2.5 validation ledger is not verified")
    tests = validation.get("python_tests", {})
    if tests.get("passed", 0) < 247 or tests.get("failed") != 0:
        raise RuntimeError("Illustrated 2.5 validation ledger does not record the full Python suite")
    strict = validation.get("diagram_core_strict", {})
    if strict.get("approved") != 56 or strict.get("warnings") != 0 or strict.get("errors") != 0:
        raise RuntimeError("Diagram Core strict validation is incomplete")
    showcase = validation.get("public_showcase", {})
    if showcase.get("rest_verified") != 56 or showcase.get("reduced_motion_verified") != 56 or not showcase.get("mode_switching_verified"):
        raise RuntimeError("56-icon showcase browser gates are incomplete")
    real_case = validation.get("real_case", {})
    if real_case.get("character_timelines") != 13 or real_case.get("animated_edges") != 13 or real_case.get("readable_edges") != 2:
        raise RuntimeError("real-case browser and Edge Motion gates are incomplete")

    for relative in (
        "outputs/illustrated-2.5-showcase/illustrated-2.5-showcase.quality.json",
        "outputs/illustrated-2.5-release-case/illustrated-2.5-release-case.quality.json",
    ):
        quality = _read(relative)
        summary = quality.get("summary", {})
        if any(summary.get(key) != 0 for key in ("errors", "warnings", "issues")):
            raise RuntimeError(f"{relative} is not clean")

    evidence = validation.get("export_evidence", {})
    evidence_path = ROOT / str(evidence.get("path", ""))
    if not evidence_path.is_file() or _sha256(evidence_path) != evidence.get("sha256"):
        raise RuntimeError("formal export evidence is missing or does not match the validation ledger")
    from scripts.build_icon_system_release_evidence import verify_evidence

    report = verify_evidence(evidence_path)
    if not report.get("ok") or report.get("systems") != 2 or report.get("formats") != 10:
        raise RuntimeError("formal two-system export evidence did not verify")
    return validation


def _label(icon_id: str) -> str:
    special = {"pdf": "PDF", "http-request": "HTTP Request", "ci-cd": "CI/CD", "llm": "LLM"}
    return special.get(icon_id, icon_id.replace("-", " ").title())


def _review_sequences() -> dict[str, list[str]]:
    sequences = {}
    for relative in (
        "assets/illustrated/motion-contracts/illustrated-performance-v5.json",
        "assets/illustrated/motion-contracts/illustrated-performance-v6.review.json",
    ):
        for item in _read(relative)["performances"]:
            sequences[item["icon"]] = list(item["semantic_sequence"])
    for icon_id, spec in ILLUSTRATED_PUBLIC_MOTION_SPECS.items():
        sequences[icon_id] = list(spec["sequence"])
    return sequences


def _build_motion_contract(sequences: dict[str, list[str]]) -> dict:
    performances = []
    for icon_id in illustrated_icon_ids():
        definition = illustrated_definition(icon_id)
        item = {
            "icon": icon_id,
            "id": ILLUSTRATED_PUBLIC_ICON_PERFORMANCES[icon_id],
            "semantic_sequence": sequences[icon_id],
            "primary_parts": list(definition.parts[1:]),
            "rest_at": ILLUSTRATED_PUBLIC_REST_AT[icon_id],
        }
        spec = ILLUSTRATED_PUBLIC_MOTION_SPECS.get(icon_id)
        if spec is not None:
            item["motion_recipe"] = {
                "type": spec["recipe"],
                "prepare_parts": list(spec["prepare_parts"]),
                "action_parts": list(spec["action_parts"]),
                "result_parts": list(spec["result_parts"]),
            }
        performances.append(item)
    return {
        "system": "illustrated",
        "icon_system_version": "2.5.0",
        "contract": PUBLIC_CONTRACT,
        "supersedes": "illustrated-performance-v5",
        "review_source": "illustrated-performance-v7-review",
        "review_sources": list(REVIEW_CONTRACTS),
        "status": "approved",
        "approved_at": APPROVED_AT,
        "human_visual_acceptance": "confirmed",
        "public_showcase_enabled": True,
        "selection_policy": "automatic-for-supported-showcase-icons",
        "repeat_delay": 0.8,
        "cancel_behavior": "restore-authored-rest-pose",
        "reduced_motion_behavior": "static-rest",
        "performances": performances,
    }


def _build_catalog(sequences: dict[str, list[str]]) -> dict:
    return {
        "system": "illustrated",
        "display_name": "Illustrated",
        "display_name_zh": "插画",
        "version": "2.5.0",
        "catalog_revision": 10,
        "status": "approved",
        "legacy_aliases": ["illustrated-character-v2"],
        "motion_status": "approved",
        "motion_contract": {
            "id": PUBLIC_CONTRACT,
            "status": "approved",
            "source": "assets/illustrated/motion-contracts/illustrated-performance-v6.json",
        },
        "archived_motion_review_contract": {
            "id": "illustrated-performance-v7-review",
            "status": "archived-after-approval",
            "source": "assets/illustrated/motion-contracts/illustrated-performance-v7.review.json",
        },
        "previous_archived_motion_review_contract": {
            "id": "illustrated-performance-v6-review",
            "status": "archived-after-approval",
            "source": "assets/illustrated/motion-contracts/illustrated-performance-v6.review.json",
        },
        "previous_motion_contract": {
            "id": "illustrated-performance-v5",
            "status": "approved-archive",
            "source": "assets/illustrated/motion-contracts/illustrated-performance-v5.json",
        },
        "icons": [
            {
                "id": icon_id,
                "semantic_role": illustrated_definition(icon_id).semantic_role,
                "parts": list(illustrated_definition(icon_id).parts[1:]),
                "supported_states": [],
                "supported_actions": sequences[icon_id],
                "status": "approved",
                "motion_status": "approved",
                "asset_revision": 2 if icon_id in CONVENTION_IDS else 1,
            }
            for icon_id in illustrated_icon_ids()
        ],
    }


def _build_showcase(sequences: dict[str, list[str]]) -> dict:
    columns = 4
    card_width, card_height = 310, 230
    x_gap, y_gap = 47, 80
    nodes = []
    for index, icon_id in enumerate(illustrated_icon_ids()):
        column, row = index % columns, index // columns
        nodes.append(
            {
                "id": icon_id,
                "label": _label(icon_id),
                "caption": " • ".join(sequences[icon_id]),
                "position": [50 + column * (card_width + x_gap), 160 + row * (card_height + y_gap)],
                "size": [card_width, card_height],
                "role": ROLES[icon_id],
                "icon": icon_id,
            }
        )
    rows = (len(nodes) + columns - 1) // columns
    return {
        "version": "0.4",
        "composition_policy": "composition-v1",
        "resolved_presentation": {
            "icon_system": {"value": "illustrated", "source": "explicit", "version": "2.5.0"},
            "style": {"value": "deep-tech", "source": "explicit"},
            "layout": {"value": "matrix", "source": "explicit"},
            "motion": {"value": "showcase-v1", "source": "default"},
        },
        "preset": "illustrated-2.5-showcase",
        "icon_system": "illustrated",
        "canvas": {"width": 1480, "height": 190 + rows * (card_height + y_gap)},
        "style": "deep-tech",
        "title": {
            "text": "Illustrated 2.5 · Public Showcase",
            "subtitle": "56 approved icons · automatic showcase-v1 performances",
        },
        "motion": {
            "profile": "showcase-v1",
            "sequence": "staged",
            "stagger": 0.08,
            "node": {"preset": "icon-performance"},
            "edge": {"preset": "none"},
            "group": {"preset": "none"},
            "title": {"preset": "highlight-sweep"},
            "reduced_motion": "static",
        },
        "motion_policy": {
            "profile": "unrestricted",
            "motion_area": "unrestricted",
            "max_active_flow_edges": 0,
            "max_particle_edges": 0,
            "max_active_pulse_nodes": 56,
            "max_scanning_groups": 0,
        },
        "nodes": nodes,
    }


def _build_real_case() -> dict:
    nodes = [
        ("application-user", "Application User", "Submits a governed query", "user", "actor", 60, 210),
        ("policy-gateway", "Policy Gateway", "Admits and scopes traffic", "gateway", "risk", 390, 210),
        ("query-api", "Query API", "Normalizes the request", "api", "process", 720, 210),
        ("rag-agent", "RAG Agent", "Plans retrieval and response", "agent", "agent", 1050, 210),
        ("language-model", "Language Model", "Generates grounded language", "llm", "agent", 1380, 210),
        ("cited-output", "Cited Output", "Delivers evidence-backed results", "output", "output", 1710, 210),
        ("source-documents", "Source Documents", "Approved enterprise corpus", "document", "source", 60, 650),
        ("tokenizer", "Tokenizer", "Segments and budgets context", "token", "process", 390, 650),
        ("embedding-service", "Embedding Service", "Vectorizes document chunks", "embedding", "process", 720, 650),
        ("vector-index", "Vector Index", "Indexes semantic vectors", "vector-database", "memory", 1050, 650),
        ("document-store", "Document Store", "Resolves source passages", "document-store", "memory", 1380, 650),
        ("conversation-memory", "Conversation Memory", "Recalls authorized context", "memory", "memory", 1710, 650),
        ("runtime-monitoring", "Runtime Monitoring", "Observes quality and latency", "monitoring", "process", 1910, 430),
    ]
    node_items = [
        {
            "id": node_id,
            "label": label,
            "caption": caption,
            "position": [x, y],
            "size": [250 if node_id != "runtime-monitoring" else 210, 160],
            "role": role,
            "icon": icon,
        }
        for node_id, label, caption, icon, role, x, y in nodes
    ]
    links = [
        ("application-user", "policy-gateway", "query", "packet-flow"),
        ("policy-gateway", "query-api", "admit", "packet-flow"),
        ("query-api", "rag-agent", "route", "packet-flow"),
        ("rag-agent", "language-model", "prompt", "comet-flow"),
        ("language-model", "cited-output", "response", "packet-flow"),
        ("source-documents", "tokenizer", "content", "stream-flow"),
        ("tokenizer", "embedding-service", "segments", "stream-flow"),
        ("embedding-service", "vector-index", "vectors", "stream-flow"),
        ("vector-index", "document-store", "matches", "packet-flow"),
        ("document-store", "conversation-memory", "citations", "packet-flow"),
        ("vector-index", "rag-agent", "retrieve", "comet-flow"),
        ("conversation-memory", "rag-agent", "recall", "packet-flow"),
        ("rag-agent", "runtime-monitoring", "telemetry", "stream-flow"),
    ]
    positions = {item[0]: (item[5], item[6], 250 if item[0] != "runtime-monitoring" else 210) for item in nodes}
    edges = []
    for index, (source, target, label, effect) in enumerate(links):
        sx, sy, sw = positions[source]
        tx, ty, _ = positions[target]
        x1, y1 = sx + sw, sy + 80
        x2, y2 = tx, ty + 80
        path = f"M {x1} {y1} C {(x1+x2)//2} {y1}, {(x1+x2)//2} {y2}, {x2} {y2}"
        edges.append(
            {
                "id": f"flow-{index+1}",
                "from": source,
                "to": target,
                "label": label,
                "kind": "transfer",
                "importance": "primary" if index < 5 else "supporting",
                "flow_id": "online-query" if index < 5 or index in {10, 11} else "knowledge-preparation",
                "flow_importance": "primary" if index < 5 else "supporting",
                "flow_repeat": "loop" if effect == "stream-flow" else "event-driven",
                "path": path,
                "label_position": [(x1 + x2) / 2, (y1 + y2) / 2 - 12],
                "motion": {"enabled": True, "effect": effect, "delay": round(index * 0.05, 2)},
            }
        )
    return {
        "version": "0.4",
        "composition_policy": "composition-v1",
        "resolved_presentation": {
            "icon_system": {"value": "illustrated", "source": "explicit", "version": "2.5.0"},
            "style": {"value": "minimal-light", "source": "model"},
            "layout": {"value": "layered", "source": "explicit"},
            "motion": {"value": "showcase-v1", "source": "explicit"},
        },
        "icon_system": "illustrated",
        "preset": "illustrated-2.5-release-case",
        "canvas": {"width": 2180, "height": 1040},
        "style": "minimal-light",
        "title": {
            "text": "Governed RAG Production Architecture",
            "subtitle": "Continuous knowledge preparation → policy-scoped retrieval → grounded response",
        },
        "motion": {
            "profile": "showcase-v1",
            "sequence": "staged",
            "stagger": 0.08,
            "intensity": 1.0,
            "node": {"preset": "icon-performance"},
            "edge": {"preset": "packet-flow"},
            "group": {"preset": "none"},
            "title": {"preset": "highlight-sweep"},
            "reduced_motion": "static",
        },
        "motion_policy": {"profile": "unrestricted", "motion_area": "unrestricted", "pulse_mode": "all"},
        "nodes": node_items,
        "edges": edges,
    }


def _write_preview() -> tuple[Path, Path]:
    source = render_release_preview()
    preview_path = _write_text("assets/illustrated/previews/illustrated-2.5.0.svg", source)
    root = ET.fromstring(source)
    ids = [element.attrib["id"] for element in root.iter() if "id" in element.attrib]
    quality = {
        "system": "illustrated",
        "version": "2.5.0",
        "status": "approved",
        "icon_count": len(illustrated_icon_ids()),
        "duplicate_ids": sorted({item for item in ids if ids.count(item) > 1}),
        "errors": 0 if len(ids) == len(set(ids)) else 1,
        "motion_status": "approved",
    }
    quality_path = _write("assets/illustrated/previews/illustrated-2.5.0.quality.json", quality)
    return preview_path, quality_path


def promote() -> dict:
    if len(illustrated_icon_ids()) != 56:
        raise RuntimeError("Illustrated public registry must contain exactly 56 icons")
    sequences = _review_sequences()
    if set(sequences) != set(illustrated_icon_ids()):
        raise RuntimeError("motion sequences must cover the exact public registry")
    _require_final_gates()

    motion_path = _write("assets/illustrated/motion-contracts/illustrated-performance-v6.json", _build_motion_contract(sequences))
    catalog = _build_catalog(sequences)
    catalog_path = _write_current("assets/illustrated/catalog.json", catalog)
    snapshot_catalog = _write("assets/illustrated/snapshots/catalog-2.5.0.json", catalog)

    mapping = _read("assets/illustrated/template-mappings.json")
    mapping.update(
        {
            "version": "2.5.0",
            "public_motion_contract": PUBLIC_CONTRACT,
            "archived_motion_review_contract": "illustrated-performance-v7-review",
            "previous_archived_motion_review_contract": "illustrated-performance-v6-review",
        }
    )
    for item in mapping["mappings"]:
        item["final_template_matrix"] = "outputs/illustrated-template-matrix-2.5/illustrated-template-matrix.html"
        if item["style"] == "deep-tech":
            item["public_showcase"] = "outputs/illustrated-2.5-showcase/illustrated-2.5-showcase.html"
    mapping_path = _write_current("assets/illustrated/template-mappings.json", mapping)
    snapshot_mapping = _write("assets/illustrated/snapshots/template-mappings-2.5.0.json", mapping)

    snapshot_registry = _write_text(
        "assets/illustrated/snapshots/registry-2.5.0.py",
        (ROOT / "src/anidiagram/illustrated_registry.py").read_text(encoding="utf-8"),
    )

    showcase_path = _write("examples/illustrated-2.5-showcase.diagram.json", _build_showcase(sequences))
    case_path = _write("examples/illustrated-2.5-release-case.diagram.json", _build_real_case())
    preview_path, quality_path = _write_preview()

    convention_path = ROOT / "assets/illustrated/reviews/2.5.0-convention-alignment-acceptance.json"
    remaining_motion_path = ROOT / "assets/illustrated/reviews/2.5.0-batches-6-10-motion-acceptance.json"

    acceptance = {
        "schema": "illustrated-release-acceptance-v1",
        "system": "illustrated",
        "version": "2.5.0",
        "status": "confirmed",
        "approved_at": APPROVED_AT,
        "static_acceptance": {"status": "confirmed", "approved_icon_count": 56},
        "motion_acceptance": {
            "status": "confirmed",
            "approved_contract": PUBLIC_CONTRACT,
            "review_contracts": list(REVIEW_CONTRACTS),
            "approved_icon_count": 56,
        },
        "template_acceptance": {
            "status": "confirmed",
            "style_count": 13,
            "icon_count": 56,
            "instance_count": 728,
        },
        "convention_alignment": {
            "status": "confirmed",
            "approved_icon_count": len(convention_alignment_icon_ids()),
            "acceptance_record": str(convention_path.relative_to(ROOT)),
        },
        "real_case_acceptance": {
            "status": "confirmed",
            "case": str(case_path.relative_to(ROOT)),
            "edge_motion_contract": "edge-motion-v1@1.0.0",
            "animated_edge_count": 13,
        },
        "public_showcase": {
            "spec": str(showcase_path.relative_to(ROOT)),
            "automatic_motion_icon_count": 56,
            "manifest_verified": 56,
            "rest_verified": 56,
            "reduced_motion_verified": 56,
            "mode_switching_verified": True,
        },
        "public_registration": {"status": "confirmed", "registered_icon_count": 56},
    }
    acceptance_path = _write("assets/illustrated/reviews/2.5.0-acceptance.json", acceptance)

    hash_paths = {
        "catalog_sha256": snapshot_catalog,
        "registry_sha256": snapshot_registry,
        "tokens_sha256": ROOT / "assets/illustrated/tokens-2.5.0.json",
        "renderer_sha256": ROOT / "src/anidiagram/renderer_illustrated_character_v2.py",
        "visual_snapshot_sha256": preview_path,
        "quality_sha256": quality_path,
        "public_motion_contract_sha256": motion_path,
        "batch5_review_contract_sha256": ROOT / "assets/illustrated/motion-contracts/illustrated-performance-v6.review.json",
        "batches6_10_review_contract_sha256": ROOT / "assets/illustrated/motion-contracts/illustrated-performance-v7.review.json",
        "motion_manifest_sha256": ROOT / "src/anidiagram/motion_manifest.py",
        "motion_manifest_v2_sha256": ROOT / "src/anidiagram/motion_manifest_v2.py",
        "runtime_sha256": ROOT / "runtime/anidiagram-runtime.js",
        "public_runtime_extension_sha256": ROOT / "runtime/illustrated-performance-v6-runtime.js",
        "edge_motion_runtime_sha256": ROOT / "runtime/edge-motion-v1-runtime.js",
        "template_mapping_sha256": snapshot_mapping,
        "acceptance_record_sha256": acceptance_path,
        "convention_acceptance_sha256": convention_path,
        "remaining_motion_acceptance_sha256": remaining_motion_path,
        "public_showcase_spec_sha256": showcase_path,
        "real_case_spec_sha256": case_path,
        "previous_release_sha256": ROOT / "assets/illustrated/releases/2.4.0.json",
    }
    release = {
        "system": "illustrated",
        "display_name": "Illustrated",
        "display_name_zh": "插画",
        "version": "2.5.0",
        "status": "frozen-approved-release",
        "scope": "fifty-six-icon-template-motion-and-real-case-release",
        "catalog_lifecycle_status": "approved",
        "human_static_acceptance": "confirmed",
        "static_approved_at": APPROVED_AT,
        "icon_count": 56,
        "motion_status": "approved",
        "public_motion_contract": PUBLIC_CONTRACT,
        "public_motion_icon_count": 56,
        "archived_motion_review_contracts": list(REVIEW_CONTRACTS),
        "motion_human_acceptance": "confirmed",
        "motion_approved_at": APPROVED_AT,
        "template_style_count": 13,
        "template_instance_count": 728,
        "real_case_human_acceptance": "confirmed",
        "public_registration_acceptance": "confirmed",
        "stage_motion_contract": "edge-motion-v1@1.0.0",
        "stage_motion_status": "approved",
        "legacy_aliases": ["illustrated-character-v2"],
        "previous_release": "2.4.0",
        "hashes": {key: _sha256(path) for key, path in hash_paths.items()},
    }
    release_path = _write("assets/illustrated/releases/2.5.0.json", release)
    return {
        "version": "2.5.0",
        "icons": len(illustrated_icon_ids()),
        "performances": len(ILLUSTRATED_PUBLIC_ICON_PERFORMANCES),
        "templates": len(mapping["mappings"]),
        "validation": str((ROOT / VALIDATION_RECORD).relative_to(ROOT)),
        "release": str(release_path.relative_to(ROOT)),
        "catalog": str(catalog_path.relative_to(ROOT)),
        "mapping": str(mapping_path.relative_to(ROOT)),
    }


def main() -> None:
    print(json.dumps(promote(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

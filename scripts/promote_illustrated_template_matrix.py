#!/usr/bin/env python3
"""Promote the human-approved Illustrated template matrix to public styles."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "assets" / "illustrated" / "reviews" / "template-matrix-2.5.0-candidate.json"
MAPPING_PATH = ROOT / "assets" / "illustrated" / "template-mappings.json"
ACCEPTANCE_PATH = ROOT / "assets" / "illustrated" / "reviews" / "2.5.0-template-acceptance.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _token_hash(tokens: dict) -> str:
    payload = json.dumps(tokens, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _require_human_acceptance(review: dict, catalog: list[str]) -> dict:
    if not ACCEPTANCE_PATH.is_file():
        raise RuntimeError("template promotion requires an independent human acceptance record")
    acceptance = _read(ACCEPTANCE_PATH)
    expected_review = str(REVIEW_PATH.relative_to(ROOT))
    checks = (
        (acceptance.get("status") == "approved", "template acceptance is not approved"),
        (acceptance.get("human_visual_acceptance") == "confirmed", "template human acceptance is missing"),
        (acceptance.get("review_source") == expected_review, "template acceptance references another review"),
        (acceptance.get("style_count") == len(catalog), "template acceptance style count is incomplete"),
        (acceptance.get("reviewed_icon_count") == review.get("icon_count"), "template acceptance icon count is incomplete"),
        (acceptance.get("approved_styles") == catalog, "template acceptance does not cover the public catalog"),
    )
    for passed, message in checks:
        if not passed:
            raise RuntimeError(message)
    return acceptance


def promote(approved_at: str) -> dict:
    review = _read(REVIEW_PATH)
    catalog = _read(ROOT / "styles" / "catalog.json")["styles"]
    candidates = review["mappings"]
    if [item["style"] for item in candidates] != catalog:
        raise RuntimeError("template review does not match the public style catalog")
    acceptance = _require_human_acceptance(review, catalog)

    existing_mapping = _read(MAPPING_PATH)
    existing_by_style = {item["style"]: item for item in existing_mapping["mappings"]}
    public_mappings = []
    for item in candidates:
        style_id = item["style"]
        style_path = ROOT / "styles" / f"{style_id}.json"
        style = _read(style_path)
        style["illustrated_tokens"] = item["illustrated_tokens"]
        _write(style_path, style)

        record = dict(existing_by_style.get(style_id, {}))
        record.update(
            {
                "style": style_id,
                "status": "approved",
                "human_visual_acceptance": "confirmed",
                "approved_at": approved_at,
                "token_source": f"styles/{style_id}.json#illustrated_tokens",
                "illustrated_tokens_sha256": _token_hash(item["illustrated_tokens"]),
                "template_matrix_review": review["visual_proof"],
                "constraints": {
                    "geometry_overrides": False,
                    "semantic_structure_overrides": False,
                    "public_style": True,
                },
            }
        )
        public_mappings.append(record)

    already_promoted = (
        existing_mapping.get("template_matrix_acceptance") == str(ACCEPTANCE_PATH.relative_to(ROOT))
        and [item["style"] for item in existing_mapping["mappings"]] == catalog
    )
    public = {
        **existing_mapping,
        "mapping_revision": int(existing_mapping["mapping_revision"]) if already_promoted else int(existing_mapping["mapping_revision"]) + 1,
        "template_matrix_acceptance": str(ACCEPTANCE_PATH.relative_to(ROOT)),
        "mappings": public_mappings,
    }
    _write(MAPPING_PATH, public)

    return acceptance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved-at", default="2026-07-22")
    args = parser.parse_args()
    print(json.dumps(promote(args.approved_at), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

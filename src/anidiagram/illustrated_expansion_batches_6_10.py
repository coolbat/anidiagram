"""Review-only static candidates for Illustrated 2.5.0 Batches 6 through 10."""

from __future__ import annotations

from typing import Dict, Tuple

from .illustrated_character_icons import CharacterIconDefinition, CharacterPrimitive


BATCHES = {
    6: {
        "family": "ai-and-data",
        "icons": ("neural-network", "embedding", "token", "data-warehouse", "document-store", "dataset"),
    },
    7: {
        "family": "content-and-media",
        "icons": ("document", "pdf", "image", "audio", "video", "code-file"),
    },
    8: {
        "family": "network-and-compute",
        "icons": ("webhook", "http-request", "load-balancer", "server-cluster", "function", "edge-node"),
    },
    9: {
        "family": "source-and-delivery",
        "icons": ("source-code", "git-repository", "branch", "pull-request", "ci-cd", "deployment"),
    },
    10: {
        "family": "runtime-and-operations",
        "icons": ("task", "scheduler", "monitoring", "logs", "alert", "debug"),
    },
}

ILLUSTRATED_EXPANSION_6_10_METADATA = {
    "status": "approved",
    "human_visual_acceptance": "confirmed",
    "static_approved_at": "2026-07-23",
    "baseline_version": "2.4.0",
    "target_version": "2.5.0",
    "public_registry_changed": False,
    "motion_status": "visual-review",
    "review_motion_contract": "illustrated-performance-v7-review",
    "batches": BATCHES,
    "accessory_policy": {
        "one_dominant_subject": True,
        "maximum_external_accessories": 2,
        "generic_checkmarks": False,
        "generic_arrows": False,
        "generic_triangles": False,
        "generic_status_badges": False,
    },
}


def _p(kind: str, part: str, **attrs: str) -> CharacterPrimitive:
    return CharacterPrimitive(kind=kind, part=part, attrs=attrs)


def _icon(icon: str, role: str, parts: tuple[str, ...], primitives: tuple[CharacterPrimitive, ...]) -> CharacterIconDefinition:
    return CharacterIconDefinition(icon=icon, semantic_role=role, parts=("root",) + parts, primitives=primitives)


ILLUSTRATED_EXPANSION_BATCHES_6_10: Dict[str, CharacterIconDefinition] = {
    # Batch 6 · AI and data
    "neural-network": _icon(
        "neural-network", "neurons-connect-activate-propagate",
        ("wash", "network-shell", "network-links", "input-neurons", "hidden-neurons", "output-neuron"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("rect", "network-shell", x="17", y="19", width="86", height="83", rx="24", fill="paper", stroke="ink"),
            _p("path", "network-links", d="M31 42 57 33m-26 9 26 25M31 79l26-12m0-34 29 14M57 33l29 38M57 67l29-20m-29 20 29 4", fill="none", stroke="violet", stroke_width="2.6"),
            _p("path", "input-neurons", d="M31 42h0m0 37h0", fill="none", stroke="sky", stroke_width="10"),
            _p("path", "hidden-neurons", d="M57 33h0m0 34h0", fill="none", stroke="teal", stroke_width="11"),
            _p("path", "output-neuron", d="M86 47h0m0 24h0", fill="none", stroke="coral", stroke_width="11"),
        ),
    ),
    "embedding": _icon(
        "embedding", "content-vectorize-position-compare",
        ("wash", "vector-field", "coordinate-grid", "source-token", "vector-beads", "similarity-ring"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("rect", "vector-field", x="18", y="18", width="84", height="84", rx="18", fill="paper", stroke="ink"),
            _p("path", "coordinate-grid", d="M38 28v64M59 28v64M80 28v64M28 39h64M28 60h64M28 81h64", fill="none", stroke="lavender", stroke_width="2", opacity="0.55"),
            _p("rect", "source-token", x="26", y="29", width="23", height="18", rx="6", fill="sun", stroke="ink", stroke_width="2.6"),
            _p("path", "vector-beads", d="M47 73h0M64 54h0M79 67h0M86 39h0", fill="none", stroke="teal-dark", stroke_width="8"),
            _p("circle", "similarity-ring", cx="64", cy="54", r="17", fill="none", stroke="coral", stroke_width="2.8"),
        ),
    ),
    "token": _icon(
        "token", "tokenize-count-budget-consume",
        ("wash", "token-stack-back", "token-stack-mid", "token-face", "token-mark", "segment-ring"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p("circle", "token-stack-back", cx="67", cy="68", r="33", fill="peach", stroke="ink"),
            _p("circle", "token-stack-mid", cx="57", cy="60", r="34", fill="lavender", stroke="ink"),
            _p("circle", "token-face", cx="52", cy="53", r="32", fill="paper", stroke="ink"),
            _p("path", "token-mark", d="M37 39h30M52 39v30", fill="none", stroke="violet", stroke_width="4"),
            _p("path", "segment-ring", d="M30 82c12 12 37 13 51-3", fill="none", stroke="teal-dark", stroke_width="4"),
        ),
    ),
    "data-warehouse": _icon(
        "data-warehouse", "data-land-organize-serve",
        ("wash", "warehouse-roof", "warehouse-body", "storage-bays", "data-crates", "inventory-lights"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p("path", "warehouse-roof", d="M12 45 60 17l48 28Z", fill="lavender", stroke="ink"),
            _p("rect", "warehouse-body", x="18", y="44", width="84", height="61", rx="5", fill="paper", stroke="ink"),
            _p("path", "storage-bays", d="M29 56h25v39H29Zm37 0h25v39H66Z", fill="sky", stroke="ink", stroke_width="2.8"),
            _p("path", "data-crates", d="M34 63h15v11H34Zm0 15h15v11H34Zm37-15h15v11H71Zm0 15h15v11H71Z", fill="mint", stroke="ink", stroke_width="2"),
            _p("path", "inventory-lights", d="M41 69h0m0 15h0m37-15h0m0 15h0", fill="none", stroke="coral", stroke_width="4.5"),
        ),
    ),
    "document-store": _icon(
        "document-store", "documents-ingest-index-retrieve",
        ("wash", "cabinet-shell", "upper-drawer", "lower-drawer", "document-tabs", "index-handles"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("rect", "cabinet-shell", x="22", y="17", width="76", height="88", rx="13", fill="teal", stroke="ink"),
            _p("rect", "upper-drawer", x="30", y="28", width="60", height="29", rx="7", fill="paper", stroke="ink", stroke_width="2.8"),
            _p("rect", "lower-drawer", x="30", y="66", width="60", height="29", rx="7", fill="paper", stroke="ink", stroke_width="2.8"),
            _p("path", "document-tabs", d="M39 28V21h15v7m13 38v-7h15v7", fill="lavender", stroke="ink", stroke_width="2.4"),
            _p("path", "index-handles", d="M49 43h22M49 81h22", fill="none", stroke="coral", stroke_width="4"),
        ),
    ),
    "dataset": _icon(
        "dataset", "records-structure-filter-analyze",
        ("wash", "table-shell", "table-header", "column-lines", "record-lines", "data-markers"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("rect", "table-shell", x="15", y="21", width="90", height="78", rx="12", fill="paper", stroke="ink"),
            _p("path", "table-header", d="M16 42h88V28c0-4-3-7-7-7H23c-4 0-7 3-7 7Z", fill="lavender", stroke="ink", stroke_width="2.8"),
            _p("path", "column-lines", d="M44 22v76M75 22v76", fill="none", stroke="ink", stroke_width="2.4"),
            _p("path", "record-lines", d="M16 61h88M16 80h88", fill="none", stroke="teal-dark", stroke_width="2.4"),
            _p("path", "data-markers", d="M30 51h0m30 19h0m30 19h0", fill="none", stroke="coral", stroke_width="7"),
        ),
    ),
    # Batch 7 · Content and media
    "document": _icon(
        "document", "document-author-read-reference",
        ("wash", "page", "page-corner", "title-line", "body-lines", "reference-tab"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("path", "page", d="M25 13h45l24 24v70H25Z", fill="paper", stroke="ink"),
            _p("path", "page-corner", d="M70 14v24h24", fill="lavender", stroke="ink", stroke_width="2.8"),
            _p("path", "title-line", d="M38 50h40", fill="none", stroke="violet", stroke_width="5"),
            _p("path", "body-lines", d="M38 65h43M38 76h35M38 87h40", fill="none", stroke="teal-dark", stroke_width="2.8"),
            _p("path", "reference-tab", d="M70 87v20l8-6 8 6V87Z", fill="coral", stroke="ink", stroke_width="2.4"),
        ),
    ),
    "pdf": _icon(
        "pdf", "pdf-package-preserve-share",
        ("wash", "pdf-page", "folded-corner", "pdf-mark", "content-band", "format-seal"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p("path", "pdf-page", d="M22 13h51l24 24v70H22Z", fill="paper", stroke="ink"),
            _p("path", "folded-corner", d="M73 14v24h24", fill="peach", stroke="ink", stroke_width="2.8"),
            _p("path", "pdf-mark", d="M32 51v24m0-24h10c9 0 9 12 0 12H32m23-12v24h8c14 0 14-24 0-24Zm35 0H76v24m0-12h11", fill="none", stroke="coral", stroke_width="3"),
            _p("path", "content-band", d="M34 88h49", fill="none", stroke="violet", stroke_width="4"),
            _p("circle", "format-seal", cx="87", cy="91", r="10", fill="sun", stroke="ink", stroke_width="2.4"),
        ),
    ),
    "image": _icon(
        "image", "image-capture-compose-display",
        ("wash", "frame", "sky-field", "sun-disc", "landscape", "focus-corners"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("rect", "frame", x="13", y="20", width="94", height="80", rx="15", fill="paper", stroke="ink"),
            _p("rect", "sky-field", x="23", y="30", width="74", height="60", rx="10", fill="sky", stroke="ink", stroke_width="2.4"),
            _p("circle", "sun-disc", cx="76", cy="46", r="9", fill="sun", stroke="ink", stroke_width="2.4"),
            _p("path", "landscape", d="M24 78c12-18 24-22 36-7 10-13 22-10 36 8v11H24Z", fill="mint", stroke="ink", stroke_width="2.8"),
            _p("path", "focus-corners", d="M29 41v-6h8m46 0h8v6M29 79v6h8m46 0h8v-6", fill="none", stroke="violet", stroke_width="2.6"),
        ),
    ),
    "audio": _icon(
        "audio", "audio-record-process-play",
        ("wash", "headphones", "ear-cups", "wave-panel", "waveform", "level-dots"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("path", "headphones", d="M22 64V49c0-23 15-37 38-37s38 14 38 37v15", fill="none", stroke="violet", stroke_width="7"),
            _p("path", "ear-cups", d="M17 55h17v31H17Zm69 0h17v31H86Z", fill="lavender", stroke="ink"),
            _p("rect", "wave-panel", x="32", y="43", width="56", height="49", rx="15", fill="paper", stroke="ink"),
            _p("path", "waveform", d="M41 68h7l4-15 7 30 7-23 5 15 4-7h5", fill="none", stroke="teal-dark", stroke_width="3"),
            _p("path", "level-dots", d="M44 45h0m32 0h0", fill="none", stroke="coral", stroke_width="6"),
        ),
    ),
    "video": _icon(
        "video", "video-capture-sequence-play",
        ("wash", "video-frame", "film-rail", "screen", "play-control", "timeline-cells"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("rect", "video-frame", x="12", y="23", width="96", height="74", rx="14", fill="paper", stroke="ink"),
            _p("path", "film-rail", d="M13 39h94M13 82h94", fill="none", stroke="violet", stroke_width="5"),
            _p("rect", "screen", x="25", y="45", width="70", height="31", rx="8", fill="sky", stroke="ink", stroke_width="2.5"),
            _p("path", "play-control", d="M53 51 72 60.5 53 70Z", fill="coral", stroke="ink", stroke_width="2.4"),
            _p("path", "timeline-cells", d="M23 29h12v6H23Zm20 0h12v6H43Zm20 0h12v6H63Zm20 0h12v6H83ZM23 86h12v6H23Zm20 0h12v6H43Zm20 0h12v6H63Zm20 0h12v6H83Z", fill="sun", stroke="none"),
        ),
    ),
    "code-file": _icon(
        "code-file", "code-file-author-validate-reuse",
        ("wash", "code-page", "code-corner", "code-brackets", "code-lines", "language-tab"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("path", "code-page", d="M22 13h52l24 24v70H22Z", fill="paper", stroke="ink"),
            _p("path", "code-corner", d="M74 14v24h24", fill="mint", stroke="ink", stroke_width="2.8"),
            _p("path", "code-brackets", d="m44 50-10 10 10 10m30-20 10 10-10 10m-8-26-13 34", fill="none", stroke="violet", stroke_width="3.4"),
            _p("path", "code-lines", d="M37 88h43M37 97h30", fill="none", stroke="teal-dark", stroke_width="2.8"),
            _p("rect", "language-tab", x="27", y="20", width="28", height="13", rx="6", fill="sun", stroke="ink", stroke_width="2"),
        ),
    ),
    # Batch 8 · Network and compute
    "webhook": _icon(
        "webhook", "event-hook-receive-trigger",
        ("wash", "endpoint-socket", "hook-body", "hook-tip", "event-ring", "trigger-beads"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("rect", "endpoint-socket", x="20", y="22", width="43", height="38", rx="11", fill="paper", stroke="ink"),
            _p("path", "hook-body", d="M55 41h23c16 0 23 11 23 24 0 18-13 31-31 31-17 0-28-11-28-25", fill="none", stroke="violet", stroke_width="7"),
            _p("path", "hook-tip", d="M31 66c10-4 19 1 22 10-8 5-18 2-22-10Z", fill="coral", stroke="ink"),
            _p("circle", "event-ring", cx="42", cy="41", r="10", fill="mint", stroke="ink", stroke_width="2.6"),
            _p("path", "trigger-beads", d="M76 41h0m18 14h0m-2 22h0", fill="none", stroke="sun", stroke_width="7"),
        ),
    ),
    "http-request": _icon(
        "http-request", "http-compose-send-receive",
        ("wash", "browser-shell", "address-bar", "http-glyph", "request-rail", "transfer-beads"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("rect", "browser-shell", x="12", y="20", width="96", height="82", rx="14", fill="paper", stroke="ink"),
            _p("path", "address-bar", d="M13 40h94M25 30h0m10 0h0m10 0h0", fill="none", stroke="coral", stroke_width="5.5"),
            _p("path", "http-glyph", d="M27 52v16m9-16v16m-9-8h9m7-8h16m-8 0v16M66 68V52h10c9 0 9 13 0 13H66M90 68V52h10c9 0 9 13 0 13H90", fill="none", stroke="violet", stroke_width="2.4"),
            _p("path", "request-rail", d="M28 83h64", fill="none", stroke="teal-dark", stroke_width="4"),
            _p("path", "transfer-beads", d="M39 83h0m21 0h0m21 0h0", fill="none", stroke="sun", stroke_width="7"),
        ),
    ),
    "load-balancer": _icon(
        "load-balancer", "traffic-distribute-balance-serve",
        ("wash", "balancer-shell", "input-port", "distribution-rails", "service-nodes", "load-signals"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("rect", "balancer-shell", x="37", y="16", width="46", height="34", rx="11", fill="lavender", stroke="ink"),
            _p("rect", "input-port", x="47", y="25", width="26", height="16", rx="6", fill="paper", stroke="ink", stroke_width="2.4"),
            _p("path", "distribution-rails", d="M60 50v19M26 69h68M26 69v12m34-12v12m34-12v12", fill="none", stroke="teal-dark", stroke_width="3.2"),
            _p("path", "service-nodes", d="M12 81h28v23H12Zm34 0h28v23H46Zm34 0h28v23H80Z", fill="sky", stroke="ink", stroke_width="2.6"),
            _p("path", "load-signals", d="M26 92h0m34 0h0m34 0h0", fill="none", stroke="coral", stroke_width="7"),
        ),
    ),
    "server-cluster": _icon(
        "server-cluster", "servers-group-coordinate-scale",
        ("wash", "cluster-back", "cluster-left", "cluster-right", "cluster-links", "activity-lights"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("rect", "cluster-back", x="38", y="12", width="44", height="64", rx="10", fill="lavender", stroke="ink"),
            _p("rect", "cluster-left", x="12", y="42", width="44", height="66", rx="10", fill="paper", stroke="ink"),
            _p("rect", "cluster-right", x="64", y="42", width="44", height="66", rx="10", fill="paper", stroke="ink"),
            _p("path", "cluster-links", d="M60 76v12M34 88h52", fill="none", stroke="teal-dark", stroke_width="3"),
            _p("path", "activity-lights", d="M46 29h0m0 15h0m-23 16h0m0 17h0m52-17h0m0 17h0", fill="none", stroke="mint", stroke_width="6"),
        ),
    ),
    "function": _icon(
        "function", "function-bind-execute-return",
        ("wash", "function-shell", "lambda-mark", "parameter-slots", "result-panel", "runtime-pulse"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("rect", "function-shell", x="18", y="17", width="84", height="86", rx="22", fill="paper", stroke="ink"),
            _p("path", "lambda-mark", d="M39 34h12l23 49M50 44 33 83m31 0h18", fill="none", stroke="violet", stroke_width="5"),
            _p("path", "parameter-slots", d="M78 34h0m10 0h0", fill="none", stroke="teal-dark", stroke_width="7"),
            _p("rect", "result-panel", x="65", y="70", width="26", height="20", rx="7", fill="mint", stroke="ink", stroke_width="2.5"),
            _p("circle", "runtime-pulse", cx="31", cy="31", r="7", fill="sun", stroke="ink", stroke_width="2.4"),
        ),
    ),
    "edge-node": _icon(
        "edge-node", "edge-sense-compute-relay",
        ("wash", "edge-shell", "sensor-window", "compute-core", "signal-arcs", "edge-feet"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p("path", "edge-shell", d="M24 31 60 13l36 18v60L60 108 24 91Z", fill="sky", stroke="ink"),
            _p("rect", "sensor-window", x="36", y="35", width="48", height="25", rx="9", fill="paper", stroke="ink", stroke_width="2.6"),
            _p("rect", "compute-core", x="42", y="68", width="36", height="25", rx="8", fill="mint", stroke="ink", stroke_width="2.6"),
            _p("path", "signal-arcs", d="M47 48c7-7 19-7 26 0m-20 0c4-3 10-3 14 0", fill="none", stroke="violet", stroke_width="2.8"),
            _p("path", "edge-feet", d="M38 98v9m44-9v9", fill="none", stroke="ink", stroke_width="4"),
        ),
    ),
    # Batch 9 · Source and delivery
    "source-code": _icon(
        "source-code", "source-author-organize-build",
        ("wash", "editor-shell", "editor-header", "file-rail", "source-glyphs", "cursor-line"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("rect", "editor-shell", x="12", y="18", width="96", height="84", rx="13", fill="paper", stroke="ink"),
            _p("path", "editor-header", d="M13 38h94M25 28h0m10 0h0m10 0h0", fill="none", stroke="coral", stroke_width="5.5"),
            _p("path", "file-rail", d="M36 39v62M22 51h8m-8 12h8m-8 12h8", fill="none", stroke="lavender", stroke_width="3"),
            _p("path", "source-glyphs", d="m54 53-9 9 9 9m31-18 9 9-9 9m-9-23-13 31", fill="none", stroke="violet", stroke_width="3.2"),
            _p("path", "cursor-line", d="M48 86h38", fill="none", stroke="teal-dark", stroke_width="4"),
        ),
    ),
    "git-repository": _icon(
        "git-repository", "repository-store-version-share",
        ("wash", "repository-shell", "repository-tab", "git-rail", "git-nodes", "repo-label"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("path", "repository-shell", d="M15 34h34l8 9h48v62H15Z", fill="paper", stroke="ink"),
            _p("path", "repository-tab", d="M16 34h32l8 9H16Z", fill="lavender", stroke="ink", stroke_width="2.6"),
            _p("path", "git-rail", d="M40 59v30m0-20h27V58m0 11v20", fill="none", stroke="violet", stroke_width="3.2"),
            _p("path", "git-nodes", d="M40 58h0m0 31h0m27-31h0m0 31h0", fill="none", stroke="teal-dark", stroke_width="8"),
            _p("rect", "repo-label", x="76", y="52", width="20", height="11", rx="5", fill="sun", stroke="ink", stroke_width="2"),
        ),
    ),
    "branch": _icon(
        "branch", "branch-diverge-develop-rejoin",
        ("wash", "branch-field", "main-rail", "branch-rail", "commit-nodes", "branch-labels"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("rect", "branch-field", x="24", y="12", width="72", height="96", rx="24", fill="paper", stroke="ink"),
            _p("path", "main-rail", d="M45 26v68", fill="none", stroke="teal-dark", stroke_width="4"),
            _p("path", "branch-rail", d="M45 49c24 0 30 10 30 24v21", fill="none", stroke="violet", stroke_width="4"),
            _p("path", "commit-nodes", d="M45 27h0m0 22h0m0 45h0M75 73h0m0 21h0", fill="none", stroke="coral", stroke_width="9"),
            _p("path", "branch-labels", d="M55 35h24M55 57h14M55 88h13", fill="none", stroke="sun", stroke_width="3"),
        ),
    ),
    "pull-request": _icon(
        "pull-request", "changes-propose-review-merge",
        ("wash", "request-card", "source-rail", "target-rail", "review-link", "change-nodes"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p("rect", "request-card", x="18", y="15", width="84", height="90", rx="18", fill="paper", stroke="ink"),
            _p("path", "source-rail", d="M39 32v55", fill="none", stroke="teal-dark", stroke_width="4"),
            _p("path", "target-rail", d="M81 32v55", fill="none", stroke="violet", stroke_width="4"),
            _p("path", "review-link", d="M39 51c21 0 42 11 42 30", fill="none", stroke="coral", stroke_width="3.5"),
            _p("path", "change-nodes", d="M39 32h0m0 55h0M81 32h0m0 55h0", fill="none", stroke="sun", stroke_width="9"),
        ),
    ),
    "ci-cd": _icon(
        "ci-cd", "change-build-test-deliver",
        ("wash", "pipeline-shell", "pipeline-rail", "build-stage", "test-stage", "delivery-stage"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("rect", "pipeline-shell", x="10", y="27", width="100", height="67", rx="20", fill="paper", stroke="ink"),
            _p("path", "pipeline-rail", d="M27 61h66", fill="none", stroke="ink", stroke_width="4"),
            _p("rect", "build-stage", x="17", y="43", width="25", height="36", rx="7", fill="lavender", stroke="ink", stroke_width="2.5"),
            _p("rect", "test-stage", x="48", y="43", width="25", height="36", rx="7", fill="sky", stroke="ink", stroke_width="2.5"),
            _p("rect", "delivery-stage", x="79", y="43", width="25", height="36", rx="7", fill="mint", stroke="ink", stroke_width="2.5"),
        ),
    ),
    "deployment": _icon(
        "deployment", "artifact-release-place-activate",
        ("wash", "deployment-frame", "release-package", "placement-rails", "target-platform", "activation-lights"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("rect", "deployment-frame", x="15", y="15", width="90", height="91", rx="20", fill="paper", stroke="ink"),
            _p("path", "release-package", d="M42 27h36v31H42Zm0 0 18 10 18-10M60 37v21", fill="lavender", stroke="ink", stroke_width="2.8"),
            _p("path", "placement-rails", d="M34 65v17m52-17v17", fill="none", stroke="teal-dark", stroke_width="4"),
            _p("path", "target-platform", d="M27 82h66v14H27Z", fill="sky", stroke="ink", stroke_width="2.8"),
            _p("path", "activation-lights", d="M43 89h0m17 0h0m17 0h0", fill="none", stroke="coral", stroke_width="6"),
        ),
    ),
    # Batch 10 · Runtime and operations
    "task": _icon(
        "task", "task-define-execute-complete",
        ("wash", "task-board", "board-clip", "task-lines", "task-markers", "active-marker"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p("rect", "task-board", x="22", y="20", width="76", height="87", rx="13", fill="paper", stroke="ink"),
            _p("rect", "board-clip", x="42", y="12", width="36", height="18", rx="8", fill="lavender", stroke="ink", stroke_width="2.6"),
            _p("path", "task-lines", d="M44 48h39M44 67h31M44 86h39", fill="none", stroke="violet", stroke_width="3"),
            _p("path", "task-markers", d="M34 48h0M34 67h0M34 86h0", fill="none", stroke="teal-dark", stroke_width="7"),
            _p("circle", "active-marker", cx="83", cy="67", r="7", fill="coral", stroke="ink", stroke_width="2.3"),
        ),
    ),
    "scheduler": _icon(
        "scheduler", "schedule-plan-trigger-repeat",
        ("wash", "calendar-shell", "calendar-header", "date-grid", "clock-face", "clock-hands"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("rect", "calendar-shell", x="13", y="21", width="78", height="78", rx="14", fill="paper", stroke="ink"),
            _p("path", "calendar-header", d="M14 43h76M31 14v17m42-17v17", fill="none", stroke="violet", stroke_width="5"),
            _p("path", "date-grid", d="M29 56h10m11 0h10m11 0h10M29 70h10m11 0h10m11 0h10M29 84h10m11 0h10", fill="none", stroke="teal-dark", stroke_width="4"),
            _p("circle", "clock-face", cx="87", cy="83", r="24", fill="sky", stroke="ink"),
            _p("path", "clock-hands", d="M87 69v15l10 7", fill="none", stroke="coral", stroke_width="3.2"),
        ),
    ),
    "monitoring": _icon(
        "monitoring", "metrics-observe-detect-report",
        ("wash", "monitor-shell", "metric-screen", "metric-trace", "signal-points", "monitor-stand"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("rect", "monitor-shell", x="10", y="18", width="100", height="70", rx="14", fill="paper", stroke="ink"),
            _p("rect", "metric-screen", x="20", y="29", width="80", height="48", rx="8", fill="sky", stroke="ink", stroke_width="2.5"),
            _p("path", "metric-trace", d="M28 61h13l8-17 11 25 10-15 9 7h13", fill="none", stroke="violet", stroke_width="3.2"),
            _p("path", "signal-points", d="M49 44h0m11 25h0m10-15h0", fill="none", stroke="coral", stroke_width="7"),
            _p("path", "monitor-stand", d="M60 88v12M39 101h42", fill="none", stroke="ink", stroke_width="5"),
        ),
    ),
    "logs": _icon(
        "logs", "events-record-order-inspect",
        ("wash", "log-stack-back", "log-stack-mid", "log-sheet", "timestamp-dots", "log-lines"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("rect", "log-stack-back", x="31", y="13", width="70", height="77", rx="11", fill="sky", stroke="ink"),
            _p("rect", "log-stack-mid", x="23", y="21", width="70", height="77", rx="11", fill="lavender", stroke="ink"),
            _p("rect", "log-sheet", x="15", y="29", width="70", height="77", rx="11", fill="paper", stroke="ink"),
            _p("path", "timestamp-dots", d="M29 47h0m0 17h0m0 17h0m0 17h0", fill="none", stroke="coral", stroke_width="6"),
            _p("path", "log-lines", d="M42 47h30M42 64h23M42 81h32M42 98h20", fill="none", stroke="teal-dark", stroke_width="3"),
        ),
    ),
    "alert": _icon(
        "alert", "signal-detect-escalate-acknowledge",
        ("wash", "bell-body", "bell-rim", "bell-clapper", "signal-rings", "severity-light"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p("path", "bell-body", d="M29 76c8-9 10-18 10-31 0-14 8-24 21-24s21 10 21 24c0 13 2 22 10 31Z", fill="sun", stroke="ink"),
            _p("path", "bell-rim", d="M24 76h72c0 10-8 14-18 14H42c-10 0-18-4-18-14Z", fill="coral", stroke="ink"),
            _p("circle", "bell-clapper", cx="60", cy="96", r="9", fill="lavender", stroke="ink"),
            _p("path", "signal-rings", d="M27 30c-8 9-8 23-2 33m68-33c8 9 8 23 2 33", fill="none", stroke="violet", stroke_width="3.5"),
            _p("circle", "severity-light", cx="60", cy="14", r="7", fill="coral", stroke="ink", stroke_width="2.4"),
        ),
    ),
    "debug": _icon(
        "debug", "bug-reproduce-inspect-fix",
        ("wash", "bug-body", "bug-head", "bug-legs", "inspection-lens", "probe-point"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("ellipse", "bug-body", cx="50", cy="65", rx="24", ry="30", fill="lavender", stroke="ink"),
            _p("circle", "bug-head", cx="50", cy="34", r="15", fill="coral", stroke="ink"),
            _p("path", "bug-legs", d="M28 52 16 44m12 21H13m15 13-12 9m56-35 10-8M72 65h13M72 78l10 9M42 21l-7-10m23 10 7-10", fill="none", stroke="ink", stroke_width="3.2"),
            _p("circle", "inspection-lens", cx="83", cy="79", r="20", fill="paper", stroke="teal-dark", stroke_width="4"),
            _p("circle", "probe-point", cx="83", cy="79", r="7", fill="sun", stroke="ink", stroke_width="2.4"),
        ),
    ),
}


def expansion_6_10_definition(icon: str) -> CharacterIconDefinition | None:
    return ILLUSTRATED_EXPANSION_BATCHES_6_10.get(icon)


def expansion_6_10_icon_ids() -> Tuple[str, ...]:
    return tuple(ILLUSTRATED_EXPANSION_BATCHES_6_10)


def expansion_batch_icon_ids(batch: int) -> Tuple[str, ...]:
    return tuple(BATCHES[batch]["icons"])

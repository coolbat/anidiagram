"""Public Illustrated 2.5.0 motion authority for all 56 icons."""

from __future__ import annotations

from .illustrated_sources import compose_motion_values, merge_registered_maps, source_value

# Compatibility exports retain the frozen batch objects.
ILLUSTRATED_V6_REVIEW_ICON_PERFORMANCES = source_value("expansion-5", "performances")
ILLUSTRATED_V6_REVIEW_REST_AT = source_value("expansion-5", "rest_at")
ILLUSTRATED_V7_REVIEW_ICON_PERFORMANCES = source_value("expansion-6-10", "performances")
ILLUSTRATED_V7_REVIEW_MOTION_SPECS = source_value("expansion-6-10", "motion_specs")
ILLUSTRATED_V7_REVIEW_REST_AT = source_value("expansion-6-10", "rest_at")
from .illustrated_motion_spec import illustrated_motion_spec as _spec


_PUBLIC_24_PERFORMANCES = {
    "agent": "illustrated-agent-input-reason-result-v1",
    "operator": "illustrated-operator-focus-operate-confirm-v1",
    "tool": "illustrated-tool-prepare-execute-complete-v1",
    "output": "illustrated-output-compose-deliver-confirm-v1",
    "database": "illustrated-database-ingest-store-persist-v1",
    "api": "illustrated-api-request-route-response-v1",
    "search": "illustrated-search-query-scan-discover-v1",
    "memory": "illustrated-memory-capture-index-recall-v1",
    "file": "illustrated-file-prepare-attach-reference-v1",
    "folder": "illustrated-folder-prepare-store-index-v1",
    "cloud": "illustrated-cloud-prepare-transfer-sync-v1",
    "shield": "illustrated-shield-prepare-lock-protect-v1",
    "user": "illustrated-user-request-interact-consume-v1",
    "server": "illustrated-server-host-compute-serve-v1",
    "ai-model": "illustrated-ai-model-infer-transform-predict-v1",
    "message-queue": "illustrated-message-queue-buffer-order-deliver-v1",
    "vector-database": "illustrated-vector-database-embed-index-retrieve-v1",
    "knowledge-base": "illustrated-knowledge-base-curate-connect-reference-v1",
    "gateway": "illustrated-gateway-admit-route-mediate-v1",
    "container": "illustrated-container-package-isolate-run-v1",
}

_PUBLIC_24_REST_AT = {
    "agent": 1.72,
    "operator": 1.68,
    "tool": 1.62,
    "output": 1.70,
    "database": 1.72,
    "api": 1.66,
    "search": 1.78,
    "memory": 1.72,
    "file": 1.58,
    "folder": 1.66,
    "cloud": 1.72,
    "shield": 1.68,
    "user": 1.66,
    "server": 1.70,
    "ai-model": 1.80,
    "message-queue": 1.76,
    "vector-database": 1.78,
    "knowledge-base": 1.82,
    "gateway": 1.76,
    "container": 1.80,
}


_CONVENTION_RECIPE_OVERRIDES = {
    "output": _spec(
        ("compose", "deliver", "confirm"),
        "cascade",
        ("delivery-tray", "delivery-lip"),
        ("artifact-card", "artifact-corner", "emergence-track"),
        ("artifact-lines",),
        1.70,
    ),
    "memory": _spec(
        ("capture", "index", "recall"),
        "draw",
        ("context-stack", "context-card"),
        ("context-nodes", "context-links"),
        ("recall-orbit", "recall-focus"),
        1.72,
    ),
    "gateway": _spec(
        ("admit", "route", "mediate"),
        "sweep",
        ("boundary-appliance", "policy-core"),
        ("inbound-lanes", "outbound-lanes", "request-packets"),
        ("response-packets",),
        1.76,
    ),
    "token": _spec(
        ("tokenize", "count", "budget"), "cascade",
        ("tokenizer-shell", "context-strip"),
        ("token-segments", "segment-glyphs"),
        ("budget-rail", "budget-slots"), 1.80,
    ),
    "data-warehouse": _spec(
        ("land", "organize", "serve"), "cascade",
        ("warehouse-roof", "warehouse-body"),
        ("storage-cylinder", "storage-top", "storage-layers"),
        ("inventory-points",), 1.86,
    ),
    "document-store": _spec(
        ("ingest", "index", "retrieve"), "sweep",
        ("store-body", "store-top"),
        ("document-card", "document-corner", "record-lines"),
        ("index-points",), 1.82,
    ),
    "webhook": _spec(
        ("emit", "callback", "resolve"), "draw",
        ("callback-field", "event-node"),
        ("callback-arcs", "handler-node"),
        ("result-node", "event-pulse"), 1.86,
    ),
    "git-repository": _spec(
        ("store", "version", "share"), "draw",
        ("repository-shell", "repository-tab"),
        ("git-main-rail", "git-branch-rail"),
        ("commit-nodes",), 1.84,
    ),
    "branch": _spec(
        ("diverge", "develop", "rejoin"), "draw",
        ("main-rail", "main-nodes"), ("branch-rail",),
        ("branch-nodes", "branch-focus"), 1.88,
    ),
    "pull-request": _spec(
        ("propose", "review", "merge"), "draw",
        ("source-rail", "source-nodes"),
        ("request-path", "request-tip"), ("target-node",), 1.88,
    ),
    "ci-cd": _spec(
        ("build", "test", "deliver"), "cascade",
        ("delivery-loop",), ("source-stage", "build-stage"),
        ("release-stage", "stage-cores"), 1.86,
    ),
    "deployment": _spec(
        ("release", "place", "activate"), "bounce",
        ("environment-dock", "server-bays"),
        ("release-package", "package-seam", "placement-track"),
        ("runtime-lights",), 1.86,
    ),
}

ILLUSTRATED_PUBLIC_ICON_PERFORMANCES = compose_motion_values("performances", _PUBLIC_24_PERFORMANCES)
ILLUSTRATED_PUBLIC_REST_AT = compose_motion_values("rest_at", _PUBLIC_24_REST_AT)
ILLUSTRATED_PUBLIC_MOTION_SPECS = merge_registered_maps([
    ("expansion-6-10", ILLUSTRATED_V7_REVIEW_MOTION_SPECS, ()),
    ("convention-alignment", _CONVENTION_RECIPE_OVERRIDES, tuple(_CONVENTION_RECIPE_OVERRIDES)),
])

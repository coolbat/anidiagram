"""Review-only semantic motion specifications for Illustrated Batches 6-10."""

from __future__ import annotations

from .illustrated_motion_spec import illustrated_motion_spec as _spec


ILLUSTRATED_V7_REVIEW_MOTION_SPECS = {
    "neural-network": _spec(("connect", "activate", "propagate"), "draw", ("network-shell",), ("network-links",), ("output-neuron",), 1.82),
    "embedding": _spec(("vectorize", "position", "compare"), "cascade", ("vector-field", "coordinate-grid"), ("source-token", "vector-beads"), ("similarity-ring",), 1.84),
    "token": _spec(("count", "budget", "consume"), "fan", ("token-stack-back", "token-stack-mid"), ("token-face", "token-mark"), ("segment-ring",), 1.80),
    "data-warehouse": _spec(("land", "organize", "serve"), "cascade", ("warehouse-roof", "warehouse-body"), ("storage-bays", "data-crates"), ("inventory-lights",), 1.86),
    "document-store": _spec(("ingest", "index", "retrieve"), "sweep", ("cabinet-shell",), ("upper-drawer", "lower-drawer", "document-tabs"), ("index-handles",), 1.82),
    "dataset": _spec(("structure", "filter", "analyze"), "draw", ("table-shell", "table-header"), ("column-lines", "record-lines"), ("data-markers",), 1.86),
    "document": _spec(("author", "read", "reference"), "draw", ("page", "page-corner"), ("title-line", "body-lines"), ("reference-tab",), 1.80),
    "pdf": _spec(("package", "preserve", "share"), "draw", ("pdf-page", "folded-corner"), ("pdf-mark", "content-band"), ("format-seal",), 1.84),
    "image": _spec(("capture", "compose", "display"), "cascade", ("frame", "sky-field"), ("sun-disc", "landscape"), ("focus-corners",), 1.82),
    "audio": _spec(("record", "process", "play"), "oscillate", ("headphones", "ear-cups"), ("wave-panel", "waveform"), ("level-dots",), 1.86),
    "video": _spec(("capture", "sequence", "play"), "sweep", ("video-frame", "film-rail"), ("timeline-cells", "screen"), ("play-control",), 1.82),
    "code-file": _spec(("author", "validate", "reuse"), "draw", ("code-page", "code-corner"), ("code-brackets", "code-lines"), ("language-tab",), 1.84),
    "webhook": _spec(("hook", "receive", "trigger"), "draw", ("endpoint-socket", "event-ring"), ("hook-body", "hook-tip"), ("trigger-beads",), 1.86),
    "http-request": _spec(("compose", "send", "receive"), "sweep", ("browser-shell", "address-bar"), ("http-glyph", "request-rail"), ("transfer-beads",), 1.84),
    "load-balancer": _spec(("distribute", "balance", "serve"), "draw", ("balancer-shell", "input-port"), ("distribution-rails",), ("service-nodes", "load-signals"), 1.88),
    "server-cluster": _spec(("group", "coordinate", "scale"), "fan", ("cluster-back",), ("cluster-left", "cluster-right", "cluster-links"), ("activity-lights",), 1.86),
    "function": _spec(("bind", "execute", "return"), "draw", ("function-shell", "parameter-slots"), ("lambda-mark",), ("result-panel", "runtime-pulse"), 1.82),
    "edge-node": _spec(("sense", "compute", "relay"), "oscillate", ("edge-shell", "edge-feet"), ("sensor-window", "signal-arcs"), ("compute-core",), 1.84),
    "source-code": _spec(("author", "organize", "build"), "draw", ("editor-shell", "editor-header"), ("file-rail", "source-glyphs"), ("cursor-line",), 1.84),
    "git-repository": _spec(("store", "version", "share"), "draw", ("repository-shell", "repository-tab"), ("git-rail", "git-nodes"), ("repo-label",), 1.84),
    "branch": _spec(("diverge", "develop", "rejoin"), "draw", ("branch-field", "main-rail"), ("branch-rail", "commit-nodes"), ("branch-labels",), 1.88),
    "pull-request": _spec(("propose", "review", "merge"), "draw", ("request-card", "source-rail"), ("review-link", "target-rail"), ("change-nodes",), 1.88),
    "ci-cd": _spec(("build", "test", "deliver"), "cascade", ("pipeline-shell", "pipeline-rail"), ("build-stage", "test-stage"), ("delivery-stage",), 1.86),
    "deployment": _spec(("release", "place", "activate"), "bounce", ("deployment-frame",), ("release-package", "placement-rails"), ("target-platform", "activation-lights"), 1.86),
    "task": _spec(("define", "execute", "complete"), "cascade", ("task-board", "board-clip"), ("task-lines", "task-markers"), ("active-marker",), 1.82),
    "scheduler": _spec(("plan", "trigger", "repeat"), "oscillate", ("calendar-shell", "calendar-header"), ("date-grid", "clock-hands"), ("clock-face",), 1.86),
    "monitoring": _spec(("observe", "detect", "report"), "draw", ("monitor-shell", "metric-screen"), ("metric-trace",), ("signal-points", "monitor-stand"), 1.84),
    "logs": _spec(("record", "order", "inspect"), "fan", ("log-stack-back", "log-stack-mid"), ("log-sheet", "log-lines"), ("timestamp-dots",), 1.86),
    "alert": _spec(("detect", "escalate", "acknowledge"), "oscillate", ("bell-body", "bell-rim"), ("signal-rings", "bell-clapper"), ("severity-light",), 1.86),
    "debug": _spec(("reproduce", "inspect", "fix"), "sweep", ("bug-body", "bug-head", "bug-legs"), ("inspection-lens",), ("probe-point",), 1.84),
}


ILLUSTRATED_V7_REVIEW_ICON_PERFORMANCES = {
    icon: f"illustrated-{icon}-{'-'.join(spec['sequence'])}-v1"
    for icon, spec in ILLUSTRATED_V7_REVIEW_MOTION_SPECS.items()
}

ILLUSTRATED_V7_REVIEW_REST_AT = {
    icon: spec["rest_at"] for icon, spec in ILLUSTRATED_V7_REVIEW_MOTION_SPECS.items()
}

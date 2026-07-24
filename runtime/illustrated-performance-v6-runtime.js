  // Illustrated 2.5.0 public extension: approved Batch 5 motions.
  function playIllustratedDeveloper({ config, parts, gsap }) {
    const required = ["body", "head", "hair", "code-console", "console-header", "code-glyphs", "hands"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const glyphLength = primeStrokeDraw([parts["code-glyphs"]], gsap).get(parts["code-glyphs"]);
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.fromTo(parts["code-console"], { y: 10, scale: 0.94 }, { y: 0, scale: 1, duration: 0.3, ease: "back.out(2.8)" }, 0)
      .to([parts.head, parts.hair], { y: 2, rotation: -2, duration: 0.18, ease: "sine.inOut" }, 0.18)
      .to([parts.head, parts.hair], { y: 0, rotation: 0, duration: 0.2, ease: "sine.inOut" }, 0.36)
      .fromTo(parts["code-glyphs"], { opacity: 0.2, strokeDashoffset: glyphLength }, { opacity: 1, strokeDashoffset: 0, duration: 0.62, ease: "power1.inOut" }, 0.3)
      .to(parts.hands, { y: 4, duration: 0.11, yoyo: true, repeat: 3, ease: "power1.inOut" }, 0.52)
      .to(parts["console-header"], { scaleX: 1.03, duration: 0.16, ease: "sine.inOut" }, 1.18)
      .to(parts["console-header"], { scaleX: 1, duration: 0.18, ease: "sine.inOut" }, 1.34);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  function playIllustratedAgentTeam({ config, parts, gsap }) {
    const required = ["collaboration-field", "team-links", "lead-agent", "lead-core", "member-left", "member-right", "member-cores"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const linkLength = primeStrokeDraw([parts["team-links"]], gsap).get(parts["team-links"]);
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.fromTo([parts["lead-agent"], parts["lead-core"]], { y: -10, scale: 0.72 }, { y: 0, scale: 1.12, duration: 0.3, ease: "back.out(3)" }, 0)
      .to([parts["lead-agent"], parts["lead-core"]], { scale: 1, duration: 0.18, ease: "power2.out" }, 0.3)
      .fromTo(parts["team-links"], { opacity: 0.18, strokeDashoffset: linkLength }, { opacity: 1, strokeDashoffset: 0, duration: 0.5, ease: "power1.inOut" }, 0.25)
      .fromTo(parts["member-left"], { x: -13, opacity: 0.35, scale: 0.82 }, { x: 0, opacity: 1, scale: 1, duration: 0.34, ease: "back.out(2.8)" }, 0.55)
      .fromTo(parts["member-right"], { x: 13, opacity: 0.35, scale: 0.82 }, { x: 0, opacity: 1, scale: 1, duration: 0.34, ease: "back.out(2.8)" }, 0.68)
      .fromTo(parts["member-cores"], { opacity: 0.28, scale: 0.55 }, { opacity: 1, scale: 1.35, duration: 0.25, ease: "back.out(3.2)" }, 0.88)
      .to(parts["member-cores"], { scale: 1, duration: 0.22, ease: "elastic.out(1, 0.4)" }, 1.13)
      .to(parts["collaboration-field"], { scale: 1.025, duration: 0.16, ease: "sine.inOut" }, 1.34)
      .to(parts["collaboration-field"], { scale: 1, duration: 0.18, ease: "sine.inOut" }, 1.5);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  function playIllustratedAssistant({ config, parts, gsap }) {
    const required = ["assistant-shell", "face-panel", "eyes", "smile", "headset", "earpieces", "response-panel", "response-lines"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const lineLength = primeStrokeDraw([parts["response-lines"]], gsap).get(parts["response-lines"]);
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.to(parts["assistant-shell"], { y: -4, scaleY: 1.03, duration: 0.22, ease: "back.out(2.4)" }, 0)
      .fromTo([parts.headset, parts.earpieces], { scale: 0.88, opacity: 0.45 }, { scale: 1.08, opacity: 1, duration: 0.3, ease: "back.out(3)" }, 0.12)
      .to([parts.headset, parts.earpieces], { scale: 1, duration: 0.18, ease: "power2.out" }, 0.42)
      .to(parts.eyes, { scaleY: 0.15, duration: 0.1, yoyo: true, repeat: 1, ease: "power1.inOut" }, 0.58)
      .to(parts.smile, { scaleX: 1.16, duration: 0.18, ease: "back.out(2.5)" }, 0.78)
      .fromTo(parts["response-panel"], { y: 7, opacity: 0.4 }, { y: 0, opacity: 1, duration: 0.28, ease: "back.out(2.6)" }, 0.86)
      .fromTo(parts["response-lines"], { opacity: 0.2, strokeDashoffset: lineLength }, { opacity: 1, strokeDashoffset: 0, duration: 0.36, ease: "power1.inOut" }, 1.02)
      .to([parts["assistant-shell"], parts.smile], { y: 0, scaleX: 1, scaleY: 1, duration: 0.24, ease: "sine.inOut" }, 1.4);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  function playIllustratedHumanReviewer({ config, parts, gsap }) {
    const required = ["body", "head", "hair", "glasses", "review-sheet", "review-lines", "decision-signals", "hands"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const lineLength = primeStrokeDraw([parts["review-lines"]], gsap).get(parts["review-lines"]);
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.fromTo(parts["review-sheet"], { y: 10, opacity: 0.5, scale: 0.94 }, { y: 0, opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2.7)" }, 0)
      .to([parts.head, parts.hair, parts.glasses], { rotation: 4, y: 2, duration: 0.2, ease: "sine.inOut" }, 0.2)
      .to([parts.head, parts.hair, parts.glasses], { rotation: -3, duration: 0.24, ease: "sine.inOut" }, 0.42)
      .fromTo(parts["review-lines"], { opacity: 0.2, strokeDashoffset: lineLength }, { opacity: 1, strokeDashoffset: 0, duration: 0.58, ease: "power1.inOut" }, 0.34)
      .fromTo(parts["decision-signals"], { opacity: 0.22, scale: 0.55 }, { opacity: 1, scale: 1.38, duration: 0.28, ease: "back.out(3.1)" }, 0.88)
      .to(parts["decision-signals"], { scale: 1, duration: 0.22, ease: "elastic.out(1, 0.42)" }, 1.16)
      .to(parts.hands, { y: -3, duration: 0.16, ease: "sine.inOut" }, 1.15)
      .to([parts.head, parts.hair, parts.glasses, parts.hands], { rotation: 0, x: 0, y: 0, duration: 0.26, ease: "sine.inOut" }, 1.4);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  function playIllustratedLlm({ config, parts, gsap }) {
    const required = ["context-back", "context-mid", "model-shell", "model-mark", "token-lines", "completion-dots"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const lengths = primeStrokeDraw([parts["model-mark"], parts["token-lines"]], gsap);
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.fromTo(parts["context-back"], { x: 10, y: -5, rotation: 6 }, { x: 0, y: 0, rotation: 0, duration: 0.32, ease: "back.out(2.8)" }, 0)
      .fromTo(parts["context-mid"], { x: -10, y: -2, rotation: -6 }, { x: 0, y: 0, rotation: 0, duration: 0.32, ease: "back.out(2.8)" }, 0.1)
      .fromTo(parts["model-shell"], { y: 8, scale: 0.94 }, { y: 0, scale: 1, duration: 0.28, ease: "back.out(2.6)" }, 0.22)
      .fromTo(parts["model-mark"], { opacity: 0.2, strokeDashoffset: lengths.get(parts["model-mark"]) }, { opacity: 1, strokeDashoffset: 0, duration: 0.42, ease: "power1.inOut" }, 0.42)
      .fromTo(parts["token-lines"], { opacity: 0.2, strokeDashoffset: lengths.get(parts["token-lines"]) }, { opacity: 1, strokeDashoffset: 0, duration: 0.38, ease: "power1.inOut" }, 0.72)
      .fromTo(parts["completion-dots"], { opacity: 0.18, scale: 0.45 }, { opacity: 1, scale: 1.42, duration: 0.28, ease: "back.out(3.2)" }, 1.0)
      .to(parts["completion-dots"], { scale: 1, duration: 0.22, ease: "elastic.out(1, 0.42)" }, 1.28)
      .to(parts["model-shell"], { scale: 1.02, duration: 0.14, ease: "sine.inOut" }, 1.42)
      .to(parts["model-shell"], { scale: 1, duration: 0.18, ease: "sine.inOut" }, 1.56);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  function playIllustratedReasoning({ config, parts, gsap }) {
    const required = ["reasoning-shell", "thought-field", "reasoning-path", "premise-points", "conclusion-point", "insight-base"];
    if (!hasParts(parts, required)) return null;
    setInitial(parts, gsap);
    const pathLength = primeStrokeDraw([parts["reasoning-path"]], gsap).get(parts["reasoning-path"]);
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    timeline.to(parts["reasoning-shell"], { scaleY: 0.97, scaleX: 1.025, duration: 0.16, ease: "power2.inOut" }, 0)
      .to(parts["reasoning-shell"], { scaleY: 1, scaleX: 1, duration: 0.22, ease: "back.out(2.5)" }, 0.16)
      .fromTo(parts["premise-points"], { opacity: 0.2, scale: 0.55 }, { opacity: 1, scale: 1.28, duration: 0.28, ease: "back.out(3)" }, 0.3)
      .to(parts["premise-points"], { scale: 1, duration: 0.18, ease: "power2.out" }, 0.58)
      .fromTo(parts["reasoning-path"], { opacity: 0.18, strokeDashoffset: pathLength }, { opacity: 1, strokeDashoffset: 0, duration: 0.68, ease: "power1.inOut" }, 0.46)
      .fromTo(parts["conclusion-point"], { opacity: 0.25, scale: 0.45 }, { opacity: 1, scale: 1.5, duration: 0.28, ease: "back.out(3.4)" }, 1.08)
      .to(parts["conclusion-point"], { scale: 1, duration: 0.22, ease: "elastic.out(1, 0.4)" }, 1.36)
      .to(parts["insight-base"], { scaleX: 1.14, duration: 0.16, ease: "sine.inOut" }, 1.46)
      .to(parts["insight-base"], { scaleX: 1, duration: 0.18, ease: "sine.inOut" }, 1.62);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }

  performances["illustrated-developer-code-build-deliver-v1"] = playIllustratedDeveloper;
  performances["illustrated-agent-team-coordinate-delegate-synthesize-v1"] = playIllustratedAgentTeam;
  performances["illustrated-assistant-listen-guide-respond-v1"] = playIllustratedAssistant;
  performances["illustrated-human-reviewer-inspect-decide-annotate-v1"] = playIllustratedHumanReviewer;
  performances["illustrated-llm-context-transform-generate-v1"] = playIllustratedLlm;
  performances["illustrated-reasoning-premise-infer-conclude-v1"] = playIllustratedReasoning;

  // Illustrated 2.5.0 public extension: configured expansion and revised-icon motions.
  function playIllustratedPublicConfigured({ config, parts, gsap }) {
    const spec = config.motion_recipe || {};
    const names = [...(spec.prepare_parts || []), ...(spec.action_parts || []), ...(spec.result_parts || [])];
    if (!hasParts(parts, names)) return null;
    setInitial(parts, gsap);
    const prepare = (spec.prepare_parts || []).map((name) => parts[name]).filter(Boolean);
    const action = (spec.action_parts || []).map((name) => parts[name]).filter(Boolean);
    const result = (spec.result_parts || []).map((name) => parts[name]).filter(Boolean);
    const timeline = gsap.timeline({ repeat: -1, repeatDelay: config.repeat_delay || CHARACTER_REPEAT_DELAY });
    if (prepare.length) timeline.fromTo(prepare, { opacity: 0.42, y: 8, scale: 0.92 }, { opacity: 1, y: 0, scale: 1, duration: 0.3, stagger: 0.05, ease: "back.out(2.5)" }, 0);
    const recipe = spec.type || "cascade";
    if (recipe === "draw") {
      const lengths = primeStrokeDraw(action, gsap);
      action.forEach((target, index) => timeline.fromTo(target,
        { opacity: 0.18, strokeDashoffset: lengths.get(target) },
        { opacity: 1, strokeDashoffset: 0, duration: 0.52, ease: "power1.inOut" }, 0.32 + index * 0.08));
    } else if (recipe === "fan") {
      timeline.fromTo(action, { opacity: 0.35, x: (i) => i % 2 ? 10 : -10, rotation: (i) => i % 2 ? 7 : -7, scale: 0.9 },
        { opacity: 1, x: 0, rotation: 0, scale: 1, duration: 0.46, stagger: 0.08, ease: "back.out(2.8)" }, 0.32);
    } else if (recipe === "oscillate") {
      timeline.fromTo(action, { opacity: 0.4, scaleY: 0.72 }, { opacity: 1, scaleY: 1.22, duration: 0.28, stagger: 0.07, ease: "sine.inOut" }, 0.32)
        .to(action, { scaleY: 1, duration: 0.28, stagger: 0.05, ease: "sine.inOut" }, 0.68);
    } else if (recipe === "sweep") {
      timeline.fromTo(action, { opacity: 0.35, x: -10, scale: 0.9 }, { opacity: 1, x: 8, scale: 1.08, duration: 0.4, stagger: 0.07, ease: "power2.inOut" }, 0.32)
        .to(action, { x: 0, scale: 1, duration: 0.24, stagger: 0.05, ease: "power2.out" }, 0.76);
    } else if (recipe === "bounce") {
      timeline.fromTo(action, { opacity: 0.35, y: -12, scale: 0.84 }, { opacity: 1, y: 5, scale: 1.08, duration: 0.38, stagger: 0.07, ease: "back.out(2.9)" }, 0.32)
        .to(action, { y: 0, scale: 1, duration: 0.24, stagger: 0.05, ease: "power2.out" }, 0.74);
    } else {
      timeline.fromTo(action, { opacity: 0.28, y: 10, scale: 0.8 }, { opacity: 1, y: 0, scale: 1, duration: 0.42, stagger: 0.1, ease: "back.out(2.8)" }, 0.32);
    }
    if (result.length) timeline.fromTo(result, { opacity: 0.25, scale: 0.5 }, { opacity: 1, scale: 1.34, duration: 0.28, stagger: 0.07, ease: "back.out(3.2)" }, 1.08)
      .to(result, { scale: 1, duration: 0.22, stagger: 0.05, ease: "elastic.out(1, 0.42)" }, 1.36);
    return finishCharacterAtRest(timeline, parts, config.rest_at);
  }
  performances["illustrated-neural-network-connect-activate-propagate-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-embedding-vectorize-position-compare-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-token-count-budget-consume-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-data-warehouse-land-organize-serve-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-document-store-ingest-index-retrieve-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-dataset-structure-filter-analyze-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-document-author-read-reference-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-pdf-package-preserve-share-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-image-capture-compose-display-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-audio-record-process-play-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-video-capture-sequence-play-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-code-file-author-validate-reuse-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-webhook-hook-receive-trigger-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-http-request-compose-send-receive-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-load-balancer-distribute-balance-serve-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-server-cluster-group-coordinate-scale-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-function-bind-execute-return-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-edge-node-sense-compute-relay-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-source-code-author-organize-build-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-git-repository-store-version-share-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-branch-diverge-develop-rejoin-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-pull-request-propose-review-merge-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-ci-cd-build-test-deliver-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-deployment-release-place-activate-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-task-define-execute-complete-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-scheduler-plan-trigger-repeat-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-monitoring-observe-detect-report-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-logs-record-order-inspect-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-alert-detect-escalate-acknowledge-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-debug-reproduce-inspect-fix-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-output-compose-deliver-confirm-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-memory-capture-index-recall-v1"] = playIllustratedPublicConfigured;
  performances["illustrated-gateway-admit-route-mediate-v1"] = playIllustratedPublicConfigured;
  characterPerformanceIds.add("illustrated-agent-input-reason-result-v1");
  characterPerformanceIds.add("illustrated-operator-focus-operate-confirm-v1");
  characterPerformanceIds.add("illustrated-tool-prepare-execute-complete-v1");
  characterPerformanceIds.add("illustrated-output-compose-deliver-confirm-v1");
  characterPerformanceIds.add("illustrated-database-ingest-store-persist-v1");
  characterPerformanceIds.add("illustrated-api-request-route-response-v1");
  characterPerformanceIds.add("illustrated-search-query-scan-discover-v1");
  characterPerformanceIds.add("illustrated-memory-capture-index-recall-v1");
  characterPerformanceIds.add("illustrated-file-prepare-attach-reference-v1");
  characterPerformanceIds.add("illustrated-folder-prepare-store-index-v1");
  characterPerformanceIds.add("illustrated-cloud-prepare-transfer-sync-v1");
  characterPerformanceIds.add("illustrated-shield-prepare-lock-protect-v1");
  characterPerformanceIds.add("illustrated-user-request-interact-consume-v1");
  characterPerformanceIds.add("illustrated-server-host-compute-serve-v1");
  characterPerformanceIds.add("illustrated-ai-model-infer-transform-predict-v1");
  characterPerformanceIds.add("illustrated-message-queue-buffer-order-deliver-v1");
  characterPerformanceIds.add("illustrated-vector-database-embed-index-retrieve-v1");
  characterPerformanceIds.add("illustrated-knowledge-base-curate-connect-reference-v1");
  characterPerformanceIds.add("illustrated-gateway-admit-route-mediate-v1");
  characterPerformanceIds.add("illustrated-container-package-isolate-run-v1");
  characterPerformanceIds.add("illustrated-developer-code-build-deliver-v1");
  characterPerformanceIds.add("illustrated-agent-team-coordinate-delegate-synthesize-v1");
  characterPerformanceIds.add("illustrated-assistant-listen-guide-respond-v1");
  characterPerformanceIds.add("illustrated-human-reviewer-inspect-decide-annotate-v1");
  characterPerformanceIds.add("illustrated-llm-context-transform-generate-v1");
  characterPerformanceIds.add("illustrated-reasoning-premise-infer-conclude-v1");
  characterPerformanceIds.add("illustrated-neural-network-connect-activate-propagate-v1");
  characterPerformanceIds.add("illustrated-embedding-vectorize-position-compare-v1");
  characterPerformanceIds.add("illustrated-token-count-budget-consume-v1");
  characterPerformanceIds.add("illustrated-data-warehouse-land-organize-serve-v1");
  characterPerformanceIds.add("illustrated-document-store-ingest-index-retrieve-v1");
  characterPerformanceIds.add("illustrated-dataset-structure-filter-analyze-v1");
  characterPerformanceIds.add("illustrated-document-author-read-reference-v1");
  characterPerformanceIds.add("illustrated-pdf-package-preserve-share-v1");
  characterPerformanceIds.add("illustrated-image-capture-compose-display-v1");
  characterPerformanceIds.add("illustrated-audio-record-process-play-v1");
  characterPerformanceIds.add("illustrated-video-capture-sequence-play-v1");
  characterPerformanceIds.add("illustrated-code-file-author-validate-reuse-v1");
  characterPerformanceIds.add("illustrated-webhook-hook-receive-trigger-v1");
  characterPerformanceIds.add("illustrated-http-request-compose-send-receive-v1");
  characterPerformanceIds.add("illustrated-load-balancer-distribute-balance-serve-v1");
  characterPerformanceIds.add("illustrated-server-cluster-group-coordinate-scale-v1");
  characterPerformanceIds.add("illustrated-function-bind-execute-return-v1");
  characterPerformanceIds.add("illustrated-edge-node-sense-compute-relay-v1");
  characterPerformanceIds.add("illustrated-source-code-author-organize-build-v1");
  characterPerformanceIds.add("illustrated-git-repository-store-version-share-v1");
  characterPerformanceIds.add("illustrated-branch-diverge-develop-rejoin-v1");
  characterPerformanceIds.add("illustrated-pull-request-propose-review-merge-v1");
  characterPerformanceIds.add("illustrated-ci-cd-build-test-deliver-v1");
  characterPerformanceIds.add("illustrated-deployment-release-place-activate-v1");
  characterPerformanceIds.add("illustrated-task-define-execute-complete-v1");
  characterPerformanceIds.add("illustrated-scheduler-plan-trigger-repeat-v1");
  characterPerformanceIds.add("illustrated-monitoring-observe-detect-report-v1");
  characterPerformanceIds.add("illustrated-logs-record-order-inspect-v1");
  characterPerformanceIds.add("illustrated-alert-detect-escalate-acknowledge-v1");
  characterPerformanceIds.add("illustrated-debug-reproduce-inspect-fix-v1");

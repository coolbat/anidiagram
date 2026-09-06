# Architecture accuracy loop: implementation and acceptance

Scope approved on 2026-09-06: implement the first three follow-ups from the
independent Archify/AniDiagram pilot, then commit and push. External repository
benchmark expansion is a later step; no production deployment is requested.

## Compatibility and implementation order

Baseline: `dabea298f03d8f36c5939c9aaceafa2030bab586`, clean `main`, seven existing
related commits ahead of origin. Preserve the existing Plan/Script schemas,
default renderer bytes, quality outcomes, runtime scheduling and release assets.
All new behavior is additive and explicitly enabled. No Archify dependency.

1. **Independent regressions and source-fact preflight.** A sidecar facts file
   binds stable node/relation IDs to predicates, objects, conditions and existing
   repository sources. An independent `accuracy-check` command checks pinned
   Python definition locations and diagram relation fields. Behavioral meaning
   requires a separate review record bound to exact input/facts hashes; references
   alone never count as semantic proof. Unknowns remain unknown. `--strict`
   blocks contradicted or unresolved required claims. The review record is an
   attributable assertion, not a cryptographic proof of human/agent independence.
   Acceptance: wrong module, reversed/changed relation, unsupported behavior,
   stale review, malformed input and dirty-worktree substitution are rejected.
2. **Optional readable labels.** `--readable-labels` sets
   `edge.label_placement=avoid-nodes` on the effective style. Place full labels
   away from nodes/other labels, retain arrows and geometry, and report inability
   to place text as a quality error rather than silently omit it. HTML includes
   a visible relation table with IDs, direction, kind, condition and protocol.
   Acceptance: independent minimal fixtures and all six pilot overlaps fixed;
   old defaults and the 21-case hash snapshot unchanged.
3. **Real rendered acceptance.** Extend optional `visual-check --strict-labels`
   to inspect actual label visibility, node/label collisions and arrow markers.
   Keep reference verification, semantic review and rendered readability as
   distinct results; browser capture still does not imply semantic approval.
   Acceptance: frozen old counterexamples fail, new readable outputs pass,
   browser errors/hidden labels cannot produce a pass, and missing tools skip.

Each slice has focused RED/GREEN tests and compatibility checks. Commit the
coupled opt-in command/rendering contract together, then its CI/docs checkpoint.
Final checkpoint: full Python suite, Node tests, schema validation,
56-asset strict gate, Illustrated rest/reduced-motion/mode gates, wheel smoke
outside checkout, before/after screenshot review, then non-force push and remote
SHA/CI verification. Do not rewrite historical pilot output or approved galleries.

## Limits

Python AST checks only definition identity/location at a pinned blob; they do
not establish dynamic call reachability, arbitrary control-flow meaning or
whether a label truthfully summarizes behavior. Independent reviewers can also
be wrong. The benchmark must retain real source-backed oracles and distinguish
incorrect facts, missing facts, unknowns and information lost in rendering.

## Progress

- [x] Read current code, rules and prior evidence; verify clean source and remote.
- [x] Independent regressions and facts preflight.
- [x] Optional label placement and relation table.
- [x] Strict real-browser readability checks.
- [x] Full local verification and implementation commit. Push / CI status is
      recorded by Git and GitHub, not asserted in advance by this checklist.

## 使用：先核对事实，再验收呈现

三个命令可以独立运行。`accuracy-check` 不会自动修正语义，也不会成为旧版
`--deliver` 的隐式前置条件；需要准确性门禁的工作流应显式串联：

```bash
anidiagram accuracy-check input.diagram.json --facts facts.json \
  --review review.json --repo-root /path/to/local/repo \
  --strict --out outputs/accuracy.json &&
anidiagram --spec input.diagram.json --repo-root /path/to/local/repo \
  --readable-labels --formats svg,html,quality --outdir outputs/result \
  --runtime-dependency inline --runtime-source node_modules/gsap/dist/gsap.min.js \
  --deliver &&
anidiagram visual-check outputs/result/diagram.html --strict-labels
```

只有已提供事实的必选项全部得到支持，第一步严格检查才通过。未列出的事实、
遗漏的模块、整体架构完整性不在自动证明范围内：`coverage.completeness` 始终
为 `not-assessed`。`ready` 不等于“项目理解 100% 准确”。不能把自己生成的 facts
再与自己的图匹配，当作独立语义证据。

### facts.json

复用图里的节点 / `semantic_relation_id` 和已经绑定的 repository source ID。
固定 Git SHA、仓库身份、文件和行号仍由原证据检查器核验；不执行目标项目。

```json
{
  "version": "0.1",
  "claims": [
    {
      "id": "dispatch-owner",
      "subject": "cli",
      "predicate": "python-definition",
      "object": {"path": "src/cli.py", "symbol": "dispatch"},
      "condition": "",
      "source_refs": ["cli-source"],
      "confidence": "asserted",
      "required": true
    },
    {
      "id": "render-gate",
      "subject": "render-call",
      "predicate": "relation",
      "object": {"from": "delivery", "to": "renderer", "direction": "forward", "kind": "function-call"},
      "condition": "quality.summary.errors == 0",
      "source_refs": ["delivery-source"]
    }
  ]
}
```

- `python-definition`：仅检查词法定义及其文件归属；类方法用 `Class.method`。
  引用必须覆盖定义行，或省略行号引用完整文件。纯文件名节点标签若指向另一个
  文件会被拒绝；一般描述性标签不能靠 AST 判真。此 predicate 的 condition 必须为空。
- `relation`：比较端点、方向、kind 和 condition；字段匹配仍是 `pending`，
  因为不能据此证明源码真的调用、返回或传输了数据。
- `behavior`：object 是非空文字描述，源码含义需要独立复核；引用存在不足以通过。
- `confidence: unknown` 保留未知，缺少引用也可以登记；未知的必选事实阻断严格检查。
  `required` 默认 true，不能悄悄把关键遗漏降为非必选。

非严格模式的 `ok` 只代表没有已知矛盾；务必查看 `ready`、逐条 verdict 和三个 gates。
退出码：0 检查通过，1 存在矛盾（严格模式也包含未解决必选项），2 输入无效，
3 报告事务写入失败。输出不能覆盖输入、事实清单或复核记录。

### review.json

复核者直接阅读固定版本源码，记录理由及证据。先不带 `--review` 运行检查，
取得输出中的两个 SHA-256，然后独立编写：

```json
{
  "version": "0.1",
  "reviewer": "reviewer identity",
  "specification_sha256": "<from accuracy-check>",
  "facts_sha256": "<from accuracy-check>",
  "decisions": [
    {
      "claim_id": "render-gate",
      "verdict": "supported",
      "rationale": "Explain the exact source branch and why rendering is reachable only after the gate.",
      "source_refs": ["delivery-source"]
    }
  ]
}
```

verdict 为 supported / contradicted / unknown。哈希绑定规范化 JSON；Plan 输入绑定
其编译后的 Script。更改图、条件或事实后，旧复核记录失效。复核记录不能覆盖
机械检查发现的矛盾。这个记录不是身份签名，不保证复核者独立或判断正确；
报告明确标为 `recorded-not-proof`，不是模型评分器。

### 可读标签和浏览器门禁

`--readable-labels` 只支持 svg / html / viewer / quality；暂不承诺其他导出格式。
直接 Python 调用可设置 `style['edge']['label_placement']='avoid-nodes'`。
完整标签沿实际路径选择位置、避让节点和其他标签，并用细虚线指引；无法放下
保留全文并产生 `label_unplaced` error。`--deliver` 此时不覆盖之前的正常产物。

HTML 采用原尺寸可滚动画布，避免为了塞进一屏而把文字缩得过小；下方可滚动表格
保留全部关系、方向、类型、条件和协议。截图可能只包含图的一部分，可用滚动条、
键盘和既有缩放控件阅读。没有改变底层拓扑、边路径、动效调度或旧模式的 fit 行为。

`visual-check --strict-labels` 检查真实字体布局、全文保留、节点/标签重叠、字体过小
（屏幕文字框高度低于 10 px）、路径端点和箭头 marker，以及表格字段。新画布允许
明确标注的可滚动区域，报告 `stage_scroll_reachable`，不冒充整图首屏可见。
源码引用显示的是生成时的状态；浏览器检查不重新核验仓库，不裁决语义，
`visual_review` 仍为 pending。完整的动态视觉评审、颜色对比度等不在此门禁范围。

旧 HTML 没有完整期望值元数据，严格检查返回 unavailable 并以失败退出；
它不能从被清空的 SVG 文本反推原标签。独立回归脚本另读原始 Script，负责验证旧反例。
无 Node / Playwright / Chromium 时为 skipped（非通过），退出码 2。

## 可复现测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 scripts/verify_accuracy_loop.py --outdir build/ci/accuracy
PYTHONPATH=src python3 scripts/check_compatibility_snapshot.py tests/compatibility-baseline-18cb0f3.json
```

浏览器需要项目的 `npm ci`、`npx playwright install chromium`，中文测试在 Linux
需要 Noto CJK 字体。CI 已加入相同门禁，无需临时目录中的历史对照文件。
`tests/fixtures/accuracy/delivery_truth.json` 的四类真假事实由独立的小型源码及其
执行测试支撑；该文件是人工 oracle，不是可以直接传给 `--facts` 的输入格式。

固定 pilot 的旧文件保持不动，新产物另存 `outputs/accuracy-study/accuracy-loop/`。
外部仓库、多次独立运行、盲评和遗漏率统计仍是下一轮评测，不在本次准确率结论中。

## 本次本地验收记录（2026-09-06）

- Python 全套：354 项通过；旧版兼容快照：21 / 21 字节一致。
- 独立浏览器 oracle：4 个正例通过，3 个旧版反例按预期失败。
- 严格浏览器门禁：4 个正例 + 9 个注入错误反例均得到预期结果；14 份严格
  visual receipts 通过独立 JSON Schema 校验。
- 固定 pilot：同一份 Script 的 22 条边，原 SVG 有 6 处标签-节点重叠及 1 处
  标签-标签重叠；新 SVG 为 0。新 HTML 的四尺寸 × 两配色偏好全部通过严格检查。
- Diagram Core：56 个 approved assets 严格校验无错误 / 警告；提交画廊体积预算通过。
- Illustrated：56 图标展示和 13 节点真实案例的 rest / reduced-motion / mode
  门禁通过；没有重写已提交的画廊资源。
- 独立 wheel：仓库外运行 28 项相关测试，安装版 CLI 渲染 / 事务交付 / 严格
  浏览器验收通过。Playwright 从明确指定的项目开发依赖提供，不是 Python 运行时依赖。
- 原阅读器 Node 图算法 2 项通过；公开阅读契约的 23 个文档 / 15 个 schema
  通过独立 Draft202012Validator 校验。

这些结果是本地验收证据，不代表远端 CI、生产部署或跨项目准确率。

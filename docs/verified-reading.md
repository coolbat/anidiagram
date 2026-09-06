# 源码证据、架构比较与阅读器

这些能力是 DiagramPlan 0.2 / DiagramScript 0.4 的可选扩展。
旧计划、旧图和默认 CLI 参数保持原行为。所有示例都复用现有编译器、
图标、动效和交付事务；无需安装 Archify。

事实预检、可读标签和严格浏览器验收见 [准确性闭环](accuracy-loop.md)。
引用存在、语义成立、信息完整呈现是三个不同的检查结果。

## 源码引用核验

在既有 `semantic.sources` 中加入 `repository`，实体继续用 `source_refs`
引用 source ID：

```json
{
  "id": "renderer-source",
  "type": "repository",
  "title": "HTML renderer",
  "repository": {
    "url": "https://github.com/coolbat/anidiagram",
    "revision": "18cb0f35e41f907210852de5ca0edbe9adcc2970",
    "path": "src/anidiagram/renderer_html_runtime.py",
    "line": 1
  }
}
```

`end_line` 可选。核验读取固定提交的 Git blob，不读取工作区中的未提交修改。
仓库 origin、完整提交 SHA、普通文件、行号范围都会核验；符号链接、子模块、
路径越界和超过 8 MiB 的源码文件会被拒绝。当前仓库 URL 支持 GitHub HTTPS；
一个产物使用一个本地仓库。不会自动 fetch，也不会执行被分析仓库的代码。

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --plan examples/verified-reading/repository-reader.plan.json \
  --repo-root . \
  --outdir outputs/verified-reading \
  --basename repository-reader \
  --formats svg,html,quality \
  --deliver
```

HTML 显示固定版本的源码链接，delivery receipt 增加 `evidence`。
每个 source 记录 blob ID、SHA-256 和字节数。`references-verified` 只证明
引用的文件和行号存在，架构含义仍需人工审查。普通 `uri/note` 来源保持原用法，
没有 `repository` 就不要求 Git。手工 Script 中的证据也会重新核验，不能通过
写入 `verified: true` 跳过检查。缺失本地 revision 时需先准备对应提交。

Python API：`compile_scene(spec, repo_root=repository_path)`。

## 语义比较

```bash
anidiagram compare old.plan.json new.plan.json \
  --out outputs/review/delta.html --json
```

输入要求 Plan 0.2。稳定 ID 用于区分新增、删除和字段变化；集合排序不产生
虚假的语义变化。flow 的 `relation_ids` 保留顺序，不作集合排序。
报告分别记录 `semantic_changes`、`presentation_changes`、`geometry_changes`，
并细分 topology、scope、evidence 等类别。样式变化不会被报为系统语义变化。

Before / Delta / After 页面和 `.comparison.json` 在同目录一起提交，失败时回滚。
两个输入都需通过 schema 和 quality error 门禁；源文件不可作为输出路径。
带仓库来源的输入同样需要 `--repo-root`。比较不会修改原计划或自动推断变更。

## 阅读器与章节

CLI 加 `--reader`，或在 Plan 顶层写入：

```json
{
  "reader": {
    "enabled": true,
    "views": [
      {
        "id": "request",
        "label": "请求路径",
        "relation_ids": ["client-request", "ingress-route"]
      }
    ]
  }
}
```

阅读器提供节点搜索、角色筛选、邻接查询、上游/下游、最短有向路径和可复制的
阅读链接。双向边支持两方向遍历；无向边仅参与邻接查询，避免被解读为依赖方向。
点击节点与键盘可访问的下拉菜单都能选择起点。没有路径时明确显示空结果。

`views` 最多五章，每章可引用 `node_ids`、`relation_ids`，必须至少选择一个对象。
关系端点会自然包含在该章中。章节切换不创造边、不修改调度器，也不会自动播放。
选中状态的样式位于 SVG 外部；原 SVG 下载、打印和常规导出不包含阅读高亮。
首次展开和改变视口时只缩放阅读面板的显示尺寸，原 viewBox 与语义几何不变。

分享卡支持 SVG 和 1200×630 PNG，显示选中节点、实际关系方向和 graph SHA-256。
最多 8 个节点、8 条关系；超量或文字无法完整排版时拒绝导出并提示缩小选择。
卡片是选择摘要，不是截图；SVG metadata 保留该选择的完整节点与关系数据。

## 类型语义

继续使用 `semantic.intent.diagram_kind`。只有添加 `semantic.type_details`
才开启类型约束，已有自由形式 kind 和布局不会被自动替换。

| kind | type_details | 检查 |
| --- | --- | --- |
| sequence | participants、messages、activations | 消息顺序、同步/异步/返回模式、返回对应的先前调用、激活区间 |
| lifecycle | initial、terminal、recovery_relations | 终止状态无出边、终态可达、真实失败状态恢复关系 |
| dataflow | datasets、transformations | 转换输入/输出确实连接数据集且方向正确 |
| workflow | approvals | 批准/拒绝引用不同出边，条件存在且不同 |
| architecture | ownership、trust_boundaries、crossings | 分组归属、真实边界跨越关系和明确机制 |

所有字段引用既有实体、关系和分组 ID。编译后的 `type_semantics` 在 Scene 边界
重新校验，SVG metadata 保留语义，HTML 提供可读的类型说明；时序消息编号按
显式顺序编译。此阶段提供语义约束和说明，并未新增独立 UML lifeline 渲染器。
五类可运行示例位于 `examples/verified-reading/`，包含虚构示例的范围说明。

## 视觉证据

```bash
anidiagram visual-check outputs/verified-reading/repository-reader.html --json
```

命令冻结输入 HTML，在 1440×900、1600×1000、1920×1080、2048×1320 捕获
light/dark 浏览器配色偏好截图。它保留图的 authored style，所以两种偏好下
截图可能相同；这不是新增明暗主题。Node.js 与 Playwright/Chromium 是该命令
的可选开发依赖，普通渲染不依赖它们。

输出 `.visual.json`、`.visual.html` 联系表和 8 张 PNG。检查文档溢出、舞台裁切、
页面错误，并记录运行时/GSAP 可用性。捕获使用减少动效模式，不代替动态行为测试。
自动 receipt 始终写 `visual_review: pending`；退出码 0 代表包含性和捕获通过，
1 代表失败，2 代表工具缺失而跳过。命令不会重新渲染或改写源 HTML。
`--viewports` 可指定一到八个尺寸，`--outdir` 可改变 sidecar 目录。

## 复现与回归

```bash
PYTHONPATH=src python3 scripts/build_verified_reading_proofs.py
node --test tests/reader-graph.test.cjs
node scripts/verify_reader_sharing.mjs outputs/archify-followups/repository-reader.html
PYTHONPATH=src python3 scripts/verify_visual_check.py
PYTHONPATH=src python3 -m unittest discover -s tests
```

生成真实源码样例需要本地保留固定提交；CI 使用显式标记为测试数据的 reader
fixture，Git 正向/反向核验由隔离 Git 测试仓库覆盖。JSON Schema 的独立验证
脚本为 `scripts/verify_reading_schemas.py`，开发环境需安装 `jsonschema` 4.x。

兼容性快照可先在改动前用 `scripts/check_compatibility_snapshot.py <path> --record`
记录，再在改动后用相同命令去掉 `--record` 检查。它覆盖 16 个 preset、
已有测试 fixture、生产请求示例、中文图和 Illustrated 2.5 showcase。

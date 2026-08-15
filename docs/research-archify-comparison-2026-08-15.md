# Archify 与 AniDiagram 源码对照及调优结论

观察日期：2026-08-15（Asia/Shanghai）

## 结论

Archify 适合作为 **交付、验证和阅读交互的架构参考**，不适合作为
AniDiagram 的直接依赖或替代内核。两者都使用 typed IR、确定性渲染、自包含
HTML 和机器校验，但产品重心不同：

- Archify 是面向技术系统图的「可验证阅读器」，强项是精确关系探索、源码证据、
  架构差异和原子交付；
- AniDiagram 是面向语义动画图的「编译与导出引擎」，强项是统一语义层、16 种
  布局、13 种风格、56 枚结构化插画图标、角色级动作和多格式动画导出。

本轮采用 `architecture-reference`：借鉴 Archify 的可操作诊断设计，用
AniDiagram 自己的质量契约实现；不复制 Archify 的渲染器、模板或运行时。

## 复现证据

### Archify

- 仓库：<https://github.com/tt-a1i/archify>
- 检查提交：`cffdd42eed0ebf013aa070378d94facdd3d56b10`
- 包版本：`2.14.0`
- 许可：MIT
- 运行时：Node.js `>=18`
- 包边界：主 Skill 在 `archify/`；零安装 CLI 可直接运行；开发依赖只有 AJV，
  `package.json` 没有 install/postinstall 生命周期脚本。
- CI：Node 18 / 20 / 22 / 24，另有 WebM、跨平台包验收、ZIP 新鲜度和发布门禁。
- 测试：首次受限运行中 628 项有 11 项因沙箱禁止监听 `127.0.0.1` 而失败；
  允许 loopback 后同一套测试退出 0，原 11 项全部通过。
- 实际交付：`outputs/archify-evaluation/anidiagram-runtime.html`
- Showcase 校验：9 / 9，0 errors，0 warnings。
- 视觉检查：1440×900、1600×1000、1920×1080、2048×1320 均无横向或纵向
  溢出；明暗主题截图均已人工查看。

### AniDiagram

- 仓库：<https://github.com/coolbat/anidiagram>
- 对照基线：`3d26d31b385007c66cd0d1f9d1b9bc826cb46680`
- 核心契约：DiagramPlan 0.2 → DiagramScript 0.4 → Scene → SVG / HTML / export / quality。
- 当前表面：16 种布局、13 种公开风格、Illustrated 2.5.0 的 56 枚图标和
  10 类交付格式。
- 最终验证：Diagram Core 56 / 56，0 errors，0 warnings；Python 全量测试
  302 / 302。
- 对照产物：
  `outputs/archify-evaluation/anidiagram-native/production-request-path.html`，质量
  100 分、0 errors、0 warnings，并通过新增 advisory 暴露 3 个短关系标签问题。

## 架构与能力对照

| 维度 | Archify | AniDiagram | 判断 |
| --- | --- | --- | --- |
| 产品中心 | 技术架构图的验证、阅读、评审 | 通用语义动画图编译与多格式交付 | 保持各自定位 |
| 输入 IR | architecture / workflow / sequence / dataflow / lifecycle 五套 schema | 一个语义 DiagramPlan 与统一 DiagramScript | 不引入五套平行内核 |
| 布局 | Agent 主导显式布局，强 artifact geometry gate | 16 种确定性语义布局，可继续手工 geometry | 互补 |
| 视觉 | 4 个 preset、轻量 semantic sigil | 13 种 style、Diagram Core 与 56 枚 Illustrated | AniDiagram 更强 |
| 动效 | 有限 trace 与阅读者触发的路径/故事动画 | 图标部件动作、edge-motion、三种调度模式和动画导出 | AniDiagram 更强 |
| 阅读交互 | Finder、Upstream/Downstream、Route、Lens、Story、Presentation、Share Card | 播放模式、缩放、下载、语义动画控制 | Archify 明显更强 |
| 交付 | validate → atomic deliver → hash receipt → visual-check；last-good preview | 直接写各格式与 quality，另有 release evidence | 优先补交付事务性 |
| 证据 | Git revision 校验的源码跳转；Architecture Delta | DiagramPlan source provenance；无源码打开和 delta 产品面 | 分阶段借鉴 |
| 质量诊断 | 稳定 rule、subject、evidence、supported fixes | 原先只有 code/path/message | 本轮已补第一阶段 |
| 发布 | 零依赖 Skill ZIP，单文件 HTML 为主 | Python wheel + npm runtime + gallery，多格式输出 | 不统一分发模型 |

## 本轮已实施的针对性调整

### 1. 可操作质量诊断

`QualityIssue` 保留原有 `code`、`severity`、`path`、`message`，新增：

- `subject`：稳定的节点或关系身份；
- `evidence`：矩形、交叠尺寸、路径线段、可用宽度与所需宽度等测量事实；
- `supported_fixes`：受支持的局部修复动作 ID。

既有调用者仍可使用旧字段和 `summary`，新增字段是向后兼容扩展。

### 2. 线段穿节点检测

旧实现只在显式路径的某个 waypoint 落入节点时告警，因此两个 waypoint 都在
节点外、但中间线段穿过节点的情况会漏检。新实现增加有限线段与矩形相交检测，
并返回第一条相交 segment 和 blocking node。

为了不把既有发布图一次性全部变成 warning，新增的 segment-only 发现先进入
非阻断 `advisories`；原有 waypoint 进入节点的情况继续进入 `issues`。

### 3. 关系标签静默隐藏可见化

短直线关系上，旧渲染器会为了可读性省略放不下的标签。新质量报告将此事实记录
为 `edge_label_hidden` advisory，包含 `available_width` 和 `required_width`，但不改变
`ok`、`score` 或旧的 errors/warnings summary。

这让我们可以在不破坏现有 302 项测试和发布物的前提下，逐步清理历史布局。

## 本轮继续实施

### P1：原子交付与确定性回执（已完成）

CLI 新增 `--deliver`：源输入只读取一次，已解析 DiagramScript 与 style 在内存中
冻结；所有请求格式先写入目标目录内的私有暂存目录。质量 error、导出器 skipped、
文件缺失或空文件都会在公开目标被触碰前阻断。提交阶段使用同目录 `os.replace`
和逐项备份；中途失败会回滚所有目标并保留 last-good。

成功后生成 `AniDiagramDeliveryReceipt` v0.1，记录 source、resolved spec、style 与
各产物的 SHA-256 / bytes。`--plan-out`、`--spec-out` 位于 `--outdir` 时也参与同一
事务。若操作系统同时拒绝回滚，错误会暴露 recovery path，并保留私有备份，避免
清理过程销毁最后的恢复副本。

真实 production request 样例已通过该链路提交 SVG、HTML、quality 与 compiled
spec；回执质量为 100 分、0 errors、0 warnings、3 advisories，回执中的 4 个产物
SHA-256 均与磁盘文件逐项一致。

## 后续优先级

### P1：把 advisory 纳入新布局的验收

旧图继续兼容；新建 composition-v1 图可增加严格模式，要求
`edge_segment_node_collision` 与 `edge_label_hidden` 为零。先修 layout compiler，
不要靠删除关系标签或隐藏 overflow 过门禁。

### P2：语义阅读器

基于 DiagramPlan 已有稳定 entity / relation / flow ID，先实现 Node Finder、单节点
upstream/downstream 和两点 route。查询必须只使用 authored topology，且交互态不得
污染 SVG、打印或导出。

### P2：多视口视觉检查

把当前分散的 Playwright gate 统一成一个 HTML sidecar receipt：记录固定 viewport、
明暗主题、overflow、截图路径和 artifact hash；自动检查仍不得宣称人工视觉通过。

### P3：源码证据与架构 Delta

仅在用户明确要求“基于仓库事实”时启用 revision-pinned source refs。Architecture
Delta 先只比较语义实体/关系/分组，视觉位置变化单列，避免把布局改动误报为系统
变化。

## 明确不采用

- 不把 Archify 的五套 schema 复制到 AniDiagram；这会削弱统一语义层。
- 不引入 Archify 的大体积 HTML 模板或阅读运行时作为依赖；本次 Archify 产物约
  641 KB，且会与现有 HTML runtime 形成双重状态所有者。
- 不用 Archify 替换 Illustrated、Motion Manifest、Edge Motion 或浏览器导出链路。
- 不因 GitHub 热度直接采用；stars/forks 只代表关注度，不代表与当前架构契合。

## 验证命令

```bash
PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --strict --json
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m anidiagram.cli \
  --plan examples/contracts/production-request-path.plan.json \
  --spec-out outputs/archify-evaluation/anidiagram-native/production-request-path.diagram.json \
  --outdir outputs/archify-evaluation/anidiagram-native \
  --basename production-request-path \
  --formats svg,html,quality \
  --deliver
```

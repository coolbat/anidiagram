# AniDiagram 产品宣传片 · 脚本 v2

状态：脚本草案，待确认后进入分镜与制作。
v2 依据确认的方向：约 90 秒单一版本、无旁白、英文、深色 Deep Tech 基调。

## 基本参数

| 项目 | 决定 |
| --- | --- |
| 时长 | 94 秒（成片），只做一个版本 |
| 画幅 | 16:9，1920×1080，30fps |
| 语言 | 英文屏幕文字，无旁白 |
| 声音 | 纯音乐驱动：低频电子氛围，约 110 BPM，场景切换卡在重拍上；数据包流动、格式扇出、检查通过处加轻量音效 |
| 视觉基调 | 深色底 `#0B1220` 一类的 Deep Tech 色系，青色/蓝色强调；案例画面统一使用 deep-tech 或 dark 变体 |
| 观众 | 平台工程师、技术作者、需要讲清系统的团队 |
| 核心设定 | **片中每一张架构图都由 AniDiagram 生成**，片尾点明 |

### 无旁白的文字规则

没有旁白，屏幕文字承担全部叙事：

- 主标题每张不超过 8 个英文单词，停留至少 2 秒（约每秒 2.5 个词的阅读速度）。
- 同一时刻画面上最多一个主标题 + 一行小字说明。
- 字体：标题用几何无衬线体（如 Inter Display / Space Grotesk），代码与命令用等宽字体（如JetBrains Mono）。
- 文字入场跟随音乐节拍，不使用逐字打字机效果（命令行除外）。

### 表述边界（制作时必须遵守）

- 不出现 "understands any codebase"、"100% accurate" 一类说法。
- 案例画面角标统一写：`Source-backed reading · not an official architecture`。
- `--text` 表述为 draft（草稿）；规则不认识的句子进入诊断，不会被猜成连线。
- “检查通过不等于架构语义已被证明”在第 10 场正面出现一次，作为可信度卖点。

---

## 分场脚本

时间码按音乐小节对齐（成片配乐 120 BPM，一小节 2 秒，代码合成），以下为成片实际时间。

### 场 1 · 冷开场（0:00–0:06）

**画面**：一张灰色、低保真的方框连线图，箭头交错，镜头缓慢推近。文件名标签 `architecture_v7_FINAL.png` 在角落闪一下。画面定格、去色。

**屏幕文字**：
> Most architecture diagrams are stale the day they ship.

**音乐**：只有低频铺底，没有节拍。

**素材**：新做（故意做成反差的旧式图，不使用项目产物）。

---

### 场 2 · 片名（0:06–0:12）

**画面**：旧图碎裂成节点，节点在深色背景上重组成 Dify 三层结构（deep-tech 英文版），图标亮起，第一个数据包沿连线跑过。片名在图上方浮现。

**屏幕文字**：
> **AniDiagram**
> Architecture diagrams that explain, move, and ship.

**音乐**：第一拍鼓点进入，正好落在数据包出发的瞬间。

**素材**：`assets/readme/hero.svg`（版式参考）、`gallery/cases/dify/dify-deep-tech-en-motion.webp`。

---

### 场 3 · 工作原理（0:12–0:20）

**画面**：`workflow.svg` 五个阶段从左到右随节拍逐个点亮。随后画面上下分成两条轨道：上轨是实体、关系、分组、流程；下轨是图标、风格、布局、动效，中间一道青色分隔线。底部滑出合约链。

**屏幕文字**（两张，依次出现）：
> Meaning first. Look second.

> `DiagramPlan 0.2 → DiagramScript 0.4 → SVG · HTML · quality`

**素材**：`assets/readme/workflow.svg`；双轨动画新做。

---

### 场 4 · 三种开始方式（0:20–0:30）

画面分三栏，每栏依次点亮约 3.5 秒，最后三栏同时可见。

| 栏 | 画面 | 栏顶文字 |
| --- | --- | --- |
| 4a | 终端输入 `npx skills add coolbat/anidiagram --skill anidiagram`，Agent 对话框出现提示 “Map this project's core request path, with source evidence”，右侧生成图 | **Ask your agent** |
| 4b | 终端运行 `anidiagram --text "Gateway calls Orders; Orders publishes to a queue, which notifies Shipping; Billing might audit Orders." --planner rules ...`，图滑入（Gateway → Orders → queue → Shipping），底部闪过诊断：未解析片段 `Billing might audit Orders`，覆盖率 2/3 | **Write one sentence** |
| 4c | `production-request-path.plan.json` 在左侧滚动，右侧渲染为交互图，文件树弹出 `.svg .html .quality.json .delivery.json` | **Edit an explicit plan** |

**场末小字**：
> Unknown phrases become diagnostics — never guessed edges.

**素材**：终端与 Agent 录屏需新录（现场生成 `outputs/quickstart`、`outputs/brief`）；4c 右侧复用 `gallery/narration/production-request.html`。4b 的句子已实测：得到 4 个节点、3 条关系，`Billing might audit Orders` 进入未解析诊断。注意必须用 `, which`；写成 `that` 会把 “queue that notifies Shipping” 合并成一个节点。

---

### 场 5 · 主案例：Dify（0:30–0:44）

**画面**：
1. Dify 三层图（deep-tech 英文版）全屏，角标 `Dify 1.17.0 · Source-backed reading · not an official architecture`。
2. 高亮 “document ingestion” 链路，其余变暗：上传 → Celery 索引任务 → 文件 / SQL / 向量索引。
3. 切换高亮 “chat answer” 链路：请求 → API 进程内的问答线程 → 检索 → Plugin Daemon HTTP 边界。
4. 侧边弹出一张源码引用卡片（文件路径 + 行号），计数器滚到 `32 source references`。

**屏幕文字**（三张，依次出现）：
> How does a document become an answer?

> Ingestion runs in Celery. Chat runs in the API process.

> Every edge traces back to pinned source lines.

**素材**：`gallery/cases/dify/index.deep-tech.en.html`、`dify-deep-tech-en.html`（交互聚焦章节）、`evidence.en.md`。用 Playwright 按固定时间点截帧录制。

---

### 场 6 · 更多真实项目（0:44–0:52）

**画面**：三张卡片随节拍依次横滑入画，每张播放自身动效约 2 秒，最后三张缩小排成一行。

| 卡片 | 卡片标题 |
| --- | --- |
| n8n（deep-tech 英文版） | One webhook, three layers |
| Langfuse（英文版） | From an AI call to a queryable trace |
| Open WebUI（英文版，深色） | One chat UI, two model paths |

**屏幕文字**：
> One question per diagram. Scope stated, gaps named.

**素材**：`outputs/readme-showcase-v2/n8n/n8n-deep-tech-en-motion.webp`、`langfuse/langfuse-en-motion.webp`、`open-webui/open-webui-en.visual.1920x1080-dark.png`。Open WebUI 卡片标题需按该案例实际讲的问题核对后再定稿。

---

### 场 7 · 视觉系统（0:52–1:02）

**画面**：
1. 风格墙：同一张图以 12 种风格平铺，从中心向外随节拍逐格点亮。
2. 硬切到布局墙：16 种布局，每格带轻微动效。
3. 硬切到两套图标系统左右对比：左侧 Illustrated 2.5 的 56 枚图标逐个弹入且部件在动；右侧 diagram-core-v1 线框图标。

**屏幕文字**（随三段画面依次出现）：
> 12 styles

> 16 semantic layouts

> 2 icon languages · same meaning

**素材**：`gallery/styles/*.svg`、`gallery/layouts/*.svg`、`gallery/icon-systems/illustrated-2.5.html`、`diagram-core-v1.html`。

---

### 场 8 · 动效与引导讲解（1:02–1:12）

**画面**：
1. 特写：离散请求是一个个跳动的 packet，持续数据流是不断流动的 stream-flow；图标部件在动（服务器灯闪、齿轮转）。
2. 播放 `explanation.mp4`：点击 “Start Explanation”，Step 1/3 HTTPS → Step 2 → Step 3 依次推进。
3. 工具栏依次切换 Expressive → Readable → Off，画面动效逐级收敛到静止。
4. 阅读工具：搜索一个节点，高亮它的上下游，再显示两点之间的最短路径。

**屏幕文字**：
> Packets for requests. Streams for flows.

> Press play. The diagram walks you through it.

> Expressive · Readable · Off — reduced motion respected.

**素材**：`gallery/runtime-motion.html`、`gallery/narration/explanation.mp4`（直接复用；其界面为浅色，放进深色设备框中展示）、`examples/verified-reading/` 的阅读工具录屏。

---

### 场 9 · 多格式交付（1:12–1:18）

**画面**：中心一张图，随节拍向四周扇形“发射”格式卡片：SVG、HTML、PNG、PDF、GIF、WebP、APNG、MP4、Lottie、quality.json。最后一帧闪过同一张图的中文版，提示中英文原生支持。

**屏幕文字**：
> One source. Every format.

> English and Chinese, natively.

**素材**：`gallery/previews/agent-runtime-flow.{gif,webp,mp4,apng}`、`gallery/readme-showcase/enterprise-agent-platform-zh.html`。

---

### 场 10 · 质量即交付物（1:18–1:26）

**画面**：
1. 图上叠加检测层：文字适配、节点重叠、路径交叉处依次出现测量框并变绿。
2. `quality.json` 快速滚动，停在 `"errors": 0`。
3. `--deliver` 动画：产物写入私有目录，全部通过后才替换公开文件；演示一次失败，旧的 last-good 产物被恢复。
4. `delivery.json` 中的 SHA-256 逐行出现。
5. 最后一行字缓慢浮现。

**屏幕文字**：
> Quality checks ship with the diagram.

> Fail the gate, keep the last good one.

> Passing geometry ≠ proven architecture. It tells you so.

**素材**：Dify 目录下现成的 `*.quality.json`、`*.delivery.json`；检测叠层与交付流程动画新做。

---

### 场 11 · 收尾（1:26–1:34）

**画面**：全片出现过的图随节拍快速回闪，汇聚成 Dify 主图后淡出。第一行字浮现，停 2 秒；随后切到 CTA 画面，音乐收尾在最后一个重拍。

**屏幕文字**：
> Every diagram in this video was made with AniDiagram.

**CTA 画面**：

```
AniDiagram
npx skills add coolbat/anidiagram --skill anidiagram
coolbat.github.io/anidiagram/gallery
Open source · MIT
```

---

## 素材复用清单

| 场次 | 直接复用 | 需要新录或新做 |
| --- | --- | --- |
| 1 | — | 低保真旧架构图 |
| 2 | `hero.svg`、`dify-deep-tech-en-motion.webp` | 碎裂重组转场 |
| 3 | `workflow.svg` | 双轨分层动画 |
| 4 | `production-request.html` | 终端与 Agent 录屏 3 段 |
| 5 | Dify deep-tech 英文案例页、交互图、证据 | Playwright 定时截帧 |
| 6 | n8n、Langfuse、Open WebUI 英文产物 | 卡片排版 |
| 7 | styles、layouts、icon-systems 全部 SVG | 风格墙、布局墙拼版 |
| 8 | `explanation.mp4`、`runtime-motion.html` | 阅读工具录屏、深色设备框 |
| 9 | `agent-runtime-flow.*` 预览、中文企业智能体图 | 格式扇出动画 |
| 10 | quality、delivery JSON | 检测叠层、交付流程动画 |
| 11 | 全片素材回闪 | CTA 画面 |

## 制作路线（脚本确认后）

1. 用 Playwright 对各案例 HTML 做确定性截帧，得到无浏览器界面的干净素材。
2. 选定配乐并标出节拍点，以节拍表锁定各场时间码。
3. 用 HyperFrames 搭建 11 个场景，统一字体、色板与转场。
4. 逐场截图审阅后，预览确认再渲染 1080p 定稿。


## 成片说明

- 工程：`outputs/promo-video/anidiagram-promo/`（HyperFrames 0.8.139），成片 `renders/anidiagram-promo.mp4`，1920×1080 30fps。
- Langfuse 与 Open WebUI 用各自 `*-en.diagram.json` 以 `deep-tech` 风格重渲染，统一深色画面。
- 配乐由 `tools/make_music.py` 代码合成（无外部素材），响度归一到 -14 LUFS。
- 案例动效由 `tools/capture.mjs` 以 30fps 确定性逐帧录制。

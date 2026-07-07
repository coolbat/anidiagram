# AniDiagram 中文说明

语言：[English](./README.md) | 简体中文

AniDiagram 是一个 clean-room 的 DiagramScript 渲染器，用来生成可动画的架构图、流程图、教学图和产品说明图。

本仓库不是 GitHub fork，也不复制 [REFERENCES.md](./REFERENCES.md) 中列出的参考项目的源码、文档、图片、生成资产或 git 历史。旧项目和外部项目只作为产品方向与功能验证参考。

## Showcase

AniDiagram 的 README 展示分成两套画廊：

- **Style Showcase**：12 个签名案例，每个视觉风格一个，用来回答“它能长成什么气质？”
- **Layout Showcase**：14 个教学案例，每个布局 preset 一个，用来回答“这个布局适合什么场景？”

画廊源文件：`gallery/index.html`
机器可读 manifest：[gallery/showcase_manifest.json](./gallery/showcase_manifest.json)

README 首屏使用从 GSAP runtime 真实录制出来的 animated preview，所以在
GitHub README 里也能直接看到高保真动效。Style / Layout 的大量卡片继续用
轻量 SVG 预览，保证页面足够轻、足够好扫。可交互的 `.html` runtime 页面
需要通过 GitHub Pages 这类静态站点承载，或者用本地静态服务器打开。

### Hero Demo

| Agent Runtime Flow |
| --- |
| [![Agent Runtime Flow](./gallery/previews/agent-runtime-flow.webp)](./gallery/previews/agent-runtime-flow.mp4)<br>从浏览器 runtime 录制的高保真预览，展示 agent think-act、search discover、API request/response、memory commit 动效。<br>[GIF](./gallery/previews/agent-runtime-flow.gif) · [APNG](./gallery/previews/agent-runtime-flow.apng) · Runtime HTML：`gallery/hero/agent-runtime-flow.html` |

本地打开可交互 runtime：

```bash
python3 -m http.server 8765
```

然后访问 `http://127.0.0.1:8765/gallery/hero/agent-runtime-flow.html`。如果用
GitHub Pages 发布，README 按钮应链接到 Pages URL，而不是 GitHub 的 `blob`
源码页。

### Style Showcase

每个内置风格都有一份签名 DiagramScript 案例、SVG 预览、HTML runtime 和 quality report。README 卡片链接到便携 SVG 预览；如果要打开高保真 HTML runtime，需要本地 serve `gallery/`，或启用 GitHub Pages。

| `minimal-light` | `deep-tech` | `blueprint` |
| --- | --- | --- |
| [![minimal-light style showcase](./gallery/styles/minimal-light.svg)](./gallery/styles/minimal-light.svg)<br>Customer Support Triage | [![deep-tech style showcase](./gallery/styles/deep-tech.svg)](./gallery/styles/deep-tech.svg)<br>Realtime AI Ops Mesh | [![blueprint style showcase](./gallery/styles/blueprint.svg)](./gallery/styles/blueprint.svg)<br>MCP Server Architecture |

| `flat-icon` | `dark-terminal` | `notion-clean` |
| --- | --- | --- |
| [![flat-icon style showcase](./gallery/styles/flat-icon.svg)](./gallery/styles/flat-icon.svg)<br>Feature Priority Board | [![dark-terminal style showcase](./gallery/styles/dark-terminal.svg)](./gallery/styles/dark-terminal.svg)<br>Incident Response Runbook | [![notion-clean style showcase](./gallery/styles/notion-clean.svg)](./gallery/styles/notion-clean.svg)<br>Product Discovery Workflow |

| `glassmorphism` | `claude-warm` | `openai-minimal` |
| --- | --- | --- |
| [![glassmorphism style showcase](./gallery/styles/glassmorphism.svg)](./gallery/styles/glassmorphism.svg)<br>AI Growth Funnel | [![claude-warm style showcase](./gallery/styles/claude-warm.svg)](./gallery/styles/claude-warm.svg)<br>Research Reasoning Loop | [![openai-minimal style showcase](./gallery/styles/openai-minimal.svg)](./gallery/styles/openai-minimal.svg)<br>Evaluation Pipeline |

| `dark-luxury` | `aurora-orb` | `sketch-board` |
| --- | --- | --- |
| [![dark-luxury style showcase](./gallery/styles/dark-luxury.svg)](./gallery/styles/dark-luxury.svg)<br>Executive Signal Network | [![aurora-orb style showcase](./gallery/styles/aurora-orb.svg)](./gallery/styles/aurora-orb.svg)<br>Creative Agent Studio | [![sketch-board style showcase](./gallery/styles/sketch-board.svg)](./gallery/styles/sketch-board.svg)<br>Attention Teaching Flow |

完整风格画廊源文件：`gallery/styles/index.html`

### Layout Showcase

每个布局 preset 都有一个具体 AI / 产品案例，用来说明什么时候该用这个布局。

| `pipeline` | `loop` |
| --- | --- |
| [![pipeline layout showcase](./gallery/layouts/pipeline.svg)](./gallery/layouts/pipeline.svg)<br>RAG Ingestion Pipeline | [![loop layout showcase](./gallery/layouts/loop.svg)](./gallery/layouts/loop.svg)<br>Agent Reflection Loop |

| `hub-spoke` | `layered` |
| --- | --- |
| [![hub-spoke layout showcase](./gallery/layouts/hub-spoke.svg)](./gallery/layouts/hub-spoke.svg)<br>Agent Tool Hub | [![layered layout showcase](./gallery/layouts/layered.svg)](./gallery/layouts/layered.svg)<br>LLM App Architecture Layers |

| `swimlane` | `compare` |
| --- | --- |
| [![swimlane layout showcase](./gallery/layouts/swimlane.svg)](./gallery/layouts/swimlane.svg)<br>Human-in-the-loop Approval Flow | [![compare layout showcase](./gallery/layouts/compare.svg)](./gallery/layouts/compare.svg)<br>RAG vs Agentic RAG |

| `matrix` | `timeline` |
| --- | --- |
| [![matrix layout showcase](./gallery/layouts/matrix.svg)](./gallery/layouts/matrix.svg)<br>AI Feature Priority Matrix | [![timeline layout showcase](./gallery/layouts/timeline.svg)](./gallery/layouts/timeline.svg)<br>AI Product Launch Roadmap |

| `stack` | `funnel` |
| --- | --- |
| [![stack layout showcase](./gallery/layouts/stack.svg)](./gallery/layouts/stack.svg)<br>AI Runtime Stack | [![funnel layout showcase](./gallery/layouts/funnel.svg)](./gallery/layouts/funnel.svg)<br>Lead-to-Agent Automation Funnel |

| `sequence` | `er` |
| --- | --- |
| [![sequence layout showcase](./gallery/layouts/sequence.svg)](./gallery/layouts/sequence.svg)<br>API Tool Calling Sequence | [![er layout showcase](./gallery/layouts/er.svg)](./gallery/layouts/er.svg)<br>Agent Memory Data Model |

| `network` | `agent-memory` |
| --- | --- |
| [![network layout showcase](./gallery/layouts/network.svg)](./gallery/layouts/network.svg)<br>Distributed Agent Runtime Mesh | [![agent-memory layout showcase](./gallery/layouts/agent-memory.svg)](./gallery/layouts/agent-memory.svg)<br>Personalized Agent Memory Flow |

完整布局画廊源文件：`gallery/layouts/index.html`

### Runtime Motion Showcase

P0 高保真 runtime 当前重点展示四个语义图标表演：

| Performance | 语义节奏 |
| --- | --- |
| `agent-think-act-v2` | thought dots 聚合，core 决策，decision token 输出 |
| `search-discover-v2` | 扫描，发现结果，锁定目标 |
| `api-request-response-v2` | request 发出，response 返回，status 完成 |
| `database-write-v2` | write token 落入，存储结构受力，commit flash 完成 |

## 能做什么

- 校验 DiagramScript `0.1`、`0.2`、`0.3`。
- 将自然语言 brief 编译成 DiagramPlan v0.1，再编译成 freeform DiagramScript v0.3。
- 把 JSON spec 或内置 preset 编译成 typed Scene IR。
- 输出 portable animated SVG 和高保真 HTML runtime。
- 支持分层入场、路径绘制、流动粒子、节点发光、burst ring、动态分组边框等动效。
- 支持 `off`、`subtle`、`normal`、`expressive`、`teaching` motion profile。
- 支持结构化 motion effect object，用于连线流动、箭头粒子、动态虚线、边框扫描、icon pulse、标题 reveal。
- 支持 `motion_policy` 动效预算，控制同时运动的连线、节点和边框数量，避免复杂图变乱。
- 可选输出 PNG、GIF、PDF、WebP、MP4、APNG、Lottie。
- 生成 quality report，检查越界、重叠、文本溢出和显式路径碰撞。
- 内置 14 个 clean-room 布局 preset 和 12 个视觉风格。

SVG、调试 viewer HTML、Lottie 和 quality report 只依赖 Python 标准库。主输出
`html` 会写入高保真 runtime 页面，包含静态 SVG stage、命名 parts、Motion
Manifest 和浏览器 runtime；GSAP backend 通过 CDN 加载 GSAP，不增加 Python
依赖。PNG/GIF/PDF/WebP/APNG/MP4 默认走轻量 Python 导出器，适合快速预览；
其中 PNG/GIF/PDF/WebP/APNG 依赖可选 Pillow，MP4 还需要 `ffmpeg`。如果要
最高质量导出，可以使用 `--export-renderer browser`，让 PNG、GIF、PDF、
WebP、MP4、APNG 和 Lottie 从真实 `html` runtime 页面通过 Playwright/
Chromium 捕获，完整保留高保真图标动效。browser Lottie 是帧序列型，视觉
更准，但文件会比默认结构化 Lottie 更大。

## 快速开始

渲染 JSON spec：

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/agent-memory.diagram.json \
  --style styles/blueprint.json \
  --outdir outputs \
  --basename agent-memory \
  --formats svg,html,quality
```

渲染内置 preset：

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --preset agent-memory \
  --outdir outputs \
  --basename agent-memory \
  --all
```

把自然语言 brief 编译成复杂自由排版图：

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --brief examples/briefs/loop-engineering.txt \
  --style styles/sketch-board.json \
  --outdir outputs \
  --basename loop-engineering \
  --formats svg,html,quality \
  --plan-out outputs/loop-engineering.plan.json \
  --spec-out outputs/loop-engineering.diagram.json
```

渲染高保真 HTML Runtime 示例：

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/high-fidelity-runtime.diagram.json \
  --style styles/deep-tech.json \
  --outdir outputs \
  --basename high-fidelity-runtime \
  --formats svg,html,quality \
  --html-runtime gsap
```

需要旧调试 viewer 时显式导出：

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/agent-memory.diagram.json \
  --outdir outputs \
  --basename agent-memory \
  --formats viewer
```

从浏览器 runtime 导出高保真栅格、视频、PDF 和 Lottie：

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/high-fidelity-runtime.diagram.json \
  --style styles/deep-tech.json \
  --outdir outputs \
  --basename high-fidelity-runtime-hq \
  --formats png,gif,webp,apng,mp4,pdf,lottie,quality \
  --html-runtime gsap \
  --export-renderer browser \
  --export-scale 2 \
  --export-fps 24 \
  --export-frames 48
```

安装可选栅格导出依赖：

```bash
python3 -m pip install ".[raster]"
```

浏览器捕获导出还需要 Node.js，以及 Node 侧可解析的 Playwright/Chromium。

## CLI 结果

CLI 成功时会输出结构化 JSON：

```json
{
  "ok": true,
  "schema": {"name": "DiagramScript", "version": "0.2"},
  "preset": "agent-memory",
  "style": "blueprint",
  "outputs": {
    "svg": {"format": "svg", "path": "/abs/agent-memory.svg", "status": "written"},
    "quality": {"format": "quality", "path": "/abs/agent-memory.quality.json", "status": "written"}
  },
  "stats": {"nodes": 6, "edges": 6, "groups": 2}
}
```

校验失败会输出到 stderr，并以退出码 `2` 结束。

## DiagramScript

Schema 文件：

- [schemas/diagram-script-v0.1.schema.json](./schemas/diagram-script-v0.1.schema.json)
- [schemas/diagram-script-v0.2.schema.json](./schemas/diagram-script-v0.2.schema.json)
- [schemas/diagram-script-v0.3.schema.json](./schemas/diagram-script-v0.3.schema.json)
- [schemas/diagram-plan-v0.1.schema.json](./schemas/diagram-plan-v0.1.schema.json)
- [schemas/style-profile-v0.1.schema.json](./schemas/style-profile-v0.1.schema.json)

`0.2` 增加 route、step badge、preset metadata 和更严格的 role 校验。`0.3` 增加结构化 effect object、语义 icon 和节点形状。更完整的字段说明见 [docs/diagram-script.md](./docs/diagram-script.md)。

DiagramPlan v0.1 是更上层的 brief/LLM 合约。当前本地 planner 和编译器见 [docs/prompt-to-diagram-flow.md](./docs/prompt-to-diagram-flow.md)。

## 布局 Preset

AniDiagram 内置 14 个 clean-room 布局 preset。它们既可以直接渲染，也可以作为手写 DiagramScript 的参考。

| Preset | 布局形态 | 适合场景 | 默认风格 |
| --- | --- | --- | --- |
| `pipeline` | 从左到右链路 | ETL、构建、评审、发布流程 | `blueprint` |
| `loop` | 环形反馈回路 | observe-decide-act-learn 系统 | `claude-warm` |
| `hub-spoke` | 中心枢纽加放射依赖 | agent、协调器、服务枢纽 | `deep-tech` |
| `layered` | 水平架构层 | UI、domain、data 分层 | `notion-clean` |
| `swimlane` | 按负责人分泳道 | 客户、团队、系统之间的交接 | `minimal-light` |
| `compare` | 左右对比组 | 方案权衡和决策比较 | `openai-minimal` |
| `matrix` | 2x2 象限 | 优先级和组合管理 | `flat-icon` |
| `timeline` | 里程碑时间线 | roadmap 和发布阶段 | `blueprint` |
| `stack` | 垂直依赖栈 | 基础设施和运行时层级 | `dark-terminal` |
| `funnel` | 漏斗式收窄 | 线索筛选和转化流程 | `glassmorphism` |
| `sequence` | 顺序消息链 | 请求响应、调用链 | `notion-clean` |
| `er` | 实体关系图 | 数据模型和归属关系 | `openai-minimal` |
| `network` | 分布式网络图 | 系统节点、缓存、worker、fanout | `dark-luxury` |
| `agent-memory` | Agent runtime + knowledge panel | 工具调用、记忆、检索、回答 | `blueprint` |

列出全部 preset：

```bash
PYTHONPATH=src python3 -m anidiagram.cli --list-presets
```

DiagramScript 也支持 freeform 布局字段：

| 字段 | 值 | 用途 |
| --- | --- | --- |
| `node.position` | `[x, y]` | 节点绝对坐标。 |
| `node.size` | `[width, height]` | 节点固定尺寸。 |
| `group.bounds` | `[x, y, width, height]` | 分组区域。 |
| `edge.route` | `curved`, `straight`, `hv`, `vh`, `orthogonal`, `points` | 连线路由方式。 |
| `edge.points` | `[x, y]` 列表 | `route` 为 `points` 时使用的显式路径。 |
| `node.step` / `edge.step` | integer | 用于流程编号的可见 step badge。 |
| `node.shape` | `rect`, `decision` | 矩形节点或菱形判断节点。 |

## 视觉风格

内置风格定义画布、颜色、节点边框、分组表现，以及可选的风格兼容 motion 默认值。

| Style | 视觉方向 | 适合场景 |
| --- | --- | --- |
| `minimal-light` | 白底、轻网格、克制边框 | 通用流程和文档 |
| `deep-tech` | 深色技术画布、高亮角色色 | agent 和基础设施图 |
| `blueprint` | 深蓝网格、工程制图感 | 架构和工程图 |
| `flat-icon` | 浅色背景、强角色色、图标化节点 | 矩阵和产品说明 |
| `dark-terminal` | 黑色终端风、紧凑边框 | 运维、CLI、运行时栈 |
| `notion-clean` | 白色文档感、细线、低饱和 | 规范、流程文档、产品流 |
| `glassmorphism` | 冷色画布、半透明面板 | 漏斗和演示型流程 |
| `claude-warm` | 温暖纸张色、柔和强调色 | 推理循环和规划图 |
| `openai-minimal` | 黑白极简 | 清爽产品图和系统图 |
| `dark-luxury` | 黑底、高级感克制强调 | 高层网络图和战略图 |
| `aurora-orb` | 圆角 aurora 色块、柔和光感 | 展示型、创意型图 |
| `sketch-board` | 教学白板感、语义 icon、默认动效 | 教学拆解和复杂概念说明 |

风格目录：[styles/](./styles/)
风格清单：[styles/catalog.json](./styles/catalog.json)

## 动效系统

当前 renderer 使用不依赖第三方运行时的 SVG/SMIL 动效。方向来自常见动画系统里的 timeline、stagger、path draw-on、flow particle、glow、burst ring 等概念，但实现保持 AniDiagram 自有的 clean-room 语义。

### Motion Profile

| Profile | 默认行为 |
| --- | --- |
| `off` | 关闭主动动效，输出静态图。 |
| `subtle` | 克制动效：节点 fade、边 draw、group soft reveal。 |
| `normal` | 默认均衡动效：节点 glow-breathe、边 comet-flow、group marching boundary。 |
| `expressive` | 更强表现：节点 pop、边 comet-flow、动态分组边框。 |
| `teaching` | 教学型动效：icon pulse、ghost-flow、border scan、title reveal。 |
| `runtime-loop` | 运行态循环：结构基本静止，线条信号流动，图标轻微呼吸，标题轻微呼吸。 |

### 动效通道

| 通道 | 支持值 |
| --- | --- |
| `motion.sequence` | `simultaneous`, `step-stagger`, `layered`, `staged`, `loop` |
| `motion.ease` | `linear`, `calm`, `snappy`, `back-out`, `elastic`, `spring` |
| `motion.reduced_motion` | `static`, `subtle`, `pause` |
| `motion.node` | `none`, `fade`, `float`, `glow-breathe`, `pop`, `pulse`, `ripple`, `status-blink`, `icon-pulse`, `icon-breathe`, `icon-semantic`, `icon-performance`, `micro-icon` |
| `motion.edge` | `none`, `static`, `draw`, `pulse`, `comet-flow`, `trace`, `dynamic-dash`, `dash-flow`, `flow-dot`, `flow-arrow`, `signal-dot`, `signal-arrow`, `ghost-flow`, `glow-line`, `comet` |
| `motion.group` | `none`, `static`, `soft-reveal`, `marching-ants`, `border-scan`, `corner-pulse` |
| `motion.title` | `none`, `fade`, `breathe`, `handwrite-reveal`, `highlight-sweep` |

DiagramScript `0.3` 支持结构化 effect object：

```json
{
  "motion": {
    "profile": "teaching",
    "edge": {"preset": "ghost-flow", "particle": "soft-dot", "trail": true, "particle_count": 1},
    "node": {"preset": "icon-semantic", "icon_motion": "database-write"},
    "group": {"preset": "border-scan"},
    "title": {"preset": "handwrite-reveal"}
  },
  "motion_policy": {
    "profile": "focused",
    "max_active_flow_edges": 4,
    "max_particle_edges": 3,
    "particle_count_per_edge": 1,
    "flow_trail_count": 1,
    "max_active_pulse_nodes": 1,
    "max_scanning_groups": 1
  }
}
```

### 动效预算

`motion` 负责“元素怎么动”，`motion_policy` 负责“最多允许多少元素同时动”。这样生成复杂架构图时，可以保留主路径流动，但自动把次要边降级成 draw，把多余节点 pulse 降级成 fade。

| 字段 | 作用 |
| --- | --- |
| `profile` | `unrestricted`, `readable`, `focused`, `expressive` 预算档位。 |
| `motion_area` | `auto`, `micro`, `small`, `medium`, `unrestricted`，先用于控制粒子尺寸和动效面积感。 |
| `max_active_flow_edges` | 最多几条连线持续运动。 |
| `max_particle_edges` | 最多几条连线显示移动粒子/箭头。 |
| `particle_count_per_edge` | 每条粒子连线默认几个粒子。 |
| `flow_trail_count` | 每条连线最多几个尾迹/残影。 |
| `max_active_pulse_nodes` | 最多几个节点做 pulse/glow/float。 |
| `max_scanning_groups` | 最多几个分组边框做扫描。 |

常用建议：复杂架构图用 `readable`，教学拆解图用 `focused`，展示型图再用 `expressive`。

运行态循环建议使用 `runtime-loop` + `readable-runtime`：

```json
{
  "motion": {
    "profile": "runtime-loop",
    "edge": {"preset": "signal-dot", "particle_count": 1, "trail_count": 0},
    "node": {"preset": "icon-breathe"},
    "group": {"preset": "static"},
    "title": {"preset": "breathe"}
  },
  "motion_policy": {
    "profile": "readable-runtime",
    "motion_area": "micro"
  }
}
```

节点可使用语义 icon：

`database`, `file`, `folder`, `api`, `cloud`, `search`, `shield`, `agent`,
`token`, `memory`, `tool`, `output`.

`icon-semantic` 会按图标语义自动选择局部动效，也可以用
`icon_motion` 显式指定：

| icon | 默认动效 |
| --- | --- |
| `database` | `database-write`：顶部椭圆轻微压缩/回弹，写入线扫过，小数据点进入，底部层线轻闪。 |
| `memory` | 叠放记忆卡片 + trace lines，用于 context memory / agent memory。 |
| `file` | `file-lines`：页面从左下进入，明显放大回弹，折角动一下，再快速画出内容线。 |
| `folder` | `folder-open`：文件夹页签轻微打开，并露出一条内部文件线。 |
| `api` | `api-ping`：请求点在括号间移动。 |
| `cloud` | `cloud-upload`：云内上传箭头移动，并配合淡入淡出的传输点。 |
| `search` | `search-sweep`：放大镜扫光，并出现一个小光点。 |
| `shield` | `shield-check`：勾选线条画入，护盾轮廓出现低透明保护脉冲。 |
| `agent` | `agent-orbit`：类脑袋线路图标，带轻量局部状态脉冲。 |
| `tool` | `tool-tap`：工具轻敲，并在接触点出现短促火花。 |
| `output` | `output-check`：内容线先出现，最后勾选线条画入。 |
| `token` | `token-pulse`：中心点脉冲，外层短线顺序点亮。 |

当节点使用 `icon-performance` 时，standalone `svg` 会降级为轻量 SVG/SMIL
图标动效；它不会尝试复刻依赖 JavaScript runtime 的高保真图标表演。
如果需要高保真，以主输出 `html` 为准；HTML runtime 会屏蔽这套 SVG
fallback，避免两套动效叠加：

| icon | runtime performance |
| --- | --- |
| `agent` | `agent-think-act-v2`：thought dots 向核心聚合，核心脉冲形成决策，随后 decision token 向外输出。 |
| `api` | `api-request-response-v2`：接口端点反应，请求 token 发出，响应 token 返回，状态码弹出。 |
| `search` | `search-discover-v2`：镜片偏转，扫光经过，结果点出现，并锁定目标。 |
| `database` | `database-write-v2`：写入 token 落入，顶部压缩，层级提交，成功闪光。 |
| `memory` | `memory-commit-v2`：上下文 token 落入，记忆卡片回弹，trace lines 点亮，提交闪光收束。 |
| `tool` | `tool-run-v2`：函数 chip 下压，connector dot 触发，spark 线条画出，最后闪光收束。 |
| `token` | `token-intent-v2`：token 外壳弹入，核心脉冲，短 ticks 依次画出，并释放 halo。 |
| `output` | `output-reveal-v2`：结果卡片落稳，内容线出现，check 画入，最后完成闪光。 |

这个模式会在 HTML 中写入 `anidiagram-motion-manifest`，manifest 指向稳定
SVG part ID，例如 `#icon-agent-thought-1`、`#icon-api-request-token`。
`html` runtime 会关闭 SVG 图标 fallback，避免同一个图标同时跑 SMIL 和 GSAP；
它通过 CDN 加载 GSAP，不把 GSAP 变成 Python 依赖。
更多 runtime 所有权、当前 performance 覆盖和导出说明见
[docs/html-runtime.md](./docs/html-runtime.md)。

## 重新生成 Gallery

```bash
PYTHONPATH=src python3 scripts/build_showcase.py --quality
```

## 测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Clean-Room 边界

AniDiagram 可以在概念层面参考已有项目和动画库，但代码、schema、示例、文档、生成资产和仓库历史都必须独立实现。

如果未来明确引入第三方 MIT 代码或资产，必须先补充原始版权和许可声明。

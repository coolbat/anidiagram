# AniDiagram 中文说明

语言：[English](./README.md) | 简体中文

AniDiagram 是一个 clean-room 的 DiagramScript 渲染器，用来生成可动画的架构图、流程图、教学图和产品说明图。当前包版本：**0.2.0**。

本仓库不是 GitHub fork，也不复制 [REFERENCES.md](./REFERENCES.md) 中列出的参考项目的源码、文档、图片、生成资产或 git 历史。旧项目和外部项目只作为产品方向与功能验证参考。

## Showcase

README 现在使用 Round 1 已审核通过的 8 个精选案例。完整的 13 种风格和
16 种布局仍保留在 Gallery 中，不再把全部案例堆进 README。

- **Hero Showcase**：3 个架构叙事案例，以 Loop Engineering 为首。
- **Template Showcase**：相同语义内容使用 3 种模板直接对照。
- **Layout Showcase**：2 个针对不同拓扑的布局案例。

Gallery 源码入口：[Gallery](./gallery/index.html) · [全部风格](./gallery/styles/index.html) ·
[全部布局](./gallery/layouts/index.html) · [Runtime 动效](./gallery/runtime-motion.html)

### Hero Showcase

| Loop Engineering Operating Architecture |
| --- |
| ![Loop Engineering Operating Architecture](./gallery/readme-showcase/hero-loop-engineering.webp)<br>`illustrated` 2.5 · `minimal-light` · `layered-loop`<br>把治理、隔离执行、验证交付和外部状态组织成三层工程循环。 |

| Governed RAG Production Architecture | Kubernetes Production Architecture |
| --- | --- |
| ![Governed RAG Production Architecture](./gallery/readme-showcase/hero-governed-rag.webp)<br>`illustrated` 2.5 · `minimal-light` · `layered` | ![Kubernetes Production Architecture](./gallery/readme-showcase/hero-kubernetes-three-layer.webp)<br>`diagram-core-v1` · `deep-tech` · 三层结构 |

本地打开可交互 runtime：

```bash
python3 -m http.server 8765
```

然后访问 `http://127.0.0.1:8765/gallery/readme-showcase/readme-showcase-round-1.html`。
仓库启用静态托管后，可以再用在线地址替换这个本地 URL。

### Template Showcase

语义内容与几何位置保持不变，只切换公共模板，直接比较视觉系统差异。

| Minimal Light | Deep Tech | Claude Warm |
| --- | --- | --- |
| ![Minimal Light 下的 Production AI Agent Request Lifecycle](./gallery/readme-showcase/template-agent-lifecycle-minimal-light.webp)<br>安静、偏文档表达 | ![Deep Tech 下的 Production AI Agent Request Lifecycle](./gallery/readme-showcase/template-agent-lifecycle-deep-tech.webp)<br>高对比技术展示 | ![Claude Warm 下的 Production AI Agent Request Lifecycle](./gallery/readme-showcase/template-agent-lifecycle-claude-warm.webp)<br>温暖的推理和教学表达 |

### Layout Showcase

| Enterprise RAG Ingestion Pipeline | MCP Tool Orchestration Hub |
| --- | --- |
| ![Enterprise RAG Ingestion Pipeline](./gallery/readme-showcase/layout-enterprise-rag-pipeline.webp)<br>`pipeline` · 顺序转换与检索 | ![MCP Tool Orchestration Hub](./gallery/readme-showcase/layout-mcp-tool-hub.webp)<br>`hub-spoke` · 一个编排器协调多种能力 |

### Runtime Motion Showcase

高保真 runtime 现在覆盖所有内置语义图标。核心表演包括：

当前动效基线通过 [gallery/runtime-motion.html](./gallery/runtime-motion.html)
统一管理和查看。这个页面嵌入 live runtime overview，列出 stage effects、
稳定 icon parts 和机器可读 catalog。后续如果要调整视觉节奏、强度、图标语义、
稳定 part ID、stage effect、默认 mode/profile 或 runtime scheduling，需要先确认后再改。

| Performance | 语义节奏 |
| --- | --- |
| `agent-think-act-v2` | brain circuit 线路画出，节点点亮，decision token 输出 |
| `search-discover-v2` | 扫描，发现结果，锁定目标 |
| `api-request-response-v2` | request 发出，response 返回，status 完成 |
| `database-write-v2` | write token 落入，存储结构受力，commit flash 完成 |
| `memory-commit-v2` | context token 落入，记忆卡片回弹，trace lines 提交 |
| `tool-run-v2` | tool chip 下压，connector 触发，spark 收束 |
| `token-intent-v2` | token 外壳弹入，intent ticks 画出，halo 释放 |
| `output-reveal-v2` | output card 落稳，内容线 reveal，check 完成 |
| `file-lines-v2` | 文档落入，折角响应，内容线依次画入 |
| `folder-open-v2` | 文件夹打开，token 进入，file line reveal |
| `cloud-upload-v2` | upload arrow 上行，传输点 pulse，status ring 收束 |
| `shield-check-v2` | 护盾扫描，check 画入，保护脉冲收束 |

## 能做什么

- 校验 DiagramScript `0.1` 到 `0.4`。
- 将自然语言 brief 编译成语义优先的 DiagramPlan v0.2，再解析成
  DiagramScript v0.4；v0.1 -> v0.3 planner 作为显式 legacy 路径保留。
- 把 JSON spec 或内置 preset 编译成 typed Scene IR。
- 输出 portable animated SVG 和高保真 HTML runtime。
- 支持分层入场、路径绘制、流动粒子、节点发光、burst ring、动态分组边框等动效。
- composition-v1 输出使用 `showcase-v1`；直接 DiagramScript 未声明 motion
  时保留兼容默认 `expressive`。`off`、`subtle`、`normal` 等低动效 profile
  仍然可用。
- 支持结构化 motion effect object，用于连线流动、箭头粒子、动态虚线、边框扫描、icon pulse、标题 reveal。
- 支持 `motion_policy` 动效预算，控制同时运动的连线、节点和边框数量，避免复杂图变乱。
- 可选输出 PNG、GIF、PDF、WebP、MP4、APNG、Lottie。
- 生成 quality report，检查越界、重叠、文本溢出和显式路径碰撞。
- 内置 16 个 clean-room 布局 preset 和 13 个公共视觉风格。
- 相同语义的中英文 brief 会生成拓扑等价的计划，并本地化节点标签与说明。
- 默认保持兼容的 `ambient`，同时提供显式启用的 Choreographer v1
  `timeline` 与 `hybrid` 播放。
- wheel 内包含运行所需资源，安装后的 CLI 不依赖源码检出目录。

SVG、调试 viewer HTML、Lottie 和 quality report 只依赖 Python 标准库。主输出
`html` 会写入高保真 runtime 页面，包含静态 SVG stage、命名 parts、Motion
Manifest 和浏览器 runtime；GSAP backend 默认使用精确的 `gsap@3.15.0`
CDN 地址，离线或自托管页面可以通过 `--runtime-dependency inline` 内联用户
提供的本地文件。Python wheel 不捆绑 GSAP。PNG/GIF/PDF/WebP/APNG/MP4
默认走轻量 Python 导出器，适合快速预览；
其中 PNG/GIF/PDF/WebP/APNG 依赖可选 Pillow，MP4 还需要 `ffmpeg`。如果要
最高质量导出，可以使用 `--export-renderer browser`，让 PNG、GIF、PDF、
WebP、MP4、APNG 和 Lottie 从真实 `html` runtime 页面通过 Playwright/
Chromium 捕获，完整保留高保真图标动效。browser Lottie 是帧序列型，视觉
更准，但文件会比默认结构化 Lottie 更大。

## 快速开始

构建并安装可脱离源码目录运行的 wheel：

```bash
python3 -m pip wheel . --no-deps --wheel-dir dist
python3 -m pip install dist/anidiagram-0.2.0-py3-none-any.whl
anidiagram --preset agent-memory --outdir outputs --formats svg,html,quality
```

下面的源码示例使用 `PYTHONPATH=src`，方便贡献者不安装就验证本地改动。

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

把已编写的 DiagramPlan v0.2 编译为已解析的 DiagramScript v0.4：

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --plan examples/contracts/production-request-path.plan.json \
  --spec-out outputs/production-request-path.diagram.json \
  --outdir outputs \
  --basename production-request-path \
  --formats svg,html,quality
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

使用本地 GSAP 渲染中文因果讲解：

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --plan examples/contracts/production-request-path.plan.json \
  --outdir outputs/choreographer \
  --basename production-request-path \
  --formats html,quality \
  --runtime-mode timeline \
  --viewer-locale zh-CN \
  --runtime-dependency inline \
  --runtime-source node_modules/gsap/dist/gsap.min.js
```

`--runtime-mode hybrid` 会先展示 ambient 总览，用户开始讲解后再进入时间线；
`--runtime-dependency none` 可生成不加载浏览器动画依赖的静态 HTML fallback。

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
- [schemas/diagram-script-v0.4.schema.json](./schemas/diagram-script-v0.4.schema.json) — `composition-v1` 已解析输出
- [schemas/diagram-plan-v0.1.schema.json](./schemas/diagram-plan-v0.1.schema.json)
- [schemas/diagram-plan-v0.2.schema.json](./schemas/diagram-plan-v0.2.schema.json) — 语义优先的当前合约
- [schemas/style-profile-v0.1.schema.json](./schemas/style-profile-v0.1.schema.json)

`0.2` 增加 route、step badge、preset metadata 和更严格的 role 校验。`0.3` 增加结构化 effect object、语义 icon 和节点形状。`0.4` 增加独立图标系统、解析来源记录与 `showcase-v1`；composition-v1 输出默认使用带版本记录的 Illustrated。更完整的字段说明见 [docs/diagram-script.md](./docs/diagram-script.md)。

DiagramPlan v0.2 是当前默认的上层 brief/LLM 合约，并通过
`composition-v1` 编译到 DiagramScript v0.4。DiagramPlan v0.1 仅保留给显式
legacy `explainer-board` 输出。当前本地 planner 和编译器见
[docs/prompt-to-diagram-flow.md](./docs/prompt-to-diagram-flow.md)。

不同输入路径的默认值必须分开理解：

| 输入路径 | 默认图标系统 | 默认动效 |
| --- | --- | --- |
| DiagramPlan v0.2 经 `composition-v1` 编译到 DiagramScript v0.4 | `illustrated`（2.5.0） | `showcase-v1` |
| 不声明 `composition_policy` 的直接 DiagramScript v0.4 | `diagram-core-v1` | 未声明 `motion` 时使用 `expressive` |
| DiagramScript v0.1-v0.3 或未声明 `icon_system` 的旧 style | `illustrated-character-v1` | scene 未声明 motion 时使用 `expressive` |

`illustrated` 是 composition-v1 默认图标系统。当前实现版本为 2.5.0，56 枚
图标在 `showcase-v1` 下自动使用正式的 `illustrated-performance-v6` 合约。
当前、默认与 legacy 边界见
[图标系统发布状态](./docs/icon-system-release-status.md)。需要技术线框语言时，
应显式指定 `diagram-core-v1`。

## 布局 Preset

AniDiagram 内置 16 个 clean-room 布局 preset。它们既可以直接渲染，也可以作为手写 DiagramScript 的参考。

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
| `agent-loop` | 顶部触发、中部认知循环、底部三支撑域 | Agent 内部机制、记忆、安全闸门、工具执行 | `sketch-board` |
| `layered-loop` | 多层蛇形主流程加外侧反馈 | 工程循环、分阶段执行、验证交付与外部状态 | `minimal-light` |

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
| `illustrated-semantic` | 暖米白画布、低饱和语义色、弱化网格与外框 | 清晰插画流程和技术说明图 |
| `sketch-board` | 教学白板感、语义 icon、默认动效 | 教学拆解和复杂概念说明 |

风格目录：[styles/](./styles/)
风格清单：[styles/catalog.json](./styles/catalog.json)

## 动效系统

SVG renderer 使用不依赖第三方运行时的 SVG/SMIL 动效；HTML runtime 使用
Motion Manifest + GSAP 承载高保真图标表演。方向来自常见动画系统里的
timeline、stagger、path draw-on、flow particle、glow、burst ring 等概念，
但实现保持 AniDiagram 自有的 clean-room 语义。

### Motion Profile

| Profile | 默认行为 |
| --- | --- |
| `off` | 关闭主动动效，输出静态图。 |
| `subtle` | 克制动效：节点 fade、边 draw、group soft reveal。 |
| `normal` | 兼容型均衡动效：节点 glow-breathe、边 comet-flow、group marching boundary。 |
| `expressive` | 兼容路径默认高保真动效：节点 pop、边 comet-flow、标题扫光、动态分组边框。 |
| `teaching` | 教学型动效：icon pulse、ghost-flow、border scan、title reveal。 |
| `runtime-loop` | 运行态循环：结构基本静止，线条信号流动，图标轻微呼吸，标题轻微呼吸。 |
| `showcase-v1` | composition-v1 默认：开启全部适用的图标表演和数据流动效，同时保留规范静止姿态与 reduced-motion 支持。 |

`expressive` 是直接或旧版 DiagramScript 未声明 motion 时的兼容默认；新建
DiagramPlan v0.2 会显式解析为 `showcase-v1`。

### 动效通道

| 通道 | 支持值 |
| --- | --- |
| `motion.sequence` | `simultaneous`, `step-stagger`, `layered`, `staged`, `loop` |
| `motion.ease` | `linear`, `calm`, `snappy`, `back-out`, `elastic`, `spring` |
| `motion.reduced_motion` | `static`, `subtle`, `pause` |
| `motion.node` | `none`, `fade`, `float`, `glow-breathe`, `pop`, `pulse`, `ripple`, `status-blink`, `icon-pulse`, `icon-breathe`, `icon-semantic`, `icon-performance`, `micro-icon` |
| `motion.edge` | `none`, `static`, `draw`, `packet-flow`, `comet-flow`, `stream-flow`（旧名称仍可作为输入别名） |
| `motion.group` | `none`, `static`, `soft-reveal`, `marching-ants`, `border-scan`, `corner-pulse` |
| `motion.title` | `none`, `fade`, `breathe`, `handwrite-reveal`, `highlight-sweep` |

Edge Motion v1.0.0 已冻结并通过人工视觉审核；Illustrated 2.5 与边动效继续维持独立版本边界。

DiagramScript `0.3` 支持结构化 effect object：

```json
{
  "motion": {
    "profile": "expressive",
    "edge": {"preset": "signal-arrow", "particle": "soft-dot", "trail": true, "particle_count": 1},
    "node": {"preset": "icon-performance", "icon_motion": "database-write-v2"},
    "group": {"preset": "border-scan"},
    "title": {"preset": "highlight-sweep"}
  },
  "motion_policy": {
    "profile": "expressive",
    "max_active_flow_edges": 8,
    "max_particle_edges": 8,
    "particle_count_per_edge": 1,
    "flow_trail_count": 1,
    "max_active_pulse_nodes": 8,
    "max_scanning_groups": 2
  }
}
```

### 动效预算

`motion` 负责“元素怎么动”，`motion_policy` 负责“最多允许多少元素同时动”。这样生成复杂架构图时，可以保留主路径流动，但自动把次要边降级成 draw，把多余节点 pulse 降级成 fade。

| 字段 | 作用 |
| --- | --- |
| `profile` | `unrestricted`, `readable`, `focused`, `expressive`, `readable-runtime` 预算档位。 |
| `motion_area` | `auto`, `micro`, `small`, `medium`, `unrestricted`，先用于控制粒子尺寸和动效面积感。 |
| `max_active_flow_edges` | 最多几条连线持续运动。 |
| `max_particle_edges` | 最多几条连线显示移动粒子/箭头。 |
| `particle_count_per_edge` | 每条粒子连线默认几个粒子。 |
| `flow_trail_count` | 每条连线最多几个尾迹/残影。 |
| `max_active_pulse_nodes` | 最多几个节点做 pulse/glow/float。 |
| `max_scanning_groups` | 最多几个分组边框做扫描。 |

常用建议：复杂架构图用 `readable`，教学拆解图用 `focused`，直接或旧版
DiagramScript 的高保真预算用 `expressive`。composition-v1 的
`showcase-v1` 是 `motion.profile`，不是 `motion_policy.profile`；编译器会把它
与 `motion_policy.profile=unrestricted`、`motion_area=unrestricted`、
`pulse_mode=all` 配对。

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
| `agent` | `agent-think-act-v2`：brain circuit 线路向外画出，节点依次点亮，核心决策脉冲后输出 decision token。 |
| `api` | `api-request-response-v2`：接口端点反应，请求 token 发出，响应 token 返回，状态码弹出。 |
| `search` | `search-discover-v2`：镜片偏转，扫光经过，结果点出现，并锁定目标。 |
| `database` | `database-write-v2`：写入 token 落入，顶部压缩，层级提交，成功闪光。 |
| `memory` | `memory-commit-v2`：上下文 token 落入，记忆卡片回弹，trace lines 点亮，提交闪光收束。 |
| `tool` | `tool-run-v2`：函数 chip 下压，connector dot 触发，spark 线条画出，最后闪光收束。 |
| `token` | `token-intent-v2`：token 外壳弹入，核心脉冲，短 ticks 依次画出，并释放 halo。 |
| `output` | `output-reveal-v2`：结果卡片落稳，内容线出现，check 画入，最后完成闪光。 |
| `file` | `file-lines-v2`：文档落入，折角响应，内容线依次画入，最后闪光收束。 |
| `folder` | `folder-open-v2`：文件夹打开，输入 token 进入，file line reveal，最后闪光收束。 |
| `cloud` | `cloud-upload-v2`：upload arrow 上行，传输点 pulse，status ring 收束。 |
| `shield` | `shield-check-v2`：护盾扫描，check 画入，保护脉冲收束。 |

这个模式会在 HTML 中写入 `anidiagram-motion-manifest`，manifest 指向稳定
SVG part ID，例如 `#icon-agent-outline-left`、`#icon-api-request-token`。
`html` runtime 会关闭 SVG 图标 fallback，避免同一个图标同时跑 SMIL 和 GSAP；
默认从精确版本 CDN 加载 GSAP，也可内联用户提供的本地文件，不把 GSAP
捆绑进 Python 包。
当前默认 runtime mode 是 `ambient`。直接 DiagramScript 未声明 motion 时使用
兼容 profile `expressive`；新 composition-v1 输出解析为 `showcase-v1`。runtime
工具栏的 Expressive 模式下，各图标独立循环播放高保真局部表演，并带少量 stagger delay；浏览器 runtime
还会生成由 GSAP 控制的 edge flow 粒子和标题扫光。Choreographer v1 已提供
显式 `timeline` 与 `hybrid` 模式，按“源节点 → 连线 → 目标节点”组织因果步骤，
并提供开始、上一步、下一步控制；不传参数时仍保持 ambient。event-driven、
state-machine 和任意节点交互仍在路线图中。更多 runtime 所有权、
当前 performance 覆盖和导出说明见 [docs/html-runtime.md](./docs/html-runtime.md)
和 [docs/runtime-motion-roadmap.md](./docs/runtime-motion-roadmap.md)。

## 重新生成 Gallery

```bash
python3 -m pip install -e ".[raster]"
PYTHONPATH=src python3 scripts/build_showcase.py --quality
```

该命令复用已经提交的 8 个 README animated WebP 预览。如果需要使用固定的
`gsap@3.15.0` 捕获 runtime 明确重新录制，执行：

```bash
PYTHONPATH=src python3 scripts/render_readme_showcase_round_1.py \
  --spec-root examples/readme-showcase-round-1 \
  --outdir gallery/readme-showcase
```

重新录制需要项目内的 Playwright/Chromium 浏览器运行环境和精确的本地
`gsap@3.15.0` 开发依赖。提交资产的合约是 24 帧、12 FPS、1x、4 个循环混合
帧和 WebP 质量 65。体积门禁：

```bash
PYTHONPATH=src python3 scripts/check_asset_budget.py
```

8 个 README WebP 合计必须小于 6 MiB、单个小于 1 MiB，完整 Gallery 小于
55 MiB。`PYTHONPATH=src python3 scripts/prune_outputs.py` 只做安全预览，不会
删除 release evidence；只有显式追加 `--apply` 才会清理符合条件的旧输出。

## 测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Clean-Room 边界

AniDiagram 可以在概念层面参考已有项目和动画库，但代码、schema、示例、文档、生成资产和仓库历史都必须独立实现。

如果未来明确引入第三方 MIT 代码或资产，必须先补充原始版权和许可声明。

## Illustrated 2.5.0

`illustrated` 是当前插画图标系统的稳定公共 id；当 DiagramPlan 使用
`icon_system: auto` 或省略该 presentation 轴时，它就是 composition-v1 默认值。
版本 2.5.0 包含 56 枚已批准图标，与 Diagram
Core v1 的 56 个语义一一对应；13 套公共模板只覆盖颜色 token，不改变图标
几何、部件 id 或语义角色。

公共 `showcase-v1` 会自动使用完整 56 项的正式
`illustrated-performance-v6` 合约。v6/v7 review 合约仅作为不可变的人审归档
证据，新图不得输出它们；`illustrated-performance-v5` 保留为 2.4.0 的不可变
公共归档。输入 alias
`illustrated-character-v2` 会解析为 `illustrated`；新 plan 与 resolved output
统一使用稳定公共 id。

## Legacy：Illustrated Character v1

对于 DiagramScript v0.1-v0.3 和未声明 `icon_system` 的旧 style，兼容默认仍是
`illustrated-character-v1`：这是一套原创的完整 13 枚 legacy 语义图标，覆盖
`agent`、`operator`、`search`、`tool`、`api`、
`memory`、`output`、`file`、`folder`、`cloud`、`shield`、`token` 和
`database`。其轻量 GSAP 动效依次为 `brain-think-pulse-v1`、
`operator-type-focus-v1`、`search-scout-find-v1`、`tool-kit-action-v1`、
`api-signal-return-v1`、`memory-index-commit-v1`、`output-envelope-reveal-v1`、
`file-note-write-v1`、`folder-file-store-v1`、`cloud-uplink-ready-v1`、
`shield-guard-confirm-v1`、`token-intent-ready-v1` 与
`bucket-ingest-confirm-v1`。可直接运行 `styles/illustrated-character.json`
与两个 `illustrated-character-v1-*` 示例查看效果。旧的 `illustrated-v1` 和
`semantic-line-v1` 仍需显式指定。

Character v1 的 HTML 使用 Motion Coordination v1.2。`Expressive` 以角色动效
为主，每条活动连线持续显示低亮度流线，并叠加一个无静默间隔的语义数据包；
标题高光只在进入时播放一次。分组框默认使用 `soft-reveal`，只有显式
指定时才持续扫描。`Readable` 保留角色的语义动作，但把舞台动效压缩到最多
两条关键连线，并移除装饰性标题与分组动效。`Off` 与系统级 reduced motion
均显示规范静态场景，不创建 GSAP timeline。

正式支持的 Character v1 主题为 `illustrated-character`、`deep-tech` 和
`teaching-sketch-character`，可在
[gallery/character-themes.html](./gallery/character-themes.html) 对比同一内容。
代表性架构示例包括 [Agent Memory](./examples/agent-memory.diagram.json)、
[High Fidelity Runtime](./examples/high-fidelity-runtime.diagram.json) 与
[Loop Engineering](./outputs/loop-engineering-architecture/loop-engineering-architecture.diagram.json)。

浏览器运行时主导的 SVG、HTML、PNG、WebP、GIF、APNG、MP4、PDF 与帧序列
Lottie 发布证据位于
[`outputs/release-evidence/character-v1/`](./outputs/release-evidence/character-v1/)。

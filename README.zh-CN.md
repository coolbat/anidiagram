# AniDiagram 中文说明

语言：[English](./README.md) | 简体中文

AniDiagram 是一个 clean-room 的 DiagramScript 渲染器，用来生成可动画的架构图、流程图、教学图和产品说明图。

本仓库不是 GitHub fork，也不复制 [REFERENCES.md](./REFERENCES.md) 中列出的参考项目的源码、文档、图片、生成资产或 git 历史。旧项目和外部项目只作为产品方向与功能验证参考。

## 案例入口

| Pipeline | Agent Memory |
| --- | --- |
| ![Pipeline preset](./gallery/pipeline.svg) | ![Agent memory preset](./gallery/agent-memory.svg) |

| Swimlane | Network |
| --- | --- |
| ![Swimlane preset](./gallery/swimlane.svg) | ![Network preset](./gallery/network.svg) |

- 预设模板画廊：[gallery/index.html](./gallery/index.html)
- 风格案例画廊：[gallery/styles/index.html](./gallery/styles/index.html)

## 风格案例展示

每个内置风格都有一份独立 DiagramScript 案例、SVG 预览、HTML viewer 和 quality report。点击预览可以打开对应 HTML viewer。

| `minimal-light` | `deep-tech` | `blueprint` |
| --- | --- | --- |
| [![minimal-light style showcase](./gallery/styles/minimal-light.svg)](./gallery/styles/minimal-light.html)<br>客服分流 | [![deep-tech style showcase](./gallery/styles/deep-tech.svg)](./gallery/styles/deep-tech.html)<br>Realtime AI Ops Mesh | [![blueprint style showcase](./gallery/styles/blueprint.svg)](./gallery/styles/blueprint.html)<br>云部署蓝图 |

| `flat-icon` | `dark-terminal` | `notion-clean` |
| --- | --- | --- |
| [![flat-icon style showcase](./gallery/styles/flat-icon.svg)](./gallery/styles/flat-icon.html)<br>优先级看板 | [![dark-terminal style showcase](./gallery/styles/dark-terminal.svg)](./gallery/styles/dark-terminal.html)<br>故障响应 Runbook | [![notion-clean style showcase](./gallery/styles/notion-clean.svg)](./gallery/styles/notion-clean.html)<br>产品发现流程 |

| `glassmorphism` | `claude-warm` | `openai-minimal` |
| --- | --- | --- |
| [![glassmorphism style showcase](./gallery/styles/glassmorphism.svg)](./gallery/styles/glassmorphism.html)<br>收入漏斗 | [![claude-warm style showcase](./gallery/styles/claude-warm.svg)](./gallery/styles/claude-warm.html)<br>研究推理循环 | [![openai-minimal style showcase](./gallery/styles/openai-minimal.svg)](./gallery/styles/openai-minimal.html)<br>评测流水线 |

| `dark-luxury` | `aurora-orb` | `sketch-board` |
| --- | --- | --- |
| [![dark-luxury style showcase](./gallery/styles/dark-luxury.svg)](./gallery/styles/dark-luxury.html)<br>高层信号网络 | [![aurora-orb style showcase](./gallery/styles/aurora-orb.svg)](./gallery/styles/aurora-orb.html)<br>创意 Agent Studio | [![sketch-board style showcase](./gallery/styles/sketch-board.svg)](./gallery/styles/sketch-board.html)<br>注意力教学流程 |

## 能做什么

- 校验 DiagramScript `0.1`、`0.2`、`0.3`。
- 将自然语言 brief 编译成 DiagramPlan v0.1，再编译成 freeform DiagramScript v0.3。
- 把 JSON spec 或内置 preset 编译成 typed Scene IR。
- 输出 animated SVG 和自包含 HTML viewer。
- 支持分层入场、路径绘制、流动粒子、节点发光、burst ring、动态分组边框等动效。
- 支持 `off`、`subtle`、`normal`、`expressive`、`teaching` motion profile。
- 支持结构化 motion effect object，用于连线流动、箭头粒子、动态虚线、边框扫描、icon pulse、标题 reveal。
- 支持 `motion_policy` 动效预算，控制同时运动的连线、节点和边框数量，避免复杂图变乱。
- 可选输出 PNG、GIF、PDF、WebP、MP4、APNG、Lottie。
- 生成 quality report，检查越界、重叠、文本溢出和显式路径碰撞。
- 内置 14 个 clean-room 布局 preset 和 12 个视觉风格。

SVG、HTML、Lottie 和 quality report 只依赖 Python 标准库。PNG/GIF/PDF/WebP/APNG 依赖可选 Pillow，MP4 还需要 `ffmpeg`。

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

安装可选栅格导出依赖：

```bash
python3 -m pip install ".[raster]"
```

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
| `motion.node` | `none`, `fade`, `float`, `glow-breathe`, `pop`, `pulse`, `ripple`, `status-blink`, `icon-pulse`, `icon-breathe`, `icon-semantic`, `micro-icon` |
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
| `database`, `memory` | `database-write`：顶部椭圆轻微压缩/回弹，写入线扫过，小数据点进入，底部层线轻闪。 |
| `file` | `file-lines`：页面从左下进入，明显放大回弹，折角动一下，再快速画出内容线。 |
| `folder` | `folder-open`：文件夹页签轻微打开，并露出一条内部文件线。 |
| `api` | `api-ping`：请求点在括号间移动。 |
| `cloud` | `cloud-upload`：云内上传箭头移动，并配合淡入淡出的传输点。 |
| `search` | `search-sweep`：放大镜扫光，并出现一个小光点。 |
| `shield` | `shield-check`：勾选线条画入，护盾轮廓出现低透明保护脉冲。 |
| `agent` | `agent-orbit`：中心点发光，小状态点环绕。 |
| `tool` | `tool-tap`：工具轻敲，并在接触点出现短促火花。 |
| `output` | `output-check`：内容线先出现，最后勾选线条画入。 |
| `token` | `token-pulse`：中心点脉冲，外层短线顺序点亮。 |

## 重新生成 Gallery

```bash
PYTHONPATH=src python3 scripts/batch_render.py --outdir gallery --quality
PYTHONPATH=src python3 scripts/build_style_showcase.py --quality
```

## 测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Clean-Room 边界

AniDiagram 可以在概念层面参考已有项目和动画库，但代码、schema、示例、文档、生成资产和仓库历史都必须独立实现。

如果未来明确引入第三方 MIT 代码或资产，必须先补充原始版权和许可声明。

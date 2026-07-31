<p align="center">
  <img src="./assets/readme/hero-zh-cn.svg" width="100%" alt="AniDiagram 把架构意图变成能够解释、运动和交付的动态架构图">
</p>

<p align="center">
  <strong>从自然语言到语义计划、动态运行时与可交付输出。</strong>
</p>

<p align="center">
  <code>Python 3.9+</code> · <code>DiagramScript 0.4</code> · <code>16 种布局</code> · <code>13 种风格</code> · <code>56 枚插画图标</code> · <code>MIT</code>
</p>

<p align="center">
  <a href="./README.md">English</a> · 简体中文 ·
  <a href="./gallery/index.html">Gallery</a> ·
  <a href="./docs/diagram-script.md">DiagramScript</a> ·
  <a href="./docs/html-runtime.md">Runtime</a>
</p>

AniDiagram 是一个 clean-room 的动态架构图渲染器与语义编排管线。输入一段
自然语言、一个语义化 `DiagramPlan` 或手写 `DiagramScript`，它会解析视觉系统、
校验场景，并输出可移植 SVG、可交互 HTML runtime，以及栅格或视频交付物。

当前包版本：**0.2.0**。

## 目录

- [先看实际效果](#先看实际效果)
- [为什么选择 AniDiagram](#为什么选择-anidiagram)
- [快速开始](#快速开始)
- [工作原理](#工作原理)
- [输入与输出](#输入与输出)
- [生成中文版](#生成中文版)
- [布局与风格](#布局与风格)
- [动效与运行时](#动效与运行时)
- [合约与兼容性](#合约与兼容性)
- [开发与验证](#开发与验证)
- [文档导航](#文档导航)

## 先看实际效果

下面的案例全部来自仓库自有语义计划，并通过 CLI 使用的同一条公共管线生成。

### 有治理的工程循环

![Loop Engineering Operating Architecture](./gallery/readme-showcase/hero-loop-engineering.webp)

`illustrated` 2.5 · `minimal-light` · `layered-loop` —— 将治理、隔离执行、
验证交付与外部状态组织成一个完整运行循环。

| Governed RAG 生产架构 | Kubernetes 生产分层 |
| --- | --- |
| ![Governed RAG Production Architecture](./gallery/readme-showcase/hero-governed-rag.webp) | ![Kubernetes Production Architecture](./gallery/readme-showcase/hero-kubernetes-three-layer.webp) |
| `illustrated` 2.5 · `minimal-light` | `diagram-core-v1` · `deep-tech` |

<details>
<summary><strong>比较不同风格和拓扑布局</strong></summary>

接下来三个案例保持语义内容与几何位置不变，只切换视觉风格。

| Minimal Light | Deep Tech | Claude Warm |
| --- | --- | --- |
| ![Minimal Light 下的 Production AI Agent Request Lifecycle](./gallery/readme-showcase/template-agent-lifecycle-minimal-light.webp) | ![Deep Tech 下的 Production AI Agent Request Lifecycle](./gallery/readme-showcase/template-agent-lifecycle-deep-tech.webp) | ![Claude Warm 下的 Production AI Agent Request Lifecycle](./gallery/readme-showcase/template-agent-lifecycle-claude-warm.webp) |

最后两个案例说明布局为什么是语义选择，而不仅是换皮肤。

| 顺序转换流程 | 中心编排枢纽 |
| --- | --- |
| ![Enterprise RAG Ingestion Pipeline](./gallery/readme-showcase/layout-enterprise-rag-pipeline.webp) | ![MCP Tool Orchestration Hub](./gallery/readme-showcase/layout-mcp-tool-hub.webp) |
| `pipeline` | `hub-spoke` |

</details>

[打开完整风格与布局 Gallery →](./gallery/index.html)

## 为什么选择 AniDiagram

| 能力 | 带来的价值 |
| --- | --- |
| **语义优先编排** | 系统含义保存在实体、关系、分组和流程里；图标、风格、布局与动效是四个独立表现轴。 |
| **从需求直接生成** | 自然语言先编译为 DiagramPlan v0.2，再生成带表现来源记录的 DiagramScript v0.4。 |
| **两套视觉语言** | Illustrated 2.5 的 56 枚图标适合生动讲解，`diagram-core-v1` 适合精确技术线框图。 |
| **语义化动效** | 图标部件、数据流连线、分组和标题都能运动，同时不把业务含义塞进渲染器代码。 |
| **中英文原生支持** | 自动识别中文 brief，输出 `zh-CN` 元数据、中文控件和跨平台 CJK 字体回退。 |
| **一份源文件，多种交付** | 输出 SVG、HTML、PNG、GIF、PDF、WebP、MP4、APNG、Lottie 和质量报告。 |
| **可直接使用的视觉范围** | 内置 16 种拓扑布局与 13 种公共风格，也支持精确手写节点和连线路径。 |
| **把校验当成交付物** | 校验 schema、边界、文字适配、重叠、显式路径、资产合约与浏览器 runtime。 |

## 快速开始

在仓库中安装本地 CLI：

```bash
python3 -m pip install -e .
```

用一句话生成架构图：

```bash
anidiagram \
  --text "展示用户请求经过 API 网关、智能体、工具、安全校验，最终形成可信结果。" \
  --outdir outputs/quickstart \
  --basename request-flow \
  --formats svg,html,quality
```

第一次成功运行会生成：

```text
outputs/quickstart/
├── request-flow.svg
├── request-flow.html
└── request-flow.quality.json
```

本地预览 HTML runtime：

```bash
python3 -m http.server 8765
```

然后打开 `http://127.0.0.1:8765/outputs/quickstart/request-flow.html`。

需要栅格或视频格式时安装可选依赖：

```bash
python3 -m pip install -e ".[raster]"
```

## 工作原理

<p align="center">
  <img src="./assets/readme/workflow-zh-cn.svg" width="100%" alt="AniDiagram 从架构意图到语义、表现编排、可视化输出与质量证据的工作流">
</p>

1. **描述含义** —— 输入 brief、DiagramPlan 或 DiagramScript。
2. **建立稳定语义** —— 实体、关系、分组、流程、语言和来源与渲染器解耦。
3. **解析表现系统** —— 图标系统、风格、布局、动效保持四轴独立。
4. **统一编译** —— DiagramScript v0.4 记录具体几何与已解析表现选择。
5. **渲染并验证** —— 从同一个 Scene 同时生成可视化文件和质量报告。

## 输入与输出

### 输入方式

| 输入 | 适用场景 | CLI |
| --- | --- | --- |
| 自然语言 brief | 从需求到图的最短路径 | `--text` 或 `--brief` |
| DiagramPlan v0.2 | 需要稳定语义和可独立选择的表现系统 | `--plan` |
| DiagramScript v0.4 | 需要精确几何、动效和渲染器控制 | `--spec` |
| 内置 preset | 需要快速使用已知拓扑 | `--preset` |

### 输出格式

| 输出 | 适合场景 | 说明 |
| --- | --- | --- |
| `svg` | 文档与静态托管 | 包含轻量语义动效回退 |
| `html` | 最高保真可交互播放 | Motion Manifest + GSAP runtime + 本地化控件 |
| `png`, `pdf` | 文档、评审与演示 | 默认 Python 渲染；浏览器捕获可获得最高保真度 |
| `gif`, `webp`, `apng` | 可直接分享的动态预览 | 可配置帧率、质量与循环混合 |
| `mp4` | 视频交付 | 需要 `ffmpeg` |
| `lottie` | 结构化或逐帧动画交换 | 表现方式由 renderer 决定 |
| `quality` | CI 与评审证据 | 输出几何和渲染问题的 JSON 摘要 |

当导出结果必须与高保真 HTML runtime 一致时，使用
`--export-renderer browser`。

## 生成中文版

默认语言策略是 `auto`：中文 brief 会自动解析为 `zh-CN`，英文 brief 输出英文。
需要显式锁定中文版时使用 `--diagram-locale zh-CN`：

```bash
anidiagram \
  --text "构建企业级智能体平台架构：请求经过 API 网关进入智能体，读取长期记忆和知识库，调用搜索工具，通过安全校验后输出结果。" \
  --diagram-locale zh-CN \
  --viewer-locale auto \
  --outdir outputs/zh-CN \
  --basename enterprise-agent-platform \
  --formats svg,html,quality
```

完整中文 Plan 示例：
[examples/zh-CN/enterprise-agent-platform.plan.json](./examples/zh-CN/enterprise-agent-platform.plan.json)。
SVG 与 HTML 会声明 `lang="zh-CN"`；栅格导出会寻找本机可用 CJK 字体，也可以
设置 `ANIDIAGRAM_CJK_FONT=/absolute/path/to/font.ttf` 固定构建字体。

## 布局与风格

### 16 种语义布局

`pipeline` · `loop` · `hub-spoke` · `layered` · `swimlane` · `compare` ·
`matrix` · `timeline` · `stack` · `funnel` · `sequence` · `er` · `network` ·
`agent-memory` · `agent-loop` · `layered-loop`

布局按拓扑选择：顺序工作用 `pipeline`，中心协调用 `hub-spoke`，分层系统用
`layered`，智能体内部机制用 `agent-loop`，受治理的循环工作流用
`layered-loop`。

### 13 种公共风格

`minimal-light` · `deep-tech` · `blueprint` · `flat-icon` · `dark-terminal` ·
`notion-clean` · `glassmorphism` · `claude-warm` · `openai-minimal` ·
`dark-luxury` · `aurora-orb` · `illustrated-semantic` · `sketch-board`

浏览[风格 Gallery](./gallery/styles/index.html)、
[布局 Gallery](./gallery/layouts/index.html)或机器可读的
[风格目录](./styles/catalog.json)。

## 动效与运行时

新的 composition-v1 图会解析为 `showcase-v1`：所有适用的插画图标执行对应
语义动作，数据流连线保持可见运动，同时为 reduced-motion 用户保留稳定静止
状态。离散传输使用单个 `packet-flow` 实心点；连续或循环关系使用
`stream-flow` 虚线持续运动；`comet-flow` 只用于明确的强调传输。

HTML runtime 提供三种查看模式：

- **Expressive** —— 完整语义图标表演和主动数据流。
- **Readable** —— 降低视觉密度，同时保留关键动作。
- **Off** —— 用于评审或 reduced motion 的规范静止结构。

可在 [Runtime Motion](./gallery/runtime-motion.html) 查看冻结动效基线，并在
[gallery/character-themes.html](./gallery/character-themes.html) 比较 legacy
角色主题。

### 动效预算

`motion` 定义元素如何运动，`motion_policy` 限制允许同时活动的动效数量。
composition-v1 默认将 `showcase-v1` 与
`motion_policy.profile=unrestricted`、`motion_area=unrestricted`、
`pulse_mode=all` 配对。复杂说明图可以选择 `readable` 或 `focused` 预算，
不需要修改语义图结构。

### 节点动效

公共节点路径是 `icon-performance`：每个支持的图标会解析为带版本的语义表演，
并使用稳定 SVG part ID。Illustrated 2.5.0 包含 56 枚已批准图标，使用公共
`illustrated-performance-v6` 合约。完整 performance 清单、静止姿态合约与
reduced-motion 行为见 [HTML runtime](./docs/html-runtime.md)。

Edge Motion v1.0.0 独立版本化，详见
[docs/edge-motion-v1.md](./docs/edge-motion-v1.md)。

## 合约与兼容性

| 输入合约 | 默认图标系统 | 默认动效 |
| --- | --- | --- |
| DiagramPlan v0.2 经 `composition-v1` 编译 | `illustrated` 2.5.0 | `showcase-v1` |
| 不声明 `composition_policy` 的直接 DiagramScript v0.4 | `diagram-core-v1` | 缺省时使用 `expressive` |
| Legacy DiagramScript v0.1–v0.3 | `illustrated-character-v1` | 缺省时使用 `expressive` |

**composition-v1 默认**使用稳定公共 ID `illustrated`。需要技术线框语言时显式
选择 `diagram-core-v1`。Legacy alias `illustrated-v1` 与
`semantic-line-v1` 仍可显式使用，但不会被新 Plan 静默选中。

Schema 位于 [schemas/](./schemas/)。语义与表现分离的正式边界由
[ADR-001](./docs/decisions/ADR-001-separate-semantic-content-from-presentation.md)
和[编排合约](./docs/diagram-composition-contract.md)定义。

## 开发与验证

运行项目门禁：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --strict --json
node --check runtime/anidiagram-runtime.js
```

重新生成完整 Gallery：

```bash
python3 -m pip install -e ".[raster]"
PYTHONPATH=src python3 scripts/build_showcase.py --quality
```

README 的 8 个精选预览是已经提交的 animated WebP。只有需要明确更新冻结捕获
合约时才重新录制：

```bash
PYTHONPATH=src python3 scripts/render_readme_showcase_round_1.py \
  --spec-root examples/readme-showcase-round-1 \
  --outdir gallery/readme-showcase
PYTHONPATH=src python3 scripts/check_asset_budget.py
```

## 文档导航

- [DiagramScript 字段说明](./docs/diagram-script.md)
- [Prompt → DiagramPlan → DiagramScript](./docs/prompt-to-diagram-flow.md)
- [语义编排合约](./docs/diagram-composition-contract.md)
- [HTML runtime 与动效模式](./docs/html-runtime.md)
- [图标系统发布状态](./docs/icon-system-release-status.md)
- [Illustrated 2.5 扩展说明](./docs/illustrated-2.5-full-expansion.md)
- [Runtime 动效路线图](./docs/runtime-motion-roadmap.md)
- [发布验证证据](./docs/release-evidence.md)

## Clean-Room 边界

本仓库不是 GitHub fork，也不复制 [REFERENCES.md](./REFERENCES.md) 中参考项目的
源码、文档、图片、生成资产或仓库历史。外部项目只用于产品研究；实现、schema、
文档和生成示例均保持独立。

## License

[MIT](./LICENSE)

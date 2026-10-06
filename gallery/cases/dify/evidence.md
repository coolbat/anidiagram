# Dify 主案例试稿：从文档到答案

[中文](evidence.md) · [English](evidence.en.md)

状态：源码阅读试稿，独立语义复核待完成；没有运行 Dify 或真实模型。

- 固定版本：1.17.0，`09a855dcef24c0edc7431c46c0cfaa494481daf5`。
- 仓库：https://github.com/langgenius/dify
- 范围：自托管、本地文本、high_quality paragraph 索引、基础 CHAT、已配置且选中的内部知识库语义检索、正常路径。
- 不覆盖整个 Dify；Workflow、Chatflow、Agent、知识流水线、多模态、重排与失败分支均排除。
- 不执行被分析仓库。Compose 仅支持部署边界/默认配置；调用关系由具体函数实现支持。

## 两条路径

文档入库：控制台经 Nginx 进入 API；文件内容保存到 storage，文件与文档元数据提交到 SQL；创建文档后投递 Celery 任务。Worker 消费任务，读取文件、提取并分段，保存分段；缺少文档 embedding 缓存时调用模型接口，随后写向量库。

在线问答：Service API 经 Nginx 进入 API；基础 CHAT 的工作线程在 API 进程内。按配置/路由选中内部知识库后做语义检索，组织上下文并生成回答，以流式响应返回。查询 embedding 有 Redis 缓存；单知识库路由也可能先调用 LLM，不把本图误读为严格时序图。

三层是逻辑分组，不是容器数量。API 和 Celery Worker 可以使用同一镜像，但为独立服务。主图仅画选定依赖；SQL 与 Redis 还有未绘制的访问方。API 的 `任务 / 查询缓存` 边在两个聚焦视图中共享，分别取其对应用途。

## 重点证据（固定 SHA）

| 判断 | 源码 |
| --- | --- |
| Nginx 分发 console/API/v1 路由 | [default.conf.template L8–45](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/docker/nginx/conf.d/default.conf.template#L8-L45) |
| 上传内容与 SQL 元数据分开保存 | [file_service.py L99–125](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/services/file_service.py#L99-L125) |
| 文档提交后才投递索引任务 | [dataset_service.py L2482–2499](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/services/dataset_service.py#L2482-L2499) |
| 自托管走 priority 队列 | [proxy/base.py L79–111](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/services/document_indexing_proxy/base.py#L79-L111) |
| Worker 提取、转换、保存分段、写索引 | [indexing_runner.py L81–159](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/core/indexing_runner.py#L81-L159) |
| 先 embedding 再写向量索引 | [vector_factory.py L168–189](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/core/rag/datasource/vdb/vector_factory.py#L168-L189) |
| CHAT 在线线程不等于 Celery Worker | [chat/app_generator.py L208–272](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/core/app/apps/chat/app_generator.py#L208-L272) |
| 检索上下文进入最终 LLM prompt | [chat/app_runner.py L160–256](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/core/app/apps/chat/app_runner.py#L160-L256) |
| 查询 embedding 缓存命中直接返回 | [cached_embedding.py L194–241](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/core/rag/embedding/cached_embedding.py#L194-L241) |
| 模型调用止于插件服务 HTTP 边界 | [plugin/impl/model.py L170–217](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/core/plugin/impl/model.py#L170-L217) |

完整 32 个引用及每条边的条件位于 `dify.plan.json`；23 条必需事实位于 `facts.json`。
`accuracy.json` 中定义存在性检查与语义待复核是不同状态。作者组织的关系事实匹配图形，只证明两份表示一致，不是独立准确率。
Plugin Daemon 实现及供应商模型代码不在这次审计内；不额外画“模型厂商”节点来暗示已经审查外部实现。

## 复现

在 AniDiagram 仓库内执行，要求 Python 3.10+，本仓库已有 GSAP；不安装 Dify 依赖。

```bash
git clone --branch 1.17.0 --depth 1 https://github.com/langgenius/dify.git outputs/readme-showcase-v2/source/dify-1.17.0
python3 examples/readme-showcase-v2/dify/build.py --source outputs/readme-showcase-v2/source/dify-1.17.0
python3 -m unittest discover -s examples/readme-showcase-v2/dify -p 'test_*.py'
python3 -I scripts/run_anidiagram.py visual-check outputs/readme-showcase-v2/dify/dify.html --strict-labels --viewports 1440x1100,1920x1320 --outdir outputs/readme-showcase-v2/dify/visual
python3 -m http.server 8769 --bind 127.0.0.1 --directory outputs/readme-showcase-v2/dify
```

已有 clone 时跳过 clone；构建器核对完整 SHA 和干净状态，版本不符则拒绝执行。
构建器同时生成中英文：`index.html` / `index.en.html`。英文通过稳定 ID 映射翻译文案，保留相同拓扑、分组、方向、条件与固定源码；分别运行事实与渲染检查，不沿用另一语言产物的复核记录。
静态与交互图共用同一语义。静态版只关闭动效；几何定制不修改 ID、来源、标签、方向或条件。
图标在表现层用公共图标作显式别名映射（例如 browser → api、worker → task），保留原 semantic kind，不把任意组件自动画成 AI Agent。
本例使用 900×1130 竖向三层布局，不强求先前 Flask 试稿的 2:1 横向比例；840 px README 宽度下保持标签可读。

## 验收状态

- 固定源码及引用：构建时校验，查看 delivery / accuracy 报告。
- 语义：作者已阅读上述路径；独立复核 pending。
- 运行时：未启动 Dify、未使用供应商 API。
- 静态 / HTML 渲染：查看各自 quality 与 visual 报告；渲染通过不代替语义准确。
- 发布：仓库在 `gallery/cases/dify/` 收录此中英文解读稿。GitHub Pages 部署是独立门禁；发布不改变语义复核仍待完成的状态。

## 图标动效预览

构建动图还需要 Pillow、Playwright 和浏览器；可使用 Playwright Chromium，或在构建命令加 `--browser-channel chrome` 复用已安装的 Chrome，不自动安装依赖。WebP 直接录制已交付、开启可读标签的 HTML，使用现有 10 个图标表演，不改变架构语义。动效回执绑定 HTML 与图片哈希，测试逐一检查图标区域的帧变化，不把连线在动算成图标在动。案例页可暂停切回静态 SVG；无 JavaScript 或偏好减少动态效果时默认静态。

## 发布固定产物

构建后，在仓库根目录运行 `python3 examples/readme-showcase-v2/dify/publish.py`。脚本先核对构建清单，再将白名单文件复制到 `gallery/cases/dify/`；SVG/HTML 渲染字节及证据保持不变，仅将交付回执中的本机路径改为可移植的定位信息。发布清单记录原始回执哈希和发布文件新哈希，不复制临时截图或 Dify 源码副本。

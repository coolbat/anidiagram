#!/usr/bin/env python3
"""Build an isolated, source-pinned Dify showcase. Never modify the README."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from anidiagram.planner import compile_plan
from anidiagram.exporters import _blend_loop_seam, _write_browser_image_sequence
from english import localize_facts, localize_plan

REVISION = "09a855dcef24c0edc7431c46c0cfaa494481daf5"
REPOSITORY = "https://github.com/langgenius/dify"

# Each source is a bounded, manually read range in the pinned repository.
LOCATIONS = [
    ("web", "web/service/datasets.ts", 153, 170, "Web creates dataset documents"),
    ("nginx", "docker/nginx/conf.d/default.conf.template", 8, 45, "Nginx API routes"),
    ("deploy", "docker/docker-compose.yaml", 227, 352, "API and Worker are separate services"),
    ("plugin-deploy", "docker/docker-compose.yaml", 573, 602, "Plugin daemon service"),
    ("file", "api/services/file_service.py", 37, 125, "File bytes and SQL metadata are separate"),
    ("document", "api/services/dataset_service.py", 2482, 2499, "Commit documents before submitting indexing"),
    ("broker", "api/extensions/ext_celery.py", 113, 132, "Celery broker configuration"),
    ("broker-default", "docker/.env.example", 115, 124, "Redis broker default"),
    ("stores", "docker/.env.example", 159, 164, "Storage and vector store defaults"),
    ("postgres", "docker/docker-compose.yaml", 425, 437, "PostgreSQL deployment option"),
    ("task-proxy", "api/services/document_indexing_proxy/batch_indexing_base.py", 37, 47, "Direct Celery dispatch"),
    ("task-policy", "api/services/document_indexing_proxy/base.py", 79, 111, "Self-hosted dispatch policy"),
    ("task", "api/tasks/document_indexing_task.py", 200, 267, "Indexing task entry points"),
    ("task-run", "api/tasks/document_indexing_task.py", 49, 125, "Task invokes IndexingRunner"),
    ("index", "api/core/indexing_runner.py", 81, 159, "Extract, transform, persist segments, load index"),
    ("extract", "api/core/rag/extractor/extract_processor.py", 115, 137, "Download uploaded file for extraction"),
    ("paragraph", "api/core/rag/index_processor/processor/paragraph_index_processor.py", 134, 149, "High-quality paragraph vector indexing"),
    ("vector-create", "api/core/rag/datasource/vdb/vector_factory.py", 168, 189, "Embed documents then write vectors"),
    ("vector-query", "api/core/rag/datasource/vdb/vector_factory.py", 252, 259, "Embed query then search vectors"),
    ("doc-embedding", "api/core/rag/embedding/cached_embedding.py", 29, 103, "Document embedding SQL cache"),
    ("query-embedding", "api/core/rag/embedding/cached_embedding.py", 194, 241, "Query embedding Redis cache"),
    ("chat-api", "api/controllers/service_api/app/completion.py", 388, 419, "Generate chat and return response stream"),
    ("dispatch", "api/services/app_generate_service.py", 218, 231, "Basic CHAT dispatch"),
    ("thread", "api/core/app/apps/chat/app_generator.py", 208, 272, "API-local thread and ChatAppRunner"),
    ("chat", "api/core/app/apps/chat/app_runner.py", 160, 256, "Retrieve context then generate answer"),
    ("retrieval", "api/core/rag/retrieval/dataset_retrieval.py", 660, 754, "Selected internal dataset retrieval"),
    ("search", "api/core/rag/datasource/retrieval_service.py", 303, 347, "Semantic vector retrieval"),
    ("model", "api/core/model_manager.py", 181, 266, "LLM and embedding model invocation"),
    ("plugin-runtime", "api/core/plugin/impl/model_runtime.py", 309, 351, "Model runtime delegates to plugin client"),
    ("plugin-llm", "api/core/plugin/impl/model.py", 170, 217, "Plugin daemon LLM HTTP contract"),
    ("plugin-embedding", "api/core/plugin/impl/model.py", 360, 399, "Plugin daemon embedding HTTP contract"),
    ("plugin-base", "api/core/plugin/impl/base.py", 98, 165, "HTTP client points at plugin daemon"),
]


def make_plan(language: str = "zh-CN") -> dict:
    if language not in ("zh-CN", "en"):
        raise ValueError(f"Unsupported showcase language: {language}")
    entities = [
        ("web", "Web 控制台", "浏览器侧\n上传 · 创建文档", "browser", "access", ["web", "file"]),
        ("nginx", "Nginx", "反向代理\n按 URL 转发", "gateway", "access", ["nginx"]),
        ("caller", "API 调用方", "问答请求\n流式响应", "client", "access", ["chat-api", "nginx"]),
        ("api", "API 服务", "Chat · RAG\n进程内线程", "server", "services", ["deploy", "dispatch", "thread", "chat", "file"]),
        ("worker", "索引 Worker", "Celery 进程\n提取 · 分段", "worker", "services", ["deploy", "task", "index"]),
        ("plugin", "插件服务", "Plugin Daemon\n模型调用边界", "plugin", "services", ["plugin-deploy", "plugin-llm", "plugin-embedding", "plugin-base"]),
        ("files", "文件存储", "原始文件\n默认本地存储", "storage", "data", ["file", "extract", "deploy", "stores"]),
        ("redis", "Redis", "任务 Broker\n查询向量缓存", "queue", "data", ["broker", "broker-default", "query-embedding"]),
        ("sql", "SQL 数据库", "元数据 · 分段\n此例 PostgreSQL", "database", "data", ["file", "index", "postgres"]),
        ("vector", "向量库", "文档向量索引\n此例 Weaviate", "database", "data", ["vector-create", "vector-query", "stores"]),
    ]
    # Edges show selected interactions, not a single global execution order.
    relations = [
        ("web-nginx", "web", "nginx", "上传 / 建文档", "http", "forward", "Console request succeeds", "ingest", ["web", "file", "nginx"]),
        ("caller-nginx", "caller", "nginx", "问答 / SSE", "http", "bidirectional", "Basic CHAT; streaming response mode", "query", ["nginx", "chat-api"]),
        ("nginx-api", "nginx", "api", "API 请求 / 响应", "http", "bidirectional", "Console API or /v1 route", "shared", ["nginx", "chat-api"]),
        ("api-files", "api", "files", "保存文件", "storage-access", "forward", "Local uploaded text file; validation succeeds", "ingest", ["file"]),
        ("api-sql", "api", "sql", "保存元数据", "database-access", "forward", "Upload and document creation succeed", "ingest", ["file", "document"]),
        ("api-redis", "api", "redis", "任务 / 查询缓存", "dependency", "forward", "Index dispatch after document commit; query embedding cache access on semantic retrieval", "shared", ["document", "task-proxy", "task-policy", "broker", "broker-default", "query-embedding"]),
        ("redis-worker", "redis", "worker", "领取索引任务", "task-delivery", "forward", "Worker consumes Celery broker; self-hosted priority_dataset queue", "ingest", ["broker", "task-policy", "task", "task-run"]),
        ("worker-files", "worker", "files", "读取原文件", "storage-access", "forward", "FILE source in extraction", "ingest", ["task-run", "index", "extract"]),
        ("worker-sql", "worker", "sql", "保存分段", "database-access", "forward", "Successful paragraph indexing", "ingest", ["index", "doc-embedding"]),
        ("worker-vector", "worker", "vector", "写入索引", "vector-access", "forward", "high_quality paragraph indexing; embedding succeeds", "ingest", ["index", "paragraph", "vector-create"]),
        ("api-vector", "api", "vector", "语义检索", "vector-access", "forward", "Dataset configured and selected; internal high_quality semantic retrieval; filters permit results", "query", ["chat", "retrieval", "search", "vector-query"]),
        ("worker-plugin", "worker", "plugin", "文档向量化", "model-invocation", "forward", "Document embedding cache miss; model configured", "ingest", ["vector-create", "doc-embedding", "model", "plugin-embedding", "plugin-base"]),
        ("api-plugin", "api", "plugin", "Embedding / LLM", "model-invocation", "forward", "Query embedding cache miss and/or LLM invocation; validated normal CHAT path", "query", ["chat", "query-embedding", "model", "plugin-runtime", "plugin-llm", "plugin-embedding", "plugin-base"]),
    ]
    result = {
        "version": "0.2",
        "semantic": {
            "language": "zh-CN", "title": "Dify · 文档如何成为答案",
            "subtitle": "1.17.0 · 三层协作 · 知识库入库与基础 Chat 问答",
            "summary": "蓝色为文档入库，绿色为在线问答，灰色为共享接口。箭头表示所选调用或任务交付，不代表耗时、所有依赖或唯一执行顺序。",
            "intent": {"diagram_kind": "architecture", "primary_question": "索引和在线问答经过哪些服务，分别读写什么？",
                       "audience": ["首次了解 Dify 架构的开发者"],
                       "scope": "Dify 1.17.0 自托管；本地文本上传；high_quality paragraph 索引；基础 AppMode.CHAT；已配置且选中的内部知识库、semantic_search；正常成功路径。",
                       "exclusions": ["不覆盖整个 Dify：Workflow、Chatflow、Agent、知识流水线、多模态、重排、错误与重试不在此图。",
                                      "逻辑三层不是三个部署服务。Chat 与 RAG 是 API 内部代码；不是独立微服务，也不代表其他模式没有异步队列。",
                                      "模型调用追到 Plugin Daemon 的 HTTP 接口；其插件运行机制及下游模型厂商未在本仓库核验，故不绘制下游连线。",
                                      "SQL / Redis 的其他消费者、Web 服务端托管、鉴权、回调细节和缓存命中分支在概览中省略。",
                                      "没有运行 Dify 或调用真实模型；独立语义复核待完成。"]},
            "entities": [{"id": key, "label": label, "description": caption, "kind": kind,
                          "role": "process", "importance": "primary", "source_refs": [f"src-{ref}" for ref in refs]}
                         for key, label, caption, kind, group, refs in entities],
            "groups": [{"id": key, "label": label, "kind": "logical-layer", "members": [e[0] for e in entities if e[4] == key]}
                       for key, label in [("access", "01  接入层 · 请求从哪里进入"), ("services", "02  执行层 · 谁处理请求与索引"), ("data", "03  数据层 · 内容、任务与索引")]],
            "relations": [{"id": key, "from": source, "to": target, "label": label, "kind": kind,
                           "direction": direction, "condition": condition, "importance": "primary",
                           "source_refs": [f"src-{ref}" for ref in refs]}
                          for key, source, target, label, kind, direction, condition, flow, refs in relations],
            "flows": [
                {"id": "index-path", "label": "索引投递与写入", "importance": "primary", "repeat": "event-driven",
                 "relation_ids": ["web-nginx", "nginx-api", "api-redis", "redis-worker", "worker-vector"]},
                {"id": "retrieval-path", "label": "问答中的检索调用", "importance": "primary", "repeat": "event-driven",
                 "relation_ids": ["caller-nginx", "nginx-api", "api-vector"]},
            ],
            "sources": [{"id": f"src-{key}", "type": "repository", "title": title,
                         "repository": {"url": REPOSITORY, "revision": REVISION, "path": path, "line": first, "end_line": last}}
                        for key, path, first, last, title in LOCATIONS],
        },
        "presentation": {"icon_system": "auto", "style": "minimal-light", "layout": "layered", "motion": "showcase-v1"},
        "presentation_sources": {"style": "model", "layout": "model"},
    }
    result["reader"] = {"enabled": True, "views": [{"id": flow, "label": label, "relation_ids": [r[0] for r in relations if r[7] in (flow, "shared")]}
                                                  for flow, label in [("ingest", "文档入库"), ("query", "在线问答")]]}
    return localize_plan(result) if language == "en" else result


def make_facts(plan: dict) -> dict:
    claims = [{"id": f"relation-{r['id']}", "subject": r["id"], "predicate": "relation",
               "object": {k: r[k] for k in ("from", "to", "direction", "kind")}, "condition": r["condition"],
               "source_refs": r["source_refs"], "confidence": "asserted", "required": True}
              for r in plan["semantic"]["relations"]]
    for key, subject, content, refs in [
        ("thread-not-celery", "api", "基础 CHAT 的 ChatAppGenerator 创建 threading.Thread 并调用 ChatAppRunner；这里的 worker 是 API 内线程，不是 Celery Worker。", ["dispatch", "thread", "chat"]),
        ("separate-storage", "files", "上传文件内容由 storage.save 保存，SQL 保存 UploadFile 元数据。", ["file"]),
        ("commit-before-queue", "api-redis", "创建文档先提交 SQL，再通过 DocumentIndexingTaskProxy.delay 投递索引任务。", ["document", "task-policy", "task-proxy"]),
        ("cache-condition", "api-plugin", "查询 Embedding 命中 Redis 缓存时直接使用缓存，不是每次检索都调用 Embedding 模型。", ["query-embedding"]),
        ("retrieval-condition", "api-vector", "本图检索发生于已配置且选中的内部知识库；单知识库路由也可能先调用 LLM，主图不是严格时序。", ["chat", "retrieval"]),
        ("plugin-boundary", "plugin", "主仓库用 HTTP 调用 Plugin Daemon 的模型接口；本次审阅没有覆盖插件服务实现与具体模型供应商。", ["plugin-base", "plugin-llm", "plugin-embedding"]),
    ]:
        claims.append({"id": key, "subject": subject, "predicate": "behavior", "object": content,
                       "condition": "", "source_refs": [f"src-{s}" for s in refs], "confidence": "asserted", "required": True})
    for subject, ref, path, symbol in [
        ("files", "file", "api/services/file_service.py", "FileService.upload_file"),
        ("worker", "index", "api/core/indexing_runner.py", "IndexingRunner.run"),
        ("vector", "vector-query", "api/core/rag/datasource/vdb/vector_factory.py", "Vector.search_by_vector"),
        ("plugin", "plugin-llm", "api/core/plugin/impl/model.py", "PluginModelClient.invoke_llm"),
    ]:
        claims.append({"id": f"definition-{ref}", "subject": subject, "predicate": "python-definition",
                       "object": {"path": path, "symbol": symbol}, "condition": "", "source_refs": [f"src-{ref}"], "confidence": "asserted", "required": True})
    facts = {"version": "0.1", "claims": claims}
    return localize_facts(facts) if plan["semantic"]["language"] == "en" else facts


def author_geometry(spec: dict, semantic: dict) -> dict:
    result = copy.deepcopy(spec)
    result["canvas"] = {"width": 900, "height": 1130}
    positions = {"web": [55, 175], "nginx": [335, 175], "caller": [615, 175],
                 "api": [55, 435], "worker": [335, 435], "plugin": [615, 435],
                 "files": [55, 790], "redis": [335, 790], "sql": [615, 790], "vector": [335, 975]}
    for node in result["nodes"]:
        node.update(position=positions[node["id"]], size=[230, 110])
        node.pop("step", None)
        # Public presentation aliases; preserve the original semantic kind.
        icons = {"web": "api", "caller": "user", "worker": "task", "plugin": "tool", "files": "document-store", "vector": "vector-database"}
        if node["id"] in icons:
            node.update(icon=icons[node["id"]], icon_resolution="alias")
    for group in result["groups"]:
        group.update(bounds={"access": [20, 125, 860, 195], "services": [20, 375, 860, 215], "data": [20, 725, 860, 385]}[group["id"]], role="neutral")
    paths = {
        "web-nginx": [[285, 230], [335, 230]],
        "caller-nginx": [[615, 230], [565, 230]],
        "nginx-api": [[450, 285], [450, 350], [170, 350], [170, 435]],
        "api-files": [[110, 545], [110, 790]],
        "api-sql": [[245, 545], [245, 615], [820, 615], [820, 790]],
        "api-redis": [[200, 545], [200, 680], [395, 680], [395, 790]],
        "redis-worker": [[480, 790], [480, 545]],
        "worker-files": [[365, 545], [365, 650], [245, 650], [245, 790]],
        "worker-sql": [[525, 545], [525, 650], [680, 650], [680, 790]],
        "worker-vector": [[565, 525], [585, 525], [585, 1030], [565, 1030]],
        "api-vector": [[55, 490], [35, 490], [35, 1030], [335, 1030]],
        "worker-plugin": [[565, 480], [615, 480]],
        "api-plugin": [[240, 435], [240, 410], [730, 410], [730, 435]],
    }
    shared = {"nginx-api", "api-redis"}
    query = {"caller-nginx", "api-vector", "api-plugin"}
    for edge in result["edges"]:
        key = edge["semantic_relation_id"]
        edge.pop("step", None)
        edge.update(points=paths[key], route="orthogonal", animated=True,
                    stroke="#64748b" if key in shared else "#0f766e" if key in query else "#2563eb")
    assert result["evidence"] == spec["evidence"], "Geometry cannot rewrite source bindings"
    assert {n["id"] for n in result["nodes"]} == {e["id"] for e in semantic["entities"]}
    for edge in result["edges"]:
        original = next(r for r in semantic["relations"] if r["id"] == edge["semantic_relation_id"])
        assert all(edge[k] == original[k] for k in ("from", "to", "direction", "condition", "label"))
    return result


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_variant(source: Path, out: Path, language: str, browser_channel: str | None = None) -> list[str]:
    stem = "dify-en" if language == "en" else "dify"
    suffix = ".en" if language == "en" else ""
    facts_name, accuracy_name = f"facts{suffix}.json", f"accuracy{suffix}.json"
    plan = make_plan(language)
    spec = author_geometry(compile_plan(plan), plan["semantic"])
    static = copy.deepcopy(spec)
    static["motion"]["profile"] = "off"
    static["resolved_presentation"]["motion"] = {"value": "off", "source": "explicit"}
    style = {"name": "readme-dify-trial", "canvas": {"background": "#ffffff", "text": "#172033", "muted": "#526176", "grid": "#ffffff"},
             "title": {"accent": "#2563eb", "highlight": "#eff6ff"}, "node": {"radius": 10, "stroke_width": 1.2},
             "effects": {"frame_opacity": 0, "grid_opacity": 0},
             "roles": {"process": {"stroke": "#94a3b8", "fill": "#ffffff", "text": "#172033"},
                       "neutral": {"stroke": "#cbd5e1", "fill": "#f1f5f9", "text": "#334155"}}}
    for name, value in ((f"{stem}.plan.json", plan), (f"{stem}.diagram.json", spec), (f"{stem}-static.diagram.json", static),
                        (facts_name, make_facts(plan)), ("style.json", style)):
        write_json(out / name, value)
    launcher = [sys.executable, "-I", str(ROOT / "scripts/run_anidiagram.py")]
    checked = subprocess.run(launcher + ["accuracy-check", str(out / f"{stem}.diagram.json"), "--facts", str(out / facts_name),
                                        "--repo-root", str(source), "--strict", "--out", str(out / accuracy_name)], check=False, capture_output=True, text=True)
    if checked.returncode not in (0, 1):
        print(checked.stdout + checked.stderr)
        raise SystemExit(checked.returncode)
    accuracy = json.loads((out / accuracy_name).read_text())
    print(json.dumps({"language": language, "accuracy": accuracy["status"], "gates": accuracy["gates"]}))
    if any(c.get("status") == "contradicted" for c in accuracy.get("claims", [])):
        raise SystemExit("Contradicted fact; inspect accuracy.json")
    for name in (stem, f"{stem}-static"):
        rendered = subprocess.run(launcher + ["--spec", str(out / f"{name}.diagram.json"), "--style", str(out / "style.json"),
                                   "--repo-root", str(source), "--outdir", str(out), "--basename", name, "--readable-labels",
                                   "--formats", "svg,html,quality", "--deliver", "--runtime-dependency", "inline",
                                   "--runtime-source", str(ROOT / "node_modules/gsap/dist/gsap.min.js")], check=False, capture_output=True, text=True)
        if rendered.returncode:
            print(rendered.stdout + rendered.stderr)
            raise SystemExit(rendered.returncode)
        report = json.loads(rendered.stdout)
        print(json.dumps({"render": name, "ok": report["ok"], "quality": report["outputs"]["quality"]["summary"]}))
    names = [f"{stem}.plan.json", f"{stem}.diagram.json", f"{stem}-static.diagram.json", facts_name, accuracy_name]
    names += [f"{name}.{ext}" for name in (stem, f"{stem}-static") for ext in ("svg", "html", "quality.json", "delivery.json")]
    command = ["node", str(HERE / "capture_motion.mjs"), str(out), stem]
    if browser_channel:
        command.append(browser_channel)
    subprocess.run(command, check=True)
    frames = [out / f"{stem}-frames/frame-{index:04d}.png" for index in range(24)]
    _blend_loop_seam(frames, 4)
    result = _write_browser_image_sequence("webp", frames, out / f"{stem}-motion.webp", 12, style, 80)
    if result["status"] != "written":
        raise RuntimeError(f"Animated preview encoding failed: {result}")
    receipt_path = out / f"{stem}-motion.json"
    receipt = json.loads(receipt_path.read_text())
    receipt.update(webp_sha256=hashlib.sha256((out / f"{stem}-motion.webp").read_bytes()).hexdigest(), loop_blend_frames=4, quality=80)
    write_json(receipt_path, receipt)
    names += [f"{stem}-motion.webp", f"{stem}-motion.json"]
    return names


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--outdir", type=Path, default=ROOT / "outputs/readme-showcase-v2/dify")
    parser.add_argument("--browser-channel", choices=("chrome", "msedge"), help="Use an already installed browser instead of Playwright Chromium")
    args = parser.parse_args()
    source, out = args.source.resolve(), args.outdir.resolve()
    sha = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if sha != REVISION or subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"], text=True).strip():
        raise SystemExit("Refusing source drift: expected the clean pinned Dify 1.17.0 checkout")
    out.mkdir(parents=True, exist_ok=True)
    names = [name for language in ("zh-CN", "en") for name in build_variant(source, out, language, args.browser_channel)]
    shared = ("index.html", "index.en.html", "evidence.md", "evidence.en.md", "showcase.css", "preview-motion.js")
    for name in shared:
        (out / name).write_bytes((HERE / name).read_bytes())
    names += ["style.json", *shared]
    write_json(out / "manifest.json", {"status": "draft", "repository": REPOSITORY, "revision": REVISION,
                                      "source_root": str(source), "independent_semantic_review": "pending", "dify_runtime": "not run",
                                      "languages": {"zh-CN": "index.html", "en": "index.en.html"},
                                      "source_files": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in ("build.py", "english.py", "publish.py", "capture_motion.mjs", *shared)},
                                      "files": {name: hashlib.sha256((out / name).read_bytes()).hexdigest() for name in names}})
    print(f"Drafts: {out / 'index.html'} and {out / 'index.en.html'}")


if __name__ == "__main__":
    main()

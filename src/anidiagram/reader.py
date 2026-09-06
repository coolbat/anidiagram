"""Optional reading surfaces; canonical SVG and motion stay independent."""

from html import escape
import json

from .resources import resource_path


def validate_reader(value, nodes, edges):
    if not isinstance(value, dict) or set(value) - {"enabled"} or type(value.get("enabled")) is not bool:
        raise ValueError("reader must contain enabled: true or false")
    if value["enabled"]:
        ids = [edge.get("semantic_relation_id", edge.get("id")) for edge in edges]
        ids = [item for item in ids if item is not None]
        if len(ids) != len(set(ids)):
            raise ValueError("reader requires unique relation IDs")


def reader_data(scene):
    ids = [edge.semantic_relation_id for edge in scene.edges if edge.semantic_relation_id]
    if len(ids) != len(set(ids)):
        raise ValueError("reader requires unique semantic_relation_id values")
    return {
        "version": 1,
        "nodes": [{"id": n.node_id, "label": n.label, "role": n.role, "kind": n.semantic_kind or "component"} for n in scene.nodes],
        "edges": [{"id": e.semantic_relation_id or f"@edge:{i}", "from": e.source, "to": e.target,
                   "label": e.label, "direction": e.direction, "index": i} for i, e in enumerate(scene.edges)],
        "evidence": scene.source_evidence,
    }


def add_reader(html, scene, locale):
    zh = locale == "zh-CN"
    labels = ({"reader": "探索架构", "search": "搜索节点", "source": "起点", "target": "终点", "role": "角色",
               "all": "全部", "neighbors": "相邻节点", "upstream": "上游", "downstream": "下游", "route": "最短路径",
               "reset": "清除筛选", "copy": "复制阅读链接", "select": "选择节点", "none": "没有找到有向路径",
               "scope": "仅查询图中已定义的关系；无向边只参与邻接查询。", "evidence": "源码引用", "copied": "链接已复制"} if zh else
              {"reader": "Explore architecture", "search": "Find nodes", "source": "From", "target": "To", "role": "Role",
               "all": "All", "neighbors": "Neighbors", "upstream": "Upstream", "downstream": "Downstream", "route": "Shortest route",
               "reset": "Clear filters", "copy": "Copy reading link", "select": "Select a node", "none": "No authored directed route",
               "scope": "Queries use authored relationships only; undirected edges appear in neighbors only.", "evidence": "Source references", "copied": "Link copied"})
    options = ''.join(f'<option value="{escape(n.node_id, quote=True)}">{escape(n.label)}</option>' for n in scene.nodes)
    roles = ''.join(f'<option value="{escape(role)}">{escape(role)}</option>' for role in sorted({n.role for n in scene.nodes}))
    controls = f'''<section id="diagram-reader" aria-label="{labels['reader']}">
<details id="reader-controls"><summary>{labels['reader']}</summary><div class="reader-fields">
<label>{labels['search']} <input id="reader-search" type="search"></label>
<label>{labels['source']} <select id="reader-source"><option value="">{labels['select']}</option>{options}</select></label>
<label>{labels['target']} <select id="reader-target"><option value="">{labels['select']}</option>{options}</select></label>
<label>{labels['role']} <select id="reader-role"><option value="">{labels['all']}</option>{roles}</select></label>
{''.join(f'<button type="button" data-reader-mode="{mode}">{labels[mode]}</button>' for mode in ('neighbors', 'upstream', 'downstream', 'route'))}
<button type="button" id="reader-clear">{labels['reset']}</button><button type="button" id="reader-copy">{labels['copy']}</button>
<input id="reader-link" aria-label="URL" readonly hidden></div><p class="reader-note">{labels['scope']}</p></details>
<div id="reader-result" role="status" aria-live="polite"></div><ul id="reader-evidence"></ul></section>'''
    css = '''<style id="reader-style">
main:has(#diagram-reader){display:flex;flex-direction:column;height:100vh;min-height:0}
main:has(#diagram-reader) .stage{flex:1;min-height:200px}
#diagram-reader{font-size:14px}#diagram-reader summary{cursor:pointer;padding:6px 0}
.reader-fields{display:flex;flex-wrap:wrap;align-items:end;gap:8px}.reader-fields label{display:grid;gap:4px}
.reader-fields input,.reader-fields select{box-sizing:border-box;max-width:240px;padding:6px;border-radius:5px;color:inherit;background:#111827;border:1px solid #64748b;font:inherit}
#reader-result{overflow-wrap:anywhere;max-height:100px;overflow:auto}.reader-note{color:#cbd5e1;margin:6px 0}
#reader-evidence:empty{display:none}#reader-evidence{max-height:100px;overflow:auto;margin:6px 0}
@media(max-width:600px){main:has(#diagram-reader){height:auto;min-height:100vh}main:has(#diagram-reader) .stage{height:65vh;flex:none}}
@media print{#diagram-reader{display:none}}
</style><style id="reader-selection-style"></style>'''
    payload = {**reader_data(scene), "labels": labels}
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c").replace("&", "\\u0026")
    scripts = '<script type="application/json" id="anidiagram-reader-data">' + data + '</script>'
    for name in ("reader-graph.js", "diagram-reader.js"):
        scripts += '<script>\n' + resource_path("runtime", name).read_text() + '\n</script>'
    html = html.replace("</head>", css + "</head>", 1)
    html = html.replace('    <p id="runtime-warning"', controls + '\n    <p id="runtime-warning"', 1)
    return html.replace("</body>", scripts + "</body>", 1)


def evidence_markup(scene, locale):
    title = "源码引用已核验" if locale == "zh-CN" else "Verified source references"
    note = ("核验范围：固定提交中的文件和行号；架构含义仍需评审。" if locale == "zh-CN" else
            "Verification covers files and lines at the pinned commit; architectural claims still need review.")
    rows = []
    for source in scene.source_evidence["sources"]:
        subjects = [key for key, refs in scene.source_evidence["subjects"].items() if source["id"] in refs]
        label = source["title"] + " · " + source["repository"]["revision"][:7]
        rows.append(f'<li><a href="{escape(source["href"], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(label)}</a> {escape(", ".join(subjects))}</li>')
    return f'<details id="source-evidence"><summary>{title}</summary><p>{note}</p><ul>{"".join(rows)}</ul></details>\n'

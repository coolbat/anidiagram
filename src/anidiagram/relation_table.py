"""Opt-in, visible rendering-fidelity fallback; authored facts are not certified facts."""

import json

from .renderer_svg import esc


def add_relation_table(html, scene, locale):
    zh = locale == 'zh-CN'
    nodes = {node.node_id: node.label for node in scene.nodes}
    edges = [{'id': edge.semantic_relation_id or f'@edge:{index}', 'source': edge.source,
              'target': edge.target, 'direction': edge.direction, 'label': edge.label,
              'kind': edge.semantic_kind or '', 'condition': edge.condition or '',
              'protocol': edge.protocol or ''} for index, edge in enumerate(scene.edges)]
    rows = []
    for edge in edges:
        arrow = {'forward': '→', 'bidirectional': '↔', 'undirected': '—'}[edge['direction']]
        endpoints = f"{nodes[edge['source']]} [{edge['source']}] {arrow} {nodes[edge['target']]} [{edge['target']}]"
        values = [edge['id'], endpoints, edge['label'], edge['kind'], edge['condition'], edge['protocol']]
        rows.append('<tr data-relation-id="' + esc(edge['id']) + '">' +
                    ''.join('<td>' + esc(value) + '</td>' for value in values) + '</tr>')
    headings = ['ID', '方向与端点', '完整标签', '关系类型', '条件', '协议'] if zh else ['ID', 'Direction / endpoints', 'Full label', 'Kind', 'Condition', 'Protocol']
    title = '关系明细（按输入声明，未经语义认证）' if zh else 'Relation details (authored, not semantically certified)'
    sources = 'verified' if scene.source_evidence else 'not-requested'
    status = (f'原尺寸滚动阅读 · 源码引用：{sources} · 语义复核：待复核 · 呈现可读性：待 visual-check 验收' if zh else
              f'Native-size scrollable diagram · Source references: {sources} · Semantic review: pending · Rendered readability: awaiting visual-check')
    table = ('<section id="relation-table" aria-label="' + title + '"><h2>' + title + '</h2><p>' + status +
             '</p><div class="relation-scroll" tabindex="0" role="region" aria-label="' + title + '"><table><thead><tr>' +
             ''.join('<th scope="col">' + heading + '</th>' for heading in headings) +
             '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div></section>')
    data = {'edges': edges, 'source_references': sources, 'semantic_review': 'pending'}
    metadata = '<script type="application/json" id="anidiagram-readability-data">' + json.dumps(data, ensure_ascii=False).replace('</', '<\\/') + '</script>'
    css = '''<style>
main:has(#relation-table){display:flex;height:100vh;min-height:0;flex-direction:column}
main:has(#relation-table) .stage{flex:1;min-height:100px;overflow:auto}
main:has(#relation-table) #viewport svg{width:auto;height:auto}
#relation-table{flex:none;color:#e2e8f0;font:13px system-ui}
#relation-table h2{font-size:14px;margin:0 0 4px}
#relation-table p{margin:0 0 6px;color:#cbd5e1;font-size:12px}
#relation-table .relation-scroll{max-height:150px;overflow:auto;border:1px solid #475569;border-radius:6px}
#relation-table table{width:100%;border-collapse:collapse;text-align:left}
#relation-table th,#relation-table td{padding:6px 10px;border-bottom:1px solid #334155;overflow-wrap:anywhere}
#relation-table th{position:sticky;top:0;background:#1e293b}
#relation-table .relation-scroll:focus-visible{outline:3px solid #38bdf8;outline-offset:2px}
</style>'''
    return html.replace('</head>', css + '</head>', 1).replace('id="stage"', 'id="stage" data-readable-scroll="true"', 1).replace('  </main>', table + '\n  </main>', 1).replace('</body>', metadata + '</body>', 1)

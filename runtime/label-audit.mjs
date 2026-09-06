/* Read-only browser geometry audit. This function is serialized into Playwright's page. */
export function auditLabels() {
  const issues = [];
  const fail = (code, details = {}) => issues.push({ code, ...details });
  const normalize = text => (text || '').replace(/\s+/g, ' ').trim();
  const box = element => {
    const b = element.getBoundingClientRect();
    return { x: b.x, y: b.y, width: b.width, height: b.height };
  };
  const overlap = (a, b) => a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
  const visible = element => {
    for (let item = element; item; item = item.parentElement) {
      const css = getComputedStyle(item);
      if (css.display === 'none' || css.visibility !== 'visible' || Number(css.opacity) < 0.1) return false;
    }
    return Boolean(element && box(element).width && box(element).height);
  };
  let data;
  try { data = JSON.parse(document.getElementById('anidiagram-readability-data')?.textContent || 'null'); }
  catch { fail('invalid-expectations'); }
  if (!data || !Array.isArray(data.edges)) {
    return { status: 'unavailable', issues: [{ code: 'missing-readability-expectations', hint: 'Generate HTML with --readable-labels; use a source-bound oracle for legacy artifacts.' }], edges: [] };
  }
  const svg = document.querySelector('#viewport svg') || document.querySelector('svg');
  if (!svg) return { status: 'failed', issues: [{ code: 'missing-svg' }], edges: [] };
  const canvas = box(svg);
  const groups = [...svg.querySelectorAll('g.edge')];
  const nodeElements = [...svg.querySelectorAll('g.node[id]')];
  const nodes = nodeElements.map(el => ({ id: el.id.slice(5), box: box(el.querySelector('.node-surface') || el) }));
  if (groups.length !== data.edges.length) fail('edge-count', { expected: data.edges.length, actual: groups.length });
  const table = document.getElementById('relation-table');
  const rows = [...(table?.querySelectorAll('tbody tr') || [])];
  if (!visible(table) || rows.length !== data.edges.length) fail('relation-table-missing-or-hidden');
  const measured = [];
  for (const [index, expected] of data.edges.entries()) {
    const group = groups[index], id = expected.id;
    if (!group) { fail('edge-missing', { id }); continue; }
    const label = group.querySelector('.edge-label');
    const actual = normalize(label?.textContent), bounds = label ? box(label) : null;
    if (actual !== normalize(expected.label)) fail('label-content', { id, expected: expected.label, actual });
    if (expected.label && !visible(label)) fail('label-not-visible', { id });
    if (expected.label && bounds?.height < 10) fail('label-too-small', { id, screenHeight: bounds.height });
    if (expected.label && group.dataset.labelPlacement !== 'placed') fail('label-unplaced', { id });
    if (actual && bounds) {
      for (const node of nodes) if (overlap(bounds, node.box)) fail('label-node-overlap', { id, node: node.id });
      for (const previous of measured) if (previous.label && overlap(bounds, previous.bounds)) fail('label-label-overlap', { id, other: previous.id });
      if (bounds.x < canvas.x || bounds.y < canvas.y || bounds.x + bounds.width > canvas.x + canvas.width || bounds.y + bounds.height > canvas.y + canvas.height) fail('label-outside-canvas', { id });
    }
    const cells = rows[index]?.querySelectorAll('td');
    if (!cells || cells.length !== 6 || rows[index].dataset.relationId !== id) fail('relation-row', { id });
    else {
      for (const [offset, field] of [[0, 'id'], [2, 'label'], [3, 'kind'], [4, 'condition'], [5, 'protocol']]) {
        if (normalize(cells[offset].textContent) !== normalize(expected[field])) fail('relation-field', { id, field });
      }
      const arrow = { forward: '→', bidirectional: '↔', undirected: '—' }[expected.direction];
      const endpoints = cells[1].textContent;
      if (!arrow || !endpoints.includes(`[${expected.source}] ${arrow} `) || !endpoints.includes(`[${expected.target}]`)) fail('relation-endpoints', { id });
    }
    const line = group.querySelector('.edge-draw');
    if (!line) { fail('missing-edge-path', { id }); continue; }
    const markerStart = line.getAttribute('marker-start'), markerEnd = line.getAttribute('marker-end');
    if (Boolean(markerStart) !== (expected.direction === 'bidirectional') || Boolean(markerEnd) !== (expected.direction !== 'undirected')) fail('arrow-direction', { id });
    for (const ref of [markerStart, markerEnd].filter(Boolean)) {
      const markerId = /^url\(#(.+)\)$/.exec(ref)?.[1];
      const marker = markerId && document.getElementById(markerId);
      if (!marker?.querySelector('path') || marker.getAttribute('orient') !== (expected.direction === 'bidirectional' ? 'auto-start-reverse' : 'auto')) fail('arrow-marker', { id });
    }
    const transform = line.getScreenCTM();
    const scale = transform && Math.max(Math.hypot(transform.a, transform.b), Math.hypot(transform.c, transform.d));
    if (!scale || !line.getTotalLength()) fail('path-not-visible', { id });
    else {
      for (const [at, nodeId, endpoint] of [[0, expected.source, 'start'], [line.getTotalLength(), expected.target, 'end']]) {
        const local = line.getPointAtLength(at), point = new DOMPoint(local.x, local.y).matrixTransform(transform);
        const n = nodes.find(node => node.id === nodeId)?.box;
        if (!n) { fail('missing-endpoint-node', { id, nodeId }); continue; }
        const right = n.x + n.width, bottom = n.y + n.height;
        const inside = point.x >= n.x && point.x <= right && point.y >= n.y && point.y <= bottom;
        const distance = inside ? Math.min(point.x-n.x, right-point.x, point.y-n.y, bottom-point.y) :
          Math.hypot(Math.max(n.x-point.x, 0, point.x-right), Math.max(n.y-point.y, 0, point.y-bottom));
        if (distance > 14 * scale) fail('path-wrong-endpoint', { id, endpoint, nodeId, distance });
      }
    }
    measured.push({ id, label: actual, bounds, direction: expected.direction });
  }
  return { status: issues.length ? 'failed' : 'passed', issues, edges: measured,
    semantic_review: 'not-checked', source_references: 'not-reverified',
    scope: 'Text, table fields, node/label bounds and endpoint/marker geometry in frozen reduced-motion HTML. Not a semantic or comprehensive visual approval.' };
}

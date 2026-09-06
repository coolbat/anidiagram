/* Portable selection summary. Every listed relationship retains its authored direction. */
(function () {
  "use strict";
  const esc = value => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
  function buildCard(data, selection) {
    const labels = data.labels;
    if (!selection.nodes.length) throw new Error(labels.card_empty);
    if (selection.nodes.length > 8 || selection.edges.length > 8) throw new Error(labels.card_limit);
    const nodes = new Map(data.nodes.map(node => [node.id, node]));
    const edges = new Map(data.edges.map(edge => [edge.id, edge]));
    const context = document.createElement("canvas").getContext("2d");
    function lines(value, width, size, limit) {
      context.font = `${size}px system-ui`;
      const rows = [""];
      for (const char of Array.from(value)) {
        if (context.measureText(rows.at(-1) + char).width > width) rows.push("");
        rows[rows.length - 1] += char;
      }
      if (rows.length > limit) throw new Error(labels.card_text);
      return rows;
    }
    function text(value, x, y, width, size, limit = 2, color = "#172033") {
      const rows = lines(String(value), width, size, limit);
      return `<text x="${x}" y="${y}" font-size="${size}" fill="${color}">` + rows.map((row, index) => `<tspan x="${x}" dy="${index ? size + 3 : 0}">${esc(row)}</tspan>`).join("") + "</text>";
    }
    const selectedNodes = selection.nodes.map(id => nodes.get(id));
    const selectedEdges = selection.edges.map(id => edges.get(id));
    if (selectedNodes.some(item => !item) || selectedEdges.some(item => !item)) throw new Error(labels.card_empty);
    const metadata = { schema: "anidiagram-share-card-0.1", graph_sha256: data.graph_sha256,
                       nodes: selectedNodes, edges: selectedEdges };
    const count = Math.max(selectedNodes.length, selectedEdges.length);
    const rowHeight = Math.min(95, Math.floor(380 / count));
    const rowFont = count <= 4 ? 24 : 16;
    let body = `<rect width="1200" height="630" rx="24" fill="#f8fafc"/><rect x="32" y="32" width="8" height="66" rx="4" fill="#2563eb"/>`;
    body += text(data.title, 60, 60, 1080, 30, 2);
    body += text(labels.nodes, 48, 146, 370, 18, 1, "#475569") + text(labels.edges, 470, 146, 680, 18, 1, "#475569");
    selectedNodes.forEach((node, index) => {
      const y = 192 + index * rowHeight;
      body += `<rect x="40" y="${y - 24}" width="400" height="${rowHeight - 4}" rx="7" fill="#e8efff"/>` + text(node.label, 54, y - 4, 365, rowFont);
    });
    selectedEdges.forEach((edge, index) => {
      const arrow = edge.direction === "bidirectional" ? " ↔ " : edge.direction === "undirected" ? " — " : " → ";
      const label = nodes.get(edge.from).label + arrow + nodes.get(edge.to).label + (edge.label ? " · " + edge.label : "");
      body += text(label, 470, 188 + index * rowHeight, 680, rowFont);
    });
    body += text(`AniDiagram · ${labels.nodes} ${selection.nodes.length}/${data.nodes.length} · ${labels.edges} ${selection.edges.length}/${data.edges.length} · ${data.graph_sha256.slice(0, 12)}`, 48, 596, 1100, 14, 1, "#64748b");
    return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img"><title>${esc(data.title)}</title><metadata>${esc(JSON.stringify(metadata))}</metadata><g font-family="system-ui, sans-serif">${body}</g></svg>`;
  }
  async function saveCard(data, selection, format) {
    await document.fonts.ready;
    const svg = buildCard(data, selection);
    let blob = new Blob([svg], { type: "image/svg+xml" });
    if (format === "png") {
      const svgURL = URL.createObjectURL(blob);
      try {
        const image = new Image(); image.src = svgURL; await image.decode();
        const canvas = document.createElement("canvas"); canvas.width = 1200; canvas.height = 630;
        canvas.getContext("2d").drawImage(image, 0, 0);
        blob = await new Promise(resolve => canvas.toBlob(resolve, "image/png"));
        if (!blob) throw new Error("PNG export failed");
      } finally { URL.revokeObjectURL(svgURL); }
    }
    const url = URL.createObjectURL(blob), link = document.createElement("a");
    link.href = url; link.download = "anidiagram-selection." + format;
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  window.AniDiagramShareCard = { buildCard, saveCard };
})();

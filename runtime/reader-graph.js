/* Pure queries over authored topology. No renderer state or inferred edges. */
(function (root) {
  "use strict";
  function createGraph(data) {
    const nodes = new Map(data.nodes.map(node => [node.id, node]));
    const edges = new Map(data.edges.map(edge => [edge.id, edge]));
    if (nodes.size !== data.nodes.length || edges.size !== data.edges.length) throw new Error("Duplicate graph IDs");
    for (const edge of edges.values()) {
      if (!nodes.has(edge.from) || !nodes.has(edge.to)) throw new Error("Missing graph endpoint");
    }
    function arcs(id, mode) {
      const found = [];
      for (const edge of edges.values()) {
        const both = edge.direction === "bidirectional" || mode === "neighbors";
        if (edge.direction === "undirected" && mode !== "neighbors") continue;
        if (edge.from === id && (mode !== "upstream" || both)) found.push([edge.to, edge.id]);
        if (edge.to === id && (mode === "upstream" || both)) found.push([edge.from, edge.id]);
      }
      return found.sort((a, b) => a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0);
    }
    function reach(source, mode = "downstream") {
      if (!nodes.has(source) || !["upstream", "downstream", "neighbors"].includes(mode)) return { nodes: [], edges: [] };
      const seen = new Set([source]), traversed = new Set(), queue = [source];
      for (let i = 0; i < queue.length; i += 1) {
        for (const [next, edge] of arcs(queue[i], mode)) {
          traversed.add(edge);
          if (!seen.has(next)) { seen.add(next); if (mode !== "neighbors") queue.push(next); }
        }
      }
      return { nodes: [...seen], edges: [...traversed] };
    }
    function route(source, target) {
      if (!nodes.has(source) || !nodes.has(target)) return { found: false, nodes: [], edges: [] };
      const queue = [source], previous = new Map([[source, null]]);
      for (let i = 0; i < queue.length && !previous.has(target); i += 1) {
        for (const [next, edge] of arcs(queue[i], "downstream")) {
          if (!previous.has(next)) { previous.set(next, [queue[i], edge]); queue.push(next); }
        }
      }
      if (!previous.has(target)) return { found: false, nodes: [], edges: [] };
      const nodeIds = [target], edgeIds = [];
      while (nodeIds[0] !== source) {
        const [prior, edge] = previous.get(nodeIds[0]);
        nodeIds.unshift(prior); edgeIds.unshift(edge);
      }
      return { found: true, nodes: nodeIds, edges: edgeIds };
    }
    return { nodes, edges, reach, route };
  }
  if (typeof module !== "undefined" && module.exports) module.exports = { createGraph };
  else root.AniDiagramGraph = { createGraph };
})(globalThis);

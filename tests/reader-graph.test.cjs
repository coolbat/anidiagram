const { test } = require("node:test");
const assert = require("node:assert/strict");
const { createGraph } = require("../runtime/reader-graph.js");
const nodes = ["a", "b", "c", "d", "isolated"].map(id => ({ id }));
const edges = [
  { id: "a-b", from: "a", to: "b", direction: "forward" },
  { id: "b-c", from: "b", to: "c", direction: "bidirectional" },
  { id: "c-a", from: "c", to: "a", direction: "forward" },
  { id: "b-d", from: "b", to: "d", direction: "undirected" },
];
test("reach terminates on cycles and never follows undirected edges as dependencies", () => {
  const graph = createGraph({ nodes, edges });
  assert.deepEqual(new Set(graph.reach("a").nodes), new Set(["a", "b", "c"]));
  assert.deepEqual(graph.route("a", "d"), { found: false, nodes: [], edges: [] });
  assert.equal(graph.reach("b", "neighbors").nodes.includes("d"), true);
  assert.equal(graph.route("c", "b").edges[0], "b-c");
});
test("shortest directed path is deterministic with parallel edges", () => {
  const graph = createGraph({ nodes, edges: [...edges, { id: "0-a-b", from: "a", to: "b", direction: "forward" }] });
  assert.deepEqual(graph.route("a", "c"), { found: true, nodes: ["a", "b", "c"], edges: ["0-a-b", "b-c"] });
  assert.deepEqual(graph.route("a", "a"), { found: true, nodes: ["a"], edges: [] });
  assert.equal(graph.route("a", "isolated").found, false);
  assert.deepEqual(graph.reach("not-a-node").nodes, []);
});

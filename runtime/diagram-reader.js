/* Optional reader controls; selection styles live outside the canonical SVG. */
(function () {
  "use strict";
  function start() {
    const payload = document.getElementById("anidiagram-reader-data");
    if (!payload) return;
    const data = JSON.parse(payload.textContent), graph = window.AniDiagramGraph.createGraph(data), labels = data.labels;
    const get = id => document.getElementById("reader-" + id);
    const stage = document.getElementById("stage"), svg = stage.querySelector("svg");
    // Fit only the outer reader display; authored coordinates and the existing
    // pan/zoom transform remain owned by the original viewer.
    const fitReader = () => {
      if (window.AniDiagramViewport) return;
      const box = svg.viewBox.baseVal;
      const scale = Math.min(1, (stage.clientWidth - 4) / box.width, (stage.clientHeight - 4) / box.height);
      if (scale > 0) document.getElementById("viewport").style.setProperty("--reader-fit-width", box.width * scale + "px");
    };
    new ResizeObserver(fitReader).observe(stage);
    fitReader();
    const nodeElements = new Map(data.nodes.map(node => [node.id, document.getElementById("node-" + node.id)]));
    const edgeElements = [...svg.querySelectorAll("g.edge")];
    const emptyState = () => ({ mode: "neighbors", source: "", target: "", role: "", query: "", view: "" });
    let state = emptyState();
    let selection = { nodes: [], edges: [] };
    const selector = element => {
      const parts = [];
      while (element && element !== svg) {
        parts.unshift(element.tagName + ":nth-child(" + ([...element.parentElement.children].indexOf(element) + 1) + ")");
        element = element.parentElement;
      }
      return "#viewport svg > " + parts.join(" > ");
    };
    function readingURL() {
      const url = new URL(location.href);
      url.hash = "anidiagram=" + encodeURIComponent(JSON.stringify({ version: 1, ...state }));
      return url.href;
    }
    function render() {
      let active = false;
      const view = data.views.find(item => item.id === state.view);
      if (view) {
        const edgeIds = view.relation_ids || [];
        selection = { nodes: [...new Set([...(view.node_ids || []), ...edgeIds.flatMap(id => {
          const edge = graph.edges.get(id); return [edge.from, edge.to];
        })])], edges: [...edgeIds] };
        active = true;
      } else if (state.source) {
        selection = state.mode === "route" ? graph.route(state.source, state.target) : graph.reach(state.source, state.mode);
        active = true;
      } else selection = { nodes: data.nodes.map(n => n.id), edges: data.edges.map(e => e.id) };
      if (state.query || state.role) {
        selection = { nodes: selection.nodes.filter(id => {
          const node = graph.nodes.get(id);
          return (!state.role || node.role === state.role) && (!state.query || (node.label + " " + node.id).toLowerCase().includes(state.query.toLowerCase()));
        }), edges: selection.edges };
        selection.edges = selection.edges.filter(id => {
          const edge = graph.edges.get(id);
          return selection.nodes.includes(edge.from) && selection.nodes.includes(edge.to);
        });
        active = true;
      }
      const rules = [];
      if (active) {
        for (const [id, element] of nodeElements) if (element) rules.push(selector(element) + (selection.nodes.includes(id) ? "{filter:drop-shadow(0 0 4px #38bdf8)}" : "{opacity:.18!important}"));
        for (const edge of data.edges) if (edgeElements[edge.index]) rules.push(selector(edgeElements[edge.index]) + (selection.edges.includes(edge.id) ? "{filter:drop-shadow(0 0 2px #38bdf8)}" : "{opacity:.12!important}"));
      }
      document.getElementById("reader-selection-style").textContent = "@media screen{" + rules.join("\n") + "}";
      const none = state.mode === "route" && state.source && !graph.route(state.source, state.target).found;
      get("result").textContent = none ? labels.none : active ? selection.nodes.map(id => graph.nodes.get(id).label).join(" · ") +
        (selection.edges.length ? " | " + selection.edges.map(id => graph.edges.get(id).label || id).join(" · ") : "") : "";
      if (view) get("result").textContent = view.label + (view.description ? " · " + view.description : "") + " | " + get("result").textContent;
      get("evidence").replaceChildren();
      for (const source of data.evidence.sources || []) {
        if (!(data.evidence.subjects[state.source] || []).includes(source.id)) continue;
        const item = document.createElement("li"), link = document.createElement("a");
        link.textContent = source.title; link.href = source.href; link.target = "_blank"; link.rel = "noopener noreferrer";
        item.append(link); get("evidence").append(item);
      }
      for (const name of ["source", "target", "role"]) get(name).value = state[name];
      get("search").value = state.query;
      if (get("view")) {
        get("view").value = state.view;
        const index = data.views.findIndex(item => item.id === state.view);
        get("previous").disabled = index <= 0;
        get("next").disabled = index >= data.views.length - 1;
      }
      document.querySelectorAll("[data-reader-mode]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.readerMode === state.mode)));
    }
    for (const name of ["source", "target", "role"]) get(name).addEventListener("change", event => { state[name] = event.target.value; state.view = ""; render(); });
    get("search").addEventListener("input", event => { state.query = event.target.value; state.view = ""; render(); });
    document.querySelectorAll("[data-reader-mode]").forEach(button => button.addEventListener("click", () => { state.mode = button.dataset.readerMode; state.view = ""; render(); }));
    get("clear").addEventListener("click", () => { state = emptyState(); render(); });
    if (get("view")) {
      const selectView = id => { state = { ...emptyState(), view: id }; render(); };
      get("view").addEventListener("change", event => selectView(event.target.value));
      for (const [name, delta] of [["previous", -1], ["next", 1]]) get(name).addEventListener("click", () => {
        const index = data.views.findIndex(item => item.id === state.view);
        selectView(data.views[Math.max(0, Math.min(data.views.length - 1, index + delta))].id);
      });
    }
    for (const format of ["svg", "png"]) get("share-" + format).addEventListener("click", async () => {
      try { await window.AniDiagramShareCard.saveCard(data, selection, format); }
      catch (error) { get("result").textContent = error.message; }
    });
    get("copy").addEventListener("click", async () => {
      const url = readingURL(); get("link").value = url; get("link").hidden = false;
      try { await navigator.clipboard.writeText(url); get("result").textContent = labels.copied; } catch { get("link").focus(); get("link").select(); }
    });
    stage.addEventListener("pointerdown", event => {
      const node = event.target.closest("g.node");
      if (!node) return;
      const id = data.nodes.find(item => nodeElements.get(item.id) === node)?.id;
      if (id) { event.stopPropagation(); state = { ...emptyState(), source: id }; get("controls").open = true; render(); }
    }, true);
    function restore() {
      if (!location.hash.startsWith("#anidiagram=") || location.hash.length > 4096) return;
      try {
        const input = JSON.parse(decodeURIComponent(location.hash.slice(12)));
        if (input.version !== 1 || !["neighbors", "upstream", "downstream", "route"].includes(input.mode)) return;
        state = { mode: input.mode, source: graph.nodes.has(input.source) ? input.source : "",
                  target: graph.nodes.has(input.target) ? input.target : "",
                  role: data.nodes.some(node => node.role === input.role) ? input.role : "",
                  query: typeof input.query === "string" ? input.query.slice(0, 200) : "",
                  view: data.views.some(view => view.id === input.view) ? input.view : "" };
        get("controls").open = true;
        render();
      } catch { /* Malformed links are ignored; no topology is changed. */ }
    }
    window.addEventListener("hashchange", restore);
    window.AniDiagramReader = { graph, readingURL, getSelection: () => JSON.parse(JSON.stringify(selection)),
                               shareCard: () => window.AniDiagramShareCard.buildCard(data, selection) };
    render(); restore();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();

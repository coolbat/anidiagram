"""Opt-in constraints for technical diagram kinds, using existing entity/relation IDs."""

from copy import deepcopy


def _object(value, allowed, required=()):
    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
        raise ValueError("type_details contains missing or unsupported fields")


def _ids(value, known, label, *, nonempty=True):
    if not isinstance(value, list) or (nonempty and not value) or any(not isinstance(item, str) or item not in known for item in value):
        raise ValueError(f"{label} must reference existing IDs")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} must contain unique IDs")
    return value


def _rows(value, label):
    if not isinstance(value, list) or not value or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{label} must be a non-empty array of objects")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")


def validate_type_semantics(kind, details, entities, relations, groups):
    nodes = {node["id"]: node for node in entities}
    edges = {edge["id"]: edge for edge in relations}
    group_map = {group["id"]: group for group in groups}
    if len(edges) != len(relations):
        raise ValueError("typed semantics require unique relation IDs")

    def directed(relation_id):
        if not isinstance(relation_id, str) or relation_id not in edges or edges[relation_id].get("direction", "forward") != "forward":
            raise ValueError("typed directed relationships must reference an authored forward relation")
        return edges[relation_id]

    if kind == "sequence":
        _object(details, {"participants", "messages", "activations"}, {"participants", "messages"})
        participants = _ids(details["participants"], nodes, "participants")
        messages = _rows(details["messages"], "messages")
        seen = {}
        for index, message in enumerate(messages):
            _object(message, {"relation_id", "mode", "reply_to"}, {"relation_id", "mode"})
            edge = directed(message["relation_id"])
            if edge["from"] not in participants or edge["to"] not in participants:
                raise ValueError("message endpoints must be declared participants")
            if not isinstance(message["mode"], str) or message["mode"] not in {"sync", "async", "return"} or message["relation_id"] in seen:
                raise ValueError("messages require a valid mode and unique relation_id")
            if message["mode"] == "return":
                _text(message.get("reply_to"), "reply_to")
                earlier = seen.get(message.get("reply_to"))
                if earlier is None or earlier[1]["mode"] == "return":
                    raise ValueError("a return must reply_to a preceding call")
                call = edges[earlier[1]["relation_id"]]
                if (edge["from"], edge["to"]) != (call["to"], call["from"]):
                    raise ValueError("return endpoints must reverse the referenced call")
            elif "reply_to" in message:
                raise ValueError("reply_to is valid only for return messages")
            seen[message["relation_id"]] = (index, message)
        if "activations" in details:
            for activation in _rows(details["activations"], "activations"):
                _object(activation, {"participant", "start", "end"}, {"participant", "start", "end"})
                for field in ("participant", "start", "end"):
                    _text(activation[field], field)
                if activation["participant"] not in participants or activation["start"] not in seen or activation["end"] not in seen:
                    raise ValueError("activation must reference a participant and existing messages")
                if seen[activation["start"]][0] > seen[activation["end"]][0]:
                    raise ValueError("activation end must not precede its start")
                for boundary in ("start", "end"):
                    edge = edges[activation[boundary]]
                    if activation["participant"] not in {edge["from"], edge["to"]}:
                        raise ValueError("activation boundaries must involve their participant")
    elif kind == "lifecycle":
        _object(details, {"initial", "terminal", "recovery_relations"}, {"initial", "terminal"})
        if not isinstance(details["initial"], str) or details["initial"] not in nodes:
            raise ValueError("initial must reference an existing state entity")
        terminal = _ids(details["terminal"], nodes, "terminal")
        for edge in relations:
            if edge["from"] in terminal or (edge.get("direction") == "bidirectional" and edge["to"] in terminal):
                raise ValueError("terminal states must not have outgoing transitions")
        reachable = {details["initial"]}
        while True:
            expanded = reachable | {edge["to"] for edge in relations if edge["from"] in reachable and edge.get("direction", "forward") != "undirected"}
            expanded |= {edge["from"] for edge in relations if edge["to"] in reachable and edge.get("direction") == "bidirectional"}
            if expanded == reachable:
                break
            reachable = expanded
        if not set(terminal) <= reachable:
            raise ValueError("terminal states must be reachable from the initial state")
        for relation_id in _ids(details.get("recovery_relations", []), edges, "recovery_relations", nonempty=False):
            edge = directed(relation_id)
            failed = nodes[edge["from"]].get("state", {})
            target = nodes[edge["to"]].get("state", {})
            if failed.get("result") != "failure" and failed.get("phase") != "failed":
                raise ValueError("a recovery must leave an explicitly failed state")
            if edge["to"] in terminal or target.get("result") == "failure" or target.get("phase") == "failed":
                raise ValueError("a recovery must return to a non-terminal, non-failed state")
    elif kind == "dataflow":
        _object(details, {"datasets", "transformations"}, {"datasets", "transformations"})
        datasets = _ids(details["datasets"], nodes, "datasets")
        transformations = _rows(details["transformations"], "transformations")
        _ids([row.get("entity_id") for row in transformations], nodes, "transformations")
        for transform in transformations:
            _object(transform, {"entity_id", "inputs", "outputs"}, {"entity_id", "inputs", "outputs"})
            if transform["entity_id"] in datasets:
                raise ValueError("a transformation entity cannot also be a dataset")
            for field in ("inputs", "outputs"):
                for relation_id in _ids(transform[field], edges, field):
                    edge = directed(relation_id)
                    transform_side, data_side = ("to", "from") if field == "inputs" else ("from", "to")
                    if edge[transform_side] != transform["entity_id"] or edge[data_side] not in datasets:
                        raise ValueError("transformation inputs/outputs must use the authored dataset directions")
    elif kind == "workflow":
        _object(details, {"approvals"}, {"approvals"})
        approvals = _rows(details["approvals"], "approvals")
        _ids([row.get("entity_id") for row in approvals], nodes, "approvals")
        for approval in approvals:
            _object(approval, {"entity_id", "approved", "rejected"}, {"entity_id", "approved", "rejected"})
            paths = [directed(approval[field]) for field in ("approved", "rejected")]
            if approval["approved"] == approval["rejected"] or any(edge["from"] != approval["entity_id"] for edge in paths):
                raise ValueError("approval outcomes must be distinct outgoing relations")
            for edge in paths:
                _text(edge.get("condition"), "approval condition")
            if paths[0]["condition"] == paths[1]["condition"]:
                raise ValueError("approval conditions must distinguish the outcomes")
    elif kind == "architecture":
        _object(details, {"ownership", "trust_boundaries", "crossings"})
        if not details:
            raise ValueError("architecture type_details requires ownership or trust boundaries")
        if "ownership" in details:
            ownership = _rows(details["ownership"], "ownership")
            _ids([row.get("group_id") for row in ownership], group_map, "ownership")
            for owner in ownership:
                _object(owner, {"group_id", "owner"}, {"group_id", "owner"})
                _text(owner["owner"], "owner")
        boundaries = _ids(details.get("trust_boundaries", []), group_map, "trust_boundaries", nonempty=False)
        crossing_ids = set()
        for edge in relations:
            if any((edge["from"] in group_map[group]["members"]) != (edge["to"] in group_map[group]["members"]) for group in boundaries):
                crossing_ids.add(edge["id"])
        crossings = details.get("crossings", [])
        if not isinstance(crossings, list) or any(not isinstance(row, dict) for row in crossings):
            raise ValueError("crossings must be an array of objects")
        declared = _ids([row.get("relation_id") for row in crossings], edges, "crossings", nonempty=False)
        if set(declared) != crossing_ids:
            raise ValueError("crossings must describe exactly the authored relationships crossing declared boundaries")
        for row in crossings:
            _object(row, {"relation_id", "mechanism"}, {"relation_id", "mechanism"})
            _text(row["mechanism"], "boundary crossing mechanism")
    else:
        raise ValueError("type_details supports architecture, workflow, sequence, dataflow, or lifecycle")


def compile_type_semantics(semantic):
    if "type_details" not in semantic:
        return None
    kind, details = semantic["intent"]["diagram_kind"], semantic["type_details"]
    validate_type_semantics(kind, details, semantic["entities"], semantic.get("relations", []), semantic.get("groups", []))
    return {"kind": kind, "details": deepcopy(details),
            "groups": [{"id": group["id"], "members": list(group["members"])} for group in semantic.get("groups", [])]}


def validate_compiled_type(value, nodes, edges, groups):
    _object(value, {"kind", "details", "groups"}, {"kind", "details", "groups"})
    if not isinstance(value["groups"], list):
        raise ValueError("typed group membership must be an array")
    node_ids = {node.node_id for node in nodes}
    group_ids = {group.group_id for group in groups}
    _ids([group.get("id") for group in value["groups"] if isinstance(group, dict)], group_ids, "typed groups", nonempty=False)
    for group in value["groups"]:
        _object(group, {"id", "members"}, {"id", "members"})
        _ids(group["members"], node_ids, "typed group members")
    if any(not edge.semantic_relation_id for edge in edges):
        raise ValueError("typed semantics require a stable ID for every relation")
    validate_type_semantics(value["kind"], value["details"],
                            [{"id": node.node_id, "state": node.state} for node in nodes],
                            [{"id": edge.semantic_relation_id, "from": edge.source, "to": edge.target, "direction": edge.direction,
                              "condition": edge.condition} for edge in edges], value["groups"])


def semantic_facts(scene, locale):
    """Render verified structural details as a compact, readable companion."""
    kind, details = scene.type_semantics["kind"], scene.type_semantics["details"]
    nodes = {node.node_id: node.label for node in scene.nodes}
    groups = {group.group_id: group.label for group in scene.groups}
    edges = {edge.semantic_relation_id: edge for edge in scene.edges}
    def relation(relation_id):
        edge = edges[relation_id]
        return f'{nodes[edge.source]} → {nodes[edge.target]}' + (f' · {edge.label}' if edge.label else '')
    zh = locale == "zh-CN"
    if kind == "sequence":
        modes = {"sync": "同步调用", "async": "异步消息", "return": "返回"} if zh else {"sync": "Synchronous call", "async": "Asynchronous message", "return": "Return"}
        result = [f'{index + 1}. {modes[item["mode"]]}: {relation(item["relation_id"])}' for index, item in enumerate(details["messages"])]
        for activation in details.get("activations", []):
            result.append(f'{nodes[activation["participant"]]} · {activation["start"]} — {activation["end"]}')
        return result
    if kind == "lifecycle":
        return [("初始状态: " if zh else "Initial: ") + nodes[details["initial"]],
                ("终止状态: " if zh else "Terminal: ") + ', '.join(nodes[item] for item in details["terminal"])] + [
                    ("恢复: " if zh else "Recovery: ") + relation(item) for item in details.get("recovery_relations", [])]
    if kind == "workflow":
        return [nodes[item["entity_id"]] + ': ' + ' / '.join(relation(item[field]) + ' (' + edges[item[field]].condition + ')' for field in ("approved", "rejected")) for item in details["approvals"]]
    if kind == "dataflow":
        return [nodes[item["entity_id"]] + ': ' + ' / '.join(relation(rel) for rel in item["inputs"] + item["outputs"]) for item in details["transformations"]]
    return [groups[item["group_id"]] + ': ' + item["owner"] for item in details.get("ownership", [])] + [
        relation(item["relation_id"]) + ' · ' + item["mechanism"] for item in details.get("crossings", [])]

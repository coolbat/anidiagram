"""Optional source-fact preflight; reference and presentation checks are not semantic proof."""

import ast
import re
from pathlib import Path

from .artifact_bundle import commit_bundle
from .delivery import canonical_json_bytes, digest_bytes
from .repository_evidence import _git
from .schema import compile_scene


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _definitions(tree, prefix=""):
    for child in ast.iter_child_nodes(tree):
        name = prefix
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = prefix + child.name
            yield name, child.lineno, child.end_lineno
            name += "."
        yield from _definitions(child, name)


def _definition(claim, node, sources, root):
    target = claim['object']
    _require(isinstance(target, dict) and set(target) == {'path', 'symbol'} and
             all(_text(v) for v in target.values()), 'python-definition object requires path and symbol')
    matches = [s for s in sources if s['repository']['path'] == target['path']]
    if not matches:
        return 'contradicted', 'Requested definition file differs from its pinned evidence.'
    # Only an explicit filename label asserts a mechanical module owner. General
    # prose/aggregated captions remain outside this narrow ownership rule.
    label = node.label.strip()
    if re.fullmatch(r'[\w./-]+\.py', label) and label != Path(target['path']).name and label != target['path']:
        return 'contradicted', 'Displayed module filename differs from the definition owner.'
    for source in matches:
        try:
            definitions = list(_definitions(ast.parse(_git(root, 'cat-file', 'blob', source['blob']))))
        except (SyntaxError, UnicodeError, RecursionError, ValueError):
            return 'unknown', 'Pinned source could not be parsed as Python; no code was executed.'
        found = [item for item in definitions if item[0] == target['symbol']]
        if len(found) > 1:
            return 'unknown', 'Multiple lexical definitions; active runtime binding is unresolved.'
        ref = source['repository']
        if found and ('line' not in ref or ref['line'] <= found[0][1] <= ref.get('end_line', ref['line'])):
            return 'supported', 'Definition found in pinned blob at lines %s–%s.' % found[0][1:]
    return 'contradicted', 'Qualified definition is absent from the cited source span.'


def _decisions(review, identities, claims):
    if review is None:
        return {}
    _require(isinstance(review, dict) and set(review) == {
        'version', 'reviewer', 'specification_sha256', 'facts_sha256', 'decisions'}, 'invalid review record')
    _require(review['version'] == '0.1' and _text(review['reviewer']), 'review needs version and reviewer')
    for key, value in identities.items():
        _require(review.get(key) == value, 'review hash does not match current ' + key)
    rows = review['decisions']
    _require(isinstance(rows, list) and 0 < len(rows) <= len(claims), 'invalid review decisions')
    result = {}
    by_id = {c['id']: c for c in claims}
    for row in rows:
        _require(isinstance(row, dict) and set(row) == {'claim_id', 'verdict', 'rationale', 'source_refs'},
                 'invalid review decision fields')
        claim_id = row['claim_id']
        _require(isinstance(claim_id, str) and claim_id in by_id and claim_id not in result,
                 'review claim IDs must be existing and unique')
        _require(row['verdict'] in ('supported', 'contradicted', 'unknown') and _text(row['rationale']),
                 'review needs verdict and rationale')
        refs = row['source_refs']
        _require(isinstance(refs, list) and bool(refs) and all(isinstance(r, str) for r in refs) and
                 len(refs) == len(set(refs)) and set(refs) <= set(by_id[claim_id].get('source_refs', [])),
                 'review evidence must be unique claim source references')
        result[claim_id] = row
    return result


def check_accuracy(specification, facts, *, repo_root=None, review=None):
    """Check narrow immutable facts and record separately authored semantic review.

    `ok` means no known contradiction; `ready` additionally requires support for
    every required claim. Neither means arbitrary architecture is proven correct.
    """
    _require(isinstance(facts, dict) and set(facts) == {'version', 'claims'} and
             facts.get('version') == '0.1', 'facts require version 0.1 and claims')
    claims = facts['claims']
    _require(isinstance(claims, list) and 0 < len(claims) <= 200, 'facts need 1–200 claims')
    scene = compile_scene(specification, repo_root=repo_root)
    nodes = {n.node_id: n for n in scene.nodes}
    edges = {e.semantic_relation_id: e for e in scene.edges if e.semantic_relation_id}
    _require(len(nodes) == len(scene.nodes) and
             len(edges) == sum(bool(e.semantic_relation_id) for e in scene.edges) and
             not (set(nodes) & set(edges)), 'accuracy subjects must have unambiguous IDs')
    sources = {s['id']: s for s in scene.source_evidence.get('sources', [])}
    bindings = scene.source_evidence.get('subjects', {})
    identities = {'specification_sha256': digest_bytes(canonical_json_bytes(specification))['sha256'],
                  'facts_sha256': digest_bytes(canonical_json_bytes(facts))['sha256']}
    seen = set()
    for claim in claims:
        _require(isinstance(claim, dict) and set(claim) <= {
            'id', 'subject', 'predicate', 'object', 'condition', 'source_refs', 'confidence', 'required'} and
            {'id', 'subject', 'predicate', 'object', 'condition', 'source_refs'} <= set(claim), 'invalid claim fields')
        _require(_text(claim['id']) and claim['id'] not in seen, 'claim IDs must be nonempty and unique')
        seen.add(claim['id'])
        _require(_text(claim['subject']) and claim['subject'] in set(nodes) | set(edges), 'claim subject is absent')
        _require(claim['predicate'] in ('python-definition', 'relation', 'behavior'), 'unknown claim predicate')
        _require(claim.get('confidence', 'asserted') in ('asserted', 'unknown'), 'confidence must be asserted or unknown')
        _require(type(claim.get('required', True)) is bool, 'required must be boolean')
        _require(isinstance(claim['condition'], str), 'condition must be text')
        refs = claim['source_refs']
        _require(isinstance(refs, list) and all(isinstance(r, str) for r in refs) and len(set(refs)) == len(refs),
                 'source_refs must be unique strings')
        _require(set(refs) <= set(sources) and set(refs) <= set(bindings.get(claim['subject'], [])),
                 'claim evidence is missing or unbound to the subject')
        _require(bool(refs) or claim.get('confidence') == 'unknown', 'asserted claims require pinned evidence')
        if claim['predicate'] == 'python-definition':
            _require(claim['subject'] in nodes, 'definition subject must be a node')
            obj = claim['object']
            _require(isinstance(obj, dict) and set(obj) == {'path', 'symbol'} and
                     all(_text(v) for v in obj.values()), 'python-definition object requires path and symbol')
            _require(not claim['condition'], 'definition condition must be empty; use behavior for conditional claims')
        elif claim['predicate'] == 'relation':
            obj = claim['object']
            _require(claim['subject'] in edges and isinstance(obj, dict) and set(obj) == {'from', 'to', 'direction', 'kind'}
                     and all(_text(v) for v in obj.values()), 'relation requires from/to/direction/kind')
        else:
            _require(_text(claim['object']), 'behavior object must be nonempty text')
    decisions = _decisions(review, identities, claims)
    results = []
    for claim in claims:
        basis, status, reason = 'source-review-required', 'pending', 'References do not establish behavioral meaning.'
        if claim['predicate'] == 'python-definition' and claim['source_refs']:
            status, reason = _definition(claim, nodes[claim['subject']], [sources[r] for r in claim['source_refs']], repo_root)
            basis = 'python-ast'
        elif claim['predicate'] == 'relation':
            edge = edges[claim['subject']]
            actual = {'from': edge.source, 'to': edge.target, 'direction': edge.direction, 'kind': edge.semantic_kind}
            basis = 'diagram-fields-only'
            if actual != claim['object'] or (edge.condition or '') != claim['condition']:
                status, reason = 'contradicted', 'Claim direction/type/condition differs from the diagram.'
            else:
                reason = 'Authored fields match; source causality still requires independent review.'
        if claim.get('confidence') == 'unknown' and status != 'contradicted':
            status, reason = 'unknown', 'Author explicitly left this claim unresolved.'
        elif status != 'contradicted' and claim['id'] in decisions:
            decision = decisions[claim['id']]
            status, reason, basis = decision['verdict'], decision['rationale'], 'review-record'
        results.append({**claim, 'required': claim.get('required', True), 'status': status, 'basis': basis, 'reason': reason})
    ok = not any(c['status'] == 'contradicted' for c in results)
    ready = ok and all(c['status'] == 'supported' for c in results if c['required'])
    return {'schema': {'name': 'AniDiagramAccuracyCheck', 'version': '0.1'}, 'ok': ok, 'ready': ready,
            'status': 'ready' if ready else 'needs-review' if ok else 'failed', **identities,
            'gates': {'source_references': 'verified' if sources else 'not-requested',
                      'semantic_review': 'recorded-not-proof' if review else 'pending',
                      'rendered_readability': 'not-checked'},
            'coverage': {'provided_claims': len(claims), 'required_claims': sum(c['required'] for c in results),
                         'completeness': 'not-assessed'},
            'reviewer': review['reviewer'] if review else None, 'claims': results,
            'limits': 'AST proves lexical definitions only; matching diagram fields is not source causality. Review records are assertions, not authenticated independent proof. No target code is executed.'}


def accuracy_command(input_path, facts_path, *, repo_root=None, review_path=None, output=None, strict=False):
    import json
    from .planner import compile_plan
    inputs = [Path(input_path), Path(facts_path)]
    raw = [path.read_bytes() for path in inputs]
    diagram, facts = [json.loads(data) for data in raw]
    _require(isinstance(diagram, dict), 'accuracy input must be a Plan or DiagramScript object')
    if 'semantic' in diagram:
        diagram = compile_plan(diagram)
    review = None
    if review_path:
        inputs.append(Path(review_path))
        raw.append(inputs[-1].read_bytes())
        review = json.loads(raw[-1])
    result = check_accuracy(diagram, facts, repo_root=repo_root, review=review)
    if strict:
        result['ok'] = result['ready']
    result['strict'] = strict
    _require(all(path.read_bytes() == data for path, data in zip(inputs, raw)), 'accuracy input changed during check')
    if output:
        commit_bundle({Path(output): canonical_json_bytes(result)}, inputs=inputs)
    return result

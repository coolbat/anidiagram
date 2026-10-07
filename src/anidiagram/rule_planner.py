"""Conservative EN/ZH relation grammar with exact source-span provenance.

This is deliberately a small grammar, not an NLP model. Unhandled clauses remain
visible; referents are resolved only for a local, singular ``which`` antecedent.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .localization import resolve_locale
from .planning import rule_diagnostics


_PAYLOAD = r'(?:[\w-]+\s+){1,2}?'
_EN_VERBS = (
    r'calls?', r'invokes?', r'writes?\s+to', r'notifies', r'notify', r'collects?', r'enters?',
    r'forwards?\s+(?:' + _PAYLOAD + r')?to', r'sends?\s+(?:' + _PAYLOAD + r')?to', r'routes?\s+(?:' + _PAYLOAD + r')?to',
    r'talks?\s+to', r'connects?\s+to', r'queries', r'reads?\s+from', r'reads', r'fetches\s+from', r'loads?\s+from',
    r'stores?\s+(?:' + _PAYLOAD + r')?(?:in|into)', r'persists?\s+to', r'saves?\s+(?:' + _PAYLOAD + r')?to',
    r'publishes\s+to', r'publishes', r'emits?\s+(?:' + _PAYLOAD + r')?to', r'pushes\s+(?:' + _PAYLOAD + r')?to',
)
_ZH_VERBS = ('调用', '写入', '通知', '采集', '进入', '访问', '转发给', '转发到', '发送给', '发送到', '发给', '路由到',
             '查询', '读取', '存入', '存储到', '保存到', '写到', '发布到', '推送给', '推送到')
_VERB = r'\b(?:' + '|'.join(_EN_VERBS) + r')\b|' + '|'.join(_ZH_VERBS)
_VERB_KIND = (
    (re.compile(r'^(?:writ|stor|persist|sav)|写入|存入|存储到|保存到|写到', re.I), 'data-write'),
    (re.compile(r'^(?:notif|publish|emit|push)|通知|发布到|推送', re.I), 'async-message'),
    (re.compile(r'^(?:collect|read|fetch|load|quer)|采集|读取|查询', re.I), 'data-read'),
)
# Unparsed follow-up predicates split a clause so they are reported, not
# absorbed into a target name ("collects metrics and raises alerts").
_TRAILING_PREDICATE = r'raises|triggers|sends|emits|generates|alerts'
_NEGATION = re.compile(r"\b(?:not|never|no|without|neither|nor|cannot|[a-z]+n['’]t)\b|不|未|没有|禁止|无需", re.I)
_AMBIGUOUS = re.compile(r'^(?:it|they|them|this|that|these|those|which|someone|something|其|它|他们|它们|该服务)$', re.I)
_ADVERB_EN = r'(?:\s+(?:directly|also|then|only|first|still|usually|always|later|now|again|asynchronously|synchronously))+$'
_ADVERB_ZH = r'(?:直接|也|还|再|会|将|则|先|才|就|只|仅|同时|随后|然后|再次)+$'
_ALL_SERVICES = {'all services', 'each service', 'every service', '所有服务', '各服务', '每个服务'}
_OWN_DATABASE = re.compile(r'^(?:(?:its|their)\s+own\s+databases?|各自(?:的)?数据库)$', re.I)


def _name(value: str) -> str:
    value = value.strip().strip('`"“”')
    value = re.sub(r'^(?:(?:the|an?|then|and|also)\s+)+', '', value, flags=re.I)
    value = re.sub(r'\s+services$', ' service', value, flags=re.I)
    value = re.sub(_ADVERB_EN, '', value, flags=re.I)
    value = re.sub(_ADVERB_ZH, '', value)
    return value.strip()


def _alias_key(label: str) -> str:
    return re.sub(r'(?:\s+service|服务)$', '', label.casefold()) or label.casefold()


def _names(value: str) -> List[str]:
    values = [_name(item) for item in re.split(r'\s+and\s+|\s*&\s*|和|与|、|及', value, flags=re.I)]
    # English right-node raising: "inventory and payment services".
    if len(values) > 1 and re.search(r'\s+services\s*$', value, re.I):
        values = [item if re.search(r'\s+service$', item, re.I) else item + ' service' for item in values]
    return values


def _valid_name(value: str) -> bool:
    return bool(value and len(value) <= 64 and len(value.split()) <= 7
                and not _AMBIGUOUS.fullmatch(value)
                and not re.search(r'\b(?:or|but|if|unless|because|not|never|does|do|can|may|might|must|should|could|would|will|shall|via|through|to|from|calls?|writes?|deletes?|fails?|succeeds?|returns?|after|before|when|once|until|then|each|every|its|their|own|' + _TRAILING_PREDICATE + r'|forwards|talks|reads|fetches|publishes|pushes|stores|saves|persists|routes|loads|queries|invokes|connects)\b|调用|写入|通过|经过|进入|通知|采集|访问|发给|发送|转发|推送|成功|失败|并|不|各自|把', value, re.I))


def _kind(label: str) -> tuple:
    lowered = label.lower()
    if re.search(r'\bdatabase[s]?\b|数据库', lowered):
        return 'database', 'memory'
    if re.search(r'\bqueue\b|队列', lowered):
        return 'queue', 'tool'
    if re.search(r'\bgateway\b|网关', lowered):
        return 'api', 'process'
    if re.search(r'\b(?:user|users|client|requests?)\b|用户|请求', lowered):
        return 'user', 'source'
    if re.search(r'\bmonitoring\b|监控', lowered):
        return 'monitor', 'process'
    return 'service', 'process'


def _clauses(brief: str) -> List[Dict[str, Any]]:
    result = []
    for match in re.finditer(r'[^,，。.;；!?！？\n]+', brief):
        raw = match.group()
        text = raw.strip()
        if not text:
            continue
        start = match.start() + len(raw) - len(raw.lstrip())
        result.append({'text': text, 'start': start, 'end': start + len(text)})
    return result


def extract_rule_plan(brief: str, title: str = '', style: Optional[str] = None,
                      language: str = 'auto') -> Optional[Dict[str, Any]]:
    locale = resolve_locale(language, (title, brief))
    zh = locale == 'zh-CN'
    entities: List[Dict[str, Any]] = []
    relations: List[Dict[str, Any]] = []
    provenance: List[Dict[str, Any]] = []
    sources = [{'id': 'input-brief', 'type': 'brief', 'title': '输入需求' if zh else 'Input brief', 'note': brief}]
    by_name: Dict[str, str] = {}
    last_targets: List[str] = []
    pending_condition = ''
    pending_condition_ref = ''
    inferred_title = ''
    saw_relation_grammar = False

    def entity(label: str, ref: str) -> str:
        label = _name(label)
        key = _alias_key(label)
        if key not in by_name:
            item_id = 'entity-' + str(len(entities) + 1)
            kind, role = _kind(label)
            entities.append({'id': item_id, 'label': label, 'kind': kind, 'role': role,
                             'importance': 'primary', 'source_refs': [ref]})
            by_name[key] = item_id
        else:
            item_id = by_name[key]
            item = next(item for item in entities if item['id'] == item_id)
            # "Billing" and "billing service" are one entity; keep the explicit service name.
            if len(label) > len(item['label']):
                item['label'] = label
            if ref not in item['source_refs']:
                item['source_refs'].append(ref)
        return item_id

    def connect(left: str, right: str, kind: str, label: str, ref: str, condition: str = '') -> None:
        relation = {'id': 'relation-' + str(len(relations) + 1), 'from': entity(left, ref), 'to': entity(right, ref),
                    'kind': kind, 'label': label, 'direction': 'forward', 'importance': 'primary', 'source_refs': [ref]}
        if condition:
            relation['condition'] = condition
            if pending_condition_ref:
                relation['source_refs'].append(pending_condition_ref)
        relations.append(relation)

    for index, clause in enumerate(_clauses(brief)):
        ref = 'brief-clause-' + str(index + 1)
        source_text = clause['text']
        text = source_text
        partial_reasons = []
        inline_condition = ''
        record = {**clause, 'source_ref': ref, 'status': 'unsupported', 'reason': 'Unsupported sentence grammar; no relation inferred.'}
        sources.append({'id': ref, 'type': 'brief', 'title': '简报片段 ' + str(index + 1) if zh else 'Brief clause ' + str(index + 1), 'note': source_text})
        provenance.append(record)
        # Only a title prefix is removed, with the complete original source kept.
        if ':' in text or '：' in text:
            prefix, text = re.split(r'[:：]', text, maxsplit=1)
            if re.match(r'^(?:if|when|after|before|on|upon)\b|^(?:如果|若|当)', prefix, re.I):
                inline_condition = prefix.strip()
            else:
                inferred_title = re.sub(r'^(?:构建|设计|绘制|创建|build\s+(?:an?\s+)?|draw\s+(?:an?\s+)?)', '', prefix, flags=re.I).strip()
                if not re.match(r'^(?:构建|设计|绘制|创建|build\b|draw\b)', prefix, re.I) or re.search(_VERB, prefix, re.I):
                    partial_reasons.append('Unrecognized prefix retained; only the relation body was parsed.')
            text = text.strip()
        condition = inline_condition or pending_condition
        pending_condition = ''
        if (re.match(r'^(?:if|when|after|before)\b|^(?:on|upon)\s+\S+(?:\s+\S+)?\s+(?:success|failure|completion|error)$', text, re.I)
                or re.fullmatch(r'(?:如果|若|当).+|.+(?:成功|失败)(?:后|时)', text)):
            pending_condition, pending_condition_ref = text, ref
            record.update(status='context', reason='Condition applies only to the immediately following supported clause.')
            last_targets = []
            continue
        condition_match = re.match(r'^(.+?(?:成功|失败)(?:后|时))(.+)$', text)
        if condition_match:
            condition, text = condition_match.groups()
        negative = bool(_NEGATION.search(source_text))
        parse_text = _NEGATION.sub('', text)
        if negative:
            parse_text = re.sub(r'\b(?:does|do|must|should|can)\s+', '', parse_text, flags=re.I).strip()
            record.update(status='negated', reason='Negated clause retained without positive relations.')
        # A relative clause is resolved only against exactly one prior object.
        if re.match(r'^which\s+', parse_text, re.I):
            separator = brief[provenance[-2]['end']:clause['start']] if index else ''
            if len(last_targets) != 1 or not re.fullmatch(r'[,，]\s*', separator):
                record.update(reason='Ambiguous relative pronoun; antecedent is not singular.')
                saw_relation_grammar = saw_relation_grammar or bool(re.search(_VERB, parse_text, re.I))
                last_targets = []
                continue
            parse_text = re.sub(r'^which\s+', last_targets[0] + ' ', parse_text, flags=re.I)
        local_subjects: List[str] = []
        targets_in_clause: List[str] = []
        # After 'collects metrics', 'and alerts' is an ambiguous predicate, not
        # a proven second collected object. Retain it for review like 并告警.
        pieces = re.split(r'\s+and\s+(?=(?:' + _VERB + r'|\b(?:' + _TRAILING_PREDICATE + r'))\b)|并(?=' + '|'.join(_ZH_VERBS) + r'|告警)',
                          parse_text, flags=re.I)
        consumed = 0
        for piece in pieces:
            # 前端把请求发给后端 -> 前端发给后端; the moved object is payload, not an entity.
            piece = re.sub(r'把[^把]*?(?=' + '|'.join(_ZH_VERBS) + r')', '', piece.strip())
            edges = []
            subjects: List[str] = []
            targets: List[str] = []
            # "requests pass through a gateway to the order service" / 用户下单经过网关进入订单服务.
            route = re.fullmatch(r'(.+?)\s+(?:pass(?:es)?|flows?|go(?:es)?|travels?|(?:places?|submits?|sends?)\s+(?:an?\s+)?\w+)\s+'
                                 r'(?:through|via)\s+(.+?)\s+(?:to|into)\s+(.+)', piece, re.I)
            if route is None:
                route = re.fullmatch(r'(.+?)(?:经过|通过)(.+?)(?:进入|到达|访问)(.+)', piece)
            # "Orders go from the gateway to the order service": the subject is the payload label.
            hop = re.fullmatch(r'(.+?)\s+(?:go(?:es)?|flows?|moves?|travels?)\s+from\s+(.+?)\s+(?:to|into)\s+(.+)', piece, re.I)
            via = re.fullmatch(r'(.*?)\s*(?:through\s+|via\s+|通过)(.+?)(?:\s+(?:notifies|notify)\s+|通知)(.+)', piece, re.I)
            if hop and route is None:
                saw_relation_grammar = True
                payload, source, target = hop.groups()
                subjects, targets = _names(source), _names(target)
                edges = [(a, b, 'request', _name(payload)) for a in subjects for b in targets]
            elif route:
                saw_relation_grammar = True
                actor, middle, target = route.groups()
                actor = re.sub(r'下单$', '', actor)
                subjects, middles, targets = _names(actor), _names(middle), _names(target)
                edges = [(a, b, 'request', '请求' if zh else 'request') for a in subjects for b in middles]
                edges += [(a, b, 'request', '路由' if zh else 'route') for a in middles for b in targets]
            elif via:
                saw_relation_grammar = True
                actor, middle, target = via.groups()
                subjects, middles, targets = _names(actor) if actor.strip() else [], _names(middle), _names(target)
                edges = [(a, b, 'async-message', '发布' if zh else 'publish') for a in subjects for b in middles]
                edges += [(a, b, 'async-message', '通知' if zh else 'notify') for a in middles for b in targets]
                if not subjects:
                    partial_reasons.append('Notification recipients extracted; sending actor was not specified.')
            else:
                # A verb can also occur inside a name (查询服务调用账本); use the
                # first occurrence whose actor and target are both valid names.
                for match in re.finditer(_VERB, piece, re.I):
                    actor, verb, target = piece[:match.start()].strip(), match.group(), piece[match.end():].strip()
                    if not target:
                        continue
                    saw_relation_grammar = True
                    subjects = _names(actor) if actor else local_subjects
                    targets = _names(target)
                    if _name(actor).casefold() in _ALL_SERVICES:
                        subjects = [item['label'] for item in entities if re.search(r'\bservice$|服务$', item['label'], re.I)]
                        if target.casefold() == 'databases':
                            partial_reasons.append('Unspecified database ownership: aggregate target only, per-service mapping needs review.')
                    kind = next((value for pattern, value in _VERB_KIND if pattern.search(verb)), 'request')
                    if _OWN_DATABASE.match(_name(target)) and subjects:
                        targets = [name + ('数据库' if zh else ' database') for name in subjects]
                        edges = [(a, b, kind, verb) for a, b in zip(subjects, targets)]
                    else:
                        edges = [(a, b, kind, verb) for a in subjects for b in targets]
                    if edges and all(_valid_name(name) for edge in edges for name in edge[:2]):
                        break
                    edges = []
            endpoints = {name for edge in edges for name in edge[:2]}
            if not edges or not all(_valid_name(name) for name in endpoints):
                continue
            for left, right, kind, label in edges:
                if negative:
                    entity(left, ref)
                    entity(right, ref)
                else:
                    connect(left, right, kind, label, ref, condition)
            consumed += 1
            local_subjects = subjects
            targets_in_clause = targets
        if not negative and consumed:
            if consumed == len(pieces) and not partial_reasons:
                record.update(status='extracted', reason='Matched explicit relation grammar; semantics require review.')
            else:
                record.update(status='partial', reason=' '.join(partial_reasons) if partial_reasons else 'Only supported predicates extracted; remainder retained.')
        if not negative and targets_in_clause and record['status'] == 'extracted':
            last_targets = targets_in_clause
        else:
            last_targets = []
        pending_condition_ref = ''
    # An unmatched condition is not considered extracted coverage.
    for item in provenance:
        if item['status'] == 'context':
            used = any(item['source_ref'] in relation['source_refs'] for relation in relations)
            item.update(status='extracted' if used else 'unsupported', reason='Condition attached to next relation.' if used else 'Condition has no supported following relation.')
    if not entities:
        if saw_relation_grammar or _NEGATION.search(brief):
            raise ValueError('Explicit relation could not be resolved; provide an authored --plan. No positive template was generated.')
        return None
    planning = rule_diagnostics(provenance)
    title = title or inferred_title or ('简报关系图' if zh else 'Brief relationship map')
    return {
        'version': '0.2', 'planning': planning,
        'semantic': {'language': locale, 'title': title,
                     'subtitle': '按显式句式提取；未支持片段请核验。' if zh else 'Explicit sentence rules; review unsupported clauses.',
                     'summary': brief,
                     'intent': {'diagram_kind': 'architecture', 'primary_question': brief or title,
                                'audience': ['技术团队'] if zh else ['technical'],
                                'scope': 'Only matched explicit relations are drawn; grammatical order is not a verified execution sequence.',
                                'exclusions': ['No semantic certification, arbitrary coreference, or implied architecture.']},
                     'entities': entities, 'relations': relations, 'flows': [], 'sources': sources},
        'presentation': {'icon_system': 'auto', 'style': style or 'auto', 'layout': 'auto', 'motion': 'showcase-v1'},
    }

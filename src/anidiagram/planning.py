"""Bounded diagnostics for the model-free agent template, not semantic analysis."""

from __future__ import annotations

from copy import deepcopy
import math
import re
from typing import Any, Dict, Iterable, Mapping


# This finite vocabulary is deliberately inspectable. Unknown concepts are not
# counted as covered, and a match says nothing about the correctness of a flow.
_CONCEPTS = {
    "request": ("request", "requests", "brief", "用户请求", "输入需求", "请求"),
    "agent": ("agent", "agents", "智能体"),
    "memory": ("memory", "context", "notes", "knowledge", "记忆", "上下文", "笔记", "知识库"),
    "tool": ("tool", "tools", "search", "browser", "工具", "搜索", "浏览器"),
    "guardrail": ("guardrail", "guardrails", "validation", "policy", "safety", "安全", "护栏", "校验", "策略"),
    "feedback": ("loop", "loops", "retry", "retries", "feedback", "循环", "重试", "反馈"),
    "output": ("output", "outputs", "result", "results", "输出", "结果"),
    "gateway": ("gateway", "gateways", "网关"),
    "order": ("ecommerce", "e-commerce", "order", "orders", "电商", "订单"),
    "inventory": ("inventory", "stock", "库存"),
    "payment": ("payment", "payments", "支付"),
    "message-queue": ("message queue", "message queues", "queue", "queues", "mq", "消息队列"),
    "logistics": ("logistics", "shipping", "物流"),
    "loyalty": ("loyalty", "reward points", "积分"),
    "database": ("database", "databases", "数据库"),
    "monitoring": ("monitoring", "metrics", "监控", "指标"),
    "alert": ("alert", "alerts", "告警"),
}

# Words used to describe the template, not an open-ended business vocabulary.
# Any residual fragment keeps assessment conservative, including custom names.
_EN_SCAFFOLD = set("""
a an the and or but if then else when whether after before through into from to
of for by with without in on at as is are was be been being it its this that
these those their all each any no not do does should can must use uses using
used receive receives received read reads reading update updates write writes
return returns returning show shows draw create build design explain describe
diagram architecture flow workflow system template teaching engineering user
users input inputs output final verified valid validate validates validated
verify checks check fail fails failed failure failures success succeed succeeds
give gives project event events rule rules clarify clarifies goal goals plan
plans planning next step steps act acts action actions execute executes external
observe observes observation decide decides work working done back long term
long-term reasoning reason coordinate coordination process processes processing
requesting perform performs execution looped retrying guard safe safety constraint
constraints budget tool-call calls call calling dispatch result context state
feedback-loop control core optional simple basic ordered sequential deliver
delivery human review reviewed notes memory agent ai api
""".split())
_ZH_SCAFFOLD = (
    "最终形成", "最终", "最后", "长期", "工作", "用户", "接收", "进入", "读取", "更新",
    "使用", "调用", "通过", "经过", "执行", "返回", "输出", "失败时", "失败", "成功",
    "根据", "重新规划", "规划", "推理", "协调", "展示", "构建", "画一个", "画", "绘制",
    "生成", "创建", "设计", "解释", "包含", "组成", "中文", "架构图", "架构", "流程图",
    "流程", "模板", "平台", "可信", "已验证", "验证", "一个", "并", "的", "和", "与", "后", "时", "并且",
)


def _unrecognized_fragments(brief: str) -> list:
    remainder = brief.lower()
    aliases = sorted({term for terms in _CONCEPTS.values() for term in terms}, key=len, reverse=True)
    for term in aliases:
        if re.fullmatch(r"[a-z][a-z -]*", term):
            remainder = re.sub(r"(?<![a-z0-9_])" + re.escape(term) + r"(?:s|es)?(?![a-z0-9_])", " ", remainder)
        else:
            remainder = remainder.replace(term, " ")
    for phrase in sorted(_ZH_SCAFFOLD, key=len, reverse=True):
        remainder = remainder.replace(phrase, " ")
    return sorted({word for word in re.findall(r"[a-z][a-z0-9_-]*|[\u3400-\u9fff]+", remainder)
                   if word not in _EN_SCAFFOLD})


def contains_term(text: str, terms: Iterable[str]) -> bool:
    """Match Latin tokens at boundaries; CJK phrases do not require spaces."""
    lowered = text.lower()
    for term in terms:
        if re.fullmatch(r"[a-z][a-z -]*", term):
            if re.search(r"(?<![a-z0-9_])" + re.escape(term) + r"(?:s|es)?(?![a-z0-9_])", lowered):
                return True
        elif term in lowered:
            return True
    return False


def brief_diagnostics(brief: str, represented: Iterable[str]) -> Dict[str, Any]:
    """Compare recognized vocabulary to template slots, never extract nouns."""
    recognized = {name for name, aliases in _CONCEPTS.items() if contains_term(brief, aliases)}
    available = set(represented)
    matched = sorted(recognized & available)
    unmatched = sorted(recognized - available)
    unrecognized = _unrecognized_fragments(brief)
    # Scripts outside English/Chinese make this diagnostic unassessed even if
    # the text embeds an English template keyword. This is not language ID.
    unsupported_script = any(
        char.isalpha() and not ("a" <= char.lower() <= "z" or "\u3400" <= char <= "\u9fff")
        for char in brief
    )
    status = "unassessed"
    ratio = None
    if not unsupported_script and unmatched:
        status = "partial"
        ratio = round(len(matched) / len(recognized), 4)
    elif not unsupported_script and not unrecognized and "agent" in matched and len(matched) >= 3:
        status = "template-match"
        ratio = 1.0
    guidance = "Use --plan for explicit entities and relations, or the AniDiagram Skill workflow with source review."
    warnings = []
    if status == "partial":
        warnings.append({
            "code": "brief_coverage_low",
            "message": "The agent template omits recognized concepts: " + ", ".join(unmatched) + ". " + guidance,
        })
    elif status == "unassessed":
        warnings.append({
            "code": "brief_coverage_unassessed",
            "message": "This brief's language or domain is not sufficiently covered by the agent-template vocabulary. "
            + ("Unrecognized fragments: " + ", ".join(unrecognized) + ". " if unrecognized else "") + guidance,
        })
    return {
        "method": "agent-template-v1",
        "semantic_accuracy": "not-assessed",
        "limitations": "Known-term coverage is not noun extraction, full brief coverage, language identification, or semantic correctness. Residual lexical fragments conservatively mark unfamiliar vocabulary as unassessed. Negation and relationship order are not assessed; all template structure requires review.",
        "coverage": {
            "method": "known-term-heuristic-v1",
            "status": status,
            "matched_terms": matched,
            "unmatched_terms": unmatched,
            "unrecognized_fragments": unrecognized,
            "ratio": ratio,
        },
        "warnings": warnings,
    }


def validate_planning(value: Any) -> Dict[str, Any]:
    """Validate optional diagnostic metadata at both input boundaries."""
    if isinstance(value, Mapping) and value.get("method") == "explicit-rules-v1":
        return validate_rule_planning(value)
    if isinstance(value, Mapping) and value.get("method") == "subprocess-plan-v1":
        return validate_subprocess_planning(value)
    if not isinstance(value, Mapping) or set(value) != {"method", "semantic_accuracy", "limitations", "coverage", "warnings"}:
        raise ValueError("planning requires method, semantic_accuracy, limitations, coverage, and warnings")
    if value["method"] != "agent-template-v1" or value["semantic_accuracy"] != "not-assessed":
        raise ValueError("planning must identify agent-template-v1 and semantic_accuracy not-assessed")
    if not isinstance(value["limitations"], str) or not value["limitations"].strip():
        raise ValueError("planning.limitations must be non-empty text")
    coverage = value["coverage"]
    if not isinstance(coverage, Mapping) or set(coverage) != {"method", "status", "matched_terms", "unmatched_terms", "unrecognized_fragments", "ratio"}:
        raise ValueError("planning.coverage has invalid fields")
    if coverage["method"] != "known-term-heuristic-v1" or not isinstance(coverage["status"], str) or coverage["status"] not in {"partial", "template-match", "unassessed"}:
        raise ValueError("planning.coverage requires a known heuristic method and status")
    for field in ("matched_terms", "unmatched_terms", "unrecognized_fragments"):
        terms = coverage[field]
        if not isinstance(terms, list) or any(not isinstance(term, str) or not term for term in terms) or len(terms) != len(set(terms)):
            raise ValueError("planning.coverage." + field + " must contain unique non-empty strings")
    ratio = coverage["ratio"]
    if ratio is not None and (type(ratio) not in (int, float) or not math.isfinite(ratio) or not 0 <= ratio <= 1):
        raise ValueError("planning.coverage.ratio must be null or a number between 0 and 1")
    if (coverage["status"] == "unassessed") != (ratio is None):
        raise ValueError("planning.coverage.ratio must be null exactly when coverage is unassessed")
    if set(coverage["matched_terms"]) & set(coverage["unmatched_terms"]):
        raise ValueError("planning.coverage matched and unmatched terms must be disjoint")
    if coverage["status"] == "template-match" and (
        ratio != 1 or coverage["unmatched_terms"] or coverage["unrecognized_fragments"]
        or "agent" not in coverage["matched_terms"] or len(coverage["matched_terms"]) < 3
    ):
        raise ValueError("planning.coverage template-match requires only represented template vocabulary")
    if coverage["status"] == "partial":
        matched_count, unmatched_count = len(coverage["matched_terms"]), len(coverage["unmatched_terms"])
        if not unmatched_count or ratio != round(matched_count / (matched_count + unmatched_count), 4):
            raise ValueError("planning.coverage partial ratio must match the recognized-term counts")
    if not isinstance(value["warnings"], list):
        raise ValueError("planning.warnings must be an array")
    for warning in value["warnings"]:
        if (not isinstance(warning, Mapping) or set(warning) != {"code", "message"}
                or not isinstance(warning["code"], str) or warning["code"] not in {"brief_coverage_low", "brief_coverage_unassessed"}
                or not isinstance(warning["message"], str) or not warning["message"].strip()):
            raise ValueError("planning.warnings contains an invalid warning")
    expected_codes = {"partial": ["brief_coverage_low"], "unassessed": ["brief_coverage_unassessed"], "template-match": []}
    if [warning["code"] for warning in value["warnings"]] != expected_codes[coverage["status"]]:
        raise ValueError("planning.warnings must preserve the coverage status warning")
    return deepcopy(dict(value))


def rule_diagnostics(provenance: list) -> Dict[str, Any]:
    """Report grammar coverage of source clauses, never semantic correctness."""
    unsupported = [item['text'] for item in provenance if item['status'] != 'extracted']
    parsed = sum(item['status'] == 'extracted' for item in provenance)
    warnings = []
    if unsupported:
        warnings.append({'code': 'brief_rule_unparsed', 'message': 'Some clauses were not fully extracted: ' + '; '.join(unsupported) + '. Use an authored --plan to express unresolved relations.'})
    if any(item['status'] == 'negated' for item in provenance):
        warnings.append({'code': 'brief_rule_negation', 'message': 'Negated clauses are preserved as source evidence and are never drawn as positive relations.'})
    return {
        'method': 'explicit-rules-v1', 'semantic_accuracy': 'not-assessed',
        'limitations': 'Explicit EN/ZH sentence grammar only, not semantic certification. Coverage counts fully matched clauses, not facts. Unsupported predicates, negation, and ambiguous pronouns are retained. Relative which resolves only a singular immediately preceding object. Database ownership remains unresolved unless explicit.',
        'coverage': {'method': 'explicit-clause-rules-v1', 'status': 'partial' if unsupported else 'extracted',
                     'parsed_clauses': parsed, 'total_clauses': len(provenance),
                     'unparsed_spans': list(dict.fromkeys(unsupported)),
                     'ratio': round(parsed / len(provenance), 4) if provenance else 0},
        'provenance': deepcopy(provenance), 'warnings': warnings,
    }


def validate_rule_planning(value: Mapping[str, Any]) -> Dict[str, Any]:
    fields = {'method', 'semantic_accuracy', 'limitations', 'coverage', 'warnings', 'provenance'}
    if set(value) != fields or value.get('semantic_accuracy') != 'not-assessed':
        raise ValueError('planning rule diagnostics require exact fields and semantic_accuracy not-assessed')
    if not isinstance(value['limitations'], str) or not value['limitations'].strip():
        raise ValueError('planning.limitations must be non-empty text')
    provenance = value['provenance']
    if not isinstance(provenance, list) or not provenance:
        raise ValueError('planning.provenance must contain source clauses')
    seen = set()
    previous_end = 0
    for item in provenance:
        if (not isinstance(item, Mapping) or set(item) != {'source_ref', 'text', 'start', 'end', 'status', 'reason'}
                or any(not isinstance(item[key], str) or not item[key].strip() for key in ('source_ref', 'text', 'reason'))
                or item['source_ref'] in seen or type(item['start']) is not int or type(item['end']) is not int
                or item['start'] < previous_end or item['end'] != item['start'] + len(item['text'])
                or not isinstance(item['status'], str) or item['status'] not in {'extracted', 'partial', 'unsupported', 'negated'}):
            raise ValueError('planning.provenance contains an invalid source clause')
        seen.add(item['source_ref'])
        previous_end = item['end']
    expected = rule_diagnostics(provenance)
    coverage = value['coverage']
    if (not isinstance(coverage, Mapping) or set(coverage) != set(expected['coverage'])
            or type(coverage.get('ratio')) not in (int, float)
            or type(coverage.get('parsed_clauses')) is not int or type(coverage.get('total_clauses')) is not int
            or dict(coverage) != expected['coverage']):
        raise ValueError('planning.coverage must agree with rule provenance counts and spans')
    warnings = value['warnings']
    if (not isinstance(warnings, list) or any(not isinstance(w, Mapping) or set(w) != {'code', 'message'}
            or not isinstance(w['message'], str) or not w['message'].strip() for w in warnings)
            or [w['code'] for w in warnings] != [w['code'] for w in expected['warnings']]):
        raise ValueError('planning.warnings must preserve unresolved rule clauses and negation warnings')
    return deepcopy(dict(value))


def subprocess_diagnostics() -> Dict[str, Any]:
    return {'method': 'subprocess-plan-v1', 'semantic_accuracy': 'not-assessed',
            'limitations': 'Opt-in external command output passed DiagramPlan structural validation only. Provider accuracy, source fidelity, and complete brief coverage are not assessed.',
            'coverage': {'method': 'provider-unassessed-v1', 'status': 'unassessed', 'ratio': None},
            'warnings': [{'code': 'brief_provider_unassessed', 'message': 'Provider output has structural validation only; review all entities, relations, and provenance against the brief.'}]}


def validate_subprocess_planning(value: Mapping[str, Any]) -> Dict[str, Any]:
    if dict(value) != subprocess_diagnostics():
        raise ValueError('planning subprocess diagnostics must retain structural-only validation limits')
    return deepcopy(dict(value))

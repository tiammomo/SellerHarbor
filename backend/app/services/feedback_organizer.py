from __future__ import annotations

import re

from app.models.schemas import FeedbackOrganization, OrganizeFeedbackRequest, PlatformRule, Product
from app.services.platform_rules import platform_rule


FACT_KEYWORDS = {
    "支持",
    "可以",
    "可",
    "有",
    "带",
    "收到",
    "到手",
    "包装",
    "物流",
    "客服",
    "售后",
    "清洗",
    "预约",
    "使用",
    "洗后",
    "不缩水",
    "不褪色",
    "无异味",
    "没有异味",
    "防泼水",
    "独立包装",
}

OPINION_KEYWORDS = {
    "喜欢",
    "满意",
    "舒服",
    "方便",
    "省事",
    "好用",
    "好看",
    "安静",
    "细腻",
    "顺滑",
    "不错",
    "值",
    "划算",
    "合适",
    "轻",
    "稳",
    "香",
    "清爽",
    "有质感",
}

UNCERTAIN_KEYWORDS = {
    "可能",
    "应该",
    "大概",
    "估计",
    "听说",
    "据说",
    "感觉能",
    "号称",
    "宣传说",
}

HIGH_RISK_TERMS = {
    "治疗",
    "治愈",
    "药用",
    "医用级",
    "减肥",
    "燃脂",
    "保证有效",
    "永久有效",
    "全网最低",
    "第一",
    "最",
}


def organize_feedback(product: Product, payload: OrganizeFeedbackRequest) -> FeedbackOrganization:
    raw_text = _normalize_text(payload.rawText)
    rule = platform_rule(payload.platform or "taobao")
    sentences = _split_sentences(raw_text)
    uncertain_claims = _extract_uncertain_claims(sentences)
    confirmed_facts = _extract_confirmed_facts(product, sentences, uncertain_claims)
    subjective_opinions = _extract_subjective_opinions(sentences, confirmed_facts, uncertain_claims)
    risk_flags = _risk_flags(product=product, raw_text=raw_text, rule=rule, confirmed_facts=confirmed_facts, uncertain_claims=uncertain_claims)
    recommended = _recommended_content_types(
        consent_status=payload.consentStatus,
        confirmed_facts=confirmed_facts,
        subjective_opinions=subjective_opinions,
        risk_flags=risk_flags,
    )
    readiness_score = _readiness_score(
        confirmed_facts=confirmed_facts,
        subjective_opinions=subjective_opinions,
        uncertain_claims=uncertain_claims,
        risk_flags=risk_flags,
        consent_status=payload.consentStatus,
    )
    return FeedbackOrganization(
        productId=product.id,
        productName=product.name,
        sourceType=payload.sourceType,
        consentStatus=payload.consentStatus,
        sourceSummary=_summary(raw_text, sentences),
        confirmedFacts=confirmed_facts,
        subjectiveOpinions=subjective_opinions,
        uncertainClaims=uncertain_claims,
        riskFlags=risk_flags,
        recommendedContentTypes=recommended,
        readinessScore=readiness_score,
        nextActions=_next_actions(
            confirmed_facts=confirmed_facts,
            subjective_opinions=subjective_opinions,
            uncertain_claims=uncertain_claims,
            risk_flags=risk_flags,
            consent_status=payload.consentStatus,
        ),
        sourceTrace=[
            "organizer.raw_feedback",
            "organizer.sentence_rules",
            "product.forbidden_claims",
            f"rules.platform.{rule.platform}",
        ],
    )


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\r", "\n")).strip()


def _split_sentences(text: str) -> list[str]:
    chunks = re.split(r"[。！？!?；;\n]+", text)
    sentences: list[str] = []
    for chunk in chunks:
        item = _clean_sentence(chunk)
        if not item:
            continue
        parts = re.split(r"[，,]+", item)
        sentences.extend(_clean_sentence(part) for part in parts if _clean_sentence(part))
    return _unique(sentences)[:12]


def _clean_sentence(value: str) -> str:
    item = value.strip(" ，,、\t")
    for prefix in ("客户反馈", "客户回访说", "客户说", "回访说", "用户反馈", "用户说", "表示"):
        if item.startswith(prefix):
            item = item[len(prefix):].strip(" ：:，,、\t")
    return item


def _extract_uncertain_claims(sentences: list[str]) -> list[str]:
    return _unique(sentence for sentence in sentences if _contains_any(sentence, UNCERTAIN_KEYWORDS))[:6]


def _extract_confirmed_facts(product: Product, sentences: list[str], uncertain_claims: list[str]) -> list[str]:
    product_terms = _product_terms(product)
    uncertain_set = set(uncertain_claims)
    facts: list[str] = []
    for sentence in sentences:
        if sentence in uncertain_set:
            continue
        if _contains_any(sentence, product_terms) or _contains_any(sentence, FACT_KEYWORDS):
            if not _is_pure_opinion(sentence):
                facts.append(sentence)
    return _unique(facts)[:8]


def _extract_subjective_opinions(
    sentences: list[str],
    confirmed_facts: list[str],
    uncertain_claims: list[str],
) -> list[str]:
    fact_set = set(confirmed_facts)
    uncertain_set = set(uncertain_claims)
    opinions: list[str] = []
    for sentence in sentences:
        if sentence in uncertain_set:
            continue
        if _contains_any(sentence, OPINION_KEYWORDS) or _is_pure_opinion(sentence):
            if sentence not in fact_set or _contains_any(sentence, OPINION_KEYWORDS):
                opinions.append(sentence)
    return _unique(opinions)[:8]


def _risk_flags(
    *,
    product: Product,
    raw_text: str,
    rule: PlatformRule,
    confirmed_facts: list[str],
    uncertain_claims: list[str],
) -> list[str]:
    flags: list[str] = []
    if not confirmed_facts:
        flags.append("missing_confirmed_facts")
    if uncertain_claims:
        flags.append("uncertain_claims_present")
    if any(term and term in raw_text for term in product.forbiddenClaims):
        flags.append("forbidden_claim")
    if any(term and term in raw_text for term in rule.riskTerms):
        flags.append("platform_sensitive_claim")
    if any(term and term in raw_text for term in HIGH_RISK_TERMS):
        flags.append("high_risk_claim")
    return _unique(flags)


def _recommended_content_types(
    *,
    consent_status: str,
    confirmed_facts: list[str],
    subjective_opinions: list[str],
    risk_flags: list[str],
) -> list[str]:
    if "forbidden_claim" in risk_flags or "high_risk_claim" in risk_flags:
        return ["review_invitation", "cs_followup"]
    if not confirmed_facts:
        return ["review_invitation", "cs_followup"]
    recommended = ["review_invitation", "cs_followup", "recommendation", "detail_page"]
    if consent_status == "confirmed" and subjective_opinions:
        recommended.append("experience_copy")
    return recommended


def _readiness_score(
    *,
    confirmed_facts: list[str],
    subjective_opinions: list[str],
    uncertain_claims: list[str],
    risk_flags: list[str],
    consent_status: str,
) -> int:
    score = 35
    score += min(35, len(confirmed_facts) * 10)
    score += min(20, len(subjective_opinions) * 5)
    if consent_status == "confirmed":
        score += 10
    if consent_status == "pending":
        score -= 15
    score -= min(25, len(uncertain_claims) * 8)
    score -= min(35, len(risk_flags) * 10)
    return max(0, min(100, score))


def _next_actions(
    *,
    confirmed_facts: list[str],
    subjective_opinions: list[str],
    uncertain_claims: list[str],
    risk_flags: list[str],
    consent_status: str,
) -> list[str]:
    actions: list[str] = []
    if consent_status == "pending":
        actions.append("先确认客户授权状态，再生成体验类内容。")
    if not confirmed_facts:
        actions.append("补充可验证事实，例如规格、功能、物流、客服或实际使用场景。")
    if not subjective_opinions:
        actions.append("补充客户主观感受，帮助生成更自然的口碑素材。")
    if uncertain_claims:
        actions.append("不确定表达不要直接作为事实使用，需人工核实或降级为主观感受。")
    if "forbidden_claim" in risk_flags or "high_risk_claim" in risk_flags:
        actions.append("删除禁用词和高风险承诺，再进入生成或导出流程。")
    if not actions:
        actions.append("整理结果可直接保存为真实反馈，并用于评价邀请、推荐语或详情页口碑素材。")
    return actions


def _summary(text: str, sentences: list[str]) -> str:
    if len(text) <= 180:
        return text
    summary = "。".join(sentences[:3]).strip()
    return summary[:180]


def _product_terms(product: Product) -> set[str]:
    terms: set[str] = set()
    terms.update(product.sellingPoints)
    terms.update(product.usageScenarios)
    terms.update(product.targetAudiences)
    terms.update(product.attributes.keys())
    terms.update(product.attributes.values())
    terms.add(product.name)
    return {term for term in terms if term and len(term) >= 2}


def _is_pure_opinion(sentence: str) -> bool:
    return sentence.startswith(("觉得", "感觉", "整体", "总体")) or sentence.endswith(("不错", "满意", "喜欢", "舒服", "方便"))


def _contains_any(value: str, terms) -> bool:
    return any(term and term in value for term in terms)


def _unique(items) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.models.schemas import Feedback, GeneratedContent, GenerationConfig, Product, QualityReport
from app.services.llm import llm_client
from app.services.platform_rules import platform_rule
from app.utils.ids import new_id
from app.db.repository import now_iso


class GenerationState(TypedDict, total=False):
    product: Product
    feedback: Feedback | None
    config: GenerationConfig
    rule: dict[str, Any]
    facts: dict[str, Any]
    policy: dict[str, Any]
    llm_output: dict[str, Any]
    contents: list[GeneratedContent]
    rewrite_count: int


MAX_REWRITE_ATTEMPTS = 1
EXPERIENCE_CONTENT_TYPES = {"review_draft", "experience_copy", "recommendation"}
REWRITABLE_RISKS = {
    "forbidden_claim",
    "platform_sensitive_claim",
    "high_repetition_risk",
    "high_exaggeration_risk",
    "low_quality_score",
    "mild_exaggeration",
    "minor_concern",
}


async def run_generation_agent(product: Product, feedback: Feedback | None, config: GenerationConfig) -> list[GeneratedContent]:
    graph = _build_graph()
    result = await graph.ainvoke({"product": product, "feedback": feedback, "config": config, "rewrite_count": 0})
    return result["contents"]


def _build_graph():
    builder = StateGraph(GenerationState)
    builder.add_node("normalize_input", _normalize_input)
    builder.add_node("apply_platform_rule", _apply_platform_rule)
    builder.add_node("extract_facts", _extract_facts)
    builder.add_node("policy_guard", _policy_guard)
    builder.add_node("safe_alternative", _safe_alternative)
    builder.add_node("generate_drafts", _generate_drafts)
    builder.add_node("evaluate_and_check_risk", _evaluate_and_check_risk)
    builder.add_node("rewrite_drafts", _rewrite_drafts)

    builder.set_entry_point("normalize_input")
    builder.add_edge("normalize_input", "apply_platform_rule")
    builder.add_edge("apply_platform_rule", "extract_facts")
    builder.add_edge("extract_facts", "policy_guard")
    builder.add_conditional_edges(
        "policy_guard",
        _route_after_policy,
        {"generate": "generate_drafts", "safe_alternative": "safe_alternative"},
    )
    builder.add_edge("safe_alternative", END)
    builder.add_edge("generate_drafts", "evaluate_and_check_risk")
    builder.add_conditional_edges(
        "evaluate_and_check_risk",
        _route_after_evaluation,
        {"rewrite": "rewrite_drafts", "end": END},
    )
    builder.add_edge("rewrite_drafts", "evaluate_and_check_risk")
    return builder.compile()


async def _normalize_input(state: GenerationState) -> GenerationState:
    config = state["config"]
    rule = platform_rule(config.platform)
    if not config.merchantType:
        config = config.model_copy(update={"merchantType": rule.merchantType})
    return {**state, "config": config}


async def _apply_platform_rule(state: GenerationState) -> GenerationState:
    rule = platform_rule(state["config"].platform)
    return {**state, "rule": rule.model_dump()}


async def _extract_facts(state: GenerationState) -> GenerationState:
    product = state["product"]
    feedback = state.get("feedback")
    facts = {
        "productFacts": {
            "attributes": product.attributes,
            "sellingPoints": product.sellingPoints,
            "usageScenarios": product.usageScenarios,
            "targetAudiences": product.targetAudiences,
        },
        "feedbackFacts": feedback.confirmedFacts if feedback else [],
        "subjectiveOpinions": feedback.subjectiveOpinions if feedback else [],
        "forbiddenClaims": product.forbiddenClaims,
    }
    return {**state, "facts": facts}


async def _policy_guard(state: GenerationState) -> GenerationState:
    config = state["config"]
    rule = state["rule"]
    feedback = state.get("feedback")
    risk_flags: list[str] = []
    blocking_flags: list[str] = []
    if rule.get("requireExperienceEvidence") and feedback is None and config.contentType in EXPERIENCE_CONTENT_TYPES:
        risk_flags.append("missing_feedback_context")
        if config.persona == "first_person":
            blocking_flags.append("missing_feedback_context")
    if rule.get("merchantVoiceReviewRisk") and config.persona == "merchant" and config.contentType in EXPERIENCE_CONTENT_TYPES:
        risk_flags.append("merchant_voice_review_risk")
        blocking_flags.append("merchant_voice_review_risk")
    return {
        **state,
        "policy": {
            "riskFlags": _unique(risk_flags),
            "blockingFlags": _unique(blocking_flags),
            "allowGeneration": not blocking_flags,
        },
    }


def _route_after_policy(state: GenerationState) -> str:
    return "generate" if state.get("policy", {}).get("allowGeneration", True) else "safe_alternative"


async def _safe_alternative(state: GenerationState) -> GenerationState:
    policy = state.get("policy", {})
    rule = state["rule"]
    config = state["config"]
    product = state["product"]
    blocking_flags = policy.get("blockingFlags", []) or policy.get("riskFlags", [])
    task_id = new_id("task")
    text = _safe_alternative_text(product, rule, blocking_flags)
    risk_flags = _unique([*policy.get("riskFlags", []), "safe_alternative_generated"])
    content = GeneratedContent(
        id=new_id("gen"),
        taskId=task_id,
        text=text,
        score=62,
        riskFlags=risk_flags,
        sourceTrace=[
            "agent.node.policy_guard",
            "agent.node.safe_alternative",
            f"rules.platform.{rule['platform']}",
            "product.name",
            "product.selling_points",
        ],
        reviewStatus="pending",
        qualityReport=QualityReport(
            naturalness=72,
            specificity=60,
            factConsistency=90,
            platformFit=68 if config.contentType in EXPERIENCE_CONTENT_TYPES else 75,
            repetitionRisk=5,
            exaggerationRisk=5,
            overallScore=62,
        ),
        createdAt=now_iso(),
    )
    return {**state, "contents": [content]}


async def _generate_drafts(state: GenerationState) -> GenerationState:
    system = """你是 ReviewPilot 的合规口碑内容生成器。
你必须基于商品资料、真实反馈和平台规则生成可审核草稿。
不要编造真实消费者身份、订单、物流、疗效、收益、排名或未提供的使用经历。
qualityReport 中 repetitionRisk 和 exaggerationRisk 的含义是风险分，0 代表低风险，100 代表高风险。
输出必须是严格 JSON，不要 Markdown，不要解释。
"""
    payload = {
        "task": "生成商家可审核的口碑内容草稿",
        "outputSchema": {
            "items": [
                {
                    "text": "最终草稿文本",
                    "score": "0-100",
                    "riskFlags": [],
                    "sourceTrace": [],
                    "qualityReport": {
                        "naturalness": "0-100",
                        "specificity": "0-100",
                        "factConsistency": "0-100",
                        "platformFit": "0-100",
                        "repetitionRisk": "0-100",
                        "exaggerationRisk": "0-100",
                        "overallScore": "0-100",
                    },
                }
            ]
        },
        "count": state["config"].count,
        "generationConfig": state["config"].model_dump(),
        "platformRule": state["rule"],
        "product": state["product"].model_dump(),
        "feedback": state["feedback"].model_dump() if state.get("feedback") else None,
        "facts": state["facts"],
        "policy": state["policy"],
        "constraints": [
            "每条 text 必须符合 platformRule 的平台语气和结构。",
            "必须避开 forbiddenClaims 和 platformRule.riskTerms。",
            "如果缺少真实反馈，不要写第一人称已购买或已使用经历。",
            "sourceTrace 必须包含 rules.platform.<platform>，并尽量包含 product.* 和 feedback.*。",
            "riskFlags 必须真实反映风险；如果 repetitionRisk 或 exaggerationRisk 大于等于 70，riskFlags 必须说明原因。",
            "只返回 JSON: {\"items\":[...]}。",
        ],
    }
    llm_output = await llm_client.generate_json(system=system, payload=payload)
    return {**state, "llm_output": llm_output}


async def _rewrite_drafts(state: GenerationState) -> GenerationState:
    system = """你是 ReviewPilot 的合规重写器。
你只负责修正已有候选文案中的风险和低质量问题，不新增未经提供的事实。
重写后必须更克制、更具体、更符合平台规则。
qualityReport 中 repetitionRisk 和 exaggerationRisk 的含义是风险分，0 代表低风险，100 代表高风险。
输出必须是严格 JSON，不要 Markdown，不要解释。
"""
    payload = {
        "task": "重写低质或有风险的候选口碑内容",
        "rewriteAttempt": state.get("rewrite_count", 0) + 1,
        "count": state["config"].count,
        "generationConfig": state["config"].model_dump(),
        "platformRule": state["rule"],
        "product": state["product"].model_dump(),
        "feedback": state["feedback"].model_dump() if state.get("feedback") else None,
        "facts": state["facts"],
        "policy": state["policy"],
        "rejectedCandidates": [content.model_dump() for content in state.get("contents", [])],
        "outputSchema": {
            "items": [
                {
                    "text": "重写后的草稿文本",
                    "score": "0-100",
                    "riskFlags": [],
                    "sourceTrace": [],
                    "qualityReport": {
                        "naturalness": "0-100",
                        "specificity": "0-100",
                        "factConsistency": "0-100",
                        "platformFit": "0-100",
                        "repetitionRisk": "0-100",
                        "exaggerationRisk": "0-100",
                        "overallScore": "0-100",
                    },
                }
            ]
        },
        "constraints": [
            "必须删除或弱化 forbidden_claim、platform_sensitive_claim、high_repetition_risk、high_exaggeration_risk 对应问题。",
            "不得新增商品资料、反馈、订单、物流、售后或使用经历中没有出现的事实。",
            "保留 sourceTrace，并额外包含 agent.node.rewrite_drafts。",
            "只返回 JSON: {\"items\":[...]}。",
        ],
    }
    llm_output = await llm_client.generate_json(system=system, payload=payload)
    return {**state, "llm_output": llm_output, "rewrite_count": state.get("rewrite_count", 0) + 1}


async def _evaluate_and_check_risk(state: GenerationState) -> GenerationState:
    config = state["config"]
    product = state["product"]
    feedback = state.get("feedback")
    rule = state["rule"]
    task_id = new_id("task")
    contents: list[GeneratedContent] = []
    for raw in state["llm_output"].get("items", [])[: config.count]:
        text = str(raw.get("text", "")).strip()
        if not text:
            continue
        source_trace = _unique(
            [
                "agent.node.evaluate_and_check_risk",
                *(["agent.node.rewrite_drafts"] if state.get("rewrite_count", 0) else []),
                f"rules.platform.{rule['platform']}",
                "product.selling_points",
                "product.usage_scenarios",
                *(raw.get("sourceTrace", []) or []),
                *([f"feedback.{feedback.id}.confirmed_facts", f"feedback.{feedback.id}.subjective_opinions"] if feedback else []),
            ]
        )
        score = _clamp(raw.get("score"), 80)
        quality_raw = raw.get("qualityReport") or {}
        repetition_risk = _clamp(quality_raw.get("repetitionRisk"), 8)
        exaggeration_risk = _clamp(quality_raw.get("exaggerationRisk"), 8)
        risk_flags = _unique(
            [
                *state.get("policy", {}).get("riskFlags", []),
                *raw.get("riskFlags", []),
                *_detect_risks(text, product, rule),
                *(["high_repetition_risk"] if repetition_risk >= 70 else []),
                *(["high_exaggeration_risk"] if exaggeration_risk >= 70 else []),
                *(["low_quality_score"] if score < 70 else []),
            ]
        )
        if "high_repetition_risk" in risk_flags or "high_exaggeration_risk" in risk_flags:
            score = min(score, 69)
        if score < 70 and "low_quality_score" not in risk_flags:
            risk_flags.append("low_quality_score")
        quality = QualityReport(
            naturalness=_clamp(quality_raw.get("naturalness"), score),
            specificity=_clamp(quality_raw.get("specificity"), score),
            factConsistency=_clamp(quality_raw.get("factConsistency"), score),
            platformFit=_clamp(quality_raw.get("platformFit"), score),
            repetitionRisk=repetition_risk,
            exaggerationRisk=exaggeration_risk,
            overallScore=score,
        )
        contents.append(
            GeneratedContent(
                id=new_id("gen"),
                taskId=task_id,
                text=text,
                score=score,
                riskFlags=risk_flags,
                sourceTrace=source_trace,
                reviewStatus="pending",
                qualityReport=quality,
                createdAt=now_iso(),
            )
        )
    if not contents:
        raise RuntimeError("LLM returned no usable review drafts")
    return {**state, "contents": contents}


def _route_after_evaluation(state: GenerationState) -> str:
    if state.get("rewrite_count", 0) >= MAX_REWRITE_ATTEMPTS:
        return "end"
    if _needs_rewrite(state.get("contents", [])):
        return "rewrite"
    return "end"


def _needs_rewrite(contents: list[GeneratedContent]) -> bool:
    for content in contents:
        if content.score < 70:
            return True
        if any(flag in REWRITABLE_RISKS for flag in content.riskFlags):
            return True
    return False


def _detect_risks(text: str, product: Product, rule: dict[str, Any]) -> list[str]:
    risks = []
    if any(term and term in text for term in product.forbiddenClaims):
        risks.append("forbidden_claim")
    if any(term and term in text for term in rule.get("riskTerms", [])):
        risks.append("platform_sensitive_claim")
    return risks


def _safe_alternative_text(product: Product, rule: dict[str, Any], blocking_flags: list[str]) -> str:
    selling_points = "、".join(product.sellingPoints[:3]) or product.name
    platform_name = rule.get("displayName") or rule.get("platform") or "目标平台"
    if "missing_feedback_context" in blocking_flags:
        return (
            f"当前缺少已确认客户反馈，不建议直接生成第一人称好评草稿。"
            f"可以先用于{platform_name}的评价邀请：如果你体验过 {product.name} 的{selling_points}，"
            "欢迎结合真实使用场景留下感受，我们会根据反馈继续优化商品和服务。"
        )
    if "merchant_voice_review_risk" in blocking_flags:
        return (
            f"商家口吻不适合伪装成用户好评。可以改为商家侧说明：{product.name}主打{selling_points}，"
            "建议用户结合真实体验分享使用场景和具体感受，避免夸大效果或替用户下结论。"
        )
    return (
        f"当前请求存在合规风险，建议先补充真实反馈依据。可围绕{product.name}的{selling_points}"
        "生成评价邀请或客服回访话术，再由人工审核后使用。"
    )


def _clamp(value: Any, fallback: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = fallback
    return max(0, min(100, number))


def _unique(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result

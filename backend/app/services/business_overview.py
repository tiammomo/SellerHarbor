from __future__ import annotations

from collections import Counter

from app.db.repository import now_iso
from app.models.schemas import (
    BusinessContentMixItem,
    BusinessEvidenceCoverage,
    BusinessOverview,
    BusinessProductGap,
    BusinessRecommendedAction,
    BusinessReviewFunnel,
    BusinessRiskBreakdownItem,
    Feedback,
    GeneratedContent,
    GenerationTask,
    Product,
)


CONTENT_TYPE_LABELS = {
    "review_draft": "口碑草稿",
    "experience_copy": "使用体验",
    "recommendation": "推荐语",
    "review_invitation": "评价邀请",
    "share_guide": "晒单引导",
    "cs_followup": "客服回访",
    "detail_page": "详情页口碑",
}

RISK_FLAG_GUIDANCE = {
    "missing_feedback_context": ("缺少真实反馈依据", "critical", "补充客户授权反馈，或切换为商家口吻的评价邀请/推荐语。"),
    "merchant_voice_review_risk": ("商家口吻体验风险", "critical", "体验类内容避免商家冒充用户表达，改为评价邀请或详情页口碑。"),
    "safe_alternative_generated": ("安全替代话术", "info", "可用于客服回访或评价邀请，不建议作为用户评价直接发布。"),
    "forbidden_claim": ("命中商品禁用表达", "critical", "删除禁用词，并在商品资料中完善替代表达。"),
    "platform_sensitive_claim": ("平台敏感表达", "warning", "核对目标平台规则，弱化绝对化或强承诺表述。"),
    "high_repetition_risk": ("重复风险较高", "warning", "增加真实场景、规格细节和客户反馈差异。"),
    "high_exaggeration_risk": ("夸大风险较高", "critical", "把强效果承诺改为可验证事实或主观感受边界。"),
    "low_quality_score": ("质量分偏低", "warning", "补充商品卖点、使用场景或真实反馈后重新生成。"),
    "mild_exaggeration": ("轻度夸张", "warning", "弱化语气，避免必买、最好、保证有效等表达。"),
    "minor_concern": ("轻微关注项", "info", "人工复核来源依据后再通过。"),
}


def build_business_overview(
    *,
    products: list[Product],
    feedbacks: list[Feedback],
    tasks: list[GenerationTask],
    contents: list[GeneratedContent],
) -> BusinessOverview:
    usable_feedback_product_ids = {
        feedback.productId
        for feedback in feedbacks
        if feedback.consentStatus in {"confirmed", "not_required"}
    }
    ready_products = [
        product
        for product in products
        if _has_strong_profile(product) and product.id in usable_feedback_product_ids
    ]
    gaps = _build_product_gaps(products, usable_feedback_product_ids)
    review_funnel = _build_review_funnel(contents)
    risk_breakdown = _build_risk_breakdown(contents)
    content_mix = _build_content_mix(tasks, contents)
    recommended_actions = _build_recommended_actions(
        products=products,
        gaps=gaps,
        review_funnel=review_funnel,
        risk_breakdown=risk_breakdown,
        contents=contents,
    )
    total_products = len(products)
    products_with_feedback = len(usable_feedback_product_ids)
    return BusinessOverview(
        positioning="内容与评价运营助手",
        primaryUseCases=["评价邀请", "客服回访", "商品推荐语", "详情页口碑素材"],
        evidenceCoverage=BusinessEvidenceCoverage(
            totalProducts=total_products,
            productsWithUsableFeedback=products_with_feedback,
            productsWithoutUsableFeedback=max(0, total_products - products_with_feedback),
            readyProducts=len(ready_products),
            coverageRate=_percent(products_with_feedback, total_products),
            gaps=gaps[:8],
        ),
        reviewFunnel=review_funnel,
        contentMix=content_mix,
        riskBreakdown=risk_breakdown,
        recommendedActions=recommended_actions,
        generatedAt=now_iso(),
    )


def _has_strong_profile(product: Product) -> bool:
    return (
        len(product.sellingPoints) >= 2
        and len(product.usageScenarios) >= 1
        and len(product.forbiddenClaims) >= 1
    )


def _build_product_gaps(products: list[Product], usable_feedback_product_ids: set[str]) -> list[BusinessProductGap]:
    gaps: list[BusinessProductGap] = []
    for product in products:
        if product.id not in usable_feedback_product_ids:
            gaps.append(
                BusinessProductGap(
                    productId=product.id,
                    productName=product.name,
                    category=product.category,
                    gap="missing_feedback",
                    detail="缺少已授权或不需授权的真实反馈，体验类内容会被降级为安全替代话术。",
                    nextActionHref=f"/feedback?productId={product.id}",
                )
            )
            continue
        if len(product.sellingPoints) < 2 or not product.usageScenarios:
            gaps.append(
                BusinessProductGap(
                    productId=product.id,
                    productName=product.name,
                    category=product.category,
                    gap="weak_product_profile",
                    detail="商品卖点或使用场景不足，生成内容会偏泛，需要补充可验证细节。",
                    nextActionHref=f"/products?productId={product.id}",
                )
            )
            continue
        if not product.forbiddenClaims:
            gaps.append(
                BusinessProductGap(
                    productId=product.id,
                    productName=product.name,
                    category=product.category,
                    gap="missing_forbidden_claims",
                    detail="未配置禁用表达，风险检查缺少商品级边界。",
                    nextActionHref=f"/products?productId={product.id}",
                )
            )
    return gaps


def _build_review_funnel(contents: list[GeneratedContent]) -> BusinessReviewFunnel:
    status_counts = Counter(content.reviewStatus for content in contents)
    approved = status_counts["approved"]
    rejected = status_counts["rejected"]
    exportable = sum(
        1
        for content in contents
        if content.reviewStatus == "approved"
        and content.score >= 70
        and not content.riskFlags
    )
    return BusinessReviewFunnel(
        pending=status_counts["pending"],
        approved=approved,
        rejected=rejected,
        rewriting=status_counts["rewriting"],
        exportable=exportable,
        approvalRate=_percent(approved, approved + rejected),
    )


def _build_content_mix(tasks: list[GenerationTask], contents: list[GeneratedContent]) -> list[BusinessContentMixItem]:
    task_by_id = {task.id: task for task in tasks}
    counts: Counter[str] = Counter()
    for content in contents:
        task = task_by_id.get(content.taskId)
        if task:
            counts[task.config.contentType] += 1
    total = sum(counts.values())
    return [
        BusinessContentMixItem(
            contentType=content_type,
            label=CONTENT_TYPE_LABELS.get(content_type, content_type),
            count=count,
            share=_percent(count, total),
        )
        for content_type, count in counts.most_common()
    ]


def _build_risk_breakdown(contents: list[GeneratedContent]) -> list[BusinessRiskBreakdownItem]:
    counts: Counter[str] = Counter(flag for content in contents for flag in content.riskFlags)
    items: list[BusinessRiskBreakdownItem] = []
    for flag, count in counts.most_common(8):
        label, level, action = RISK_FLAG_GUIDANCE.get(
            flag,
            ("未分类风险", "warning", "进入审核中心核对来源依据、平台规则和禁用表达。"),
        )
        items.append(
            BusinessRiskBreakdownItem(
                flag=flag,
                label=label,
                count=count,
                level=level,
                action=action,
            )
        )
    return items


def _build_recommended_actions(
    *,
    products: list[Product],
    gaps: list[BusinessProductGap],
    review_funnel: BusinessReviewFunnel,
    risk_breakdown: list[BusinessRiskBreakdownItem],
    contents: list[GeneratedContent],
) -> list[BusinessRecommendedAction]:
    actions: list[BusinessRecommendedAction] = []
    if not products:
        actions.append(
            BusinessRecommendedAction(
                key="create_product",
                label="先录入商品资料",
                detail="至少补齐商品卖点、使用场景和禁用表达，生成结果才有事实边界。",
                priority=10,
                href="/products",
                tone="primary",
            )
        )
    missing_feedback_count = sum(1 for gap in gaps if gap.gap == "missing_feedback")
    if missing_feedback_count:
        actions.append(
            BusinessRecommendedAction(
                key="record_feedback",
                label="补充真实反馈",
                detail=f"{missing_feedback_count} 个商品缺少可用反馈，优先录入客服回访或客户授权摘要。",
                priority=20,
                href="/feedback",
                tone="warning",
            )
        )
    if review_funnel.pending:
        actions.append(
            BusinessRecommendedAction(
                key="review_pending",
                label="处理待审核素材",
                detail=f"{review_funnel.pending} 条内容等待人工确认，通过后才能进入导出素材池。",
                priority=30,
                href="/review",
                tone="primary",
            )
        )
    critical_risk_count = sum(item.count for item in risk_breakdown if item.level == "critical")
    if critical_risk_count:
        actions.append(
            BusinessRecommendedAction(
                key="fix_critical_risks",
                label="收敛高风险表达",
                detail=f"发现 {critical_risk_count} 个高风险标记，建议先核对禁用词和平台规则。",
                priority=35,
                href="/review",
                tone="warning",
            )
        )
    if review_funnel.exportable:
        actions.append(
            BusinessRecommendedAction(
                key="export_ready",
                label="导出通过素材",
                detail=f"{review_funnel.exportable} 条已通过且无风险标记的内容可用于运营素材包。",
                priority=40,
                href="/review",
                tone="success",
            )
        )
    if products and not contents:
        actions.append(
            BusinessRecommendedAction(
                key="generate_safe_use_cases",
                label="生成首批安全场景素材",
                detail="建议从评价邀请、客服回访、推荐语和详情页口碑开始验证业务闭环。",
                priority=45,
                href="/generate",
                tone="primary",
            )
        )
    if not actions:
        actions.append(
            BusinessRecommendedAction(
                key="scale_batch",
                label="扩展下一批商品",
                detail="当前内容素材状态健康，可以继续扩充商品和反馈，服务跨平台上架与热款优化。",
                priority=90,
                href="/products",
                tone="neutral",
            )
        )
    return sorted(actions, key=lambda item: item.priority)[:5]


def _percent(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        return 0
    return round((numerator / denominator) * 100)

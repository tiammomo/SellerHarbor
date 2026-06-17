from __future__ import annotations

import os
from collections import defaultdict

from app.models.schemas import (
    Feedback,
    GeneratedContent,
    GenerationTask,
    ProductCollectionStep,
    ProductMarketSource,
    Product,
    ProductOpportunityReport,
    ProductOpportunitySignal,
    ProductResearchProvider,
    ProductValidationCheck,
    ProductVisual,
)


def all_research_providers() -> list[ProductResearchProvider]:
    providers = [
        _provider(
            id="ebay_browse_api",
            name="eBay Browse API",
            channel="marketplace",
            priority=1,
            integration_mode="official_api",
            pricing_hint="官方开发者计划可免费加入，适合先做系统拉取",
            best_for=["跨境现货商品", "价格带", "商品图", "卖点关键词", "来源链接"],
            core_signals=["标题", "价格", "商品图", "类目", "卖家/刊登信息"],
            limitations=["默认更偏 eBay 现有供给，不代表 Amazon/TikTok 真实需求", "需要开发者 Key"],
            setup_actions=["配置 EBAY_CLIENT_ID/EBAY_CLIENT_SECRET", "按关键词和目标站点拉 item_summary", "把商品图和来源链接落入选品池"],
            credential_env_vars=["EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET"],
            collection_modes=["official_api", "manual_input"],
            automation_level="high",
            data_quality="high",
            image_support="product_image",
            free_tier=True,
            contribution_summary="自动化程度高，能直接贡献真实商品图、标题、价格、链接和类目，是第一阶段最值得接的免费商品源。",
            contribution_fields=["imageUrl", "sourceUrl", "price", "currency", "marketplace", "sourceProductId", "category"],
            collection_notes=["适合系统按关键词批量拉取候选品", "价格和图片质量高，但销量/需求需再用趋势源交叉验证"],
        ),
        _provider(
            id="bestbuy_api",
            name="Best Buy Product API",
            channel="retail_api",
            priority=1,
            integration_mode="official_api",
            pricing_hint="官方 API，适合电子、家电、数码类免费验证",
            best_for=["电子产品", "小家电", "规格参数", "价格库存", "商品图"],
            core_signals=["价格", "库存", "规格", "描述", "商品图"],
            limitations=["类目偏美国 BestBuy，不覆盖泛跨境全品类", "需要 API Key"],
            setup_actions=["配置 BESTBUY_API_KEY", "按类目/关键词拉商品列表", "用规格和价格补齐商品属性"],
            credential_env_vars=["BESTBUY_API_KEY"],
            collection_modes=["official_api", "manual_input"],
            automation_level="high",
            data_quality="high",
            image_support="product_image",
            free_tier=True,
            contribution_summary="对家电/数码类贡献很强：自动化拉取多、结构化程度高、商品图片和规格可信。",
            contribution_fields=["imageUrl", "price", "availability", "specifications", "description", "sourceUrl"],
            collection_notes=["适合厨房电器、健康设备、数码配件", "不适合服饰、美妆、食品等长尾类目"],
        ),
        _provider(
            id="etsy_open_api",
            name="Etsy Open API",
            channel="marketplace",
            priority=2,
            integration_mode="official_api",
            pricing_hint="官方 API，适合设计感商品和礼品方向",
            best_for=["家居装饰", "礼品", "饰品", "手作风格", "审美趋势"],
            core_signals=["Listing 标题", "价格", "图片", "标签", "店铺线索"],
            limitations=["偏手作/设计感，不适合标准化工业品判断销量", "需要开发者应用"],
            setup_actions=["配置 ETSY_API_KEY", "按关键词拉 active listings", "提取主图、标签和价格带"],
            credential_env_vars=["ETSY_API_KEY"],
            collection_modes=["official_api", "manual_input"],
            automation_level="high",
            data_quality="medium",
            image_support="product_image",
            free_tier=True,
            contribution_summary="能自动补商品图、标题、价格和标签，适合判断审美、礼品化和差异化方向。",
            contribution_fields=["imageUrl", "tags", "price", "shop", "sourceUrl", "styleKeywords"],
            collection_notes=["适合家居、服饰配饰、节日礼品", "销量信号要谨慎，只作为审美/供给参考"],
        ),
        _provider(
            id="open_food_facts",
            name="Open Food Facts",
            channel="open_data",
            priority=2,
            integration_mode="official_api",
            pricing_hint="开放数据，适合食品饮料类免费补图和资料",
            best_for=["食品饮料", "配料", "营养信息", "包装图", "条码"],
            core_signals=["商品包装图", "配料", "营养表", "品牌", "条码"],
            limitations=["覆盖取决于社区贡献，跨境新品可能缺数据", "不提供电商销量"],
            setup_actions=["按条码或关键词查询", "把包装图、配料和禁用表达风险写入商品资料"],
            collection_modes=["official_api", "manual_input"],
            automation_level="medium",
            data_quality="medium",
            image_support="product_image",
            free_tier=True,
            contribution_summary="食品类很有价值：能贡献包装图、配料和营养信息，可直接提升合规审核质量。",
            contribution_fields=["imageUrl", "ingredients", "nutrition", "brand", "barcode"],
            collection_notes=["适合食品饮料和健康零食", "需要人工复核配料翻译和合规表达"],
        ),
        _provider(
            id="google_trends",
            name="Google Trends",
            channel="trend",
            priority=2,
            integration_mode="public_page_capture",
            pricing_hint="官方免费趋势工具，适合人工/半自动验证需求走势",
            best_for=["关键词趋势", "地区热度", "季节性", "搜索增长"],
            core_signals=["搜索兴趣", "地区", "时间趋势", "相关查询"],
            limitations=["不是电商成交数据", "官方 API 权限有限，早期建议人工录入/截图归档"],
            setup_actions=["录入目标关键词", "人工导入趋势指数和地区", "与商品图/价格源交叉验证"],
            collection_modes=["manual_input", "public_page_capture"],
            automation_level="low",
            data_quality="high",
            image_support="none",
            free_tier=True,
            contribution_summary="数据质量高，但自动化低。主要贡献需求趋势和季节性，不能贡献商品图。",
            contribution_fields=["keywordTrend", "regionInterest", "seasonality", "relatedQueries"],
            collection_notes=["适合人工录入趋势指数", "不作为单独选品依据，要配合商品源和内容源"],
        ),
        _provider(
            id="pinterest_trends",
            name="Pinterest Trends",
            channel="trend",
            priority=2,
            integration_mode="public_page_capture",
            pricing_hint="官方免费趋势工具，适合审美和生活方式类目",
            best_for=["家居", "服饰", "美妆", "礼品", "生活方式趋势"],
            core_signals=["搜索趋势", "保存趋势", "购物趋势", "人群兴趣"],
            limitations=["地区覆盖和登录状态会影响可见数据", "自动接口有限"],
            setup_actions=["人工导入关键词趋势", "记录热门视觉方向", "用于指导图片和内容角度"],
            collection_modes=["manual_input", "public_page_capture"],
            automation_level="low",
            data_quality="medium",
            image_support="creative_image",
            free_tier=True,
            contribution_summary="适合贡献审美趋势和视觉方向，自动化低，但对图片风格和内容角度很有帮助。",
            contribution_fields=["visualTrend", "seasonality", "audienceInterest", "relatedKeywords"],
            collection_notes=["适合家居、美妆、服饰、礼品", "更像趋势雷达，不是商品库"],
        ),
        _provider(
            id="pexels_api",
            name="Pexels API",
            channel="image",
            priority=3,
            integration_mode="official_api",
            pricing_hint="免费图片/视频 API，适合做无真实图时的场景图兜底",
            best_for=["场景图", "内容封面", "素材占位", "视觉氛围"],
            core_signals=["免费图片", "视频素材", "摄影师信息", "授权说明"],
            limitations=["不是真实商品图，不能当市场证据", "需要 PEXELS_API_KEY"],
            setup_actions=["配置 PEXELS_API_KEY", "按商品关键词/场景拉图片", "标记为 scene_fallback"],
            credential_env_vars=["PEXELS_API_KEY"],
            collection_modes=["official_api", "fallback_image"],
            automation_level="high",
            data_quality="low",
            image_support="scene_image",
            free_tier=True,
            contribution_summary="自动化高、图片多，但只适合作为场景兜底图，不能代表真实商品和销量。",
            contribution_fields=["imageUrl", "photographer", "licenseNote", "sceneKeyword"],
            collection_notes=["仅在商品没有真实图时使用", "前端必须标注为场景兜底图"],
        ),
        _provider(
            id="pixabay_api",
            name="Pixabay API",
            channel="image",
            priority=3,
            integration_mode="official_api",
            pricing_hint="免费图片/视频 API，适合补充素材图",
            best_for=["素材图", "场景图", "短视频封面", "低成本占位"],
            core_signals=["图片", "视频", "标签", "授权说明"],
            limitations=["不是真实商品图", "关键词匹配可能偏泛化"],
            setup_actions=["配置 PIXABAY_API_KEY", "按商品/类目关键词拉图", "与真实商品图区分展示"],
            credential_env_vars=["PIXABAY_API_KEY"],
            collection_modes=["official_api", "fallback_image"],
            automation_level="high",
            data_quality="low",
            image_support="scene_image",
            free_tier=True,
            contribution_summary="自动化高、素材覆盖广，适合兜底视觉展示，不参与市场需求高权重评分。",
            contribution_fields=["imageUrl", "tags", "licenseNote", "sceneKeyword"],
            collection_notes=["只做视觉兜底", "不能作为商品证据或供应链证据"],
        ),
        _provider(
            id="amazon_best_sellers",
            name="Amazon Best Sellers",
            channel="amazon",
            priority=3,
            integration_mode="public_page_capture",
            pricing_hint="公开榜单免费查看，建议人工导入/URL 归档",
            best_for=["榜单排名", "类目热销", "商品图", "价格评分", "Review 数"],
            core_signals=["榜单排名", "价格", "评分", "Review 数", "商品图"],
            limitations=["无免费官方榜单 API", "自动抓取需严格遵守站点条款，推荐人工导入 URL/CSV"],
            setup_actions=["人工复制榜单 URL 或导入 CSV", "记录排名、图片、价格和 Review 数", "用 Keepa/SellerSprite 复核"],
            collection_modes=["manual_input", "csv_import", "public_page_capture"],
            automation_level="low",
            data_quality="high",
            image_support="product_image",
            free_tier=True,
            contribution_summary="质量高但自动化低。适合人工导入热销榜单证据，不建议无节制抓取。",
            contribution_fields=["rank", "imageUrl", "price", "rating", "reviewCount", "sourceUrl"],
            collection_notes=["优先人工 URL/CSV 导入", "自动化时要做频控和合规检查"],
        ),
        _provider(
            id="seller_sprite",
            name="SellerSprite 卖家精灵",
            channel="amazon",
            priority=1,
            integration_mode="api_or_export",
            pricing_hint="付费，适合国内团队长期使用",
            best_for=["Amazon 关键词需求", "竞品数量", "类目机会", "Listing 优化"],
            core_signals=["关键词搜索量", "BSR/销量估算", "Review gap", "价格带", "竞品集中度"],
            limitations=["第三方估算需用 Amazon 一方数据交叉验证", "需要账号或导出权限"],
            setup_actions=["配置 SELLERSPRITE_API_KEY 或导入 CSV", "建立关键词与商品类目的映射"],
            credential_env_vars=["SELLERSPRITE_API_KEY"],
        ),
        _provider(
            id="helium10",
            name="Helium 10 Black Box",
            channel="amazon",
            priority=2,
            integration_mode="api_or_export",
            pricing_hint="付费，适合 Amazon/Walmart 多市场研究",
            best_for=["Amazon 产品库筛选", "关键词反查", "市场容量验证"],
            core_signals=["月销估算", "搜索量", "竞品 ASIN", "关键词机会", "广告竞争"],
            limitations=["与 SellerSprite 信号有重叠", "API 能力取决于订阅计划"],
            setup_actions=["配置 HELIUM10_API_KEY 或导入 Black Box 导出", "与 Keepa 历史曲线交叉校验"],
            credential_env_vars=["HELIUM10_API_KEY"],
        ),
        _provider(
            id="keepa",
            name="Keepa",
            channel="amazon",
            priority=3,
            integration_mode="api_or_export",
            pricing_hint="低成本付费，适合做价格/BSR 历史验证",
            best_for=["价格历史", "BSR 波动", "季节性", "短期爆款排雷"],
            core_signals=["价格曲线", "BSR 曲线", "库存/卖家变化", "促销波动"],
            limitations=["不直接给内容热度", "需要和关键词/竞品工具组合使用"],
            setup_actions=["配置 KEEPA_API_KEY", "为 Amazon 候选品建立 ASIN 观察列表"],
            credential_env_vars=["KEEPA_API_KEY"],
        ),
        _provider(
            id="amazon_opportunity_explorer",
            name="Amazon Product Opportunity Explorer",
            channel="amazon",
            priority=4,
            integration_mode="official_manual",
            pricing_hint="Seller Central 内置，通常免费",
            best_for=["一方客户搜索行为", "需求缺口", "价格预期", "新品方向验证"],
            core_signals=["搜索趋势", "Top clicked products", "价格区间", "客户需求"],
            limitations=["需要 Amazon Seller Central 权限", "自动化接入受平台权限限制"],
            setup_actions=["从 Seller Central 导出机会报告", "作为 Amazon 候选品的一方数据复核"],
        ),
        _provider(
            id="kalodata",
            name="Kalodata",
            channel="tiktok_shop",
            priority=1,
            integration_mode="api_or_export",
            pricing_hint="付费，适合 TikTok Shop 团队",
            best_for=["TikTok Shop 热销商品", "达人带货", "视频/直播趋势", "竞品店铺"],
            core_signals=["GMV/销量趋势", "达人数量", "带货视频", "直播间表现", "市场站点"],
            limitations=["偏 TikTok Shop，不能替代供应链验证", "数据口径依赖平台公开信息"],
            setup_actions=["配置 KALODATA_API_KEY 或导入商品榜单", "按站点建立类目机会池"],
            credential_env_vars=["KALODATA_API_KEY"],
        ),
        _provider(
            id="tiktok_creative_center",
            name="TikTok Creative Center Top Products",
            channel="tiktok_ads",
            priority=2,
            integration_mode="official_free",
            pricing_hint="官方免费，适合早期验证",
            best_for=["TikTok 广告趋势", "地区/类目热度", "素材方向"],
            core_signals=["Top Products", "地区", "类目", "时间窗口", "广告创意"],
            limitations=["更偏广告侧，不等同于成交数据", "自动化接口有限"],
            setup_actions=["按目标市场定期人工/半自动采集", "把产品热度映射到内容角度"],
        ),
        _provider(
            id="pipiads",
            name="PiPiADS",
            channel="ads",
            priority=3,
            integration_mode="api_or_export",
            pricing_hint="付费，适合 TikTok/Facebook 广告 spy",
            best_for=["爆款广告素材", "Hook/脚本角度", "竞品投放观察"],
            core_signals=["广告素材", "互动", "投放时长", "落地页", "TikTok Shop 线索"],
            limitations=["广告跑得久不代表履约好", "需要结合评价痛点和供应链"],
            setup_actions=["配置 PIPIADS_API_KEY 或导入收藏夹", "沉淀可复用素材角度"],
            credential_env_vars=["PIPIADS_API_KEY"],
        ),
        _provider(
            id="minea",
            name="Minea",
            channel="independent",
            priority=4,
            integration_mode="api_or_export",
            pricing_hint="付费，适合 DTC/独立站和多渠道广告研究",
            best_for=["Meta/TikTok/Pinterest 广告", "Shopify 店铺观察", "DTC 创意验证"],
            core_signals=["广告渠道", "素材类型", "投放持续时间", "店铺线索", "视觉搜索"],
            limitations=["销量估算只能作方向信号", "要警惕同质化跟卖"],
            setup_actions=["配置 MINEA_API_KEY 或导入广告集合", "为独立站候选品建立素材库"],
            credential_env_vars=["MINEA_API_KEY"],
        ),
        _provider(
            id="dropship_io",
            name="Dropship.io",
            channel="independent",
            priority=5,
            integration_mode="api_or_export",
            pricing_hint="付费，适合 Shopify/Dropshipping 方向",
            best_for=["Shopify 商品库", "竞品店铺", "销售追踪", "TikTok Shop 商品库"],
            core_signals=["商品库", "店铺估算", "销量趋势", "竞品商品", "导入 Shopify"],
            limitations=["店铺销量估算可能被反爬/保护工具影响", "不能替代样品和利润核算"],
            setup_actions=["配置 DROPSHIP_IO_API_KEY 或导入商品库", "只把销售估算作为二级信号"],
            credential_env_vars=["DROPSHIP_IO_API_KEY"],
        ),
    ]
    return sorted(providers, key=lambda item: (item.priority, item.name))


def build_opportunity_reports(
    products: list[Product],
    feedbacks: list[Feedback],
    tasks: list[GenerationTask],
    contents: list[GeneratedContent],
) -> list[ProductOpportunityReport]:
    feedback_by_product: dict[str, list[Feedback]] = defaultdict(list)
    for feedback in feedbacks:
        feedback_by_product[feedback.productId].append(feedback)

    task_ids_by_product: dict[str, set[str]] = defaultdict(set)
    for task in tasks:
        task_ids_by_product[task.productId].add(task.id)

    contents_by_product: dict[str, list[GeneratedContent]] = defaultdict(list)
    for content in contents:
        for product_id, task_ids in task_ids_by_product.items():
            if content.taskId in task_ids:
                contents_by_product[product_id].append(content)
                break

    reports = [
        build_opportunity_report(
            product=product,
            feedbacks=feedback_by_product[product.id],
            contents=contents_by_product[product.id],
        )
        for product in products
    ]
    return sorted(reports, key=lambda item: item.score, reverse=True)


def build_opportunity_report(
    product: Product,
    feedbacks: list[Feedback],
    contents: list[GeneratedContent],
) -> ProductOpportunityReport:
    completeness = _completeness(product)
    evidence = min(100, len(feedbacks) * 34)
    avg_content_score = _avg([content.score for content in contents]) or 70
    approved_count = len([content for content in contents if content.reviewStatus == "approved"])
    risk_count = len([content for content in contents if content.riskFlags])
    category_fit = _category_fit(product)
    differentiation = _differentiation_score(product)
    margin = _margin_score(product)
    ops = _ops_score(product)
    content_fit = min(100, avg_content_score * 0.7 + approved_count * 10 + len(product.usageScenarios) * 4)
    risk_penalty = _risk_penalty(product, risk_count)

    signals = [
        _signal(
            "demand_proxy",
            "需求潜力",
            f"{category_fit} / 100",
            category_fit,
            "provider.seller_sprite|provider.kalodata|internal.category",
            0.26,
            "由类目跨境适配、平台可传播性和可外部验证程度估算。",
        ),
        _signal(
            "content_fit",
            "内容传播适配",
            f"{round(content_fit)} / 100",
            round(content_fit),
            "provider.tiktok_creative_center|sellerharbor.generated_content",
            0.20,
            "结合使用场景、已生成内容质量和可复用素材沉淀估算。",
        ),
        _signal(
            "evidence_depth",
            "真实反馈证据",
            f"{len(feedbacks)} 条",
            evidence,
            "sellerharbor.feedback",
            0.18,
            "口碑素材生成需要真实反馈支撑，反馈越多越适合扩展多平台内容。",
        ),
        _signal(
            "differentiation",
            "差异化",
            product.attributes.get("竞品差异", "待补竞品差异"),
            differentiation,
            "internal.product_attributes",
            0.16,
            "优先选择有明确功能、材质、场景或竞品差异的商品。",
        ),
        _signal(
            "margin_proxy",
            "毛利空间代理",
            product.attributes.get("价格带", "待补价格带"),
            margin,
            "internal.price_band",
            0.12,
            "用价格带和类目履约复杂度粗略判断是否值得进入深度测算。",
        ),
        _signal(
            "ops_readiness",
            "履约准备度",
            product.attributes.get("库存状态", "待补库存状态"),
            ops,
            "internal.ops",
            0.08,
            "库存、禁用表达和基础资料影响上线速度和合规风险。",
        ),
    ]
    score = _clamp(round(sum(signal.score * signal.weight for signal in signals) - risk_penalty))
    confidence = _clamp(round(completeness * 0.38 + evidence * 0.24 + min(100, len(contents) * 20) * 0.14 + _external_coverage(product) * 0.24))
    providers = _recommended_provider_ids(product)
    checks = _validation_checks(product, feedbacks, contents, providers)
    risk_flags = _risk_flags(product, risk_count, confidence)
    level = "launch_candidate" if score >= 78 and confidence >= 62 else "validate_more" if score >= 58 else "needs_data"
    visual = _product_visual(product, providers)
    market_sources = _market_sources(product, providers, visual)

    return ProductOpportunityReport(
        productId=product.id,
        productName=product.name,
        category=product.category,
        visual=visual,
        score=score,
        confidence=confidence,
        level=level,
        recommendedProviders=providers,
        marketSources=market_sources,
        collectionPlan=_collection_plan(product, providers, visual),
        signals=signals,
        checks=checks,
        nextActions=_next_actions(level, providers, checks, risk_flags),
        riskFlags=risk_flags,
        sourceTrace=[
            "sellerharbor.product",
            "sellerharbor.feedback",
            "sellerharbor.generated_content",
            *[f"provider.{provider_id}" for provider_id in providers],
        ],
    )


def _provider(
    *,
    id: str,
    name: str,
    channel: str,
    priority: int,
    integration_mode: str,
    pricing_hint: str,
    best_for: list[str],
    core_signals: list[str],
    limitations: list[str],
    setup_actions: list[str],
    credential_env_vars: list[str] | None = None,
    collection_modes: list[str] | None = None,
    automation_level: str | None = None,
    data_quality: str | None = None,
    image_support: str = "none",
    free_tier: bool = False,
    contribution_summary: str | None = None,
    contribution_fields: list[str] | None = None,
    collection_notes: list[str] | None = None,
) -> ProductResearchProvider:
    credential_env_vars = credential_env_vars or []
    collection_modes = collection_modes or _default_collection_modes(integration_mode)
    automation_level = automation_level or _default_automation_level(integration_mode)
    data_quality = data_quality or ("high" if integration_mode.startswith("official") else "medium")
    return ProductResearchProvider(
        id=id,
        name=name,
        channel=channel,
        priority=priority,
        integrationMode=integration_mode,
        pricingHint=pricing_hint,
        bestFor=best_for,
        coreSignals=core_signals,
        limitations=limitations,
        setupActions=setup_actions,
        credentialEnvVars=credential_env_vars,
        enabled=any(os.getenv(name) for name in credential_env_vars) if credential_env_vars else True,
        collectionModes=collection_modes,
        automationLevel=automation_level,
        dataQuality=data_quality,
        imageSupport=image_support,
        freeTier=free_tier,
        contributionSummary=contribution_summary or f"主要贡献：{'、'.join(core_signals[:4])}。适合用于{'、'.join(best_for[:2])}。",
        contributionFields=contribution_fields or core_signals,
        collectionNotes=collection_notes or setup_actions,
    )


def _default_collection_modes(integration_mode: str) -> list[str]:
    if integration_mode == "official_api":
        return ["official_api", "manual_input"]
    if integration_mode == "api_or_export":
        return ["official_api", "csv_import", "manual_input"]
    if integration_mode == "official_manual":
        return ["manual_input", "csv_import"]
    if integration_mode == "public_page_capture":
        return ["manual_input", "public_page_capture"]
    if integration_mode == "official_free":
        return ["manual_input", "public_page_capture"]
    return ["manual_input"]


def _default_automation_level(integration_mode: str) -> str:
    if integration_mode == "official_api":
        return "high"
    if integration_mode == "api_or_export":
        return "medium"
    if integration_mode in {"official_manual", "public_page_capture", "official_free"}:
        return "low"
    return "medium"


def _product_visual(product: Product, providers: list[str]) -> ProductVisual:
    manual_image = _first_attr(product, ["商品图片URL", "图片URL", "imageUrl", "sourceImageUrl", "商品主图"])
    source_url = _first_attr(product, ["来源链接", "sourceUrl", "商品链接", "采集URL"])
    source_name = _first_attr(product, ["数据来源", "sourceName", "市场平台", "marketplace"]) or "人工录入"
    if manual_image:
        return ProductVisual(
            imageUrl=manual_image,
            imageSource=source_name,
            imageRole="product",
            licenseNote="人工录入或来源平台商品图，请确认授权与平台使用条款。",
            confidence=92,
            sourceUrl=source_url or None,
        )

    marketplace_provider = _first_provider(
        providers,
        ["ebay_browse_api", "bestbuy_api", "etsy_open_api", "open_food_facts", "amazon_best_sellers"],
    )
    if marketplace_provider:
        return ProductVisual(
            imageUrl=_fallback_image(product),
            imageSource=_provider_name(marketplace_provider),
            imageRole="marketplace",
            licenseNote="系统建议从该来源拉取真实商品图；当前先展示免费场景兜底图，接入后替换。",
            confidence=68,
            sourceUrl=source_url or _provider_source_url(marketplace_provider),
        )

    image_provider = _first_provider(providers, ["pexels_api", "pixabay_api"])
    return ProductVisual(
        imageUrl=_fallback_image(product),
        imageSource=_provider_name(image_provider or "fallback_visual"),
        imageRole="scene_fallback",
        licenseNote="免费图库场景图，仅用于视觉占位，不作为真实商品、销量或供应链证据。",
        confidence=42,
        sourceUrl=_provider_source_url(image_provider or "pexels_api"),
    )


def _market_sources(product: Product, providers: list[str], visual: ProductVisual) -> list[ProductMarketSource]:
    provider_by_id = {provider.id: provider for provider in all_research_providers()}
    source_url = _first_attr(product, ["来源链接", "sourceUrl", "商品链接", "采集URL"])
    sources: list[ProductMarketSource] = []
    for provider_id in providers:
        provider = provider_by_id.get(provider_id)
        if not provider:
            continue
        status = _source_status(provider, visual)
        source = ProductMarketSource(
            providerId=provider.id,
            providerName=provider.name,
            collectionMode=_primary_collection_mode(provider),
            automationLevel=provider.automationLevel,
            dataQuality=provider.dataQuality,
            imageSupport=provider.imageSupport,
            freeTier=provider.freeTier,
            status=status,
            contributionScore=_contribution_score(provider, product, status),
            fields=provider.contributionFields,
            explanation=_source_explanation(provider, status),
            actionLabel=_source_action_label(provider, status),
            sourceUrl=source_url if status == "manual" else _provider_source_url(provider.id),
        )
        sources.append(source)
    return sorted(sources, key=lambda item: item.contributionScore, reverse=True)


def _collection_plan(product: Product, providers: list[str], visual: ProductVisual) -> list[ProductCollectionStep]:
    steps = [
        ProductCollectionStep(
            key="manual_seed",
            label="人工录入基础证据",
            mode="manual_input",
            priority=1,
            providerIds=["sellerharbor.product"],
            expectedFields=["商品图", "来源链接", "价格", "币种", "竞品差异", "库存状态"],
            qualityImpact="先补真实商品图和来源链接，能显著提升图片可信度和报告置信度。",
            automationHint="适合商家先把已有店铺链接、1688/供应链链接或竞品 URL 填进来。",
        ),
    ]
    if any(provider in providers for provider in ["ebay_browse_api", "bestbuy_api", "etsy_open_api", "open_food_facts"]):
        steps.append(
            ProductCollectionStep(
                key="official_api_fetch",
                label="官方 API 系统拉取",
                mode="official_api",
                priority=2,
                providerIds=[provider for provider in providers if provider in {"ebay_browse_api", "bestbuy_api", "etsy_open_api", "open_food_facts"}],
                expectedFields=["商品图", "标题", "价格", "类目", "规格", "来源链接"],
                qualityImpact="自动化程度高、结构化强，是后续批量选品的数据底座。",
                automationHint="配置对应 API Key 后按关键词/类目定时拉取候选品。",
            )
        )
    if any(provider in providers for provider in ["google_trends", "pinterest_trends", "tiktok_creative_center", "amazon_best_sellers"]):
        steps.append(
            ProductCollectionStep(
                key="public_trend_capture",
                label="公开页面半自动采集",
                mode="public_page_capture",
                priority=3,
                providerIds=[provider for provider in providers if provider in {"google_trends", "pinterest_trends", "tiktok_creative_center", "amazon_best_sellers"}],
                expectedFields=["趋势指数", "地区", "时间窗口", "榜单排名", "素材截图/链接"],
                qualityImpact="质量高但自动化有限，适合人工复核后作为机会分加权证据。",
                automationHint="先支持手动录入和 CSV，再做低频、合规、带来源归档的采集。",
            )
        )
    if visual.imageRole == "scene_fallback" or any(provider in providers for provider in ["pexels_api", "pixabay_api"]):
        steps.append(
            ProductCollectionStep(
                key="fallback_visual",
                label="免费图库补场景图",
                mode="fallback_image",
                priority=4,
                providerIds=[provider for provider in providers if provider in {"pexels_api", "pixabay_api"}] or ["pexels_api", "pixabay_api"],
                expectedFields=["场景图", "授权说明", "图片来源"],
                qualityImpact="只提升页面可读性和内容视觉参考，不提升真实商品证据分。",
                automationHint="没有真实商品图时自动按类目/场景关键词拉取，并在前端标注为兜底图。",
            )
        )
    return steps


def _signal(
    key: str,
    label: str,
    value: str,
    score: int,
    source: str,
    weight: float,
    explanation: str,
) -> ProductOpportunitySignal:
    return ProductOpportunitySignal(
        key=key,
        label=label,
        value=value,
        score=_clamp(score),
        source=source,
        weight=weight,
        explanation=explanation,
    )


def _validation_checks(
    product: Product,
    feedbacks: list[Feedback],
    contents: list[GeneratedContent],
    providers: list[str],
) -> list[ProductValidationCheck]:
    checks = [
        _check(
            "product_assets",
            "商品资料完整",
            "passed" if _completeness(product) >= 75 else "watch",
            "卖点、人群、场景、禁用表达会影响自动生成质量。",
            "sellerharbor.product",
        ),
        _check(
            "review_evidence",
            "真实反馈证据",
            "passed" if feedbacks else "missing",
            "至少需要 1 条真实反馈，才能安全生成第一人称体验内容。",
            "sellerharbor.feedback",
        ),
        _check(
            "amazon_keyword_validation",
            "Amazon 关键词/竞品验证",
            "missing" if "seller_sprite" in providers else "watch",
            "用 SellerSprite 或 Helium 10 拉搜索量、竞品数量、Review gap。",
            "provider.seller_sprite|provider.helium10",
        ),
        _check(
            "price_bsr_history",
            "价格与 BSR 历史",
            "missing" if "keepa" in providers else "watch",
            "用 Keepa 排除短期促销、季节性和异常 BSR 波动。",
            "provider.keepa",
        ),
        _check(
            "tiktok_content_validation",
            "TikTok 素材热度",
            "missing" if any(provider in providers for provider in ["kalodata", "pipiads", "tiktok_creative_center"]) else "watch",
            "用 Kalodata、TikTok Creative Center、PiPiADS 检查内容和达人信号。",
            "provider.kalodata|provider.pipiads|provider.tiktok_creative_center",
        ),
        _check(
            "approved_content",
            "已沉淀可用口碑",
            "passed" if any(content.reviewStatus == "approved" for content in contents) else "watch",
            "通过审核的内容越多，越适合进入批量生成和多平台改写。",
            "sellerharbor.generated_content",
        ),
    ]
    return checks


def _check(key: str, label: str, status: str, detail: str, source: str) -> ProductValidationCheck:
    return ProductValidationCheck(key=key, label=label, status=status, detail=detail, source=source)


def _recommended_provider_ids(product: Product) -> list[str]:
    category = product.category
    explicit_platforms = product.attributes.get("主推平台", "")
    providers: list[str] = []

    providers.append("ebay_browse_api")

    if any(keyword in category for keyword in ["厨房", "家居", "健康", "电器", "数码"]):
        providers.append("bestbuy_api")

    if any(keyword in category for keyword in ["家居", "家纺", "服饰", "礼品", "饰品", "美妆"]):
        providers.append("etsy_open_api")

    if any(keyword in category for keyword in ["食品", "饮料", "零食"]):
        providers.append("open_food_facts")

    providers.append("google_trends")

    if any(keyword in category for keyword in ["家居", "家纺", "美妆", "服饰", "母婴", "礼品"]):
        providers.append("pinterest_trends")

    if any(keyword in category for keyword in ["厨房", "家居", "家纺", "母婴", "健康", "食品", "美妆"]) or any(
        keyword in explicit_platforms for keyword in ["Amazon", "亚马逊", "京东", "天猫"]
    ):
        providers.extend(["amazon_best_sellers", "seller_sprite", "keepa", "amazon_opportunity_explorer"])

    if any(keyword in category for keyword in ["美妆", "食品", "服饰", "家居", "母婴", "厨房"]) or any(
        keyword in explicit_platforms for keyword in ["TikTok", "抖音", "小红书"]
    ):
        providers.extend(["kalodata", "tiktok_creative_center", "pipiads"])

    if any(keyword in category for keyword in ["服饰", "美妆", "家居", "食品"]) or any(
        keyword in explicit_platforms for keyword in ["独立站", "Shopify", "DTC"]
    ):
        providers.extend(["minea", "dropship_io"])

    if not _first_attr(product, ["商品图片URL", "图片URL", "imageUrl", "sourceImageUrl", "商品主图"]):
        providers.extend(["pexels_api", "pixabay_api"])

    return _unique(providers or ["ebay_browse_api", "google_trends", "pexels_api"])


def _category_fit(product: Product) -> int:
    category = product.category
    score = 55
    if any(keyword in category for keyword in ["厨房", "家居", "家纺"]):
        score += 18
    if any(keyword in category for keyword in ["美妆", "食品", "母婴", "服饰"]):
        score += 22
    if "健康" in category:
        score += 10
    if product.usageScenarios:
        score += min(12, len(product.usageScenarios) * 3)
    if product.targetAudiences:
        score += min(8, len(product.targetAudiences) * 2)
    return _clamp(score)


def _differentiation_score(product: Product) -> int:
    score = 42
    if product.attributes.get("竞品差异"):
        score += 24
    score += min(24, len(product.sellingPoints) * 5)
    if any(any(token in item for token in ["静音", "轻", "便携", "自清洗", "无添加", "防泼水", "亲肤"]) for item in product.sellingPoints):
        score += 10
    return _clamp(score)


def _margin_score(product: Product) -> int:
    price_band = product.attributes.get("价格带", "")
    base = 64
    if price_band in {"利润款", "高客单"}:
        base += 18
    if price_band == "主推款":
        base += 10
    if price_band == "引流款":
        base -= 8
    if any(keyword in product.category for keyword in ["易碎", "大件"]):
        base -= 16
    return _clamp(base)


def _ops_score(product: Product) -> int:
    score = 45
    inventory = product.attributes.get("库存状态", "")
    if inventory == "现货充足":
        score += 24
    elif inventory == "少量现货":
        score += 10
    elif inventory in {"预售", "清仓"}:
        score -= 10
    if product.forbiddenClaims:
        score += 14
    if product.attributes:
        score += min(12, len(product.attributes) * 2)
    return _clamp(score)


def _risk_penalty(product: Product, risk_count: int) -> int:
    penalty = risk_count * 8
    if any(keyword in product.category for keyword in ["健康", "食品", "母婴", "美妆"]):
        penalty += 6
    if not product.forbiddenClaims:
        penalty += 10
    return penalty


def _external_coverage(product: Product) -> int:
    return min(100, len(_recommended_provider_ids(product)) * 16)


def _risk_flags(product: Product, risk_count: int, confidence: int) -> list[str]:
    flags: list[str] = []
    if risk_count:
        flags.append("generated_content_risk_exists")
    if any(keyword in product.category for keyword in ["健康", "食品", "母婴", "美妆"]):
        flags.append("regulated_category_review_needed")
    if confidence < 55:
        flags.append("low_validation_confidence")
    if not product.forbiddenClaims:
        flags.append("missing_forbidden_claims")
    return flags


def _next_actions(level: str, providers: list[str], checks: list[ProductValidationCheck], risk_flags: list[str]) -> list[str]:
    actions: list[str] = []
    missing = [check for check in checks if check.status == "missing"]
    if missing:
        actions.append(f"先补齐 {missing[0].label}，避免把弱信号商品推入生成流程。")
    if "seller_sprite" in providers:
        actions.append("用 SellerSprite/Helium 10 拉关键词需求、竞品数量和 Review gap。")
    if "keepa" in providers:
        actions.append("用 Keepa 复核价格与 BSR 历史，排除短期促销造成的假机会。")
    if "kalodata" in providers:
        actions.append("用 Kalodata/TikTok Creative Center 检查 TikTok Shop 与内容素材热度。")
    if "minea" in providers:
        actions.append("用 Minea 或 Dropship.io 看独立站广告素材和竞品店铺走势。")
    if risk_flags:
        actions.append("先完成合规词、禁用表达和评价证据复核，再批量生成口碑素材。")
    if level == "launch_candidate":
        actions.append("可以进入小批量内容生成与多平台素材 A/B 验证。")
    return _unique(actions[:5])


def _completeness(product: Product) -> int:
    checks = [
        bool(product.name),
        bool(product.category),
        len(product.sellingPoints) >= 2,
        bool(product.targetAudiences),
        bool(product.usageScenarios),
        bool(product.forbiddenClaims),
        bool(product.attributes),
    ]
    return round(sum(1 for item in checks if item) / len(checks) * 100)


def _avg(values: list[int]) -> int:
    return round(sum(values) / len(values)) if values else 0


def _unique(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def _clamp(value: int | float) -> int:
    return max(0, min(100, round(value)))


def _first_attr(product: Product, keys: list[str]) -> str:
    for key in keys:
        value = product.attributes.get(key)
        if value and value.strip():
            return value.strip()
    return ""


def _first_provider(providers: list[str], candidates: list[str]) -> str:
    for candidate in candidates:
        if candidate in providers:
            return candidate
    return ""


def _provider_name(provider_id: str) -> str:
    if provider_id == "fallback_visual":
        return "免费图库兜底"
    for provider in all_research_providers():
        if provider.id == provider_id:
            return provider.name
    return provider_id


def _provider_source_url(provider_id: str) -> str:
    urls = {
        "ebay_browse_api": "https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search",
        "bestbuy_api": "https://bestbuyapis.github.io/api-documentation/",
        "etsy_open_api": "https://developers.etsy.com/",
        "open_food_facts": "https://openfoodfacts.github.io/openfoodfacts-server/api/",
        "google_trends": "https://trends.google.com/",
        "pinterest_trends": "https://trends.pinterest.com/",
        "pexels_api": "https://www.pexels.com/api/",
        "pixabay_api": "https://pixabay.com/api/docs/",
        "amazon_best_sellers": "https://www.amazon.com/Best-Sellers/zgbs",
        "tiktok_creative_center": "https://ads.tiktok.com/creative/creativeCenter",
        "seller_sprite": "https://www.sellersprite.com/",
        "helium10": "https://www.helium10.com/",
        "keepa": "https://keepa.com/",
        "amazon_opportunity_explorer": "https://sell.amazon.com/tools/product-opportunity-explorer",
        "kalodata": "https://www.kalodata.com/",
        "pipiads": "https://www.pipiads.com/",
        "minea": "https://www.minea.com/",
        "dropship_io": "https://www.dropship.io/",
    }
    return urls.get(provider_id, "")


def _fallback_image(product: Product) -> str:
    category = product.category
    if any(keyword in category for keyword in ["厨房", "电器"]):
        return "https://images.unsplash.com/photo-1556911220-bff31c812dba?auto=format&fit=crop&w=900&q=80"
    if any(keyword in category for keyword in ["家纺", "床品"]):
        return "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80"
    if any(keyword in category for keyword in ["家居", "日用"]):
        return "https://images.unsplash.com/photo-1513161455079-7dc1de15ef3e?auto=format&fit=crop&w=900&q=80"
    if "食品" in category or "饮料" in category:
        return "https://images.unsplash.com/photo-1504754524776-8f4f37790ca0f?auto=format&fit=crop&w=900&q=80"
    if "美妆" in category:
        return "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=900&q=80"
    if "服饰" in category:
        return "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?auto=format&fit=crop&w=900&q=80"
    if "健康" in category:
        return "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=900&q=80"
    if "母婴" in category:
        return "https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?auto=format&fit=crop&w=900&q=80"
    return "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80"


def _primary_collection_mode(provider: ProductResearchProvider) -> str:
    if provider.collectionModes:
        return provider.collectionModes[0]
    return "manual_input"


def _source_status(provider: ProductResearchProvider, visual: ProductVisual) -> str:
    if provider.id in {"pexels_api", "pixabay_api"} and visual.imageRole == "scene_fallback":
        return "fallback"
    if provider.credentialEnvVars and not provider.enabled:
        return "needs_key"
    if provider.automationLevel == "low":
        return "manual"
    return "ready"


def _contribution_score(provider: ProductResearchProvider, product: Product, status: str) -> int:
    score = {"high": 72, "medium": 58, "low": 38}[provider.dataQuality]
    score += {"high": 14, "medium": 8, "low": 2}[provider.automationLevel]
    if provider.imageSupport == "product_image":
        score += 10
    elif provider.imageSupport == "creative_image":
        score += 6
    elif provider.imageSupport == "scene_image":
        score -= 4
    if provider.freeTier:
        score += 4
    if status == "needs_key":
        score -= 16
    if status == "manual":
        score -= 8
    if provider.id == "open_food_facts" and not any(keyword in product.category for keyword in ["食品", "饮料"]):
        score -= 24
    return _clamp(score)


def _source_explanation(provider: ProductResearchProvider, status: str) -> str:
    status_note = {
        "ready": "当前适合系统自动拉取或接入。",
        "needs_key": "需要先配置 API Key，配置后可进入系统拉取。",
        "manual": "更适合人工录入、CSV 导入或低频页面归档。",
        "fallback": "仅用于无真实商品图时补视觉，不作为选品证据。",
    }[status]
    return f"{provider.contributionSummary} {status_note}"


def _source_action_label(provider: ProductResearchProvider, status: str) -> str:
    if status == "needs_key":
        return f"配置 {'/'.join(provider.credentialEnvVars)}"
    if status == "manual":
        return "人工录入或导入 CSV"
    if status == "fallback":
        return "作为兜底图展示"
    if provider.integrationMode == "official_api":
        return "接入官方 API 拉取"
    return "接入或导入数据"

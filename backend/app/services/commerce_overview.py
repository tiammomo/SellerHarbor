from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from app.db.repository import now_iso
from app.models.schemas import (
    BusinessRecommendedAction,
    CommerceHotProduct,
    CommerceInventoryAlert,
    CommerceKpi,
    CommerceOverview,
    CommercePlatform,
    CommercePlatformSummary,
    CommerceWarehouseSummary,
    Feedback,
    GeneratedContent,
    Product,
)


PLATFORMS: list[tuple[CommercePlatform, str]] = [
    ("temu", "Temu"),
    ("tiktok_shop", "TikTok Shop"),
]

WAREHOUSE_FALLBACKS = [
    ("us-west-la", "US-West LA 3PL", "US"),
    ("us-east-nj", "US-East NJ 3PL", "US"),
    ("uk-midlands", "UK Midlands 3PL", "UK"),
]

FALLBACK_STOCK = [18, 7, 42, 4, 29, 13]
FALLBACK_RESERVED = [2, 1, 8, 0, 5, 3]
FALLBACK_SALES = [32, 18, 24, 9, 14, 27]
READY_STATUSES = {"ready", "live", "active", "listed", "online", "published", "已上架", "在线", "可售"}
WATCH_STATUSES = {"draft", "reviewing", "blocked", "needs_fix", "low_inventory", "草稿", "审核中", "被拒", "待优化"}


@dataclass(frozen=True)
class ProductCommerceProfile:
    product: Product
    sku: str
    platforms: list[CommercePlatform]
    platform_statuses: dict[CommercePlatform, str]
    warehouse_key: str
    warehouse_name: str
    warehouse_country: str
    available_stock: int
    reserved_stock: int
    safety_stock: int
    weekly_sales: int
    rating: float
    review_count: int
    evidence_count: int

    @property
    def stock_status(self) -> str:
        if self.available_stock <= 0:
            return "out_of_stock"
        if self.available_stock <= self.safety_stock:
            return "low_stock"
        return "healthy"

    @property
    def heat_score(self) -> int:
        score = self.weekly_sales * 2 + self.review_count // 2 + round(self.rating * 8) + self.evidence_count * 6
        if self.stock_status != "healthy":
            score += 8
        return max(0, min(100, score))


def build_commerce_overview(
    *,
    products: list[Product],
    feedbacks: list[Feedback],
    contents: list[GeneratedContent],
) -> CommerceOverview:
    feedbacks_by_product = _group_feedbacks(feedbacks)
    contents_by_product = _group_contents_by_product(contents)
    profiles = [
        _build_profile(
            product=product,
            index=index,
            feedbacks=feedbacks_by_product.get(product.id, []),
            contents=contents_by_product.get(product.id, []),
        )
        for index, product in enumerate(products)
    ]
    platform_summaries = [_build_platform_summary(platform, label, profiles) for platform, label in PLATFORMS]
    warehouse_summaries = _build_warehouse_summaries(profiles)
    inventory_alerts = _build_inventory_alerts(profiles)
    hot_products = _build_hot_products(profiles)
    recommended_actions = _build_recommended_actions(
        products=products,
        profiles=profiles,
        inventory_alerts=inventory_alerts,
        platform_summaries=platform_summaries,
        feedbacks_by_product=feedbacks_by_product,
    )

    return CommerceOverview(
        positioning="SellerHarbor 跨境卖家商品运营港",
        operatingFocus=["商品主数据收口", "Temu / TikTok Shop 上架管理", "海外仓库存分配", "好评与热款追踪"],
        kpis=_build_kpis(products, profiles, hot_products),
        platforms=platform_summaries,
        warehouses=warehouse_summaries,
        inventoryAlerts=inventory_alerts,
        hotProducts=hot_products,
        recommendedActions=recommended_actions,
        generatedAt=now_iso(),
    )


def _build_profile(
    *,
    product: Product,
    index: int,
    feedbacks: list[Feedback],
    contents: list[GeneratedContent],
) -> ProductCommerceProfile:
    attrs = _normalized_attributes(product)
    fallback_warehouse = WAREHOUSE_FALLBACKS[index % len(WAREHOUSE_FALLBACKS)]
    platforms = _platforms(attrs, index)
    available_stock = _int_attr(attrs, "availablestock", "inventory", "stock", "库存", "可用库存", default=FALLBACK_STOCK[index % len(FALLBACK_STOCK)])
    safety_stock = _int_attr(attrs, "safetystock", "安全库存", default=10)
    reserved_stock = _int_attr(attrs, "reservedstock", "reserved", "占用库存", default=FALLBACK_RESERVED[index % len(FALLBACK_RESERVED)])
    evidence_count = len(feedbacks) + len(contents)

    platform_statuses: dict[CommercePlatform, str] = {}
    for platform, _label in PLATFORMS:
        explicit_status = _platform_status(attrs, platform)
        if explicit_status:
            platform_statuses[platform] = explicit_status
            continue
        if platform not in platforms:
            platform_statuses[platform] = "missing"
        elif _listing_ready(product) and available_stock > safety_stock:
            platform_statuses[platform] = "ready"
        else:
            platform_statuses[platform] = "watch"

    return ProductCommerceProfile(
        product=product,
        sku=_attr(attrs, "sku", "sellersku", "商家sku", "商品sku") or f"SKU-{product.id[-6:].upper()}",
        platforms=platforms,
        platform_statuses=platform_statuses,
        warehouse_key=_slug(_attr(attrs, "warehousekey", "仓库编码") or fallback_warehouse[0]),
        warehouse_name=_attr(attrs, "warehousename", "warehouse", "海外仓", "仓库") or fallback_warehouse[1],
        warehouse_country=_attr(attrs, "warehousecountry", "country", "仓库国家") or fallback_warehouse[2],
        available_stock=available_stock,
        reserved_stock=max(0, reserved_stock),
        safety_stock=max(1, safety_stock),
        weekly_sales=_int_attr(attrs, "weeklysales", "sales7d", "近7日销量", default=FALLBACK_SALES[index % len(FALLBACK_SALES)] + evidence_count * 4),
        rating=_float_attr(attrs, "rating", "评分", default=round(4.2 + min(0.7, evidence_count * 0.12), 1) if evidence_count else 0),
        review_count=_int_attr(attrs, "reviewcount", "reviews", "评价数", default=evidence_count * 12),
        evidence_count=evidence_count,
    )


def _build_platform_summary(platform: CommercePlatform, label: str, profiles: list[ProductCommerceProfile]) -> CommercePlatformSummary:
    ready = sum(1 for profile in profiles if _status_bucket(profile.platform_statuses[platform]) == "ready")
    watch = sum(1 for profile in profiles if _status_bucket(profile.platform_statuses[platform]) == "watch")
    missing = sum(1 for profile in profiles if _status_bucket(profile.platform_statuses[platform]) == "missing")
    total_listings = ready + watch
    priority_action = "保持同步节奏"
    if missing:
        priority_action = f"补齐 {missing} 个商品的 {label} Listing"
    elif watch:
        priority_action = f"处理 {watch} 个 {label} 待优化 Listing"
    return CommercePlatformSummary(
        platform=platform,
        label=label,
        totalListings=total_listings,
        readyListings=ready,
        watchListings=watch,
        missingListings=missing,
        readinessRate=_percent(ready, len(profiles)),
        priorityAction=priority_action,
    )


def _build_warehouse_summaries(profiles: list[ProductCommerceProfile]) -> list[CommerceWarehouseSummary]:
    groups: dict[str, list[ProductCommerceProfile]] = defaultdict(list)
    for profile in profiles:
        groups[profile.warehouse_key].append(profile)
    summaries: list[CommerceWarehouseSummary] = []
    for key, items in groups.items():
        platforms = sorted({platform for item in items for platform in item.platforms})
        low_stock = sum(1 for item in items if item.stock_status != "healthy")
        summaries.append(
            CommerceWarehouseSummary(
                key=key,
                name=items[0].warehouse_name,
                country=items[0].warehouse_country,
                platforms=platforms,
                totalSkus=len(items),
                totalUnits=sum(item.available_stock for item in items),
                reservedUnits=sum(item.reserved_stock for item in items),
                lowStockSkus=low_stock,
                stockHealthRate=_percent(len(items) - low_stock, len(items)),
            )
        )
    return sorted(summaries, key=lambda item: (item.lowStockSkus, -item.totalUnits), reverse=True)


def _build_inventory_alerts(profiles: list[ProductCommerceProfile]) -> list[CommerceInventoryAlert]:
    alerts: list[CommerceInventoryAlert] = []
    for profile in profiles:
        if profile.stock_status == "healthy":
            continue
        status = "out_of_stock" if profile.stock_status == "out_of_stock" else "low_stock"
        detail = "已无可售库存，需要立即补货或下调平台可售库存。"
        if status == "low_stock":
            detail = f"可用库存 {profile.available_stock} 低于安全库存 {profile.safety_stock}，热款风险需要优先处理。"
        alerts.append(
            CommerceInventoryAlert(
                productId=profile.product.id,
                productName=profile.product.name,
                sku=profile.sku,
                warehouseKey=profile.warehouse_key,
                warehouseName=profile.warehouse_name,
                availableStock=profile.available_stock,
                reservedStock=profile.reserved_stock,
                safetyStock=profile.safety_stock,
                status=status,
                detail=detail,
                nextActionHref=f"/products?productId={profile.product.id}",
            )
        )
    return sorted(alerts, key=lambda item: (item.status != "out_of_stock", item.availableStock))[:8]


def _build_hot_products(profiles: list[ProductCommerceProfile]) -> list[CommerceHotProduct]:
    hot_products: list[CommerceHotProduct] = []
    for profile in sorted(profiles, key=lambda item: item.heat_score, reverse=True)[:6]:
        heat_level = "needs_attention"
        if profile.heat_score >= 85:
            heat_level = "hot"
        elif profile.heat_score >= 60:
            heat_level = "rising"
        elif profile.heat_score >= 35:
            heat_level = "steady"
        hot_products.append(
            CommerceHotProduct(
                productId=profile.product.id,
                productName=profile.product.name,
                category=profile.product.category,
                sku=profile.sku,
                heatScore=profile.heat_score,
                heatLevel=heat_level,
                weeklySales=profile.weekly_sales,
                rating=profile.rating,
                reviewCount=profile.review_count,
                availableStock=profile.available_stock,
                platforms=profile.platforms,
                nextAction=_hot_product_action(profile),
            )
        )
    return hot_products


def _build_kpis(products: list[Product], profiles: list[ProductCommerceProfile], hot_products: list[CommerceHotProduct]) -> list[CommerceKpi]:
    total_platform_slots = max(1, len(products) * len(PLATFORMS))
    ready_slots = sum(
        1
        for profile in profiles
        for platform, _label in PLATFORMS
        if _status_bucket(profile.platform_statuses[platform]) == "ready"
    )
    healthy_stock = sum(1 for profile in profiles if profile.stock_status == "healthy")
    hot_count = sum(1 for product in hot_products if product.heatLevel in {"hot", "rising"})
    return [
        CommerceKpi(key="product_master", label="商品主档", value=len(products), unit="个", tone="primary", detail="统一承载跨平台商品资料"),
        CommerceKpi(key="listing_readiness", label="上架就绪率", value=_percent(ready_slots, total_platform_slots), unit="%", tone="success", detail="Temu / TikTok Shop 综合就绪"),
        CommerceKpi(key="stock_health", label="库存健康率", value=_percent(healthy_stock, len(profiles)), unit="%", tone="warning", detail="按安全库存线判断"),
        CommerceKpi(key="hot_products", label="热款/潜力款", value=hot_count, unit="个", tone="primary", detail="结合销量、评价和反馈信号"),
    ]


def _build_recommended_actions(
    *,
    products: list[Product],
    profiles: list[ProductCommerceProfile],
    inventory_alerts: list[CommerceInventoryAlert],
    platform_summaries: list[CommercePlatformSummary],
    feedbacks_by_product: dict[str, list[Feedback]],
) -> list[BusinessRecommendedAction]:
    actions: list[BusinessRecommendedAction] = []
    if not products:
        actions.append(
            BusinessRecommendedAction(
                key="create_product_master",
                label="先建立商品主档",
                detail="录入 SKU、变体、平台目标和仓库库存后，才能形成跨平台运营收口。",
                priority=10,
                href="/products",
                tone="primary",
            )
        )
        return actions

    missing_listings = sum(summary.missingListings for summary in platform_summaries)
    if missing_listings:
        actions.append(
            BusinessRecommendedAction(
                key="complete_platform_listings",
                label="补齐跨平台 Listing",
                detail=f"发现 {missing_listings} 个平台商品位缺少上架资料，优先补齐 Temu / TikTok Shop 映射。",
                priority=20,
                href="/products",
                tone="warning",
            )
        )
    if inventory_alerts:
        actions.append(
            BusinessRecommendedAction(
                key="resolve_inventory_alerts",
                label="处理海外仓库存预警",
                detail=f"{len(inventory_alerts)} 个 SKU 低于安全库存，先调整平台可售库存或安排补货。",
                priority=25,
                href="/products",
                tone="warning",
            )
        )
    hot_low_stock = [profile for profile in profiles if profile.heat_score >= 60 and profile.stock_status != "healthy"]
    if hot_low_stock:
        actions.append(
            BusinessRecommendedAction(
                key="protect_hot_products",
                label="保护热款不断货",
                detail=f"{len(hot_low_stock)} 个热款/潜力款存在库存风险，建议优先补货并收紧平台分配。",
                priority=30,
                href="/products",
                tone="primary",
            )
        )
    missing_feedback = sum(1 for product in products if not feedbacks_by_product.get(product.id))
    if missing_feedback:
        actions.append(
            BusinessRecommendedAction(
                key="collect_review_signals",
                label="补充好评与客服反馈",
                detail=f"{missing_feedback} 个商品缺少评价/反馈信号，热款判断和详情页素材会偏弱。",
                priority=40,
                href="/feedback",
                tone="neutral",
            )
        )
    if not actions:
        actions.append(
            BusinessRecommendedAction(
                key="scale_next_batch",
                label="扩展下一批跨境商品",
                detail="当前商品、库存和评价信号较健康，可以继续导入新品并批量准备上架素材。",
                priority=90,
                href="/products",
                tone="success",
            )
        )
    return sorted(actions, key=lambda item: item.priority)[:5]


def _hot_product_action(profile: ProductCommerceProfile) -> str:
    if profile.stock_status != "healthy":
        return "优先补货，并降低平台可售库存避免断货。"
    if profile.review_count <= 0:
        return "补充好评和客服反馈，提升详情页可信度。"
    missing = [label for platform, label in PLATFORMS if _status_bucket(profile.platform_statuses[platform]) == "missing"]
    if missing:
        return f"同步准备 {'、'.join(missing)} 上架资料。"
    return "保持库存节奏，继续沉淀好评和详情页素材。"


def _group_feedbacks(feedbacks: list[Feedback]) -> dict[str, list[Feedback]]:
    grouped: dict[str, list[Feedback]] = defaultdict(list)
    for feedback in feedbacks:
        grouped[feedback.productId].append(feedback)
    return grouped


def _group_contents_by_product(contents: list[GeneratedContent]) -> dict[str, list[GeneratedContent]]:
    grouped: dict[str, list[GeneratedContent]] = defaultdict(list)
    # GeneratedContent only stores taskId; this overview uses content count as a secondary signal when callers can enrich later.
    for content in contents:
        source_product = next((trace.split(":", 1)[1] for trace in content.sourceTrace if trace.startswith("product:")), "")
        if source_product:
            grouped[source_product].append(content)
    return grouped


def _listing_ready(product: Product) -> bool:
    return bool(product.name and product.category and product.sellingPoints and product.attributes)


def _platforms(attrs: dict[str, str], index: int) -> list[CommercePlatform]:
    raw = _attr(attrs, "platforms", "platform", "平台", "目标平台")
    platforms = _parse_platforms(raw)
    if platforms:
        return platforms
    if _platform_status(attrs, "temu"):
        platforms.append("temu")
    if _platform_status(attrs, "tiktok_shop"):
        platforms.append("tiktok_shop")
    if platforms:
        return platforms
    return ["temu", "tiktok_shop"] if index % 2 == 0 else ["temu"]


def _parse_platforms(value: str | None) -> list[CommercePlatform]:
    if not value:
        return []
    normalized = value.replace("，", ",").replace("|", ",").replace("/", ",")
    platforms: list[CommercePlatform] = []
    for item in normalized.split(","):
        token = item.strip().lower().replace(" ", "_").replace("-", "_")
        if "temu" in token and "temu" not in platforms:
            platforms.append("temu")
        if ("tiktok" in token or "tik_tok" in token or "抖音" in token) and "tiktok_shop" not in platforms:
            platforms.append("tiktok_shop")
    return platforms


def _platform_status(attrs: dict[str, str], platform: CommercePlatform) -> str:
    if platform == "temu":
        return (_attr(attrs, "temustatus", "temu状态", "temulistingstatus") or "").strip().lower()
    return (_attr(attrs, "tiktokstatus", "tiktokshopstatus", "tiktok状态", "tiktoklistingstatus") or "").strip().lower()


def _status_bucket(status: str) -> str:
    normalized = status.strip().lower()
    if normalized in READY_STATUSES:
        return "ready"
    if normalized == "missing":
        return "missing"
    if normalized in WATCH_STATUSES or normalized:
        return "watch"
    return "missing"


def _normalized_attributes(product: Product) -> dict[str, str]:
    return {_normalize_key(key): str(value).strip() for key, value in product.attributes.items() if str(value).strip()}


def _attr(attrs: dict[str, str], *keys: str) -> str | None:
    for key in keys:
        value = attrs.get(_normalize_key(key))
        if value:
            return value
    return None


def _int_attr(attrs: dict[str, str], *keys: str, default: int) -> int:
    value = _attr(attrs, *keys)
    if value is None:
        return default
    digits = "".join(char for char in value if char.isdigit() or char == "-")
    if not digits or digits == "-":
        return default
    return int(digits)


def _float_attr(attrs: dict[str, str], *keys: str, default: float) -> float:
    value = _attr(attrs, *keys)
    if value is None:
        return default
    allowed = "".join(char for char in value if char.isdigit() or char in {".", "-"})
    if not allowed or allowed in {"-", "."}:
        return default
    return round(float(allowed), 1)


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "").replace("_", "").replace("-", "")


def _slug(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    return "-".join(part for part in normalized.split("-") if part) or "warehouse"


def _percent(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        return 0
    return round((numerator / denominator) * 100)

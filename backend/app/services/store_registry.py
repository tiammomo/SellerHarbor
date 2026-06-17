from __future__ import annotations

from app.core.config import settings
from app.core.tenant import current_tenant_id
from app.db import repository
from app.models.schemas import (
    CommercePlatform,
    StoreCapability,
    StoreDataBoundary,
    StoreExpansionSlot,
    StoreProfile,
    StoreRegistry,
)
from app.services.temu_integration import TEMU_CREDENTIAL_ENV_VARS, build_temu_integration_status


PLATFORM_LABELS: dict[str, str] = {
    "temu": "Temu",
    "tiktok_shop": "TikTok Shop",
}


def build_store_registry() -> StoreRegistry:
    platform = _normalize_platform(settings.store.default_store_platform)
    multi_store_enabled = settings.store.multi_store_enabled or len(settings.store.allowed_store_ids) > 1
    return StoreRegistry(
        tenantId=current_tenant_id(),
        mode="multi_store_ready" if multi_store_enabled else "single_store",
        defaultStoreId=settings.store.default_store_id,
        multiStoreEnabled=multi_store_enabled,
        stores=[_default_store(platform)],
        expansionSlots=_expansion_slots(platform),
        dataBoundaries=_data_boundaries(),
        nextActions=_next_actions(multi_store_enabled=multi_store_enabled),
        updatedAt=repository.now_iso(),
    )


def _default_store(platform: CommercePlatform) -> StoreProfile:
    connection_status = _connection_status(platform)
    return StoreProfile(
        id=settings.store.default_store_id,
        tenantId=current_tenant_id(),
        name=settings.store.default_store_name,
        platform=platform,
        platformLabel=PLATFORM_LABELS[platform],
        status="active",
        region=_store_region(platform),
        externalSellerId=_external_seller_id(platform),
        isDefault=True,
        defaultWarehouse=settings.store.default_store_warehouse,
        sharedInventoryGroup="default-shared-inventory",
        credentialScope=_credential_scope(platform),
        connectionStatus=connection_status,
        capabilities=_capabilities(connection_status),
        notes=[
            "当前商品主档仍属于租户级主数据，不直接绑定单个店铺。",
            "后续 PlatformListing 会用 storeId 把同一商品映射到多个平台店铺。",
            "海外仓库存保持共享视角，后续按 storeId 做平台占用和安全库存分配。",
        ],
    )


def _normalize_platform(value: str) -> CommercePlatform:
    platform = value.strip().lower().replace("-", "_")
    if platform in PLATFORM_LABELS:
        return platform  # type: ignore[return-value]
    return "temu"


def _store_region(platform: CommercePlatform) -> str:
    if platform == "temu" and settings.temu.region:
        return settings.temu.region
    return settings.store.default_store_region


def _external_seller_id(platform: CommercePlatform) -> str | None:
    if platform == "temu" and settings.temu.seller_id:
        return settings.temu.seller_id
    return None


def _connection_status(platform: CommercePlatform) -> str:
    if platform != "temu":
        return "planned"
    temu = build_temu_integration_status()
    if temu.configured:
        return "ready"
    if temu.readiness == "needs_authorization":
        return "needs_authorization"
    return "needs_credentials"


def _credential_scope(platform: CommercePlatform) -> str:
    if platform == "temu":
        return "env:SELLERHARBOR_TEMU_* for default store"
    return "planned:per-store credential vault"


def _capabilities(connection_status: str) -> list[StoreCapability]:
    read_status = "ready" if connection_status == "ready" else "needs_credentials"
    if connection_status == "planned":
        read_status = "planned"
    if connection_status == "needs_authorization":
        read_status = "needs_permission"

    return [
        StoreCapability(
            key="tenant_catalog",
            label="租户级商品主档",
            mode="manual",
            status="ready",
            detail="当前单店铺也先把商品作为租户级主数据维护，避免后续多店铺重复建商品。",
            riskLevel="low",
        ),
        StoreCapability(
            key="listing_read",
            label="店铺 Listing 读取",
            mode="read",
            status=read_status,
            detail="未来按 storeId 同步平台 Listing、审核状态、外部商品 ID 和字段完整度。",
            riskLevel="low",
        ),
        StoreCapability(
            key="order_read",
            label="店铺订单与销量读取",
            mode="read",
            status=read_status,
            detail="未来按店铺沉淀销量、履约和热款信号，不与其他店铺混用。",
            riskLevel="low",
        ),
        StoreCapability(
            key="inventory_allocation",
            label="共享仓库存分配",
            mode="manual",
            status="planned",
            detail="下一阶段把共享海外仓库存拆成仓库库存和店铺占用，降低多平台超卖风险。",
            riskLevel="medium",
        ),
        StoreCapability(
            key="store_writeback",
            label="店铺写回操作",
            mode="write",
            status="blocked",
            detail="Listing、价格、库存写回必须按店铺独立授权，并经过预览、人工确认、审计和回滚。",
            riskLevel="high",
        ),
    ]


def _expansion_slots(default_platform: CommercePlatform) -> list[StoreExpansionSlot]:
    slots = [
        StoreExpansionSlot(
            key="additional_temu_store",
            label="新增 Temu 店铺",
            platform="temu",
            status="ready_for_config" if default_platform != "temu" else "planned",
            detail="支持后续把另一个 Temu 店铺作为独立 storeId 接入，凭证和同步任务不与默认店铺共用。",
            requiredEnvVars=TEMU_CREDENTIAL_ENV_VARS,
        ),
        StoreExpansionSlot(
            key="tiktok_shop_store",
            label="新增 TikTok Shop 店铺",
            platform="tiktok_shop",
            status="ready_for_config" if default_platform != "tiktok_shop" else "planned",
            detail="预留 TikTok Shop 店铺配置入口；需要确认官方 API、区域和授权方式后接入。",
            requiredEnvVars=["future:SELLERHARBOR_TIKTOK_SHOP_*"],
        ),
    ]
    return slots


def _data_boundaries() -> list[StoreDataBoundary]:
    return [
        StoreDataBoundary(
            key="tenant",
            label="商家 / 团队边界",
            currentState="通过 X-SellerHarbor-Tenant-ID 隔离。",
            nextSchema="tenants / users / roles",
            reason="多店铺属于同一个商家空间，不能替代租户隔离。",
        ),
        StoreDataBoundary(
            key="stores",
            label="店铺主档",
            currentState="默认店铺由环境变量配置。",
            nextSchema="stores(id, tenant_id, platform, name, region, status, default_warehouse_id)",
            reason="一个租户可拥有多个 Temu / TikTok Shop 店铺，每个店铺需要独立状态和授权。",
        ),
        StoreDataBoundary(
            key="platform_listings",
            label="平台 Listing",
            currentState="平台状态暂存在 products.attributes。",
            nextSchema="platform_listings(id, tenant_id, store_id, product_id, external_listing_id, status, sync_state)",
            reason="同一商品可以在多个店铺拥有不同标题、价格、状态、审核结果和外部 ID。",
        ),
        StoreDataBoundary(
            key="inventory_allocations",
            label="共享仓库存分配",
            currentState="仓库、库存和销量暂存在 products.attributes。",
            nextSchema="warehouses / inventory_items / platform_allocations / inventory_movements",
            reason="多店铺共享海外仓时，需要区分总库存、可用库存、店铺占用和安全库存。",
        ),
        StoreDataBoundary(
            key="integration_credentials",
            label="平台授权凭证",
            currentState="默认店铺 Temu 凭证通过环境变量注入。",
            nextSchema="encrypted store_credentials with rotation metadata",
            reason="多店铺不能复用 token，凭证必须按店铺加密存储、轮换和审计。",
        ),
    ]


def _next_actions(*, multi_store_enabled: bool) -> list[str]:
    actions = [
        "短期继续按默认店铺运营，不影响当前商品、反馈、生成和看板流程。",
        "新增 PlatformListing 表时必须包含 store_id，商品主档不直接复制为多份。",
        "新增库存表时把 warehouse_id、store_id 和 platform 分开建模，支持共享仓与平台占用。",
        "平台 API 接入先按单店铺只读同步验证，再扩展到多店铺授权和同步任务。",
    ]
    if not multi_store_enabled:
        actions.append("等真实出现第二个店铺时，再开启 SELLERHARBOR_MULTI_STORE_ENABLED 并配置允许的 store id。")
    return actions

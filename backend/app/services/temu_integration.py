from __future__ import annotations

from app.core.config import settings
from app.db import repository
from app.models.schemas import TemuCapability, TemuIntegrationStatus, TemuRequirement


TEMU_CREDENTIAL_ENV_VARS = [
    "SELLERHARBOR_TEMU_API_BASE_URL",
    "SELLERHARBOR_TEMU_APP_KEY",
    "SELLERHARBOR_TEMU_APP_SECRET",
    "SELLERHARBOR_TEMU_ACCESS_TOKEN",
    "SELLERHARBOR_TEMU_SELLER_ID",
    "SELLERHARBOR_TEMU_REGION",
    "SELLERHARBOR_TEMU_SANDBOX",
]


TEMU_DOCS = [
    "https://partner.temu.com/",
    "https://partner.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303",
    "https://partner.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a",
    "https://www.postman.com/temu-open/temu-open-platform/overview",
]


def build_temu_integration_status() -> TemuIntegrationStatus:
    temu = settings.temu
    missing = _missing_credentials()
    configured = not missing
    readiness = _readiness(configured=configured, missing=missing)

    return TemuIntegrationStatus(
        configured=configured,
        readiness=readiness,
        region=temu.region,
        sandbox=temu.sandbox,
        apiBaseUrl=temu.api_base_url,
        credentialEnvVars=TEMU_CREDENTIAL_ENV_VARS,
        requirements=_requirements(missing),
        capabilities=_capabilities(configured),
        nextActions=_next_actions(missing),
        docs=TEMU_DOCS,
        updatedAt=repository.now_iso(),
    )


def _missing_credentials() -> list[str]:
    missing = []
    if not settings.temu.api_base_url:
        missing.append("SELLERHARBOR_TEMU_API_BASE_URL")
    if not settings.temu.app_key:
        missing.append("SELLERHARBOR_TEMU_APP_KEY")
    if not settings.temu.app_secret:
        missing.append("SELLERHARBOR_TEMU_APP_SECRET")
    if not settings.temu.access_token:
        missing.append("SELLERHARBOR_TEMU_ACCESS_TOKEN")
    return missing


def _readiness(*, configured: bool, missing: list[str]) -> str:
    if configured:
        return "ready"
    if settings.temu.partially_configured and "SELLERHARBOR_TEMU_ACCESS_TOKEN" in missing:
        return "needs_authorization"
    return "needs_credentials"


def _requirements(missing: list[str]) -> list[TemuRequirement]:
    missing_set = set(missing)
    return [
        TemuRequirement(
            key="partner_app",
            label="Temu Partner 应用",
            status="missing" if {"SELLERHARBOR_TEMU_APP_KEY", "SELLERHARBOR_TEMU_APP_SECRET"} & missing_set else "ready",
            detail="需要 Temu Partner/Open Platform 应用的 app key 和 app secret。",
            envVars=["SELLERHARBOR_TEMU_APP_KEY", "SELLERHARBOR_TEMU_APP_SECRET"],
        ),
        TemuRequirement(
            key="seller_authorization",
            label="Seller Center 授权",
            status="missing" if "SELLERHARBOR_TEMU_ACCESS_TOKEN" in missing_set else "ready",
            detail="需要店铺在 Temu Seller Center 授权应用，获得可调用店铺管理 API 的 token。",
            envVars=["SELLERHARBOR_TEMU_ACCESS_TOKEN", "SELLERHARBOR_TEMU_SELLER_ID"],
        ),
        TemuRequirement(
            key="region_scope",
            label="区域与店铺范围",
            status="ready" if settings.temu.region else "missing",
            detail="确认店铺区域、站点和 token 对应范围；多区域店铺可能需要分别授权。",
            envVars=["SELLERHARBOR_TEMU_REGION", "SELLERHARBOR_TEMU_SANDBOX"],
        ),
        TemuRequirement(
            key="permission_scope",
            label="接口权限确认",
            status="manual",
            detail="需要在 Temu 后台确认商品列表、订单列表、订单履约、库存/价格等权限是否对当前店铺开放。",
            envVars=[],
        ),
    ]


def _capabilities(configured: bool) -> list[TemuCapability]:
    read_status = "planned" if configured else "needs_permission"
    return [
        TemuCapability(
            key="products_read",
            label="商品 / SKU / Listing 只读同步",
            mode="read",
            status=read_status,
            detail="第一阶段同步商品主档、SKU、平台状态和上架资料完整度。",
            requiredPermission="product list / goods read",
            riskLevel="low",
        ),
        TemuCapability(
            key="orders_read",
            label="订单与履约状态只读同步",
            mode="read",
            status=read_status,
            detail="同步订单列表、订单状态、发货和履约信息，用于销量与热款判断。",
            requiredPermission="order list / order fulfillment read",
            riskLevel="low",
        ),
        TemuCapability(
            key="inventory_read",
            label="库存信号只读同步",
            mode="read",
            status=read_status,
            detail="同步可用库存、占用库存或仓库相关字段；具体字段依赖店铺权限和接口返回。",
            requiredPermission="inventory / goods read",
            riskLevel="low",
        ),
        TemuCapability(
            key="events_subscribe",
            label="Webhook / 事件订阅",
            mode="event",
            status="planned" if configured else "needs_permission",
            detail="用于后续减少轮询，接收订单、履约或商品变更事件。",
            requiredPermission="event subscription",
            riskLevel="medium",
        ),
        TemuCapability(
            key="listing_write",
            label="Listing / 价格 / 库存写回",
            mode="write",
            status="blocked",
            detail="暂不自动写回；必须等只读同步稳定后，再加人工确认、审计、重试和回滚。",
            requiredPermission="goods write / price change / inventory update",
            riskLevel="high",
        ),
    ]


def _next_actions(missing: list[str]) -> list[str]:
    if missing:
        return [
            "确认 Temu Seller Center 是否有 Partner/Open Platform 或 Third-party App 授权入口。",
            "确认店铺区域、站点、卖家 ID，以及是否需要 sandbox/test shop。",
            "准备 Temu Partner app key、app secret 和 Seller Center 授权 token。",
            "先开通商品列表、订单列表、订单履约和库存只读权限；写回权限后置。",
        ]
    return [
        "用 Postman 或后端调试脚本验证签名和 token 可用。",
        "先实现商品、订单、库存只读同步 dry-run，不写入业务表。",
        "确认字段映射后再导入 SellerHarbor 商品主档。",
        "写回类操作保持禁用，直到审计、回滚和人工确认就绪。",
    ]

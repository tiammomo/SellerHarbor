from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.db import repository
from app.models.schemas import CreateProduct, MarketIngestionItem, MarketIngestionRequest, MarketIngestionRun, Product
from app.services import object_storage


OPEN_FOOD_FACTS_PROVIDER_ID = "open_food_facts"
OPEN_FOOD_FACTS_SEARCH_URL = "https://world.openfoodfacts.org/api/v2/search"
LOW_FREQUENCY_COOLDOWN = timedelta(hours=6)


async def ingest_open_food_facts(payload: MarketIngestionRequest) -> MarketIngestionRun:
    keyword = _normalize_keyword(payload.keyword)
    limit = payload.limit
    started_at = repository.now_iso()

    last_run = repository.last_market_ingestion_run(OPEN_FOOD_FACTS_PROVIDER_ID, keyword)
    if last_run and not payload.force:
        next_allowed = _parse_iso(last_run.startedAt) + LOW_FREQUENCY_COOLDOWN
        if datetime.now(timezone.utc) < next_allowed:
            return last_run.model_copy(
                update={
                    "status": "skipped",
                    "message": f"低频保护中：同一关键词 6 小时内不重复采集，下一次允许时间 { _to_iso(next_allowed) }。",
                    "nextAllowedAt": _to_iso(next_allowed),
                }
            )

    try:
        raw_products = await _search_open_food_facts(keyword=keyword, limit=limit)
        items = await _persist_open_food_facts_products(raw_products=raw_products, keyword=keyword, limit=limit)
        status = "completed"
        message = f"已从 Open Food Facts 低频采集 {len([item for item in items if item.status == 'created'])} 个商品候选。"
    except Exception as exc:
        items = []
        status = "failed"
        message = f"Open Food Facts 采集失败：{exc}"

    finished_at = repository.now_iso()
    return repository.create_market_ingestion_run(
        provider_id=OPEN_FOOD_FACTS_PROVIDER_ID,
        keyword=keyword,
        status=status,
        requested_limit=limit,
        created_count=len([item for item in items if item.status == "created"]),
        skipped_count=len([item for item in items if item.status == "skipped"]),
        items=items,
        message=message,
        started_at=started_at,
        finished_at=finished_at,
        next_allowed_at=_to_iso(_parse_iso(started_at) + LOW_FREQUENCY_COOLDOWN),
    )


async def _search_open_food_facts(*, keyword: str, limit: int) -> list[dict[str, Any]]:
    params = {
        "search_terms": keyword,
        "page_size": max(8, min(30, limit * 6)),
        "json": 1,
        "fields": ",".join(
            [
                "code",
                "product_name",
                "brands",
                "categories",
                "image_front_url",
                "image_url",
                "ingredients_text",
                "quantity",
                "countries_tags",
                "nutriscore_grade",
                "nova_group",
                "ecoscore_grade",
                "stores",
                "labels_tags",
            ]
        ),
    }
    category_tag = _category_tag_for_keyword(keyword)
    if category_tag:
        params["categories_tags"] = category_tag
    headers = {"User-Agent": "ReviewPilot/0.1 product-sourcing-demo"}
    async with httpx.AsyncClient(timeout=20, headers=headers, follow_redirects=True) as client:
        response = await client.get(OPEN_FOOD_FACTS_SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()
    products = data.get("products")
    if not isinstance(products, list):
        return []
    return [product for product in products if isinstance(product, dict)]


async def _persist_open_food_facts_products(*, raw_products: list[dict[str, Any]], keyword: str, limit: int) -> list[MarketIngestionItem]:
    existing_by_source_id = _existing_by_source_id()
    items: list[MarketIngestionItem] = []
    created = 0

    for raw in raw_products:
        if created >= limit:
            break
        code = str(raw.get("code") or "").strip()
        name = _clean_text(raw.get("product_name"))
        image_url = _clean_text(raw.get("image_front_url")) or _clean_text(raw.get("image_url"))
        source_url = f"https://world.openfoodfacts.org/product/{code}" if code else "https://world.openfoodfacts.org/"

        if not code:
            items.append(_item(raw, status="skipped", reason="缺少 Open Food Facts 条码 ID"))
            continue
        if not name:
            items.append(_item(raw, status="skipped", reason="缺少商品名称"))
            continue
        if not image_url:
            items.append(_item(raw, status="skipped", reason="缺少可展示商品图"))
            continue
        if code in existing_by_source_id:
            existing_product = existing_by_source_id[code]
            items.append(
                MarketIngestionItem(
                    sourceProductId=code,
                    productName=name,
                    imageUrl=existing_product.attributes.get("商品图片URL") or image_url,
                    sourceImageUrl=existing_product.attributes.get("原始商品图片URL") or image_url,
                    imageStorageKey=existing_product.attributes.get("对象存储Key") or None,
                    imageStorageStatus=_item_storage_status(existing_product),
                    sourceUrl=source_url,
                    status="skipped",
                    reason="商品已存在，按来源商品 ID 去重",
                    productId=existing_product.id,
                )
            )
            continue

        image_asset = await _store_image_asset(source_image_url=image_url, keyword=keyword, source_product_id=code)
        product = repository.create_product(
            _to_product(
                raw,
                keyword=keyword,
                image_url=image_asset["image_url"],
                source_image_url=image_url,
                source_url=source_url,
                image_storage_key=image_asset["storage_key"],
                image_storage_status=image_asset["storage_status"],
                image_storage_message=image_asset["storage_message"],
                image_content_type=image_asset["content_type"],
                image_size_bytes=image_asset["size_bytes"],
            )
        )
        existing_by_source_id[code] = product
        created += 1
        items.append(
            MarketIngestionItem(
                sourceProductId=code,
                productName=product.name,
                imageUrl=image_asset["image_url"],
                sourceImageUrl=image_url,
                imageStorageKey=image_asset["storage_key"],
                imageStorageStatus=image_asset["storage_status"],
                sourceUrl=source_url,
                status="created",
                reason=image_asset["storage_message"] or "已写入选品池",
                productId=product.id,
            )
        )

    return items


def _to_product(
    raw: dict[str, Any],
    *,
    keyword: str,
    image_url: str,
    source_image_url: str,
    source_url: str,
    image_storage_key: str | None,
    image_storage_status: str | None,
    image_storage_message: str,
    image_content_type: str,
    image_size_bytes: int,
) -> CreateProduct:
    code = str(raw.get("code") or "").strip()
    name = _clean_text(raw.get("product_name"))
    brands = _clean_text(raw.get("brands"))
    quantity = _clean_text(raw.get("quantity"))
    ingredients = _clean_text(raw.get("ingredients_text"))
    labels = _labels(raw.get("labels_tags"))
    countries = _countries(raw.get("countries_tags"))
    nutriscore = _clean_text(raw.get("nutriscore_grade")).upper()
    nova_group = str(raw.get("nova_group") or "").strip()
    ecoscore = _clean_text(raw.get("ecoscore_grade")).upper()

    attributes = {
        "商品图片URL": image_url,
        "原始商品图片URL": source_image_url,
        "来源链接": source_url,
        "数据来源": "Open Food Facts",
        "来源商品ID": code,
        "采集方式": "官方API",
        "采集关键词": keyword,
        "采集时间": repository.now_iso(),
        "图片存储": "MinIO" if image_storage_status == "stored" else "来源URL",
        "图片存储状态": _image_storage_label(image_storage_status),
        "图片存储说明": image_storage_message,
        "对象存储Bucket": object_storage.status()["bucket"] if image_storage_status == "stored" else "",
        "对象存储Key": image_storage_key or "",
        "图片ContentType": image_content_type,
        "图片大小Bytes": str(image_size_bytes) if image_size_bytes else "",
        "品牌": brands,
        "规格": quantity,
        "开放类目": _clean_text(raw.get("categories")),
        "销售国家": countries,
        "配料": ingredients[:180] if ingredients else "",
        "Nutri-Score": nutriscore,
        "NOVA分组": nova_group,
        "Eco-Score": ecoscore,
        "标签": "、".join(labels[:8]),
    }
    attributes = {key: value for key, value in attributes.items() if value}

    selling_points = _unique(
        [
            *(["有开放数据库商品包装图"] if image_url else []),
            *(["配料信息可复核"] if ingredients else []),
            *(["多国家市场有记录"] if countries else []),
            *(labels[:3]),
            *(["Nutri-Score " + nutriscore] if nutriscore else []),
        ]
    )[:5]

    return CreateProduct(
        name=name if not brands else f"{brands} {name}",
        category="食品饮料",
        attributes=attributes,
        sellingPoints=selling_points or ["开放数据库已收录", "可补充包装图和配料信息"],
        targetAudiences=["跨境食品选品运营", "健康零食/饮品买手"],
        usageScenarios=["跨境食品趋势观察", "商品图与配料信息补全", "合规表达复核"],
        forbiddenClaims=["减肥", "燃脂", "治疗", "治愈", "药用"],
    )


async def _store_image_asset(*, source_image_url: str, keyword: str, source_product_id: str) -> dict[str, Any]:
    if not object_storage.configured():
        return {
            "image_url": source_image_url,
            "storage_key": None,
            "storage_status": "source_url",
            "storage_message": "对象存储未配置，保留来源图片 URL",
            "content_type": "",
            "size_bytes": 0,
        }

    try:
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": "ReviewPilot/0.1 image-ingestion"}, follow_redirects=True) as client:
            response = await client.get(source_image_url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if not content_type.lower().startswith("image/"):
                raise ValueError(f"非图片响应：{content_type or 'unknown'}")
            data = response.content
            if len(data) > 5 * 1024 * 1024:
                raise ValueError("图片超过 5MB，已跳过对象存储")

        stored = await asyncio.to_thread(
            object_storage.store_product_image,
            provider_id=OPEN_FOOD_FACTS_PROVIDER_ID,
            keyword=keyword,
            source_product_id=source_product_id,
            data=data,
            content_type=content_type,
        )
        return {
            "image_url": stored.url,
            "storage_key": stored.key,
            "storage_status": "stored",
            "storage_message": "图片已下载并存入 MinIO",
            "content_type": stored.content_type,
            "size_bytes": stored.size,
        }
    except Exception as exc:
        return {
            "image_url": source_image_url,
            "storage_key": None,
            "storage_status": "failed",
            "storage_message": f"MinIO 存储失败，保留来源图片 URL：{exc}",
            "content_type": "",
            "size_bytes": 0,
        }


def _existing_by_source_id() -> dict[str, Product]:
    result: dict[str, Product] = {}
    for product in repository.list_products():
        if product.attributes.get("数据来源") != "Open Food Facts":
            continue
        source_id = product.attributes.get("来源商品ID")
        if source_id:
            result[source_id] = product
    return result


def _item(raw: dict[str, Any], *, status: str, reason: str) -> MarketIngestionItem:
    code = str(raw.get("code") or "").strip()
    return MarketIngestionItem(
        sourceProductId=code or "unknown",
        productName=_clean_text(raw.get("product_name")) or "unknown",
        imageUrl=_clean_text(raw.get("image_front_url")) or _clean_text(raw.get("image_url")) or None,
        sourceImageUrl=_clean_text(raw.get("image_front_url")) or _clean_text(raw.get("image_url")) or None,
        sourceUrl=f"https://world.openfoodfacts.org/product/{code}" if code else None,
        status=status,
        reason=reason,
    )


def _normalize_keyword(value: str) -> str:
    keyword = value.strip().lower()
    return keyword or "coffee"


def _category_tag_for_keyword(keyword: str) -> str:
    if keyword in {"coffee", "instant coffee", "咖啡", "速溶咖啡"}:
        return "en:instant-coffees"
    if keyword in {"tea", "奶茶", "茶"}:
        return "en:teas"
    if keyword in {"chocolate", "巧克力"}:
        return "en:chocolates"
    if keyword in {"snack", "snacks", "零食"}:
        return "en:snacks"
    return ""


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _item_storage_status(product: Product) -> str | None:
    if product.attributes.get("对象存储Key"):
        return "stored"
    if product.attributes.get("商品图片URL"):
        return "source_url"
    return None


def _image_storage_label(value: str | None) -> str:
    if value == "stored":
        return "已存入对象存储"
    if value == "failed":
        return "存储失败，使用来源图片"
    if value == "source_url":
        return "使用来源图片"
    return ""


def _labels(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_label_name(item) for item in value if _label_name(item)]


def _label_name(value: Any) -> str:
    text = str(value or "").strip()
    if ":" in text:
        text = text.split(":", 1)[1]
    return text.replace("-", " ")


def _countries(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    names = [_label_name(item).title() for item in value[:6]]
    return "、".join([name for name in names if name])


def _unique(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        clean = item.strip()
        if clean and clean not in result:
            result.append(clean)
    return result


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _to_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

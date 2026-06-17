from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from app.core.config import settings
from app.core.tenant import current_tenant_id
from app.models.schemas import (
    AuditEvent,
    CreateFeedback,
    CreateProduct,
    DashboardStats,
    Feedback,
    GeneratedContent,
    GenerationConfig,
    GenerationTask,
    MarketIngestionItem,
    MarketIngestionRun,
    Product,
    QualityReport,
    ReviewRecord,
)
from app.utils.ids import new_id


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def init_db() -> None:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
              id TEXT PRIMARY KEY,
              tenant_id TEXT NOT NULL DEFAULT 'local',
              name TEXT NOT NULL,
              category TEXT NOT NULL,
              attributes TEXT NOT NULL,
              selling_points TEXT NOT NULL,
              target_audiences TEXT NOT NULL,
              usage_scenarios TEXT NOT NULL,
              forbidden_claims TEXT NOT NULL,
              brand_voice_id TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS feedbacks (
              id TEXT PRIMARY KEY,
              tenant_id TEXT NOT NULL DEFAULT 'local',
              product_id TEXT NOT NULL,
              product_name TEXT,
              source_type TEXT NOT NULL,
              source_summary TEXT NOT NULL,
              confirmed_facts TEXT NOT NULL,
              subjective_opinions TEXT NOT NULL,
              consent_status TEXT NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS generation_tasks (
              id TEXT PRIMARY KEY,
              tenant_id TEXT NOT NULL DEFAULT 'local',
              product_id TEXT NOT NULL,
              product_name TEXT,
              config TEXT NOT NULL,
              status TEXT NOT NULL,
              message TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS generated_contents (
              id TEXT PRIMARY KEY,
              tenant_id TEXT NOT NULL DEFAULT 'local',
              task_id TEXT NOT NULL,
              text TEXT NOT NULL,
              score INTEGER NOT NULL,
              risk_flags TEXT NOT NULL,
              source_trace TEXT NOT NULL,
              review_status TEXT NOT NULL,
              edited_text TEXT,
              quality_report TEXT NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS review_records (
              id TEXT PRIMARY KEY,
              tenant_id TEXT NOT NULL DEFAULT 'local',
              content_id TEXT NOT NULL,
              action TEXT NOT NULL,
              comment TEXT,
              reviewer TEXT NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS market_ingestion_runs (
              id TEXT PRIMARY KEY,
              tenant_id TEXT NOT NULL DEFAULT 'local',
              provider_id TEXT NOT NULL,
              keyword TEXT NOT NULL,
              status TEXT NOT NULL,
              requested_limit INTEGER NOT NULL,
              created_count INTEGER NOT NULL,
              skipped_count INTEGER NOT NULL,
              items TEXT NOT NULL,
              message TEXT,
              started_at TEXT NOT NULL,
              finished_at TEXT NOT NULL,
              next_allowed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_events (
              id TEXT PRIMARY KEY,
              tenant_id TEXT NOT NULL DEFAULT 'local',
              actor TEXT NOT NULL,
              action TEXT NOT NULL,
              resource_type TEXT NOT NULL,
              resource_id TEXT,
              metadata TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            """
        )
        for table in (
            "products",
            "feedbacks",
            "generation_tasks",
            "generated_contents",
            "review_records",
            "market_ingestion_runs",
            "audit_events",
        ):
            _ensure_column(conn, table, "tenant_id", f"TEXT NOT NULL DEFAULT '{settings.default_tenant_id}'")
        _ensure_column(conn, "generation_tasks", "message", "TEXT")
        _ensure_column(conn, "generation_tasks", "updated_at", "TEXT")
        conn.commit()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def seed_demo() -> None:
    tenant_id = current_tenant_id()
    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM products WHERE tenant_id = ?", (tenant_id,)).fetchone()[0]
        if count:
            return
        products = [
            CreateProduct(
                name="静音破壁料理机 Pro",
                category="厨房电器",
                attributes={
                    "sku": "RP-BLENDER-PRO-WH",
                    "platforms": "temu,tiktok_shop",
                    "temuStatus": "live",
                    "tiktokStatus": "live",
                    "warehouse": "US-West LA 3PL",
                    "warehouseCountry": "US",
                    "availableStock": "18",
                    "reservedStock": "2",
                    "safetyStock": "10",
                    "weeklySales": "32",
                    "rating": "4.7",
                    "reviewCount": "58",
                    "容量": "1.75L",
                    "功率": "1200W",
                    "材质": "高硼硅玻璃杯体",
                    "颜色": "珍珠白",
                },
                sellingPoints=["真静音降噪 42dB", "10叶精钢刀头", "12小时预约", "自清洗功能", "8档变速"],
                targetAudiences=["宝妈家庭", "养生人群", "上班族"],
                usageScenarios=["早餐豆浆", "宝宝辅食", "健身果蔬汁", "养生五谷糊"],
                forbiddenClaims=["治疗", "药用", "最安静", "第一"],
            ),
            CreateProduct(
                name="轻奢纯棉四件套",
                category="家纺",
                attributes={
                    "sku": "RP-BEDDING-COTTON-18",
                    "platforms": "temu",
                    "temuStatus": "live",
                    "warehouse": "US-East NJ 3PL",
                    "warehouseCountry": "US",
                    "availableStock": "7",
                    "reservedStock": "1",
                    "safetyStock": "10",
                    "weeklySales": "18",
                    "rating": "4.6",
                    "reviewCount": "32",
                    "材质": "100%新疆长绒棉",
                    "支数": "60支",
                    "工艺": "缎纹",
                    "尺寸": "1.8m",
                },
                sellingPoints=["60支长绒棉亲肤", "活性印染不褪色", "YKK隐形拉链", "可机洗"],
                targetAudiences=["新婚夫妇", "品质生活人群", "乔迁送礼"],
                usageScenarios=["婚房布置", "卧室升级", "乔迁新居", "换季换新"],
                forbiddenClaims=["防螨", "抗菌", "医用级"],
            ),
            CreateProduct(
                name="儿童护脊书包",
                category="母婴用品",
                attributes={
                    "sku": "RP-SCHOOLBAG-22L",
                    "platforms": "temu,tiktok_shop",
                    "temuStatus": "live",
                    "tiktokStatus": "draft",
                    "warehouse": "UK Midlands 3PL",
                    "warehouseCountry": "UK",
                    "availableStock": "42",
                    "reservedStock": "8",
                    "safetyStock": "12",
                    "weeklySales": "24",
                    "rating": "4.5",
                    "reviewCount": "41",
                    "适用年级": "1-6年级",
                    "容量": "22L",
                    "重量": "0.75kg",
                    "材质": "防泼水牛津布",
                },
                sellingPoints=["S型减压肩带", "3D护脊背板", "反光条设计", "多隔层收纳", "可调节胸扣"],
                targetAudiences=["小学生家长", "开学季采购"],
                usageScenarios=["日常上学", "课外补习", "短途旅行"],
                forbiddenClaims=["矫正脊柱", "治疗驼背", "医用"],
            ),
            CreateProduct(
                name="冻干咖啡礼盒",
                category="食品饮料",
                attributes={
                    "sku": "RP-COFFEE-FD-20",
                    "platforms": "temu",
                    "temuStatus": "reviewing",
                    "warehouse": "US-West LA 3PL",
                    "warehouseCountry": "US",
                    "availableStock": "4",
                    "reservedStock": "0",
                    "safetyStock": "10",
                    "weeklySales": "9",
                    "rating": "4.2",
                    "reviewCount": "9",
                    "规格": "3g×20颗",
                    "产地": "云南保山",
                    "工艺": "低温冻干",
                    "烘焙": "中深烘",
                },
                sellingPoints=["冷热双溶 3秒速溶", "SCA 80+精品级", "0蔗糖0添加", "独立氮气锁鲜"],
                targetAudiences=["咖啡爱好者", "上班族", "健身人群"],
                usageScenarios=["办公室下午茶", "居家手冲替代", "户外露营"],
                forbiddenClaims=["减肥", "燃脂", "治病"],
            ),
            CreateProduct(
                name="智能体脂秤 S3",
                category="健康设备",
                attributes={
                    "sku": "RP-SCALE-S3-BK",
                    "platforms": "temu,tiktok_shop",
                    "temuStatus": "live",
                    "tiktokStatus": "reviewing",
                    "warehouse": "US-East NJ 3PL",
                    "warehouseCountry": "US",
                    "availableStock": "29",
                    "reservedStock": "5",
                    "safetyStock": "10",
                    "weeklySales": "14",
                    "rating": "4.4",
                    "reviewCount": "18",
                    "测量指标": "18项",
                    "精度": "50g",
                    "材质": "钢化玻璃面板",
                    "连接": "蓝牙+WiFi",
                },
                sellingPoints=["18项身体指标", "全家成员管理", "趋势图表分析", "IPX5防水"],
                targetAudiences=["健身人群", "减脂人群", "健康管理"],
                usageScenarios=["每日晨起称重", "减脂期追踪", "家庭健康管理"],
                forbiddenClaims=["医用精度", "诊断", "治疗"],
            ),
        ]
        created = [create_product(item, conn=conn) for item in products]
        feedbacks = [
            CreateFeedback(
                productId=created[0].id,
                sourceType="customer_review",
                sourceSummary="客户反馈打豆浆确实比之前的老机器安静很多，预约功能很方便，晚上设置好早上就能喝到热豆浆。清洗也方便，自清洗功能省了不少事。",
                confirmedFacts=["预约功能可正常使用", "自清洗功能可用", "可打豆浆"],
                subjectiveOpinions=["比老机器安静", "方便", "省事"],
            ),
            CreateFeedback(
                productId=created[0].id,
                sourceType="cs_summary",
                sourceSummary="客服回访记录：客户表示买来主要给宝宝做辅食，南瓜泥、胡萝卜泥打得非常细腻，没有颗粒感。",
                confirmedFacts=["可制作辅食", "南瓜泥细腻"],
                subjectiveOpinions=["非常细腻", "没有颗粒感"],
            ),
            CreateFeedback(
                productId=created[1].id,
                sourceType="customer_review",
                sourceSummary="收到后打开没有异味，面料摸起来很舒服，洗了之后没有缩水也没有褪色，颜色和图片一致。",
                confirmedFacts=["无异味", "洗后不缩水", "洗后不褪色", "颜色与图片一致"],
                subjectiveOpinions=["面料舒服", "好看", "有质感"],
            ),
            CreateFeedback(
                productId=created[2].id,
                sourceType="customer_review",
                sourceSummary="孩子开学用了一个学期，书包自重很轻，肩带宽厚不会勒肩膀。分隔多，孩子自己就能整理好书本文具。",
                confirmedFacts=["自重轻", "肩带宽厚", "多分隔", "有反光条"],
                subjectiveOpinions=["不会勒肩膀", "孩子能自己整理"],
            ),
        ]
        for item in feedbacks:
            create_feedback(item, conn=conn)
        conn.commit()


def create_product(payload: CreateProduct, conn: sqlite3.Connection | None = None) -> Product:
    tenant_id = current_tenant_id()
    product_id = new_id("prod")
    ts = now_iso()
    values = (
        product_id,
        tenant_id,
        payload.name.strip(),
        payload.category.strip(),
        _json(payload.attributes),
        _json(_clean(payload.sellingPoints)),
        _json(_clean(payload.targetAudiences)),
        _json(_clean(payload.usageScenarios)),
        _json(_clean(payload.forbiddenClaims)),
        payload.brandVoiceId,
        ts,
        ts,
    )
    owns_conn = conn is None
    if conn is None:
        conn = sqlite3.connect(settings.db_path)
    conn.execute(
        """
        INSERT INTO products
        (id, tenant_id, name, category, attributes, selling_points, target_audiences, usage_scenarios, forbidden_claims, brand_voice_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        values,
    )
    if owns_conn:
        conn.commit()
        conn.close()
        return get_product(product_id)
    return Product(
        id=product_id,
        tenantId=tenant_id,
        name=payload.name.strip(),
        category=payload.category.strip(),
        attributes=payload.attributes,
        sellingPoints=_clean(payload.sellingPoints),
        targetAudiences=_clean(payload.targetAudiences),
        usageScenarios=_clean(payload.usageScenarios),
        forbiddenClaims=_clean(payload.forbiddenClaims),
        brandVoiceId=payload.brandVoiceId,
        createdAt=ts,
        updatedAt=ts,
    )


def list_products() -> list[Product]:
    tenant_id = current_tenant_id()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM products WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,)).fetchall()
    return [_product(row) for row in rows]


def get_product(product_id: str) -> Product:
    tenant_id = current_tenant_id()
    with connect() as conn:
        row = conn.execute("SELECT * FROM products WHERE id = ? AND tenant_id = ?", (product_id, tenant_id)).fetchone()
    if not row:
        raise KeyError("product not found")
    return _product(row)


def create_feedback(payload: CreateFeedback, conn: sqlite3.Connection | None = None) -> Feedback:
    tenant_id = current_tenant_id()
    product = _get_product_with_conn(payload.productId, conn) if conn is not None else get_product(payload.productId)
    feedback_id = new_id("fb")
    ts = now_iso()
    values = (
        feedback_id,
        tenant_id,
        product.id,
        product.name,
        payload.sourceType,
        payload.sourceSummary.strip(),
        _json(_clean(payload.confirmedFacts)),
        _json(_clean(payload.subjectiveOpinions)),
        payload.consentStatus,
        ts,
    )
    owns_conn = conn is None
    if conn is None:
        conn = sqlite3.connect(settings.db_path)
    conn.execute(
        """
        INSERT INTO feedbacks
        (id, tenant_id, product_id, product_name, source_type, source_summary, confirmed_facts, subjective_opinions, consent_status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        values,
    )
    if owns_conn:
        conn.commit()
        conn.close()
        return get_feedback(feedback_id)
    return Feedback(
        id=feedback_id,
        tenantId=tenant_id,
        productId=product.id,
        productName=product.name,
        sourceType=payload.sourceType,
        sourceSummary=payload.sourceSummary.strip(),
        confirmedFacts=_clean(payload.confirmedFacts),
        subjectiveOpinions=_clean(payload.subjectiveOpinions),
        consentStatus=payload.consentStatus,
        createdAt=ts,
    )


def _get_product_with_conn(product_id: str, conn: sqlite3.Connection) -> Product:
    row = conn.execute("SELECT * FROM products WHERE id = ? AND tenant_id = ?", (product_id, current_tenant_id())).fetchone()
    if not row:
        raise KeyError("product not found")
    return _product(row)


def list_feedback(product_id: str | None = None) -> list[Feedback]:
    tenant_id = current_tenant_id()
    with connect() as conn:
        if product_id:
            rows = conn.execute(
                "SELECT * FROM feedbacks WHERE tenant_id = ? AND product_id = ? ORDER BY created_at DESC",
                (tenant_id, product_id),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM feedbacks WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,)).fetchall()
    return [_feedback(row) for row in rows]


def get_feedback(feedback_id: str) -> Feedback:
    tenant_id = current_tenant_id()
    with connect() as conn:
        row = conn.execute("SELECT * FROM feedbacks WHERE id = ? AND tenant_id = ?", (feedback_id, tenant_id)).fetchone()
    if not row:
        raise KeyError("feedback not found")
    return _feedback(row)


def create_generation_task(config: GenerationConfig, contents: list[GeneratedContent], product: Product) -> GenerationTask:
    tenant_id = current_tenant_id()
    task_id = contents[0].taskId if contents else new_id("task")
    ts = now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO generation_tasks (id, tenant_id, product_id, product_name, config, status, message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (task_id, tenant_id, product.id, product.name, config.model_dump_json(), "completed", None, ts, ts),
        )
        _insert_generated_contents(conn, contents)
        conn.commit()
    return GenerationTask(
        id=task_id,
        tenantId=tenant_id,
        productId=product.id,
        productName=product.name,
        config=config,
        status="completed",
        contents=contents,
        createdAt=ts,
        updatedAt=ts,
    )


def create_generation_task_pending(config: GenerationConfig, product: Product) -> GenerationTask:
    tenant_id = current_tenant_id()
    task_id = new_id("task")
    ts = now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO generation_tasks (id, tenant_id, product_id, product_name, config, status, message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (task_id, tenant_id, product.id, product.name, config.model_dump_json(), "pending", "queued", ts, ts),
        )
        conn.commit()
    return GenerationTask(
        id=task_id,
        tenantId=tenant_id,
        productId=product.id,
        productName=product.name,
        config=config,
        status="pending",
        message="queued",
        contents=[],
        createdAt=ts,
        updatedAt=ts,
    )


def update_generation_task_status(task_id: str, status: str, message: str | None = None) -> GenerationTask:
    tenant_id = current_tenant_id()
    ts = now_iso()
    with connect() as conn:
        row = conn.execute("SELECT * FROM generation_tasks WHERE id = ? AND tenant_id = ?", (task_id, tenant_id)).fetchone()
        if not row:
            raise KeyError("generation task not found")
        conn.execute(
            "UPDATE generation_tasks SET status = ?, message = ?, updated_at = ? WHERE id = ? AND tenant_id = ?",
            (status, message, ts, task_id, tenant_id),
        )
        conn.commit()
    return get_generation_task(task_id)


def complete_generation_task(task_id: str, contents: list[GeneratedContent]) -> GenerationTask:
    tenant_id = current_tenant_id()
    ts = now_iso()
    with connect() as conn:
        row = conn.execute("SELECT * FROM generation_tasks WHERE id = ? AND tenant_id = ?", (task_id, tenant_id)).fetchone()
        if not row:
            raise KeyError("generation task not found")
        conn.execute("DELETE FROM generated_contents WHERE task_id = ? AND tenant_id = ?", (task_id, tenant_id))
        _insert_generated_contents(conn, contents)
        conn.execute(
            "UPDATE generation_tasks SET status = ?, message = ?, updated_at = ? WHERE id = ? AND tenant_id = ?",
            ("completed", None, ts, task_id, tenant_id),
        )
        conn.commit()
    return get_generation_task(task_id)


def fail_generation_task(task_id: str, message: str) -> GenerationTask:
    return update_generation_task_status(task_id, "failed", message[:500])


def fail_stale_generation_tasks(timeout_seconds: int) -> list[GenerationTask]:
    tenant_id = current_tenant_id()
    cutoff = (
        datetime.now(timezone.utc) - timedelta(seconds=max(1, timeout_seconds))
    ).isoformat().replace("+00:00", "Z")
    message = f"generation task recovered as failed after {max(1, timeout_seconds)}s timeout"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM generation_tasks
            WHERE tenant_id = ?
              AND status IN ('pending', 'generating')
              AND COALESCE(updated_at, created_at) < ?
            ORDER BY created_at ASC
            """,
            (tenant_id, cutoff),
        ).fetchall()
        task_ids = [row["id"] for row in rows]
        for task_id in task_ids:
            conn.execute(
                "UPDATE generation_tasks SET status = ?, message = ?, updated_at = ? WHERE id = ? AND tenant_id = ?",
                ("failed", message, now_iso(), task_id, tenant_id),
            )
        conn.commit()
    return [get_generation_task(task_id) for task_id in task_ids]


def generation_task_status_counts() -> dict[str, int]:
    tenant_id = current_tenant_id()
    with connect() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS count FROM generation_tasks WHERE tenant_id = ? GROUP BY status",
            (tenant_id,),
        ).fetchall()
    counts = {"pending": 0, "generating": 0, "completed": 0, "failed": 0}
    for row in rows:
        counts[str(row["status"])] = int(row["count"])
    return counts


def stale_generation_task_count(timeout_seconds: int) -> int:
    tenant_id = current_tenant_id()
    cutoff = (
        datetime.now(timezone.utc) - timedelta(seconds=max(1, timeout_seconds))
    ).isoformat().replace("+00:00", "Z")
    with connect() as conn:
        return int(
            conn.execute(
                """
                SELECT COUNT(*) FROM generation_tasks
                WHERE tenant_id = ?
                  AND status IN ('pending', 'generating')
                  AND COALESCE(updated_at, created_at) < ?
                """,
                (tenant_id, cutoff),
            ).fetchone()[0]
        )


def _insert_generated_contents(conn: sqlite3.Connection, contents: list[GeneratedContent]) -> None:
    tenant_id = current_tenant_id()
    for content in contents:
        conn.execute(
            """
            INSERT INTO generated_contents
            (id, tenant_id, task_id, text, score, risk_flags, source_trace, review_status, edited_text, quality_report, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                content.id,
                tenant_id,
                content.taskId,
                content.text,
                content.score,
                _json(content.riskFlags),
                _json(content.sourceTrace),
                content.reviewStatus,
                content.editedText,
                content.qualityReport.model_dump_json(),
                content.createdAt,
            ),
        )


def list_generation_tasks() -> list[GenerationTask]:
    tenant_id = current_tenant_id()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM generation_tasks WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,)).fetchall()
    return [_task(row) for row in rows]


def get_generation_task(task_id: str) -> GenerationTask:
    tenant_id = current_tenant_id()
    with connect() as conn:
        row = conn.execute("SELECT * FROM generation_tasks WHERE id = ? AND tenant_id = ?", (task_id, tenant_id)).fetchone()
    if not row:
        raise KeyError("generation task not found")
    return _task(row)


def list_contents(status: str | None = None, task_id: str | None = None) -> list[GeneratedContent]:
    where = ["tenant_id = ?"]
    params: list[Any] = [current_tenant_id()]
    if status:
        where.append("review_status = ?")
        params.append(status)
    if task_id:
        where.append("task_id = ?")
        params.append(task_id)
    sql = "SELECT * FROM generated_contents"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_content(row) for row in rows]


def get_content(content_id: str) -> GeneratedContent:
    tenant_id = current_tenant_id()
    with connect() as conn:
        row = conn.execute("SELECT * FROM generated_contents WHERE id = ? AND tenant_id = ?", (content_id, tenant_id)).fetchone()
    if not row:
        raise KeyError("content not found")
    return _content(row)


def review_content(content_id: str, status: str, action: str, reviewer: str, comment: str | None = None, edited_text: str | None = None) -> GeneratedContent:
    tenant_id = current_tenant_id()
    ts = now_iso()
    with connect() as conn:
        row = conn.execute("SELECT * FROM generated_contents WHERE id = ? AND tenant_id = ?", (content_id, tenant_id)).fetchone()
        if not row:
            raise KeyError("content not found")
        conn.execute(
            "UPDATE generated_contents SET review_status = ?, edited_text = COALESCE(?, edited_text) WHERE id = ? AND tenant_id = ?",
            (status, edited_text, content_id, tenant_id),
        )
        conn.execute(
            "INSERT INTO review_records (id, tenant_id, content_id, action, comment, reviewer, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (new_id("review"), tenant_id, content_id, action, comment, reviewer, ts),
        )
        conn.commit()
    return get_content(content_id)


def create_audit_event(
    *,
    actor: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    tenant_id = current_tenant_id()
    event_id = new_id("audit")
    ts = now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO audit_events (id, tenant_id, actor, action, resource_type, resource_id, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                tenant_id,
                actor.strip() or "system",
                action.strip(),
                resource_type.strip(),
                resource_id,
                _json(metadata or {}),
                ts,
            ),
        )
        conn.commit()
    return AuditEvent(
        id=event_id,
        tenantId=tenant_id,
        actor=actor.strip() or "system",
        action=action.strip(),
        resourceType=resource_type.strip(),
        resourceId=resource_id,
        metadata=metadata or {},
        createdAt=ts,
    )


def list_audit_events(limit: int = 50) -> list[AuditEvent]:
    tenant_id = current_tenant_id()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_events WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?",
            (tenant_id, max(1, min(200, limit))),
        ).fetchall()
    return [_audit_event(row) for row in rows]


def dashboard_stats() -> DashboardStats:
    tenant_id = current_tenant_id()
    with connect() as conn:
        total_products = conn.execute("SELECT COUNT(*) FROM products WHERE tenant_id = ?", (tenant_id,)).fetchone()[0]
        total_feedbacks = conn.execute("SELECT COUNT(*) FROM feedbacks WHERE tenant_id = ?", (tenant_id,)).fetchone()[0]
        total_generations = conn.execute("SELECT COUNT(*) FROM generated_contents WHERE tenant_id = ?", (tenant_id,)).fetchone()[0]
        pending_reviews = conn.execute(
            "SELECT COUNT(*) FROM generated_contents WHERE tenant_id = ? AND review_status = 'pending'",
            (tenant_id,),
        ).fetchone()[0]
        approved_today = conn.execute(
            "SELECT COUNT(*) FROM review_records WHERE tenant_id = ? AND action = 'approved' AND created_at >= ?",
            (tenant_id, _today_start()),
        ).fetchone()[0]
        avg_score = conn.execute("SELECT AVG(score) FROM generated_contents WHERE tenant_id = ?", (tenant_id,)).fetchone()[0] or 0
        risk_intercepted = conn.execute(
            "SELECT COUNT(*) FROM generated_contents WHERE tenant_id = ? AND risk_flags <> '[]'",
            (tenant_id,),
        ).fetchone()[0]
        weekly = []
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6)
        for index in range(7):
            day = start + timedelta(days=index)
            next_day = day + timedelta(days=1)
            weekly.append(
                conn.execute(
                    "SELECT COUNT(*) FROM generated_contents WHERE tenant_id = ? AND created_at >= ? AND created_at < ?",
                    (tenant_id, day.isoformat().replace("+00:00", "Z"), next_day.isoformat().replace("+00:00", "Z")),
                ).fetchone()[0]
            )
    return DashboardStats(
        totalProducts=total_products,
        totalFeedbacks=total_feedbacks,
        totalGenerations=total_generations,
        pendingReviews=pending_reviews,
        approvedToday=approved_today,
        averageScore=round(float(avg_score), 1),
        riskIntercepted=risk_intercepted,
        weeklyGenerations=weekly,
    )


def last_market_ingestion_run(provider_id: str, keyword: str) -> MarketIngestionRun | None:
    tenant_id = current_tenant_id()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM market_ingestion_runs
            WHERE tenant_id = ? AND provider_id = ? AND keyword = ?
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (tenant_id, provider_id, keyword.strip().lower()),
        ).fetchone()
    return _market_ingestion_run(row) if row else None


def list_market_ingestion_runs(limit: int = 20) -> list[MarketIngestionRun]:
    tenant_id = current_tenant_id()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM market_ingestion_runs WHERE tenant_id = ? ORDER BY started_at DESC LIMIT ?",
            (tenant_id, max(1, min(100, limit))),
        ).fetchall()
    return [_market_ingestion_run(row) for row in rows]


def create_market_ingestion_run(
    *,
    provider_id: str,
    keyword: str,
    status: str,
    requested_limit: int,
    created_count: int,
    skipped_count: int,
    items: list[MarketIngestionItem],
    message: str | None,
    started_at: str,
    finished_at: str,
    next_allowed_at: str | None,
) -> MarketIngestionRun:
    tenant_id = current_tenant_id()
    run_id = new_id("ingest")
    normalized_keyword = keyword.strip().lower()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO market_ingestion_runs
            (id, tenant_id, provider_id, keyword, status, requested_limit, created_count, skipped_count, items, message, started_at, finished_at, next_allowed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                tenant_id,
                provider_id,
                normalized_keyword,
                status,
                requested_limit,
                created_count,
                skipped_count,
                _json([item.model_dump() for item in items]),
                message,
                started_at,
                finished_at,
                next_allowed_at,
            ),
        )
        conn.commit()
    return MarketIngestionRun(
        id=run_id,
        tenantId=tenant_id,
        providerId=provider_id,
        keyword=normalized_keyword,
        status=status,
        requestedLimit=requested_limit,
        createdCount=created_count,
        skippedCount=skipped_count,
        items=items,
        message=message,
        startedAt=started_at,
        finishedAt=finished_at,
        nextAllowedAt=next_allowed_at,
    )


def _task(row: sqlite3.Row) -> GenerationTask:
    contents = list_contents(task_id=row["id"])
    return GenerationTask(
        id=row["id"],
        tenantId=row["tenant_id"],
        productId=row["product_id"],
        productName=row["product_name"],
        config=GenerationConfig.model_validate_json(row["config"]),
        status=row["status"],
        message=row["message"],
        contents=contents,
        createdAt=row["created_at"],
        updatedAt=row["updated_at"] or row["created_at"],
    )


def _product(row: sqlite3.Row) -> Product:
    return Product(
        id=row["id"],
        tenantId=row["tenant_id"],
        name=row["name"],
        category=row["category"],
        attributes=_loads(row["attributes"], {}),
        sellingPoints=_loads(row["selling_points"], []),
        targetAudiences=_loads(row["target_audiences"], []),
        usageScenarios=_loads(row["usage_scenarios"], []),
        forbiddenClaims=_loads(row["forbidden_claims"], []),
        brandVoiceId=row["brand_voice_id"],
        createdAt=row["created_at"],
        updatedAt=row["updated_at"],
    )


def _feedback(row: sqlite3.Row) -> Feedback:
    return Feedback(
        id=row["id"],
        tenantId=row["tenant_id"],
        productId=row["product_id"],
        productName=row["product_name"],
        sourceType=row["source_type"],
        sourceSummary=row["source_summary"],
        confirmedFacts=_loads(row["confirmed_facts"], []),
        subjectiveOpinions=_loads(row["subjective_opinions"], []),
        consentStatus=row["consent_status"],
        createdAt=row["created_at"],
    )


def _content(row: sqlite3.Row) -> GeneratedContent:
    return GeneratedContent(
        id=row["id"],
        tenantId=row["tenant_id"],
        taskId=row["task_id"],
        text=row["text"],
        score=row["score"],
        riskFlags=_loads(row["risk_flags"], []),
        sourceTrace=_loads(row["source_trace"], []),
        reviewStatus=row["review_status"],
        editedText=row["edited_text"],
        qualityReport=QualityReport.model_validate(_loads(row["quality_report"], {})),
        createdAt=row["created_at"],
    )


def _market_ingestion_run(row: sqlite3.Row) -> MarketIngestionRun:
    return MarketIngestionRun(
        id=row["id"],
        tenantId=row["tenant_id"],
        providerId=row["provider_id"],
        keyword=row["keyword"],
        status=row["status"],
        requestedLimit=row["requested_limit"],
        createdCount=row["created_count"],
        skippedCount=row["skipped_count"],
        items=[MarketIngestionItem.model_validate(item) for item in _loads(row["items"], [])],
        message=row["message"],
        startedAt=row["started_at"],
        finishedAt=row["finished_at"],
        nextAllowedAt=row["next_allowed_at"],
    )


def _audit_event(row: sqlite3.Row) -> AuditEvent:
    return AuditEvent(
        id=row["id"],
        tenantId=row["tenant_id"],
        actor=row["actor"],
        action=row["action"],
        resourceType=row["resource_type"],
        resourceId=row["resource_id"],
        metadata=_loads(row["metadata"], {}),
        createdAt=row["created_at"],
    )


def _clean(items: list[str]) -> list[str]:
    return [item.strip() for item in items if item and item.strip()]


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _loads(value: str, fallback: Any) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _today_start() -> str:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")

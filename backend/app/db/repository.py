from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from app.core.config import settings
from app.models.schemas import (
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
              product_id TEXT NOT NULL,
              product_name TEXT,
              config TEXT NOT NULL,
              status TEXT NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS generated_contents (
              id TEXT PRIMARY KEY,
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
              content_id TEXT NOT NULL,
              action TEXT NOT NULL,
              comment TEXT,
              reviewer TEXT NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS market_ingestion_runs (
              id TEXT PRIMARY KEY,
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
            """
        )
        conn.commit()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def seed_demo() -> None:
    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count:
            return
        products = [
            CreateProduct(
                name="静音破壁料理机 Pro",
                category="厨房电器",
                attributes={"容量": "1.75L", "功率": "1200W", "材质": "高硼硅玻璃杯体", "颜色": "珍珠白"},
                sellingPoints=["真静音降噪 42dB", "10叶精钢刀头", "12小时预约", "自清洗功能", "8档变速"],
                targetAudiences=["宝妈家庭", "养生人群", "上班族"],
                usageScenarios=["早餐豆浆", "宝宝辅食", "健身果蔬汁", "养生五谷糊"],
                forbiddenClaims=["治疗", "药用", "最安静", "第一"],
            ),
            CreateProduct(
                name="轻奢纯棉四件套",
                category="家纺",
                attributes={"材质": "100%新疆长绒棉", "支数": "60支", "工艺": "缎纹", "尺寸": "1.8m"},
                sellingPoints=["60支长绒棉亲肤", "活性印染不褪色", "YKK隐形拉链", "可机洗"],
                targetAudiences=["新婚夫妇", "品质生活人群", "乔迁送礼"],
                usageScenarios=["婚房布置", "卧室升级", "乔迁新居", "换季换新"],
                forbiddenClaims=["防螨", "抗菌", "医用级"],
            ),
            CreateProduct(
                name="儿童护脊书包",
                category="母婴用品",
                attributes={"适用年级": "1-6年级", "容量": "22L", "重量": "0.75kg", "材质": "防泼水牛津布"},
                sellingPoints=["S型减压肩带", "3D护脊背板", "反光条设计", "多隔层收纳", "可调节胸扣"],
                targetAudiences=["小学生家长", "开学季采购"],
                usageScenarios=["日常上学", "课外补习", "短途旅行"],
                forbiddenClaims=["矫正脊柱", "治疗驼背", "医用"],
            ),
            CreateProduct(
                name="冻干咖啡礼盒",
                category="食品饮料",
                attributes={"规格": "3g×20颗", "产地": "云南保山", "工艺": "低温冻干", "烘焙": "中深烘"},
                sellingPoints=["冷热双溶 3秒速溶", "SCA 80+精品级", "0蔗糖0添加", "独立氮气锁鲜"],
                targetAudiences=["咖啡爱好者", "上班族", "健身人群"],
                usageScenarios=["办公室下午茶", "居家手冲替代", "户外露营"],
                forbiddenClaims=["减肥", "燃脂", "治病"],
            ),
            CreateProduct(
                name="智能体脂秤 S3",
                category="健康设备",
                attributes={"测量指标": "18项", "精度": "50g", "材质": "钢化玻璃面板", "连接": "蓝牙+WiFi"},
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
    product_id = new_id("prod")
    ts = now_iso()
    values = (
        product_id,
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
        (id, name, category, attributes, selling_points, target_audiences, usage_scenarios, forbidden_claims, brand_voice_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        values,
    )
    if owns_conn:
        conn.commit()
        conn.close()
        return get_product(product_id)
    return Product(
        id=product_id,
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
    with connect() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
    return [_product(row) for row in rows]


def get_product(product_id: str) -> Product:
    with connect() as conn:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not row:
        raise KeyError("product not found")
    return _product(row)


def create_feedback(payload: CreateFeedback, conn: sqlite3.Connection | None = None) -> Feedback:
    product = _get_product_with_conn(payload.productId, conn) if conn is not None else get_product(payload.productId)
    feedback_id = new_id("fb")
    ts = now_iso()
    values = (
        feedback_id,
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
        (id, product_id, product_name, source_type, source_summary, confirmed_facts, subjective_opinions, consent_status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        values,
    )
    if owns_conn:
        conn.commit()
        conn.close()
        return get_feedback(feedback_id)
    return Feedback(
        id=feedback_id,
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
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not row:
        raise KeyError("product not found")
    return _product(row)


def list_feedback(product_id: str | None = None) -> list[Feedback]:
    with connect() as conn:
        if product_id:
            rows = conn.execute("SELECT * FROM feedbacks WHERE product_id = ? ORDER BY created_at DESC", (product_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM feedbacks ORDER BY created_at DESC").fetchall()
    return [_feedback(row) for row in rows]


def get_feedback(feedback_id: str) -> Feedback:
    with connect() as conn:
        row = conn.execute("SELECT * FROM feedbacks WHERE id = ?", (feedback_id,)).fetchone()
    if not row:
        raise KeyError("feedback not found")
    return _feedback(row)


def create_generation_task(config: GenerationConfig, contents: list[GeneratedContent], product: Product) -> GenerationTask:
    task_id = contents[0].taskId if contents else new_id("task")
    ts = now_iso()
    with connect() as conn:
        conn.execute(
            "INSERT INTO generation_tasks (id, product_id, product_name, config, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (task_id, product.id, product.name, config.model_dump_json(), "completed", ts),
        )
        for content in contents:
            conn.execute(
                """
                INSERT INTO generated_contents
                (id, task_id, text, score, risk_flags, source_trace, review_status, edited_text, quality_report, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content.id,
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
        conn.commit()
    return GenerationTask(id=task_id, productId=product.id, productName=product.name, config=config, status="completed", contents=contents, createdAt=ts)


def list_generation_tasks() -> list[GenerationTask]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM generation_tasks ORDER BY created_at DESC").fetchall()
    return [_task(row) for row in rows]


def get_generation_task(task_id: str) -> GenerationTask:
    with connect() as conn:
        row = conn.execute("SELECT * FROM generation_tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        raise KeyError("generation task not found")
    return _task(row)


def list_contents(status: str | None = None, task_id: str | None = None) -> list[GeneratedContent]:
    where = []
    params: list[Any] = []
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
    with connect() as conn:
        row = conn.execute("SELECT * FROM generated_contents WHERE id = ?", (content_id,)).fetchone()
    if not row:
        raise KeyError("content not found")
    return _content(row)


def review_content(content_id: str, status: str, action: str, reviewer: str, comment: str | None = None, edited_text: str | None = None) -> GeneratedContent:
    ts = now_iso()
    with connect() as conn:
        row = conn.execute("SELECT * FROM generated_contents WHERE id = ?", (content_id,)).fetchone()
        if not row:
            raise KeyError("content not found")
        conn.execute(
            "UPDATE generated_contents SET review_status = ?, edited_text = COALESCE(?, edited_text) WHERE id = ?",
            (status, edited_text, content_id),
        )
        conn.execute(
            "INSERT INTO review_records (id, content_id, action, comment, reviewer, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (new_id("review"), content_id, action, comment, reviewer, ts),
        )
        conn.commit()
    return get_content(content_id)


def dashboard_stats() -> DashboardStats:
    with connect() as conn:
        total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        total_feedbacks = conn.execute("SELECT COUNT(*) FROM feedbacks").fetchone()[0]
        total_generations = conn.execute("SELECT COUNT(*) FROM generated_contents").fetchone()[0]
        pending_reviews = conn.execute("SELECT COUNT(*) FROM generated_contents WHERE review_status = 'pending'").fetchone()[0]
        approved_today = conn.execute(
            "SELECT COUNT(*) FROM review_records WHERE action = 'approved' AND created_at >= ?",
            (_today_start(),),
        ).fetchone()[0]
        avg_score = conn.execute("SELECT AVG(score) FROM generated_contents").fetchone()[0] or 0
        risk_intercepted = conn.execute("SELECT COUNT(*) FROM generated_contents WHERE risk_flags <> '[]'").fetchone()[0]
        weekly = []
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6)
        for index in range(7):
            day = start + timedelta(days=index)
            next_day = day + timedelta(days=1)
            weekly.append(
                conn.execute(
                    "SELECT COUNT(*) FROM generated_contents WHERE created_at >= ? AND created_at < ?",
                    (day.isoformat().replace("+00:00", "Z"), next_day.isoformat().replace("+00:00", "Z")),
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
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM market_ingestion_runs
            WHERE provider_id = ? AND keyword = ?
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (provider_id, keyword.strip().lower()),
        ).fetchone()
    return _market_ingestion_run(row) if row else None


def list_market_ingestion_runs(limit: int = 20) -> list[MarketIngestionRun]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM market_ingestion_runs ORDER BY started_at DESC LIMIT ?",
            (max(1, min(100, limit)),),
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
    run_id = new_id("ingest")
    normalized_keyword = keyword.strip().lower()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO market_ingestion_runs
            (id, provider_id, keyword, status, requested_limit, created_count, skipped_count, items, message, started_at, finished_at, next_allowed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
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
        productId=row["product_id"],
        productName=row["product_name"],
        config=GenerationConfig.model_validate_json(row["config"]),
        status=row["status"],
        contents=contents,
        createdAt=row["created_at"],
    )


def _product(row: sqlite3.Row) -> Product:
    return Product(
        id=row["id"],
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

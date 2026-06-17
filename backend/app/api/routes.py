from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response

from app.agents.review_generation import run_generation_agent
from app.core.config import settings
from app.core.tenant import current_tenant_id, tenant_context
from app.db import repository
from app.models.schemas import CreateFeedback, CreateProduct, GenerationConfig, MarketIngestionRequest, OrganizeFeedbackRequest, ReviewRequest
from app.services.market_ingestion import ingest_open_food_facts
from app.services import object_storage
from app.services.business_overview import build_business_overview
from app.services.commerce_overview import build_commerce_overview
from app.services.feedback_organizer import organize_feedback
from app.services.llm import LLMError, LLMUnavailableError, llm_client
from app.services.observability import runtime_metrics
from app.services.platform_rules import all_platform_rules
from app.services.product_sourcing import all_research_providers, build_opportunity_report, build_opportunity_reports
from app.services.readiness import build_readiness_report

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "time": repository.now_iso()}


@router.get("/llm/config")
async def llm_config() -> dict:
    return {
        "configured": settings.llm.configured,
        "model": settings.llm.model,
        "provider": settings.llm.provider,
        "baseUrl": settings.llm.base_url,
        "timeoutSeconds": settings.llm.timeout_seconds,
        "connectTimeoutSeconds": settings.llm.connect_timeout_seconds,
    }


@router.get("/llm/health")
async def llm_health() -> dict:
    return await llm_client.health()


@router.get("/readiness")
async def readiness() -> dict:
    return await build_readiness_report()


@router.get("/metrics")
async def metrics() -> dict:
    return {
        **runtime_metrics.snapshot(),
        "generationTaskStatusCounts": repository.generation_task_status_counts(),
    }


@router.get("/storage/status")
async def storage_status() -> dict:
    return object_storage.status()


@router.api_route("/assets/{object_key:path}", methods=["GET", "HEAD"])
async def get_asset(object_key: str, request: Request):
    try:
        asset = object_storage.read_object(object_key)
    except object_storage.ObjectStorageError as exc:
        status_code = 404 if object_storage.configured() else 503
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    return Response(
        content=b"" if request.method == "HEAD" else asset.data,
        media_type=asset.content_type,
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Length": str(len(asset.data)),
        },
    )


@router.get("/rules/platforms")
async def platform_rules():
    return all_platform_rules()


@router.get("/product-sourcing/providers")
async def product_sourcing_providers():
    return all_research_providers()


@router.get("/product-sourcing/reports")
async def product_sourcing_reports():
    return build_opportunity_reports(
        products=repository.list_products(),
        feedbacks=repository.list_feedback(),
        tasks=repository.list_generation_tasks(),
        contents=repository.list_contents(),
    )


@router.get("/product-sourcing/reports/{product_id}")
async def product_sourcing_report(product_id: str):
    try:
        product = repository.get_product(product_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="product not found") from exc
    return build_opportunity_report(
        product=product,
        feedbacks=repository.list_feedback(product_id),
        contents=[
            content
            for task in repository.list_generation_tasks()
            if task.productId == product_id
            for content in task.contents
        ],
    )


@router.get("/product-sourcing/ingestion-runs")
async def product_sourcing_ingestion_runs(limit: int = Query(default=20, ge=1, le=100)):
    return repository.list_market_ingestion_runs(limit)


@router.post("/product-sourcing/ingest/open-food-facts")
async def product_sourcing_ingest_open_food_facts(payload: MarketIngestionRequest):
    return await ingest_open_food_facts(payload)


@router.get("/dashboard")
async def dashboard():
    return repository.dashboard_stats()


@router.get("/business/overview")
async def business_overview():
    return build_business_overview(
        products=repository.list_products(),
        feedbacks=repository.list_feedback(),
        tasks=repository.list_generation_tasks(),
        contents=repository.list_contents(),
    )


@router.get("/commerce/overview")
async def commerce_overview():
    return build_commerce_overview(
        products=repository.list_products(),
        feedbacks=repository.list_feedback(),
        contents=repository.list_contents(),
    )


@router.get("/audit/events")
async def audit_events(limit: int = Query(default=50, ge=1, le=200)):
    return repository.list_audit_events(limit)


@router.get("/products")
async def list_products():
    return repository.list_products()


@router.post("/products", status_code=201)
async def create_product(payload: CreateProduct, request: Request):
    try:
        product = repository.create_product(payload)
        repository.create_audit_event(
            actor=_actor(request),
            action="product.created",
            resource_type="product",
            resource_id=product.id,
            metadata={"name": product.name, "category": product.category},
        )
        return product
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/products/{product_id}")
async def get_product(product_id: str):
    try:
        return repository.get_product(product_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="product not found") from exc


@router.get("/feedback")
async def list_feedback(productId: str | None = Query(default=None), product_id: str | None = Query(default=None)):
    return repository.list_feedback(productId or product_id)


@router.post("/feedback/organize")
async def organize_feedback_endpoint(payload: OrganizeFeedbackRequest, request: Request):
    try:
        product = repository.get_product(payload.productId)
        result = organize_feedback(product, payload)
        repository.create_audit_event(
            actor=_actor(request),
            action="feedback.organized",
            resource_type="product",
            resource_id=product.id,
            metadata={
                "sourceType": payload.sourceType,
                "readinessScore": result.readinessScore,
                "riskFlags": result.riskFlags,
                "confirmedFacts": len(result.confirmedFacts),
                "subjectiveOpinions": len(result.subjectiveOpinions),
            },
        )
        return result
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="product not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/feedback", status_code=201)
async def create_feedback(payload: CreateFeedback, request: Request):
    try:
        feedback = repository.create_feedback(payload)
        repository.create_audit_event(
            actor=_actor(request),
            action="feedback.created",
            resource_type="feedback",
            resource_id=feedback.id,
            metadata={"productId": feedback.productId, "sourceType": feedback.sourceType},
        )
        return feedback
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="product not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/feedback/{feedback_id}")
async def get_feedback(feedback_id: str):
    try:
        return repository.get_feedback(feedback_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="feedback not found") from exc


@router.get("/generations")
async def list_generations():
    return repository.list_generation_tasks()


@router.post("/generations", status_code=201)
async def create_generation(config: GenerationConfig, request: Request):
    try:
        product, feedback = _generation_inputs(config)
        await llm_client.ensure_ready()
        contents = await run_generation_agent(product, feedback, config)
        contents = [content.model_copy(update={"tenantId": current_tenant_id()}) for content in contents]
        task = repository.create_generation_task(config, contents, product)
        repository.create_audit_event(
            actor=_actor(request),
            action="generation.completed",
            resource_type="generation_task",
            resource_id=task.id,
            metadata={"mode": "sync", "productId": product.id, "contentCount": len(task.contents)},
        )
        return task
    except HTTPException:
        raise
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {exc}") from exc
    except KeyError as exc:
        message = str(exc).strip("'") or "resource not found"
        raise HTTPException(status_code=404, detail=message) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {exc}") from exc


@router.post("/generation-jobs", status_code=202)
async def create_generation_job(config: GenerationConfig, background_tasks: BackgroundTasks, request: Request):
    try:
        product, _feedback = _generation_inputs(config)
        await llm_client.ensure_ready()
        task = repository.create_generation_task_pending(config, product)
        actor = _actor(request)
        repository.create_audit_event(
            actor=actor,
            action="generation.queued",
            resource_type="generation_task",
            resource_id=task.id,
            metadata={"mode": "async", "productId": product.id, "count": config.count},
        )
        background_tasks.add_task(_run_generation_job, task.id, actor, current_tenant_id())
        return task
    except HTTPException:
        raise
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except KeyError as exc:
        message = str(exc).strip("'") or "resource not found"
        raise HTTPException(status_code=404, detail=message) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/generations/{task_id}")
async def get_generation(task_id: str):
    try:
        return repository.get_generation_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="generation task not found") from exc


@router.get("/generation-jobs/{task_id}")
async def get_generation_job(task_id: str):
    return await get_generation(task_id)


@router.post("/generations/{content_id}/review")
async def review_from_generations(content_id: str, payload: ReviewRequest, request: Request):
    return await review_content(content_id, payload, request)


@router.get("/contents")
async def list_contents(status: str | None = None, taskId: str | None = None, task_id: str | None = None):
    return repository.list_contents(status=status, task_id=taskId or task_id)


@router.get("/contents/{content_id}")
async def get_content(content_id: str):
    try:
        return repository.get_content(content_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="content not found") from exc


@router.post("/contents/{content_id}/review")
async def review_content(content_id: str, payload: ReviewRequest, request: Request):
    status, action = _normalize_review(payload)
    try:
        content = repository.review_content(
            content_id=content_id,
            status=status,
            action=action,
            reviewer=payload.reviewer or "local-user",
            comment=payload.comment,
            edited_text=payload.editedText,
        )
        repository.create_audit_event(
            actor=_actor(request),
            action=f"content.{action}",
            resource_type="generated_content",
            resource_id=content_id,
            metadata={"status": content.reviewStatus, "taskId": content.taskId},
        )
        return content
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="content not found") from exc


def _generation_inputs(config: GenerationConfig):
    product = repository.get_product(config.productId)
    feedback = repository.get_feedback(config.feedbackId) if config.feedbackId else None
    if feedback and feedback.productId != product.id:
        raise HTTPException(status_code=400, detail="feedback does not belong to product")
    return product, feedback


async def _run_generation_job(task_id: str, actor: str, tenant_id: str) -> None:
    with tenant_context(tenant_id):
        task = repository.update_generation_task_status(task_id, "generating", "generation started")
        try:
            product, feedback = _generation_inputs(task.config)
            contents = await run_generation_agent(product, feedback, task.config)
            contents = [content.model_copy(update={"tenantId": tenant_id, "taskId": task_id}) for content in contents]
            completed = repository.complete_generation_task(task_id, contents)
            repository.create_audit_event(
                actor=actor,
                action="generation.completed",
                resource_type="generation_task",
                resource_id=task_id,
                metadata={"mode": "async", "productId": completed.productId, "contentCount": len(completed.contents)},
            )
        except Exception as exc:
            failed = repository.fail_generation_task(task_id, str(exc))
            repository.create_audit_event(
                actor=actor,
                action="generation.failed",
                resource_type="generation_task",
                resource_id=task_id,
                metadata={"mode": "async", "productId": failed.productId, "message": failed.message or str(exc)},
            )


def _actor(request: Request) -> str:
    return (
        request.headers.get("x-sellerharbor-actor")
        or request.headers.get("x-forwarded-user")
        or request.headers.get("x-user")
        or "local-user"
    ).strip()


def _normalize_review(payload: ReviewRequest) -> tuple[str, str]:
    action = (payload.action or payload.status or "").strip()
    status = (payload.status or payload.action or "").strip()
    if action in {"approved", "approve"} or status in {"approved", "approve"}:
        return "approved", "approved"
    if action in {"rejected", "reject"} or status in {"rejected", "reject"}:
        return "rejected", "rejected"
    if action in {"rewrite_requested", "rewriting"} or status in {"rewrite_requested", "rewriting"}:
        return "rewriting", "rewrite_requested"
    if action == "pending" or status == "pending":
        return "pending", "pending"
    raise HTTPException(status_code=400, detail="review action or status is invalid")

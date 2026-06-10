from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.agents.review_generation import run_generation_agent
from app.core.config import settings
from app.db import repository
from app.models.schemas import CreateFeedback, CreateProduct, GenerationConfig, ReviewRequest
from app.services.platform_rules import all_platform_rules
from app.services.product_sourcing import all_research_providers, build_opportunity_report, build_opportunity_reports

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
    }


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


@router.get("/dashboard")
async def dashboard():
    return repository.dashboard_stats()


@router.get("/products")
async def list_products():
    return repository.list_products()


@router.post("/products", status_code=201)
async def create_product(payload: CreateProduct):
    try:
        return repository.create_product(payload)
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


@router.post("/feedback", status_code=201)
async def create_feedback(payload: CreateFeedback):
    try:
        return repository.create_feedback(payload)
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
async def create_generation(config: GenerationConfig):
    try:
        product = repository.get_product(config.productId)
        feedback = repository.get_feedback(config.feedbackId) if config.feedbackId else None
        if feedback and feedback.productId != product.id:
            raise HTTPException(status_code=400, detail="feedback does not belong to product")
        contents = await run_generation_agent(product, feedback, config)
        return repository.create_generation_task(config, contents, product)
    except HTTPException:
        raise
    except KeyError as exc:
        message = str(exc).strip("'") or "resource not found"
        raise HTTPException(status_code=404, detail=message) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {exc}") from exc


@router.get("/generations/{task_id}")
async def get_generation(task_id: str):
    try:
        return repository.get_generation_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="generation task not found") from exc


@router.post("/generations/{content_id}/review")
async def review_from_generations(content_id: str, payload: ReviewRequest):
    return await review_content(content_id, payload)


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
async def review_content(content_id: str, payload: ReviewRequest):
    status, action = _normalize_review(payload)
    try:
        return repository.review_content(
            content_id=content_id,
            status=status,
            action=action,
            reviewer=payload.reviewer or "local-user",
            comment=payload.comment,
            edited_text=payload.editedText,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="content not found") from exc


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

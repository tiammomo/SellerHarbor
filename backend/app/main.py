from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.db.repository import init_db, seed_demo, now_iso


app = FastAPI(title="ReviewPilot Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    init_db()
    if settings.seed_demo:
        seed_demo()


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "time": now_iso()}


app.include_router(router, prefix="/api")


"""CareerPilot FastAPI entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.services.session_store import get_store


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    get_store()  # ensure DB exists
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="CareerPilot API",
        description=(
            "Multi-agent AI career & interview preparation assistant "
            "orchestrated with LangGraph."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api")
    return app


app = create_app()

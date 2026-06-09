"""Trace FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..bootstrap import bootstrap
from ..config import settings
from .routers import audit_routes, auth, exams, investigator


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap()  # create tables + demo users if absent
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Trace API",
        description="Leak-proof, traceable exam paper distribution.",
        version="0.2.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(exams.router)
    app.include_router(investigator.router)
    app.include_router(audit_routes.router)

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok", "service": "trace", "version": app.version}

    return app


app = create_app()

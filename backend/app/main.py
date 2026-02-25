from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.security import RateLimiter, rate_limit_middleware, security_headers_middleware
from app.db import init_db
import logging


def create_app() -> FastAPI:
    setup_logging()
    logger = logging.getLogger("app.startup")
    logger.info("OpenRouter API key loaded: %s", "yes" if settings.openrouter_api_key else "no")
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    limiter = RateLimiter(settings.rate_limit_per_minute, settings.rate_limit_window_s)
    app.middleware("http")(rate_limit_middleware(limiter))
    app.middleware("http")(security_headers_middleware())

    @app.on_event("startup")
    async def on_startup():
        await init_db()

    return app


app = create_app()

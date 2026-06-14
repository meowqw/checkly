"""FastAPI-приложение Finance Manager."""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    token = settings.proverkacheka_token.strip()
    if not token:
        logger.warning("PROVERKACHEKA_TOKEN не задан — сканирование QR не будет работать")
    elif token.startswith("your_") or token == "your_proverkacheka_token":
        logger.warning(
            "PROVERKACHEKA_TOKEN похож на заглушку из .env.example — замените на реальный токен "
            "и выполните: docker compose up -d --force-recreate app"
        )
    normalizer = settings.product_normalizer.strip().lower()
    grok_key = settings.grok_api_key.strip()
    openai_key = settings.openai_api_key.strip()
    if normalizer in ("groq",):
        from app.implementations.groq_product_normalizer import resolve_groq_api_key

        if not resolve_groq_api_key():
            logger.warning("PRODUCT_NORMALIZER=groq, но GROQ_API_KEY / gsk_* ключ не задан")
    elif normalizer in ("grok", "xai"):
        if grok_key.startswith("gsk_"):
            logger.warning(
                "GROK_API_KEY начинается с gsk_ — это ключ Groq, не xAI. "
                "Укажите PRODUCT_NORMALIZER=groq или ключ xai- с console.x.ai"
            )
        elif not grok_key or grok_key.startswith("your_"):
            logger.warning("PRODUCT_NORMALIZER=grok, но GROK_API_KEY (xai-) не задан")
    elif normalizer in ("gpt", "openai"):
        if not openai_key or openai_key.startswith("your_"):
            logger.warning("PRODUCT_NORMALIZER=gpt, но OPENAI_API_KEY не задан")
    elif not grok_key and not openai_key:
        logger.warning(
            "GROK_API_KEY и OPENAI_API_KEY не заданы — товары из чека сохранятся без AI-категорий"
        )
    elif grok_key.startswith("your_") and openai_key.startswith("your_"):
        logger.warning(
            "Ключи LLM похожи на заглушки — укажите GROK_API_KEY или OPENAI_API_KEY в .env "
            "и выполните: docker compose up -d --force-recreate app"
        )
    if not settings.app_debug and settings.jwt_secret == "change-me-in-production":
        logger.warning(
            "JWT_SECRET не задан — используется небезопасное значение по умолчанию. "
            "Задайте JWT_SECRET в .env для production."
        )

    app = FastAPI(
        title="Finance Manager API",
        version="1.0.0",
        debug=settings.app_debug,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.message})

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(_: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("IntegrityError: %s", exc.orig)
        return JSONResponse(status_code=409, content={"error": "Конфликт данных"})

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        message = str(exc) if settings.app_debug else "Внутренняя ошибка сервера"
        return JSONResponse(status_code=500, content={"error": message})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router)
    return app


app = create_app()

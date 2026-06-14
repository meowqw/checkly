"""Конфигурация приложения из переменных окружения."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "finance_manager"
    db_user: str = "finance"
    db_password: str = "finance123"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    # External APIs
    proverkacheka_token: str = ""
    # Нормализация товаров: auto | grok | gpt (auto — Grok, если задан GROK_API_KEY)
    product_normalizer: str = "auto"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    grok_api_key: str = ""
    grok_model: str = "grok-3-mini"
    grok_base_url: str = "https://api.x.ai/v1"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # App
    app_debug: bool = False
    # Доп. CORS origins через запятую (для мобильного клиента, LAN IP и т.д.)
    cors_origins: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://localhost",
            "capacitor://localhost",
            "http://localhost",
            "http://localhost:8080",
            "https://localhost:8080",
        ]
        if self.cors_origins.strip():
            origins.extend(o.strip() for o in self.cors_origins.split(",") if o.strip())
        return list(dict.fromkeys(origins))

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

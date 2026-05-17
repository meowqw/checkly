"""Выбор реализации нормалайзера по настройкам."""
import logging

from app.config import get_settings
from app.implementations.gpt_product_normalizer import GptProductNormalizer
from app.implementations.groq_product_normalizer import GroqProductNormalizer, resolve_groq_api_key
from app.implementations.grok_product_normalizer import GrokProductNormalizer
from app.interfaces.product_normalizer import ProductNormalizerInterface

logger = logging.getLogger(__name__)


def _is_real_key(value: str) -> bool:
    key = value.strip()
    return bool(key) and not key.startswith("your_")


def get_product_normalizer() -> ProductNormalizerInterface:
    settings = get_settings()
    choice = settings.product_normalizer.strip().lower()
    grok_key = settings.grok_api_key.strip()
    groq_key = resolve_groq_api_key()

    if choice in ("groq",):
        return GroqProductNormalizer()
    if choice in ("grok", "xai"):
        if grok_key.startswith("gsk_") or groq_key:
            logger.info(
                "PRODUCT_NORMALIZER=grok, но ключ gsk_* — используем Groq (console.groq.com), не xAI Grok"
            )
            return GroqProductNormalizer()
        return GrokProductNormalizer()
    if choice in ("gpt", "openai"):
        return GptProductNormalizer()

    # auto
    if groq_key:
        return GroqProductNormalizer()
    if _is_real_key(grok_key) and grok_key.startswith("xai-"):
        return GrokProductNormalizer()
    if _is_real_key(grok_key):
        return GrokProductNormalizer()
    return GptProductNormalizer()

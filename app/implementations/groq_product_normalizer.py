"""Нормализация товаров через Groq (OpenAI-совместимый API)."""
from openai import OpenAI

from app.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.dto.receipts import ProductNormalizerInputDTO, ProductNormalizerOutputDTO
from app.implementations.product_normalizer_common import (
    SYSTEM_PROMPT,
    build_user_message,
    map_llm_error,
    map_to_output,
    parse_normalizer_response,
)
from app.interfaces.product_normalizer import ProductNormalizerInterface


def resolve_groq_api_key() -> str:
    settings = get_settings()
    if settings.groq_api_key.strip():
        return settings.groq_api_key.strip()
    key = settings.grok_api_key.strip()
    if key.startswith("gsk_"):
        return key
    return ""


class GroqProductNormalizer(ProductNormalizerInterface):
    """Клиент Groq: https://api.groq.com/openai/v1 (ключи начинаются с gsk_)."""

    def normalize_items(self, dto: ProductNormalizerInputDTO) -> ProductNormalizerOutputDTO:
        api_key = resolve_groq_api_key()
        if not api_key:
            raise ExternalServiceError(
                "GROQ_API_KEY не задан (ключ Groq начинается с gsk_, см. console.groq.com)"
            )

        if not dto.items:
            return ProductNormalizerOutputDTO(items=[])

        settings = get_settings()
        try:
            client = OpenAI(api_key=api_key, base_url=settings.groq_base_url)
            completion = client.chat.completions.create(
                model=settings.groq_model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_message(dto)},
                ],
                temperature=0.2,
            )
            content = completion.choices[0].message.content or "{}"
            raw_items = parse_normalizer_response(content)
        except ExternalServiceError:
            raise
        except Exception as exc:
            raise map_llm_error(exc, provider="Groq", key_env="GROQ_API_KEY") from exc

        return map_to_output(raw_items)

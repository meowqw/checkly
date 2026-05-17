"""Нормализация товаров через xAI Grok (OpenAI-совместимый API)."""
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


class GrokProductNormalizer(ProductNormalizerInterface):
    """Клиент xAI: https://api.x.ai/v1 — совместим с OpenAI SDK."""

    def normalize_items(self, dto: ProductNormalizerInputDTO) -> ProductNormalizerOutputDTO:
        settings = get_settings()
        if not settings.grok_api_key:
            raise ExternalServiceError("GROK_API_KEY не задан")

        if not dto.items:
            return ProductNormalizerOutputDTO(items=[])

        try:
            client = OpenAI(
                api_key=settings.grok_api_key,
                base_url=settings.grok_base_url,
            )
            completion = client.chat.completions.create(
                model=settings.grok_model,
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
            raise map_llm_error(exc, provider="Grok (xAI)", key_env="GROK_API_KEY") from exc

        return map_to_output(raw_items)

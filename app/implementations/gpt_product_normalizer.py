"""Нормализация товаров через OpenAI GPT."""
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


class GptProductNormalizer(ProductNormalizerInterface):
    def normalize_items(self, dto: ProductNormalizerInputDTO) -> ProductNormalizerOutputDTO:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ExternalServiceError("OPENAI_API_KEY не задан")

        if not dto.items:
            return ProductNormalizerOutputDTO(items=[])

        try:
            client = OpenAI(api_key=settings.openai_api_key)
            completion = client.chat.completions.create(
                model=settings.openai_model,
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
            raise map_llm_error(exc, provider="OpenAI", key_env="OPENAI_API_KEY") from exc

        return map_to_output(raw_items)

"""Общая логика нормализации товаров для LLM-провайдеров."""
import json
import logging
from typing import Any

from app.core.category_taxonomy import build_taxonomy_prompt_block, normalize_expense_category, resolve_subcategory
from app.core.exceptions import ExternalServiceError
from app.dto.receipts import (
    NormalizedItemDTO,
    ProductNormalizerInputDTO,
    ProductNormalizerOutputDTO,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""Ты помощник для нормализации позиций из фискальных чеков.
Для каждого товара верни JSON без markdown.

Поля каждого объекта:
- raw_name (точно как во входе)
- normalized_name (краткое нормализованное имя)
- product_name (человекочитаемое название)
- brand (строка или null)
- category (родительская категория)
- subcategory (подкатегория — ОБЯЗАТЕЛЬНО, если у категории есть дочерние в дереве)
- confidence (число от 0 до 1)

{build_taxonomy_prompt_block()}

Правила:
- category и subcategory должны строго совпадать с деревом выше (регистр и формулировка).
- Если у категории есть подкатегории — subcategory не может быть null.
- Для «Подарки», «Животные» и «Прочее» subcategory = null.
- Продукты → Снэки: чипсы, орехи, сухарики, попкорн, снеки.
- Продукты → Никотин: сигареты, табак, стики, вейп, IQOS, Glo.
- Животные: корм, наполнитель, товары для питомцев.
- Продукты → Алкоголь: пиво, вино, водка, шампанское и любой алкоголь.
- Продукты → Напитки: только безалкогольное (вода, сок, газировка, чай, кофе, энергетики).
- Продукты → Крупы: рис, гречка, овсянка, перловка, макароны, мука, бобовые в сухом виде.
- Суммы не меняй. Отвечай только валидным JSON."""


def build_user_message(dto: ProductNormalizerInputDTO) -> str:
    payload = {
        "merchant": dto.merchant,
        "items": [
            {"raw_name": i.raw_name, "price": i.price, "quantity": i.quantity}
            for i in dto.items
        ],
    }
    return (
        'Нормализуй товары и верни JSON вида {"items": [...]}.\n'
        + json.dumps(payload, ensure_ascii=False)
    )


def parse_normalizer_response(content: str) -> list[dict[str, Any]]:
    parsed = json.loads(content or "{}")
    raw_items = parsed.get("items", parsed if isinstance(parsed, list) else [])
    if not isinstance(raw_items, list):
        raise ValueError("Ответ модели не содержит массив items")
    return raw_items


def map_to_output(raw_items: list[dict[str, Any]]) -> ProductNormalizerOutputDTO:
    items: list[NormalizedItemDTO] = []
    for entry in raw_items:
        if not isinstance(entry, dict):
            continue
        raw_name = entry.get("raw_name", "")
        category = normalize_expense_category(entry.get("category"))
        subcategory = resolve_subcategory(
            category,
            entry.get("subcategory"),
            raw_name,
        )
        items.append(
            NormalizedItemDTO(
                raw_name=raw_name,
                normalized_name=entry.get("normalized_name") or entry.get("product_name", ""),
                product_name=entry.get("product_name") or entry.get("normalized_name", ""),
                brand=entry.get("brand"),
                category=category,
                subcategory=subcategory,
                confidence=float(entry.get("confidence", 0.5)),
            )
        )
    return ProductNormalizerOutputDTO(items=items)


def map_llm_error(exc: Exception, *, provider: str, key_env: str) -> ExternalServiceError:
    logger.exception("Ошибка нормализации через %s", provider)
    err = str(exc).lower()
    if "incorrect api key" in err or "invalid_api_key" in err or "401" in err or "invalid x-api-key" in err:
        return ExternalServiceError(
            f"Неверный {key_env}. Укажите ключ в .env и пересоздайте контейнер: "
            "docker compose up -d --force-recreate app"
        )
    if "insufficient_quota" in err or "exceeded your current quota" in err:
        return ExternalServiceError(f"Исчерпана квота {provider} — проверьте баланс в личном кабинете")
    return ExternalServiceError("Не удалось нормализовать товары")

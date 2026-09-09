"""Метаданные OpenAPI для Swagger / ReDoc."""

API_DESCRIPTION = """
REST API учёта личных финансов (**Checkly**).

## Авторизация

Защищённые эндпоинты требуют заголовок `Authorization: Bearer <access_token>`.
Токен выдаётся при регистрации (`POST /v1/auth/register`) или входе (`POST /v1/auth/login`).

## Часовой пояс

Клиент может передавать заголовок `X-Timezone` (IANA, например `Europe/Moscow`).
Он используется при регистрации, входе и фильтрации транзакций/статистики по датам
(`from` / `to` как календарные `YYYY-MM-DD`).

## Денежные суммы

Все суммы (`balance`, `amount`) — целые числа в **копейках** (85000 = 850,00 ₽).

## Категории и теги

- Категории — **плоский** список (без иерархии). `GET /v1/categories` возвращает
  `usage_count` (сколько раз категория стоит на позициях пользователя) и сортирует
  по типу → частота ↓ → имя.
- Теги **независимы** от категорий (M2M на `transaction_items`).
  `GET /v1/tags` — `usage_count` и сортировка по частоте ↓.
- Ручная операция: `POST /v1/transactions` принимает опциональный `tag_ids` (до 5 UUID).
- Правка позиции чека: `PATCH /v1/transactions/{id}/items/{item_id}` с `category_id` и опционально `tag_ids`.

## Чеки (QR)

`POST /v1/receipts/qr` — загрузка через proverkacheka.com. Опционально серверный
`PROVERKACHEKA_PROXY` (SOCKS5 `socks5h://…`) только для этого HTTP-запроса.
Категории/теги позиций заполняет AI-нормализатор (Groq/Grok/GPT); при сбое — «Прочее» без тегов.

## Ошибки

При ошибке API возвращает JSON `{"error": "текст"}`.
Коды: 400 — неверный запрос, 401 — не авторизован, 403 — запрещено,
404 — не найдено, 409 — конфликт данных, 502 — ошибка внешнего сервиса (чек).
"""

OPENAPI_TAGS = [
    {"name": "auth", "description": "Регистрация и вход"},
    {"name": "accounts", "description": "Счета пользователя и семейный доступ"},
    {
        "name": "categories",
        "description": "Плоские категории доходов/расходов; в списке — usage_count и сортировка по частоте",
    },
    {
        "name": "tags",
        "description": "Теги позиций (независимы от категорий; usage_count; системные + пользовательские)",
    },
    {
        "name": "transactions",
        "description": "Транзакции: список с фильтрами, ручное создание (в т.ч. tag_ids), правка позиций",
    },
    {"name": "receipts", "description": "Импорт чеков по QR-коду (proverkacheka)"},
    {"name": "stats", "description": "Статистика и агрегаты за период from/to"},
]

COMMON_ERROR_RESPONSES: dict[int, dict] = {
    400: {"description": "Неверный запрос"},
    401: {"description": "Требуется авторизация"},
    403: {"description": "Доступ запрещён"},
    404: {"description": "Ресурс не найден"},
    409: {"description": "Конфликт данных"},
    502: {"description": "Ошибка внешнего сервиса"},
    500: {"description": "Внутренняя ошибка сервера"},
}

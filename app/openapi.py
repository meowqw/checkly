"""Метаданные OpenAPI для Swagger / ReDoc."""

API_DESCRIPTION = """
REST API учёта личных финансов.

## Авторизация

Защищённые эндпоинты требуют заголовок `Authorization: Bearer <access_token>`.
Токен выдаётся при регистрации (`POST /v1/auth/register`) или входе (`POST /v1/auth/login`).

## Часовой пояс

Клиент может передавать заголовок `X-Timezone` (IANA, например `Europe/Moscow`).
Он используется при регистрации, входе и фильтрации транзакций по датам.

## Денежные суммы

Все суммы (`balance`, `amount`) — целые числа в **копейках**.

## Ошибки

При ошибке API возвращает JSON `{"error": "текст"}`.
Коды: 400 — неверный запрос, 401 — не авторизован, 403 — запрещено,
404 — не найдено, 409 — конфликт данных, 502 — ошибка внешнего сервиса (чек).
"""

OPENAPI_TAGS = [
    {"name": "auth", "description": "Регистрация и вход"},
    {"name": "accounts", "description": "Счета пользователя"},
    {"name": "categories", "description": "Категории доходов и расходов"},
    {"name": "transactions", "description": "Транзакции"},
    {"name": "receipts", "description": "Импорт чеков по QR-коду"},
    {"name": "stats", "description": "Статистика и агрегаты"},
]

COMMON_ERROR_RESPONSES: dict[int, dict] = {
    400: {"description": "Неверный запрос"},
    401: {"description": "Требуется авторизация"},
    403: {"description": "Доступ запрещён"},
    404: {"description": "Ресурс не найден"},
    409: {"description": "Конфликт данных"},
    500: {"description": "Внутренняя ошибка сервера"},
}

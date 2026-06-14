# Finance Manager — Backend (справочник для AI)

Документ описывает **серверную часть** репозитория `/finance_manager`. Цель — чтобы через месяцы можно было быстро понять домен, архитектуру, API и где что править.

Связанный документ: [`web/FRONTEND.md`](web/FRONTEND.md)

---

## 1. Что это за продукт

**Finance Manager (Checkly)** — MVP личного учёта финансов с упором на **российские фискальные чеки**.

Пользователь:
1. Регистрируется / логинится
2. Создаёт счета (карта, наличные и т.д.)
3. Добавляет **ручные** доходы/расходы или **сканирует QR чека**
4. Смотрит историю, фильтрует по периоду, меняет категории позиций чека
5. Может создавать **свои** категории (для ручных операций; чеки мапятся только на **системные**)

Ключевые бизнес-правила:
- Все суммы в **копейках** (`850 ₽` → `85000`), тип `int` / `BigInteger`
- Публичные ID в API — **UUID** в поле `uid`, внутренний `id` (BigInteger) наружу не отдаётся
- Даты транзакций в БД — **naive local datetime** в часовом поясе пользователя (не UTC)
- Баланс счёта меняется **только** через транзакции (create/update/delete), не «магически»
- QR-транзакции **нельзя** редактировать целиком; можно менять категорию **позиций**

---

## 2. Стек

| Компонент | Технология |
|-----------|------------|
| API | FastAPI 0.115, Uvicorn |
| ORM | SQLAlchemy 2.0 |
| БД | MySQL 8.0 (PyMySQL) |
| Миграции | Alembic |
| DTO | Pydantic 2.x |
| Конфиг | pydantic-settings (`.env`) |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Чеки | proverkacheka.com API |
| AI-категоризация | OpenAI / xAI Grok / Groq (через OpenAI SDK) |
| Docker | `docker-compose.yml`, `Dockerfile` |

Зависимости: `requirements.txt`

---

## 3. Структура каталогов

```
finance_manager/
├── app/
│   ├── main.py                 # FastAPI app, CORS, exception handlers, /health
│   ├── config.py               # Settings из .env
│   ├── api/
│   │   ├── deps.py             # DbSession, CurrentUser, UserTimezone, RequestTimezone
│   │   └── v1/
│   │       ├── router.py       # prefix /v1
│   │       ├── auth.py
│   │       ├── accounts.py
│   │       ├── categories.py
│   │       ├── transactions.py
│   │       └── receipts.py
│   ├── dto/                    # Pydantic: *RequestDTO, *ResponseDTO, service DTO
│   ├── services/               # Бизнес-логика
│   ├── repositories/           # SQLAlchemy-запросы
│   ├── interfaces/             # ABC: ReceiptProvider, ProductNormalizer
│   ├── implementations/        # proverkacheka, GPT/Grok/Groq normalizers
│   ├── core/
│   │   ├── enums.py
│   │   ├── dates.py            # timezone, normalize_range, to_storage_datetime
│   │   ├── security.py         # JWT, hash password
│   │   ├── exceptions.py
│   │   ├── category_taxonomy.py  # дерево категорий + keyword hints для LLM
│   │   └── uuid_utils.py
│   └── database/
│       ├── __init__.py         # engine, SessionLocal, get_db
│       └── models.py
├── alembic/
│   └── versions/               # 001–004
├── scripts/
│   ├── seed_categories.py
│   └── clean_receipt_data.py
├── docker-compose.yml          # dev
├── docker-compose.prod.yml
├── docker-compose.prod-ip.yml
├── Dockerfile
├── deploy/DEPLOY.md
└── .env
```

### Слои (строго)

```
HTTP → api/v1/*.py (тонкий контроллер)
     → services/*.py (правила, оркестрация)
     → repositories/*.py (SQL)
     → database/models.py
```

**API не ходит в repositories напрямую** — только через services.

Внешние сервисы подменяются через интерфейсы в `TransactionService(receipt_provider=..., product_normalizer=...)`.

---

## 4. API

**Базовый prefix:** `/v1`  
**OpenAPI:** `http://localhost:8000/docs`  
**Health:** `GET /health` → `{"status":"ok"}`

**Auth:** `Authorization: Bearer <jwt>`  
**Timezone:** `X-Timezone: Europe/Moscow` (IANA). На register/login сохраняется в `users.timezone`; на авторизованных запросах синхронизируется с заголовком.

**Ошибки:** `{"error": "сообщение"}` + HTTP-код

### 4.1 Auth — `/v1/auth`

| Method | Path | Auth | Body | Response |
|--------|------|------|------|----------|
| POST | `/register` | нет | `{email, login, password}` | `{user, access_token}` |
| POST | `/login` | нет | `{login, password}` | `{user, access_token}` |

`user`: `{id, email, login, timezone}`

Файлы: `app/api/v1/auth.py`, `app/services/auth_service.py`, `app/dto/auth.py`

### 4.2 Accounts — `/v1/accounts`

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/` | — | `{accounts: [{id, name, balance}]}` |
| POST | `/` | `{name, balance?}` | `{account}` |
| PATCH | `/{account_id}` | `{name?, balance?}` | `{account}` |
| DELETE | `/{account_id}` | — | `{success: true}` |

Счёт привязан к пользователю через `user_accounts` (M:N).

Файлы: `app/api/v1/accounts.py`, `app/services/account_service.py`

### 4.3 Categories — `/v1/categories`

| Method | Path | Query / Body | Response |
|--------|------|--------------|----------|
| GET | `/` | `include=children` | `{categories: [...]}` |
| POST | `/` | `{name, type, parent_id?, icon?, color?}` | `{category}` |
| PATCH | `/{category_id}` | `{name?, icon?, color?}` | `{category}` |
| DELETE | `/{category_id}` | — | `{success: true}` |

`CategoryDTO`: `{id, name, type, parent_id, icon, color, is_custom, children?}`

- `user_id IS NULL` → системная категория (read-only для пользователя)
- `is_custom: true` → создана пользователем; delete/update разрешены
- Системные категории используются для **парсинга чеков** и LLM

Файлы: `app/api/v1/categories.py`, `app/services/category_service.py`

### 4.4 Transactions — `/v1/transactions`

| Method | Path | Query / Body | Response |
|--------|------|--------------|----------|
| GET | `/` | `from`, `to`, `type`, `account_id` | `{transactions: [...]}` |
| POST | `/` | manual tx body | `{transaction}` |
| GET | `/{id}` | — | `{transaction}` (detail) |
| PATCH | `/{id}` | `{amount?, category_id?, comment?}` | `{transaction}` — **только manual** |
| PATCH | `/{id}/items/{item_id}` | `{category_id}` | `{transaction}` |
| DELETE | `/{id}` | — | `{success: true}` |

**Create manual:**
```json
{
  "account_id": "uuid",
  "type": "expense|income",
  "amount": 85000,
  "currency": "RUB",
  "occurred_at": "2026-06-15T14:30:00",
  "category_id": "uuid|null",
  "comment": "..."
}
```

**List item:** `{id, type, amount, currency, occurred_at, source, comment, title, account, merchant, category, items_count, items}`

**Detail item:** `{id, amount, source, type, currency, occurred_at, comment, merchant, items: [{id, raw_name, amount, category_id, category}]}`

`source`: `manual` | `qr_receipt` | `ocr` | `import`

Файлы: `app/api/v1/transactions.py`, `app/services/transaction_service.py`, `app/dto/transactions.py`

### 4.5 Receipts — `/v1/receipts`

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/qr` | `{account_id, qr}` | `{transaction}` (detail) |

Файл: `app/api/v1/receipts.py`

---

## 5. Модели БД

Файл: `app/database/models.py`

| Таблица | Назначение |
|---------|------------|
| `users` | uid, email, login, password, **timezone** |
| `accounts` | uid, name, balance (копейки) |
| `user_accounts` | связь user ↔ account |
| `categories` | дерево; user_id NULL = системная |
| `merchants` | глобальные (inn, name, address) |
| `products` | глобальный каталог товаров |
| `product_aliases` | raw_name + merchant → product |
| `transactions` | операция |
| `transaction_items` | позиция чека / ручная строка |
| `receipts` | фискальные поля, raw_qr, raw_json; 1:1 с transaction |
| `user_product_category_overrides` | персональная категория для product_id |

Индекс: `ix_transactions_user_occurred (user_id, occurred_at)` — миграция 003.

Enums: `app/core/enums.py` — `TransactionType`, `TransactionSource`, `CategoryType`, `Currency`.

---

## 6. Миграции Alembic

| Rev | Файл | Содержание |
|-----|------|------------|
| 001 | `001_initial_schema.py` | Полная схема |
| 002 | `002_user_product_category_overrides.py` | overrides |
| 003 | `003_performance_indexes.py` | индекс транзакций |
| 004 | `004_user_timezone.py` | `users.timezone` |

```bash
docker compose exec app alembic upgrade head
```

---

## 7. Auth и JWT

1. Register/login → `AuthService` → `create_access_token(user.uid)`
2. JWT payload: `{sub: user_uid, exp}`
3. `get_current_user` в `deps.py` декодирует token → `UserRepository.get_by_uid`
4. Password: bcrypt через `passlib`

При login/register timezone берётся из `X-Timezone` (`RequestTimezone`).

При авторизованных запросах `UserTimezone`:
- возвращает `user.timezone`
- если заголовок отличается — обновляет в БД

---

## 8. Даты и timezone

Файл: `app/core/dates.py`

**Модель:** в MySQL хранится naive datetime = **локальное wall-clock время пользователя**.

| Функция | Назначение |
|---------|------------|
| `resolve_timezone(name)` | IANA или fallback `Europe/Moscow` |
| `to_storage_datetime(dt, tz)` | aware → naive local |
| `now_local(tz)` | «сейчас» в TZ пользователя |
| `normalize_range_start/end(date, tz)` | границы фильтра: если время `00:00:00`, то начало/конец **календарного дня** в TZ |

Фронт шлёт фильтры как `from=2026-06-15&to=2026-06-15` (YYYY-MM-DD) + `X-Timezone`.

---

## 9. Категории и сидер

### Справочник

Единый источник правды: **`app/core/category_taxonomy.py`**

Синхронизирован с `scripts/seed_categories.py`.

**Расходы (пример):**
- Продукты → Молочные, Сладости, Овощи и фрукты, Напитки, Мясо и рыба, **Алкоголь**, **Крупы**
- Здоровье, Дом, Транспорт, Развлечения, Одежда, Связь, Образование, Подарки, Прочее

**Доходы:** Зарплата, Подработка, Возвраты, Прочие доходы

Функции:
- `normalize_expense_category()` — только из справочника, иначе «Прочее»
- `resolve_subcategory()` — валидация + keyword hints (`_KEYWORD_HINTS`)
- `build_taxonomy_prompt_block()` — текст для LLM prompt

### Сидер

```bash
python scripts/seed_categories.py
# или автоматически при docker compose up
```

Идемпотентен: не дублирует, обновляет icon/color.

### Lookup для чеков

`CategoryService.find_system_for_receipt(category, subcategory)` — **только поиск** системных категорий, без создания новых.

---

## 10. Сканирование чека (QR)

### Поток

```
POST /v1/receipts/qr
  → TransactionService.create_transaction_from_receipt()
    1. ProverkachekaReceiptProvider.get_receipt_by_qr(qr)
    2. Merchant (по INN)
    3. Transaction (expense, qr_receipt, amount=total)
    4. Receipt (фискальные поля + raw)
    5. Для каждой позиции:
       - ProductMatchingService.find_existing_product()
       - known → TransactionItem + user override category
       - unknown → batch LLM normalize
    6. LLM → find_system_for_receipt → Product + Alias + TransactionItem
    7. adjust_account_balance (-amount)
    8. commit
```

### Proverkacheka

`app/implementations/proverkacheka_receipt_provider.py`  
POST `https://proverkacheka.com/api/v1/check/get`  
Env: `PROVERKACHEKA_TOKEN`

### Product Normalizer (LLM)

Фабрика: `app/implementations/product_normalizer_factory.py`  
Общий prompt: `app/implementations/product_normalizer_common.py`

| `PRODUCT_NORMALIZER` | Провайдер |
|----------------------|-----------|
| `groq` | GroqProductNormalizer |
| `grok` / `xai` | GrokProductNormalizer |
| `gpt` / `openai` | GptProductNormalizer |
| `auto` | Groq (gsk_) → xAI → GPT |

Prompt включает дерево категорий из `build_taxonomy_prompt_block()`.

При ошибке LLM (`ExternalServiceError`) — fallback: категория «Прочее», confidence 0.

### Product Matching

`app/services/product_matching_service.py`  
Приоритет: GTIN → alias (raw_name + merchant) → alias (normalized_name).

### Overrides

`PATCH .../items/{item_id}` с `category_id`:
- обновляет `transaction_item.category_id`
- если есть `product_id` → upsert в `user_product_category_overrides`

---

## 11. TransactionService — правила

Файл: `app/services/transaction_service.py`

### Баланс

| Событие | Действие |
|---------|----------|
| create expense | balance -= amount |
| create income | balance += amount |
| update manual amount | delta = new - old |
| delete | revert (инверсия типа) |

### Редактирование

- `PATCH /transactions/{id}` — только `source == manual`
- QR: только категории позиций

### Список

- фильтры `from`/`to` через `normalize_range_start/end` + timezone
- `account_id` → internal id через user_accounts
- sort: `occurred_at DESC`
- eager load: account, merchant, items→category→parent

### Отображение категории

`_category_display_name`: `"Родитель › Дочерняя"`

---

## 12. Переменные окружения

Файл: `.env` (см. `.env.example`)

| Переменная | Default | Описание |
|------------|---------|----------|
| `DB_*` | localhost/finance | MySQL |
| `JWT_SECRET` | change-me... | ⚠️ обязателен в prod |
| `JWT_EXPIRE_MINUTES` | 10080 | 7 дней |
| `PROVERKACHEKA_TOKEN` | | QR чеки |
| `PRODUCT_NORMALIZER` | auto | groq/grok/gpt/auto |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | | GPT |
| `GROK_API_KEY`, `GROK_MODEL`, `GROK_BASE_URL` | | xAI |
| `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_BASE_URL` | | Groq |
| `APP_DEBUG` | false | SQL echo |
| `CORS_ORIGINS` | | доп. origins через запятую |

Docker MySQL: `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`

---

## 13. Docker

### Dev (`docker-compose.yml`)

- **db:** MySQL :3306, volume `mysql_data`
- **app:** :8000, volume `./:/workspace`, hot reload
- startup: `alembic upgrade head && seed_categories && uvicorn --reload`

### Prod (`docker-compose.prod.yml` + `docker-compose.prod-ip.yml`)

- MySQL без внешнего порта
- app: workers 2, restart unless-stopped
- IP override: порт 8000 наружу

Подробнее: `deploy/DEPLOY.md`

---

## 14. Скрипты

| Скрипт | Назначение |
|--------|------------|
| `scripts/seed_categories.py` | системные категории |
| `scripts/clean_receipt_data.py` | очистка QR-транзакций/products для повторного теста |

```bash
python scripts/clean_receipt_data.py --all
python scripts/clean_receipt_data.py --products
python scripts/clean_receipt_data.py --qr-transactions
```

---

## 15. Исключения

`app/core/exceptions.py`:

| Класс | HTTP |
|-------|------|
| `NotFoundError` | 404 |
| `UnauthorizedError` | 401 |
| `ForbiddenError` | 403 |
| `ConflictError` | 409 |
| `ExternalServiceError` | 502 |

Handlers в `main.py`: `AppError`, `IntegrityError` → 409, generic → 500.

---

## 16. Конвенции для правок

1. Новый endpoint → `api/v1/` + service + repository + dto
2. Новая таблица → model + alembic migration (не `create_all` в prod)
3. Новая системная категория → **`category_taxonomy.py`** + `seed_categories.py` + перезапуск сидера
4. Изменение LLM prompt → `product_normalizer_common.py` + `category_taxonomy.py`
5. Публичные ID — только `uid`
6. Деньги — только копейки, без float
7. DTO: `*RequestDTO` / `*ResponseDTO` для API; внутренние service DTO без суффиксов Request/Response

---

## 17. Быстрые ссылки

| Задача | Файл |
|--------|------|
| Новый endpoint | `app/api/v1/*.py` |
| Бизнес-логика | `app/services/*.py` |
| SQL | `app/repositories/*.py` |
| Схема | `app/database/models.py` |
| Категории LLM | `app/core/category_taxonomy.py` |
| Чеки | `app/implementations/proverkacheka_receipt_provider.py` |
| LLM выбор | `app/implementations/product_normalizer_factory.py` |
| Auth deps | `app/api/deps.py` |
| Даты | `app/core/dates.py` |

### Типичный сценарий API

```http
POST /v1/auth/register
POST /v1/accounts          {"name":"Карта","balance":0}
POST /v1/transactions      {manual expense}
POST /v1/receipts/qr       {"account_id":"...","qr":"t=...&s=..."}
GET  /v1/transactions?from=2026-06-01&to=2026-06-30
PATCH /v1/transactions/{id}/items/{item_id}  {"category_id":"..."}
```

---

## 18. Запуск локально

```bash
docker compose up -d
# API: http://localhost:8000/docs
# Frontend (отдельно): cd web && npm run dev
```

```bash
docker compose exec app alembic upgrade head
docker compose exec app python scripts/seed_categories.py
```

# Finance Manager — Backend (справочник для AI)

Документ описывает **серверную часть** репозитория `/finance_manager`. Цель — чтобы через месяцы можно было быстро понять домен, архитектуру, API и где что править.

Связанный документ: [`web/FRONTEND.md`](web/FRONTEND.md)

---

## 0. Инструкции для AI-агента (обязательно читать)

### Роль

Ты — **сеньор Python / FastAPI разработчик**. Пишешь production-код: ясно, узко по задаче, с уважением к существующей архитектуре. Не джун-спагетти, не «переписать всё с нуля».

### Как правильно писать код здесь

1. **Слои строго:** `api → services → repositories → models`. API **не** импортирует repositories (исключений нет; сервис сам создаёт repo из `Session`).
2. **Не ломай контракт API** без явной просьбы. Аддитивные поля/query-параметры — ок; breaking changes — только с миграцией фронта.
3. **Не трогай фронт** (`web/`), если пользователь не попросил. Бэкенд-задачи = только `app/`, `alembic/`, `scripts/`, `tests/`, этот файл.
4. **Деньги** — только `int` копейки. **ID наружу** — только `uid` (UUID). Внутренний `id` наружу не отдавать.
5. **Даты в БД** — naive local wall-clock в TZ пользователя (`app/core/dates.py`), не UTC.
6. **Баланс счёта** меняется только через create/update/delete транзакций (`TransactionService`), не «магически» в PATCH account без нужды.
7. **QR** нельзя `PATCH` целиком; категории позиций — можно. Внешние API (proverkacheka, LLM) — только через интерфейсы + моки в тестах.
8. **Минимальный diff:** не рефактори соседний код «заодно», не добавляй зависимости без нужды, не пиши markdown/доки без просьбы (кроме обновления этого файла, когда меняется бэкенд-контракт или структура).
9. **После существенных правок** — прогон тестов:
   ```bash
   docker compose exec app pytest tests/ -q
   ```
10. **Новый endpoint** → router + service + dto + OpenAPI (`summary`/`description`, `Field(description=...)`). Новая таблица → model + Alembic (не `create_all` в prod).

### Чего не делать

- Не коммитить и не пушить без явной просьбы пользователя.
- Не вызывать реальные LLM/proverkacheka в unit/integration тестах.
- Не удалять системные категории и не ломать идемпотентность сидеров.
- Не «ускорять» bcrypt/login ценой безопасности.
- Не менять смысл stats (суммы tx vs категории по items) без согласования.

### Быстрый чеклист перед сдачей задачи

- [ ] Слои соблюдены, публичные ID = uid, деньги = int
- [ ] Старый клиент без новых query-параметров не сломан (если менялся API)
- [ ] `pytest tests/ -q` зелёный
- [ ] При изменении API/архитектуры — обновлён **этот** `BACKEND.md`

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
| Тесты | pytest + httpx (`requirements-dev.txt`), SQLite in-memory |

Зависимости: `requirements.txt` (runtime), `requirements-dev.txt` (pytest, httpx)

---

## 3. Структура каталогов

```
finance_manager/
├── app/
│   ├── main.py                 # FastAPI app, CORS, exception handlers, /health
│   ├── openapi.py              # RU-описания для Swagger (теги, ошибки)
│   ├── config.py               # Settings из .env
│   ├── api/
│   │   ├── deps.py             # DbSession, CurrentUser, UserTimezone, RequestTimezone
│   │   └── v1/
│   │       ├── router.py       # prefix /v1
│   │       ├── auth.py
│   │       ├── accounts.py
│   │       ├── categories.py
│   │       ├── transactions.py
│   │       ├── receipts.py
│   │       └── stats.py
│   ├── dto/                    # Pydantic: *RequestDTO, *ResponseDTO (+ stats.py)
│   ├── services/
│   │   ├── transaction_service.py
│   │   ├── stats_service.py    # агрегаты для /v1/stats
│   │   ├── transaction_mapper.py   # ORM → TransactionListItemDTO (shared)
│   │   └── transaction_queries.py  # list_transactions_for_filters (shared)
│   ├── repositories/           # SQLAlchemy-запросы
│   ├── interfaces/             # ABC: ReceiptProvider, ProductNormalizer
│   ├── implementations/        # proverkacheka, GPT/Grok/Groq normalizers
│   ├── core/
│   │   ├── enums.py
│   │   ├── dates.py            # timezone, normalize_range, to_storage_datetime
│   │   ├── security.py         # JWT, hash password
│   │   ├── exceptions.py
│   │   ├── timing_middleware.py  # X-Process-Time / X-Process-Time-Ms
│   │   ├── category_taxonomy.py  # дерево категорий + keyword hints для LLM
│   │   ├── category_display.py   # category_display_name() для API
│   │   └── uuid_utils.py
│   └── database/
│       ├── __init__.py         # engine, SessionLocal, get_db
│       └── models.py
├── alembic/
│   └── versions/               # 001–004
├── scripts/
│   ├── seed_categories.py
│   ├── seed_demo_data.py       # тестовые пользователи/tx/чеки
│   ├── benchmark_api.py        # latency эндпоинтов
│   └── clean_receipt_data.py
├── tests/
│   ├── conftest.py             # SQLite + фикстуры
│   ├── helpers.py              # FakeReceiptProvider / FakeProductNormalizer
│   ├── unit/
│   └── integration/
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
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

**API не ходит в repositories напрямую** — только через services (`StatsService(db)`, `TransactionService(db)`, …).

Внешние сервисы подменяются через интерфейсы в `TransactionService(receipt_provider=..., product_normalizer=...)`.

**Latency:** каждый ответ содержит заголовки `X-Process-Time` (сек) и `X-Process-Time-Ms` (`TimingMiddleware`). Медленные запросы (>200 мс) пишутся в лог warning.

---

## 4. API

**Базовый prefix:** `/v1`  
**OpenAPI:** `http://localhost:8000/docs` (описания на **русском**, `HTTPBearer`, `X-Timezone`)  
**Health:** `GET /health` → `{"status":"ok"}`

**Auth:** `Authorization: Bearer <jwt>` (схема в Swagger)  
**Timezone:** `X-Timezone: Europe/Moscow` (IANA). На register/login сохраняется в `users.timezone`; на авторизованных запросах синхронизируется с заголовком.

**Ошибки:** `{"error": "сообщение"}` + HTTP-код (400/401/403/404/409/502 описаны на роутах)

Метаданные OpenAPI: `app/openapi.py` + `Field(description=...)` в DTO + `summary`/`description` на роутерах.

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
| GET | `/` | `from`, `to`, `type`, `account_id`, **`category_id?`**, **`limit?`**, **`offset?`** | `{transactions: [...]}` (+ meta при пагинации) |
| POST | `/` | manual tx body | `{transaction}` |
| GET | `/{id}` | — | `{transaction}` (detail) |
| PATCH | `/{id}` | `{amount?, category_id?, comment?}` | `{transaction}` — **только manual** |
| PATCH | `/{id}/items/{item_id}` | `{category_id}` | `{transaction}` |
| DELETE | `/{id}` | — | `{success: true}` |

**Пагинация (аддитивная, фронт без изменений работает):**
- Без `limit` — весь список по фильтру, **без** полей `total` / `limit` / `offset` / `has_more` (`response_model_exclude_none`)
- С `limit` (1…100) и `offset` (≥0):
```json
{
  "transactions": [ /* страница */ ],
  "total": 226,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```
- Константа max: `TRANSACTIONS_MAX_LIMIT = 100` в `transaction_service.py`

**Фильтр `category_id` (как у `/stats`):**
- корень → операции с позицией в родителе или любой подкатегории;
- подкатегория → только с позицией в ней;
- ручная операция попадает, если её item.category в scope;
- QR-чек попадает, если **хотя бы одна** позиция в scope (в ответе items чека по-прежнему все).

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

- `category` в list — **только manual**; для `qr_receipt` → `null`
- `items[].category` — `{name}` (`CategoryBriefDTO`), не `dict`
- Маппинг list/detail: `transaction_mapper.py` (используется и в `TransactionService`, и в `StatsService`)
- Загрузка связей: `selectinload` (account, merchant, items→category→parent)

**Detail item:** `{id, amount, source, type, currency, occurred_at, comment, merchant, items: [{id, raw_name, amount, category_id, category}]}`

`source`: `manual` | `qr_receipt` | `ocr` | `import`

Файлы: `app/api/v1/transactions.py`, `app/services/transaction_service.py`, `app/services/transaction_mapper.py`, `app/dto/transactions.py`

### 4.5 Receipts — `/v1/receipts`

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/qr` | `{account_id, qr}` | `{transaction}` (detail) |

Файл: `app/api/v1/receipts.py`

### 4.6 Stats — `/v1/stats`

| Method | Path | Query | Response |
|--------|------|-------|----------|
| GET | `/` | `from`, `to`, `account_id`, **`category_id?`** | см. ниже |

```json
{
  "expense": 125000,
  "income": 300000,
  "categories": [
    { "category_id": "uuid|null", "name": "Продукты › Снэки", "amount": 4500, "percent": 12, "color": "#16a34a" }
  ],
  "recent_expenses": [ /* до 8 TransactionListItemDTO, compact */ ]
}
```

**Правила агрегации (`StatsService`):**
- Без `category_id`: `expense` / `income` — `SUM(transaction.amount)` по типу (SQL)
- С `category_id`: суммы по **позициям** (`transaction_items`) в scope категорий; корень = родитель + все дети, подкатегория = только она
- `categories` — **только расходы**; для чеков суммируются **позиции** (`transaction_items.amount`), не сумма чека целиком (SQL GROUP BY + display-name в Python)
- транзакции **без позиций** → сумма tx в «Прочее» (**только** без фильтра `category_id`)
- `percent` — доля от суммы категорийных расходов в текущей выборке
- `color` — из категории; у подкатегорий наследуется `parent.color`
- `recent_expenses` — `LIMIT 8` расходов; при фильтре — только tx с позицией в scope; `compact=True`

Query **`type` нет** — stats всегда считает и расходы, и доходы (в рамках фильтра категорий).

Реализация: SQL в repo —
`sum_amounts_by_type` / `sum_item_amounts_by_type`, `aggregate_expense_category_amounts`, `list_recent_expenses`.

Файлы: `app/api/v1/stats.py`, `app/services/stats_service.py`, `app/dto/stats.py`, `app/repositories/transaction_repository.py`, `app/services/transaction_queries.py`

**Главная страница фронта** использует только этот endpoint (не тянет полный `/transactions`).

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
- Продукты → Молочные, Сладости, Овощи и фрукты, Напитки, Мясо и рыба, **Алкоголь**, **Крупы**, **Снэки**, **Никотин**
- Здоровье, Дом, Транспорт, Развлечения, Одежда, Связь, Образование, Подарки, **Животные**, Прочее

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

Идемпотентен: не дублирует, обновляет icon/color. Безопасен для prod — существующие категории не удаляются, только добавляются недостающие.

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

`category_display_name()` в `app/core/category_display.py`: `"Родитель › Дочерняя"`

В **списке** транзакций поле `category` — только для **manual** (из категории первой позиции). Для `qr_receipt` → `category: null`; категории только у **позиций** внутри чека.

---

## 11.1 StatsService

Файл: `app/services/stats_service.py`

- Конструктор: `StatsService(db)` — как у остальных сервисов
- Фильтры: `resolve_transaction_filters()` (`transaction_queries.py`)
- Агрегаты — SQL в `TransactionRepository` (не загрузка всех строк)
- `recent_expenses`: `map_transaction_to_list_item(tx, compact=True)`
- **Не** создаёт `TransactionService` (нет лишней инициализации LLM/receipt provider)

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
| `scripts/seed_demo_data.py` | демо-пользователи, счета, manual/QR tx (идемпотентно; `--force`) |
| `scripts/benchmark_api.py` | latency всех основных эндпоинтов (`X-Process-Time-Ms`) |
| `scripts/clean_receipt_data.py` | очистка QR-транзакций/products для повторного теста |

```bash
# демо-данные (логин demo / demo12345)
docker compose exec app python scripts/seed_demo_data.py
docker compose exec app python scripts/seed_demo_data.py --force

# бенчмарк
docker compose exec app python scripts/benchmark_api.py --runs 15

python scripts/clean_receipt_data.py --all
python scripts/clean_receipt_data.py --products
python scripts/clean_receipt_data.py --qr-transactions
```

Демо-аккаунты: `demo`, `alice`, `bob` — пароль `demo12345`.

---

## 14.1 Тесты

```bash
docker compose exec app pip install -q -r requirements-dev.txt
docker compose exec app pytest tests/ -q
```

| Каталог | Что |
|---------|-----|
| `tests/unit/` | dates, security/JWT, category_display, taxonomy, transaction_mapper |
| `tests/integration/` | auth, accounts, balance, QR (моки), stats, list/pagination, categories, product matching |
| `tests/helpers.py` | `FakeReceiptProvider`, `FakeProductNormalizer` |
| `tests/conftest.py` | SQLite in-memory (`StaticPool`), BigInteger→Integer для AUTOINCREMENT |

Покрывать обязательно при правках: **баланс**, **manual vs QR edit rules**, **stats (items vs tx.amount)**, **пагинация**, **ownership** (чужой uid → 404/403).

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

1. Новый endpoint → `api/v1/` + service + dto + **`openapi.py`** / `summary`/`description` на роуте
2. Новая таблица → model + alembic migration (не `create_all` в prod)
3. Новая системная категория → **`category_taxonomy.py`** + перезапуск сидера (идемпотентно, prod-safe)
4. Изменение LLM prompt → `product_normalizer_common.py` + `category_taxonomy.py`
5. List-маппинг транзакций → **`transaction_mapper.py`** (не дублировать в сервисах)
6. Фильтрованный список tx → **`transaction_queries.py`** (`resolve_transaction_filters`)
7. Агрегаты для UI → **`stats_service.py`** + SQL в repo; не считать на фронте (offline fallback — исключение)
8. Публичные ID — только `uid`
9. Деньги — только копейки, без float
10. DTO: `*RequestDTO` / `*ResponseDTO` для API; внутренние service DTO без суффиксов Request/Response
11. Сервисы принимают `Session` (`FooService(db)`), сами создают repositories
12. Внешние HTTP/LLM — только через `interfaces/` + implementations; в тестах — `tests/helpers.py`
13. После изменения API/слоёв/скриптов — обновить **BACKEND.md**
14. Прогон: `docker compose exec app pytest tests/ -q`

---

## 17. Быстрые ссылки

| Задача | Файл |
|--------|------|
| Новый endpoint | `app/api/v1/*.py` |
| Swagger RU | `app/openapi.py`, DTO `Field(description=...)`, роуты |
| Бизнес-логика | `app/services/*.py` |
| List tx DTO | `app/services/transaction_mapper.py` |
| Фильтры tx / stats query | `app/services/transaction_queries.py` |
| Статистика | `app/services/stats_service.py`, `app/dto/stats.py` |
| SQL | `app/repositories/*.py` |
| Схема | `app/database/models.py` |
| Категории LLM | `app/core/category_taxonomy.py` |
| Имя категории в API | `app/core/category_display.py` |
| Чеки | `app/implementations/proverkacheka_receipt_provider.py` |
| LLM выбор | `app/implementations/product_normalizer_factory.py` |
| Auth deps | `app/api/deps.py` |
| Даты | `app/core/dates.py` |
| Timing headers | `app/core/timing_middleware.py` |
| Тесты | `tests/` |
| Демо-данные | `scripts/seed_demo_data.py` |
| Бенчмарк | `scripts/benchmark_api.py` |

### Типичный сценарий API

```http
POST /v1/auth/register
POST /v1/accounts          {"name":"Карта","balance":0}
POST /v1/transactions      {manual expense}
POST /v1/receipts/qr       {"account_id":"...","qr":"t=...&s=..."}
GET  /v1/stats?from=2026-06-01&to=2026-06-30
GET  /v1/transactions?from=2026-06-01&to=2026-06-30
GET  /v1/transactions?from=2026-06-01&to=2026-06-30&limit=20&offset=0
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
docker compose exec app python scripts/seed_demo_data.py   # опционально
docker compose exec app pip install -q -r requirements-dev.txt
docker compose exec app pytest tests/ -q
```

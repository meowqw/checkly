# Checkly (Finance Manager)

MVP личного учёта финансов с упором на **российские фискальные чеки**.

**Backend:** FastAPI + MySQL  
**Frontend:** React + Vite + Capacitor (веб и Android APK)  
**Offline-first:** ручные операции и счета работают без сети, синхронизация при появлении сети

Подробная документация для разработки:
- [BACKEND.md](BACKEND.md) — API, домен, миграции, чеки, LLM
- [web/FRONTEND.md](web/FRONTEND.md) — UI, offline, сборка APK
- [deploy/DEPLOY.md](deploy/DEPLOY.md) — деплой на VPS

---

## Возможности

- Регистрация и авторизация (JWT)
- Счета, баланс в копейках
- Категории: системные (для чеков) + пользовательские (для ручного ввода)
- Ручные доходы и расходы
- Сканирование QR чека ([proverkacheka.com](https://proverkacheka.com))
- AI-категоризация товаров: **Groq / xAI Grok / OpenAI GPT** (автовыбор в `auto`)
- Кэш товаров в `products` / `product_aliases`, персональные overrides категорий
- Дашборд: баланс, траты по категориям, последние операции
- Android APK с нативным сканером QR (ML Kit)

Все суммы в API и БД — **копейки** (`850 ₽` → `85000`).

---

## Быстрый старт (Docker)

```bash
cp .env.example .env
# Минимум для чеков: PROVERKACHEKA_TOKEN
# Для AI-категорий: GROQ_API_KEY, GROK_API_KEY или OPENAI_API_KEY

docker compose up --build
```

| Сервис | URL |
|--------|-----|
| API | http://localhost:8000 |
| Swagger (RU) | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

При старте контейнера: `alembic upgrade head` → сидер категорий → uvicorn.

### Фронтенд (dev)

```bash
cd web
npm install
npm run dev
```

http://localhost:5173 — Vite проксирует `/v1` на `:8000` ( `VITE_API_URL` можно оставить пустым).

---

## Деплой на VPS

Пошагово: **[deploy/DEPLOY.md](deploy/DEPLOY.md)**

```bash
# на сервере
docker compose -f docker-compose.prod.yml up -d --build
```

**Без домена** (только IP):

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.prod-ip.yml up -d --build
# → http://IP:8000
```

В `.env` на сервере задайте `JWT_SECRET` и `CORS_ORIGINS` (IP, `capacitor://localhost` для APK).

---

## Локальный запуск без Docker

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Поднимите MySQL, укажите DB_* в .env

alembic upgrade head
python scripts/seed_categories.py
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd web && npm install && npm run dev
```

### Android APK

```bash
cd web
cp .env.android.example .env.production.local
# VITE_API_URL=http://ВАШ_IP:8000

npm run android:apk
```

---

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `DB_*` | Подключение к MySQL |
| `JWT_SECRET` | Секрет JWT (**обязателен в prod**) |
| `JWT_EXPIRE_MINUTES` | Время жизни токена (по умолчанию 7 дней) |
| `PROVERKACHEKA_TOKEN` | Токен proverkacheka.com для QR-чеков |
| `PRODUCT_NORMALIZER` | `auto`, `groq`, `grok` / `xai`, `gpt` / `openai` |
| `GROQ_API_KEY` | Groq (`gsk_...`) — приоритет в `auto` |
| `GROK_API_KEY` | xAI Grok (`xai-...`), не путать с Groq |
| `OPENAI_API_KEY` | OpenAI при `PRODUCT_NORMALIZER=gpt` |
| `APP_DEBUG` | SQL echo и подробные ошибки |
| `CORS_ORIGINS` | Доп. origins через запятую (APK, LAN IP) |

Полный список: `.env.example`

---

## API (кратко)

Prefix: `/v1` · Auth: `Authorization: Bearer <token>` · Timezone: `X-Timezone: Europe/Moscow`

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/v1/auth/register`, `/login` | Регистрация / вход |
| CRUD | `/v1/accounts` | Счета |
| CRUD | `/v1/categories` | Категории (`?include=children`) |
| CRUD | `/v1/transactions` | Операции, фильтры `from`/`to` |
| GET | `/v1/stats` | Статистика за период (расходы/доходы, категории, recent) |
| PATCH | `/v1/transactions/{id}/items/{item_id}` | Категория позиции чека |
| POST | `/v1/receipts/qr` | Импорт чека по QR |

Детали, схемы и примеры: **http://localhost:8000/docs** и [BACKEND.md](BACKEND.md).

---

## Структура репозитория

```
finance_manager/
├── app/                    # FastAPI backend
│   ├── api/v1/             # HTTP-роуты
│   ├── services/           # бизнес-логика
│   ├── repositories/       # SQL
│   ├── dto/                # Pydantic-схемы
│   ├── implementations/    # proverkacheka, LLM-нормализаторы
│   └── core/               # enums, dates, category_taxonomy
├── alembic/                # миграции БД
├── scripts/
│   ├── seed_categories.py  # системные категории (идемпотентно)
│   └── clean_receipt_data.py
├── web/                    # React + Capacitor клиент
├── deploy/                 # инструкции деплоя
├── docker-compose.yml      # dev
├── docker-compose.prod.yml # production
└── BACKEND.md, README.md
```

---

## Категории (системные)

Справочник: `app/core/category_taxonomy.py` (синхронизирован с сидером).

**Расходы:** Продукты (Молочные, Сладости, Снэки, Никотин, Алкоголь, …), Здоровье, Дом, Транспорт, Развлечения, Одежда, Связь, Образование, Подарки, **Животные**, Прочее.

**Доходы:** Зарплата, Подработка, Возвраты, Прочие доходы.

```bash
python scripts/seed_categories.py   # безопасно на prod — только добавляет/обновляет
```

---

## Скрипты

```bash
# Миграции
alembic upgrade head
alembic revision --autogenerate -m "описание"

# Сброс чеков и товаров (для повторного теста AI)
python scripts/clean_receipt_data.py --all
python scripts/clean_receipt_data.py --qr-transactions
python scripts/clean_receipt_data.py --products
```

---

## Типичный сценарий

1. `POST /v1/auth/register` — пользователь + JWT
2. `POST /v1/accounts` — счёт `{ "name": "Карта", "balance": 0 }`
3. `POST /v1/transactions` — ручной расход
4. `POST /v1/receipts/qr` — QR чека `{ "account_id": "...", "qr": "t=...&s=..." }`
5. `GET /v1/transactions?from=2026-06-01&to=2026-06-30` — история за период

Или через UI: http://localhost:5173

---

## Стек

| Часть | Технологии |
|-------|------------|
| API | FastAPI, SQLAlchemy 2, Pydantic 2, Alembic |
| БД | MySQL 8 |
| Auth | JWT (python-jose), bcrypt |
| Чеки | proverkacheka.com API |
| AI | OpenAI SDK → Groq / xAI / GPT |
| Web | React 18, TypeScript, Vite, Tailwind |
| Mobile | Capacitor 6, ML Kit barcode |

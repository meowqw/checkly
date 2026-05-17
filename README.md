# Finance Manager API

MVP backend для учёта расходов с поддержкой QR-чеков, ручных операций и автоматической нормализации товаров через AI.

## Возможности

- Регистрация и авторизация (JWT)
- Счета пользователя
- Категории (системные + пользовательские)
- Ручные доходы/расходы
- Сканирование QR-чека (proverkacheka.com)
- Нормализация неизвестных товаров (OpenAI GPT)
- Кэширование товаров в `products` / `product_aliases`

Все суммы хранятся в **копейках** (850 ₽ → `85000`).

## Быстрый старт (Docker)

```bash
cp .env.example .env
# Заполните PROVERKACHEKA_TOKEN и GROK_API_KEY (или OPENAI_API_KEY) в .env

docker compose up --build
```

API: http://localhost:8000  
Документация: http://localhost:8000/docs  
Health: http://localhost:8000/health

При старте контейнера автоматически выполняются миграции и сидер категорий.

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Поднимите MySQL и укажите DB_* в .env

alembic upgrade head
python scripts/seed_categories.py
uvicorn app.main:app --reload --port 8000
```

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `DB_HOST` | Хост MySQL |
| `DB_PORT` | Порт MySQL |
| `DB_NAME` | Имя базы |
| `DB_USER` | Пользователь БД |
| `DB_PASSWORD` | Пароль БД |
| `JWT_SECRET` | Секрет для JWT |
| `JWT_ALGORITHM` | Алгоритм JWT (по умолчанию HS256) |
| `JWT_EXPIRE_MINUTES` | Время жизни токена в минутах |
| `PROVERKACHEKA_TOKEN` | Токен proverkacheka.com |
| `PRODUCT_NORMALIZER` | `auto`, `groq`, `grok` или `gpt` |
| `GROQ_API_KEY` | Ключ Groq (`gsk_...`, console.groq.com) — приоритет в `auto` |
| `GROQ_MODEL` | Модель Groq (по умолчанию `llama-3.3-70b-versatile`) |
| `GROK_API_KEY` | Ключ xAI Grok (`xai-...`, console.x.ai), не путать с Groq |
| `GROK_MODEL` | Модель xAI (по умолчанию `grok-3-mini`) |
| `OPENAI_API_KEY` | Ключ OpenAI (если `PRODUCT_NORMALIZER=gpt`) |
| `OPENAI_MODEL` | Модель GPT (по умолчанию gpt-4o-mini) |
| `APP_DEBUG` | Режим отладки SQLAlchemy |

## API (основное)

| Метод | Путь | Auth |
|-------|------|------|
| POST | `/v1/auth/register` | нет |
| POST | `/v1/auth/login` | нет |
| GET/POST/PATCH/DELETE | `/v1/accounts` | да |
| GET/POST/PATCH/DELETE | `/v1/categories` | да |
| GET/POST/PATCH/DELETE | `/v1/transactions` | да |
| POST | `/v1/receipts/qr` | да |

Заголовок авторизации: `Authorization: Bearer <token>`

## Архитектура

```
app/
  api/v1/          # HTTP-контроллеры (тонкий слой)
  dto/             # Pydantic DTO между слоями
  services/        # Бизнес-логика
  repositories/    # Доступ к БД
  interfaces/      # Контракты внешних сервисов
  implementations/ # proverkacheka, GPT
  database/models  # SQLAlchemy-сущности
```

## Пример сценария

1. `POST /v1/auth/register` — создать пользователя
2. `POST /v1/accounts` — создать счёт
3. `POST /v1/transactions` — ручной расход
4. `POST /v1/receipts/qr` — загрузить QR чека

## Миграции

```bash
alembic upgrade head
alembic revision --autogenerate -m "описание"
```

## Сидеры

```bash
python scripts/seed_categories.py
```

Создаёт системные категории расходов (Продукты, Здоровье, Дом, …) и доходов (Зарплата, Подработка, …) с подкатегориями.

### Сброс товаров и чеков (для повторного теста)

```bash
python scripts/clean_receipt_data.py --all
```

Удаляет все QR-транзакции (с возвратом суммы на счета), товары и алиасы — чтобы снова проверить нормализацию Groq/GPT.

## Веб-приложение

Лёгкий клиент в папке [`web/`](web/):

```bash
# Backend на :8000, затем:
cd web && npm install && npm run dev
```

Откройте http://localhost:5173 — регистрация, счета, операции, QR-чеки.

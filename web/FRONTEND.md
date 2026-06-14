# Checkly — Frontend (справочник для AI)

Документ описывает **клиентскую часть** в `/finance_manager/web`. React + Vite + Capacitor, offline-first. Цель — быстро понять UI, слои данных и сборку APK.

Связанный документ: [`../BACKEND.md`](../BACKEND.md)

---

## 1. Что делает клиент

Мобильный и веб-клиент для Finance Manager / **Checkly alfa**:
- авторизация
- дашборд (баланс, категории, последние траты)
- список операций с фильтрами и навигацией по периодам
- ручное добавление дохода/расхода
- сканирование QR чека (нативно на Android, камера в браузере)
- счета, категории (свои + системные)
- **offline-first**: ручные операции и счета работают без сети, синхронизация при online

---

## 2. Стек

| Слой | Технология |
|------|------------|
| UI | React 18, TypeScript 5.6 |
| Сборка | Vite 4.5 |
| Роутинг | react-router-dom 6 |
| Стили | Tailwind CSS 3.4, DM Sans |
| Иконки | lucide-react |
| Mobile | Capacitor 6.2 (Android) |
| QR Android | @capacitor-mlkit/barcode-scanning |
| QR Web | html5-qrcode |
| Offline | idb (IndexedDB) |
| Alias | `@/*` → `src/*` |

Конфиги: `vite.config.ts`, `capacitor.config.ts`, `tailwind.config.js`, `tsconfig.json`

---

## 3. Структура каталогов

```
web/
├── index.html
├── package.json
├── vite.config.ts
├── capacitor.config.ts
├── .env.example                 # dev: пустой VITE_API_URL → proxy
├── .env.android.example         # шаблон для APK
├── .env.production.local        # gitignored, обязателен для APK
├── scripts/
│   ├── build-apk.sh
│   └── apply-android-icon.sh
├── resources/
│   └── checkly-icon-512.png
├── android/                     # Capacitor Android (gitignored)
└── src/
    ├── main.tsx                 # BrowserRouter
    ├── App.tsx                  # providers + routes
    ├── index.css                # Tailwind + .page-shell, safe-area
    ├── api/
    │   ├── client.ts            # HTTP, auth, types — НЕ импортировать из pages напрямую
    │   └── data-service.ts      # ★ главный фасад для UI
    ├── context/
    │   ├── AuthContext.tsx
    │   ├── AccountsContext.tsx
    │   └── SyncContext.tsx
    ├── pages/                   # экраны по роутам
    ├── components/
    │   ├── Layout.tsx
    │   ├── ProtectedRoute.tsx
    │   ├── CategoryIcon.tsx, CategoryPicker.tsx, CreateCategorySheet.tsx
    │   ├── ItemCategorySheet.tsx
    │   ├── QrCameraScanner.tsx
    │   ├── dashboard/           # sidebar desktop
    │   ├── mobile/              # PeriodNavigator, TxRow, FAB...
    │   └── ui/                  # Button, Card, Badge
    └── lib/
        ├── dates.ts             # периоды, timezone, parse/format
        ├── categories.ts
        ├── category-icons.ts
        ├── stats.ts
        ├── transactions.ts
        ├── connectivity.ts
        ├── data-events.ts
        ├── qr-scanner.ts
        ├── qr-payload.ts
        ├── utils.ts
        └── offline/
            ├── db.ts
            ├── cache.ts
            ├── queue.ts
            ├── sync.ts
            ├── temp-id-map.ts
            └── types.ts
```

### Главное правило импортов

**Страницы и компоненты импортируют `@/api/data-service`**, не `client.ts` напрямую.

Исключения: `AuthContext` (login/register), типы, `formatMoney`, `rublesToKopecks`.

---

## 4. Роутинг

`src/App.tsx`:

```
/login                    LoginPage (без Layout)

ProtectedRoute + AccountsProvider + Layout:
  /                       DashboardPage
  /transactions           TransactionsPage
  /add                    AddTransactionPage
  /qr                     QrPage
  /accounts               AccountsPage
  /categories             CategoriesPage
  /settings               SettingsPage
  *                       → redirect /
```

**Providers:**
```
AuthProvider
  └── SyncProvider
        └── Routes → ProtectedRoute → AccountsProvider → Layout → Outlet
```

`Layout.tsx`:
- Desktop (`lg+`): sidebar
- Mobile: bottom nav + FAB (Вручную / Чек)
- Nav скрыт на `/add`, `/qr`
- Баннеры offline/sync из `useSync()`

---

## 5. Auth

### Хранение (`src/api/client.ts`)

| Key | Значение |
|-----|----------|
| `fm_token` | JWT |
| `fm_user` | `{id, email, login, timezone}` |

### AuthContext

- `login` / `register`: **`clearOfflineData()`** → API → `setAuth`
- `logout`: clear offline + clear auth
- `setUnauthorizedHandler`: 401 → wipe offline + logout

### HTTP

Каждый запрос:
- `Authorization: Bearer ...`
- **`X-Timezone`** из `getUserTimezone()` (`Intl.DateTimeFormat`)

---

## 6. API client vs data-service

### client.ts — низкий уровень

- `API_BASE = import.meta.env.VITE_API_URL ?? ""`
- Пустой URL в dev → относительные `/v1/...` → **Vite proxy** на `:8000`
- APK/prod: **обязателен** `VITE_API_URL` при сборке
- Суммы в **копейках**; UI: `formatMoney()`, формы: `rublesToKopecks()`

Эндпоинты: `/v1/auth/*`, `/accounts`, `/categories`, `/transactions`, `/receipts/qr`

### data-service.ts — фасад (использовать в UI)

| Функция | Online | Offline |
|---------|--------|---------|
| `getAccounts` | API → cache | cache |
| `createAccount` / `deleteAccount` | API | queue + optimistic |
| `getCategories` | API → cache | cache |
| `create/update/deleteCategory` | API | **ошибка** |
| `getTransactions` | API → cache → merge | cache → merge |
| `createTransaction` | API | local tx + queue |
| `deleteTransaction` | API | hide + queue |
| `updateTransactionItem` | API | queue + patch cache |
| `scanQr` | API | **ошибка** |
| `prefetchCoreData` | warm cache | no-op |
| `processSyncQueue` | replay queue | no-op offline |

После мутаций: `notifyAccountsChanged()` / `notifyTransactionsChanged()`.

---

## 7. Offline-first

### IndexedDB (`lib/offline/db.ts`)

DB: `finance_manager`, version 1

| Store | Key | Содержимое |
|-------|-----|------------|
| `cache` | string | `{data, fetchedAt}` |
| `queue` | op id | `QueuedOp` |
| `localTransactions` | tx id | pending tx |
| `hiddenIds` | `{kind}:{id}` | soft-delete |

`clearOfflineData()` — при login/register/logout/401.

### Cache keys

- `accounts`
- `categories`
- `transactions:${JSON.stringify(params)}`
- `meta:tempIdMap` — маппинг `local_*` → server id

### Queue (`lib/offline/queue.ts`)

Типы операций: `createAccount`, `deleteAccount`, `createTransaction`, `deleteTransaction`, `updateTransactionItem`

Temp IDs: `local_${uuid}`

### Sync (`lib/offline/sync.ts`)

`processSyncQueue()` — FIFO, stop on first error, refresh cache, update temp-id-map.

### SyncContext

- `online`, `pendingCount`, `syncing`, `lastSyncAt`, `syncNow()`
- on reconnect → auto sync + prefetch

### Data events (`lib/data-events.ts`)

Pub/sub вне React: `subscribeAccountsChanged`, `subscribeTransactionsChanged`

---

## 8. Contexts

| Context | Hook | Scope | Данные |
|---------|------|-------|--------|
| AuthContext | `useAuth()` | App | user, login, register, logout |
| AccountsContext | `useAccounts()` | Protected | accounts, loading, refresh, primaryAccount |
| SyncContext | `useSync()` | App | online, pendingCount, syncing, syncNow |

---

## 9. Страницы

### DashboardPage (`/`)

- PeriodNavigator: day/week/month + стрелки назад/вперёд
- Баланс (sum accounts), расходы/доходы за период
- Top-5 категорий (`loadCategoryStats`)
- Последние 8 трат за неделю

### TransactionsPage (`/transactions`)

- PeriodNavigator (default: month)
- Фильтры: тип, счёт
- Группировка по дате (`groupByDate`)
- Expand row → позиции, удаление, `ItemCategorySheet`

### AddTransactionPage (`/add`)

- Сумма в рублях → kopecks
- expense/income, счёт, CategoryPicker, datetime-local
- `toApiDateTimeLocal()` — naive local ISO
- **работает offline**

### QrPage (`/qr`)

- **только online**
- Native scan (Capacitor ML Kit) / web camera
- `data.scanQr()` → список позиций
- Редактирование категорий позиций

### AccountsPage, CategoriesPage, SettingsPage

- Accounts: CRUD, offline create/delete
- Categories: системные + свои; create/delete **online only**
- Settings: профиль, links, logout

### LoginPage

- Tabs вход/регистрация, без Layout

---

## 10. Даты и периоды

Файл: `src/lib/dates.ts`

| Функция | Назначение |
|---------|------------|
| `getUserTimezone()` | IANA TZ → header `X-Timezone` |
| `getPeriodRange(period, anchor)` | day / week (пн–вс) / month |
| `shiftPeriodAnchor(period, anchor, ±1)` | стрелки навигации |
| `canGoPeriodNext()` | блок «в будущее» |
| `toApiDateTimeRange(from, to)` | `{from: YYYY-MM-DD, to: YYYY-MM-DD}` |
| `toApiDateTimeLocal(value)` | naive ISO для create tx |
| `parseApiDateTime(iso)` | naive = local wall clock |
| `formatTxDate(iso)` | Сегодня/Вчера/дата |

Компонент: `src/components/mobile/PeriodNavigator.tsx`

Offline merge фильтрует через `parseRangeBound()` в `cache.ts`.

---

## 11. Категории и иконки

### category-icons.ts

- `CATEGORY_ICON_MAP` — id → Lucide
- `CATEGORY_NAME_ICON/COLOR` — fallback для системных имён
- `PRESET_CATEGORY_ICONS/COLORS` — UI создания

### CategoryIcon.tsx

Отображение: цветной круг + иконка.

### categories.ts

`getRootCategories`, `getSubcategories`, `buildCategoryDisplayMap`, ...

### CRUD

| Действие | Offline |
|----------|---------|
| List | ✅ cache |
| Create custom | ❌ |
| Delete custom | ❌ |
| Patch item category | ✅ queue |

**Чеки** используют только **системные** категории (бэкенд + LLM).

Компоненты: `CategoryPicker`, `CreateCategorySheet`, `ItemCategorySheet`

---

## 12. Мобильные компоненты

| Файл | Назначение |
|------|------------|
| `PeriodNavigator` | табы + ← label → |
| `PeriodTabs` | День / Неделя / Месяц |
| `TxRow` | строка операции |
| `PageHeader` | заголовок экрана |
| `FabActionMenu` | FAB: Вручную / Чек |
| `MenuRow` | пункт меню Settings |

CSS: `.page-shell`, `pb-safe-b`, `env(safe-area-inset-bottom)`

---

## 13. Capacitor и APK

### capacitor.config.ts

```typescript
appId: "com.financemanager.app"
appName: "Checkly alfa"
webDir: "dist"
server.androidScheme: "http"   // HTTP API из WebView
```

### Env для сборки

| Файл | Когда |
|------|-------|
| `.env` | dev, пустой VITE_API_URL |
| `.env.production.local` | **APK build** — `VITE_API_URL=http://IP:8000` |

`VITE_API_URL` **вшивается при build** — смена URL = пересборка.

### Сборка

```bash
cd web
# .env.production.local:
# VITE_API_URL=http://193.33.153.105:8000

npm run android:apk
# → android/app/build/outputs/apk/debug/checkly-alfa.apk
```

Скрипт `scripts/build-apk.sh`:
1. JDK 17
2. проверка `.env.production.local`
3. `apply-android-icon.sh`
4. `cap:sync` (build + sync)
5. `gradlew assembleDebug`

Иконка: `resources/checkly-icon-512.png` → mipmap через `sips`.

### API URL по среде

| Среда | VITE_API_URL |
|-------|--------------|
| Browser dev | пусто (proxy) |
| Телефон Wi‑Fi | `http://192.168.x.x:8000` |
| Emulator | `http://10.0.2.2:8000` |
| VPS | `http://IP:8000` |

---

## 14. Vite

`vite.config.ts`:
- `base: "./"` — для Capacitor WebView
- proxy `/v1`, `/health` → `127.0.0.1:8000`
- alias `@` → `./src`

Dev: `npm run dev` → `:5173`

---

## 15. Конвенции для правок

### Делать

- Читать/писать через **`data-service`**
- Суммы: **`rublesToKopecks` / `formatMoney`**
- Фильтры транзакций: **`getPeriodRange` + `toApiDateTimeRange`**
- Списки tx: подписка **`subscribeTransactionsChanged`**
- Счета: **`useAccounts()`**
- QR и CRUD категорий: проверять **`useSync().online`**

### Не делать

- `api.*` из pages (кроме auth)
- Думать что API в рублях — только **копейки**
- Category create offline
- Менять API URL без rebuild APK

### Offline flow

```
UI action
  → data-service (enqueue + optimistic cache/local tx)
  → online
  → SyncContext.syncNow()
  → processSyncQueue()
  → API + temp-id-map
  → refresh cache + notify*
```

---

## 16. npm scripts

| Script | Действие |
|--------|----------|
| `npm run dev` | Vite :5173 |
| `npm run build` | tsc + vite → dist |
| `npm run cap:sync` | build + cap sync android |
| `npm run android` | sync + Android Studio |
| `npm run android:apk` | debug APK |
| `npm run android:apk:release` | release APK |

---

## 17. Быстрые ссылки

| Задача | Файл |
|--------|------|
| Новая страница | `src/pages/` + `App.tsx` route |
| API вызов из UI | `src/api/data-service.ts` |
| HTTP/types | `src/api/client.ts` |
| Offline DB | `src/lib/offline/db.ts` |
| Cache merge | `src/lib/offline/cache.ts` |
| Sync | `src/lib/offline/sync.ts` |
| Периоды/даты | `src/lib/dates.ts` |
| Period UI | `src/components/mobile/PeriodNavigator.tsx` |
| Auth | `src/context/AuthContext.tsx` |
| Layout/nav | `src/components/Layout.tsx` |
| APK | `scripts/build-apk.sh` |

---

## 18. Запуск

```bash
# Backend (из корня репо)
docker compose up -d

# Frontend dev
cd web && npm install && npm run dev
# http://localhost:5173 — API через proxy
```

Для теста на телефоне в LAN: `VITE_API_URL=http://<mac-ip>:8000` в `.env.production.local` + `npm run android:apk`, CORS на бэке через `CORS_ORIGINS`.

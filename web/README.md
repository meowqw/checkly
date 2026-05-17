# Checkly Web

Веб-клиент в стиле светлого dashboard для Finance Manager API.

## Стек

- React 18 + TypeScript
- Tailwind CSS
- Lucide Icons
- Vite
- [Capacitor](https://capacitorjs.com/) — упаковка в Android-приложение

## Запуск (браузер)

```bash
# Backend на :8000
cd web
npm install
npm run dev
```

http://localhost:5173

## Android-приложение

Тот же React-код упаковывается в нативную оболочку (WebView). Отдельный React Native не нужен.

### Что установить

1. [Android Studio](https://developer.android.com/studio) (SDK, эмулятор)
2. Node.js 18+
3. Backend API доступен с телефона по сети

### Сборка APK без Android Studio

Нужны только **JDK 17+** и **Android SDK** (командная строка, без IDE).

1. **Java**

```bash
brew install openjdk@17
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
```

2. **Android SDK** (если ещё нет папки `~/Library/Android/sdk`)

- Скачайте [Command line tools](https://developer.android.com/studio#command-tools) (не полную Studio)
- Распакуйте в `~/Library/Android/sdk/cmdline-tools/latest/`
- Добавьте в `~/.zshrc`:

```bash
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin
```

- Установите пакеты:

```bash
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
```

3. **URL API и сборка**

```bash
cd web
cp .env.android.example .env.production.local
# VITE_API_URL=http://192.168.x.x:8000

npm run android:apk
```

Готовый файл:

`web/android/app/build/outputs/apk/debug/app-debug.apk`

Скопируйте на телефон и установите (разрешите установку из неизвестных источников).

Release-версия для магазина требует подписи ключом: `npm run android:apk:release` (нужен keystore).

### Сборка через Android Studio (опционально)

```bash
npm run android
```

Откроется IDE → **Run** на эмуляторе или телефоне.

### Повторная сборка после правок UI

```bash
npm run cap:sync
# в Android Studio: Run
```

### API с телефона

| Где запущен backend | `VITE_API_URL` |
|---------------------|----------------|
| Mac/PC, телефон в той же Wi‑Fi | `http://192.168.x.x:8000` |
| Эмулятор Android Studio | `http://10.0.2.2:8000` |
| VPS в интернете | `https://ваш-домен` |

В корневом `.env` backend при необходимости:

```env
CORS_ORIGINS=http://192.168.1.10:5173
```

Docker: пробросьте порт `8000:8000`, на телефоне используйте IP хоста.

Для HTTP (не HTTPS) на Android 9+ в `android/app/src/main/AndroidManifest.xml` может понадобиться `android:usesCleartextTraffic="true"` в `<application>` — Capacitor иногда добавляет это при `add android`; если запросы не идут, включите вручную.

### QR-камера

На странице «Сканировать чек» кнопка **«Сканировать камерой»**:

- **Android-приложение** — нативный сканер Google ML Kit (`@capacitor-mlkit/barcode-scanning`)
- **Браузер** — камера через `html5-qrcode` (нужен HTTPS или localhost)

После `npx cap add android` и `npm run cap:sync` в `android/app/src/main/AndroidManifest.xml` должны быть:

```xml
<uses-permission android:name="android.permission.CAMERA" />
```

Если запросы по HTTP к API не проходят, добавьте в `<application>`:

```xml
android:usesCleartextTraffic="true"
```

### Альтернативы

| Вариант | Плюсы | Минусы |
|---------|--------|--------|
| **Capacitor** (настроено) | Один код с вебом, APK, Play Store | Нужен Android Studio |
| **PWA** | Без магазина, «Добавить на экран» | Слабее интеграция с ОС |
| **React Native** | Нативный UX | Переписывать UI |

## Экраны

- **Главная** — метрики, категории расходов (прогресс-бары), последние траты, переключатель периода
- **Счета** — создание и удаление
- **Транзакции** — список с фильтрами
- **Категории** — дерево системных категорий
- **Добавить трату** / **Сканировать чек** — отдельные формы
- **Настройки** — профиль и выход

## Требования

Node.js 16+ (рекомендуется 18+)

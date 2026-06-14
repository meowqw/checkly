# Деплой backend на Ubuntu (чистый сервер)

Нужны: **Docker**, **Git**, файл `.env`. Android Studio и Node на сервере **не нужны** (фронт собираете локально или отдельно).

---

## Без домена (только IP) — самый простой вариант

Домен **не нужен**. API будет по адресу `http://ВАШ_IP:8000`.

### 1–4. Docker, git clone, `.env`

Как ниже, но в `.env` добавьте (подставьте IP сервера):

```env
CORS_ORIGINS=http://123.45.67.89:8000,capacitor://localhost,https://localhost
```

`123.45.67.89` — публичный IP VPS.

### 5. Запуск с открытым портом 8000

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.prod-ip.yml up -d --build
```

### 6. Файрвол

```bash
sudo ufw allow OpenSSH
sudo ufw allow 8000/tcp
sudo ufw enable
```

### 7. Проверка

С **вашего Mac** (не с сервера):

```bash
curl http://123.45.67.89:8000/health
```

В браузере: `http://123.45.67.89:8000/docs`

### APK без домена

На Mac в `web/.env.production.local`:

```env
VITE_API_URL=http://123.45.67.89:8000
```

```bash
npm run cap:sync && npm run android:apk
```

В APK уже включён HTTP (`usesCleartextTraffic`) — для IP это нормально.

**Минусы без домена:** нет HTTPS (трафик не шифруется), IP может смениться у некоторых хостингов. Для личного MVP это обычно ок.

---

## С доменом (HTTPS) — опционально позже

Если купите домен — см. раздел 6 ниже (Nginx + certbot).

---

## 1. Подключитесь к серверу

```bash
ssh user@YOUR_SERVER_IP
```

## 2. Установите Docker

```bash
sudo apt update
sudo apt install -y ca-certificates curl git

curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Выйдите из SSH и зайдите снова (чтобы группа `docker` применилась), либо:

```bash
newgrp docker
```

Проверка:

```bash
docker --version
docker compose version
```

## 3. Клонируйте проект

```bash
cd ~
git clone https://github.com/YOUR_USER/finance_manager.git
cd finance_manager
```

(или свой URL репозитория)

## 4. Настройте `.env`

```bash
cp .env.example .env
nano .env
```

**Обязательно смените** (не оставляйте значения из example):

| Переменная | Пример |
|------------|--------|
| `MYSQL_ROOT_PASSWORD` | длинный случайный пароль |
| `MYSQL_PASSWORD` | другой длинный пароль |
| `JWT_SECRET` | случайная строка 32+ символов |
| `PROVERKACHEKA_TOKEN` | ваш токен |
| `GROQ_API_KEY` или `OPENAI_API_KEY` | для нормализации товаров |
| `PRODUCT_NORMALIZER` | `groq` |

Для мобильного приложения / фронта (с доменом):

```env
CORS_ORIGINS=https://your-frontend.com,capacitor://localhost
```

Без домена — см. раздел **«Без домена»** в начале файла.

Сгенерировать секрет:

```bash
openssl rand -hex 32
```

## 5. Запустите API

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Проверка:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}

docker compose -f docker-compose.prod.yml logs -f app
```

Снаружи пока API **не виден** — порт привязан к `127.0.0.1:8000` (только с сервера). Так безопаснее.

## 6. Nginx + HTTPS (рекомендуется)

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo nano /etc/nginx/sites-available/finance-api
```

Скопируйте содержимое из `deploy/nginx-api.conf.example`, замените `api.example.com`.

```bash
sudo ln -s /etc/nginx/sites-available/finance-api /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d api.example.com
```

Откройте в браузере: `https://api.example.com/docs`

## 7. Файрвол

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

Порт `8000` наружу **не открывайте**, если стоит Nginx.

## Обновление после `git pull`

```bash
cd ~/finance_manager
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## Полезные команды

```bash
# Логи
docker compose -f docker-compose.prod.yml logs -f app

# Остановить
docker compose -f docker-compose.prod.yml down

# Остановить и удалить БД (осторожно!)
docker compose -f docker-compose.prod.yml down -v
```

## Подключение фронта / APK

В `web/.env.production.local` (сборка на своём Mac):

```env
VITE_API_URL=https://api.example.com
```

Пересоберите APK: `npm run android:apk`

## Без Docker (не рекомендуется)

Можно поставить Python 3.11, MySQL 8, venv и systemd — но Docker проще для обновлений. Если нужно — напишите, добавим unit-файл.

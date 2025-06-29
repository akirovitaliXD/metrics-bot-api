# Server Metrics Hub

FastAPI-сервис и Telegram-бот для лёгкого мониторинга серверов.

## Возможности

- Сбор нагрузки CPU и использования RAM с нескольких Linux-серверов по SSH (по умолчанию каждые 5 минут, настраивается).
- Хранение метрик 30 дней в SQLite (можно переключиться на PostgreSQL).
- REST-API (FastAPI) с интерактивной документацией `/docs`.
- Telegram-бот (aiogram): строит графики, инлайн-клавиатура, разграничение доступа по пользователям, мультиязычный интерфейс.
- Развёртывание одним контейнером (Dockerfile), совместим с Pterodactyl (`Docker Build` egg).
- Настройка через файл `.env` (шаблон `env.example`).

## Быстрый старт локально

```bash
git clone https://github.com/<you>/metrics-bot-api.git
cd metrics-bot-api
cp env.example .env   # заполните TELEGRAM_TOKEN и др.
docker compose up --build
```

Доступ:
- Swagger: http://localhost:8000/docs
- Бот: напишите ему `/start` в Telegram

## Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|------------|----------|-----------------------|
| TELEGRAM_TOKEN | токен бота | — |
| SUPER_ADMIN_ID | ID супер-админа Telegram | 0 |
| USER_ACCESS | правила доступа `uid:servers;…` | (пусто) |
| DATABASE_URL | строка подключения к БД | `sqlite:////mnt/server/metrics.db` |
| FETCH_INTERVAL | период опроса, сек | 300 |
| API_BASE_URL | URL, по которому бот обращается к API | `http://localhost:8000` |

## Структура проекта
```
.
├─ Dockerfile
├─ docker-compose.yml  # для локального запуска
├─ requirements.txt
├─ main.py             # FastAPI
├─ config.py           # загрузка .env
├─ db/                 # БД, модели, планировщик
├─ bot/                # Telegram-бот
├─ lang/               # файлы переводов
└─ env.example
```

## Развёртывание в Pterodactyl (кратко)
1. Репозиторий с Dockerfile доступен узлу Wings.
2. Создайте Egg «Docker Build», укажите Git-URL, команду запуска:
   ```
   uvicorn main:app --host 0.0.0.0 --port ${SERVER_PORT}
   ```
3. Задайте переменные окружения (TELEGRAM_TOKEN и др.).
4. Создайте сервер, нажмите **Reinstall**, дождитесь сборки, затем **Start**.

Подробная инструкция — в английском README в разделе «Deploy on Pterodactyl». 
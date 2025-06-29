# Server Metrics Hub

FastAPI service and Telegram bot for lightweight server monitoring.

## Features

- Collects CPU load and memory usage from multiple Linux servers over SSH (default every 5 min, configurable).
- Stores metrics for **30 days** in SQLite (can switch to PostgreSQL via `DATABASE_URL`).
- RESTful API with OpenAPI docs at `/docs` (FastAPI).
- Telegram bot (aiogram) shows graphs, supports inline buttons, per-user access rules, multi-language UI (i18n).
- Single-container deployment, ready for Docker / Pterodactyl (Docker Build egg).
- Simple configuration via `.env` file (see `env.example`).

## Quick start (local)

```bash
# clone
git clone https://github.com/<you>/metrics-bot-api.git
cd metrics-bot-api

# configure
cp env.example .env              # fill in TELEGRAM_TOKEN etc.

# build & run
docker compose up --build
```

Access:
- Swagger UI: http://localhost:8000/docs
- Telegram: open your bot, send `/start`

## Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| TELEGRAM_TOKEN | Token of your Telegram bot | – |
| SUPER_ADMIN_ID | Telegram user ID with full access | 0 |
| USER_ACCESS | Mapping `uid:server_ids;...` | `` |
| DATABASE_URL | DB connection string | `sqlite:////mnt/server/metrics.db` |
| FETCH_INTERVAL | Metric fetch period (s) | `300` |
| API_BASE_URL | URL the bot uses to reach API | `http://localhost:8000` |

## Project structure

```
.
├─ Dockerfile           # build single container
├─ docker-compose.yml   # local convenience (not used by Pterodactyl)
├─ requirements.txt
├─ main.py              # FastAPI entrypoint
├─ config.py            # env loader
├─ db/                  # models, scheduler, engine
├─ bot/                 # aiogram bot (handlers, utils, states)
├─ lang/                # i18n JSON files
└─ env.example
```

## Deploy on Pterodactyl (short)

1. Ensure Dockerfile uses `$SERVER_PORT` (already set).
2. Create an Egg with Docker Build enabled, pointing to your Git repo.
3. Set startup command:
   ```
   uvicorn main:app --host 0.0.0.0 --port ${SERVER_PORT}
   ```
4. Add environment variables (TELEGRAM_TOKEN, etc.).
5. Create server, reinstall -> start. Swagger will be available on assigned port.

See documentation in `README_RU.md` for a detailed step-by-step Russian guide. 
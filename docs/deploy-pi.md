# Deploy on Raspberry Pi (Docker)

## Environment

Copy `.env.example` to `.env` and set JWT + Kasa credentials. Set `TZ` for plug schedules.

Enable BuildKit for faster repeat builds:

```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

## When to rebuild vs restart

| Change | Action |
|--------|--------|
| Python code under `server/` only | `docker compose restart server` (code is bind-mounted to `/code`) |
| `server/requirements.txt` or `server/dockerfile` | `docker compose build server && docker compose up -d server` |
| Console HTML/JS/CSS only | Refresh browser (console is mounted at `/usr/share/nginx/html`) |
| `console/dockerfile` or nginx config | `docker compose build console && docker compose up -d console` |
| Both services, full rebuild | `docker compose build` (prefer `docker compose build server` if UI unchanged) |

Avoid `docker compose up --build` on every edit; use `--no-build` when containers already exist:

```bash
docker compose up -d --no-build
```

## Verify API after deploy

```bash
docker compose logs server --tail 30
docker compose exec server python -c "import main"
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8167/ping
```

A **502** from `/plants/api/*` usually means the server worker failed to import `main` — check logs for tracebacks.

## Build context

`server/.dockerignore` excludes `venv/`, `uploads/`, `database.db`, and other local data so Pi builds stay smaller and layer cache is stable.

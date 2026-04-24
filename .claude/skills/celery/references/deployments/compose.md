---
name: Celery Docker Compose Deployment
description: Docker Compose patterns for celery beat, workers, and off-host worker scaling
---

# Docker Compose Deployment

## Standard Layout

```yaml
services:
  backend:
    build: ./backend
    command: gunicorn app.wsgi:application -b 0.0.0.0:8000

  celery-beat:
    build: ./backend
    command: celery -A proj beat -l info
    depends_on: [redis]
    deploy:
      replicas: 1  # CRITICAL: never more than 1 beat instance

  celery-worker:
    build: ./backend
    command: celery -A proj worker -Q default -c 4 -l info --pool=prefork
    depends_on: [redis, backend]
    deploy:
      replicas: 2  # scale horizontally

  celery-worker-io:
    build: ./backend
    command: celery -A proj worker -Q api_tasks -P gevent -c 100 -l info
    depends_on: [redis]

  redis:
    image: redis:7-alpine
```

## Off-Host Workers (No DB Access)

Workers on a separate host connect only to the broker. Use a lightweight settings
module with no `DATABASES` config.

```yaml
# docker-compose.worker.yaml — runs on separate host
services:
  celery-worker:
    image: ghcr.io/org/backend:latest
    command: celery -A proj worker -Q api_tasks -l info -P gevent -c 100
    environment:
      DJANGO_SETTINGS_MODULE: config.settings_celery_light
      CELERY_BROKER_URL: redis://broker-host:6379/1
      INTERNAL_API_URL: https://api.example.com/api/internal
      INTERNAL_SERVICE_TOKEN: ${INTERNAL_SERVICE_TOKEN}
    # No database volumes — tasks use REST API
```

## Beat With DB Access (DatabaseScheduler)

When beat needs runtime-editable schedules, mount the DB and use full settings:

```yaml
  celery-beat:
    build: ./backend
    command: >
      celery -A proj beat -l info
      --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      DJANGO_SETTINGS_MODULE: backend.settings
    volumes:
      - ./backend/db.sqlite3:/app/backend/prod.db.sqlite3
    deploy:
      replicas: 1
```

## Beat Without DB (Static Schedule)

Define schedule in code. No DB volume needed:

```yaml
  celery-beat:
    build: ./backend
    command: celery -A proj beat -l info
    environment:
      DJANGO_SETTINGS_MODULE: config.settings_celery_light
      CELERY_BROKER_URL: redis://redis:6379/1
```

## Health Checks

```yaml
  celery-worker:
    healthcheck:
      test: ["CMD", "celery", "-A", "proj", "inspect", "ping", "-t", "10"]
      interval: 30s
      timeout: 15s
      retries: 3
```

## Scaling Workers

```bash
# Scale up workers
docker compose up -d --scale celery-worker=4

# Scale IO workers independently
docker compose up -d --scale celery-worker-io=8
```

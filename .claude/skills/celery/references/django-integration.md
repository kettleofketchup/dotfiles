---
name: Celery Django Integration
description: Django celery setup, settings patterns, lightweight worker settings, beat schedulers
---

# Django + Celery Integration

## Project Layout

```
proj/
  config/
    __init__.py
    celery.py              # Full celery app (with DB)
    celery_light.py        # Lightweight celery app (no DB, API-only workers)
    settings.py            # Full Django settings
    settings_celery.py     # Minimal settings for light workers
```

## Full Celery App (celery.py)

```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("proj")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

## Lightweight Celery App (celery_light.py)

For workers that use REST API instead of ORM:

```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_celery")

import django
django.setup()

app = Celery("proj")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

## Minimal Settings (settings_celery.py)

```python
"""Minimal Django settings — no ORM, no middleware. Workers use REST API."""
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = "celery-worker-not-serving-http"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "myapp",  # for task autodiscovery
]

DATABASES = {}  # no DB access — tasks call backend via HTTP

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:6379/1"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:6379/1"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

INTERNAL_SERVICE_TOKEN = os.environ.get("INTERNAL_SERVICE_TOKEN", "")
AUTH_USER_MODEL = "myapp.CustomUser"  # if models import AbstractUser
```

## Full Settings With DB (for beat or ORM workers)

Add database config to the minimal settings when workers need ORM:

```python
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

## Beat Schedule — Static (Code-Defined)

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    "cleanup-hourly": {
        "task": "app.tasks.cleanup_expired",
        "schedule": crontab(minute=0),
    },
    "sync-every-minute": {
        "task": "app.tasks.sync_data",
        "schedule": 60.0,
    },
}
```

## Beat Schedule — Dynamic (django-celery-beat)

```bash
pip install django-celery-beat
```

```python
# settings.py
INSTALLED_APPS += ["django_celery_beat"]
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
```

Schedules editable via Django admin at runtime. Beat process needs DB access.

## Internal HTTP Client Pattern

For tasks running on workers without DB access:

```python
import os, requests

API_URL = os.environ.get("INTERNAL_API_URL", "http://backend:8000/api/internal")

def _headers():
    return {
        "X-Internal-Token": os.environ.get("INTERNAL_SERVICE_TOKEN", ""),
        "Content-Type": "application/json",
    }

def get_resource(resource_id):
    resp = requests.get(f"{API_URL}/resources/{resource_id}/", headers=_headers())
    resp.raise_for_status()
    return resp.json()
```

---
name: Celery Result Backends
description: Redis, RPC, database, and disabled result backends with configuration and tradeoffs
---

# Result Backends

## Comparison

| Backend | Speed | Persistence | Multi-Read | Best For |
|---------|-------|-------------|------------|----------|
| Redis | Fast | AOF optional | Yes | Most production use |
| RPC (AMQP) | Fast | No | No (single read) | Fire-and-consume-once |
| Database | Slow | Yes | Yes | Audit trails, low volume |
| Disabled | N/A | N/A | N/A | Fire-and-forget tasks |

## Redis Backend (Recommended)

```python
# settings.py or celery.py
app.conf.result_backend = "redis://redis:6379/1"
app.conf.result_expires = 3600          # auto-cleanup after 1 hour
app.conf.result_backend_thread_safe = True

# Use a different Redis DB than the broker to isolate concerns
# Broker: redis://redis:6379/0
# Results: redis://redis:6379/1
```

### Reading Results

```python
result = my_task.delay(arg)
result.id          # task UUID
result.status      # PENDING, STARTED, SUCCESS, FAILURE, RETRY
result.get(timeout=30)  # block until result (use sparingly)
result.ready()     # non-blocking check

# Group results
from celery import group
job = group(task.s(i) for i in range(10))
result = job.apply_async()
result.get()       # list of all results
```

## RPC Backend

Results sent back via AMQP reply queue. Each result can only be read once:

```python
app.conf.result_backend = "rpc://"
app.conf.result_persistent = False  # faster, results lost on broker restart
```

Use when: caller consumes result immediately, no need for persistence or re-reads.

## Database Backend

```python
# Requires: pip install django-celery-results
INSTALLED_APPS = ["django_celery_results"]

app.conf.result_backend = "django-db"
app.conf.result_extended = True  # store task args/kwargs in DB
```

Use when: need audit trails, task history dashboard, low task volume.
Avoid when: high throughput — each result is a DB write.

## Disabled (Fire-and-Forget)

```python
app.conf.result_backend = None

# Or per-task
@app.task(ignore_result=True)
def send_email(to, subject, body): ...
```

Best performance. Use for tasks where the caller never checks the result.
This is the default when `result_backend` is not configured.

## Ignoring Results Selectively

```python
# Global default: store results
app.conf.result_backend = "redis://redis:6379/1"

# But ignore for high-volume fire-and-forget tasks
@app.task(ignore_result=True)
def log_analytics_event(event_data): ...

# And store for tasks that need tracking
@app.task
def generate_report(report_id):
    # caller will poll result.status
    return {"url": f"/reports/{report_id}.pdf"}
```

## Result Expiration

```python
# Global TTL
app.conf.result_expires = 86400  # 24 hours

# Per-task override
@app.task(result_expires=300)  # 5 minutes
def short_lived_task(): ...
```

Always set `result_expires` to prevent unbounded storage growth.

## Chords and Callbacks

Result backends are **required** for chords (callback after group completes):

```python
from celery import chord

# This NEEDS a result backend
callback = summarize.s()
header = [fetch_data.s(url) for url in urls]
chord(header)(callback)
```

If using `result_backend = None`, chords will fail silently. Either enable
a backend or restructure as a chain of tasks.

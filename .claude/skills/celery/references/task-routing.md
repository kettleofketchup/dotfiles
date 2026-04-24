---
name: Celery Task Routing
description: Multi-queue routing, worker specialization, when to use separate queues vs single queue
---

# Task Routing and Queue Architecture

## Defining Queues

```python
# celery.py or settings.py
from kombu import Queue

app.conf.task_queues = (
    Queue("default", routing_key="task.#"),
    Queue("db_tasks", routing_key="db.#"),
    Queue("api_tasks", routing_key="api.#"),
    Queue("critical", routing_key="critical.#"),
)

app.conf.task_default_queue = "default"
```

## Routing Tasks to Queues

```python
# Automatic routing by task name pattern
app.conf.task_routes = {
    "app.tasks.sync_*": {"queue": "api_tasks"},
    "steam.tasks.*": {"queue": "db_tasks"},
    "events.tasks.send_*": {"queue": "critical"},
}

# Or per-task decorator
@app.task(queue="api_tasks")
def call_external_api(payload): ...

# Or at call time
call_external_api.apply_async(args=[payload], queue="critical")
```

## Starting Specialized Workers

```bash
# DB worker: low concurrency, prefork (CPU-bound ORM queries)
celery -A proj worker -Q db_tasks -c 4 --prefetch-multiplier=1

# API worker: high concurrency, gevent (I/O-bound HTTP calls)
celery -A proj worker -Q api_tasks -P gevent -c 100

# Critical worker: single task at a time, guaranteed ordering
celery -A proj worker -Q critical -c 1 --prefetch-multiplier=1

# Mixed worker: handles multiple queues
celery -A proj worker -Q default,api_tasks -c 8
```

## When to Use Multiple Queues

**Use separate queues when:**
- Tasks have different SLAs (send email in <5s vs generate report in <5m)
- Tasks have different resource profiles (CPU-heavy vs I/O-heavy)
- Tasks have different failure domains (external API failures shouldn't block DB tasks)
- Need to scale worker types independently
- Some workers must be off-host (no DB access)

**Single queue is fine when:**
- All tasks are homogeneous (similar runtime, similar resources)
- Low task volume (<1000/hour)
- No need for independent scaling

## Worker Pool Selection

| Pool | Best For | Flag | Concurrency |
|------|----------|------|-------------|
| prefork | CPU-bound, ORM queries | `-P prefork` | `-c` = CPU count |
| gevent | I/O-bound, HTTP calls | `-P gevent` | `-c 100-500` |
| solo | Debugging, single-task | `-P solo` | always 1 |

gevent uses ~63% less RAM than prefork at equivalent concurrency.

## Priority Queues

```python
# Higher priority = consumed first (with Redis broker)
app.conf.task_queues = (
    Queue("critical", queue_arguments={"x-max-priority": 10}),
    Queue("default", queue_arguments={"x-max-priority": 5}),
    Queue("low", queue_arguments={"x-max-priority": 1}),
)

# Send with priority
send_notification.apply_async(args=[user_id], priority=9)
```

## Rate Limiting

```python
# Per-task rate limit
@app.task(rate_limit="100/m")  # max 100 per minute
def call_discord_api(payload): ...

@app.task(rate_limit="10/s")   # max 10 per second
def send_webhook(url, data): ...
```

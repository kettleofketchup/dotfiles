---
name: Celery Performance Optimization
description: Prefetch, connection pooling, concurrency tuning, retries, and efficiency patterns
---

# Performance Optimization

## Prefetch Multiplier

Controls how many tasks a worker pre-fetches from the broker:

```python
# Short tasks (<1s): higher prefetch reduces broker round-trips
app.conf.worker_prefetch_multiplier = 4   # default

# Long tasks (>30s): set to 1 to prevent one worker hoarding tasks
app.conf.worker_prefetch_multiplier = 1
```

Set to `0` for unlimited prefetch (not recommended for mixed workloads).

## Connection Pooling

```python
# Broker connection pool (match to active worker threads)
app.conf.broker_pool_limit = 10

# For gevent workers, increase pool size
app.conf.broker_pool_limit = 50

# Connection retry on startup
app.conf.broker_connection_retry_on_startup = True
```

## Late Acknowledgement

Tasks are acked after completion instead of at receipt. Ensures tasks are
re-delivered if a worker crashes mid-execution:

```python
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1  # pair with late ack

# IMPORTANT: tasks must be idempotent when using late ack
```

## Task Compression

Reduce broker bandwidth for large payloads:

```python
app.conf.task_compression = "gzip"  # or "bzip2", "zstd"
```

## Task Time Limits

```python
# Hard kill after 5 minutes (SIGKILL)
app.conf.task_time_limit = 300

# Soft limit raises SoftTimeLimitExceeded after 4 minutes
app.conf.task_soft_time_limit = 240

# Per-task override
@app.task(soft_time_limit=60, time_limit=120)
def bounded_task(): ...
```

## Retry Patterns

### Automatic Retry with Exponential Backoff

```python
@app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,        # 1s, 2s, 4s, 8s...
    retry_backoff_max=600,     # cap at 10 minutes
    retry_jitter=True,         # randomize to prevent thundering herd
    max_retries=5,
)
def resilient_task(self, data):
    return call_external_service(data)
```

### Manual Retry

```python
@app.task(bind=True, max_retries=3)
def manual_retry_task(self, data):
    try:
        do_work(data)
    except TransientError as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

## Batch Operations

Avoid N+1 task dispatch. Send bulk data in one task:

```python
# BAD: 1000 individual tasks
for user_id in user_ids:
    process_user.delay(user_id)

# GOOD: batch task with chunking
from celery import group
chunks = [user_ids[i:i+100] for i in range(0, len(user_ids), 100)]
group(process_user_batch.s(chunk) for chunk in chunks).apply_async()
```

## Task Design Rules

1. **Keep tasks small** — pass IDs not objects (serialization cost)
2. **Make tasks idempotent** — safe to retry without side effects
3. **Avoid DB queries in task arguments** — fetch inside the task
4. **Set `ignore_result=True`** for fire-and-forget tasks
5. **Use `bind=True`** when accessing `self.request` or `self.retry`

```python
# BAD: passing ORM object (serialization failure)
process_order.delay(order)

# GOOD: pass ID, fetch inside task
process_order.delay(order.id)
```

## Monitoring

```bash
# Real-time task events
celery -A proj events

# Inspect active tasks
celery -A proj inspect active

# Queue lengths (Redis)
redis-cli LLEN default
redis-cli LLEN api_tasks

# Flower web dashboard
pip install flower
celery -A proj flower --port=5555
```

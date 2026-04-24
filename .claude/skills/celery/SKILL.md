---
name: celery
description: Celery distributed task queue with Django. Task routing, off-host workers, beat scheduling, result backends, retries, optimization.
version: 1.0.0
---

# Celery Distributed Task Queue

Celery 5.x with Django. Covers distributed workers, task routing, beat scheduling,
result backends, and deployment patterns (Compose, K8s, VMs).

## Core Architecture

- **Beat**: Single-instance scheduler. Never scale beyond 1 replica.
- **Workers**: Stateless consumers. Scale horizontally. Can run off-host.
- **Broker**: Redis or RabbitMQ. The only shared dependency between beat and workers.

## Two Worker Models

### 1. ORM Workers (DB Access)
Use full Django settings. Tasks import models directly. Must have DB connectivity.
Best for: data migrations, aggregation queries, ORM-heavy operations.

### 2. API Workers (No DB Access)
Use lightweight Django settings with `DATABASES = {}`. Tasks call the backend
REST API via HTTP. Can run on separate hosts with only broker access.
Best for: external API calls, notifications, webhooks, event processing.

See `references/django-integration.md` for settings patterns and internal HTTP client.

## Decision: When Tasks Need DB vs API

| Signal | Use ORM Worker | Use API Worker |
|--------|---------------|----------------|
| Single DB query + write | Yes | No |
| Calls external APIs | No | Yes |
| Runs on separate host | No | Yes |
| Needs Django admin models | Yes | No |
| High I/O concurrency needed | No | Yes (gevent) |
| Must survive backend downtime | Yes | No |

## Beat Scheduling

**Static schedule** (code-defined): No DB needed. Define `app.conf.beat_schedule` in celery app.
**Dynamic schedule** (`django-celery-beat`): Editable via Django admin. Beat needs DB access.

See `references/django-integration.md` for both patterns.

## Quick Reference

| Topic | Reference |
|-------|-----------|
| Django settings, celery apps, beat schedulers | `references/django-integration.md` |
| Queue definitions, worker pools, rate limiting | `references/task-routing.md` |
| Redis/RPC/DB/disabled backends, chords | `references/result-backends.md` |
| Prefetch, retries, batching, monitoring | `references/optimization.md` |
| Docker Compose deployment | `references/deployments/compose.md` |
| Kubernetes deployment + HPA | `references/deployments/k8s.md` |
| VM/systemd deployment | `references/deployments/vm.md` |

## Key Rules

1. **Beat is a singleton** — always `replicas: 1`, use `Recreate` strategy in K8s
2. **Pass IDs not objects** — `task.delay(order_id)` not `task.delay(order)`
3. **Make tasks idempotent** — safe to retry without side effects
4. **Set `ignore_result=True`** on fire-and-forget tasks
5. **Use `task_acks_late=True`** with `prefetch_multiplier=1` for crash safety
6. **Set time limits** — `task_soft_time_limit` + `task_time_limit` on all tasks
7. **Use gevent for I/O** — 63% less RAM than prefork at equivalent concurrency

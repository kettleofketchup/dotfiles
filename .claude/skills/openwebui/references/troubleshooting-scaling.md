# Scaling, Performance & DB Migration Troubleshooting

## Scaling & Multi-Replica

**Core requirements:** Same `WEBUI_SECRET_KEY` on all replicas, PostgreSQL (not SQLite), Redis for WebSockets, shared storage (RWX PVC), external vector DB (not default ChromaDB).

**Login loops/401:** Different secret keys. Fix: set same `WEBUI_SECRET_KEY`.

**WebSocket 403:** Configure `CORS_ALLOW_ORIGIN` with all access URLs, enable Redis for WebSockets.

**Config mismatch:** Set `REDIS_URL` for Pub/Sub config sync across replicas.

**DB locked errors:** Migrate from SQLite to PostgreSQL.

**Worker crashes during upload:** Switch from default ChromaDB to pgvector/milvus/qdrant or ChromaDB HTTP mode.

**Safe update procedure:** Designate one migration pod (`ENABLE_DB_MIGRATIONS=True` on master only) or scale to 1 replica during upgrades.

**Pool sizing:** `Total connections = (POOL_SIZE + MAX_OVERFLOW) x replicas x UVICORN_WORKERS`. Keep under DB `max_connections`.

**Function/tool pip crashes:** Set `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS=False`, pre-install packages in Dockerfile.

## Performance & Optimization

- Task models: use fast non-reasoning models (gpt-5-nano, gemma3:1b) for title/tag generation
- `ENABLE_BASE_MODELS_CACHE=True` + `MODELS_CACHE_TTL=300`; `RAG_SYSTEM_CONTEXT=True` for KV cache
- PostgreSQL mandatory at scale; `ENABLE_REALTIME_CHAT_SAVE=False`; `CONTENT_EXTRACTION_ENGINE=tika` (pypdf leaks)
- Embeddings: default SentenceTransformers ~500MB/worker; use `RAG_EMBEDDING_ENGINE=openai` or `ollama`
- High concurrency: `THREAD_POOL_SIZE=2000`, `AIOHTTP_CLIENT_TIMEOUT=1800`

## Database Migration (Manual)

Backup first. Run inside container:

```bash
cd /app/backend/open_webui
export DATABASE_URL="sqlite:////app/backend/data/webui.db"
export WEBUI_SECRET_KEY=$(cat /app/backend/.webui_secret_key)
alembic current -v
alembic upgrade head
```

**"Table already exists":** Restore backup, drop table + re-run, or `alembic stamp <revision>`.

**"No such table":** Run `alembic upgrade head`.

**Multiple failures:** Step through one migration at a time.

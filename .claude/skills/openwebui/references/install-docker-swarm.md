# Docker Swarm Installation

Deploys ChromaDB, Ollama, and OpenWebUI as services. ChromaDB runs as separate HTTP server (required for multi-worker; default SQLite is not fork-safe).

## Before Starting

```bash
mkdir -p data/open-webui data/chromadb data/ollama
```

## Docker Stack (GPU Support)

```yaml
version: '3.9'
services:
  openWebUI:
    image: ghcr.io/open-webui/open-webui:main
    depends_on: [chromadb, ollama]
    volumes:
      - ./data/open-webui:/app/backend/data
    environment:
      DATA_DIR: /app/backend/data
      OLLAMA_BASE_URLS: http://ollama:11434
      CHROMA_HTTP_PORT: 8000
      CHROMA_HTTP_HOST: chromadb
      CHROMA_TENANT: default_tenant
      VECTOR_DB: chroma
      RAG_EMBEDDING_ENGINE: ollama
      RAG_EMBEDDING_MODEL: nomic-embed-text-v1.5
      RAG_EMBEDDING_MODEL_TRUST_REMOTE_CODE: "True"
    ports:
      - target: 8080
        published: 8080
        mode: overlay
    deploy:
      replicas: 1
      restart_policy: {condition: any, delay: 5s, max_attempts: 3}

  chromadb:
    hostname: chromadb
    image: chromadb/chroma:0.5.15
    volumes:
      - ./data/chromadb:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ALLOW_RESET=TRUE
      - PERSIST_DIRECTORY=/chroma/chroma
    ports:
      - target: 8000
        published: 8000
        mode: overlay
    deploy:
      replicas: 1
      restart_policy: {condition: any, delay: 5s, max_attempts: 3}
    healthcheck:
      test: ["CMD-SHELL", "curl localhost:8000/api/v1/heartbeat || exit 1"]
      interval: 10s
      retries: 2
      start_period: 5s
      timeout: 10s

  ollama:
    image: ollama/ollama:latest
    hostname: ollama
    ports:
      - target: 11434
        published: 11434
        mode: overlay
    deploy:
      resources:
        reservations:
          generic_resources:
            - discrete_resource_spec: {kind: "NVIDIA-GPU", value: 0}
      replicas: 1
      restart_policy: {condition: any, delay: 5s, max_attempts: 3}
    volumes:
      - ./data/ollama:/root/.ollama
```

## GPU Requirements

1. Ensure CUDA is enabled
2. Install [Nvidia Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
3. Enable GPU in `/etc/nvidia-container-runtime/config.toml`: uncomment `swarm-resource = "DOCKER_RESOURCE_GPU"`. Restart Docker daemon.

For CPU only: remove the `generic_resources` section from the ollama service.

## Deploy

```bash
docker stack deploy -c docker-stack.yaml -d super-awesome-ai
```

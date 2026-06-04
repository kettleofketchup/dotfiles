# Docker Compose and Swarm Installation

## Docker Compose Setup

Docker Compose requires an additional package, `docker-compose-v2`.

Older Docker Compose tutorials may reference version 1 syntax, which uses commands like `docker-compose build`. Ensure you use version 2 syntax, which uses commands like `docker compose build` (note the space instead of a hyphen).

### Example `docker-compose.yml`

```yaml
services:
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    volumes:
      - open-webui:/app/backend/data
volumes:
  open-webui:
```

### Using Slim Images

```yaml
services:
  openwebui:
    image: ghcr.io/open-webui/open-webui:main-slim
    ports:
      - "3000:8080"
    volumes:
      - open-webui:/app/backend/data
volumes:
  open-webui:
```

Slim images download required models (whisper, embedding models) on first use, which may result in longer initial startup times but significantly smaller image sizes.

### Starting the Services

```bash
docker compose up -d
```

### Nvidia GPU Support

Change the image from `ghcr.io/open-webui/open-webui:main` to `ghcr.io/open-webui/open-webui:cuda` and add the following to your service definition:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

### Uninstall

1. **Stop and Remove the Services:**
    ```bash
    docker compose down
    ```

2. **Remove the Volume (Optional, deletes all data):**
    ```bash
    docker compose down -v
    ```
    Or manually:
    ```bash
    docker volume rm <your_project_name>_open-webui
    ```

3. **Remove the Image (Optional):**
    ```bash
    docker rmi ghcr.io/open-webui/open-webui:main
    ```

## Docker Swarm

See [install-docker-swarm.md](install-docker-swarm.md) for the full Docker Swarm stack with ChromaDB, Ollama, and Open WebUI services.

# Open Terminal

Give your AI a real computer to work on.

Open Terminal connects a real computing environment to Open WebUI. The AI can write code, execute it, read the output, fix errors, and iterate, all without leaving the chat. It handles files, installs packages, runs servers, and returns results directly to you. Run it in a Docker container for isolation, or bare metal for direct access to your machine.

## Capabilities

- **Data analysis and reporting** - Upload spreadsheets, CSVs, or databases. The AI reads the data, runs analysis scripts, and generates charts or reports.
- **Document search and extraction** - Point the AI at a folder of PDFs, Word docs, or emails. It reads all of them and returns structured results: summaries, extracted fields, or cross-references.
- **Web development with live preview** - The AI builds HTML/CSS/JS projects, starts a preview server, and renders the result inside Open WebUI. Iterate by describing changes in chat.
- **Software development** - Clone repos, run test suites, debug failures, refactor code, and work with Git, all through natural language.
- **File and system automation** - Bulk rename, sort, deduplicate, convert, compress, and organize files. Manage disk space, schedule backups, process logs.

## Key Features

| Feature | Description |
| :--- | :--- |
| **Code execution** | Runs real commands and returns output |
| **File browser** | Browse, upload, download, and edit files in the sidebar |
| **Document reading** | PDF, Word, Excel, PowerPoint, RTF, EPUB, email |
| **Website preview** | Live preview of web projects inside Open WebUI |
| **Isolation optional** | Run in a Docker container for sandboxing, or bare metal for full access |

Open Terminal requires models with **native function calling** support. Frontier models (GPT-5.4, Claude Sonnet 4.6, Gemini 3.1 Pro) handle complex multi-step tasks well. Smaller models may work for simple commands but can struggle with longer workflows.

## Installation

Choose an installation method based on your needs:

| Method | When to use |
| :--- | :--- |
| **Docker** | Runs in an isolated container, separated from your host system |
| **Bare Metal** | The AI works directly on your machine -- your real files, tools, and environment |
| **Docker Compose** | You already run Open WebUI with Docker Compose and want to add Open Terminal to it |

### Docker

Requires Docker.

```bash
docker run -d \
  --name open-terminal \
  --restart unless-stopped \
  -p 8000:8000 \
  -v open-terminal:/home/user \
  -e OPEN_TERMINAL_API_KEY=your-secret-key \
  ghcr.io/open-webui/open-terminal
```

| Flag | Purpose |
| :--- | :--- |
| `-d` | Run in background |
| `--name open-terminal` | Container name for reference |
| `--restart unless-stopped` | Auto-restart on reboot |
| `-p 8000:8000` | Expose on `http://localhost:8000` |
| `-v open-terminal:/home/user` | Persist files across restarts |
| `-e OPEN_TERMINAL_API_KEY=...` | Authentication key |

Verify by opening `http://localhost:8000/docs` in your browser.

If no API key was set, one is generated automatically. Find it with: `docker logs open-terminal`

### Bare Metal

**Warning**: In this mode, the AI can do anything your user account can do, including modifying and deleting files.

**Option A -- Run without installing:**

```bash
uvx open-terminal run --host 0.0.0.0 --port 8000 --api-key your-secret-key
```

**Option B -- Install with pip:**

```bash
pip install open-terminal
open-terminal run --host 0.0.0.0 --port 8000 --api-key your-secret-key
```

Open Terminal serves files from the current directory. To scope it to a specific project:

```bash
cd /path/to/your/project
uvx open-terminal run --host 0.0.0.0 --port 8000 --api-key your-secret-key
```

Windows is supported via pywinpty with full PowerShell support.

### Docker Compose

Add Open Terminal as a service in your existing `docker-compose.yml`:

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:latest
    container_name: open-webui
    ports:
      - "3000:8080"
    volumes:
      - open-webui:/app/backend/data

  open-terminal:
    image: ghcr.io/open-webui/open-terminal
    container_name: open-terminal
    volumes:
      - open-terminal:/home/user
    environment:
      - OPEN_TERMINAL_API_KEY=your-secret-key

volumes:
  open-webui:
  open-terminal:
```

When both services share a Docker Compose network, use the service name as the host: `http://open-terminal:8000` (`localhost` won't resolve between containers).

## Connecting to Open WebUI

**Admin Panel (recommended):** Admin Panel > Settings > Integrations > Open Terminal section (NOT External Tools) > **+** > fill URL, API Key, Auth Type (Bearer) > Save. Enable native function calling in Workspace > Models > Capabilities. Pre-configure via `TERMINAL_SERVER_CONNECTIONS` env var for Docker deployments.

**Personal Settings (testing only):** Routes requests through browser. Use Admin Settings for production.

### Troubleshooting

- Docker Compose: `http://open-terminal:8000`; Separate containers: `http://host.docker.internal:8000`; Same machine: `http://localhost:8000`
- Quick check: `docker exec open-webui curl -s http://open-terminal:8000/health`
- AI doesn't use terminal: toggle on, refresh, confirm model supports tool calling
- Wrong API key: `docker logs open-terminal | grep "API key:"`

## File Browser

When Open Terminal is connected, a **file browser** appears in the chat sidebar. Features: navigate folders, preview text/code (syntax highlighting)/PDFs/CSVs/markdown/images, upload by drag-and-drop, download files, edit text files in-place, create/delete items. Refreshes automatically when AI creates or changes files.

## Enterprise Multi-User

For isolated, per-user terminal containers, see **Terminals** — provisions a dedicated Open Terminal per user with lifecycle management, resource controls, and policy-based environments.

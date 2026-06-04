# Workspace: Knowledge, Skills, Notes, Channels, Open Terminal

## Knowledge

### Retrieval Modes

| Mode | Behavior |
|------|----------|
| **Focused Retrieval** (default) | RAG identifies relevant chunks; hybrid search (BM25 + vector) with reranking |
| **Full Context** | Injects complete file; bypasses RAG/chunking; always injected regardless of native FC |

### Native Mode (Agentic) Tools

| Tool | With Attached KB | Without KB |
|------|-----------------|------------|
| `list_knowledge` | Yes | No |
| `list_knowledge_bases` / `search_knowledge_bases` / `query_knowledge_bases` | No | Yes |
| `search_knowledge_files` / `query_knowledge_files` | Yes (scoped) | Yes |
| `view_file` / `view_knowledge_file` | Yes | No |

**Critical**: With Native Function Calling, attached knowledge is **NOT automatically injected**. Model must call tools. Solutions: add system prompt instructions, disable native FC, or use Full Context mode.

### API Endpoints

- `POST /api/v1/files/` — upload files
- `GET /api/v1/files/{id}/process/status` — check processing
- `POST /api/v1/knowledge/{id}/file/add` — add file to KB

---

## Skills

Reusable markdown instruction sets. **$ mention**: full content injected into system prompt. **Model-attached**: lazy-load — only manifest (name + description) injected; model uses `view_skill` tool on demand.

Fields: Name, Skill ID (unique slug, editable at creation only), Description, Content (Markdown). Import `.md` with YAML frontmatter. Active/inactive toggle. Private by default.

---

## Notes

Persistent workspace outside individual conversations. Features: rich Markdown/Rich Text editor, AI Enhance (in-place improvement), Chat sidebar, context injection (no chunking), export to `.txt`/`.md`/`.pdf`.

Agentic tools (native FC): `search_notes`, `view_note`, `write_note`, `replace_note_content`

Quick creation: `/notes/new?title=My%20Title&content=Initial%20text`

---

## Channels

Persistent shared spaces for humans and AI. Features: `@model` tagging, threads/reactions/pins, file sharing. Types: Standard (topic rooms), Group (team-scoped), DM (1:1 or small-group).

Enable: Admin Panel > Settings > General > **Channels (Beta)**.

---

## Open Terminal

Connects a computing environment to Open WebUI for code execution, file management, and automation. Requires **native function calling** (frontier models recommended).

Connect via Admin Settings > Integrations > Open Terminal, or via user Settings > Tools (browser-direct, testing only). Enterprise: per-user isolated containers with lifecycle management.

# Copilot custom instructions — file paths & frontmatter

## File locations

| Path | Type | Notes |
|------|------|-------|
| `.github/copilot-instructions.md` | Repo-wide | Single file; loaded for Chat, code completion, and PR review |
| `.github/instructions/<name>.instructions.md` | Path-scoped | Requires `applyTo:` glob frontmatter |
| `AGENTS.md` (any directory) | Agent-shared | Recognized by Copilot Chat / cloud agent |
| `CLAUDE.md` / `GEMINI.md` (root only) | Agent-shared | Same recognition as `AGENTS.md` |

**Hard requirements:**
- The repo-wide file MUST be at `.github/copilot-instructions.md` exactly. A file at `.github/instructions/copilot-instructions.md` is treated as a (likely-malformed) path-scoped instruction and not loaded as the repo file.
- Instructions become live "as soon as you save the file" — no commit / push step.
- PR review uses instructions from the **PR's base branch**, not the head branch.

## Frontmatter for `.instructions.md` files

```markdown
---
applyTo: "**/*.ts,**/*.tsx"
excludeAgent: "code-review"
---

<instruction body here — natural language, kept short>
```

**Keys:**

| Key | Required? | Value | Notes |
|-----|-----------|-------|-------|
| `applyTo` | Required | Comma-separated globs | Globs are matched against repo-relative paths |
| `excludeAgent` | Optional | `"code-review"` or `"cloud-agent"` | Use to scope a file to chat/completion only |

`.github/copilot-instructions.md` does NOT take frontmatter — it always applies repo-wide.

## Glob syntax (applyTo)

| Pattern | Meaning |
|---------|---------|
| `*.py` | `.py` files in the **current** directory only |
| `**/*.py` | `.py` files **anywhere** in the repo |
| `src/*.py` | direct children of `src/` only |
| `src/**/*.py` | any `.py` under `src/`, recursive |
| `**` | every file |
| `**/*.ts,**/*.tsx` | comma-separated alternatives (no spaces) |

## Length & content rules

- Keep each file under ~2 pages of rendered Markdown (GitHub docs guidance). Long files dilute attention and may be truncated by Copilot.
- Write **task-specific** rules ("when editing Django models, run `makemigrations` against the dev container"), not general philosophy ("write clean code").
- Avoid duplicating content across multiple `.instructions.md` files — let `applyTo` scopes do the routing.
- Don't paste large schemas or tables of constants — point to a canonical source file the reviewer can click into.

## Precedence when layered

All applicable sets are passed to Copilot in priority order:

1. **Personal** (user's GitHub.com → Copilot settings → Custom instructions) — highest, wins ties.
2. **Repository** (`.github/copilot-instructions.md` + matching `.instructions.md` files + `AGENTS.md`).
3. **Organization** (Org Settings → Copilot → Custom instructions) — lowest.

"All sets are provided" — Copilot doesn't *replace*, it layers. Plan rules so they compose cleanly rather than contradict.

## Examples

### Minimal repo-wide file

```markdown
# Project rules for Copilot

This repo uses `just` for all task running. Never invoke `pytest` / `python manage.py` directly — always go through `just test::run '<cmd>'`.

PRs must include a `## Test plan` section.
```

### Path-scoped Django rule

`.github/instructions/django.instructions.md`:
```markdown
---
applyTo: "backend/**/*.py"
---

- Run migrations via `just db::makemigrations <app>` then `just py::migrate`.
- All cache invalidation goes through django-cacheops decorators on the model; do not call `cache.delete(...)` directly.
- Logging: use `structlog.get_logger(__name__)`, not `logging.getLogger`.
```

### Chat-only style guide (excluded from code review)

`.github/instructions/style-chat.instructions.md`:
```markdown
---
applyTo: "**"
excludeAgent: "code-review"
---

When asked to summarize a PR, lead with the **why** in 1 sentence, then bullet the user-facing changes.
```

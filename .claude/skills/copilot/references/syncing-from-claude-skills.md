# Bridging Copilot config → `.claude/skills/`

## The principle

`.claude/skills/<name>/SKILL.md` is the **canonical source** of project conventions in this user's repos. Copilot can't follow file references the way Claude Code does — it loads the literal `.md` files that match its known paths into the model's context. So the rule is:

> **Copilot instruction files contain a short summary AND a pointer back to the canonical Claude skill. Never duplicate; never let the summary drift past one screen.**

Treating Copilot's files as the source of truth instead would force the user to update two places every time a convention changes — which is exactly the drift problem this skill exists to prevent.

## The four-file pattern (for any repo with `.claude/skills/`)

### 1. Top-level pointer in `.github/copilot-instructions.md`

Lead with a "Project conventions" section that lists each relevant Claude skill, one line each:

```markdown
# Copilot guidance for this repo

## Project conventions (canonical: `.claude/skills/`)

- **Logging** — structlog, system/subsystem taxonomy. See `.claude/skills/logging/SKILL.md`.
- **Testing** — Django tests via Docker, Playwright fixtures. See `.claude/skills/testing/SKILL.md`.
- **Brand/UI** — PrimaryButton, brand tokens, no inline styles. See `.claude/skills/brand/SKILL.md`.
- **Caching** — django-cacheops decorators, no manual `cache.delete`. See `.claude/skills/django-redis-caching/SKILL.md`.

[3–8 lines of repo-wide rules — task runner, env activation, PR conventions]

Canonical source: `.claude/skills/` — update there first.
```

### 2. Path-scoped `.github/instructions/<skill>.instructions.md` per skill

For each Claude skill with a clear file scope, mirror it:

```markdown
---
applyTo: "backend/**/*.py"
---

# Backend Python conventions

Summary (canonical: `.claude/skills/logging/SKILL.md`):
- Use `structlog.get_logger(__name__)`, not stdlib `logging`.
- Required log fields: `system`, `subsystem`, `event`.
- Levels: debug for traces, info for state changes, warn for recoverable, error for needs-attention.

Caching (canonical: `.claude/skills/django-redis-caching/SKILL.md`):
- Cache via `@cached_as` / `@cached_view` decorators on the model/view.
- Never call `cache.delete(...)` directly — cacheops invalidates on save.
```

Keep each summary to **3–8 bullets**. If you need more, the Copilot file is doing too much — pull the user toward the canonical skill instead.

### 3. Per-language file that catches small things

Some conventions are too small for a skill but worth telling Copilot:

```markdown
---
applyTo: "frontend/**/*.{ts,tsx}"
---

- Imports: use the `~/` alias for `frontend/app/`, not relative `../../`.
- Loggers: `const log = getLogger('<moduleName>');` per module.
- Forms: Zod + React Hook Form via `ZodResolver` (canonical: `.claude/skills/zod-form-validation/SKILL.md`).
```

### 4. `AGENTS.md` at repo root (optional, for cross-agent parity)

If the project wants Copilot Chat AND other agents (Codex, Cursor, etc.) to see the same rules without duplicating, an `AGENTS.md` at the root is recognized by Copilot too. Use it for absolutely-must-know rules only:

```markdown
# Agent guidance

Run everything through `just` (e.g., `just test::run '<cmd>'`). Never invoke `pytest` / `python manage.py` directly.

For detailed conventions, see `.claude/skills/` (Claude Code) and `.github/copilot-instructions.md` (Copilot).
```

## Worked example: DraftForge

Given the existing skills (`logging`, `testing`, `django-redis-caching`, `brand`, `frontend-development`, etc.), a clean Copilot layout for DraftForge would be:

```
.github/
├── copilot-instructions.md                       # repo-wide pointer + 5-line top rules
├── instructions/
│   ├── backend.instructions.md                   # applyTo: backend/**/*.py
│   ├── frontend.instructions.md                  # applyTo: frontend/**/*.{ts,tsx}
│   ├── tests.instructions.md                     # applyTo: tests/**, **/tests/**
│   └── brand.instructions.md                     # applyTo: frontend/app/components/**
└── AGENTS.md   (optional)
```

**Each `.instructions.md` body opens with: `Canonical source: .claude/skills/<name>/SKILL.md`.**

The Copilot files never copy more than ~10 bullets of the skill — they exist so PR reviews catch the most common drift (raw `<button>` instead of `PrimaryButton`, `cache.delete()` instead of cacheops, etc.) without forcing Copilot to load the entire skill content.

## What NOT to put in Copilot files

- Long workflow walkthroughs (Copilot review applies them once per file — they bloat context with no value).
- Full schemas / API specs (point to the file).
- Anything that varies by feature flag or env (Copilot doesn't know the runtime).
- Anything the Claude skill already says well — just reference it.

## What NOT to do

- **Don't generate `copilot-instructions.md` from a script that concatenates skill files.** Skills are written for Claude; their tone, length, and structure are wrong for Copilot. Hand-author the summary.
- **Don't symlink** `.claude/skills/X/SKILL.md` → `.github/instructions/X.instructions.md`. Different audiences, different formats, and the symlink will break frontmatter.
- **Don't aim for completeness in the Copilot files.** Aim for "catch the 5 most common drift patterns in PR review." Everything else lives in the Claude skill.

# Migration Status & Publishing

## Config Conversion: Theme Overrides & Analytics

### Theme Overrides

**mkdocs.yml:** `theme: custom_dir: overrides`

**zensical.toml:**
```toml
[project.theme]
custom_dir = "overrides"
```

Override blocks and partials work the same way. `overrides/main.html` extends `base.html`.

### Analytics & Consent

**zensical.toml:**
```toml
[project.extra.analytics]
provider = "google"
property = "G-XXXXXXXXXX"

[project.extra.consent]
title = "Cookie consent"
description = "We use cookies..."
```

## Key Differences

| mkdocs-material | Zensical |
|-----------------|----------|
| `mkdocs.yml` (YAML) | `zensical.toml` (TOML) or legacy YAML |
| `theme: name: material` | Theme built-in, no `name` needed |
| `mkdocs serve` / `build` / `new` | `zensical serve` / `build` / `new` |
| `mkdocs gh-deploy` | GitHub Actions workflow (no built-in deploy command) |
| Explicit extension config required | Common extensions auto-enabled |
| `material/` icon prefix default | `lucide/` default (all sets available) |
| pip/pipx install | pip, uv, or Docker |

## Theme Variants

Use `variant = "classic"` to match Material for MkDocs appearance during migration. Switch to `variant = "modern"` (default) when ready.

## Feature Parity Status

Most features supported. Not yet available:
- Social cards (under development)
- Tag listing pages (under development)
- Blog plugin
- `strict` mode, `hooks`, `watch`, `validation` settings
- `mkdocs gh-deploy` command (use CI/CD workflows instead)

## Publishing Changes

Replace in CI workflows:
- `pip install mkdocs-material` → `pip install zensical`
- `mkdocs build` → `zensical build --clean`
- `mkdocs gh-deploy` → Use GitHub Actions deploy workflow (see [setup/publishing.md](setup/publishing.md))

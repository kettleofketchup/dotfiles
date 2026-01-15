---
name: just
description: Bootstrap repos with just command runner. Use when setting up new projects, creating justfiles, or adding task automation. Provides ./dev bootstrap script that installs just, modular justfile structure in just/ directory, and recipe conventions.
---

# Just Command Runner

Task automation using [just](https://github.com/casey/just) with a standardized project structure.

## Project Structure

```
project/
├── dev                 # Bootstrap script (installs just, runs `just dev`)
├── justfile            # Root: import 'just/justfile'
└── just/
    ├── justfile        # Main file with settings, modules, and imports
    ├── dev.just        # Development recipes (imported, no namespace)
    ├── go.just         # Go module (go::build, go::test)
    ├── docker.just     # Docker module (docker::build, docker::push)
    └── release.just    # Release module (release::all, release::linux)
```

## Bootstrapping a New Repo

1. Copy `assets/dev` to project root, make executable: `chmod +x dev`
2. Copy `assets/just/` directory to project root
3. Edit `just/dev.just` with project-specific setup commands
4. Add additional `.just` modules as needed

## Quick Reference

### Root Justfile

```just
# justfile (root) - imports from just/ directory
import 'just/justfile'
```

### Main Justfile with Modules

```just
# just/justfile
set quiet
set dotenv-load

# Modules: namespaced with :: syntax
mod go          # go::build, go::test, go::lint
mod docker      # docker::build, docker::push
mod release     # release::all, release::linux

# Imports: merged into this namespace
import 'dev.just'

# Top-level aliases for common operations
build:
    just go::build myapp

test:
    just go::test myapp
```

### Module Example

```just
# go.just - called as go::build, go::test, etc.
VERSION := `git describe --tags --always 2>/dev/null || echo "dev"`
BIN_DIR := env_var("PWD") / "bin"

build tool:
    @mkdir -p {{BIN_DIR}}
    go build -o {{BIN_DIR}}/{{tool}} .

test tool:
    go test -race -cover ./...

lint:
    golangci-lint run
```

### Import vs Module

| Feature | `import 'file.just'` | `mod name` |
|---------|----------------------|------------|
| Namespace | Merged | Separate (`name::*`) |
| Calling | `just recipe` | `just name::recipe` |
| Use for | Shared settings, dev | Categorized tooling |

### Common Dev Module

```just
# dev.just - Imported (no namespace)

# Bootstrap the development environment
dev:
    echo "Installing dependencies..."
    # npm install / pip install -r requirements.txt / cargo build
    echo "Done!"

# Clean build artifacts
clean:
    rm -rf dist/ build/ target/
```

## Shell Completions Setup

When setting up just for a user, check if shell completions are configured and set them up if missing.

### Detection

Check if `_just` completion function exists:

```bash
# For zsh
type _just &>/dev/null

# For bash
type _just &>/dev/null || complete -p just &>/dev/null
```

### Setup Steps

If completions don't exist:

1. **Create completions directory** (respects XDG):
   ```bash
   JUST_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/just"
   mkdir -p "$JUST_CONFIG_DIR"
   ```

2. **Generate completions file**:
   ```bash
   # For zsh
   just --completions zsh > "$JUST_CONFIG_DIR/completions.zsh"

   # For bash
   just --completions bash > "$JUST_CONFIG_DIR/completions.bash"
   ```

3. **Add sourcing to shell rc** (if not already present):

   For **zsh** (`~/.zshrc`):
   ```bash
   # just completions
   if command -v just &>/dev/null; then
       [[ -f "${XDG_CONFIG_HOME:-$HOME/.config}/just/completions.zsh" ]] && source "${XDG_CONFIG_HOME:-$HOME/.config}/just/completions.zsh"
   fi
   ```

   For **bash** (`~/.bashrc`):
   ```bash
   # just completions
   if command -v just &>/dev/null; then
       [[ -f "${XDG_CONFIG_HOME:-$HOME/.config}/just/completions.bash" ]] && source "${XDG_CONFIG_HOME:-$HOME/.config}/just/completions.bash"
   fi
   ```

### Verification

After adding, verify with:
```bash
source ~/.zshrc  # or ~/.bashrc
type _just  # should show completion function
```

## References

Detailed syntax and patterns in `references/`:

| File | Contents |
|------|----------|
| `modules.md` | Module system (`mod`), namespacing with `::`, import vs mod |
| `settings.md` | All justfile settings (`set quiet`, `set dotenv-load`, etc.) |
| `recipes.md` | Recipe syntax, parameters, dependencies, shebang recipes |
| `attributes.md` | Recipe attributes (`[group]`, `[confirm]`, `[private]`, etc.) |
| `functions.md` | Built-in functions (`env()`, `os()`, `join()`, etc.) |
| `syntax.md` | Variables, strings, conditionals, imports |

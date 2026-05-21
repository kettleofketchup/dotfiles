# Offline dotfiles + zinit bundle

## Purpose

Produce a single `dotfiles.tar` on an online machine and restore the full
shell environment (dotfiles + all zinit plugins/binaries) on an airgapped
machine without internet access.

## File layout

```
~/dotfiles/
├── zinit-offline/
│   ├── README.md              (updated: new workflow + script paths)
│   ├── install-dotfiles.sh    (NEW)
│   └── zinit-offline.tar.gz   (NEW location — was at repo root)
├── bin/
│   ├── zinit-pack.sh          (MODIFIED — writes into zinit-offline/)
│   └── zinit-depack.sh        (MODIFIED — reads from zinit-offline/)
├── just/
│   └── dev.just               (MODIFIED — adds `pack-offline` recipe)
└── .gitignore                 (MODIFIED — adds dotfiles.tar, updates zinit path)
```

## Pack flow (online machine)

```
just pack-offline
  ├─ bin/zinit-pack.sh
  │    writes zinit-offline/zinit-offline.tar.gz
  └─ tar -cf dotfiles.tar -C $HOME dotfiles
       (zinit archive is inside the tree, so it goes in too)
```

### Outer-tar excludes

With `tar -C $HOME -cf dotfiles.tar dotfiles`, archive paths are `dotfiles/...`
so excludes match against that prefix:

- `dotfiles/dotfiles.tar` — prevent self-inclusion
- `dotfiles/.worktrees` — transient git worktrees
- `dotfiles/.cache` — local cache

`.git/` is **included** so the offline machine retains history.

## Restore flow (airgapped machine)

```
tar xf dotfiles.tar -C ~                       (user runs)
~/dotfiles/zinit-offline/install-dotfiles.sh   (user runs)
  ├─ sanity-check: dotfiles root is $HOME/dotfiles
  ├─ sanity-check: zinit-offline/zinit-offline.tar.gz exists
  ├─ bin/zinit-depack.sh
  └─ cd ~/dotfiles && stow -R .
```

Two-step intentionally: user owns the extraction step (and any conflict
with an existing `~/dotfiles`). The installer assumes the tree is already
in place.

## Script details

### `bin/zinit-pack.sh` change
- Change `BUNDLE` from `$DOTFILES_DIR/zinit-offline.tar.gz` to
  `$DOTFILES_DIR/zinit-offline/zinit-offline.tar.gz`.
- No other behavior changes (progress, symlink fix-up metadata, etc.).

### `bin/zinit-depack.sh` change
- Same BUNDLE path update.
- Tar-extract logic that strips the `zinit-offline/` prefix already works.

### `zinit-offline/install-dotfiles.sh` (new)
```
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOTFILES="$(cd "$SCRIPT_DIR/.." && pwd)"

# Guard: only run from $HOME/dotfiles
[[ "$DOTFILES" == "$HOME/dotfiles" ]] || {
  echo "Error: expected dotfiles at \$HOME/dotfiles, got $DOTFILES" >&2
  exit 1
}

# Guard: stow must be installed (offline target may not have it)
command -v stow >/dev/null || {
  echo "Error: 'stow' not found. Install GNU stow before running this script." >&2
  echo "  Arch:   sudo pacman -S stow" >&2
  echo "  Debian: sudo apt-get install stow" >&2
  exit 1
}

# Step 1: depack zinit
"$DOTFILES/bin/zinit-depack.sh"

# Step 2: detect stow conflicts; back them up
cd "$DOTFILES"
conflicts=$(stow -n . 2>&1 | awk '/existing target is/ {print $NF}' || true)
if [[ -n "$conflicts" ]]; then
  backup="$HOME/.dotfiles-backup-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$backup"
  echo "Backing up conflicting files to $backup ..."
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    target="$HOME/$f"
    if [[ -e "$target" ]]; then
      mv "$target" "$backup/"
      echo "  $f"
    fi
  done <<< "$conflicts"
fi

# Step 3: stow dotfiles
stow -R .

echo "Done. Open a new shell to load the restored environment."
```

### `just pack-offline` (new recipe in `just/dev.just`)
```
pack-offline:
    bin/zinit-pack.sh
    tar --exclude='dotfiles/dotfiles.tar' \
        --exclude='dotfiles/.worktrees' \
        --exclude='dotfiles/.cache' \
        -cf "$HOME/dotfiles/dotfiles.tar" \
        -C "$HOME" dotfiles
    echo "Built: $HOME/dotfiles/dotfiles.tar ($(du -h "$HOME/dotfiles/dotfiles.tar" | cut -f1))"
```

## `.gitignore` changes

- Update `zinit-offline.tar.gz` → `zinit-offline/zinit-offline.tar.gz`
- Add `dotfiles.tar`

## Out of scope

- Auto-install of system packages (apt/pacman) — covered by the existing
  `install_linux.sh` for online machines. The offline installer is purely
  zinit + stow.
- Cross-arch portability — zinit gh-r binaries are arch-specific. Pack
  and depack must run on the same architecture.

#!/usr/bin/env bash
# Restore dotfiles + zinit on an airgapped machine.
# Assumes the dotfiles tree has already been extracted to $HOME/dotfiles.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOTFILES="$(cd "$SCRIPT_DIR/.." && pwd)"

# Guard: only run from $HOME/dotfiles
if [[ "$DOTFILES" != "$HOME/dotfiles" ]]; then
    echo "Error: expected dotfiles at \$HOME/dotfiles, got $DOTFILES" >&2
    echo "Move the tree to ~/dotfiles and re-run." >&2
    exit 1
fi

# Guard: stow must be installed (airgapped target may not have it)
if ! command -v stow >/dev/null 2>&1; then
    echo "Error: 'stow' not found. Install GNU stow before running this script." >&2
    echo "  Arch:   sudo pacman -S stow" >&2
    echo "  Debian: sudo apt-get install stow" >&2
    exit 1
fi

# Step 1: depack zinit
echo "==> Restoring zinit ..."
"$DOTFILES/bin/zinit-depack.sh"

# Step 2: detect stow conflicts and back them up
cd "$DOTFILES"
echo "==> Checking for stow conflicts ..."
conflicts="$(stow -nv . 2>&1 | awk '/existing target is/ {print $NF}' || true)"
if [[ -n "$conflicts" ]]; then
    backup="$HOME/.dotfiles-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup"
    echo "    backing up conflicting files to $backup"
    while IFS= read -r rel; do
        [[ -z "$rel" ]] && continue
        target="$HOME/$rel"
        if [[ -e "$target" && ! -L "$target" ]]; then
            mkdir -p "$backup/$(dirname "$rel")"
            mv "$target" "$backup/$rel"
            echo "      $rel"
        fi
    done <<< "$conflicts"
fi

# Step 3: stow dotfiles
echo "==> Stowing dotfiles ..."
stow -R .

echo "Done. Open a new shell to load the restored environment."

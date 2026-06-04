#!/usr/bin/env bash
# Restore the zinit share directory from zinit-offline.tar.gz.
set -euo pipefail

ZINIT_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/zinit"
DOTFILES_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUNDLE="$DOTFILES_DIR/zinit-offline/zinit-offline.tar.gz"

if [[ ! -f "$BUNDLE" ]]; then
    echo "Error: $BUNDLE not found."
    echo "Run bin/zinit-pack.sh first, or copy zinit-offline.tar.gz into zinit-offline/."
    exit 1
fi

if [[ -d "$ZINIT_HOME" ]]; then
    echo "Warning: $ZINIT_HOME already exists."
    read -rp "Overwrite? [y/N] " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
    rm -rf "$ZINIT_HOME"
fi

# Extract zinit data (skip the metadata prefixed with zinit-offline/)
mkdir -p "$ZINIT_HOME"
echo "Depacking zinit-offline.tar.gz -> $ZINIT_HOME ..."
tar -xzf "$BUNDLE" -C "$ZINIT_HOME" --strip-components=0 \
    --exclude='zinit-offline/*'

# Extract metadata to dotfiles dir
tar -xzf "$BUNDLE" -C "$DOTFILES_DIR" 'zinit-offline/*' 2>/dev/null || true

# Fix absolute symlinks if the username/home changed
PACK_HOME_FILE="$DOTFILES_DIR/zinit-offline/.pack-home"
if [[ -f "$PACK_HOME_FILE" ]]; then
    PACK_HOME="$(cat "$PACK_HOME_FILE")"
    if [[ "$PACK_HOME" != "$HOME" ]]; then
        echo "Fixing symlinks ($PACK_HOME -> $HOME) ..."
        fixed=0
        while IFS= read -r -d '' link; do
            target="$(readlink "$link")"
            if [[ "$target" == "$PACK_HOME"* ]]; then
                ln -sfn "${target/$PACK_HOME/$HOME}" "$link"
                ((fixed++))
            fi
        done < <(find "$ZINIT_HOME" -type l -print0)
        echo "  -> rewrote $fixed symlinks"
    fi
fi

echo "Done. Zinit restored to $ZINIT_HOME"

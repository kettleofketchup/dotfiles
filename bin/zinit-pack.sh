#!/usr/bin/env bash
# Package the zinit share directory for offline/airgapped deployment.
# Produces zinit-offline/zinit-offline.tar.gz inside the dotfiles repo.
set -euo pipefail

ZINIT_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/zinit"
DOTFILES_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OFFLINE_DIR="$DOTFILES_DIR/zinit-offline"
BUNDLE="$OFFLINE_DIR/zinit-offline.tar.gz"

if [[ ! -d "$ZINIT_HOME" ]]; then
    echo "Error: $ZINIT_HOME does not exist. Nothing to pack."
    exit 1
fi

mkdir -p "$OFFLINE_DIR"

# Save packing user's HOME so depack can fix symlinks on a different user
echo "$HOME" > "$OFFLINE_DIR/.pack-home"

# Get total size for progress
total_bytes=$(du -sb "$ZINIT_HOME" | cut -f1)
echo "Packing $ZINIT_HOME ($(numfmt --to=iec "$total_bytes" 2>/dev/null || echo "${total_bytes} bytes")) ..."

# Single archive: zinit data + metadata (README, .pack-home)
# Use pv for progress if available, otherwise a tar-verbose counter
if command -v pv &>/dev/null; then
    tar -cf - \
        -C "$DOTFILES_DIR" zinit-offline/README.md zinit-offline/.pack-home \
        -C "$ZINIT_HOME" . \
      | pv -s "$total_bytes" -p -e -r \
      | gzip > "$BUNDLE"
else
    total_files=$(find "$ZINIT_HOME" -not -type d | wc -l)
    tar -cvf - \
        -C "$DOTFILES_DIR" zinit-offline/README.md zinit-offline/.pack-home \
        -C "$ZINIT_HOME" . \
      2> >(
        count=0
        while IFS= read -r _; do
            count=$((count + 1))
            if ((count % 50 == 0 || count == total_files)); then
                pct=$((count * 100 / total_files))
                bar=$(printf '#%.0s' $(seq 1 $((pct / 2))))
                printf "\r  [%-50s] %d%%" "$bar" "$pct" >&2
            fi
        done
        printf "\n" >&2
      ) \
      | gzip > "$BUNDLE"
fi

echo "Done: $BUNDLE ($(du -sh "$BUNDLE" | cut -f1))"

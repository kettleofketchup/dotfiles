# Offline Bundle

Snapshot of `~/.local/share/zinit/` plus the dotfiles repo, for offline or
airgapped deployments. A new machine can bootstrap shell + plugins + binaries
without internet access.

## Pack (online machine)

```bash
just pack-offline
```

This produces two files:

| File                                         | What it is                                     |
|----------------------------------------------|------------------------------------------------|
| `zinit-offline/zinit-offline.tar.gz`         | All zinit plugins, gh-r binaries, completions |
| `dotfiles.tar`                               | Whole repo (includes the zinit archive above) |

Transfer **`dotfiles.tar`** to the target machine — it has everything.

## Restore (airgapped machine)

```bash
tar xf dotfiles.tar -C ~                       # extract to ~/dotfiles
~/dotfiles/zinit-offline/install-dotfiles.sh   # depack zinit + stow
```

The installer:
1. Verifies the tree is at `~/dotfiles` and `stow` is installed
2. Runs `bin/zinit-depack.sh` (restores `~/.local/share/zinit/`)
3. Backs up any conflicting dotfiles to `~/.dotfiles-backup-<timestamp>/`
4. Runs `stow -R .`

Open a new shell after restore.

## What's inside `zinit-offline.tar.gz`

| Directory      | Contents                                            |
|----------------|-----------------------------------------------------|
| `zinit.git/`   | Zinit plugin manager source                         |
| `plugins/`     | All plugins and gh-r binaries (bat, fd, fzf, etc.)  |
| `completions/` | Symlinks to generated/bundled completion files      |
| `snippets/`    | OMZ snippets (docker, ssh, git, etc.)               |
| `polaris/`     | `$ZPFX` — sbin symlinks and built artifacts         |
| `services/`    | Zinit services (if any)                             |

## Notes

- Archive size depends on installed gh-r binaries (~1 GB typical).
- The bundle is platform-specific (linux/amd64 by default). Pack and restore
  on matching architecture.
- Re-run `just pack-offline` after adding or updating plugins.
- The depack script rewrites absolute symlinks if `$HOME` changes between
  pack and restore machines (e.g., `kettle` → `mark`).

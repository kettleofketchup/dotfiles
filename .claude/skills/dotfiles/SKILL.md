---
name: dotfiles
description: GNU stow + chezmoi dotfiles at ~/dotfiles. Use for dotfile edits, per-machine config (mac vs homepc), stow conflicts, chezmoi templates, app-native includes, 1Password/age secrets.
version: 1.0.0
last_updated: 2026-09-15
---

# Dotfiles (stow + chezmoi)

Manage `~/dotfiles`, a GNU stow package that maps onto `$HOME`, optionally
alongside chezmoi for templated and secret-bearing files.

## The one rule

**One manager owns each path.** stow symlinks; chezmoi writes real files. Point
chezmoi at a path stow owns and `chezmoi apply` replaces the symlink, after
which `stow -R` conflicts with what chezmoi wrote. The failure is silent.

A third actor also edits `$HOME` on the Linux box: omarchy's migrations. Some
write through symlinks (`cat tmp > file`, safe), others replace them
(`mv tmp file`, breaks stow). Re-check after every omarchy update.

## Before changing anything

```bash
python3 ~/.claude/skills/dotfiles/scripts/check_dotfiles.py all
```

- `drift` — repo-tracked paths that are real files in `$HOME` instead of links
- `overlap` — paths claimed by both stow and chezmoi

Exit 1 means something needs attention. Run `drift` after any omarchy update or
OS config migration, and `overlap` before every `chezmoi apply`.

## How a change takes effect

The two managers differ here, and it is the most common source of confusion:

| managed by | target in $HOME | making a change take effect |
|---|---|---|
| **stow** | symlink into the repo | nothing — editing the repo file *is* editing the live file |
| **chezmoi** | a real file it writes | `chezmoi apply` |

So Hyprland config (`~/.config/hypr/hyprland.lua`, a stow symlink) needs **no
`chezmoi apply`** — only `hyprctl reload` to make the running compositor re-read
it. Only chezmoi-managed paths need applying; `chezmoi managed` lists exactly
which those are.

`chezmoi apply` covers **everything chezmoi manages** and nothing else -- it
cannot touch a stow path, because it does not know one exists. Command detail,
and what happens when another tool rewrites a chezmoi-managed file, are in
`references/chezmoi-workflow.md`.

## Adding a per-machine difference

Stop at the first option that fits:

1. **The app has its own include** — use it. No manager involved.
   `config-file = ?local.conf` (ghostty), `source ~/.config/zsh/local.zsh`,
   `[include]` (git), `Include` (ssh), `source-file -q` (tmux).
2. **A whole file differs per host** — per-host stow package (`homepc/`, `mac/`),
   excluded from `stow .` via `.stow-local-ignore`, stowed explicitly.
3. **Needs templating, a computed value, or a secret** — now use chezmoi.

Details and worked examples: `references/machine-differences.md`.

## Editing tracked files

Files under `~/dotfiles` are symlinked into `$HOME`, so editing either path edits
the same file. Prefer the repo path — it makes the git context obvious.

After adding or moving files:

```bash
stow -d ~/dotfiles -t ~ -n -v .    # dry run first, always
stow -d ~/dotfiles -t ~ -R .       # restow
```

Never `cd` into the repo for these; `-d`/`-t` is equivalent and avoids hook
issues. A single conflict aborts the whole run.

## When stow reports a conflict

The live `$HOME` file is usually the repo file plus lines something appended.
Adopt it, then review:

```bash
stow -d ~/dotfiles -t ~ -n -v --adopt .   # preview
stow -d ~/dotfiles -t ~ --adopt .         # moves live file into repo, links back
git -C ~/dotfiles diff                    # what was adopted
```

`--adopt` overwrites the repo copy, so only run it when that file is committed
and clean — git is the undo. If the adopted lines are machine-specific (a CLI
appending its own completions), move them into the machine-local include rather
than committing them to the shared repo.

## Machine-local shell config

`~/.config/zsh/local.zsh` is gitignored and sourced from the end of `.zshrc`.
Put host-specific shell config there, and point CLI installers that want to
append to `~/.zshrc` at that file instead.

## Secrets

age for anything needed to bootstrap the machine; 1Password for everything else.
Never commit a plaintext secret — rotate rather than rewrite history.
See `references/secrets.md`.

## References

| file | contents |
|---|---|
| `references/stow.md` | tree folding, `.stow-local-ignore` semantics, `--adopt`, per-host packages, the un-stow hazard |
| `references/chezmoi.md` | install and adopt, source state attributes, special files, `.chezmoiroot`, coexistence |
| `references/chezmoi-workflow.md` | `apply`/`status`/`diff`/`update`, what apply covers, files another tool rewrites |
| `references/machine-differences.md` | decision order, app-native includes, chezmoi's data/ignore/template layers |
| `references/secrets.md` | 1Password functions and caveats, age setup, what never to commit |

## Scripts

| file | contents |
|---|---|
| `scripts/check_dotfiles.py` | `drift` and `overlap` checks; `all` runs both |
| `scripts/test_check_dotfiles.py` | tests — run after editing the checker |

## Repo facts worth not rediscovering

- `~/dotfiles` is one stow package, not many: `stow -d ~/dotfiles -t ~ .`
- `.stow-local-ignore` **replaces** stow's default ignore list rather than
  extending it, and its patterns are anchored regexes.
- Only `.stow-local-ignore` and `~/.stow-global-ignore` are real. `.stow-ignore`
  and `.stowignore` in this repo are inert and got stowed into `$HOME` as junk.
- stow folds whole directories when the target does not exist, so a correctly
  stowed file is often not itself a symlink — its parent is.

# chezmoi

chezmoi renders a **source state** into `$HOME` by writing real files. It does
not symlink by default. That is why it must never be pointed at a path stow
already owns — see "Coexistence" below.

## Install and adopt

```bash
# Arch                 # macOS
pacman -S chezmoi      brew install chezmoi

chezmoi init                 # creates source dir + ~/.config/chezmoi/chezmoi.toml
chezmoi add ~/.config/foo    # take a file under management
chezmoi edit ~/.config/foo   # edit the SOURCE, not the target
chezmoi diff                 # what apply would change -- always run first
chezmoi apply                # write to $HOME
chezmoi managed              # every path chezmoi claims
chezmoi forget <path>        # stop managing (leaves the target alone)
```

Source dir defaults to `$XDG_DATA_HOME/chezmoi` (`~/.local/share/chezmoi`);
`destDir` defaults to `$HOME`. Both are settable in `chezmoi.toml`.

## Keeping the source inside ~/dotfiles

`.chezmoiroot` is read from the root of the source directory before any other
file and sets the source state path; everything else resolves relative to it.
So the git repo root can stay `~/dotfiles` while chezmoi's source lives in a
subdirectory:

```
~/dotfiles/
  .chezmoiroot          <- contains: chezmoi
  chezmoi/              <- actual source state
    dot_config/...
```

Add `^/chezmoi$` and `^/\.chezmoiroot$` to `.stow-local-ignore` so stow never
touches that subtree. Then point chezmoi at the repo:

```toml
# ~/.config/chezmoi/chezmoi.toml  (per-machine, NOT committed)
sourceDir = "~/dotfiles"
```

## Source state attributes

Prefixes on source filenames:

| prefix | effect |
|---|---|
| `dot_` | target gets a leading dot (`dot_zshrc` -> `.zshrc`) |
| `private_` | strip group/world permissions |
| `readonly_` | strip write permissions |
| `executable_` | add execute permission |
| `symlink_` | create a symlink instead of a regular file |
| `create_` | create if absent, then never overwrite |
| `modify_` | contents are a script that transforms the existing file |
| `remove_` | remove the target |
| `empty_` | keep the file even when empty (empty files are removed by default) |
| `encrypted_` | file is encrypted in the source state |
| `literal_` | stop parsing further prefixes |
| `external_` | ignore attributes on child entries |

Script prefixes: `run_`, plus `once_` (run only if these contents never ran) and
`onchange_` (run if contents changed for this filename).

Suffixes: `.tmpl` treats contents as a template; `.literal` stops suffix parsing.

## Special files and directories

| name | purpose |
|---|---|
| `.chezmoiroot` | relocate the source state into a subdirectory |
| `.chezmoiignore` | which targets to skip — **is itself a template** |
| `.chezmoidata.$FORMAT`, `.chezmoidata/` | data committed to the repo, shared by all machines |
| `.chezmoitemplates/` | reusable fragments, included with `{{ template "name" . }}` |
| `.chezmoi.$FORMAT.tmpl` | template for the per-machine config, rendered at `chezmoi init` |
| `.chezmoiexternal.$FORMAT`, `.chezmoiexternals/` | fetch external files/archives |
| `.chezmoiscripts/` | scripts that are run but never written to `$HOME` |
| `.chezmoiremove` | targets to delete |
| `.chezmoiversion` | minimum chezmoi version required |

## Coexistence with stow

One owner per path. The failure is silent and bidirectional: `chezmoi apply`
overwrites a stow symlink with a real file, and `stow -R` then conflicts with
what chezmoi wrote.

Guard before every `chezmoi apply` on a stow-managed machine:

```bash
python3 ~/.claude/skills/dotfiles/scripts/check_dotfiles.py overlap
```

If it reports a conflict, pick one owner: `chezmoi forget <path>` to give it back
to stow, or delete it from the stow package to give it to chezmoi.

Day-to-day commands (`apply`, `status`, `diff`, `update`) live in
`chezmoi-workflow.md`.

# chezmoi day-to-day workflow

## Applying

`chezmoi apply` ensures **every target in the source state**, i.e. exactly what
`chezmoi managed` lists -- not everything in `$HOME`. Anything stow owns is
untouched, because chezmoi has no idea it exists.

```bash
chezmoi status                    # what drifted, and what apply would do
chezmoi diff                      # the actual content change
chezmoi apply --dry-run --verbose # rehearse, change nothing
chezmoi apply                     # everything chezmoi manages
chezmoi apply ~/.config/mise      # just this path (recurses by default)
```

`chezmoi status` prints two columns: the first is the target vs. what chezmoi
last wrote, the second is what `apply` will do. `A` created, `D` deleted,
`M` modified, `R` script will run, space no change. `MM` means you changed it
*and* apply will change it back.

Useful flags:

| flag | effect |
|---|---|
| `-n`, `--dry-run` | change nothing; pair with `-v` |
| `-x`, `--exclude <types>` | skip entry types |
| `-i`, `--include <types>` | only these types |
| `--init` | regenerate the config file from `.chezmoi.toml.tmpl` first |
| `--force` | **make all changes without prompting** -- skips the drift guard |
| `-r=false` | do not recurse |

Entry types for `-x`/`-i` (all verified against 2.72): `all`, `dirs`, `files`,
`remove`, `scripts`, `symlinks`, `encrypted`, `externals`, `always`. Running
`chezmoi apply -x scripts` is the usual way to apply config without executing
`run_` scripts.

### chezmoi update pulls the WHOLE repo

`chezmoi update` is `git pull --autostash --rebase` in the source directory,
followed by an apply. Because `sourceDir` is `~/dotfiles`, that pull updates the
**entire stow repo**, not just `chezmoi/`. It also autostashes uncommitted work.

On a dirty tree prefer doing it explicitly, so the git step is something you
chose:

```bash
git -C ~/dotfiles pull --rebase
chezmoi diff && chezmoi apply
```

## Files another tool rewrites

Some configs have a second writer: `mise use -g <tool>` rewrites
`~/.config/mise/config.toml`, `rustup` rewrites its own, shell installers append
to rc files. The target then drifts from the source, and `chezmoi apply` wants to
revert it.

chezmoi does notice. It prompts -- `"<path> has changed since chezmoi last wrote
it?"` -- and with no TTY it refuses rather than guessing. The danger is not
silence, it is answering that prompt on autopilot, or running `--force`, which
makes all changes without prompting.

Workflow for these:

```bash
mise use -g some-tool          # the other tool writes the target
chezmoi re-add ~/.config/mise/config.toml   # capture it back into the source
chezmoi diff                   # confirm nothing is left pending
```

`chezmoi status` lists targets that have drifted; make it a habit before `apply`.

**Do not template a file that another tool rewrites.** `chezmoi re-add` refuses
to overwrite templates, so the cheap round-trip above stops working and every
change has to be merged into the template by hand. If such a file genuinely
needs per-machine differences, prefer the app's own include mechanism, or split
the machine-specific part into a second file the other tool does not touch.


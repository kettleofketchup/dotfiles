# GNU stow in this repo

`~/dotfiles` is a **single stow package**: the repo root maps onto `$HOME`.

```bash
stow -d ~/dotfiles -t ~ -n -v .    # dry run, always do this first
stow -d ~/dotfiles -t ~ .          # apply
stow -d ~/dotfiles -t ~ -R .       # restow (re-link after moving files)
```

Do not `cd` into the repo to run these; `-d`/`-t` is equivalent and avoids hook issues.

## Tree folding

If a target directory does not exist in `$HOME`, stow symlinks the **whole
directory** (`~/.config/alacritty -> ../dotfiles/.config/alacritty`). If it
already exists as a real directory, stow descends and links individual files.

Consequence when auditing: a correctly stowed file is often *not itself a
symlink* — its parent is. Compare resolved paths, never test the leaf for
symlink-ness. `scripts/check_dotfiles.py drift` does this correctly.

## .stow-local-ignore

Lives in the package root. Semantics that matter:

- A present ignore file **replaces** stow's built-in default list; it does not extend it.
- Every pattern is a regex, implicitly anchored (`^...$`).
- A pattern containing `/` matches the path relative to the package root, with a
  leading slash: `^/AGENTS\.md$` ignores only the repo-root copy.
- Any other pattern matches **any single path segment**, so `dev` prunes every
  `dev/` at every depth.
- Blank lines and `#` comments are skipped.
- stow never stows `.stow-local-ignore` itself.

**Only `.stow-local-ignore` (package) and `~/.stow-global-ignore` are real.**
Files named `.stow-ignore` or `.stowignore` are not recognised by GNU stow — in
this repo they were themselves stowed into `$HOME` as junk symlinks.

## Conflicts and --adopt

A conflict aborts the **entire** stow run, so one stale file blocks everything:

```
* cannot stow dotfiles/.zshrc over existing target .zshrc
  since neither a link nor a directory and --adopt not specified
```

When the live file is the one you want to keep:

```bash
stow -d ~/dotfiles -t ~ -n -v --adopt .   # preview
stow -d ~/dotfiles -t ~ --adopt .         # moves live file INTO repo, links it back
git -C ~/dotfiles diff                    # review exactly what was adopted
```

`--adopt` overwrites the repo copy with the live one. Only safe when the repo
file is committed and clean — git is the undo.

## Per-host packages

Add a directory to `.stow-local-ignore` so `stow .` skips it, then stow it
explicitly on the machines that want it:

```
~/dotfiles/homepc/.config/ghostty/local.conf
~/dotfiles/mac/.config/ghostty/local.conf

stow -d ~/dotfiles -t ~ homepc     # on the Linux box
stow -d ~/dotfiles -t ~ mac        # on the Mac
```

Use this for *small* per-host deltas combined with an app-native include (see
`machine-differences.md`). Duplicating an entire config per host invites drift.

## The un-stow hazard

Installers that write with `mv tmp target` **replace a symlink with a real
file**, silently detaching it from the repo. Writers using `cat tmp > target`
write through the symlink and are safe.

Omarchy's migrations do both: `1781043107.sh` uses `cat >` (safe),
`1781063758.sh` uses `mv` (breaks the link). This is how
`~/.config/ghostty/config` became a real file while `themes/` beside it stayed a
symlink.

After any omarchy update or OS-level config migration:

```bash
python3 ~/.claude/skills/dotfiles/scripts/check_dotfiles.py drift
```

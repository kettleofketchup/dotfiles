# Machine differences (mac vs homepc)

## Decision order — stop at the first that fits

**1. Does the app have its own include mechanism?** Use it. No dotfile manager
involved, works the same on every machine, and the shared file stays readable.

| app | include directive |
|---|---|
| ghostty | `config-file = ?local.conf` |
| zsh | `[[ -f ~/.config/zsh/local.zsh ]] && source ~/.config/zsh/local.zsh` |
| git | `[include] path = ~/.config/git/local` |
| ssh | `Include ~/.ssh/config.local` |
| tmux | `source-file -q ~/.tmux.local.conf` |
| kitty | `include local.conf` |

**2. Does a whole file differ per host?** Use a per-host stow package
(`homepc/`, `mac/`) — see `stow.md`.

**3. Do you need templating, a computed value, or a secret?** Now use chezmoi.

Reaching for chezmoi templating where the app already has an include adds a
render step and a tool dependency for nothing.

## ghostty concretely

Ghostty resolves relative `config-file` paths against the file containing the
key, processes `config-file` keys at the **end** of the current file (so the
included file wins), and treats a `?` prefix as optional — a missing file is
ignored rather than an error.

```
# ~/.config/ghostty/config      <- shared, stow-tracked
font-size = 12
config-file = ?local.conf       <- per-machine, wins over the above
```

Then track the delta per host: `~/dotfiles/mac/.config/ghostty/local.conf`,
`~/dotfiles/homepc/.config/ghostty/local.conf`. Nothing is duplicated except the
lines that genuinely differ.

## chezmoi's layers, general to specific

1. **`.chezmoidata.yaml`** in the repo — defaults for every machine, committed.
2. **`~/.config/chezmoi/chezmoi.toml` `[data]`** — this machine's values, not
   committed, overrides the above. Generated at `chezmoi init` from
   `.chezmoi.toml.tmpl`, which can prompt and store the answer.
3. **`.chezmoiignore`** — which files exist at all here. Itself a template.
4. **`.tmpl` branching** — differences inside one file.
5. **`.chezmoitemplates/`** — shared fragments, the base/override mechanism.

## Template variables

```gotemplate
{{ .chezmoi.os }}             darwin | linux
{{ .chezmoi.arch }}           arm64  | amd64
{{ .chezmoi.hostname }}       KettleHome
{{ .chezmoi.osRelease.id }}   arch          (linux only)
{{ .chezmoi.username }}  {{ .chezmoi.homeDir }}
```

## Patterns

Branch inside a file:

```gotemplate
{{ if eq .chezmoi.os "darwin" -}}
font-size = 14
macos-option-as-alt = true
{{- else -}}
font-size = 12
{{- end }}
```

Skip whole files per machine (`.chezmoiignore` is a template, so the logic is
inverted — you list what to *ignore*):

```gotemplate
{{ if ne .chezmoi.os "darwin" }}
.config/aerospace
{{ end }}
```

Share a base fragment across targets:

```
.chezmoitemplates/ghostty-common      <- the shared body
```
```gotemplate
{{ template "ghostty-common" . }}
{{ if eq .chezmoi.os "darwin" }}macos-option-as-alt = true{{ end }}
```

Prompt once at init and reuse the answer:

```gotemplate
{{/* .chezmoi.toml.tmpl */}}
[data]
role = {{ promptStringOnce . "role" "machine role (work/home)" | quote }}
```

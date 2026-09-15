# Secrets

**This repo is PUBLIC** (`github.com/kettleofketchup/dotfiles`). Everything
committed is world-readable and assume-already-cloned. A secret that lands here
is burned the moment it is pushed: **rotate it, do not just delete it** —
rewriting history does not un-publish what was already fetched or indexed.

Installed and verified on this machine: `op` 2.39.0 (`/usr/bin/op`), `age` 1.3.1
(`~/.local/bin/age`), `gpg` 2.4.9. `chezmoi doctor` confirms chezmoi sees all three.

`~/.config/chezmoi/chezmoi.toml` lives **outside** the repo and is mode `0600`.
It may hold private data, so keep it there — never move it under `~/dotfiles`.

Two mechanisms, chosen by one question: **is this secret needed to bootstrap the
machine?**

| | age (encrypted in repo) | 1Password (`op`) |
|---|---|---|
| works offline | yes | no |
| external dependency | none at apply time | `op` installed + signed in |
| bootstrap-safe | yes, once the key is present | no — chicken-and-egg |
| rotation | re-encrypt and commit | change it in 1Password, done |
| secret in repo | yes, encrypted | never |

**Rule:** age for anything required *to get the machine running* (SSH keys, the
deploy token that clones the repo). 1Password for everything else. Putting the
SSH key you need to clone the dotfiles behind 1Password is how you lock yourself
out of your own bootstrap.

## 1Password

Requires the 1Password CLI installed and signed in. chezmoi checks for a valid
session token and prompts interactively when it is missing or expired; set
`onepassword.prompt = false` to fail instead of prompting.

```gotemplate
{{ onepasswordRead "op://Private/github/token" }}          # simplest, prefer this
{{ (onepasswordDetailsFields "$UUID").password.value }}
{{ (index (onepassword "$UUID").fields 1).value }}
{{ onepasswordItemFields "$UUID" | toJson }}
{{ onepasswordDocument "$UUID" }}
```

Caveats worth knowing:

- Each call shells out to `op`. Many secrets makes `chezmoi apply` noticeably slow.
- Upstream warning: *do not* use `prompt` on shared machines — an interactively
  acquired session token is passed to the CLI as a command line parameter, which
  is visible to other users. Fine on a single-user workstation.
- For headless machines set `onepassword.mode` to `service` or `connect`. In
  those modes `account` parameters are disallowed, and `onepasswordDocument` is
  unavailable in `connect` mode.

## age

```bash
chezmoi age-keygen --output=$HOME/key.txt   # prints the public key (recipient)
chezmoi add --encrypt ~/.ssh/id_ed25519     # stored as encrypted_ in the source
```

```toml
# ~/.config/chezmoi/chezmoi.toml
encryption = "age"              # must come before the [age] section
[age]
    identity  = "/home/kettle/key.txt"
    recipient = "age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p"
```

Multiple keys use the plural forms `identities` / `recipients`.

Encrypted files carry the `encrypted_` prefix in the source state and are
decrypted automatically during `apply`, `diff` and `status`.

On a new machine: copy `key.txt` across (this is the one secret that cannot live
in the repo — store it in 1Password and retrieve it by hand during bootstrap),
then set `age.identity` to its path.

## Auditing

Run these before pushing anything unusual, and after any incident:

```bash
# working tree
git -C ~/dotfiles grep -nIE 'ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{50}|sk-ant-[A-Za-z0-9_-]{50}|AKIA[0-9A-Z]{16}|glpat-[A-Za-z0-9_-]{20}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY'

# every commit ever made (slow; 207 commits ~ seconds)
git -C ~/dotfiles grep -nIE '<same pattern>' $(git -C ~/dotfiles rev-list --all)

# filenames that should never have been added
git -C ~/dotfiles log --all --pretty=format: --name-only --diff-filter=A \
  | sort -u | grep -iE '(^|/)\.env|\.pem$|\.key$|id_rsa|id_ed25519|netrc|\.npmrc'
```

Length bounds matter: `ghp_[A-Za-z0-9]{36}` matches a real token but not the
`ghp_xxxxxxxxxxxx` placeholders that appear throughout the skill docs.

Last audit 2026-09-15: working tree clean (three hits, all documentation
placeholders), **0 hits across all 207 commits**, no secret-shaped filenames
ever added, `~/.ssh` is not in the repo.

## Never

- Do not commit a plaintext secret, even briefly — rewriting history does not
  un-leak it. Rotate instead.
- Do not put secrets in `.chezmoidata.*`; that file is committed as-is.
- `chezmoi.toml` may hold private data; upstream advises permissions `0600`.

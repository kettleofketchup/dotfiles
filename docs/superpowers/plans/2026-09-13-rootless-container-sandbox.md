# Rootless Container Sandbox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the root Docker daemon on this Arch workstation with rootless podman, so `docker <anything>` works without sudo or docker-group membership and container root maps to an unprivileged host UID.

**Architecture:** `podman-docker` provides `/usr/bin/docker` as a shim over podman, which runs daemonless in the user's namespace (`kettle:100000:65536`). Interactive docker stays behaviorally stock; a separate `sbx` wrapper supplies aggressive hardening for untrusted agent-run code. A verification script asserts the security properties and doubles as this plan's test suite.

**Tech Stack:** podman 6.1.0, crun, netavark + aardvark-dns, passt, systemd user units, GNU Stow, bash.

**Spec:** `docs/superpowers/specs/2026-09-13-rootless-container-sandbox-design.md`

## Global Constraints

- Target user is `kettle`, uid 1000, subuid/subgid range `kettle:100000:65536` (already allocated — do not change).
- Arch Linux, kernel 7.1.9-arch1-2, cgroup v2 with `cpu memory pids` delegated.
- All podman packages come from the official `extra` repo. **No AUR in this plan.**
- Dotfiles are GNU Stow-managed; `~/bin -> dotfiles/bin` and `~/.config -> dotfiles/.config` are already linked. New files go in the repo, then `stow -R .`.
- Private registries `<your-registry-host-1>` and `<your-registry-host-2>` must keep working; their CAs are at `/etc/docker/certs.d/*/ca.crt`.
- Commit messages end with `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>` and carry no other watermark.
- Use `git -C <path>` rather than `cd` for git operations in subdirectories.

## Do not use a git worktree for this plan

Stow symlinks in `$HOME` point at the main checkout (`/home/kettle/dotfiles`). Editing a worktree copy would leave `~/.config/containers` pointing at unmodified files, so verification would test the wrong content. Work on a branch in the main checkout instead:

```bash
git -C /home/kettle/dotfiles checkout -b rootless-podman
```

## Irreversibility warning

Task 3 removes the `docker` package. Everything in `/var/lib/docker` — images, named volumes, containers — becomes invisible to podman, which uses `~/.local/share/containers`. **Task 1 is a hard gate.** Do not proceed past it until volume data is migrated or explicitly written off.

---

### Task 1: Inventory and preserve existing Docker state

**Files:**
- Create: `/home/kettle/docker-migration/inventory.txt` (scratch, outside the repo — not committed)
- Create: `/home/kettle/docker-migration/volumes/` (scratch tarballs)
- Create: `bin/container-rollback`

**Interfaces:**
- Produces: `bin/container-rollback`, an executable that restores the Docker setup. Later tasks append nothing to it; it is written once, here, while the original state is still observable.

- [ ] **Step 1: Capture the inventory**

```bash
mkdir -p /home/kettle/docker-migration/volumes
{
  echo "=== captured $(date -Is) ==="
  echo "--- packages ---";        pacman -Q docker docker-compose docker-buildx lazydocker ufw-docker 2>&1
  echo "--- images ---";          sudo docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' 2>&1
  echo "--- containers ---";      sudo docker ps -a --format '{{.Names}}\t{{.Image}}\t{{.Status}}' 2>&1
  echo "--- volumes ---";         sudo docker volume ls --format '{{.Name}}' 2>&1
  echo "--- disk ---";            sudo du -sh /var/lib/docker 2>&1
  echo "--- per-volume size ---"; sudo sh -c 'du -sh /var/lib/docker/volumes/* 2>/dev/null' 2>&1
} | tee /home/kettle/docker-migration/inventory.txt
```

- [ ] **Step 2: Review the inventory with the user — STOP HERE**

Print the volume list and sizes. For each named volume, the user must say *keep* or *discard*. Known candidates from the compose projects on this machine:

- `~/.config/windows/docker-compose.yml` — dockur/windows, typically a multi-GB VM disk image
- `~/.local/share/cliproxyapi/compose.yaml`
- `~/<private-repo>/investigations/harbor-dh-rewriter/compose.yaml`
- `~/git_repos/{hookshot,hookshot-certutil-nss,hookshot-release,hookshot-cache-lru,vscode-offline,builder/edge-go}`

Do not continue without an explicit decision per volume.

- [ ] **Step 3: Export every volume marked keep**

Write `keep-volumes.txt` first, one volume name per line, from the Step 2 decision.

```bash
for vol in $(cat /home/kettle/docker-migration/keep-volumes.txt); do
  echo "exporting $vol"
  sudo docker run --rm \
    -v "$vol":/from:ro \
    -v /home/kettle/docker-migration/volumes:/to \
    alpine tar czf "/to/${vol}.tar.gz" -C /from .
done
sudo chown -R kettle:kettle /home/kettle/docker-migration/volumes
ls -lh /home/kettle/docker-migration/volumes
```

- [ ] **Step 4: Back up host config that the swap will disturb**

```bash
sudo cp -a /etc/docker /home/kettle/docker-migration/etc-docker-backup
sudo chown -R kettle:kettle /home/kettle/docker-migration/etc-docker-backup
find /home/kettle/docker-migration/etc-docker-backup -type f
```

Expected: both `ca.crt` files and `daemon.json` present.

- [ ] **Step 5: Write the rollback script**

Create `bin/container-rollback`:

```bash
#!/usr/bin/env bash
# container-rollback — restore the root-Docker setup replaced by rootless podman.
# See docs/superpowers/specs/2026-09-13-rootless-container-sandbox-design.md
set -euo pipefail

BACKUP="${BACKUP:-/home/kettle/docker-migration}"

if [[ ! -d "$BACKUP/etc-docker-backup" ]]; then
  echo "error: no backup at $BACKUP/etc-docker-backup" >&2
  exit 1
fi

echo "==> stopping rootless podman"
systemctl --user disable --now podman.socket 2>/dev/null || true

echo "==> restoring docker packages"
sudo pacman -S --needed --noconfirm docker docker-compose ufw-docker
# podman-docker Conflicts With docker, so pacman removes it here automatically.

echo "==> restoring /etc/docker"
sudo mkdir -p /etc/docker
sudo cp -a "$BACKUP/etc-docker-backup/." /etc/docker/

echo "==> removing podman-side host config"
sudo rm -f /etc/sysctl.d/99-rootless-ports.conf
sudo sysctl --system >/dev/null

echo "==> re-enabling the root daemon"
sudo systemctl enable --now docker.socket

echo "==> done. Remove DOCKER_HOST from .config/zsh/exports.zsh and restow:"
echo "    git -C /home/kettle/dotfiles checkout -- .config/zsh/exports.zsh"
echo "    stow -R -d /home/kettle/dotfiles -t /home/kettle ."
```

- [ ] **Step 6: Verify the rollback script parses and is executable**

```bash
chmod +x /home/kettle/dotfiles/bin/container-rollback
bash -n /home/kettle/dotfiles/bin/container-rollback && echo "syntax OK"
```

Expected: `syntax OK`.

- [ ] **Step 7: Commit**

```bash
git -C /home/kettle/dotfiles add bin/container-rollback
git -C /home/kettle/dotfiles commit -m "feat(containers): add rollback script for the podman migration

Restores docker packages, /etc/docker contents, and the root daemon socket
from the pre-migration backup in /home/kettle/docker-migration.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Verification harness (the failing test)

**Files:**
- Create: `bin/container-sandbox-verify`

**Interfaces:**
- Consumes: nothing.
- Produces: `bin/container-sandbox-verify`, exit 0 when every property holds, exit 1 otherwise. Every later task is "make more of this pass." Tests needing a network pull are skipped when `SKIP_NET=1`.

- [ ] **Step 1: Write the verification script**

Create `bin/container-sandbox-verify`:

```bash
#!/usr/bin/env bash
# container-sandbox-verify — assert the rootless container security properties.
# Spec: docs/superpowers/specs/2026-09-13-rootless-container-sandbox-design.md
set -uo pipefail

PASS=0; FAIL=0; SKIP=0
IMG="${IMG:-docker.io/library/alpine:latest}"

ok()   { printf '  \033[32mPASS\033[0m  %s\n' "$1"; PASS=$((PASS+1)); }
bad()  { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; FAIL=$((FAIL+1)); }
skip() { printf '  \033[33mSKIP\033[0m  %s\n' "$1"; SKIP=$((SKIP+1)); }
sect() { printf '\n\033[1m%s\033[0m\n' "$1"; }

# ---- engine precondition -------------------------------------------------
# Every check below depends on being able to run a container at all. Without
# this gate a `refute` passes for the WRONG reason: the command failed because
# the engine was unreachable, not because the sandbox contained it.
ENGINE_OK=0
docker run --rm "$IMG" true >/dev/null 2>&1 && ENGINE_OK=1

engine_or_skip() {
  if [[ "$ENGINE_OK" -ne 1 ]]; then
    skip "$1 (engine cannot run containers - NOT TESTED)"
    return 1
  fi
  return 0
}

# contained NAME <docker run args...>
# Passes ONLY when the operation fails AND the failure is a genuine denial.
contained() {
  local n="$1"; shift
  engine_or_skip "$n" || return
  local out rc
  out="$(docker run --rm "$@" 2>&1)"; rc=$?
  if [[ "$rc" -eq 0 ]]; then
    bad "$n (operation SUCCEEDED - not contained)"
  elif grep -qiE 'permission denied|read-only file system|operation not permitted' <<<"$out"; then
    ok "$n"
  else
    bad "$n (inconclusive - engine error, not a denial: $(head -c 120 <<<"$out" | tr '\n' ' '))"
  fi
}

# assert NAME COMMAND...  -> passes when COMMAND succeeds
assert() { local n="$1"; shift; if "$@" >/dev/null 2>&1; then ok "$n"; else bad "$n"; fi; }
# refute NAME COMMAND...  -> passes when COMMAND fails
refute() { local n="$1"; shift; if "$@" >/dev/null 2>&1; then bad "$n"; else ok "$n"; fi; }

# sbx_denied NAME <sbx run args...>
# Passes ONLY when the sandboxed operation fails AND the failure is a genuine
# denial rather than an sbx/engine malfunction.
sbx_denied() {
  local n="$1"; shift
  local out rc
  out="$(sbx run "$@" 2>&1)"; rc=$?
  if [[ "$rc" -eq 0 ]]; then
    bad "$n (operation SUCCEEDED - not sandboxed)"
  elif grep -qiE 'permission denied|read-only file system|operation not permitted|bad address|network is unreachable|could not resolve|temporary failure in name resolution|name does not resolve' <<<"$out"; then
    ok "$n"
  else
    bad "$n (inconclusive - sbx or engine error, not a denial: $(head -c 120 <<<"$out" | tr '\n' ' '))"
  fi
}

sect "Host privilege"
refute "no root dockerd running"            pgrep -u root -x dockerd
refute "user is not in the docker group"    sh -c 'id -nG | grep -qw docker'
assert "docker resolves to podman"          sh -c 'docker --version 2>&1 | grep -qi podman'
assert "docker works without sudo"          docker info
assert "linger enabled for kettle"          sh -c 'loginctl show-user kettle -p Linger | grep -q Linger=yes'
assert "podman user socket present"         test -S "${XDG_RUNTIME_DIR:-}/podman/podman.sock"
assert "DOCKER_HOST points at user socket"  sh -c '[ "${DOCKER_HOST:-}" = "unix://${XDG_RUNTIME_DIR:-}/podman/podman.sock" ]'

sect "User namespace mapping"
engine_or_skip "container uid 0 maps to host 1000" && assert "container uid 0 maps to host 1000" \
  sh -c "docker run --rm '$IMG' head -1 /proc/self/uid_map | awk '\$1==0 && \$2==1000 {f=1} END{exit !f}'"
engine_or_skip "container non-root maps into subuid range" && assert "container non-root maps into subuid range" \
  sh -c "docker run --rm '$IMG' sed -n 2p /proc/self/uid_map | awk '\$2==100000 {f=1} END{exit !f}'"

sect "Host filesystem containment"
contained "cannot read /etc/shadow via host mount"  -v /:/host:ro "$IMG" cat /host/etc/shadow
contained "cannot write host root via host mount"   -v /:/host "$IMG" touch /host/sbx-probe
contained "privileged still cannot write host root" --privileged -v /:/host "$IMG" touch /host/sbx-probe
contained "cannot list root-owned /root"            -v /:/host:ro "$IMG" ls /host/root

sect "Storage and runtime"
if command -v podman >/dev/null 2>&1 && podman info >/dev/null 2>&1; then
  assert "storage driver is native overlay" \
    sh -c "podman info --format '{{.Store.GraphDriverName}}' | grep -qx overlay"
  refute "not falling back to fuse-overlayfs" \
    sh -c "podman info --format '{{.Store.GraphOptions}}' | grep -q mount_program"
  assert "default runtime is crun" \
    sh -c "podman info --format '{{.Host.OCIRuntime.Name}}' | grep -qx crun"
else
  skip "storage driver is native overlay (podman not installed or unreachable - NOT TESTED)"
  skip "not falling back to fuse-overlayfs (podman not installed or unreachable - NOT TESTED)"
  skip "default runtime is crun (podman not installed or unreachable - NOT TESTED)"
fi

sect "Compatibility"
assert "unqualified image names resolve to docker.io" \
  sh -c "podman info --format '{{.Registries}}' | grep -q docker.io"
assert "<your-registry-host-1> CA installed" \
  test -f /etc/containers/certs.d/<your-registry-host-1>/ca.crt
assert "<your-registry-host-2> CA installed" \
  test -f /etc/containers/certs.d/<your-registry-host-2>/ca.crt
assert "unprivileged low ports permitted" \
  sh -c "[ \"\$(sysctl -n net.ipv4.ip_unprivileged_port_start)\" = 0 ]"

if [[ "${SKIP_NET:-0}" = 1 ]]; then
  skip "port 80 publish (SKIP_NET=1)"
else
  assert "can publish host port 80" \
    sh -c "docker run --rm -d --name sbxverify80 -p 80:80 '$IMG' sleep 5 >/dev/null && sleep 1 && docker rm -f sbxverify80 >/dev/null"
fi

sect "sbx sandbox profile"
assert "sbx is executable"                 test -x "$HOME/bin/sbx"
if [[ "$ENGINE_OK" -eq 1 && -x "$HOME/bin/sbx" ]]; then
  sbx_denied "sbx denies network by default"  "$IMG" wget -q -T3 -O- https://example.com
  assert "sbx allows network with --net"     sbx run --net "$IMG" true
  sbx_denied "sbx workdir is read-only"       "$IMG" touch /work/probe
  sbx_denied "sbx rootfs is read-only"        "$IMG" touch /probe
  assert "sbx tmpfs is writable"             sbx run "$IMG" sh -c 'echo ok > /tmp/x'
  assert "sbx runs as non-root"              sh -c "sbx run '$IMG' id -u | grep -qx 65534"
else
  skip "sbx denies network by default (engine or sbx unavailable - NOT TESTED)"
  skip "sbx allows network with --net (engine or sbx unavailable - NOT TESTED)"
  skip "sbx workdir is read-only (engine or sbx unavailable - NOT TESTED)"
  skip "sbx rootfs is read-only (engine or sbx unavailable - NOT TESTED)"
  skip "sbx tmpfs is writable (engine or sbx unavailable - NOT TESTED)"
  skip "sbx runs as non-root (engine or sbx unavailable - NOT TESTED)"
fi

printf '\n\033[1m%d passed, %d failed, %d skipped\033[0m\n' "$PASS" "$FAIL" "$SKIP"
[[ "$FAIL" -eq 0 ]]
```

- [ ] **Step 2: Run it to confirm it fails**

```bash
chmod +x /home/kettle/dotfiles/bin/container-sandbox-verify
/home/kettle/dotfiles/bin/container-sandbox-verify; echo "exit=$?"
```

Expected: many FAIL lines (`docker resolves to podman`, `sbx is executable`, …) and `exit=1`. A few pass already — `user is not in the docker group` passes because that was never done. Checks that depend on the engine being reachable (`docker run` succeeding) or on podman/sbx being installed — the two userns-mapping checks, the four host-filesystem-containment checks, the three storage/runtime checks, and five of the six sbx-profile checks — report SKIP rather than PASS or FAIL, because the engine cannot run a container yet and neither podman nor sbx exist. `no root dockerd running` may FAIL instead of PASS if `docker.service` is actively running rather than merely socket-activated and idle. That is correct; the suite measures the end state, and a SKIP or FAIL here is not a bug — it means the property has genuinely not been established yet.

- [ ] **Step 3: Commit**

```bash
git -C /home/kettle/dotfiles add bin/container-sandbox-verify
git -C /home/kettle/dotfiles commit -m "test(containers): add rootless sandbox verification harness

Asserts userns mapping, host filesystem containment under -v /:/host
including --privileged, storage driver, registry CA presence, and the
sbx profile's network and filesystem restrictions.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Swap docker for podman

**Files:**
- Modify: system packages (no repo files)

**Interfaces:**
- Consumes: Task 1's backup and volume exports.
- Produces: `/usr/bin/docker` as a podman shim; `podman` on PATH.

- [ ] **Step 1: Confirm Task 1's gate is closed**

```bash
test -f /home/kettle/docker-migration/inventory.txt || { echo "STOP: Task 1 not done"; exit 1; }
test -d /home/kettle/docker-migration/etc-docker-backup || { echo "STOP: no /etc/docker backup"; exit 1; }
ls /home/kettle/docker-migration/volumes/
echo "gate OK"
```

- [ ] **Step 2: Stop the root daemon**

```bash
sudo systemctl disable --now docker.socket docker.service
systemctl is-active docker.socket docker.service; echo "(inactive expected)"
```

- [ ] **Step 3: Install podman, removing docker**

```bash
sudo pacman -S --needed podman podman-docker podman-compose netavark aardvark-dns passt crun
```

pacman will prompt to remove `docker` and `ufw-docker`, because `podman-docker` conflicts with `docker`. Accept. `docker-compose` and `lazydocker` have no hard dependency on `docker` and must remain — confirm they are absent from the removal list before accepting.

- [ ] **Step 4: Verify the shim**

```bash
docker --version
command -v docker
pacman -Qo /usr/bin/docker
```

Expected: a version string mentioning podman, `/usr/bin/docker`, owned by `podman-docker`.

- [ ] **Step 5: Confirm the harness moved**

```bash
SKIP_NET=1 /home/kettle/dotfiles/bin/container-sandbox-verify; echo "exit=$?"
```

Expected: `docker resolves to podman` and `docker works without sudo` now PASS. Still failing: socket, DOCKER_HOST, linger, CAs, sysctl, crun default, sbx. `exit=1` is correct at this stage.

- [ ] **Step 6: Record the step**

No repo files changed, so commit empty to keep the history legible:

```bash
git -C /home/kettle/dotfiles commit --allow-empty -m "chore(containers): swap docker for podman-docker

Removes the root Docker daemon and ufw-docker; /usr/bin/docker is now a
podman shim. docker-compose and lazydocker retained.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Migrate private registry CAs

**Files:**
- Modify: `/etc/containers/certs.d/` (system)

**Interfaces:**
- Consumes: `/home/kettle/docker-migration/etc-docker-backup/certs.d/`.
- Produces: working pulls from `<your-registry-host-1>` and `<your-registry-host-2>`.

- [ ] **Step 1: Write the failing check**

```bash
test -f /etc/containers/certs.d/<your-registry-host-2>/ca.crt && echo PASS || echo "FAIL (expected)"
```

Expected: `FAIL (expected)`.

- [ ] **Step 2: Copy the CAs to podman's path**

```bash
sudo mkdir -p /etc/containers/certs.d
sudo cp -a /home/kettle/docker-migration/etc-docker-backup/certs.d/. /etc/containers/certs.d/
sudo find /etc/containers/certs.d -type f -name ca.crt
```

Expected: both `<your-registry-host-1>/ca.crt` and `<your-registry-host-2>/ca.crt`.

- [ ] **Step 3: Verify the check passes**

```bash
test -f /etc/containers/certs.d/<your-registry-host-2>/ca.crt && echo PASS
test -f /etc/containers/certs.d/<your-registry-host-1>/ca.crt && echo PASS
```

Expected: two `PASS` lines.

- [ ] **Step 4: Prove a real pull works**

```bash
podman login <your-registry-host-2>
podman pull <your-registry-host-2>/<a-known-image>:<tag>
```

Substitute a real image from `inventory.txt`. A TLS/x509 error means the CA path is wrong; any other outcome (auth failure, 404) means TLS succeeded and this task is done.

- [ ] **Step 5: Record the step**

```bash
git -C /home/kettle/dotfiles commit --allow-empty -m "chore(containers): migrate registry CAs to /etc/containers/certs.d

Podman does not read /etc/docker/certs.d, so the <your-registry-host-1> and
<your-registry-host-2> CAs are copied to podman's search path.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Enable the user socket, linger, and low ports

**Files:**
- Create: `/etc/sysctl.d/99-rootless-ports.conf` (system)
- Modify: `.config/zsh/exports.zsh` (remove the `$HOME/.docker/bin` PATH line at line 8; add `DOCKER_HOST`)

**Interfaces:**
- Produces: `$XDG_RUNTIME_DIR/podman/podman.sock` and `DOCKER_HOST` pointing at it, for Docker-API clients (lazydocker, testcontainers, compose).

- [ ] **Step 1: Enable the user socket and linger**

```bash
systemctl --user enable --now podman.socket
sudo loginctl enable-linger kettle
systemctl --user is-active podman.socket
loginctl show-user kettle -p Linger
test -S "$XDG_RUNTIME_DIR/podman/podman.sock" && echo "socket OK"
```

Expected: `active`, `Linger=yes`, `socket OK`.

- [ ] **Step 2: Permit unprivileged low ports**

```bash
echo 'net.ipv4.ip_unprivileged_port_start=0' | sudo tee /etc/sysctl.d/99-rootless-ports.conf
sudo sysctl --system >/dev/null
sysctl net.ipv4.ip_unprivileged_port_start
```

Expected: `net.ipv4.ip_unprivileged_port_start = 0`.

Tradeoff, restated from the spec: any unprivileged process on this machine may now bind ports below 1024, not only podman.

- [ ] **Step 3: Edit exports.zsh**

Delete the line `export PATH="$HOME/.docker/bin":$PATH` (a Docker Desktop leftover — that directory does not exist) and append:

```sh
# Rootless podman exposes a Docker-compatible API socket; point Docker-API
# clients (lazydocker, testcontainers, compose) at it.
export DOCKER_HOST="unix://${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/podman/podman.sock"
```

- [ ] **Step 4: Verify in a fresh shell**

```bash
zsh -lic 'echo "$DOCKER_HOST"; echo "$PATH" | tr : "\n" | grep -c "\.docker/bin"'
```

Expected: `unix:///run/user/1000/podman/podman.sock`, then `0`.

- [ ] **Step 5: Confirm API clients work**

```bash
docker compose version
timeout 5 lazydocker --help >/dev/null && echo "lazydocker OK"
```

- [ ] **Step 6: Commit**

```bash
git -C /home/kettle/dotfiles add .config/zsh/exports.zsh
git -C /home/kettle/dotfiles commit -m "feat(zsh): point Docker-API clients at the rootless podman socket

Sets DOCKER_HOST to the podman user socket and drops the stale
\$HOME/.docker/bin PATH entry left by Docker Desktop.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Stow podman configuration

**Files:**
- Create: `.config/containers/registries.conf`
- Create: `.config/containers/containers.conf`

**Interfaces:**
- Produces: bare image names resolving to docker.io; `crun` as the default runtime.

- [ ] **Step 1: Write the failing check**

```bash
podman info --format '{{.Host.OCIRuntime.Name}}'
```

Expected: `runc` — the default this task changes.

- [ ] **Step 2: Create the registries config**

`.config/containers/registries.conf`:

```toml
# Podman requires fully-qualified image names unless a search list exists.
# Docker muscle memory (`docker run alpine`) depends on this.
unqualified-search-registries = ["docker.io"]
```

- [ ] **Step 3: Create the engine config**

`.config/containers/containers.conf`. Deliberately close to stock — global hardening belongs in `sbx`, not here, because read-only or keep-id defaults break ordinary images:

```toml
[containers]
# Bound runaway processes without changing how normal images behave.
pids_limit = 4096
log_size_max = 10485760

[engine]
# crun starts faster and uses less memory than runc.
runtime = "crun"
```

- [ ] **Step 4: Restow and verify**

```bash
stow -R -d /home/kettle/dotfiles -t /home/kettle .
readlink -f /home/kettle/.config/containers/containers.conf
podman info --format '{{.Host.OCIRuntime.Name}}'
podman info --format '{{.Registries}}'
```

Expected: a path resolving into `dotfiles/`, runtime `crun`, registries listing `docker.io`.

- [ ] **Step 5: Confirm bare names resolve**

```bash
docker run --rm alpine echo "unqualified name OK"
```

Expected: `unqualified name OK`, with no registry-disambiguation prompt.

- [ ] **Step 6: Confirm native overlay, not fuse**

```bash
podman info --format '{{.Store.GraphDriverName}}'
podman info --format '{{.Store.GraphOptions}}'
```

Expected: `overlay`, with no `mount_program` in GraphOptions. If `mount_program` appears, podman fell back to `fuse-overlayfs`; kernel 7.1.9 supports unprivileged overlay natively, so investigate rather than accept it.

- [ ] **Step 7: Commit**

```bash
git -C /home/kettle/dotfiles add .config/containers/
git -C /home/kettle/dotfiles commit -m "feat(containers): add stowed podman registries and engine config

Restores docker-style unqualified image names and selects crun. Hardening
is intentionally kept out of the global config so stock images keep working;
it lives in bin/sbx instead.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: The `sbx` sandbox profile

**Files:**
- Create: `bin/sbx`

**Interfaces:**
- Consumes: podman from Task 3.
- Produces: `sbx run [--net] [--rw] [--dir PATH] [--memory SIZE] [--cpus N] [--pids N] [--user UID:GID] IMAGE [CMD...]`, exit code passed through from the container.

- [ ] **Step 1: Confirm the sbx assertions currently fail**

```bash
/home/kettle/dotfiles/bin/container-sandbox-verify 2>&1 | grep -A7 "sbx sandbox profile"
```

Expected: `FAIL  sbx is executable` and the rest of that section failing.

- [ ] **Step 2: Write the script**

Create `bin/sbx`:

```bash
#!/usr/bin/env bash
# sbx — run a container with hardened defaults, for untrusted code.
#
# Rootless podman already prevents a container from harming the host. This
# wrapper additionally constrains what the code can do *inside* its container:
# no capabilities, no network, no writable filesystem, bounded CPU/memory/PIDs.
#
# Spec: docs/superpowers/specs/2026-09-13-rootless-container-sandbox-design.md
set -euo pipefail

MEMORY="${SBX_MEMORY:-512m}"
CPUS="${SBX_CPUS:-1}"
PIDS="${SBX_PIDS:-128}"
USERSPEC="${SBX_USER:-65534:65534}"
TMPFS_SIZE="${SBX_TMPFS_SIZE:-64m}"
WORKDIR="${SBX_DIR:-$PWD}"
NETWORK="none"
MOUNT_MODE="ro"

usage() {
  cat <<'EOF'
sbx — run a container with hardened defaults, for untrusted code.

Usage:
  sbx run [options] IMAGE [COMMAND...]

Options:
  --net             Allow network access           (default: none)
  --rw              Mount the workdir read-write    (default: read-only)
  --dir PATH        Directory mounted at /work      (default: $PWD)
  --memory SIZE     Memory limit                    (default: 512m)
  --cpus N          CPU limit                       (default: 1)
  --pids N          PID limit                       (default: 128)
  --user UID:GID    User inside the container       (default: 65534:65534)
  -h, --help        Show this help

Env overrides: SBX_MEMORY SBX_CPUS SBX_PIDS SBX_USER SBX_DIR SBX_TMPFS_SIZE

Examples:
  sbx run python:3.12 python /work/script.py
  sbx run --net --rw node:22 npm install
EOF
}

[[ $# -eq 0 ]] && { usage; exit 2; }

case "$1" in
  -h|--help) usage; exit 0 ;;
  run)       shift ;;
  *)         echo "sbx: unknown subcommand '$1' (expected 'run')" >&2; exit 2 ;;
esac

while [[ $# -gt 0 ]]; do
  case "$1" in
    --net)     NETWORK="bridge"; shift ;;
    --rw)      MOUNT_MODE="rw";  shift ;;
    --dir)     WORKDIR="$2";     shift 2 ;;
    --memory)  MEMORY="$2";      shift 2 ;;
    --cpus)    CPUS="$2";        shift 2 ;;
    --pids)    PIDS="$2";        shift 2 ;;
    --user)    USERSPEC="$2";    shift 2 ;;
    -h|--help) usage; exit 0 ;;
    --)        shift; break ;;
    -*)        echo "sbx: unknown option '$1'" >&2; exit 2 ;;
    *)         break ;;
  esac
done

[[ $# -eq 0 ]] && { echo "sbx: no image given" >&2; exit 2; }
[[ -d "$WORKDIR" ]] || { echo "sbx: workdir '$WORKDIR' does not exist" >&2; exit 2; }

# Use gVisor when available; it intercepts syscalls in userspace, shrinking
# the host kernel's attack surface. Optional by design — see the spec.
RUNTIME_ARGS=()
if command -v runsc >/dev/null 2>&1; then
  RUNTIME_ARGS=(--runtime runsc)
fi

exec podman run --rm \
  "${RUNTIME_ARGS[@]}" \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --read-only \
  --tmpfs "/tmp:rw,noexec,nosuid,size=${TMPFS_SIZE}" \
  --user "$USERSPEC" \
  --pids-limit "$PIDS" \
  --memory "$MEMORY" \
  --cpus "$CPUS" \
  --network "$NETWORK" \
  -v "${WORKDIR}:/work:${MOUNT_MODE},U" \
  -w /work \
  "$@"
```

- [ ] **Step 3: Make it executable, check syntax, restow**

```bash
chmod +x /home/kettle/dotfiles/bin/sbx
bash -n /home/kettle/dotfiles/bin/sbx && echo "syntax OK"
stow -R -d /home/kettle/dotfiles -t /home/kettle .
test -x /home/kettle/bin/sbx && echo "stowed OK"
```

- [ ] **Step 4: Verify each restriction by hand**

```bash
sbx run alpine id                                     # -> uid=65534
sbx run alpine wget -q -T3 -O- https://example.com    # -> fails, no network
sbx run --net alpine true; echo "net opt-in: $?"      # -> 0
sbx run alpine touch /work/probe                      # -> fails, workdir ro
sbx run alpine touch /probe                           # -> fails, rootfs ro
sbx run alpine sh -c 'echo ok > /tmp/x && cat /tmp/x' # -> ok, tmpfs writable
sbx run --rw alpine touch /work/probe                 # -> succeeds
rm -f probe
```

- [ ] **Step 5: Run the harness section**

```bash
/home/kettle/dotfiles/bin/container-sandbox-verify 2>&1 | grep -A7 "sbx sandbox profile"
```

Expected: every line in that section PASS.

- [ ] **Step 6: Commit**

```bash
git -C /home/kettle/dotfiles add bin/sbx
git -C /home/kettle/dotfiles commit -m "feat(containers): add sbx hardened sandbox launcher

Runs untrusted code with all capabilities dropped, no-new-privileges, a
read-only rootfs and workdir, a noexec tmpfs, no network, and bounded
CPU/memory/PIDs. Selects the gVisor runtime automatically when present.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Guardrails, cleanup, and full verification

**Files:**
- Modify: `.claude/settings.json`
- Create: `bin/container-provision`
- Delete: `install_docker.sh`
- Modify: system — remove `/etc/docker`

**Interfaces:**
- Consumes: every prior task.
- Produces: a green `container-sandbox-verify` run.

- [ ] **Step 1: Add the deny rules**

In `.claude/settings.json`, add these to `permissions.deny`. They are a speed bump for a confused agent, **not** the security boundary — the user namespace is:

```json
"Bash(sudo docker:*)",
"Bash(sudo podman:*)",
"Bash(usermod -aG docker:*)",
"Bash(gpasswd -a * docker:*)",
"Bash(podman run * -v /:*)",
"Bash(docker run * -v /:*)",
"Bash(podman run * -v $HOME:*)",
"Bash(docker run * -v $HOME:*)"
```

- [ ] **Step 2: Validate the JSON**

```bash
python3 -m json.tool /home/kettle/dotfiles/.claude/settings.json >/dev/null && echo "valid JSON"
```

- [ ] **Step 3: Restore kept volume data**

For each tarball produced in Task 1:

```bash
for tb in /home/kettle/docker-migration/volumes/*.tar.gz; do
  [ -e "$tb" ] || continue
  vol="$(basename "$tb" .tar.gz)"
  echo "restoring $vol"
  podman volume create "$vol"
  podman run --rm -v "$vol":/to -v /home/kettle/docker-migration/volumes:/from:ro \
    alpine tar xzf "/from/$(basename "$tb")" -C /to
done
podman volume ls
```

- [ ] **Step 4: Bring up one real compose project end-to-end**

```bash
docker compose -f /home/kettle/git_repos/hookshot/docker-compose.yml up -d
docker compose -f /home/kettle/git_repos/hookshot/docker-compose.yml ps
docker compose -f /home/kettle/git_repos/hookshot/docker-compose.yml down
```

Expected: services start and stop cleanly. If a service binds a low port, this also exercises Task 5's sysctl.

- [ ] **Step 5: Remove the dead Docker config**

```bash
sudo rm -rf /etc/docker
ls /etc/docker 2>&1
```

Expected: `No such file or directory`. The backup at `/home/kettle/docker-migration/etc-docker-backup` is what `container-rollback` restores from — **do not delete it.**

- [ ] **Step 6: Delete the stale installer**

```bash
git -C /home/kettle/dotfiles rm install_docker.sh
```

It is an Ubuntu/apt script for a different machine; provisioning now lives in the spec and `container-rollback`.

- [ ] **Step 7: Write the provisioning script**

The spec requires Phase 1 be reproducible on another machine. Create `bin/container-provision`, capturing the host-level steps now that they are known-good. It is idempotent and safe to re-run; `~/.config/containers` comes from stow, not from here:

```bash
#!/usr/bin/env bash
# container-provision — reproduce the rootless podman host setup on a new machine.
# Idempotent. Dotfiles supply ~/.config/containers via stow; this covers the
# host-level pieces only.
# Spec: docs/superpowers/specs/2026-09-13-rootless-container-sandbox-design.md
set -euo pipefail

USER_NAME="${SUDO_USER:-$USER}"

echo "==> stopping any root Docker daemon"
sudo systemctl disable --now docker.socket docker.service 2>/dev/null || true

echo "==> installing the podman stack"
sudo pacman -S --needed podman podman-docker podman-compose netavark aardvark-dns passt crun

echo "==> subuid/subgid for $USER_NAME"
grep -q "^${USER_NAME}:" /etc/subuid || echo "${USER_NAME}:100000:65536" | sudo tee -a /etc/subuid
grep -q "^${USER_NAME}:" /etc/subgid || echo "${USER_NAME}:100000:65536" | sudo tee -a /etc/subgid

echo "==> migrating registry CAs, if Docker left any"
if [[ -d /etc/docker/certs.d ]]; then
  sudo mkdir -p /etc/containers/certs.d
  sudo cp -a /etc/docker/certs.d/. /etc/containers/certs.d/
fi

echo "==> permitting unprivileged low ports"
echo 'net.ipv4.ip_unprivileged_port_start=0' | sudo tee /etc/sysctl.d/99-rootless-ports.conf >/dev/null
sudo sysctl --system >/dev/null

echo "==> linger and user socket"
sudo loginctl enable-linger "$USER_NAME"
systemctl --user enable --now podman.socket

echo "==> done. Verify with: container-sandbox-verify"
```

Check it:

```bash
chmod +x /home/kettle/dotfiles/bin/container-provision
bash -n /home/kettle/dotfiles/bin/container-provision && echo "syntax OK"
```

- [ ] **Step 8: Run the full harness**

```bash
/home/kettle/dotfiles/bin/container-sandbox-verify; echo "exit=$?"
```

Expected: every assertion PASS, `exit=0`. **Do not declare completion on a partial pass** — investigate and fix any FAIL first, and report the actual output rather than summarizing it.

- [ ] **Step 9: Commit**

```bash
git -C /home/kettle/dotfiles add .claude/settings.json bin/container-provision install_docker.sh
git -C /home/kettle/dotfiles commit -m "feat(claude): deny container escape-shaped commands; drop stale installer

Blocks sudo docker/podman, docker-group self-addition, and bind mounts of
/ or \$HOME. Defense in depth only; the user namespace is the real boundary.
Also removes the Ubuntu docker installer superseded by this migration.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 10: Merge the branch**

```bash
git -C /home/kettle/dotfiles checkout main
git -C /home/kettle/dotfiles merge --no-ff rootless-podman
```

---

## Post-implementation

Once the harness has been green for a week, two optional follow-ups from the spec:

1. **gVisor.** `yay -S gvisor-git`, then confirm `sbx` picks up `runsc` automatically (it probes `command -v runsc`). Expect syscall-bound workloads to run 2-3x slower.
2. **Discard the migration scratch.** `rm -rf /home/kettle/docker-migration` once confident, accepting that `container-rollback` stops working at that point.

# Rootless container execution with podman

Date: 2026-09-13
Status: Approved, pending implementation plan

## Problem

Docker on this workstation runs as a root daemon. Using it requires `sudo`, and the
usual remedy — joining the `docker` group — is equivalent to granting passwordless
root, since `docker run -v /:/host` hands out the entire filesystem. Neither option is
acceptable for a machine where AI agents launch containers.

Two distinct risks were identified:

1. **Agent escapes to host.** An agent with container access owns the machine.
2. **Untrusted code inside the container.** Code the agent writes runs with more
   privilege, resources, and network reach than it needs.

## Goals

- `docker <anything>` works as the unprivileged user, without `sudo` and without
  `docker` group membership.
- Container root maps to an unprivileged host UID, structurally rather than by policy.
- Agents have a locked-down path for running untrusted code.
- Interactive use stays behaviorally familiar, with the documented exception of
  buildx (see Known regressions).

## Non-goals

- Defending against a malicious *user* (the human). The boundary protects the host
  from containers, not the host from its owner.
- Protecting `$HOME` from a container the user explicitly bind-mounts it into.
- Multi-tenancy or any network-reachable container service.

## Current state (verified 2026-09-13)

| Fact | Value |
|---|---|
| OS / kernel | Arch (omarchy), 7.1.9-arch1-2 |
| Docker | CE 29.7.2, root daemon, `docker.socket` enabled+active, `docker.service` disabled |
| Group membership | `kettle` is **not** in `docker`; `docker ps` fails today |
| subuid / subgid | `kettle:100000:65536` — already allocated |
| Unprivileged userns | enabled (`kernel.unprivileged_userns_clone=1`) |
| `newuidmap`/`newgidmap` | present, `cap_setuid=ep` / `cap_setgid=ep` |
| Idle daemon cost | dockerd 332 MB + containerd 194 MB + 94 MB RSS |
| Private registry CAs | `/etc/docker/certs.d/{gitlab,registry.gitlab}.<internal-domain>/ca.crt` |
| `docker build` | aliased to `docker buildx build` (buildx 0.36.1) |
| cgroup delegation | v2, `cpu memory pids` delegated to user slice |
| Linger | `Linger=no` |
| `ip_unprivileged_port_start` | 1024 |
| Podman stack | all in official `extra`: podman 6.1.0, podman-docker, podman-compose, netavark, aardvark-dns, passt, crun, fuse-overlayfs |
| Rootless Docker | **not viable cleanly** — Arch's `docker` package ships no `dockerd-rootless-setuptool.sh` |
| gVisor | AUR only; `gvisor-bin` flagged out-of-date 2026-04-29, `gvisor-git` current |

## Decision

Replace Docker with **rootless podman**, using `podman-docker` so `/usr/bin/docker`
remains the entry point.

Approach chosen over two alternatives:

- *Repoint the Docker CLI at podman's socket via `DOCKER_HOST`* — rejected because
  `docker build` is aliased to buildx, and podman's API exposes no BuildKit endpoints,
  so builds break outright. Podman-only flags (`--userns=keep-id`, `:U`) are also
  unreachable through the Docker CLI.
- *Rootless Docker from AUR* — rejected: puts a security-critical component on AUR and
  retains a daemon.

Podman and gVisor are **not** alternatives to one another. Podman is the engine layer;
gVisor (`runsc`) is an OCI runtime. Rootless podman addresses risk 1; `runsc` addresses
risk 2 and is deferred to a later phase.

## Known regressions

Accepted as part of this decision:

| Lost | Mitigation |
|---|---|
| `docker buildx` / BuildKit | `podman build` for ordinary builds. No mitigation for buildx-specific features (multi-platform emulation, cache exporters) |
| Docker Swarm, volume and network plugins | None. Not in use on this machine |
| `ufw-docker` | Obsolete under rootless; ufw governs published ports correctly on its own |
| `--gpus` (NVIDIA RTX 4090 present) | Out of scope by requirement; podman uses CDI if ever needed |

## Security model

```
container UID 0    ->  host UID 1000 (kettle)
container UID 1..N ->  host UID 100000..165535
```

A container believing itself root is, to the kernel, the unprivileged user or less.
Root-owned host paths are unreadable even through `-v /:/host`. No root daemon exists
and no group membership grants root. This holds under `--privileged`, because
privileged-within-a-userns cannot exceed that userns.

**Residual risk:** a container given a writable bind mount of `$HOME` can destroy the
user's own files as the user. This is addressed by policy (§4), not by the kernel.

## Phase 1 — System changes (require sudo, one-time)

1. `systemctl disable --now docker.socket docker.service` before any package removal.
2. `pacman -S podman podman-docker podman-compose netavark aardvark-dns passt crun`.
   This removes `docker` and `ufw-docker` (`podman-docker` Conflicts With `docker`).
   `docker-compose` and `lazydocker` have no hard dependency on `docker` and survive.
3. Migrate `/etc/docker/certs.d/` -> `/etc/containers/certs.d/`, preserving both
   `<your-registry-host-1>` and `<your-registry-host-2>` CA files. Podman does not read
   Docker's path; skipping this breaks private registry pulls.
4. `loginctl enable-linger kettle` so the podman user socket and any `--restart`
   containers survive logout.
5. `/etc/sysctl.d/99-rootless-ports.conf` with `net.ipv4.ip_unprivileged_port_start=80`,
   satisfying the ports-below-1024 requirement. 80 rather than 0: it still allows :80
   and :443, while leaving :22 and :53 protected from unprivileged squatting.
   **Accepted tradeoff:** any unprivileged process on the box may then bind ports at or
   above :80, not only podman.
6. Remove `/etc/docker/daemon.json` and `.pacnew` — dead config that would mislead.

`ufw-docker`'s removal is an improvement, not a regression: root Docker bypasses ufw's
INPUT chain, which is why that tool exists. Rootless published ports are ordinary user
sockets and obey ufw normally.

## Phase 2 — Dotfiles configuration (stowed)

- `.config/containers/registries.conf` — `unqualified-search-registries = ["docker.io"]`.
  Without it podman refuses bare image names like `alpine`.
- `.config/containers/containers.conf` — deliberately near-stock: `runtime = "crun"`,
  sane log and pids limits. Aggressive hardening is **not** placed here; global
  `--read-only` or `keep-id` defaults break stock images and would violate the
  "works like normal docker" requirement.
- `.config/zsh/exports.zsh` — add
  `DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock` for Docker-API clients
  (lazydocker, testcontainers, compose); drop the stale `$HOME/.docker/bin` PATH entry.
- `systemctl --user enable --now podman.socket`.
- Delete `install_docker.sh` — a stale Ubuntu/apt script for a different machine.
- Add a provisioning script covering Phase 1 so the setup is reproducible.

### Bind-mount ownership

Files created by container **root** land owned by the user — the common case is
painless. Files created by a non-root UID inside the container (e.g. `node` at UID 1000
-> host 101000) appear alien and resist deletion. Remedies: `:U` on the mount,
`--userns=keep-id`, or `podman unshare rm -rf`. Availability of these is why this
approach was chosen over the `DOCKER_HOST` variant.

## Phase 3 — `bin/sbx`, the sandbox profile

`dotfiles/bin/` is already stowed to `~/bin` and on PATH. `sbx` is a new wrapper
providing the hardening rootless does not itself supply, so agents need not remember
the flag set:

- `--cap-drop=ALL`, `--security-opt=no-new-privileges`
- `--read-only` plus a `noexec,nosuid` tmpfs at `/tmp`
- non-root `--user`
- `--pids-limit`, `--memory`, `--cpus`
- `--network none` by default, opt in explicitly
- no bind mounts except one explicit workdir, read-only by default
- `--runtime runsc` selected automatically when gVisor is installed

Interactive `docker` stays stock; `sbx` is the path agents are directed to. Two
commands, two trust levels.

## Phase 4 — Guardrails (defense in depth)

`.claude/settings.json` deny rules for the moves that climb back out: `sudo docker`,
`sudo podman`, `usermod -aG docker`, and podman invocations mounting `/` or `$HOME`
writable. These are a speed bump for a confused agent. The control is the user
namespace; these rules are not load-bearing and must not be described as such.

## Verification

A script asserting properties rather than assuming them:

- `docker run --rm alpine id` reports uid 0 inside.
- `/proc/self/uid_map` inside a container shows the 100000 mapping.
- Reading `/etc/shadow` through `-v /:/host:ro` fails.
- Writing to host root through `-v /:/host` fails, including under `--privileged`.
- `ps -u root` contains no `dockerd`.
- `docker compose up` succeeds on a sample stack.
- Binding host port 80 succeeds.
- A pull from `<your-registry-host-2>` succeeds.
- `podman info` reports the native `overlay` driver, not `fuse-overlayfs` (kernel
  7.1.9 supports unprivileged overlayfs).
- `sbx run` denies network and refuses a write to its read-only workdir.

## Rollback

Reinstall `docker` and `ufw-docker`, restore `/etc/docker/certs.d/` and
`daemon.json`, re-enable `docker.socket`, remove `DOCKER_HOST` and the sysctl file.
To be documented alongside the provisioning script.

## Deferred

- **gVisor.** Add `gvisor-git` and wire `--runtime runsc` into `sbx` for untrusted
  workloads. Deferred because it is AUR-only and carries real cost: syscall-bound
  workloads commonly run 2-3x slower, I/O passes through a gofer, startup is slower.
  It belongs as opt-in per container, never a global default.
- **buildx / BuildKit.** Lost with the swap. `podman build` covers ordinary builds;
  revisit only if a concrete need appears.

## Expected resource impact

Removing the root daemon reclaims roughly 620 MB resident at idle. Podman is
daemonless, adding about 1-3 MB of `conmon` per running container. `crun` starts faster
and is lighter than `runc`. The one cost is userspace networking via `passt`, whose
throughput is below a kernel bridge — immaterial for local development.

# Podman, WSL, and Docker Desktop Extension

## Using Podman

Podman is a daemonless container engine for developing, managing, and running OCI Containers.

### Basic Commands

```bash
podman run -d --name openwebui -p 3000:8080 -v open-webui:/app/backend/data ghcr.io/open-webui/open-webui:main
```

List running containers:

```bash
podman ps
```

### Networking with Podman

`slirp4netns` is being deprecated and will be removed in Podman 6. The modern successor is **pasta**, which is the default in Podman 5.0+.

### Accessing the Host (Local Services)

Use the special DNS name `host.containers.internal` to point to your computer.

**Modern Approach (Pasta - Default in Podman 5+):** No special flags needed.

**Legacy Approach (Slirp4netns):** For older versions of Podman:

```bash
podman run -d --network=slirp4netns:allow_host_loopback=true --name openwebui -p 3000:8080 -v open-webui:/app/backend/data ghcr.io/open-webui/open-webui:main
```

### Connection Configuration

In Open WebUI, navigate to **Settings > Admin Settings > Connections** and set your Ollama API connection to: `http://host.containers.internal:11434`

### Uninstall

```bash
podman rm -f openwebui
podman rmi ghcr.io/open-webui/open-webui:main    # optional
podman volume rm open-webui                        # optional, deletes all data
```

## Podman Kube Play

Podman supports Kubernetes-like syntax for deploying resources such as pods and volumes without a full Kubernetes cluster.

### Example `play.yaml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: open-webui
spec:
  containers:
    - name: container
      image: ghcr.io/open-webui/open-webui:main
      ports:
        - name: http
          containerPort: 8080
          hostPort: 3000
      volumeMounts:
        - mountPath: /app/backend/data
          name: data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName:  open-webui-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: open-webui-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

### Starting

```bash
podman kube play ./play.yaml
```

### GPU Support

Replace the image with `ghcr.io/open-webui/open-webui:cuda` and add GPU resources:

```yaml
resources:
  limits:
    nvidia.com/gpu=all: 1
```

You will need the Container Device Interface (CDI) for the GPU installed in your Podman Machine. See [Podman GPU container access](https://podman-desktop.io/docs/podman/gpu).

## Podman Quadlets (systemd)

Manage containers as native systemd services. Create `~/.config/containers/systemd/open-webui.container` with `[Container]` section setting `Image`, `ContainerName=open-webui`, `PublishPort=3000:8080`, `Volume=open-webui:/app/backend/data`, `AddHost=host.containers.internal:host-gateway`. Then:

```bash
systemctl --user daemon-reload && systemctl --user start open-webui
```

Update: `podman pull ghcr.io/open-webui/open-webui:main` then restart the service.

## Docker with WSL (Windows Subsystem for Linux)

1. Install WSL: follow [Microsoft's documentation](https://learn.microsoft.com/en-us/windows/wsl/install)
2. Install Docker Desktop from docker.com, select "WSL 2" backend
3. Go to **Settings > Resources > WSL Integration**, enable your default distro
4. From WSL terminal: `docker run -d -p 3000:8080 -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main`

Always run `docker` from WSL terminal (not PowerShell). Ensure volume mount paths are accessible from WSL.

## Docker Desktop Extension

Docker released an Open WebUI extension using Docker Model Runner for inference. See the [blog post](https://www.docker.com/blog/open-webui-docker-desktop-model-runner/). Not officially supported; designed for single local user only. Issues: [extension GitHub](https://github.com/rw4lll/open-webui-docker-extension).

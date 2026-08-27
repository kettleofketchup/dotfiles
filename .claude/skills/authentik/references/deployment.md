# Authentik Kubernetes Deployment

## Helm Chart

```
Repo: https://charts.goauthentik.io
Chart: authentik/authentik
ArtifactHub: https://artifacthub.io/packages/helm/goauthentik/authentik
```

## Minimal Values

```yaml
authentik:
  secret_key: "<generate-with-openssl-rand-base64-32>"
  postgresql:
    password: "<secure-password>"

server:
  ingress:
    enabled: false  # use Traefik IngressRoute instead

postgresql:
  enabled: true
  auth:
    password: "<same-password-as-above>"

redis:
  enabled: true
```

**Generate secret key:** `openssl rand -base64 32`

Set the external base URL — optional in 2026.8, **required from 2026.11**:

```yaml
authentik:
  web:
    base_url: "https://auth.example.com"   # AUTHENTIK_WEB__BASE_URL
```

## Production Values (Traefik + ArgoCD)

```yaml
authentik:
  secret_key: "<secret>"
  postgresql:
    password: "<password>"

server:
  replicas: 1
  metrics:
    enabled: true

worker:
  replicas: 1

postgresql:
  enabled: true
  auth:
    password: "<password>"
  primary:
    persistence:
      enabled: true
      size: 8Gi

redis:
  enabled: true
  master:
    persistence:
      enabled: true
      size: 2Gi

# Native blueprint ConfigMap mounting (no manual volumes needed)
# Only keys ending in .yaml are discovered
blueprints:
  configMaps:
    - authentik-blueprints-core
    - authentik-blueprints-apps
    - authentik-blueprints-proxy
```

## ArgoCD Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: authentik
  namespace: argocd
spec:
  project: default
  sources:
    - repoURL: https://charts.goauthentik.io
      chart: authentik
      targetRevision: "2026.*"
      helm:
        valueFiles:
          - $values/apps/authentik/values.yaml
    - repoURL: git@github.com:<user>/<repo>.git
      targetRevision: HEAD
      ref: values
  destination:
    server: https://kubernetes.default.svc
    namespace: authentik
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - ServerSideApply=true
```

## Traefik IngressRoute

```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: authentik
  namespace: authentik
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`auth.example.com`)
      kind: Rule
      services:
        - name: authentik-server
          port: 80
```

## Upgrading

```bash
helm repo update
helm upgrade authentik authentik/authentik -f values.yaml --version ^2026.8
```

- **Outpost versions must match the server version.** Upgrade standalone
  outposts at the same time; embedded outposts follow the server automatically.
- **Do not skip release lines.** Lifecycle tooling in 2026.8 blocks unsupported
  version skips — step through `2026.2 → 2026.5 → 2026.8`.
- Release cadence is three months as of 2026.2.

For the 2026.x breaking changes that affect blueprints and configuration
(`meta_hide`, `user.groups`, listen defaults, `CONN_OPTIONS`, `hash_password`),
see [releases-2026.md](releases-2026.md).

## Post-Install

1. Navigate to `https://auth.example.com/if/flow/initial-setup/`
2. Create admin account
3. Built-in PostgreSQL is for testing only; use CloudNativePG or Zalando operator for production

## Environment Variables

For the complete environment variable reference, see
[configuration-core.md](configuration-core.md) (core, PostgreSQL, cache, email,
listen addresses, web/worker tuning) and
[configuration-storage.md](configuration-storage.md) (storage, outposts,
security, airgapped settings).

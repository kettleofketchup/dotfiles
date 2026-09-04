# ArgoCD Troubleshooting

## Application Sync Issues

### OutOfSync After Successful Sync

**Cause:** Field differences between desired and live state.

```yaml
spec:
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas
        - /metadata/annotations/kubectl.kubernetes.io~1last-applied-configuration
```

### StatefulSet volumeClaimTemplates Perpetual OutOfSync

**Cause:** Kubernetes strips `apiVersion`/`kind` from `volumeClaimTemplates` entries.

**Solution — Global (recommended):**
```yaml
configs:
  cm:
    resource.customizations.ignoreDifferences.apps_StatefulSet: |
      jqPathExpressions:
        - .spec.volumeClaimTemplates[]?.apiVersion
        - .spec.volumeClaimTemplates[]?.kind
```

**Solution — Per-Application:**
```yaml
spec:
  ignoreDifferences:
    - group: apps
      kind: StatefulSet
      jqPathExpressions:
        - .spec.volumeClaimTemplates[]?.apiVersion
        - .spec.volumeClaimTemplates[]?.kind
```

### Stuck in Progressing

Common causes: Ingress controller not updating status, StatefulSet waiting for PVCs, pods failing to start.

```bash
argocd app get myapp
kubectl describe deployment -n myapp myapp
kubectl get events -n myapp
```

### Sync Failed

```bash
argocd app sync myapp --dry-run
kubectl logs -n argocd deployment/argocd-repo-server
kubectl logs -n argocd deployment/argocd-application-controller
```

## Authentication Issues

### Forgot Admin Password

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Reset password
argocd account bcrypt --password 'newpassword'
kubectl -n argocd patch secret argocd-secret \
  -p '{"stringData": {"admin.password": "$2a$10$...", "admin.passwordMtime": "'$(date +%FT%T%Z)'"}}'
```

### Disable Admin Account

```yaml
# argocd-cm ConfigMap
data:
  admin.enabled: "false"
```

## Repository Issues

### Permission Denied (SSH)

1. Verify: `ssh -T git@github.com`
2. Permissions: `chmod 600 ~/.ssh/id_rsa`
3. Known hosts: `ssh-keyscan github.com | argocd cert add-ssh --batch`

### Certificate Errors (HTTPS)

```bash
argocd cert add-tls git.example.com --from ca.pem
```

## CLI Issues

### "transport is closing" Error

**Cause:** Proxy incompatible with HTTP/2

```bash
argocd app list --grpc-web
export ARGOCD_OPTS='--grpc-web'
```

## Secret Bootstrap-Job Migrations

### A create-once seeder Job is necessary but NOT sufficient

The house pattern for a Secret that must survive syncs is a PreSync bootstrap
Job that creates it only if absent:

```bash
if kubectl -n "$NS" get secret <name> >/dev/null 2>&1; then
  echo "<name> exists; leaving it untouched"; exit 0
fi
```

That is the right pattern, and it still loses the value when you MIGRATE to it
from a chart-rendered Secret. Removing the Secret from the chart leaves it in
the Application's `.status.resources` with `requiresPruning: true`, so:

1. PreSync runs first, sees the Secret present, logs `leaving it untouched`.
2. The Sync phase then prunes it.

The log reads like a clean no-op migration while the value is destroyed. Treat
every chart-Secret → bootstrap-Job migration as **a rotation**: announce it and
restart consumers, or carry the value through one sync in an `override` value
before removing the template.

### Amplification: an operator that also owns the Secret

If a controller reconciles the same Secret, the prune becomes a spin instead of
a one-time loss — ArgoCD prunes, the operator recreates and fires whatever
Job it runs on a password change, ArgoCD prunes again.

Seen on pulp: `pulp-reset-admin-password` Jobs created every ~2s, reaching
**6,900 Jobs / 5,200 Pending pods** against a node cap of 110 pods.

The spiral is self-reinforcing, and that is what makes it an outage rather than
noise: once pending pods fill the node, the reset Jobs can no longer schedule,
so the operator never observes one completing and keeps creating more. Every
other workload on the node stops scheduling too — unrelated apps fail to sync
with `0/1 nodes are available: 1 Too many pods`.

**Break it in this order** (the reverse does not work):

```bash
# 1. Delete the backlog FIRST -- this is what lets the Jobs schedule again.
kubectl -n <ns> delete jobs -l <label> --cascade=background --wait=false

# 2. Confirm the controller settles: new Jobs should reach Complete and space
#    out. Scaling the operator to 0 does NOT hold -- selfHeal revives it, and
#    patching the Application does not hold either when an ApplicationSet owns
#    it (both revert within minutes).
kubectl -n <ns> get jobs --sort-by=.metadata.creationTimestamp | tail -3
```

Draining the backlog is the fix, not stopping the controller: with slots free
the Jobs complete, the controller observes success and settles by itself.

### Diagnosing "Too many pods"

A node pod cap is a shared resource, so the victim is rarely the culprit. When
an unrelated app is stuck in a PreSync hook, count pods by namespace before
investigating that app:

```bash
kubectl get pods -A --no-headers | awk '{print $1}' | sort | uniq -c | sort -rn | head
kubectl get node -o jsonpath='{.items[0].status.capacity.pods}'
```

## Resource Issues

### "Field not declared in schema"

Use server-side apply: `ServerSideApply=true` or skip validation: `Validate=false`

### Cached Manifest Error

```bash
kubectl rollout restart -n argocd deployment/argocd-repo-server
```

## Debugging Commands

```bash
argocd app get myapp
argocd app diff myapp
argocd app manifests myapp

kubectl logs -n argocd deployment/argocd-server
kubectl logs -n argocd deployment/argocd-repo-server
kubectl logs -n argocd deployment/argocd-application-controller
kubectl get events -n argocd --sort-by='.lastTimestamp'

argocd admin settings rbac can myuser get applications 'default/*'
```

See [troubleshooting/advanced.md](troubleshooting/advanced.md) for cluster connectivity, Redis issues, and performance.

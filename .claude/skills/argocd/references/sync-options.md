# ArgoCD Sync Options

## Sync Phases

Execution order: PreSync → Sync → PostSync → SyncFail

```yaml
metadata:
  annotations:
    argocd.argoproj.io/hook: PreSync  # PreSync, Sync, PostSync, SyncFail, Skip
```

## Sync Waves

Control ordering within phases. Lower waves execute first.

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "-1"  # Negative = before default (0)
```

Execution order: Phase → Wave number → Resource kind → Resource name

Default wave delay: 2 seconds (configurable via `ARGOCD_SYNC_WAVE_DELAY`)

### Example: Database Migration Before App

```yaml
# Job: wave -1 (runs first)
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/sync-wave: "-1"
spec:
  template:
    spec:
      containers:
        - name: migrate
          image: myapp:latest
          command: ["./migrate.sh"]
      restartPolicy: Never
---
# Deployment: wave 0 (runs after migration)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  annotations:
    argocd.argoproj.io/sync-wave: "0"
```

## Hook Deletion Policies

```yaml
metadata:
  annotations:
    argocd.argoproj.io/hook: PostSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
```

| Policy | Behavior |
|--------|----------|
| HookSucceeded | Delete after hook succeeds |
| HookFailed | Delete after hook fails |
| BeforeHookCreation | Delete existing before creating new |

## Sync Options (Application Level)

```yaml
spec:
  syncPolicy:
    syncOptions:
      - Validate=false           # Skip kubectl validation
      - CreateNamespace=true     # Auto-create namespace
      - PrunePropagationPolicy=foreground
      - PruneLast=true
      - Replace=true             # Use replace instead of apply
      - ServerSideApply=true     # Use server-side apply
      - ApplyOutOfSyncOnly=true  # Only sync changed resources
      - RespectIgnoreDifferences=true
      - FailOnSharedResource=true
```

## Sync Options (Resource Level)

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-options: Prune=false,Validate=false
```

| Option | Description |
|--------|-------------|
| `Prune=false` | Never delete this resource — **only while the chart still renders it**; see the caveat below |
| `Delete=false` | Keep on app deletion |
| `Validate=false` | Skip validation |
| `Replace=true` | Use kubectl replace |
| `ServerSideApply=true` | Server-side apply |

### `Prune=false` does not protect a resource the chart stopped rendering

ArgoCD decides what to prune from the Application's `.status.resources` list
carried over from the previous sync — **not** from the live object's
annotations. A resource that was rendered once and then removed from the chart
stays in that list with `requiresPruning: true`, and the next sync deletes it
even though the live object carries `Prune=false`, `IgnoreExtraneous`, and no
`argocd.argoproj.io/tracking-id`.

Stripping the tracking annotation is the commonly cited fix and **does not
work** for this reason. Verify with:

```bash
kubectl -n argocd get app <app> -o json \
  | jq '.status.resources[] | select(.requiresPruning == true)'
```

If the resource is listed there, it is going to be deleted on the next sync,
whatever its annotations say.

## Automated Sync Policy

```yaml
spec:
  syncPolicy:
    automated:
      prune: true       # Auto-delete removed resources
      selfHeal: true    # Revert manual cluster changes
      allowEmpty: false # Prevent accidental deletion of all resources
```

## Retry Policy

```yaml
spec:
  syncPolicy:
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

See [sync-options/advanced.md](sync-options/advanced.md) for selective sync, skip reconciliation, and namespace metadata.

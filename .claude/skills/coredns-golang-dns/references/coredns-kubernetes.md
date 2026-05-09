# Patching CoreDNS in Kubernetes

Default install lives in `kube-system/coredns` (Deployment + ConfigMap +
Service `kube-dns`). The ConfigMap holds the Corefile.

## Inspect Current State

```bash
kubectl -n kube-system get cm coredns -o yaml
kubectl -n kube-system get deploy coredns -o yaml
kubectl -n kube-system get svc kube-dns -o yaml
kubectl -n kube-system logs -l k8s-app=kube-dns -c coredns --tail=50
```

## Default Corefile (kubeadm/k3s)

```
.:53 {
    errors
    health { lameduck 5s }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
        pods insecure
        fallthrough in-addr.arpa ip6.arpa
        ttl 30
    }
    prometheus :9153
    forward . /etc/resolv.conf {
        max_concurrent 1000
    }
    cache 30
    loop
    reload
    loadbalance
}
```

## Pattern A — `import` Fragment (recommended)

Don't edit the default Corefile. Use the `import` plugin to pull a fragment
from a separate ConfigMap so upgrades don't clobber it.

1. Patch main Corefile to import a fragment:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    import /etc/coredns/custom/*.override
    .:53 {
      ...defaults...
      import /etc/coredns/custom/*.server
    }
```

2. Custom ConfigMap with fragments:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns-custom
  namespace: kube-system
data:
  internal.server: |
    internal.corp:53 {
      hosts {
        10.0.0.10 db.internal.corp
        10.0.0.11 cache.internal.corp
        fallthrough
      }
    }
  rewrite.override: |
    # zone-level overrides (rewrite, log, etc.)
```

3. Mount into the Deployment (additional volume):

```yaml
spec:
  template:
    spec:
      volumes:
        - name: custom
          configMap:
            name: coredns-custom
            optional: true
      containers:
        - name: coredns
          volumeMounts:
            - name: custom
              mountPath: /etc/coredns/custom
              readOnly: true
```

K3s ships this pattern out of the box — ConfigMap `coredns-custom` is
honoured by default, no Deployment patch needed.

## Pattern B — Strategic Merge Patch (Kustomize)

```yaml
# overlays/cluster/coredns-corefile-patch.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
      errors
      health { lameduck 5s }
      ready
      kubernetes cluster.local in-addr.arpa ip6.arpa {
        pods insecure
        fallthrough in-addr.arpa ip6.arpa
        ttl 30
      }
      hosts {
        10.0.0.10 db.internal.corp
        fallthrough
      }
      prometheus :9153
      forward . /etc/resolv.conf
      cache 30
      loop
      reload
      loadbalance
    }
```

```yaml
# overlays/cluster/kustomization.yaml
patches:
  - path: coredns-corefile-patch.yaml
    target:
      kind: ConfigMap
      name: coredns
      namespace: kube-system
```

## Pattern C — JSON-Patch Forward Zone

Add a single forward zone without touching the default block:

```yaml
patches:
  - target:
      kind: ConfigMap
      name: coredns
      namespace: kube-system
    patch: |-
      - op: add
        path: /data/Corefile
        value: |
          import /etc/coredns/custom/*.server
          .:53 { ...existing... }
```

(Use the `import` pattern; raw JSON-patch on Corefile string is brittle.)

## Roll the Deployment

```bash
kubectl -n kube-system rollout restart deploy/coredns
kubectl -n kube-system rollout status  deploy/coredns
```

`reload` plugin avoids restart for in-place ConfigMap edits, but a rollout
forces a clean state.

## Stub Domain / Conditional Forwarder

```
internal.corp:53 {
  forward . 10.0.0.53 10.0.0.54 {
    policy sequential
    health_check 5s
  }
  cache 30
}
```

Inside `coredns-custom.internal.server` so it survives upgrades.

## NodeLocal DNS Cache (optional)

Cluster nodes run a per-node CoreDNS cache forwarding to `kube-dns`. Patches
to `node-local-dns` ConfigMap follow the same `import` pattern; the upstream
manifest is `node-local-dns.yaml` from the kubernetes/dns repo.

## Verifying

From a debug pod:

```bash
kubectl run -it --rm dnsutils \
  --image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.7 -- \
  dig +short db.internal.corp
```

`+trace` shows the resolution path, `+tcp` switches transport, `+tries=1
+time=2` keeps it snappy.

## Distro Notes

| Distro | Caveat |
|--------|--------|
| EKS | CoreDNS is a managed addon — patch via `aws eks update-addon` `--configuration-values`, or set `resolveConflicts=PRESERVE` after manual edits |
| GKE | `kube-dns` is the default; CoreDNS only on Autopilot. Edit via `gcloud container clusters update --addons=` |
| AKS | Use ConfigMap `coredns-custom` (mirrors k3s pattern) |
| kops | `spec.kubeDNS.coreDNSImage` and `customConfigMap` |
| kubeadm | Edit ConfigMap directly; survives upgrades unless `kubeadm upgrade apply` rewrites it |
| k3s | `coredns-custom` ConfigMap honoured natively |

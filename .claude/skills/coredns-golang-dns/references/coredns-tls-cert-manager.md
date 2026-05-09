# DoT / DoH for CoreDNS via cert-manager + trust-manager

DoT (DNS-over-TLS, RFC 7858) listens on 853/tcp. DoH (RFC 8484) listens on
443 or 8443. CoreDNS supports both via `tls://` and `https://` schemes.

## Architecture

```
┌─────────┐  DoT/DoH (TLS)  ┌──────────┐  plain  ┌──────────┐
│ Clients │────────────────▶│ CoreDNS  │────────▶│ Upstream │
└─────────┘                  └──────────┘          └──────────┘
   ▲                              ▲
   │ trust CA bundle              │ leaf cert + key
   │ (trust-manager)              │ (cert-manager)
   └──────────────────────────────┘
```

cert-manager issues the **leaf certificate** for the resolver hostname.
trust-manager distributes the **issuing CA** to clients so they validate the
leaf.

## Step 1 — Issuer

For private/homelab CA, use a `ClusterIssuer` of kind `CA` backed by a
self-signed root. For public, use `ACME`. Example self-signed root +
intermediate CA pair:

```yaml
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata: { name: selfsigned-root }
spec:
  selfSigned: {}
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata: { name: internal-ca, namespace: cert-manager }
spec:
  isCA: true
  commonName: internal-root
  secretName: internal-ca-tls
  duration: 87600h
  privateKey: { algorithm: ECDSA, size: 256 }
  issuerRef: { name: selfsigned-root, kind: ClusterIssuer, group: cert-manager.io }
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata: { name: internal-ca }
spec:
  ca: { secretName: internal-ca-tls }
```

## Step 2 — Resolver Certificate

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: coredns-tls
  namespace: kube-system
spec:
  secretName: coredns-tls
  duration: 2160h          # 90d
  renewBefore: 360h        # 15d
  privateKey: { algorithm: ECDSA, size: 256, rotationPolicy: Always }
  commonName: dns.internal.corp
  dnsNames:
    - dns.internal.corp
    - dns.kube-system.svc.cluster.local
  ipAddresses:
    - 10.43.0.10            # cluster DNS service IP
  issuerRef:
    name: internal-ca
    kind: ClusterIssuer
    group: cert-manager.io
  usages: [server auth]
```

## Step 3 — Mount Cert + Configure CoreDNS

Patch the CoreDNS Deployment to mount the secret:

```yaml
spec:
  template:
    spec:
      volumes:
        - name: tls
          secret: { secretName: coredns-tls }
      containers:
        - name: coredns
          volumeMounts:
            - { name: tls, mountPath: /etc/coredns/tls, readOnly: true }
          ports:
            - { name: dns-tls, containerPort: 853, protocol: TCP }
            - { name: dns-doh, containerPort: 8443, protocol: TCP }
```

Add DoT and DoH server blocks via the `import`/custom ConfigMap pattern
(see `coredns-kubernetes.md`):

```
tls://. dns://.:853 {
  tls /etc/coredns/tls/tls.crt /etc/coredns/tls/tls.key
  forward . /etc/resolv.conf
  cache 30
  log
  errors
}

https://.:8443 {
  tls /etc/coredns/tls/tls.crt /etc/coredns/tls/tls.key
  forward . /etc/resolv.conf
  cache 30
  errors
}
```

For mTLS (clients must present cert), add the CA as a third arg to `tls`:

```
tls /etc/coredns/tls/tls.crt /etc/coredns/tls/tls.key /etc/coredns/tls/ca.crt
```

CoreDNS doesn't auto-reload TLS material — restart the pod after rotation.
Use `reloader` (stakater) annotations to roll on Secret change:

```yaml
metadata:
  annotations:
    secret.reloader.stakater.com/reload: "coredns-tls"
```

## Step 4 — Service Exposure

```yaml
apiVersion: v1
kind: Service
metadata:
  name: kube-dns-tls
  namespace: kube-system
spec:
  type: LoadBalancer
  selector: { k8s-app: kube-dns }
  ports:
    - { name: dot, port: 853,  targetPort: 853,  protocol: TCP }
    - { name: doh, port: 443,  targetPort: 8443, protocol: TCP }
```

## Step 5 — Trust Distribution (trust-manager)

Install trust-manager once per cluster, then publish the CA:

```yaml
apiVersion: trust.cert-manager.io/v1alpha1
kind: Bundle
metadata:
  name: internal-ca-bundle
spec:
  sources:
    - useDefaultCAs: false
    - secret:
        name: internal-ca-tls       # cert-manager CA secret
        key: ca.crt
  target:
    configMap:
      key: ca-bundle.crt
    namespaceSelector:
      matchLabels:
        trust.cert-manager.io/internal: "true"
    additionalFormats:
      jks:    { key: bundle.jks,    password: changeit }
      pkcs12: { key: bundle.p12,    password: changeit }
```

Result: every namespace labelled `trust.cert-manager.io/internal=true` gets
a ConfigMap `internal-ca-bundle` containing PEM (and JKS/P12) trust stores.

## Step 6 — Client Validation

Workload mounts the bundle at `/etc/ssl/certs/ca-bundle.crt`:

```yaml
volumes:
  - name: trust-bundle
    configMap: { name: internal-ca-bundle }
volumeMounts:
  - name: trust-bundle
    mountPath: /etc/ssl/certs/internal-ca.pem
    subPath: ca-bundle.crt
    readOnly: true
```

Smoke test from a pod with `kdig` (knot-dnsutils):

```bash
kdig -d @dns.internal.corp +tls-ca=/etc/ssl/certs/internal-ca.pem \
     +tls-host=dns.internal.corp example.com
```

Or DoH:

```bash
curl -fsS --cacert /etc/ssl/certs/internal-ca.pem \
  "https://dns.internal.corp/dns-query?name=example.com&type=A" \
  -H "accept: application/dns-json"
```

## Forwarding *Upstream* over DoT

The other half of the cert-manager + trust-manager picture: CoreDNS itself
acts as a DoT *client* to a trusted upstream (e.g. quad9, cloudflare, or
another internal resolver issued by the same CA).

```
. {
  forward . tls://9.9.9.9 tls://149.112.112.112 {
    tls_servername dns.quad9.net
    tls /etc/coredns/trust/ca-bundle.crt
    health_check 5s
  }
  cache 300
  loop
  errors
}
```

- `tls://` scheme switches the forward plugin to DoT (port 853).
- `tls_servername` sets SNI — must match a SAN on the upstream cert.
- `tls <ca-file>` pins the trust roots. Use the trust-manager Bundle
  ConfigMap mounted into the CoreDNS pod:

```yaml
volumes:
  - name: trust
    configMap: { name: internal-ca-bundle }
volumeMounts:
  - name: trust
    mountPath: /etc/coredns/trust
    readOnly: true
```

For mTLS upstream auth (uncommon — used between internal CoreDNS tiers):

```
forward . tls://internal-resolver.corp:853 {
  tls /etc/coredns/tls/tls.crt /etc/coredns/tls/tls.key /etc/coredns/trust/ca-bundle.crt
  tls_servername internal-resolver.corp
}
```

This is the natural pairing: cert-manager issues the **leaf** the upstream
presents, trust-manager publishes the **CA bundle** that CoreDNS uses to
verify it. Same Bundle, same trust chain, two consumers.

## Common Pitfalls

- DoT clients pin SNI to the `--tls-host` value — must match a `dnsNames`
  SAN, not just the CN. Modern verifiers ignore CN.
- IP-only resolvers need `ipAddresses` SANs in the Certificate.
- trust-manager Bundle copies don't auto-reload — workloads pick up the new
  bundle on Secret/ConfigMap remount (kubelet ~60s) or via reloader.
- DNS responses over TCP are 65 535 bytes max; large RRsets fit DoT/DoH
  fine but UDP needs EDNS0 (`bufsize 1232` is the safe MTU).

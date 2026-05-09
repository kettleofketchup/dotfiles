# DNS Troubleshooting

Practical recipes for diagnosing CoreDNS and Go-DNS issues. Read top to
bottom or jump to the symptom.

## Tools Cheat Sheet

| Tool | Strength |
|------|----------|
| `dig` | Verbose, scriptable, supports `+trace`, `+short`, `+notcp`, `+tls` |
| `kdig` | knot-dnsutils, native DoT/DoH (`+tls`, `+https`, `+tls-ca=`) |
| `dog` | Modern coloured output, JSON, DoT/DoH (`-T`, `-H`) |
| `nslookup` | Ubiquitous but limited; useful inside minimal containers |
| `getent hosts` | Tests the *full* libc resolution path (NSS, hosts, DNS) |

## Reading Response Codes

| RCODE | Meaning | Likely cause |
|-------|---------|--------------|
| 0 NOERROR | Success (may be empty answer) | Normal; or NODATA if no RR of that type |
| 2 SERVFAIL | Resolver gave up | Upstream timeout, DNSSEC failure, plugin panic |
| 3 NXDOMAIN | Name does not exist (authoritative) | Static plugin authoritative for zone, no record |
| 5 REFUSED | Server won't answer | ACL block, zone not configured, view didn't match |

`NODATA` (NOERROR + empty answer) is *not* NXDOMAIN — it means the name
exists but no record of the requested type. Common with `AAAA` queries.

## Symptom: "It works with `dig` but not from my pod"

Pod resolves through `kube-dns` Service, not your interceptor. Check:

```bash
kubectl exec -it <pod> -- cat /etc/resolv.conf
# nameserver 10.43.0.10  ← cluster DNS service IP
```

Pod DNS is set by kubelet from `dnsPolicy`. Override with explicit
`dnsConfig`:

```yaml
dnsPolicy: None
dnsConfig:
  nameservers: [10.0.0.53]
  searches: [svc.cluster.local, cluster.local]
  options:
    - { name: ndots, value: "2" }
```

## Symptom: NXDOMAIN for static records

Likely missing `Authoritative = true` on the response (Go) or missing
`fallthrough` *plus* a forwarder in CoreDNS. Inspect:

```bash
dig +noall +answer +comments @<resolver> myname
;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, ...
;;            flags: qr aa rd; QUERY: 1, ...
```

`aa` flag = authoritative. If absent on a static answer, the resolver isn't
claiming authority — clients ignore the answer.

## Symptom: SERVFAIL on every query

```bash
kubectl -n kube-system logs -l k8s-app=kube-dns -c coredns --tail=100
```

Common log patterns:
- `plugin/loop: Loop ... detected` → Corefile forwards to itself or to a
  cluster-internal IP that resolves back. Add `loop` plugin (it self-disables
  on detection) and review `forward` targets.
- `plugin/forward: no nameservers found` → `/etc/resolv.conf` empty or
  forward target unreachable.
- `i/o timeout` → Network policy / firewall.

## Symptom: Random slow queries (~5s)

Classic conntrack race on `glibc` parallel A/AAAA queries through UDP NAT.
Fixes:
- Set `options single-request-reopen` in `dnsConfig`.
- Run NodeLocal DNS Cache (per-node CoreDNS sidecar with TCP upstream).
- Increase pod `ndots` to 1 to reduce search-path retries.

## Symptom: Truncated UDP responses

```bash
dig myname TXT
;; Truncated, retrying in TCP mode.
```

UDP buffer cap (default 512). EDNS0 widens it:

```bash
dig +bufsize=4096 myname TXT
```

In Go, `m.SetEdns0(1232, false)` on outbound. CoreDNS adds EDNS0 if the
client did.

## Symptom: DoT handshake fails

```bash
kdig -d @dns.internal.corp +tls myname
;; DEBUG: handshake error: x509: certificate signed by unknown authority
```

Client doesn't trust the issuing CA. Fixes:
- Mount the trust-manager `Bundle` ConfigMap into the client.
- `+tls-ca=/etc/ssl/certs/internal-ca.pem`.
- Verify SNI matches: `+tls-host=dns.internal.corp` must match a SAN.

```bash
openssl s_client -connect dns.internal.corp:853 -servername dns.internal.corp \
  </dev/null 2>/dev/null | openssl x509 -text -noout | grep -A1 "Subject Alt"
```

## Symptom: trust-manager Bundle empty

```bash
kubectl get bundle -o wide
kubectl describe bundle internal-ca-bundle
```

Look for:
- `SyncStatus: Synced` and `ObservedGeneration` matches.
- Source Secret missing → check cert-manager `Certificate` status.
- `namespaceSelector` doesn't match — label the namespace.

## Symptom: CoreDNS ConfigMap edits get reverted

EKS, GKE, kops, kubeadm-managed clusters may rewrite the ConfigMap. Use
`coredns-custom` or `import` fragment pattern (see `coredns-kubernetes.md`)
so the default ConfigMap is untouched.

## Useful `dig` Flags

| Flag | Effect |
|------|--------|
| `+short` | One-line answers only |
| `+trace` | Iterative trace from roots |
| `+tcp` / `+notcp` | Force transport |
| `+tls +tls-host=NAME +tls-ca=FILE` | DoT |
| `+https +https-host=NAME` | DoH (modern dig only) |
| `+dnssec` | Set DO bit, request RRSIGs |
| `+bufsize=4096` | EDNS0 buffer |
| `+nsid` | Request server identity (NSID) |
| `+subnet=10.0.0.0/24` | EDNS Client Subnet |
| `+norecurse` | Don't ask for recursion (test caches/auth) |
| `+tries=1 +time=2` | Fail fast |

## Inspecting CoreDNS at Runtime

```bash
kubectl -n kube-system port-forward svc/kube-dns 9153
curl localhost:9153/metrics | grep coredns_dns_request
```

Key metrics:
- `coredns_dns_requests_total{type=}`
- `coredns_dns_response_rcode_count_total{rcode=}`
- `coredns_forward_request_duration_seconds`
- `coredns_cache_hits_total` / `coredns_cache_misses_total`
- `coredns_dns_responses_total{plugin=}`

## Go DNS Server Debugging

- Enable verbose logging: dump `r.Question`, `w.RemoteAddr()` per query.
- Validate Corefile-equivalent behavior: run two side-by-side and `dig`
  the same query; compare answers.
- Use `dnstest.NewServer(handler)` for unit tests instead of binding to a
  port.
- For race conditions on hot reload, run `go test -race`.

## Quick Sanity Pod

```bash
kubectl run -it --rm dnsutils \
  --image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.7 -- bash
# inside:
dig +short kubernetes.default
dig +short @10.0.0.53 db.internal.corp
nslookup -debug myname
```

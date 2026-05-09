# go-dns-interceptor

Reference Go DNS server demonstrating:

- Static A/AAAA/CNAME/TXT/SRV records loaded from YAML
- Conditional forwarding by zone (longest-suffix match)
- Default upstream forwarding
- Hot-reload-ready `LiveRecords` (atomic swap)

## Build & Run

```bash
go mod tidy
go build -o dnsi .
./dnsi -config resolver.yaml -listen :1053 -v
```

Test:

```bash
dig +short @127.0.0.1 -p 1053 db.internal.corp
dig +short @127.0.0.1 -p 1053 api.internal.corp AAAA
dig +short @127.0.0.1 -p 1053 example.com         # forwarded
```

## Test

```bash
go test ./...
```

The test suite uses a fake `dns.ResponseWriter` and exercises:

- A / AAAA / CNAME static lookups
- Authoritative bit
- SERVFAIL on missing record + no upstream
- Longest-suffix upstream selection

## Structure

| File | Purpose |
|------|---------|
| `main.go` | Listener setup, signal handling, `Handler.ServeDNS` |
| `records.go` | YAML config + record table builder |
| `handler_test.go` | Unit tests with fake ResponseWriter |
| `resolver.yaml` | Sample static record set |

## Extending

- Wildcards: pre-process `*.dev.example.` keys, fall back to suffix lookup.
- Response rewrite: clone `resp` after `Exchange`, mutate, then `WriteMsg`.
- Hot reload: watch `resolver.yaml` with `fsnotify`, call
  `LiveRecords.Replace` on debounced write events.
- DoT/DoH listener: add a `dns.Server{Net:"tcp-tls", TLSConfig: ...}` using
  certs from cert-manager (see `references/coredns-tls-cert-manager.md`).

## Notes

- Listens on `:1053` by default — running on `:53` requires `CAP_NET_BIND_SERVICE`
  or root. In Kubernetes use a Service to expose 53 → 1053.
- TTLs default to 60s; tune in YAML.
- Upstream timeout is 2s UDP / 3s TCP. Retries are sequential across the
  configured upstream list; once one succeeds the response is returned
  unchanged.

# CoreDNS Corefile

Corefile = list of *server blocks*. Each server block defines a zone and a
plugin chain. Plugin **execution order is compiled into the binary**
(`plugin.cfg`), not derived from the Corefile.

## Server Block Syntax

```
ZONE[:PORT] [SCHEME] {
  plugin1 [args]
  plugin2 [args] {
    sub-directive
  }
}
```

- `ZONE` — domain root. `.` matches anything.
- `:PORT` — listen port. Default 53. DoT uses 853, DoH 443/8443.
- `SCHEME` — `tls://` for DoT, `https://` for DoH, `dns://` (default) for plain.

## Minimal Examples

### Plain UDP/TCP resolver
```
. {
  forward . 1.1.1.1 9.9.9.9
  cache 300
  log
  errors
}
```

### Authoritative for one zone
```
example.internal {
  file /etc/coredns/zones/example.internal.db
  log
  errors
}
```

### Multiple zones, one block
```
internal. cluster.local. {
  hosts /etc/coredns/hosts {
    fallthrough
  }
  forward . /etc/resolv.conf
}
```

## Common Plugins

| Plugin | Purpose |
|--------|---------|
| `forward` | Proxy unmatched queries upstream (UDP/TCP/TLS/gRPC) |
| `cache` | In-memory response cache, NXDOMAIN included |
| `hosts` | Inline `/etc/hosts`-style A/AAAA/PTR records |
| `file` | RFC1035 zone file (full SOA + records) |
| `auto` | Auto-discover zone files in a directory |
| `template` | Synthesize RRs from regex captures |
| `rewrite` | Rewrite name/class/type pre- or post-resolution |
| `view` | Split-horizon: pick server block by client IP/name |
| `kubernetes` | k8s service discovery (Service / Endpoint records) |
| `health` `ready` | `/health` and `/ready` HTTP endpoints |
| `prometheus` | `/metrics` endpoint, default `:9153` |
| `errors` `log` | Stderr error / query logging |
| `loop` | Detect forward loops, refuses on detection |
| `reload` | Hot-reload Corefile on change (default 30s) |
| `loadbalance` | Round-robin RRset shuffle |
| `tls` | TLS for DoT (cert + key + optional CA) |
| `bind` | Bind to specific interface IPs |

## Plugin Order Caveat

`forward` always runs **after** `hosts`, `file`, `kubernetes`, `template`, and
`rewrite`. So this Corefile:

```
. {
  forward . 1.1.1.1
  hosts {
    10.0.0.1 db.internal
  }
}
```

…still resolves `db.internal` from `hosts`, regardless of the visual order.
Use `fallthrough` to let later plugins handle un-matched queries.

## Fallthrough

`hosts`, `kubernetes`, `file` and others stop the chain by default. Add
`fallthrough` (optionally with zone list) to continue:

```
. {
  hosts {
    10.0.0.1 db.internal
    fallthrough
  }
  forward . 1.1.1.1
}
```

Without `fallthrough`, queries for names *not* in `hosts` return NXDOMAIN
instead of being forwarded.

## Conditional Forwarding

```
. {
  forward . 1.1.1.1
}
internal.corp {
  forward . 10.0.0.53 10.0.0.54 {
    policy sequential
    health_check 5s
  }
  cache 30
}
```

`policy`: `random` (default), `round_robin`, `sequential`. `health_check`
intervals trigger active probing.

## Listen on Multiple Ports

```
.:53 .:5353 {
  forward . 1.1.1.1
}
```

## Reload

```
. {
  reload 10s
  ...
}
```

CoreDNS computes a SHA-512 of the Corefile every interval and re-execs with
the new config if it changes — no SIGHUP needed.

## Validate Corefile

```bash
coredns -conf /etc/coredns/Corefile -plugins   # list compiled-in plugins
coredns -conf /etc/coredns/Corefile -dns.port 1053 &  # smoke test
dig @127.0.0.1 -p 1053 example.com
```

## See Also

- Static records (`hosts`/`file`/`template`/`rewrite`): `coredns-static-records.md`
- Kubernetes deployment: `coredns-kubernetes.md`
- TLS (DoT/DoH): `coredns-tls-cert-manager.md`

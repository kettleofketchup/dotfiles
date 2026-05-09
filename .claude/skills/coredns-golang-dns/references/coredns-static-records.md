# Static Records in CoreDNS

Four plugins serve static-style data: `hosts`, `file`, `template`, `rewrite`.
Pick by query shape and required dynamism.

## `hosts` — Inline A/AAAA/PTR

Best for: small fixed maps, GitOps via ConfigMap, frequent edits.

```
. {
  hosts /etc/coredns/hosts internal.corp {
    10.0.0.10 db.internal.corp
    10.0.0.11 cache.internal.corp
    fd00::10  db.internal.corp
    ttl 60
    reload 5s
    fallthrough
  }
  forward . 1.1.1.1
}
```

Inline records (no external file):

```
. {
  hosts {
    10.0.0.10 db.internal.corp
    10.0.0.11 cache.internal.corp
    ttl 30
    fallthrough
  }
  forward . 1.1.1.1
}
```

Notes:
- Auto-generates PTR records for the configured zones.
- `reload <duration>` polls the file (default `5s`).
- Without `fallthrough`, non-matching names get NXDOMAIN.

## `file` — Authoritative Zone File

Best for: full RFC1035 zones, SRV, MX, TXT, NS, DNSSEC.

```
example.internal:53 {
  file /etc/coredns/zones/example.internal.db
  log
}
```

Zone file `example.internal.db`:

```zone
$ORIGIN example.internal.
$TTL 60
@       IN SOA ns1.example.internal. admin.example.internal. (
                2026050901 ; serial
                7200 3600 1209600 60 )
        IN NS    ns1.example.internal.

ns1     IN A     10.0.0.2
db      IN A     10.0.0.10
api     IN A     10.0.0.20
api     IN AAAA  fd00::20
www     IN CNAME api
_https._tcp.api IN SRV 0 5 443 api
_proxy  IN TXT   "v=interceptor target=api"
```

Bump the serial on each change — CoreDNS reloads the zone when the serial
increments (`reload` directive controls polling cadence).

## `template` — Synthesized RRs

Best for: regex-driven wildcard answers (e.g. nip.io style).

```
. {
  template IN A example.internal {
    match ^pod-(?P<oct1>\d+)-(?P<oct2>\d+)-(?P<oct3>\d+)-(?P<oct4>\d+)\.example\.internal\.$
    answer "{{ .Name }} 60 IN A {{ .Group.oct1 }}.{{ .Group.oct2 }}.{{ .Group.oct3 }}.{{ .Group.oct4 }}"
    fallthrough
  }
  forward . 1.1.1.1
}
```

`pod-10-0-0-7.example.internal` resolves to `10.0.0.7`. Useful for synthesized
service maps or wildcard captive answers.

## `rewrite` — Mutate Queries / Responses

Pre-resolution name swap:

```
. {
  rewrite name regex (.*)\.legacy\.corp {1}.modern.corp answer auto
  forward . 1.1.1.1
}
```

`answer auto` rewrites the response back so the client sees the original
name — vital for transparent rewrites.

Type rewrite (force HTTPS RR queries to A):

```
rewrite type HTTPS A
```

Response rewrite (rare, e.g. point a public hostname to internal IP):

```
rewrite stop {
  name exact metrics.public.example metrics.internal.svc.cluster.local
  answer name metrics.internal.svc.cluster.local metrics.public.example
}
```

## Choosing Between Plugins

| Need | Plugin |
|------|--------|
| 5-50 hosts, edited often | `hosts` (inline or file) |
| Full zone (SRV, MX, NS, DNSSEC) | `file` |
| Wildcard or pattern-based answers | `template` |
| Override existing public name with internal IP | `rewrite` (response) |
| Forward only specific zones to other resolvers | `forward zone.example`  |

## Order Trap

Even with `hosts` listed last in the Corefile, it runs **before** `forward`.
`file`/`hosts`/`template` always intercept matching names first. Use
`fallthrough` when the static set is partial.

## ConfigMap Mounting Pattern

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns-static
  namespace: kube-system
data:
  Corefile.fragment: |
    internal.corp:53 {
      hosts /etc/coredns/static/hosts internal.corp {
        fallthrough
      }
    }
  hosts: |
    10.0.0.10 db.internal.corp
    10.0.0.11 cache.internal.corp
```

Mount both keys into the CoreDNS pod and `import` the fragment from the main
Corefile (see `coredns-kubernetes.md`).

# DNS Interception Patterns in Go

Interception = sit on the resolution path and decide per-query whether to
answer locally, forward unchanged, or forward and rewrite the response.
Useful for development sandboxes, captive portals, lab environments, split
horizons, and test fixtures that need to redirect a name to a controlled IP.

## Architectural Patterns

### 1. Static Override + Recursive Forward
Simplest. Static map is checked first; misses go upstream verbatim.
See `go-dns-server.md` (already covered).

### 2. Conditional Forward (Stub Zones)
Different upstreams per zone — e.g. `*.corp` to internal resolvers,
everything else to public.

```go
type ZoneRouter struct {
    Zones map[string][]string // suffix → upstreams
    Default []string
    Client *dns.Client
}

func (z *ZoneRouter) pickUpstream(qname string) []string {
    name := dns.CanonicalName(qname)
    for suffix, ups := range z.Zones {
        if dns.IsSubDomain(suffix, name) {
            return ups
        }
    }
    return z.Default
}
```

`dns.IsSubDomain(parent, child)` does the suffix match correctly (label
boundary aware).

### 3. Response Rewrite (NXDOMAIN → Synthesized)
Forward upstream, then inspect/mutate the answer.

```go
resp, _, err := h.Client.Exchange(r, upstream)
if err != nil || resp == nil {
    serveServfail(w, r); return
}
if resp.Rcode == dns.RcodeNameError {
    // synthesize fallback
    resp = synthesizeA(r, net.ParseIP("10.0.0.99"))
}
// optional: rewrite specific names
for i, ans := range resp.Answer {
    if a, ok := ans.(*dns.A); ok && a.Hdr.Name == "target.example." {
        a.A = net.ParseIP("10.0.0.7")
        resp.Answer[i] = a
    }
}
_ = w.WriteMsg(resp)
```

When rewriting, **preserve the original `Id`** (`SetReply` already does
this) and clear `resp.Truncated` if the new payload fits in UDP.

### 4. Split-Horizon by Client IP
Different answers depending on who's asking.

```go
host, _, _ := net.SplitHostPort(w.RemoteAddr().String())
clientIP := net.ParseIP(host)
if internalCIDR.Contains(clientIP) {
    answer = internalRecords.Lookup(...)
} else {
    answer = externalRecords.Lookup(...)
}
```

CoreDNS's `view` plugin does the same with CEL expressions.

### 5. Transparent Proxy (Splice)
Forward the raw wire bytes upstream, write them back. Avoids any
re-marshalling cost and preserves bits the library may not recognize
(unknown RR types, EDNS options).

```go
func splice(r *dns.Msg, upstream string) (*dns.Msg, error) {
    raw, err := r.Pack()
    if err != nil { return nil, err }
    conn, err := net.DialTimeout("udp", upstream, 2*time.Second)
    if err != nil { return nil, err }
    defer conn.Close()
    _ = conn.SetDeadline(time.Now().Add(2 * time.Second))
    if _, err := conn.Write(raw); err != nil { return nil, err }
    buf := make([]byte, 4096)
    n, err := conn.Read(buf)
    if err != nil { return nil, err }
    out := new(dns.Msg)
    if err := out.Unpack(buf[:n]); err != nil { return nil, err }
    return out, nil
}
```

For TCP/DoT, reuse `dns.Client` instead — it handles framing.

### 6. Hot-Reloadable Static Map
Rebuild the map when the source file changes:

```go
type LiveRecords struct {
    mu  sync.RWMutex
    cur Records
}
func (l *LiveRecords) Lookup(n string, t uint16) []dns.RR {
    l.mu.RLock(); defer l.mu.RUnlock()
    return l.cur.Lookup(n, t)
}
func (l *LiveRecords) Replace(r Records) {
    l.mu.Lock(); l.cur = r; l.mu.Unlock()
}
```

Watch via `fsnotify` and call `Replace` on write events, with debounce.

### 7. EDNS Client Subnet (ECS) Awareness
For geo-routing, parse `OPT` records from the query:

```go
opt := r.IsEdns0()
if opt != nil {
    for _, o := range opt.Option {
        if subnet, ok := o.(*dns.EDNS0_SUBNET); ok {
            // subnet.Address, subnet.SourceNetmask
        }
    }
}
```

## Static Records Schema (lab-friendly)

```yaml
# resolver.yaml
listen: ":1053"
upstream:
  default: [1.1.1.1:53, 9.9.9.9:53]
  zones:
    internal.corp.: [10.0.0.53:53]
records:
  - { name: db.internal.corp.,    type: A,     ttl: 60, value: 10.0.0.10 }
  - { name: cache.internal.corp., type: A,     ttl: 60, value: 10.0.0.11 }
  - { name: api.internal.corp.,   type: A,     ttl: 60, value: 10.0.0.20 }
  - { name: api.internal.corp.,   type: AAAA,  ttl: 60, value: fd00::20 }
  - { name: www.internal.corp.,   type: CNAME, ttl: 60, value: api.internal.corp. }
  - { name: '*.dev.internal.corp.', type: A,   ttl: 30, value: 10.0.0.30 }
rewrites:
  # responses for these names get IP swapped before returning
  - name: legacy.corp.
    answer: 10.0.0.99
nxdomain_synth:
  enabled: false
  fallback_a: 10.0.0.99
```

## Pitfalls

- Forgetting `Authoritative = true` on synthesized answers — clients fall
  back to upstream and ignore the override.
- Letting the static map serve `dns.TypeANY` — RFC 8482 says return HINFO
  or empty; many resolvers cache this aggressively.
- Race conditions when hot-reloading: always swap whole maps, never mutate
  in place.
- Forgetting to copy the message before mutating — `dns.Msg` references
  shared `RR` slices when forwarded; clone with `r.Copy()` before edits.
- DoT/DoH listeners need the same rewrite logic; share the handler across
  all listeners, vary only `dns.Server.{Net,TLSConfig}`.
- UDP responses > 512 bytes truncate without EDNS0 — set `m.SetEdns0(1232,
  false)` on outbound and pass the client's bufsize through.

## Layered Composition (CoreDNS in front)

```
client → Go interceptor (1053) → CoreDNS (53) → public DNS
```

Send well-known names from the interceptor, forward the rest into CoreDNS
which handles cluster.local + recursion. Lets you keep CoreDNS unchanged
while iterating on overrides in Go.

## See Also

- Library: `go-dns-miekg.md`
- Static + forward starter: `go-dns-server.md`
- Working binary: `scripts/go-dns-interceptor/main.go`

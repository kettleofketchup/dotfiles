# Go DNS Server with Static Records + Upstream Forward

Build a small authoritative-then-recursive resolver: serve hard-coded records
for known names, forward everything else.

## Layout

```
go-dns-server/
├── go.mod
├── main.go            # entrypoint, signal handling
├── records.go         # static record table (load from YAML/JSON)
├── handler.go         # ServeDNS implementation
└── handler_test.go    # using dnstest
```

## Static Record Table

```go
// records.go
package main

import (
    "net"
    "github.com/miekg/dns"
)

type StaticRecord struct {
    Name  string  // FQDN with trailing dot
    Type  uint16  // dns.TypeA / TypeAAAA / TypeCNAME / TypeTXT / TypeSRV
    TTL   uint32
    A     net.IP
    Cname string
    Txt   []string
    Srv   *dns.SRV  // optional
}

type Records map[string][]StaticRecord  // key: lowercase FQDN

func (r Records) Lookup(name string, qtype uint16) []dns.RR {
    set, ok := r[dns.CanonicalName(name)]
    if !ok {
        return nil
    }
    var out []dns.RR
    for _, rec := range set {
        if rec.Type != qtype && qtype != dns.TypeANY {
            continue
        }
        out = append(out, rec.toRR())
    }
    return out
}

func (s StaticRecord) toRR() dns.RR {
    hdr := dns.RR_Header{Name: s.Name, Rrtype: s.Type,
        Class: dns.ClassINET, Ttl: s.TTL}
    switch s.Type {
    case dns.TypeA:     return &dns.A{Hdr: hdr, A: s.A}
    case dns.TypeAAAA:  return &dns.AAAA{Hdr: hdr, AAAA: s.A}
    case dns.TypeCNAME: return &dns.CNAME{Hdr: hdr, Target: dns.Fqdn(s.Cname)}
    case dns.TypeTXT:   return &dns.TXT{Hdr: hdr, Txt: s.Txt}
    case dns.TypeSRV:
        srv := *s.Srv; srv.Hdr = hdr; return &srv
    }
    return nil
}
```

## Loading from YAML

```yaml
# records.yaml
- name: db.internal.corp.
  type: A
  ttl: 60
  a: 10.0.0.10
- name: api.internal.corp.
  type: A
  ttl: 60
  a: 10.0.0.20
- name: api.internal.corp.
  type: AAAA
  ttl: 60
  a: fd00::20
- name: www.internal.corp.
  type: CNAME
  ttl: 60
  cname: api.internal.corp
- name: _https._tcp.api.internal.corp.
  type: SRV
  ttl: 60
  srv: { priority: 0, weight: 5, port: 443, target: api.internal.corp }
```

Use `gopkg.in/yaml.v3` to unmarshal into `[]StaticRecord` then index.

## Handler

```go
// handler.go
package main

import (
    "log/slog"
    "github.com/miekg/dns"
)

type Handler struct {
    Records  Records
    Upstream []string         // e.g. ["1.1.1.1:53", "9.9.9.9:53"]
    Client   *dns.Client      // shared, with timeout
    Log      *slog.Logger
}

func (h *Handler) ServeDNS(w dns.ResponseWriter, r *dns.Msg) {
    m := new(dns.Msg)
    m.SetReply(r)
    m.Compress = true

    if len(r.Question) == 0 {
        m.SetRcode(r, dns.RcodeFormatError)
        _ = w.WriteMsg(m); return
    }
    q := r.Question[0]
    h.Log.Debug("query", "name", q.Name, "type", dns.TypeToString[q.Qtype],
        "client", w.RemoteAddr().String())

    if rrs := h.Records.Lookup(q.Name, q.Qtype); len(rrs) > 0 {
        m.Authoritative = true
        m.Answer = rrs
        _ = w.WriteMsg(m); return
    }

    // forward upstream
    for _, ups := range h.Upstream {
        resp, _, err := h.Client.Exchange(r, ups)
        if err == nil {
            _ = w.WriteMsg(resp); return
        }
        h.Log.Warn("upstream failed", "ups", ups, "err", err)
    }
    m.SetRcode(r, dns.RcodeServerFailure)
    _ = w.WriteMsg(m)
}
```

## Entrypoint

```go
// main.go
package main

import (
    "context"
    "log/slog"
    "os"
    "os/signal"
    "syscall"
    "time"
    "github.com/miekg/dns"
)

func main() {
    log := slog.New(slog.NewJSONHandler(os.Stdout, nil))
    recs := mustLoadRecords("records.yaml")

    h := &Handler{
        Records:  recs,
        Upstream: []string{"1.1.1.1:53", "9.9.9.9:53"},
        Client:   &dns.Client{Net: "udp", Timeout: 2 * time.Second},
        Log:      log,
    }

    udp := &dns.Server{Addr: ":1053", Net: "udp", Handler: h}
    tcp := &dns.Server{Addr: ":1053", Net: "tcp", Handler: h}
    go func() { log.Info("udp listening"); _ = udp.ListenAndServe() }()
    go func() { log.Info("tcp listening"); _ = tcp.ListenAndServe() }()

    ctx, stop := signal.NotifyContext(context.Background(),
        syscall.SIGINT, syscall.SIGTERM)
    defer stop()
    <-ctx.Done()
    log.Info("shutting down")
    _ = udp.Shutdown(); _ = tcp.Shutdown()
}
```

## Test (dnstest)

```go
func TestStaticHit(t *testing.T) {
    recs := Records{"db.internal.corp.": {{
        Name: "db.internal.corp.", Type: dns.TypeA,
        TTL: 60, A: net.ParseIP("10.0.0.10")}}}
    h := &Handler{Records: recs, Log: slog.Default()}

    s := dnstest.NewServer(h)
    defer s.Close()

    c := &dns.Client{Net: "udp"}
    m := new(dns.Msg); m.SetQuestion("db.internal.corp.", dns.TypeA)
    resp, _, err := c.Exchange(m, s.Addr)
    if err != nil { t.Fatal(err) }
    if len(resp.Answer) != 1 { t.Fatalf("answers=%d", len(resp.Answer)) }
    a := resp.Answer[0].(*dns.A)
    if !a.A.Equal(net.ParseIP("10.0.0.10")) { t.Fatalf("got %v", a.A) }
}
```

## Tuning

- `dns.Client.UDPSize = 4096` to opt into EDNS0 from the client side.
- Use `dns.Server.ReusePort = true` when running multiple instances on the
  same port (Linux SO_REUSEPORT).
- Set `dns.Server.NotifyStartedFunc` to flag readiness for k8s probes.
- Cache: wrap `Handler` with an LRU keyed on `(qname, qtype)` honoring TTL.

## See Also

- Interception (rewrite, splice): `go-dns-interceptor.md`
- Library reference: `go-dns-miekg.md`
- Working binary: `scripts/go-dns-interceptor/main.go`

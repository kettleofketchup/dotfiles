# `github.com/miekg/dns` Quick Reference

The de-facto Go DNS library. Used by CoreDNS internally. Provides RR
parsing, message marshalling, server, client, and TSIG.

```go
import "github.com/miekg/dns"
```

## Core Types

| Type | Purpose |
|------|---------|
| `*dns.Msg` | DNS message (request or response) |
| `dns.RR` | Resource record interface |
| `dns.A`, `dns.AAAA`, `dns.CNAME`, `dns.SRV`, `dns.TXT` | Concrete RRs |
| `dns.Question` | One question section entry |
| `*dns.Server` | Embeddable server (`Net`, `Addr`, `Handler`) |
| `*dns.Client` | Outbound client with retry/timeout |
| `dns.Handler` | Interface — `ServeDNS(w ResponseWriter, r *Msg)` |
| `dns.ResponseWriter` | Write back, expose remote addr |

## Building Records

```go
rr, err := dns.NewRR("foo.example. 60 IN A 10.0.0.1")
// or programmatically:
a := &dns.A{
    Hdr: dns.RR_Header{
        Name:   "foo.example.",
        Rrtype: dns.TypeA,
        Class:  dns.ClassINET,
        Ttl:    60,
    },
    A: net.ParseIP("10.0.0.1"),
}
```

Names **must end in a dot** (FQDN). Use `dns.Fqdn(s)` to normalize.

## Building a Reply

```go
m := new(dns.Msg)
m.SetReply(r)              // copies ID, question, sets QR=1
m.Authoritative = true     // crucial: clients otherwise treat as referral
m.Answer = append(m.Answer, rr)
w.WriteMsg(m)
```

For NXDOMAIN:

```go
m := new(dns.Msg)
m.SetRcode(r, dns.RcodeNameError)
w.WriteMsg(m)
```

For SERVFAIL:

```go
m := new(dns.Msg)
m.SetRcode(r, dns.RcodeServerFailure)
w.WriteMsg(m)
```

## Minimal Server

```go
mux := dns.NewServeMux()
mux.HandleFunc(".", func(w dns.ResponseWriter, r *dns.Msg) {
    m := new(dns.Msg)
    m.SetReply(r)
    m.Authoritative = true
    if len(r.Question) > 0 && r.Question[0].Qtype == dns.TypeA {
        m.Answer = append(m.Answer, &dns.A{
            Hdr: dns.RR_Header{Name: r.Question[0].Name,
                Rrtype: dns.TypeA, Class: dns.ClassINET, Ttl: 60},
            A: net.ParseIP("10.0.0.1"),
        })
    }
    _ = w.WriteMsg(m)
})

go (&dns.Server{Addr: ":1053", Net: "udp", Handler: mux}).ListenAndServe()
go (&dns.Server{Addr: ":1053", Net: "tcp", Handler: mux}).ListenAndServe()
```

## Per-Zone Routing

```go
mux.HandleFunc("internal.corp.", internalHandler)
mux.HandleFunc(".",              defaultHandler)
```

Longest-suffix match wins. `dns.NewServeMux()` keeps a trie internally.

## Client (Forwarding)

```go
c := &dns.Client{
    Net:     "udp",
    Timeout: 2 * time.Second,
}
resp, _, err := c.Exchange(r, "1.1.1.1:53")
```

For TCP-only or large responses set `Net: "tcp"`. For DoT:

```go
c := &dns.Client{
    Net:       "tcp-tls",
    TLSConfig: &tls.Config{ServerName: "dns.quad9.net"},
    Timeout:   3 * time.Second,
}
resp, _, _ := c.Exchange(r, "9.9.9.9:853")
```

## EDNS0 (UDP > 512 bytes)

```go
m.SetEdns0(4096, false)
```

Required for DNSSEC, large TXT, and modern resolvers. Without it, big
answers truncate (`TC=1`) and clients retry over TCP.

## Question Helpers

```go
m := new(dns.Msg)
m.SetQuestion(dns.Fqdn("example.com"), dns.TypeA)
```

## RR Type Constants

| Const | RFC name |
|-------|----------|
| `dns.TypeA`, `TypeAAAA` | A / AAAA |
| `dns.TypeCNAME` | CNAME |
| `dns.TypePTR` | PTR (reverse) |
| `dns.TypeMX`, `TypeTXT` | MX / TXT |
| `dns.TypeSRV` | SRV |
| `dns.TypeNS`, `TypeSOA` | NS / SOA |
| `dns.TypeHTTPS`, `TypeSVCB` | RFC 9460 |
| `dns.TypeAXFR`, `TypeIXFR` | Zone transfer |
| `dns.TypeANY` | Wildcard query (deprecated by RFC 8482) |

## Reverse / PTR

```go
arpa, _ := dns.ReverseAddr("10.0.0.1")    // "1.0.0.10.in-addr.arpa."
```

## TSIG (signed dynamic update)

```go
c.TsigSecret = map[string]string{"keyname.": "base64=="}
m.SetTsig("keyname.", dns.HmacSHA256, 300, time.Now().Unix())
```

## Testing

`miekg/dns` ships `dns.HandleFunc` registration, but for unit tests use
`dnstest`:

```go
import "github.com/miekg/dns/dnstest"

s := dnstest.NewServer(handler)   // ephemeral port, both UDP+TCP
defer s.Close()
addr := s.Addr  // pass to client under test
```

## See Also

- Server example with static + forward: `go-dns-server.md`
- Interception patterns: `go-dns-interceptor.md`
- Working binary: `scripts/go-dns-interceptor/main.go`

// Package main is a small Go DNS server that serves static records and
// forwards everything else to upstream resolvers. Demonstrates the
// patterns described in references/go-dns-interceptor.md.
package main

import (
	"context"
	"flag"
	"log/slog"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/miekg/dns"
)

func main() {
	cfgPath := flag.String("config", "resolver.yaml", "path to config file")
	listen := flag.String("listen", "", "override listen address (e.g. :1053)")
	verbose := flag.Bool("v", false, "verbose logging")
	flag.Parse()

	level := slog.LevelInfo
	if *verbose {
		level = slog.LevelDebug
	}
	log := slog.New(slog.NewTextHandler(os.Stdout,
		&slog.HandlerOptions{Level: level}))

	cfg, err := LoadConfig(*cfgPath)
	if err != nil {
		log.Error("load config", "err", err)
		os.Exit(1)
	}
	if *listen != "" {
		cfg.Listen = *listen
	}

	live := NewLiveRecords()
	live.Replace(cfg.BuildRecords())

	h := &Handler{
		Records:  live,
		Zones:    cfg.Upstream.Zones,
		Default:  cfg.Upstream.Default,
		Client:   &dns.Client{Net: "udp", Timeout: 2 * time.Second},
		ClientTC: &dns.Client{Net: "tcp", Timeout: 3 * time.Second},
		Log:      log,
	}

	udp := &dns.Server{Addr: cfg.Listen, Net: "udp", Handler: h, UDPSize: 1232}
	tcp := &dns.Server{Addr: cfg.Listen, Net: "tcp", Handler: h}

	go func() {
		log.Info("listening", "net", "udp", "addr", cfg.Listen)
		if err := udp.ListenAndServe(); err != nil {
			log.Error("udp serve", "err", err)
			os.Exit(1)
		}
	}()
	go func() {
		log.Info("listening", "net", "tcp", "addr", cfg.Listen)
		if err := tcp.ListenAndServe(); err != nil {
			log.Error("tcp serve", "err", err)
			os.Exit(1)
		}
	}()

	ctx, stop := signal.NotifyContext(context.Background(),
		syscall.SIGINT, syscall.SIGTERM)
	defer stop()
	<-ctx.Done()
	log.Info("shutting down")
	shutdown, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = udp.ShutdownContext(shutdown)
	_ = tcp.ShutdownContext(shutdown)
}

// Handler implements dns.Handler with static-records-then-forward logic.
type Handler struct {
	Records  *LiveRecords
	Zones    map[string][]string
	Default  []string
	Client   *dns.Client
	ClientTC *dns.Client
	Log      *slog.Logger
}

func (h *Handler) ServeDNS(w dns.ResponseWriter, r *dns.Msg) {
	m := new(dns.Msg)
	m.SetReply(r)
	m.Compress = true

	if len(r.Question) == 0 {
		m.SetRcode(r, dns.RcodeFormatError)
		_ = w.WriteMsg(m)
		return
	}
	q := r.Question[0]
	h.Log.Debug("query",
		"name", q.Name,
		"type", dns.TypeToString[q.Qtype],
		"client", w.RemoteAddr().String())

	// 1. static lookup
	if rrs := h.Records.Lookup(q.Name, q.Qtype); len(rrs) > 0 {
		m.Authoritative = true
		m.Answer = rrs
		_ = w.WriteMsg(m)
		return
	}

	// 2. forward
	upstream := h.pickUpstream(q.Name)
	if len(upstream) == 0 {
		m.SetRcode(r, dns.RcodeServerFailure)
		_ = w.WriteMsg(m)
		return
	}
	for _, ups := range upstream {
		resp, _, err := h.Client.Exchange(r, ups)
		if err == nil && resp != nil {
			// Fall back to TCP if the UDP answer was truncated.
			if resp.Truncated && h.ClientTC != nil {
				if tcpResp, _, terr := h.ClientTC.Exchange(r, ups); terr == nil && tcpResp != nil {
					resp = tcpResp
				}
			}
			_ = w.WriteMsg(resp)
			return
		}
		h.Log.Warn("upstream failed", "ups", ups, "err", err)
	}
	m.SetRcode(r, dns.RcodeServerFailure)
	_ = w.WriteMsg(m)
}

func (h *Handler) pickUpstream(qname string) []string {
	name := dns.CanonicalName(qname)
	// longest-suffix wins
	var best string
	for suffix := range h.Zones {
		s := dns.CanonicalName(suffix)
		if dns.IsSubDomain(s, name) && len(s) > len(best) {
			best = s
		}
	}
	if best != "" {
		return h.Zones[best]
	}
	return h.Default
}

// LiveRecords is a thread-safe records map with hot-swap support.
type LiveRecords struct {
	mu  sync.RWMutex
	cur Records
}

func NewLiveRecords() *LiveRecords {
	return &LiveRecords{cur: Records{}}
}

func (l *LiveRecords) Lookup(name string, qtype uint16) []dns.RR {
	l.mu.RLock()
	defer l.mu.RUnlock()
	return l.cur.Lookup(name, qtype)
}

func (l *LiveRecords) Replace(r Records) {
	l.mu.Lock()
	l.cur = r
	l.mu.Unlock()
}

// canonical lowercases and FQDN-normalises.
func canonical(s string) string {
	return strings.ToLower(dns.Fqdn(s))
}

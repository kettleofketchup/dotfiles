package main

import (
	"log/slog"
	"net"
	"os"
	"testing"
	"time"

	"github.com/miekg/dns"
)

func mustHandler(t *testing.T) *Handler {
	t.Helper()
	cfg := &Config{
		Records: []RecordSpec{
			{Name: "db.internal.corp.", Type: "A", TTL: 60, Value: "10.0.0.10"},
			{Name: "api.internal.corp.", Type: "A", TTL: 60, Value: "10.0.0.20"},
			{Name: "api.internal.corp.", Type: "AAAA", TTL: 60, Value: "fd00::20"},
			{Name: "www.internal.corp.", Type: "CNAME", TTL: 60, Value: "api.internal.corp."},
		},
	}
	live := NewLiveRecords()
	live.Replace(cfg.BuildRecords())
	return &Handler{
		Records: live,
		Default: nil, // tests skip forwarding
		Client:  &dns.Client{Net: "udp", Timeout: time.Second},
		Log:     slog.New(slog.NewTextHandler(os.Stderr, nil)),
	}
}

// fakeWriter implements dns.ResponseWriter for unit tests.
type fakeWriter struct {
	msg *dns.Msg
}

func (f *fakeWriter) LocalAddr() net.Addr      { return &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)} }
func (f *fakeWriter) RemoteAddr() net.Addr     { return &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)} }
func (f *fakeWriter) WriteMsg(m *dns.Msg) error { f.msg = m; return nil }
func (f *fakeWriter) Write([]byte) (int, error) { return 0, nil }
func (f *fakeWriter) Close() error              { return nil }
func (f *fakeWriter) TsigStatus() error         { return nil }
func (f *fakeWriter) TsigTimersOnly(bool)       {}
func (f *fakeWriter) Hijack()                   {}

func query(t *testing.T, h *Handler, name string, qtype uint16) *dns.Msg {
	t.Helper()
	w := &fakeWriter{}
	r := new(dns.Msg)
	r.SetQuestion(dns.Fqdn(name), qtype)
	h.ServeDNS(w, r)
	if w.msg == nil {
		t.Fatalf("no response written")
	}
	return w.msg
}

func TestStaticA(t *testing.T) {
	h := mustHandler(t)
	resp := query(t, h, "db.internal.corp", dns.TypeA)
	if !resp.Authoritative {
		t.Errorf("expected AA bit set")
	}
	if len(resp.Answer) != 1 {
		t.Fatalf("answers=%d", len(resp.Answer))
	}
	a, ok := resp.Answer[0].(*dns.A)
	if !ok {
		t.Fatalf("not A: %T", resp.Answer[0])
	}
	if !a.A.Equal(net.ParseIP("10.0.0.10")) {
		t.Errorf("got %v", a.A)
	}
}

func TestStaticAAAA(t *testing.T) {
	h := mustHandler(t)
	resp := query(t, h, "api.internal.corp", dns.TypeAAAA)
	if len(resp.Answer) != 1 {
		t.Fatalf("answers=%d", len(resp.Answer))
	}
	aaaa, ok := resp.Answer[0].(*dns.AAAA)
	if !ok {
		t.Fatalf("not AAAA: %T", resp.Answer[0])
	}
	if !aaaa.AAAA.Equal(net.ParseIP("fd00::20")) {
		t.Errorf("got %v", aaaa.AAAA)
	}
}

func TestCNAMEReturnedForA(t *testing.T) {
	h := mustHandler(t)
	resp := query(t, h, "www.internal.corp", dns.TypeA)
	// www is a CNAME to api; we don't chase, but we should hand back the CNAME.
	if len(resp.Answer) != 1 {
		t.Fatalf("answers=%d", len(resp.Answer))
	}
	if _, ok := resp.Answer[0].(*dns.CNAME); !ok {
		t.Errorf("expected CNAME, got %T", resp.Answer[0])
	}
}

func TestUnknownNameNoUpstreamServfail(t *testing.T) {
	h := mustHandler(t)
	resp := query(t, h, "nope.internal.corp", dns.TypeA)
	if resp.Rcode != dns.RcodeServerFailure {
		t.Errorf("expected SERVFAIL, got %s", dns.RcodeToString[resp.Rcode])
	}
}

func TestPickUpstreamLongestSuffix(t *testing.T) {
	h := &Handler{
		Default: []string{"1.1.1.1:53"},
		Zones: map[string][]string{
			"corp.":          {"10.0.0.53:53"},
			"internal.corp.": {"10.0.0.54:53"},
		},
	}
	cases := map[string][]string{
		"db.internal.corp.": {"10.0.0.54:53"},
		"public.corp.":      {"10.0.0.53:53"},
		"example.com.":      {"1.1.1.1:53"},
	}
	for name, want := range cases {
		got := h.pickUpstream(name)
		if len(got) != len(want) || got[0] != want[0] {
			t.Errorf("%s: got %v want %v", name, got, want)
		}
	}
}

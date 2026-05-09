package main

import (
	"fmt"
	"net"
	"os"
	"strings"

	"github.com/miekg/dns"
	"gopkg.in/yaml.v3"
)

// Config is the on-disk YAML.
type Config struct {
	Listen   string         `yaml:"listen"`
	Upstream UpstreamConfig `yaml:"upstream"`
	Records  []RecordSpec   `yaml:"records"`
}

type UpstreamConfig struct {
	Default []string            `yaml:"default"`
	Zones   map[string][]string `yaml:"zones"`
}

type RecordSpec struct {
	Name  string  `yaml:"name"`
	Type  string  `yaml:"type"`
	TTL   uint32  `yaml:"ttl"`
	Value string  `yaml:"value"`
	Srv   *SrvVal `yaml:"srv,omitempty"`
}

type SrvVal struct {
	Priority uint16 `yaml:"priority"`
	Weight   uint16 `yaml:"weight"`
	Port     uint16 `yaml:"port"`
	Target   string `yaml:"target"`
}

// Records keys: lowercase FQDN.
type Records map[string][]dns.RR

func (r Records) Lookup(name string, qtype uint16) []dns.RR {
	set, ok := r[canonical(name)]
	if !ok {
		return nil
	}
	if qtype == dns.TypeANY {
		return set
	}
	out := make([]dns.RR, 0, len(set))
	for _, rr := range set {
		if rr.Header().Rrtype == qtype {
			out = append(out, dns.Copy(rr))
		}
	}
	// Resolve CNAME chain: if the question type is not CNAME but a CNAME
	// exists for the name, return the CNAME (clients then re-query).
	if len(out) == 0 && qtype != dns.TypeCNAME {
		for _, rr := range set {
			if c, ok := rr.(*dns.CNAME); ok {
				out = append(out, dns.Copy(c))
			}
		}
	}
	return out
}

// LoadConfig reads YAML from disk.
func LoadConfig(path string) (*Config, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var c Config
	if err := yaml.Unmarshal(b, &c); err != nil {
		return nil, err
	}
	if c.Listen == "" {
		c.Listen = ":1053"
	}
	return &c, nil
}

// BuildRecords converts the spec list into the lookup table.
func (c *Config) BuildRecords() Records {
	out := Records{}
	for _, spec := range c.Records {
		rr, err := spec.toRR()
		if err != nil {
			fmt.Fprintf(os.Stderr, "skip record %s/%s: %v\n",
				spec.Name, spec.Type, err)
			continue
		}
		key := canonical(spec.Name)
		out[key] = append(out[key], rr)
	}
	return out
}

func (s RecordSpec) toRR() (dns.RR, error) {
	name := dns.Fqdn(s.Name)
	ttl := s.TTL
	if ttl == 0 {
		ttl = 60
	}
	hdr := dns.RR_Header{
		Name: name, Class: dns.ClassINET, Ttl: ttl,
	}
	switch strings.ToUpper(s.Type) {
	case "A":
		ip := net.ParseIP(s.Value)
		if ip == nil || ip.To4() == nil {
			return nil, fmt.Errorf("invalid IPv4 %q", s.Value)
		}
		hdr.Rrtype = dns.TypeA
		return &dns.A{Hdr: hdr, A: ip.To4()}, nil
	case "AAAA":
		ip := net.ParseIP(s.Value)
		if ip == nil || ip.To4() != nil {
			return nil, fmt.Errorf("invalid IPv6 %q", s.Value)
		}
		hdr.Rrtype = dns.TypeAAAA
		return &dns.AAAA{Hdr: hdr, AAAA: ip}, nil
	case "CNAME":
		hdr.Rrtype = dns.TypeCNAME
		return &dns.CNAME{Hdr: hdr, Target: dns.Fqdn(s.Value)}, nil
	case "TXT":
		hdr.Rrtype = dns.TypeTXT
		return &dns.TXT{Hdr: hdr, Txt: []string{s.Value}}, nil
	case "SRV":
		if s.Srv == nil {
			return nil, fmt.Errorf("SRV requires srv block")
		}
		hdr.Rrtype = dns.TypeSRV
		return &dns.SRV{
			Hdr:      hdr,
			Priority: s.Srv.Priority,
			Weight:   s.Srv.Weight,
			Port:     s.Srv.Port,
			Target:   dns.Fqdn(s.Srv.Target),
		}, nil
	default:
		return nil, fmt.Errorf("unsupported type %q", s.Type)
	}
}

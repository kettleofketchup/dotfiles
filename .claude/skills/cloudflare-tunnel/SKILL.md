---
name: cloudflare-tunnel
description: Self-hosted Cloudflare Tunnel in front of Traefik on Kubernetes. Use for cloudflared Deployments and config.yaml, routing tunnel traffic to Traefik, dual-route IngressRoutes (human SSO plus machine service tokens), Access service tokens and policies, tunnel DNS records, or trusting Cloudflare headers at Traefik.
---

# Cloudflare Tunnel + Traefik

Local patterns for exposing cluster services through Cloudflare Tunnel, with
Traefik doing the per-host routing. For general Cloudflare product guidance use
the `cloudflare:*` plugin skills; this skill covers only how these pieces fit
together in a self-hosted cluster.

## Shape of the setup

TLS terminates at the Cloudflare edge. `cloudflared` runs in the cluster and
forwards everything over HTTP to Traefik port 80, and Traefik routes by host.
Exposure is opt-in: a hostname is reachable externally only once it has a tunnel
DNS record and an Access application.

## References

| file | read when |
|---|---|
| `references/tunnel-kubernetes.md` | deploying `cloudflared`: image, Deployment, `config.yaml`, credential Secret, tunnel CLI |
| `references/tunnel-traefik.md` | pointing the tunnel at Traefik |
| `references/traefik-integration.md` | dual-route IngressRoutes, `HeadersRegexp`, IP allow-lists, forwarded-header trust, JWT validation, human-only services |
| `references/access-service-tokens.md` | creating service tokens, Access apps and policies, token rotation, testing with curl |
| `references/dns-management.md` | tunnel CNAMEs, the API for DNS records, local vs external DNS, finding zone/account IDs, `just cf::*` recipes |

## Rules that are easy to get wrong

- Validate machine traffic on `Cf-Access-Jwt-Assertion` (the signed JWT), never
  on the raw `CF-Access-Client-Id` header.
- Only trust `CF-Connecting-IP` / `X-Forwarded-For` from the tunnel's source
  range; configure Traefik's forwarded-headers trust accordingly.
- Pass API tokens through environment variables (`$CF_API_TOKEN`), never inline.

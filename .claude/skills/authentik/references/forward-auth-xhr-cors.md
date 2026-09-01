# Forward-auth breaks XHR: the hourly token lapse

A production failure mode that looks like a network/timeout bug and is not. Read this
before debugging "the app randomly disconnects" or CORS errors behind authentik
forward-auth.

## Symptom

An SPA behind forward-auth works, then abruptly fails every API call. The console shows
one or both of:

```
Access to fetch at 'https://auth.example.com/application/o/authorize/?client_id=...'
(redirected from 'https://app.example.com/api/settings') from origin
'https://app.example.com' has been blocked by CORS policy: Response to preflight
request doesn't pass access control check: Redirect is not allowed for a preflight
request.

... has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is
present on the requested resource.
```

WebSocket/SSE apps surface it with no CORS text at all — just a bare `Disconnected
(check URL or network)`, because the handshake fails the same way. Reloading fixes it,
for about an hour.

## Root cause

`ProxyProvider.access_token_validity` defaults to **`hours=1`**. Expiry is **not**
silent: on the next request the outpost answers `302` to
`https://<authentikHost>/application/o/authorize/...` so the token can be re-minted.

- **Navigation:** invisible. The `user_login` stage's `session_duration` is `seconds=0`
  (until browser close), so the redirect round-trips and returns authenticated with no
  login prompt. Nobody notices. This is why the bug hides.
- **XHR / fetch / SSE / WebSocket:** fatal. The redirect crosses origin, so per the
  Fetch spec the browser applies CORS to the redirected request and bans redirects
  outright on anything preflighted. The page cannot intercept either error.

It is also **unrecoverable without a reload**: only a navigation can complete
`/outpost.goauthentik.io/callback`, so the token is never re-minted and the SPA
retry-storms against a redirect it can never follow. Blast radius scales with how
XHR-heavy an app is; an app doing its own SSO instead of forward-auth is immune.

## Diagnosis

Confirm before fixing. All three are cheap.

**1. Read the actual validity — never assume the default was overridden:**
```bash
kubectl -n authentik exec deploy/authentik-server -- ak shell -c "
from authentik.providers.proxy.models import ProxyProvider
from authentik.stages.user_login.models import UserLoginStage
for p in ProxyProvider.objects.all():
    print(p.name, p.access_token_validity, p.refresh_token_validity, p.mode)
for s in UserLoginStage.objects.all():
    print(s.name, s.session_duration, s.remember_me_offset)
"
```

**2. Find the 60-minute metronome.** Token re-mints appear as `/outpost.goauthentik.io/
callback` hits in the proxy access log. Consecutive entries ~60 min apart confirm it:
```
20:00:57 callback / 21:01:06 callback / 22:02:07 callback
```
A long gap after a burst of redirects is the wedge — it ends only at the manual reload.

**3. Prove the redirects are the failure, not a symptom.** In Traefik access logs (JSON,
via Loki), group by status and path for the affected host. A wedge shows a contiguous
block of `302` with **zero** `200` — a session-wide outage window, not path-specific:
```
| json | RequestHost="app.example.com"        # then tally DownstreamStatus by minute
```

Beware two false leads, both seen in a real investigation:
- **Aggregate ratios lie.** One endpoint showed 98% redirects vs 8% on another. That was
  the SPA's retry loop inflating the count, not path-specific behaviour. Bucket by time.
- **`DownstreamStatus: 0` is usually normal.** It means no status was ever written —
  i.e. a hijacked or long-polled connection. Check `Duration`: a tight cluster at one
  value (e.g. 125s across every sample, with `OriginDuration` matching) is the app's own
  long-poll window, not a proxy timeout.

## Fix — two halves, both required

### 1. Stop it firing hourly

```yaml
- model: authentik_providers_proxy.proxyprovider
  attrs:
    mode: forward_single
    external_host: https://app.example.com
    access_token_validity: days=7       # default hours=1 IS the bug
```

Two bounds on how long to go:

- **Ceiling:** must stay **under `refresh_token_validity`** (`days=30`). Past that
  there is no refresh token left to mint from and the user gets a full login instead.
- **Cost:** policy bindings are evaluated when the token is **minted**, not per
  request, so this value is also the **revocation lag** — remove someone from a group
  and they keep access until their current token expires. Make it a per-provider value
  with a global default, and shorten it on any provider whose group binding *is* the
  real access-control list.

The split below makes a lapse non-destructive, so length is a UX choice, not a
correctness one — set it by revocation tolerance, not by how annoying the lapse is.

### 2. Make the lapse fail cleanly

The outpost serves two forward-auth endpoints:

| Endpoint | Derives the request URL from | Unauthenticated response | Use for |
|---|---|---|---|
| `/outpost.goauthentik.io/auth/traefik` | `X-Forwarded-Proto` + `-Host` + `-Uri` | `302` to the authorize flow | document navigation |
| `/outpost.goauthentik.io/auth/nginx` | `X-Original-URL` **only** | `401`, no `Location` | XHR / SSE / WebSocket |

**`/auth/nginx` is not a drop-in for Traefik.** The 401 is exactly what you want, but the
endpoint derives the request URL from `X-Original-URL` and nothing else. Traefik's
`forwardAuth` sends `X-Forwarded-Proto/Host/Uri` and has no setting that emits
`X-Original-URL`, so aiming a bare `forwardAuth` at it hard-fails **every** request:

```
src/outpost/proxy/events.rs:24  level=error
configuration error: Outpost authentik Embedded Outpost (Provider <app>-proxy)
  failed to detect a forward URL from nginx
```

That is an HTTP **500**, and Traefik forwards a non-2xx forwardAuth response verbatim, so
the client gets the 500 with the backend never contacted. See "The 500 trap" below — it is
the single most likely way to get this wrong, and the resulting config *looks* correct.

Do not reach for `X-Original-URI` (the other spelling): it was removed deliberately as a
**security fix** in 2025.12.5 / 2026.2.3 and is now ignored.

Inject the header with a `headers` middleware and compose the two with a `chain`, so the
public middleware name stays stable and app IngressRoutes need no edit:

```yaml
# 1. the header the nginx endpoint requires
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata: {name: authentik-original-url, namespace: authentik}
spec:
  headers:
    customRequestHeaders:
      X-Original-URL: https://forward-auth.invalid/   # constant — see below
---
# 2. the real forwardAuth (not referenced directly)
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata: {name: authentik-forwardauth-api-auth, namespace: authentik}
spec:
  forwardAuth:
    address: http://authentik-server.authentik.svc.cluster.local/outpost.goauthentik.io/auth/nginx
    trustForwardHeader: true
    authResponseHeaders: [X-authentik-username, X-authentik-groups, X-authentik-email,
                          X-authentik-name, X-authentik-uid, X-authentik-jwt]
---
# 3. what routers actually reference. Order matters: the header must be on the request
#    before forwardAuth copies the headers into its auth sub-request.
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: authentik-forwardauth-api
  namespace: authentik
  annotations:
    argocd.argoproj.io/sync-options: Replace=true   # see "The type-change trap"
spec:
  chain:
    middlewares:
      - {name: authentik-original-url, namespace: authentik}
      - {name: authentik-forwardauth-api-auth, namespace: authentik}
```

**Why a constant is safe.** The provider is looked up by `X-Forwarded-Host` — which
Traefik already sends correctly per-request — *not* by the host inside `X-Original-URL`.
Verified against 2026.8.0 by the asymmetry:

```
X-Original-URL=<real app>         + X-Forwarded-Host=<no such provider> -> 404
X-Original-URL=<no such provider> + X-Forwarded-Host=<real app>         -> 401
```

`X-Original-URL` only has to exist and parse; it is never used for a redirect here because
this path answers 401 and never 302. One shared value therefore serves every app, and
`headers.customRequestHeaders` could not interpolate the real per-request URL anyway — it
sets static values only. Two caveats: if a provider sets `skip_path_regex`, that regex is
matched against this URL, so a constant will mis-evaluate it; and if authentik ever starts
keying **authorization** on `X-Original-URL`, this must become one middleware per provider.

Then select per request kind. Split on `Sec-Fetch-Mode`, **not** on a path prefix: an
app's XHR surface is rarely enumerable, and a missed path silently reintroduces the wedge
on exactly the endpoint nobody thought of.

```yaml
- match: Host(`app.example.com`) && HeaderRegexp(`Sec-Fetch-Mode`, `^(cors|same-origin|websocket)$`)
  priority: 20                       # explicit: default priority is rule LENGTH
  middlewares: [{name: authentik-forwardauth-api, namespace: authentik}]
- match: Host(`app.example.com`)
  priority: 10
  middlewares: [{name: authentik-forwardauth, namespace: authentik}]
```

`Sec-Fetch-Mode` is a forbidden header name, so page script cannot forge it — and there
is nothing to gain, since authorization is identical on both routes (same outpost, same
provider, same bindings). Only the failure mode differs. Omit `no-cors` so
`<script>`/`<img>` sub-resources keep the old behaviour; clients that send no
`Sec-Fetch-Mode` (curl, old browsers) fall through to the navigation route.

Send navigation to the **401** middleware and users get a bare 401 page instead of a
login prompt. Keep the two routes' `authResponseHeaders` lists in step.

**This route is not only "API calls".** A Vite/ESM SPA's own entry bundle is a
`<script type="module">`, which fetches with `Sec-Fetch-Mode: cors` — so the JS bundle
takes the API route while `<link rel=stylesheet>` (`no-cors`) takes the navigation one.
Break the API route and the page serves its CSS and nothing else: a blank white render
with no console auth error, which reads as a frontend bug, not an auth one.

## The 500 trap

The most likely way to get this wrong, because the config *looks* right and the failure
is silent on navigation. Symptoms:

- Every `Sec-Fetch-Mode: cors` request returns **500** on every forward-auth app at once.
- SPAs render blank; navigation and login still work perfectly.
- The app serves 200 when curled from inside its own pod.

Traefik's access log is the tell — the backend was never contacted:

```
DownstreamStatus: 500,  OriginStatus: 0,  OriginDuration: 0,  Overhead == Duration
```

Reproduce without a browser, from anywhere in-cluster:

```bash
kubectl -n <ns> exec deploy/<app> -- wget -S -qO- \
  --header="X-Forwarded-Host: <host>" --header="X-Forwarded-Proto: https" \
  --header="X-Forwarded-Uri: /" \
  http://authentik-server.authentik.svc.cluster.local/outpost.goauthentik.io/auth/nginx
# 500 + "failed to detect a forward URL from nginx"  -> X-Original-URL is missing
```

Do **not** chase this as a version regression. `/auth/nginx` has never accepted
`X-Forwarded-*` — that is precisely why `xabinapal/traefik-authentik-forward-plugin`
exists to bridge the two. Upgrading and downgrading are equally dead ends. (That plugin is
the other valid fix, and adds per-path 401/302/skip; but Traefik plugins are Yaegi source
fetched from GitHub at startup, so an **airgapped** cluster must vendor it into the image
via `experimental.localPlugins`. The chain above needs no plugin.)

## The type-change trap

Adding the chain means changing an **existing** middleware's type (`forwardAuth` →
`chain`). On any cluster that already has the old object, a merge apply keeps the stale
stanza next to the new one, and Traefik rejects the union outright:

```
ERR error="cannot create middleware: multi-types middleware not supported,
    consider declaring two different pieces of middleware instead"
    routerName=<app>-...  entryPointName=websecure
```

Traefik does not error the request — it **drops the router**, so traffic falls through to
whatever lower-priority route matches. Here that is the navigation route, so cors requests
answer `302` instead of the intended `401` and the fix looks half-applied rather than
broken. Nothing in the app's own logs mentions it.

- Check: `kubectl -n authentik get middleware <n> -o jsonpath='{.spec}'` must show exactly
  one top-level key.
- Recover: delete the object and let the GitOps controller recreate it clean.
- Prevent: `argocd.argoproj.io/sync-options: Replace=true` on the manifest (shown above),
  which replaces rather than merges so removed fields are actually pruned.

Objects **adopted** by ArgoCD after being created by something else (a bootstrap
`kubectl apply`, a Helm install) are the exposed case: with no
`kubectl.kubernetes.io/last-applied-configuration` to diff against, the apply cannot know
a field was removed. Not Middleware-specific — Middlewares just fail loudest.

## Notes

- A per-path exclusion such as `!PathPrefix(/v2/)` on a registry is this same bug,
  hand-patched for one non-browser client. Treat it as a symptom.
- Both halves matter: a longer token alone leaves an identical wedge, just rarer; the
  split alone yields a clean 401 an SPA still shows as "disconnected" unless it
  reloads on 401.

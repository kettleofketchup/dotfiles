# Hiding Applications from the Application Dashboard

## TL;DR

To hide an application's tile from the user's Application Dashboard
(named "My Applications" before 2026.5) **without** changing its policies
or removing it, set `meta_hide: true` on the application.

```yaml
- model: authentik_core.application
  identifiers:
    slug: grafana-access
  attrs:
    name: "Grafana Access"
    provider: !KeyOf grafana-proxy
    policy_engine_mode: any
    meta_hide: true
```

UI label: **Hide from Application Dashboard** (Applications → edit → the
`meta_hide` toggle). API field: `meta_hide` (boolean).

## Version note: this replaced the `blank://blank` hack in 2026.5

Before 2026.5 there was no dedicated field, and the documented workaround was
to set `meta_launch_url: "blank://blank"` — a sentinel URL that the frontend
special-cased into "don't render a tile".

2026.5 added the real `meta_hide` boolean. **Existing applications using
`blank://blank` are automatically migrated to `meta_hide: true` on upgrade**,
so nothing breaks. But blueprints are reconciled continuously: a blueprint
that still writes `meta_launch_url: "blank://blank"` will keep writing that
value back after the migration. Update the blueprints, don't rely on the
migration.

If you are stuck on a pre-2026.5 release, the old rules still apply:

> The literal value is `blank://blank` — **NOT** `blank://`. Authentik's URL
> validator rejects schemes without an authority part, so `blank://` alone
> fails the serializer and the blueprint apply errors with:
> `Serializer errors {'meta_launch_url': ['Enter a valid URL.']}`

On 2026.5+, `meta_hide` and `meta_launch_url` are independent: you can hide a
tile while keeping a real launch URL, which is useful when something else
(a bookmark, another app's link) deep-links into the app.

## When to use

The most common case is **forward-auth proxy providers that duplicate an
existing user-facing application**.

For example: Grafana has both a SAML provider (the real "Sign in with
Authentik" entry) and a forward-auth proxy provider (middleware that
gates the ingress). Both need an `authentik_core.application` row, but
the user only ever clicks the SAML one. The proxy-provider Application
exists purely to wire the provider into the embedded outpost — its tile
in the dashboard is noise.

| App pattern | Hide? | Why |
|---|---|---|
| User-facing OIDC/SAML app | **No** — `meta_launch_url: https://app.<base>` | This IS the entry the user clicks |
| Forward-auth proxy that duplicates an OIDC/SAML app | **Yes** — `meta_hide: true` | Middleware-only; the OIDC/SAML entry is the user's click target |
| Forward-auth proxy that IS the user-facing app (no separate OIDC/SAML) | **No** — `meta_launch_url: https://app.<base>` | The proxy entry is the only entry; users find the app here |

A useful naming convention: hidden duplicates get the suffix
`<DisplayName> Access` (e.g. "Grafana Access"), visible user-facing
proxies get a clean human name (e.g. "Files", "Models").

## Blueprint pattern

```yaml
# Hidden — duplicates the Grafana SAML entry that users actually click
- model: authentik_core.application
  identifiers:
    slug: grafana-access
  attrs:
    name: "Grafana Access"
    provider: !KeyOf grafana-proxy
    policy_engine_mode: any
    meta_hide: true
```

vs.

```yaml
# Visible — CopyParty has no separate OIDC/SAML, this IS the entry
- model: authentik_core.application
  identifiers:
    slug: copyparty-access
  attrs:
    name: "Files"
    provider: !KeyOf copyparty-proxy
    policy_engine_mode: any
    meta_launch_url: "https://files.example.com"
```

## Helm chart pattern

For umbrella charts that template proxy providers from a values list,
add a `hide` flag per provider (default `true`, since most forward-auth
providers are duplicates):

```yaml
# values.yaml
providers:
  - name: grafana
    displayName: Grafana
    subdomain: grafana
    hide: true   # duplicates Grafana SAML
  - name: copyparty
    displayName: Files
    subdomain: files
    hide: false  # CopyParty has no separate OIDC/SAML — this IS the app
```

In the helper template, default `hide` to `true` if the key is omitted.
Use `ternary` (not `=` inside an `if` block — that creates a
block-scoped variable in Go templates):

```gotemplate
{{- $hide := ternary .hide true (hasKey . "hide") -}}

- model: authentik_core.application
  identifiers:
    slug: {{ .name }}-access
  attrs:
    {{- if $hide }}
    name: "{{ .displayName }} Access"
    meta_hide: true
    {{- else }}
    name: "{{ .displayName }}"
    meta_launch_url: "https://{{ .subdomain }}.{{ .baseDomain }}"
    {{- end }}
    provider: !KeyOf {{ .name }}-proxy
    policy_engine_mode: any
```

**Gotcha:** when including this helper from a parent template, the dict
constructor must explicitly pass `hide` through, otherwise `hasKey`
inside the helper is always false and everything ends up hidden:

```gotemplate
{{- range .Values.providers }}
{{ include "proxy-providers.entry" (dict
    "name" .name
    "displayName" .displayName
    "subdomain" .subdomain
    "baseDomain" $.Values.global.baseDomain
    "groups" .groups
    "hide" .hide) | indent 6 }}
{{- end }}
```

## Verifying

After the blueprint applies, check in the Admin UI:

- **Applications → Applications**: the entry exists with the right name and
  the **Hide from Application Dashboard** toggle is on
- **Application Dashboard** (logged in as a normal user): the hidden entry is
  absent; the visible one is present and clicks through to the launch URL

Two failure modes:

- Blueprint reports `Enter a valid URL` on `meta_launch_url` → the template is
  emitting `blank://` instead of `blank://blank`. Pre-2026.5 only; on 2026.5+
  switch to `meta_hide` and drop the sentinel.
- Tile reappears after an upgrade → a blueprint is still writing
  `meta_launch_url: "blank://blank"` and overwriting the migrated `meta_hide`.
  Update the blueprint.

# Administration

Open WebUI gives administrators a full operational toolkit: usage tracking, model evaluation, system-wide announcements, and webhook integrations.

## Banners

Open WebUI allows administrators to display custom banners to logged-in users for announcements, alerts, maintenance notices, and important messages. Banners are persistent and can optionally be dismissible.

### Configuration Methods

**Option 1: Admin Panel** - Navigate to **Admin Panel > Settings > General > Banners**, click **+** to add, then **Save**.

**Option 2: Environment Variable** - Set `WEBUI_BANNERS` to a JSON string (array of banner objects).

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    environment:
      - 'WEBUI_BANNERS=[{"id":"maintenance-2026-03","type":"warning","title":"Maintenance","content":"A maintenance window is planned. <a href=\"https://intranet.example.com/status\" target=\"_blank\">See status page</a>.","dismissible":true,"timestamp":1772500000}]'
```

### Banner Object Properties

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Unique identifier. Used to track dismissal state. |
| `type` | string | yes | Banner style: `info` (Blue), `success` (Green), `warning` (Yellow), `error` (Red) |
| `title` | string | no | Title text |
| `content` | string | yes | Main message (HTML only, not Markdown) |
| `dismissible` | boolean | yes | Whether the user can dismiss the banner |
| `timestamp` | integer | yes | Present in configuration but not currently used by frontend for display timing |

### Banner ID Strategy

- Stable `id` for small text edits: `policy-reminder`
- Versioned `id` for "show again to everyone": `incident-2026-03-06-v2`
- Time-bucketed `id` for recurring events: `maintenance-2026-03`

Changing the `id` causes dismissed banners to reappear.

### Dismissal Behavior

Dismissed banners are stored client-side (browser). They may reappear if the user clears site data, uses a different device/browser, or if the `id` changes. Set `dismissible: false` for always-visible banners.

### Supported Content (HTML Only)

**Text:** `<b>`, `<strong>`, `<i>`, `<em>`, `<u>`, `<s>`, `<del>`, `<mark>`, `<small>`, `<sub>`, `<sup>`, `<code>`, `<kbd>`, `<abbr title="tooltip">`

**Structure:** `<br>`, `<hr>`, `<details><summary>Click</summary>...</details>`

**Links/Media:** `<a href="..." target="_blank">`, `<img src="..." width="16" height="16">`

**Inline styles** are supported on allowed tags.

**Not supported:** Headings (`<h1>`-`<h6>`), lists, tables, blockquotes, Markdown syntax.

### Common Pitfalls

1. **Literal newlines** in content are treated as line breaks - keep HTML compact
2. **Broken links** - always close `</a>` tags, use `target="_blank"`, escape `&` as `&amp;`
3. **JSON/YAML escaping** - validate JSON before deploying, avoid smart quotes
4. **External images** - set explicit `width`/`height`, prefer internal assets

### Best Practices

- Use banner types consistently: `info` (announcements), `success` (resolved), `warning` (maintenance), `error` (incidents)
- Remove expired banners to prevent alert fatigue
- Keep banners scannable: short title, one sentence, one link

## Webhooks

See [administration-webhooks.md](administration-webhooks.md) for full webhook reference (admin, user, and channel webhooks).

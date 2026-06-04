# Theme Overrides, Analytics & Privacy

## Theme Overrides

```toml
[project.theme]
custom_dir = "overrides"
```

Override blocks in `overrides/main.html`:
```html
{% extends "base.html" %}
{% block htmltitle %}<title>Custom</title>{% endblock %}
```

Available blocks: analytics, announce, config, container, content, extrahead, fonts, footer, header, hero, htmltitle, libs, outdated, scripts, site_meta, site_nav, styles, tabs.

Partial overrides: create matching files in `overrides/partials/`. Custom 404: `overrides/404.html`.

## Analytics & Privacy

## Analytics Configuration

```toml
[project.extra.analytics]
provider = "google"
property = "G-XXXXXXXXXX"
```

Supported providers: `google` (GA4), custom (implement `__analytics` JS callback).

## Cookie Consent

```toml
[project.extra.consent]
title = "Cookie consent"
description = "We use cookies to recognize your preferences."
cookies.analytics.name = "Google Analytics"
cookies.analytics.checked = true
```

## Feedback Widget

```toml
[project.extra.analytics]
feedback.title = "Was this page helpful?"
feedback.ratings["+1"].icon = "material/emoticon-happy-outline"
feedback.ratings["+1"].name = "This page was helpful"
feedback.ratings["+1"].note = "Thanks for your feedback!"
feedback.ratings["-1"].icon = "material/emoticon-sad-outline"
feedback.ratings["-1"].name = "This page could be improved"
feedback.ratings["-1"].note = "Help us improve this page."
```

## Custom Analytics Provider

```javascript
// Override __analytics in extra_javascript
window.__analytics = {
  initialize: function() {},
  result: function(url) {}
}
```

For full configuration details, see [zensical.org analytics docs](https://zensical.org/docs/setup/analytics/).

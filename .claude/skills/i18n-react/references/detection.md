# Locale detection: server flow, cookie, `?lang=`

## Priority chain

Configured in `app/i18n/server.ts` via `RemixI18Next`'s `detection.order`:

```ts
order: ['searchParams', 'cookie', 'header']
```

Lookup walks the chain and returns the first match in `supportedLanguages`. If none match, falls through to `fallbackLanguage`.

| Source | Mechanism | Lifetime |
|---|---|---|
| `searchParams` | `?lang=es` on the URL | One-shot (per request); also writes cookie on response |
| `cookie` | `app-locale=es` set on prior response | Until cleared or overwritten |
| `header` | `Accept-Language` from browser | Per request; reflects OS/browser settings |
| fallback | `fallbackLanguage` config value | When nothing else matches |

## Cookie semantics

Created via React Router's `createCookie`:

```ts
export const localeCookie = createCookie('app-locale', {
  sameSite: 'lax',
  path: '/',
});
```

- **No `Max-Age` / `Expires`** → session cookie. Promote to persistent (e.g. 1 year) by adding `maxAge: 60 * 60 * 24 * 365`.
- **`SameSite=Lax`** → sent on top-level navigations; safe default.
- **Not `httpOnly`** → JavaScript can read it (needed if a client-side language picker writes it directly).
- **No `secure: true`** → set this in production behind HTTPS.

## `?lang=` override behavior

`?lang=es` on any non-prerendered route:
1. Server reads `?lang=es` via `searchParams`.
2. Returns Spanish HTML.
3. `remix-i18next` sets the cookie on the response.
4. Future requests find the cookie before the header → Spanish persists.

`?lang=es` on a **prerendered** route (`react-router.config.ts` `prerender` list):
- Server doesn't run — static English HTML is served.
- Client reads `?lang=es` and re-renders Spanish after hydration (flicker).
- Cookie is not set server-side; clients can set it via JS if needed.

## Client-side sync: `useChangeLanguage`

```ts
import { useChangeLanguage } from 'remix-i18next/react';

export function Layout(...) {
  const { locale } = useLoaderData<typeof loader>();
  useChangeLanguage(locale);  // calls i18n.changeLanguage(locale) when it changes
  // ...
}
```

This hook keeps the client-side `i18n` singleton in sync with whatever the server decided. Without it, the client might run with its own default language and produce a hydration mismatch on translated content.

## Setting `<html lang={locale}>`

Always set this attribute from loader data. It:
- Tells screen readers which language is being spoken.
- Enables CSS `:lang(es)` selectors and language-specific fonts.
- Lets `app/i18n/client.ts` read `document.documentElement.lang` to bootstrap the client instance with the same locale.

## Switching language at runtime

To add a language picker:

```ts
function LanguageSwitcher() {
  const submit = useSubmit();
  return (
    <Form method="post" action="/set-locale" onChange={(e) => submit(e.currentTarget)}>
      <select name="lang" defaultValue={locale}>
        <option value="en">English</option>
        <option value="es">Español</option>
      </select>
    </Form>
  );
}
```

The `/set-locale` action sets the `app-locale` cookie via `localeCookie.serialize(lang)` in the response headers and redirects back. `remix-i18next` will pick up the new cookie on the next request.

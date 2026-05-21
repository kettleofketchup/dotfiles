# Wiring: root.tsx, entry.server.tsx, using `t()`

For dependencies and config-file contents, see `setup.md`.
For locale detection priorities and `useChangeLanguage` semantics, see `detection.md`.

## `app/root.tsx`

```ts
import { useChangeLanguage } from 'remix-i18next/react';
import { useLoaderData } from 'react-router';
import { i18nServer } from './i18n/server';

export async function loader({ request }: LoaderFunctionArgs) {
  const locale = await i18nServer.getLocale(request);
  return { locale };
}

export function Layout({ children }: { children: React.ReactNode }) {
  const { locale } = useLoaderData<typeof loader>();
  useChangeLanguage(locale);
  return (
    <html lang={locale}>
      {/* head */}
      <body>{children}</body>
    </html>
  );
}
```

If `root.tsx` already has a `loader`, merge `locale` into the existing return value rather than replacing.

## `app/entry.server.tsx`

Wrap the SSR React tree in `<I18nextProvider>` using a per-request instance:

```ts
import { I18nextProvider } from 'react-i18next';
import { createI18nInstance } from './i18n/config';
import { i18nServer } from './i18n/server';

// Inside handleRequest / handleBrowserRequest:
const locale = await i18nServer.getLocale(request);
const i18n = createI18nInstance(locale);

const markup = renderToString(
  <I18nextProvider i18n={i18n}>
    <ServerRouter context={routerContext} url={request.url} />
  </I18nextProvider>
);
```

Per-request instance is essential — sharing one instance across requests leaks locale state between concurrent users.

## `app/entry.client.tsx`

Import the client singleton before hydration:

```ts
import { I18nextProvider } from 'react-i18next';
import { i18n } from './i18n/client';

hydrateRoot(
  document,
  <I18nextProvider i18n={i18n}>
    <HydratedRouter />
  </I18nextProvider>
);
```

## Using `t()` in components

```ts
import { useTranslation } from 'react-i18next';

export function Greeting() {
  const { t } = useTranslation('common');
  return <h1>{t('greeting.hello')}</h1>;
}
```

With interpolation:

```ts
<span>{t('match.score', { home: 2, away: 1 })}</span>
// en.json: "match": { "score": "{{home}} - {{away}}" }
```

With pluralization:

```ts
<span>{t('items.count', { count: items.length })}</span>
// en.json: "items": { "count_one": "1 item", "count_other": "{{count}} items" }
```

Outside of components (utilities, zod messages):

```ts
import i18next from 'i18next';
const msg = i18next.t('errors.required', { ns: 'common' });
```

This works because `initReactI18next` registers the default i18next instance globally on the client. For SSR utilities called inside a request, prefer passing the per-request `i18n` instance explicitly via context.

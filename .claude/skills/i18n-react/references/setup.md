# Setup: Dependencies and config files

For wiring `root.tsx`, `entry.server.tsx`, and using `t()` in components, see `wiring.md`.

## Dependencies

Runtime (`dependencies`):
- `i18next` — core translation engine
- `react-i18next` — React bindings (`useTranslation`, `<I18nextProvider>`)
- `remix-i18next` — server-side detection compatible with Remix and React Router 7

Dev (`devDependencies`):
- `i18next-parser` — extracts `t()` calls into JSON
- `eslint-plugin-i18next` — provides `no-literal-string` rule

## File layout

```
app/
  i18n/
    config.ts             # createI18nInstance(locale) factory
    server.ts             # RemixI18Next + cookie definition
    client.ts             # client singleton init
    types.ts              # TS module augmentation for typed t()
    locales/
      en/<namespace>.json
      es/<namespace>.json
  root.tsx                # loader → locale; <html lang={locale}>
  entry.server.tsx        # wrap render in <I18nextProvider>
  entry.client.tsx        # bootstrap client i18n singleton
i18next-parser.config.ts  # parser config (input globs, locales)
eslint.config.js          # ESLint flat config (overrides block)
```

## `app/i18n/config.ts`

```ts
import { createInstance, type i18n } from 'i18next';
import { initReactI18next } from 'react-i18next';
import enCommon from './locales/en/common.json';
import esCommon from './locales/es/common.json';

export function createI18nInstance(locale: string): i18n {
  const instance = createInstance();
  instance.use(initReactI18next).init({
    lng: locale,
    fallbackLng: 'en',
    supportedLngs: ['en', 'es'],
    ns: ['common'],
    defaultNS: 'common',
    resources: {
      en: { common: enCommon },
      es: { common: esCommon },
    },
    interpolation: { escapeValue: false },
    react: { useSuspense: false },
  });
  return instance;
}
```

## `app/i18n/server.ts`

```ts
import { createCookie } from 'react-router';
import { RemixI18Next } from 'remix-i18next/server';

export const localeCookie = createCookie('app-locale', {
  sameSite: 'lax',
  path: '/',
});

export const i18nServer = new RemixI18Next({
  detection: {
    supportedLanguages: ['en', 'es'],
    fallbackLanguage: 'en',
    order: ['searchParams', 'cookie', 'header'],
    searchParamKey: 'lang',
    cookie: localeCookie,
  },
});
```

## `app/i18n/client.ts`

```ts
import { createI18nInstance } from './config';

const locale = document.documentElement.lang || 'en';
export const i18n = createI18nInstance(locale);
```

Imported once from `entry.client.tsx` so the singleton initializes before React mounts.

## `app/i18n/types.ts`

```ts
import type common from './locales/en/common.json';
declare module 'i18next' {
  interface CustomTypeOptions {
    defaultNS: 'common';
    resources: { common: typeof common };
  }
}
```

Makes `t('nonexistent.key')` a TypeScript error. Add more namespaces to `resources` as the app grows.

JSON imports require `resolveJsonModule: true` in `tsconfig.json`.

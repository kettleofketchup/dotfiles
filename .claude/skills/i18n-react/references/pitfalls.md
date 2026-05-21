# Pitfalls and known limitations

## Prerendered routes flicker the fallback language

**Symptom:** User with `Accept-Language: es` visits `/` and sees English for ~100ms before the page snaps to Spanish.

**Cause:** Routes listed in `react-router.config.ts` `prerender: [...]` have HTML built at deploy time. The server doesn't run for those routes, so `Accept-Language` can't be honored. Client picks up the cookie/header after hydration and re-renders.

**Fixes (in order of effort):**
1. **Accept it.** For navbar-only / small scope, the flicker is briefly visible and not catastrophic.
2. **Remove the route from `prerender`.** Loses SSG benefits (CDN edge caching, faster TTFB) for that route.
3. **Prerender both languages** — produce `/index.en.html` and `/index.es.html`, then add a CDN/edge function that picks one based on `Accept-Language`. Most complex; preserves SSG.

## Prop-based visible text not caught by lint

**Symptom:** `<Card title="Events" subtitle="Sign up here" />` passes ESLint but ships untranslated text.

**Cause:** `eslint-plugin-i18next`'s `no-literal-string` with `markupOnly: true` only flags JSX text nodes, not string-valued props.

**Why not turn `markupOnly` off:** Floods warnings on legitimate prop literals — `variant="primary"`, `size="lg"`, `to="/dashboard"`, `data-testid="..."`. Adding all those to `ignoreAttribute` is brittle.

**Workarounds:**
- **Manual conversion.** When converting a directory, grep for `title=`, `subtitle=`, `label=`, `placeholder=`, `tooltip=` patterns and wrap visible ones with `t()`.
- **Custom ESLint rule.** Build one that knows which prop names render visibly (`title`, `label`, etc.) for the project's components. Worth it only at significant scale.
- **Component refactor.** Have visible-text props accept `t()`-returned strings only via TS type discrimination — won't help legacy code.

## Hydration mismatch on `<html lang>` or translated content

**Symptom:** React error in console: "Hydration failed because the server rendered HTML didn't match the client."

**Common causes:**
- Forgot `useChangeLanguage(locale)` in `root.tsx`'s `Layout` — client uses its own default language while server used the loader-decided one.
- Client-side `i18n` instance initialized with `'en'` hard-coded instead of reading from `document.documentElement.lang`.
- `localStorage`-based detection in client config that disagrees with server decision.

**Fix:** Server decides locale (loader). Client reads server's decision from `<html lang>` or loader data. Client does NOT make its own detection on first render — only after.

## `supportedLngs` vs `fallbackLng`

**Symptom:** Added French translations to `fr/common.json` but `?lang=fr` still shows English.

**Cause:** `fr` not in `supportedLngs` array. Locales outside that list are rejected by `remix-i18next`'s detection AND by `i18next.changeLanguage()`.

**Fix:** Add to BOTH:
```ts
// in createI18nInstance:
supportedLngs: ['en', 'es', 'fr'],

// in RemixI18Next:
supportedLanguages: ['en', 'es', 'fr'],
```

And ship the JSON files. Forgetting one of the two means silent fallback to English.

## Shared i18n instance across requests

**Symptom:** User A loads `/?lang=es`, then user B (in English browser) sees Spanish.

**Cause:** Single `i18n` instance created at module scope in `entry.server.tsx` instead of per-request. `i18next.changeLanguage()` mutates global state.

**Fix:** Call `createInstance()` inside the request handler, not at module top level. Each request gets a fresh instance.

## Parser doesn't see dynamic keys

**Symptom:** `t(\`status.${match.status}\`)` doesn't generate keys in JSON files.

**Cause:** `i18next-parser` does static analysis. It can't evaluate template literals or variables.

**Fix:** Either:
- Add a comment hint: `// t('status.pending') t('status.completed') t('status.in_progress')` somewhere the parser scans — these literal forms get extracted.
- List all variants in `i18next-parser.config.ts`'s `lexers` config with `functions: ['t']`.
- Define an explicit map and use `t()` on each member.

## ESLint flat config not picking up plugin

**Symptom:** `i18next/no-literal-string` rule not enforced even though config exists.

**Cause:** Importing the plugin without registering in the `plugins` field of the override block.

**Fix:** Each override that uses a plugin's rule must declare `plugins: { i18next }` (the namespace key matches the rule prefix).

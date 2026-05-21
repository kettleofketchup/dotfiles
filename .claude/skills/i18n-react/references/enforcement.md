# Enforcement: parser, ESLint, typed `t()`, CI workflow

## `i18next-parser.config.ts`

```ts
export default {
  locales: ['en', 'es'],
  input: ['app/components/<scope>/**/*.{ts,tsx}'],
  output: 'app/i18n/locales/$LOCALE/$NAMESPACE.json',
  defaultNamespace: 'common',
  keySeparator: '.',
  createOldCatalogs: false,
};
```

`input` is the **single source of truth** for parser scope. Keep `package.json` script invocations free of input globs to avoid two places to update.

`createOldCatalogs: false` prevents the parser from writing `<lng>/<ns>_old.json` files for keys that disappear.

## `package.json` scripts

```json
{
  "scripts": {
    "i18n:extract": "i18next --config i18next-parser.config.ts",
    "i18n:check": "i18next --config i18next-parser.config.ts --fail-on-update"
  }
}
```

- `i18n:extract` — developers run locally; updates JSON files in place.
- `i18n:check` — CI runs; fails with non-zero exit if files would change (i.e., a `t()` key is missing from a locale file).

## `eslint-plugin-i18next` flat-config override

```js
// eslint.config.js
import i18next from 'eslint-plugin-i18next';

export default [
  // ... other configs ...
  {
    files: ['app/components/<scope>/**/*.{ts,tsx}'],
    plugins: { i18next },
    rules: {
      'i18next/no-literal-string': ['error', {
        markupOnly: true,
        ignoreAttribute: [
          'data-testid', 'className', 'href', 'to', 'aria-label',
        ],
      }],
    },
  },
];
```

**`markupOnly: true`** — only JSX text nodes are flagged. Without this, every `variant="primary"` style prop trips the rule. Trade-off: prop-based visible text (`title="..."`, `subtitle="..."`) is NOT caught; see `pitfalls.md`.

**`ignoreAttribute`** — additionally exempt these attribute names. `data-testid`, `className`, `href`, `to` are common technical attrs. Add `aria-label` if a11y labels are out of scope (translate them later by removing from the list).

## Typed `t()` via module augmentation

`app/i18n/types.ts`:

```ts
import type common from './locales/en/common.json';

declare module 'i18next' {
  interface CustomTypeOptions {
    defaultNS: 'common';
    resources: { common: typeof common };
  }
}
```

Effect: `t('common.nonexistent')` becomes a TypeScript error caught at compile time. Add other namespaces to `resources` as the app expands (e.g. `navbar: typeof navbar`).

If JSON imports require `resolveJsonModule: true` in `tsconfig.json`, add it.

## Validation in CI

Three checks gate every PR:

```
tsc                                    # typed t() keys must exist
eslint . --max-warnings 0              # no-literal-string violations fail
i18next --config ... --fail-on-update  # all locales have all keys
```

`--max-warnings 0` is the ratchet: even if most rules are `warn`-level during bootstrap, CI treats them as errors. Tightens strictness without changing the CI command.

## Local developer workflow

1. Add `t('ns.foo.bar')` in a covered file.
2. `npm run i18n:extract` → updates `en/<ns>.json` and other locales with placeholder values (typically the key itself).
3. Edit each locale file with real translations.
4. `npm run i18n:check` locally to confirm parser is happy.
5. `tsc && eslint` for typed-key and lint checks.
6. Commit JSON + component together.

## Expanding scope

To enforce on a new directory:
1. Append path to `i18next-parser.config.ts`'s `input` array.
2. Append same path to `eslint.config.js`'s `i18next` `overrides` `files` array.
3. Run `i18n:extract` to seed JSON keys for existing `t()` calls (or wrap literals first).
4. Translate.

# TanStack Start

Full-stack React framework on Vite + Nitro. Successor to the Vinxi-based v0/v1-beta.

## Install / scaffold

```bash
npx @tanstack/cli@latest create     # interactive scaffold (preferred)
```

Old paths to AVOID: `npm create @tanstack/start` and `create-tsrouter-app` are deprecated. Package `@tanstack/start` is unpublished — install **`@tanstack/react-start`**.

```bash
pnpm add @tanstack/react-start @tanstack/react-router nitro vite @vitejs/plugin-react
```

(Router-plugin is bundled inside `@tanstack/react-start` — do NOT add `@tanstack/router-plugin` separately. Router-only Vite apps without Start do need it.)

## `vite.config.ts` (canonical shape)

```ts
import { defineConfig } from 'vite'
import viteReact from '@vitejs/plugin-react'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import { nitro } from 'nitro/vite'

export default defineConfig({
  server: { port: 3000 },
  plugins: [
    tanstackStart({ srcDirectory: 'src' }), // bundles router-plugin internally
    viteReact(),
    nitro(),
  ],
})
```

Order: `tanstackStart` → `viteReact` → `nitro`. **Do not** add `tanstackRouter()` as a separate plugin in a Start project — `tanstackStart()` already runs it; duplicating causes double route-tree generation. `srcDirectory` is **flat top-level** (no `tsr: {}` wrapper). Default source dir is `./src` (was `./app`).

## Server functions — `.inputValidator().handler()`

```tsx
// src/server/users.ts
import { createServerFn } from '@tanstack/react-start'
import { z } from 'zod'

export const createUser = createServerFn({ method: 'POST' })
  .inputValidator(z.object({ name: z.string().min(1), age: z.number().min(0) }))
  .handler(async ({ data }) => {
    // runs only on server; bundler tree-shakes from client
    return { id: crypto.randomUUID(), ...data }
  })

// Client call (typed): const u = await createUser({ data: { name: 'a', age: 1 } })
```

`.validator()` → **`.inputValidator()`** (renamed). For GET fns use `method: 'GET'`. Accepts FormData by typing the validator accordingly.

Use server fns inside Router loaders too: `loader: () => createUser({ data: ... })`.

Access the request (cookies/headers/IP) inside `.handler()`:

```ts
import { getWebRequest } from '@tanstack/react-start/server'

createServerFn({ method: 'GET' }).handler(async () => {
  const req = getWebRequest()
  const session = req.headers.get('cookie')
  // ...
})
```

## API routes — `createFileRoute` with `server.handlers`

`createAPIFileRoute` / `createServerFileRoute` are **removed**. API routes are regular file routes; the exported variable is `Route`, not `APIRoute`.

```ts
// src/routes/api/hello.ts → GET /api/hello
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/api/hello')({
  server: {
    handlers: {
      GET: async ({ request }) => Response.json({ ok: true }),
      POST: async ({ request }) => {
        const body = await request.json()
        return Response.json({ received: body })
      },
    },
  },
})
```

Dynamic params (`/api/users/$id.ts`) work the same — handler gets `{ params }` from the route context.

## Entry points

Only one user-authored entry is required: **`src/router.tsx`** exporting `getRouter()`:

```tsx
// src/router.tsx
import { createRouter as createTanstackRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'

export function getRouter() {
  return createTanstackRouter({
    routeTree,
    scrollRestoration: true,
    defaultPreloadStaleTime: 0,
  })
}

declare module '@tanstack/react-router' {
  interface Register { router: ReturnType<typeof getRouter> }
}
```

The Vite plugin generates `client.tsx` / `ssr.tsx` / `server.ts`. **Do not author them.** Optional `src/start.ts` lets you override the default Start instance (e.g. disable built-in CSRF middleware, register global middleware).

## Deployment (Nitro presets)

Set with env var or in `nitro()` plugin opts:

```ts
nitro({ preset: 'vercel' })
// or NITRO_PRESET=vercel pnpm build
```

Presets: `node-server` (default), `vercel`, `netlify`, `cloudflare-module`, `cloudflare-pages`, `bun`, `deno-server`, `aws-lambda`. Output goes to `.output/server/index.mjs` — run with `node .output/server/index.mjs`.

## Common gotchas (last ~6 months of breakage)

- Following any pre-2025 tutorial — Vinxi is gone, almost every example is stale.
- Importing from `@tanstack/start` — that package no longer exists.
- Forgetting `nitro()` in `vite.config.ts` — build produces a client bundle only.
- Vite 8 + Nitro 3 alpha combo has known Azure/Windows breakage; pin Nitro to a known-good version if CI fails on Windows runners.
- Using `.validator()` from an old example → "is not a function".
- Reading server fn body on the client — the bundler strips it; closures over server-only modules will silently break unless inside `.handler()`.

## RSC (preview)

`@tanstack/react-start-rsc` enables React Server Components + compiler-driven CSS injection. Still preview as of skill write; check the package readme before using.

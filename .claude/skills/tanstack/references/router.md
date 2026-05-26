# TanStack Router (file-based, type-safe)

## File-based conventions (`src/routes/`)

| Token | Meaning |
|---|---|
| `__root.tsx` | Root layout; provides `<Outlet/>`, devtools mount |
| `index.tsx` / `*.index.tsx` | Exact-match for parent |
| `posts.tsx` + `posts/index.tsx` | Layout + index pair |
| `posts.$postId.tsx` / `posts/$postId.tsx` | Dynamic param (flat or directory style; mix freely) |
| `_layout.tsx` | Pathless layout (wraps children, no URL segment) |
| `posts_.tsx` (trailing `_`) | Un-nest from parent |
| `(group)/` | Route group — folder excluded from URL |
| `-component.tsx`, `-utils/` | Excluded from `routeTree.gen.ts` (colocation) |
| `$.tsx` | Splat (`_splat` param) |
| `{-$cat}` | Optional param |
| `[x]` | Escape special chars (`script[.]js.tsx` → `/script.js`) |
| `route.tsx` suffix | Directory-level layout file |

## `createFileRoute` shape

```tsx
import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'

const search = z.object({ page: z.number().catch(1) })

export const Route = createFileRoute('/posts/$postId')({
  validateSearch: search,
  loaderDeps: ({ search: { page } }) => ({ page }),   // pluck only what loader reads
  beforeLoad: ({ context }) => ({ /* merged into context */ }),
  loader: async ({ params, context, deps, abortController, preload }) => {
    return context.queryClient.ensureQueryData(postOptions(params.postId))
  },
  component: PostComponent,
  pendingComponent: Spinner,
  pendingMs: 200,            // delay before pending UI shows (avoid flash)
  pendingMinMs: 500,         // minimum time it stays visible
  errorComponent: ({ error, reset }) => <Err msg={error.message} retry={reset} />,
  notFoundComponent: () => <NotFound />,
})
```

The path string is auto-managed by the Vite plugin — don't edit it manually.

## Typed accessors

```tsx
const data = Route.useLoaderData()
const { postId } = Route.useParams()
const { page } = Route.useSearch()
```

For deep components, prefer `getRouteApi('/posts/$postId')` over importing `Route` (avoids cycles): `const route = getRouteApi('/posts/$postId'); const { postId } = route.useParams()`.

## Search params with Zod

```tsx
const productSearch = z.object({
  page: z.number().catch(1),
  sort: z.enum(['newest','oldest','price']).catch('newest'),
})
export const Route = createFileRoute('/shop/products')({
  validateSearch: productSearch,  // Zod v4: direct. Zod v3: zodValidator(schema) from @tanstack/zod-adapter
})
```

`.catch(default)` swallows validation errors silently → resilient defaults. `.default()` if you want validation errors to surface.

Other validators (Valibot 1.0+, Arktype 2.0+, Effect Schema) work directly via Standard Schema — no adapter needed.

## Typed navigation

```tsx
<Link to="/shop/products" search={{ page: 3, sort: 'newest' }} />
<Link from="/posts" to="./$postId" params={{ postId: '1' }} />

// Function form preserves other params/search keys (object form REPLACES them):
<Link to="." search={(prev) => ({ ...prev, page: prev.page + 1 })} />
<Link from="/posts/$postId" to="." params={(prev) => ({ ...prev, edit: true })} />
```

`from` enables relative paths and narrows `to` candidates by type. **Object form for `search`/`params` wipes unspecified keys** — use the function form for partial updates.

## Loaders + Query handoff

```tsx
loader: async ({ context, params }) => {
  await context.queryClient.ensureQueryData(postOptions(params.postId))
  // component reads via useSuspenseQuery(postOptions(postId)) — cache is warm
}
```

Loader args: `{ params, context, deps, abortController, preload, cause, location }`. Search params are **NOT in loader args** directly — surface them via `loaderDeps` so the loader cache keys correctly:

```tsx
loaderDeps: ({ search }) => ({ page: search.page }),  // narrow! whole search → thrashing
loader: ({ deps }) => fetchPage(deps.page),
```

Set `defaultPreloadStaleTime: 0` on `createRouter` so router preloads always defer to Query's own staleness logic.

## Router context

```tsx
// src/routes/__root.tsx
import { createRootRouteWithContext } from '@tanstack/react-router'
import type { QueryClient } from '@tanstack/react-query'

interface MyRouterContext { queryClient: QueryClient }

export const Route = createRootRouteWithContext<MyRouterContext>()({
  component: () => <><Outlet /><TanStackRouterDevtools /></>,
})

// src/router.tsx
const router = createRouter({ routeTree, context: { queryClient } })
```

`beforeLoad` returns a partial merged into descendants. For React hooks that need context, leave the value `undefined!` in `createRouter` and inject via `<RouterProvider context={{ ... }} />`.

## Vite plugin

`tanstackRouter({ target: 'react', autoCodeSplitting: true })`. Defaults: `routesDirectory './src/routes'`, `generatedRouteTree './src/routeTree.gen.ts'`, `routeFileIgnorePrefix '-'`. MUST be ordered **before** `@vitejs/plugin-react`. Add `routeTree.gen.ts` to ESLint/Prettier/Biome ignores + VSCode `files.readonlyInclude` / `search.exclude`.

## Module augmentation (mandatory)

```tsx
const router = createRouter({ routeTree, context: { queryClient } })
declare module '@tanstack/react-router' {
  interface Register { router: typeof router }
}
```

Without this, `<Link to="/...">` and typed hooks lose inference globally.

## Devtools

`import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'` (NOT `@tanstack/router-devtools` — renamed). Mount: `<TanStackRouterDevtools router={router} />`.

## Common pitfalls

- **Phantom type errors after adding/renaming a route** — `routeTree.gen.ts` regenerates on save; if IDE shows ghost errors, restart TS server.
- **Reading `search` in loader directly** → cache misses + thrashing. Route through `loaderDeps`.
- **Returning whole `search` from `loaderDeps`** → loader re-runs on every unrelated search change. Extract specific keys.
- **`Link` `to` is relative** unless prefixed with `/`. Pair with `from` for typed relative navigation.
- **Skipping module augmentation** = silently weak types.
- **Importing `Route` in deep components** can cause cycles. Use `getRouteApi('/path')`.
- **Zod v3 + `.catch()`** widens types to `unknown`; use `fallback()` from `@tanstack/zod-adapter` or upgrade to Zod v4.

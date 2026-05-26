# Debugging recipes (TanStack)

## Devtools — install per library

```tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'  // not @tanstack/router-devtools

// Inside providers (Query in QueryClientProvider, Router in the __root component):
<ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-right" />
<TanStackRouterDevtools router={router} />
```

If devtools "don't appear": they're outside the provider, or you're running a production build that tree-shook them, or you've hidden them via `process.env.NODE_ENV` checks.

## Query: "doesn't refetch when I change a filter"

Almost always: filter is not in `queryKey`. The `queryFn` closure captures the latest filter, but the cache is keyed on the original — Query returns the cached entry without re-running.

```ts
// WRONG
useQuery({ queryKey: ['users'], queryFn: () => fetchUsers(filter) })

// RIGHT
useQuery({ queryKey: ['users', filter], queryFn: () => fetchUsers(filter) })
// or use queryOptions(filter) factory
```

## Query: hydration mismatch / cross-request leak

Causes:
1. `new QueryClient()` at **module scope** on the server — shared across requests.
2. Different `QueryClient` on server vs client — dehydrated state doesn't apply.

Fix: `useState(() => new QueryClient())` on the client, fresh instance per request on the server. Pair with `<HydrationBoundary state={dehydratedState}>`.

## Query: `onSuccess`/`onError`/`onSettled` on useQuery does nothing

v5 **removed** per-query callbacks from `useQuery`. Only `useMutation` still has them. Symptoms: side-effect never fires, no TS error in loose configs. Fix: move the side-effect into the mutation that triggered the change, or into a `useEffect` keyed on `data`/`error`.

## Query: `keepPreviousData is not a function`

v5 removed it. Use the identity helper:

```ts
import { keepPreviousData } from '@tanstack/react-query'
useQuery({ ..., placeholderData: keepPreviousData })
```

Check `isPlaceholderData` to render stale-but-shown UI dimmed.

## Router: phantom type errors after adding a route

`routeTree.gen.ts` regenerates when the Vite plugin sees a save under `src/routes/`. Symptoms: TS thinks the route exists, IDE thinks it doesn't (or vice versa).

Fix:
1. Save any route file with `vite dev` running.
2. Restart the TS server in your IDE (VSCode: `> TypeScript: Restart TS Server`).
3. Confirm `routeTree.gen.ts` actually changed on disk.
4. Confirm module augmentation exists: `declare module '@tanstack/react-router' { interface Register { router: typeof router } }`.

## Router: `<Link to="/posts">` errors "Type ... is not assignable"

Module augmentation is missing or `router` type isn't being inferred. Verify:

```ts
const router = createRouter({ routeTree, context: { queryClient } })
declare module '@tanstack/react-router' { interface Register { router: typeof router } }
```

If `router` is wrapped (e.g. `getRouter()` returning a router), the augmentation must use `ReturnType<typeof getRouter>`.

## Router: loader re-runs constantly

`loaderDeps` is returning the whole `search` object (or omitted entirely with `search` read inside the loader). Fix: extract only what the loader reads.

```ts
loaderDeps: ({ search }) => ({ page: search.page }),   // narrow!
loader: ({ deps }) => fetchPage(deps.page),
```

## Router: preload doesn't hit cache

Set `defaultPreloadStaleTime: 0` on `createRouter`. Default behavior caches preloads independently of Query — you want Query in charge of staleness.

## Start: `Cannot find module '@tanstack/start'`

The package is `@tanstack/react-start`. Old tutorials are wrong.

## Start: server function returns undefined / 500

Common causes:
- Used `.validator()` instead of `.inputValidator()` (renamed).
- Threw from inside `.handler()` without a try/catch — error surfaces as a generic 500. Wrap and `console.error` in dev.
- Forgot `nitro()` in `vite.config.ts` → no server bundle.
- Plugin order wrong (must be `tanstackRouter`, `tanstackStart`, `viteReact`, `nitro`).

## Start: build succeeds but server bundle missing

Check `.output/server/index.mjs` exists. If only `.output/public/` is there, `nitro()` isn't in plugins.

## Start: API route returns HTML instead of JSON

Used `createAPIFileRoute` / `createServerFileRoute` — they're removed. Use `createFileRoute('/api/...')` with `server.handlers`.

## Start: server function 500 with no useful error

Errors thrown inside `.handler()` surface as a generic 500 on the client. Wrap with a top-level `try/catch`, log to the server console, and rethrow a typed error the client can render. Validator failures (from `.inputValidator()`) surface as 400s with field details — surface them in the UI.

## Table: row selection follows the wrong rows after sort/filter

Default row id is the array index. After sort/filter, "row at index 2" is a different record. Set `getRowId: (row) => row.id` (or any stable field) so selection keys to record identity.

## Form: errors render as `[object Object]`

Standard-schema validators (Zod/Valibot/Arktype) return arrays of issue **objects**, not strings. `field.state.meta.errors.join(', ')` stringifies objects. Use `errors.map(e => e?.message ?? String(e)).join(', ')`.

## Table: state resets on every render

`data` or `columns` is being re-created inline. Memoize:

```ts
const columns = useMemo(() => [...], [])
const data = useMemo(() => fetched ?? [], [fetched])
```

## Form: full page reload on submit

Missing `e.preventDefault()` in the `<form onSubmit>` handler.

## Virtual: rows jump / scroll position wrong

- Missing `data-index` attribute when using `rv.measureElement`.
- `estimateSize` off by an order of magnitude.
- Container missing `position: relative` and `height: rv.getTotalSize()`.

## General: "works in dev, breaks in prod"

- Devtools were doing something the prod app isn't (e.g. forcing refetch on focus).
- `import.meta.env.DEV`-gated code paths.
- Server-only modules accidentally imported on the client — Vite catches most in dev with HMR but ships them in prod. Use `?inline` / dynamic `import()` to confine.
- Different Node version on CI — Nitro 3 + Vite 8 have known issues on Node < 20.

## When stuck

1. Open both devtools (Query + Router).
2. Reproduce in the smallest possible file — paste the route + loader + queryOptions only.
3. Check the official examples in `github.com/TanStack/router/tree/main/examples/react/` — they're the canonical "what's current" reference.
4. Compare your `vite.config.ts` plugin order against `start.md`.

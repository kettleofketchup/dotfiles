# Code review checklist — TanStack PRs

Use this when reviewing a diff that touches TanStack code. Each section is a per-library checklist of the bugs that actually ship. Quote line numbers in review comments. Most items map to a "Pitfalls" entry in the matching reference file.

## Cross-cutting (any TanStack diff)

- [ ] **No `@tanstack/start` import.** Package is `@tanstack/react-start`.
- [ ] **Module augmentation present** in router setup file: `declare module '@tanstack/react-router' { interface Register { router: typeof router } }`. Without it, `<Link to=...>` types silently degrade.
- [ ] **`QueryClient` instantiated via `useState(() => new QueryClient())`** on the client or per-request on the server — never at module scope on the server.
- [ ] **Devtools mounted under their provider** (Query inside `QueryClientProvider`, Router inside root component) and tree-shakable in prod.
- [ ] **No secrets in client-bundled code** — env reads must be confined to `.handler()` bodies, server-only modules, or `import.meta.env.SERVER_*` patterns the bundler strips.

## TanStack Query

- [ ] **`queryKey` contains every input the `queryFn` reads.** If `queryFn` closes over `filter`/`userId`/etc., they belong in the key. Otherwise the cache returns stale-input data.
- [ ] **`queryFn` forwards `signal`** to `fetch`/axios for auto-cancellation on unmount or key change.
- [ ] **Conditional inputs use `enabled: !!input`** instead of guarding inside `queryFn`.
- [ ] **No `onSuccess`/`onError`/`onSettled` on `useQuery`.** Removed in v5 — silently does nothing. Move side-effects to `useMutation` or `useEffect` keyed on data.
- [ ] **`gcTime` not `cacheTime`** (renamed in v5). Same for `pending` not `loading`.
- [ ] **`placeholderData: keepPreviousData`** (the identity helper) — `keepPreviousData: true` is gone.
- [ ] **`useInfiniteQuery` sets `initialPageParam`** — required in v5.
- [ ] **Shared queries use a `queryOptions()` factory** so key + types stay in sync across `useQuery`/`useSuspenseQuery`/`prefetchQuery`/`setQueryData`.
- [ ] **Mutations include `onMutate` cancel-cache and `onError` rollback** if doing optimistic updates.

## TanStack Router

- [ ] **`validateSearch` uses `.catch(default)`** (or `.fallback()` via zod-adapter for v3) for resilient defaults that don't trigger error UI.
- [ ] **`loaderDeps` plucks only the keys the loader reads** — not the whole `search` object. Wide `loaderDeps` thrashes the loader.
- [ ] **Search params NOT read directly inside `loader`** — route them through `loaderDeps`.
- [ ] **`createRootRouteWithContext<{ queryClient }>`** for any Router + Query setup, and `defaultPreloadStaleTime: 0` on `createRouter`.
- [ ] **Deep components use `getRouteApi('/path')`** instead of importing `Route` directly (avoids cycles).
- [ ] **`<Link>` `search`/`params` use the function form `(prev) => ({ ...prev })` for partial updates.** Object form replaces all keys — easy to wipe `page` while changing `sort`.
- [ ] **`pendingMs` / `pendingMinMs` set** on routes with a `pendingComponent` to avoid spinner flash.
- [ ] **`notFoundComponent` present** on dynamic routes that can 404.
- [ ] **`routeTree.gen.ts` added to ESLint/Prettier/Biome ignores** and not edited by hand.

## TanStack Start

- [ ] **`vite.config.ts` has `tanstackStart()`, `viteReact()`, `nitro()` in that order.** No separate `tanstackRouter()` plugin (Start bundles it). No `app.config.ts` / Vinxi artifacts.
- [ ] **Server functions use `.inputValidator(...)` not `.validator(...)`.** The latter doesn't exist in current versions.
- [ ] **API routes use `createFileRoute(...)` with `server: { handlers: { GET, POST, ... } }`.** No `createAPIFileRoute` / `createServerFileRoute` — both removed.
- [ ] **Server fns wrap throws in `try/catch`** and log the real error server-side. Unhandled throws surface as opaque 500s.
- [ ] **Mutating server fns considered for CSRF** — if you've disabled the default middleware in `start.ts`, you must protect them yourself.
- [ ] **`getWebRequest()` (from `@tanstack/react-start/server`) used for cookie/header/IP access** — not `process.env` or React hooks.
- [ ] **No `window` / `document` references inside `.handler()`** bodies. They run server-side.
- [ ] **Nitro preset set** (env or plugin option) for the target deployment.

## TanStack Table

- [ ] **`data` and `columns` are memoized** (`useMemo` or module-scope). Inline arrays re-init the table every render, resetting selection/sort/filter state.
- [ ] **`getRowId: (row) => row.id`** set whenever using row selection. Default keys to array index — selection follows the wrong rows after sort/filter.
- [ ] **Function-form accessors include `id`** (`columnHelper.accessor(row => ..., { id: 'x' })`). Required at runtime.
- [ ] **Server-side mode** sets all three (`manualPagination`/`manualSorting`/`manualFiltering`) AND provides `pageCount` / `rowCount` from the API.
- [ ] **Big lists pair with `useVirtualizer`** — don't render thousands of `<tr>`.

## TanStack Form

- [ ] **`<form onSubmit>` calls `e.preventDefault()`** before `form.handleSubmit()` — otherwise full page reload.
- [ ] **`form.handleSubmit()` is `await`ed** if the next step (navigation, toast) depends on submit completing.
- [ ] **`defaultValues` is stable** — not recreated inline each render (resets the form).
- [ ] **Async validators set `onChangeAsyncDebounceMs`** — without it, every keystroke fires a request.
- [ ] **Errors rendered via `errors.map(e => e?.message)`** — not `errors.join(', ')` (issue objects, not strings).
- [ ] **Array fields keyed by stable id**, not array index — reorder/remove corrupts state otherwise.
- [ ] **Cross-field validation at form level**, not on individual fields.

## TanStack Virtual

- [ ] **Inner spacer has `position: relative` and `height: rv.getTotalSize()`.** Rows are `position: absolute` with `transform: translateY(${vi.start}px)`.
- [ ] **Rows using `rv.measureElement` have `data-index={vi.index}`.** Missing attribute → measurements applied to wrong rows.
- [ ] **`estimateSize` within an order of magnitude of reality** — wildly wrong values cause initial scroll-position jumps.
- [ ] **`rv` and `rv.measureElement` NOT in `useEffect`/`useMemo` dep arrays** — new instance each render → infinite loop.
- [ ] **`useWindowVirtualizer` `scrollMargin` measured in `useLayoutEffect`** — reading `ref.current?.offsetTop` inline is `0` on first render.
- [ ] **`rv.measure()` called after data shape changes** that the virtualizer can't detect (column count, conditional rows).

## Review prompts (paste into PR comments)

- "Is `<input>` in the queryKey? If not, refetches will use stale `<input>`."
- "What happens when `<param>` is undefined on first render? Consider `enabled`."
- "This `<Link>` passes `search={{ page: 1 }}` — does that wipe `sort`? Use function form."
- "`getRowId` is missing — selection will be wrong after sort/filter."
- "Server fn throws an Error — does the client see the message or a 500?"
- "`defaultValues` is inline — does the form reset on parent re-render?"

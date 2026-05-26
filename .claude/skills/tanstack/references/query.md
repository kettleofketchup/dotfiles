# TanStack Query v5 (React)

Object-form API only. `cacheTime → gcTime`, `loading → pending`, `keepPreviousData → placeholderData: keepPreviousData`.

## Provider setup

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

export function App({ children }) {
  // useState ensures one client per request on the server, one per tab on the client
  const [qc] = useState(() => new QueryClient({
    defaultOptions: { queries: { staleTime: 60_000 } },
  }))
  return (
    <QueryClientProvider client={qc}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
```

**Never** instantiate `QueryClient` at module scope on the server — it leaks state between requests.

## `queryOptions()` factory (THE pattern)

Single source of truth for key + fn + types. Share across hooks, prefetch, and `setQueryData`.

```ts
import { queryOptions } from '@tanstack/react-query'

export function postOptions(id: number) {
  return queryOptions({
    queryKey: ['posts', id] as const,
    queryFn: ({ signal }) => fetch(`/api/posts/${id}`, { signal }).then(r => r.json()),
    staleTime: 5_000,
  })
}

useQuery(postOptions(1))
useSuspenseQuery(postOptions(1))
useQueries({ queries: [postOptions(1), postOptions(2)] })
queryClient.prefetchQuery(postOptions(1))
queryClient.setQueryData(postOptions(1).queryKey, newPost)
useQuery({ ...postOptions(1), select: (p) => p.title }) // narrow per-component
```

For infinite queries use `infiniteQueryOptions` (same shape).

## Status flags

- `isPending` — no data yet (initial)
- `isFetching` — request in flight (incl. background refetch)
- `isLoading` = `isPending && isFetching`
- `isError`, `isSuccess`
- `fetchStatus`: `'fetching' | 'paused' | 'idle'`

`useSuspenseQuery` returns `data` typed as non-nullable — wrap in `<Suspense>` + `<ErrorBoundary>` (or `QueryErrorResetBoundary` to reset on retry).

## Mutations + optimistic updates

```tsx
const m = useMutation({
  mutationFn: addTodo,
  onMutate: async (vars) => {
    await queryClient.cancelQueries({ queryKey: ['todos'] })
    const prev = queryClient.getQueryData(['todos'])
    queryClient.setQueryData(['todos'], (old: Todo[] = []) => [...old, { id: 'tmp', ...vars }])
    return { prev }  // context for rollback
  },
  onError: (_err, _vars, ctx) => queryClient.setQueryData(['todos'], ctx?.prev),
  onSettled: () => queryClient.invalidateQueries({ queryKey: ['todos'] }),
})
```

## Invalidation

```ts
queryClient.invalidateQueries({ queryKey: ['todos'] })                          // prefix match
queryClient.invalidateQueries({ queryKey: ['todos'], exact: true })
queryClient.invalidateQueries({ predicate: q => q.queryKey[0] === 'todos' })
queryClient.invalidateQueries({ queryKey: ['todos'], refetchType: 'active' })   // 'active'|'inactive'|'all'|'none'
```

## Infinite queries

`initialPageParam` is now **required**:

```tsx
useInfiniteQuery({
  queryKey: ['projects'],
  queryFn: ({ pageParam }) => fetchProjects(pageParam),
  initialPageParam: 0,
  getNextPageParam: (last, all) => last.nextCursor ?? undefined,
  getPreviousPageParam: (first) => first.prevCursor ?? undefined,
})
```

## SSR / hydration

```tsx
// server
const qc = new QueryClient()
await qc.prefetchQuery(postOptions(id))
const dehydratedState = dehydrate(qc)

// client
<HydrationBoundary state={dehydratedState}>
  <Posts />
</HydrationBoundary>
```

With **TanStack Start + Router**, the Router → Query handoff replaces this — see `router.md` (`ensureQueryData` in loaders). The router's dehydration plumbing wires it through automatically.

## v5 removed per-query callbacks

`onSuccess` / `onError` / `onSettled` were **removed from `useQuery`** in v5 (still on `useMutation`). Move side-effects to `useEffect` keyed on `data`/`error`, or into the mutation that triggered the query change. Calling them on `useQuery` is a silent no-op in JS, type error in TS.

## Conditional queries with `enabled`

When the input may be falsy on first render, gate the query and narrow types:

```ts
const id = useParams().id
useQuery({ ...postOptions(id!), enabled: !!id })
```

`signal` forwarding (`queryFn: ({ signal }) => fetch(url, { signal })`) lets Query abort in-flight requests on unmount or queryKey change — always plumb it through.

## Pitfalls

- **Stale closures in `queryFn`** — every input the function reads must be in `queryKey`. Otherwise refetches return stale-input results.
- **Cache collisions** — incomplete keys (e.g. `['post']` for any post) overwrite each other. Always include the discriminator (id, filter, etc.).
- **`keepPreviousData` removed** — use `placeholderData: keepPreviousData` (import the identity helper) and check `isPlaceholderData` to dim stale UI during pagination.
- **`select` recomputes references** — wrap in `useCallback` or use `structuralSharing` to keep referential equality if you depend on `===`.
- **Devtools missing** — must be inside the `QueryClientProvider`. Production builds tree-shake them unless you build for dev.
- **Hydration mismatch** — never module-scope `QueryClient` on the server; use `useState(() => new QueryClient())` on the client and a per-request instance on the server.

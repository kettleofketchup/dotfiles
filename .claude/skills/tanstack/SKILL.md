---
name: tanstack
description: TanStack React — Start (SSR), Query v5, Router (type-safe), Table, Form, Virtual. Use for createServerFn, createFileRoute, queryOptions, headless tables/forms/virtual lists, or TanStack debugging.
---

# TanStack (React)

Reference-only skill. Each library has its own file under `references/`. Load only what's relevant.

## When to load which reference

| User says / file shows | Load |
|---|---|
| `@tanstack/react-start`, `createServerFn`, `vite.config.ts` with `tanstackStart`, server functions, SSR meta-framework, `src/routes/` + API routes | `references/start.md` |
| `useQuery`, `useMutation`, `queryOptions`, `QueryClient`, `useInfiniteQuery`, `useSuspenseQuery`, `HydrationBoundary`, `dehydrate` | `references/query.md` |
| `createFileRoute`, `__root.tsx`, `routeTree.gen.ts`, `validateSearch`, `loader`, `Link to=`, `tanstackRouter` Vite plugin | `references/router.md` |
| `useReactTable`, `getCoreRowModel`, `columnHelper`, `flexRender`, headless table | `references/table.md` |
| `useForm`, `form.Field`, `useStore`, TanStack Form, standard-schema validators | `references/form.md` |
| `useVirtualizer`, `useWindowVirtualizer`, virtual list, big-list rendering | `references/virtual.md` |
| "doesn't refetch", "hydration mismatch", "phantom type error after adding a route", "devtools missing", "stale data" | `references/debugging.md` |
| Reviewing a PR / diff that touches TanStack code, pre-merge bug hunt, "what could go wrong here?", common-bug audit | `references/code-review.md` |

Many real tasks combine refs: Start + Router + Query loaders is the canonical full-stack stack — load all three.

## Key facts that drive everything

- **`@tanstack/start` is dead.** The published package is **`@tanstack/react-start`**. Old guides referencing `app.config.ts` / Vinxi are stale.
- **Config is `vite.config.ts`** — Start projects use `tanstackStart()` (which bundles router-plugin internally) then `viteReact()` then `nitro()`. Router-only (no Start) needs explicit `tanstackRouter()` before `viteReact()`.
- **Server functions use `.inputValidator()`** (renamed from `.validator()`).
- **API routes are regular file routes** with a `server.handlers` object — no more `createAPIFileRoute` / `createServerFileRoute`.
- **Router types only work** with module augmentation: `declare module '@tanstack/react-router' { interface Register { router: typeof router } }`.
- **Query v5 is object-form only.** `cacheTime` → `gcTime`. `keepPreviousData` → `placeholderData: keepPreviousData`. `loading` → `pending`.
- **`queryOptions()` is the unlock** — typed query-option factories share keys/types across `useQuery`, `useSuspenseQuery`, `prefetchQuery`, `setQueryData`, and Router loaders.
- **Router + Query handoff:** put `queryClient` on `createRootRouteWithContext<{ queryClient: QueryClient }>` then call `context.queryClient.ensureQueryData(...)` in route loaders. Set `defaultPreloadStaleTime: 0` on `createRouter` so preloads always hit Query.
- **`routeTree.gen.ts` is generated** — add to ESLint/Prettier ignore and IDE readonly lists; regenerate by saving any route file with the Vite plugin running.

## Workflow guidance

1. Identify which libraries the user is actually touching — don't load all references reflexively.
2. For new code, prefer current v5 / Vite-plugin syntax over examples from older blog posts. If unsure, check `references/start.md` for the verified `vite.config.ts` shape.
3. Surface common pitfalls early — most TanStack bugs are the same 5–6 patterns documented in `references/debugging.md` (especially: missing `queryKey` deps, missing module augmentation, search params read in loader instead of `loaderDeps`, server-scope `QueryClient`).
4. When proposing examples, run `Read` on the project's actual `vite.config.ts` and `package.json` first — the ecosystem moves fast and the user's lockfile is the source of truth for which API to use.
5. **Before writing TanStack code**, scan `references/code-review.md` for the relevant section so the first draft already avoids the top bugs (missing `queryKey` deps, missing module augmentation, object-form `search` wipes, missing `getRowId`, etc.). **When reviewing TanStack code**, load `code-review.md` and walk the checklist for each library the diff touches.

## Official docs (verify current syntax here)

- Start: <https://tanstack.com/start/latest/docs/framework/react/overview>
- Query: <https://tanstack.com/query/latest/docs/framework/react/overview>
- Router: <https://tanstack.com/router/latest/docs/framework/react/overview>
- Table: <https://tanstack.com/table/latest/docs/framework/react/guide/introduction>
- Form: <https://tanstack.com/form/latest/docs/framework/react/quick-start>
- Virtual: <https://tanstack.com/virtual/latest/docs/framework/react/react-virtual>

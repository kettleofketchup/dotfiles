---
paths:
  - "**/*.tsx"
  - "**/*.jsx"
  - "**/components/**/*"
---

# React Component Development

When creating or modifying React components, apply these skills:
- **react** - React 19 patterns, hooks, Server Components, Suspense, async components
- **ui-styling** - shadcn/ui components, Tailwind, theming, forms

## Using shadcn/ui

Use shadcn/ui primitives **directly** in pages and features — that is the default.
Prefer built-in variants/sizes over custom styling.

```tsx
import { Button } from "@/components/ui/button"
<Button variant="destructive" onClick={onDelete}>Delete</Button>
```

Only extract a wrapper in `components/custom/` when multiple call sites share the
same non-trivial behavior (e.g. a button that always renders a loading spinner).
Don't wrap by default.

## React 19 Patterns

### Hooks Priority
- `use()` for promises/context
- `useOptimistic()` for optimistic updates
- `useActionState()` for form actions
- `useTransition()` for non-blocking updates

### Data Fetching
```tsx
// Prefer: useSuspenseQuery with Suspense boundary
<Suspense fallback={<Skeleton />}>
  <DataComponent />
</Suspense>

// Inside component
const { data } = useSuspenseQuery({ queryKey: ['data'], queryFn })
```

### Server vs Client
- Default to Server Components (no 'use client')
- Add 'use client' only for: useState, useEffect, event handlers, browser APIs

## Mobile-First Styling

- Base styles (no prefix) = mobile
- Add `sm:`, `md:`, `lg:` for larger viewports
- Use `min-h-11` (44px) for touch targets

## Reference Skills

Invoke for detailed patterns:
- **react** - Hooks, Server Components, async patterns, TanStack Query
- **ui-styling** - CVA variants, form integration, compound components

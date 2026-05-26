# TanStack Virtual (React)

Headless virtualization. Renders only what's visible — handles 10k+ rows without dying.

## Install

```bash
pnpm add @tanstack/react-virtual
```

## Vertical list (fixed scrollElement)

```tsx
import { useVirtualizer } from '@tanstack/react-virtual'
import { useRef } from 'react'

function Rows({ items }: { items: string[] }) {
  const parentRef = useRef<HTMLDivElement>(null)

  const rv = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 40,           // px per row (estimate ok for dynamic)
    overscan: 5,                      // render N extra above/below viewport
  })

  return (
    <div ref={parentRef} style={{ height: 600, overflow: 'auto' }}>
      <div style={{ height: rv.getTotalSize(), position: 'relative' }}>
        {rv.getVirtualItems().map((vi) => (
          <div
            key={vi.key}
            data-index={vi.index}
            ref={rv.measureElement}      // for dynamic sizing
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${vi.start}px)`,
            }}
          >
            {items[vi.index]}
          </div>
        ))}
      </div>
    </div>
  )
}
```

Critical: the inner spacer div must be `position: relative` with the calculated `height: rv.getTotalSize()`. Each row is `position: absolute` with a `transform: translateY(...)`.

## Window-scrolled list

When the page itself scrolls (no internal scroll container):

```tsx
import { useWindowVirtualizer } from '@tanstack/react-virtual'

const parentRef = useRef<HTMLDivElement>(null)
const [scrollMargin, setScrollMargin] = useState(0)

useLayoutEffect(() => {
  if (parentRef.current) setScrollMargin(parentRef.current.offsetTop)
}, [])

const rv = useWindowVirtualizer({
  count: items.length,
  estimateSize: () => 80,
  overscan: 5,
  scrollMargin,  // offset of list start from page top
})
// Apply transform: translateY(${vi.start - scrollMargin}px) to each row
```

Reading `parentRef.current?.offsetTop` inline returns `0` on first render (ref not attached yet) and never updates — measure in `useLayoutEffect`.

## Dynamic sizing (`measureElement`)

Attach `ref={rv.measureElement}` to the rendered row element — TanStack Virtual will read its size after layout and stash actual measurements. `estimateSize` only matters for the initial render and unmeasured rows.

```tsx
<div ref={rv.measureElement} data-index={vi.index}>{...}</div>
```

The `data-index` attribute is **required** when using `measureElement` so the virtualizer knows which row was measured.

## Horizontal

```tsx
useVirtualizer({
  horizontal: true,
  count, getScrollElement, estimateSize, overscan,
})
// row.start is now an X offset → use transform: translateX(...)
```

## Grid (2D)

Two virtualizers — one row, one column — composed:

```tsx
const rowV = useVirtualizer({ count: rowCount, getScrollElement, estimateSize: () => 40, overscan: 5 })
const colV = useVirtualizer({ horizontal: true, count: colCount, getScrollElement, estimateSize: () => 100, overscan: 5 })

return (
  <div ref={parentRef} style={{ height: 600, width: 800, overflow: 'auto' }}>
    <div style={{ height: rowV.getTotalSize(), width: colV.getTotalSize(), position: 'relative' }}>
      {rowV.getVirtualItems().map(row =>
        colV.getVirtualItems().map(col => (
          <div key={`${row.key}-${col.key}`} style={{
            position: 'absolute',
            top: 0, left: 0,
            width: col.size, height: row.size,
            transform: `translateX(${col.start}px) translateY(${row.start}px)`,
          }}>
            {cells[row.index][col.index]}
          </div>
        ))
      )}
    </div>
  </div>
)
```

## Scroll-to APIs

```ts
rv.scrollToIndex(42, { align: 'start' })   // 'start' | 'center' | 'end' | 'auto'
rv.scrollToOffset(1000)
rv.scrollBy(100)
```

## Pairing with TanStack Table

Render `table.getRowModel().rows[vi.index]` inside the virtual loop instead of `data[vi.index]`. Table provides the row model; Virtual provides the windowing. Set table.options.getCoreRowModel to `getCoreRowModel()` and render via `<tr>` with absolute positioning.

## Pitfalls

- **`getScrollElement` returns `null` on first render** — that's fine; the virtualizer waits. Just ensure the ref is attached.
- **Missing `data-index`** when using `measureElement` → measurements applied to wrong rows → jumpy scrolling.
- **Wrong `estimateSize`** by an order of magnitude → initial scroll position wildly off, then snaps after measurement.
- **`overscan: 0`** → flashes of blank during fast scroll. Default `5` is sane; bump to `10–20` for heavy rows.
- **`position` not set** on the inner container → all rows pile at top.
- **Conditional render that changes `count` mid-scroll** without `rv.measure()` → stale measurements. Call `rv.measure()` after data shape changes.
- **`useVirtualizer` returns a new object each render** — don't put `rv` or `rv.measureElement` into `useEffect`/`useMemo` dep arrays. Infinite loops. If you need to react to virtualizer changes, depend on `rv.range` or a stable slice instead.

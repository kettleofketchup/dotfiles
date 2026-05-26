# TanStack Table v8 (headless)

Headless: no markup, no styles. Library gives you a row/column model; you render.

## Install

```bash
pnpm add @tanstack/react-table
```

## Minimal table

```tsx
import { createColumnHelper, flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table'

type Person = { id: number; name: string; age: number }
const columnHelper = createColumnHelper<Person>()

const columns = [
  columnHelper.accessor('name', { header: 'Name', cell: (info) => info.getValue() }),
  columnHelper.accessor('age', { header: 'Age', cell: (info) => info.getValue() }),
  columnHelper.display({ id: 'actions', cell: ({ row }) => <button onClick={() => onEdit(row.original)}>Edit</button> }),
]

function PeopleTable({ data }: { data: Person[] }) {
  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() })
  return (
    <table>
      <thead>
        {table.getHeaderGroups().map(hg => (
          <tr key={hg.id}>{hg.headers.map(h => (
            <th key={h.id}>{h.isPlaceholder ? null : flexRender(h.column.columnDef.header, h.getContext())}</th>
          ))}</tr>
        ))}
      </thead>
      <tbody>
        {table.getRowModel().rows.map(row => (
          <tr key={row.id}>{row.getVisibleCells().map(cell => (
            <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
          ))}</tr>
        ))}
      </tbody>
    </table>
  )
}
```

## Sorting

```tsx
import { getSortedRowModel, type SortingState } from '@tanstack/react-table'

const [sorting, setSorting] = useState<SortingState>([])
const table = useReactTable({
  data, columns,
  state: { sorting },
  onSortingChange: setSorting,
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
})

// In header cell:
<th onClick={h.column.getToggleSortingHandler()}>
  {flexRender(h.column.columnDef.header, h.getContext())}
  {{ asc: ' ↑', desc: ' ↓' }[h.column.getIsSorted() as string] ?? null}
</th>
```

## Pagination

Client-side: add `getPaginationRowModel: getPaginationRowModel()` and optionally `initialState: { pagination: { pageSize: 25 } }`. Controls: `table.previousPage() / nextPage()`, `table.getState().pagination.pageIndex`, `table.getPageCount()`.

Server-side: set `manualPagination: true`, pass `pageCount` from server, manage `pagination` state externally via `state` + `onPaginationChange`. Same `manualSorting` / `manualFiltering` flags. Pair with Query: `useQuery(tableDataOptions(pagination, sorting))`.

## Filtering

```tsx
import { getFilteredRowModel } from '@tanstack/react-table'

const [columnFilters, setColumnFilters] = useState([])
useReactTable({
  state: { columnFilters },
  onColumnFiltersChange: setColumnFilters,
  getFilteredRowModel: getFilteredRowModel(),
  ...rest,
})
// Per-column: column.getFilterValue() / column.setFilterValue('foo')
// Global:     state: { globalFilter }, onGlobalFilterChange, globalFilterFn: 'includesString'
```

## Row selection

```tsx
import type { RowSelectionState } from '@tanstack/react-table'

const [rowSelection, setRowSelection] = useState<RowSelectionState>({})
useReactTable({
  state: { rowSelection },
  onRowSelectionChange: setRowSelection,
  enableRowSelection: true,           // or per-row predicate
  getRowId: (row) => row.id,          // CRITICAL: without this, selection keys to array index and breaks on sort/filter
  ...rest,
})

// Checkbox column:
columnHelper.display({
  id: 'select',
  header: ({ table }) => (
    <input type="checkbox"
      checked={table.getIsAllRowsSelected()}
      onChange={table.getToggleAllRowsSelectedHandler()} />
  ),
  cell: ({ row }) => (
    <input type="checkbox"
      checked={row.getIsSelected()}
      disabled={!row.getCanSelect()}
      onChange={row.getToggleSelectedHandler()} />
  ),
})

table.getSelectedRowModel().rows.map(r => r.original)
```

## Column definitions cheatsheet

```tsx
columnHelper.accessor('email', {...})              // by key
columnHelper.accessor(row => row.user.email, {     // by accessor fn
  id: 'email', ...                                 // id REQUIRED for fn accessor
})
columnHelper.display({ id: 'actions', cell: ... }) // no data
columnHelper.group({ id: 'name', header: 'Name', columns: [first, last] })  // nested headers
```

Cell options: `cell`, `header`, `footer`, `meta`, `enableSorting`, `enableHiding`, `size`, `minSize`, `maxSize`, `filterFn`, `sortingFn`.

## Pitfalls

- **`data` reference identity** — every render with a new `data` array triggers re-derive. Memoize with `useMemo(() => fetched ?? [], [fetched])`.
- **`columns` array re-creates** — define outside the component or `useMemo`. Otherwise the table reinitializes selection/sorting/filters on every render.
- **Accessor by function needs `id`** — TS won't always catch this; runtime error is "ColumnDef must have an id".
- **Server-side mode** — must set `manualPagination`/`manualSorting`/`manualFiltering` AND provide totals (`pageCount`, `rowCount`) for pagination controls to work.
- **Virtualization** — Table v8 is row-model only; pair with `useVirtualizer` (see `virtual.md`) for big lists. Don't render all rows.

# TanStack Form v1 (React)

Headless, type-safe forms. Supports standard-schema validators (Zod v4, Valibot, Arktype).

## Install

```bash
pnpm add @tanstack/react-form zod
```

## Minimal form

```tsx
import { useForm } from '@tanstack/react-form'
import { z } from 'zod'

function SignupForm() {
  const form = useForm({
    defaultValues: { email: '', password: '' },
    onSubmit: async ({ value }) => { await api.signup(value) },
  })

  return (
    <form onSubmit={(e) => { e.preventDefault(); e.stopPropagation(); form.handleSubmit() }}>
      <form.Field
        name="email"
        validators={{ onChange: z.string().email() }}
        children={(field) => (
          <>
            <input
              name={field.name}
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(e) => field.handleChange(e.target.value)}
            />
            {field.state.meta.errors.length ? <em>{field.state.meta.errors.map(e => e?.message ?? String(e)).join(', ')}</em> : null}
          </>
        )}
      />
      <form.Subscribe
        selector={(s) => [s.canSubmit, s.isSubmitting]}
        children={([canSubmit, isSubmitting]) => (
          <button type="submit" disabled={!canSubmit}>{isSubmitting ? 'Submitting…' : 'Submit'}</button>
        )}
      />
    </form>
  )
}
```

## Validators

```tsx
validators: {
  onChange: z.string().min(3),
  onBlur: z.string().email(),
  onChangeAsync: async ({ value }) => {
    const taken = await api.isUsernameTaken(value)
    return taken ? 'Username taken' : undefined
  },
  onChangeAsyncDebounceMs: 300,
}
```

Validators run at the level they're declared on (field or form). Form-level validators get full `values`:

```tsx
const form = useForm({
  defaultValues: { password: '', confirm: '' },
  validators: {
    onChange: ({ value }) => value.password === value.confirm ? undefined : 'Passwords must match',
  },
})
```

## Whole-form schema

```tsx
const schema = z.object({ email: z.string().email(), password: z.string().min(8) })
const form = useForm({ defaultValues: { email: '', password: '' }, validators: { onSubmit: schema } })
```

Per-field validators take precedence for that field.

## Subscriptions / partial reads

`form.Subscribe` (or `useStore`) lets components read narrow slices without re-rendering on every keystroke:

```tsx
import { useStore } from '@tanstack/react-form'

const isValid = useStore(form.store, (s) => s.isValid)
```

Inside `<form.Field>`, `field.state` is already scoped — that subtree is the only one that re-renders on the field change.

## Array fields

```tsx
<form.Field name="todos" mode="array">
  {(field) => (
    <>
      {field.state.value.map((_, i) => (
        <form.Field key={i} name={`todos[${i}].text`}>
          {(sub) => <input value={sub.state.value} onChange={e => sub.handleChange(e.target.value)} />}
        </form.Field>
      ))}
      <button type="button" onClick={() => field.pushValue({ text: '' })}>Add</button>
    </>
  )}
</form.Field>
```

Array helpers: `pushValue`, `insertValue(i, v)`, `removeValue(i)`, `swapValues(i, j)`, `moveValue(from, to)`.

## Submit state

`form.state`: `canSubmit`, `isSubmitting`, `isValid`, `isDirty`, `submissionAttempts`, `errorMap`. Reset via `form.reset()` (defaults) or `field.reset()` (single field). If `onSubmit` throws, `state.errorMap.onSubmit` populates.

## TanStack Start integration (server validation)

```tsx
const submit = createServerFn({ method: 'POST' })
  .inputValidator(schema)
  .handler(async ({ data }) => { /* save */ })

const form = useForm({
  defaultValues,
  onSubmit: async ({ value }) => submit({ data: value }),
})
```

Server-only errors can be surfaced by throwing and catching in a top-level `try/catch` inside `onSubmit`, then calling `form.setErrorMap({ onSubmit: ... })`.

## Pitfalls

- **Forgetting `e.preventDefault()`** in the `<form onSubmit>` handler → full page reload.
- **Putting validators on the `form.Field` element vs the `useForm` options** — both work, but field-level runs only when that field changes. Cross-field validation must live at form level.
- **Async validators without debounce** → request storms. Always set `onChangeAsyncDebounceMs`.
- **Re-creating `defaultValues` inline** triggers form resets; memoize or pass a stable object.
- **`<form.Field>` `name` is a typed string path** (e.g. `'address.street'`, `'items[0].qty'`). Typos surface as type errors only if you've enabled strict TS.
- **`field.state.meta.errors` are issue objects** (with `.message`, `.path`) when using Zod/Valibot/Arktype — calling `.join(', ')` renders `[object Object]`. Map to `e.message` first.
- **Array field keys** — using `key={i}` corrupts component state on reorder/remove. Generate stable ids (`crypto.randomUUID()` on push) and key by id.
- **`form.handleSubmit()` is async** — `await` it if the next step (navigation, redirect, toast) depends on submit completing.

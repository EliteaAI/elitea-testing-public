---
name: Shared field-render component testid must be field-conditional
description: Adding a testid to a shared component's helperText/error slot without a field check leaks it onto every field instance that renders that slot
type: feedback
---

## The trap (ELITEA-2337, `EditSecretInputGridTable.jsx`)

`EditSecretInputGridTable` is ONE component instantiated per grid field —
called once for `field === 'name'` and once for `field === 'value'`. Its
`helperText` prop renders for BOTH instances: name-validation errors (only
for `name`) AND the shared character-limit warning (`isAtCharacterLimit`,
which applies to *either* field regardless of `field`).

Naively wrapping the existing `helperText` value in a testid span —
`<span data-testid="secret-name-error">{helperText}</span>` — as the AFS's
literal Concrete Handles suggestion showed, would apply the
`secret-name-error` testid to the VALUE field's character-limit message too,
mislabeling it. Fixed by conditioning the testid on the field:

```jsx
helperText={
  helperText ? (
    <span data-testid={field === 'name' ? 'secret-name-error' : undefined}>{helperText}</span>
  ) : null
}
```

**Rule of thumb:** before wiring a testid into any prop of a component that
is instantiated multiple times with different roles (via a `field`/`type`/
`variant` discriminator prop), check whether that prop's rendered content is
shared across roles. If it is, condition the testid on the discriminator —
otherwise the same testid silently binds to two semantically different
elements. Same shape as the `#277`/PR #581 same-element-conditional-pair
rulings in `.agents/testing.md` § Locator policy, but one level removed: here
the conditional is on WHICH instance gets the testid at all, not on which of
two mutually-exclusive JSX branches within one instance.

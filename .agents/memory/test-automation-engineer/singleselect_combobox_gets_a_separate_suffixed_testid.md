---
name: SingleSelect's data-testid lands on the FormControl root, not the combobox
description: shared/ui/select/SingleSelect.jsx puts data-testid on <Select> (root wrapper), and a SEPARATE "${dataTestId}-combobox" testid on the role=combobox display element via SelectDisplayProps — the base testid resolves to a DIV with role=None, not the interactive combobox.
type: feedback
---

## Rule

`EliteaUI/src/[fsd]/shared/ui/select/SingleSelect.jsx` (`renderSelectComponent`):

```jsx
<Select
  data-testid={dataTestId}
  SelectDisplayProps={dataTestId ? { 'data-testid': `${dataTestId}-combobox` } : undefined}
  ...
/>
```

So a field wired with `LocatorDescriptor(testid="x")` resolves to the outer
`<Select>` root (a `div`, `role=None`) — clicking it DOES open the dropdown
(the click propagates to the inner display element), so `select_*`/`open_*`
methods built the normal way work fine. But if a test needs to assert the
field's DOM **identity** is specifically a MUI Select combobox (not just
"some non-textarea element" — e.g. distinguishing a `SimpleLLMInputItem`
Value field's Fixed/F-String `<textarea>` from its Variable-mode Select), the
base testid's `role` attribute reads `None`, not `"combobox"`. The real
`role="combobox"` element is a DIFFERENT node with testid `f"{base}-combobox"`.

- **To assert "this field is a Select", locate the `-combobox`-suffixed
  testid**, not the base one. Build it via a class-level template constant
  (same mechanism as `SELECT_OPTION`): `'[data-testid="{}-combobox"]'.format(base_testid)`.
- **To just detect a widget swap** (e.g. Fixed/F-String -> Variable), checking
  `tag_name != "TEXTAREA"` on the base-testid element is enough — no need for
  the combobox locator unless you need the specific "it's a Select" proof.
- Get the base testid string (not the resolved Locator) from a
  `LocatorDescriptor` via **class-level** access: `getattr(type(self), field_name).testid`
  — instance-level access (`getattr(self, field_name)`) invokes `__get__` and
  returns the already-resolved `Locator`, not the descriptor.

## Seen 1× (ELITEA-2040)

`SimpleLLMInputItem.jsx`'s LLM-node Value field, Variable mode.

See also: testid_lands_on_mui_wrapper_not_input.md (same family — MUI puts
`data-testid` where it wants, not where the caller's mental model expects).

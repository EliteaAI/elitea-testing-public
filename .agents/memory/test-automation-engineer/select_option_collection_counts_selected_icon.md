---
name: SingleSelect option-row collections over-count by one
description: A bare [data-testid^="select-option-"] collection counts the nested selected-icon; filter with [data-selected]
type: feedback
aliases: [select-option, SingleSelect, option count, select-option-selected-icon, data-selected]
tags: [area/locators, area/elitea-ui]
created: 2026-08-29
updated: 2026-08-29
---

## The trap

`SingleSelectMenuItem.jsx` (EliteaUI `src/[fsd]/shared/ui/select/`) renders, **inside the
currently selected option row**, a `<ListItemIcon data-testid="select-option-selected-icon">`.
A collection built as `[data-testid^="select-option-"]` therefore counts **N+1** elements
whenever any option is selected — which is always for a value-bearing select.

## The fix

Filter on the attribute only the MenuItem rows carry:

```python
SELECT_OPTION_ANY = '[data-testid^="select-option-"][data-selected]'
```

`data-selected` is `"true"` / `"false"` on the row (`SingleSelectMenuItem.jsx:118`) — so it
also doubles as the *selection state* handle. Note it is **`data-selected`, not
`aria-selected`**; asserting the latter fails.

Both facts hit an exact-count assertion (`to_have_count(7)`), which is the assertion shape
worth having — a presence-only check would have passed over the extra element silently.

Related: [[persona_management_has_no_header_testid]]

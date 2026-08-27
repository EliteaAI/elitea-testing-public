---
name: select-option prefix counts the selected-icon too
description: Counting SingleSelect options by testid prefix overcounts by 1 — the selected option carries select-option-selected-icon
type: feedback
aliases: [select-option-selected-icon, SingleSelect option count, select option prefix overcount]
tags: [area/locators, area/mui]
created: 2026-08-27
updated: 2026-08-27
---

## The fact

EliteaUI's shared `SingleSelectMenuItem.jsx` renders the option testid as
``data-testid={option.testId ?? `select-option-${option.value}`}`` (line 117) **and**, inside
whichever option is currently selected, a check mark with a static
`data-testid="select-option-selected-icon"` (line 141).

So a bare `[data-testid^="select-option-"]` count returns **N + 1** for an N-option select.
Measured live 2026-08-27 on the create-personal-token expiration-unit select: 6 for 5 options,
which failed an "exactly 5 options" assertion on the first run.

## The compliant shape

```python
EXPIRATION_MEASURE_OPTION_PREFIX_SELECTOR = (
    '[data-testid^="select-option-"]:not([data-testid="select-option-selected-icon"])'
)
```

Both halves are literal `[data-testid=` selectors, so it passes the reviewer's mechanical
locator grep. This is app-wide: ANY case counting options of ANY `SingleSelect` hits it.
`PopoverSelect.jsx:109` composes the same option testid, so check there too.

Related: [[personal_tokens_table_unmounts_during_refetch]]

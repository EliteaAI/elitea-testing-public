---
name: SingleSelect multi-value chip testids
description: Every `multiple` SingleSelect on Elitea now exposes select-value-chip-<value> and -remove — read/remove a chosen chip without new plumbing
type: reference
aliases: [chip testid, multi-select chip, select-value-chip, remove chip x]
tags: [area/elitea-ui, type/handle]
created: 2026-08-29
updated: 2026-08-29
---

## The handles

`EliteaUI/src/[fsd]/shared/ui/select/SingleSelect.jsx`'s `renderMultipleValue`
had NO testid of any kind, so no test could read or remove a selected chip in
ANY `multiple` select on the product. Added 2026-08-29
(EliteaAI/EliteaUI@65194eb1, for ELITEA-2302) as a **generic** shared-component
mechanism mirroring `select-option-${option.value}` in `SingleSelectMenuItem.jsx`:

```
select-value-chip-<value>          on the MUI Chip
select-value-chip-<value>-remove   on its deleteIcon (the x)
```

Works in the Users Invite dialog, the row/header Edit-roles dialogs, and every
other `multiple` select. **Check for it before proposing new chip plumbing.**

## The counting trap (same family as the option one)

A bare `[data-testid^="select-value-chip-"]` count DOUBLES, because each chip's
remove icon matches the prefix too. Use the exclusion form —
`AdminUsersPage.SELECT_VALUE_CHIP_ANY_SELECTOR`:

```python
'[data-testid^="select-value-chip-"]:not([data-testid$="-remove"])'
```

Exactly the trap `ROLE_OPTION_ANY_SELECTOR` documents for
`select-option-selected-icon`.

Related: [[row_edit_roles_dialog_save_gates]]

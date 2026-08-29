---
name: Row Edit-roles dialog — Save has two independent disable gates
description: EditUserRolesDialog Save is disabled on empty set AND on unchanged set — a read-only visit is non-destructive by construction
type: reference
aliases: [edit roles save disabled, users edit roles dialog, hasChangedRoles]
tags: [area/settings-users, type/behaviour]
created: 2026-08-29
updated: 2026-08-29
---

## Two gates, not one

`EliteaUI/src/components/EditUserRolesDialog.jsx`:

```jsx
disabled={!selectedRoles.length || !hasChangedRoles}
```

- `!selectedRoles.length` — an EMPTY role set can never be saved. So removing
  the only chip via its x leaves Save **still disabled** (verified live
  2026-08-29, ELITEA-2302).
- `!hasChangedRoles` — a sorted-JSON compare against the user's original roles.
  So a dialog opened purely to READ is non-destructive by construction; a
  layout/read-only case needs no cleanup.

## Row vs header instance

`EditUsersButton` picks `useEditUser` for the ROW instance and
`useBatchEditUsers` for the HEADER one. Same endpoint
(`PUT /api/v2/admin/users/default/{projectId}`, 200) but different bodies:
row `{id, roles}`, header `{ids, roles}`. The header flow's
`{"msg": "roles updated"}` body assertion was NOT re-verified for the row flow —
assert status + refetch there, not that body.

Role column renders multiple roles **comma-joined** (`"editor, admin"`) —
compare as a set after splitting; backend order is not part of any contract.

Related: [[singleselect_multi_value_chip_testids]]

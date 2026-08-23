---
name: Testid provenance grep — false "not on main" rows
description: The closure-record two-stage testid grep silently drops ternary- and key:-wired testids; read the hits instead of filtering them.
type: feedback
aliases: [testid provenance, closure record grep, not on main false negative, data-testid grep]
tags: [area/automation, type/gotcha]
created: 2026-08-21
updated: 2026-08-22
---

## What happens

`.agents/workflow.md` § Closure record's two-stage check —
`git grep -- "$t" origin/main -- src/ | grep -qiE '(data-testid|testid[[:space:]]*[:=])'` —
reports **no** for testids whose wiring line carries neither token, even though stage 1 found
the string and the handle works live. Confirmed 2026-08-21 (ELITEA-1834 analysis) on three
EliteaUI handles:

| Handle | Wiring line that stage 2 drops |
|---|---|
| `artifacts-file-row` / `artifacts-folder-row` | `ArtifactTable.jsx:525` — `row.type === ARTIFACT_TYPES.FOLDER ? 'artifacts-folder-row' : 'artifacts-file-row'` |
| `bucket-menu-upload-files-menuitem` | `BucketItem.jsx:153` — `key: 'bucket-menu-upload-files'`, later `+ '-menuitem'` by `DotMenu.jsx:57` |
| `bucket-menu-{name}-menu-button` | never appears whole in source — `DotMenu.jsx:354` composes `` `${id}-menu-button` `` (stage 1 can't see it either; workflow.md already warns about this class) |
| `secret-column-header-{name,secretValue,actions}` | `SecretsTable.jsx:563` — `columnTestIdPrefix="secret"`; stage 2 drops it because the token is `TestIdPrefix=`, i.e. `testid` is NOT followed by `:`/`=`. `GridTableHeader.jsx:48` then composes `` `${columnTestIdPrefix}-column-header-${column.field}` ``, so stage 1 misses it too. Same shape for every `columnTestIdPrefix` consumer (TokensTable, UsersTable, DataTable, ArtifactTable). Confirmed 2026-08-22, ELITEA-1969 review |

## Why it matters

A false "not on main" row makes a case look non-promotable and invents a human cherry-pick
that isn't needed — the exact failure mode (#19) the fetch rule was added to prevent, just
from the other direction.

## What to do

When a handle you have **used live** reports absent, read the hits instead of counting them:
`git grep -- "$t" origin/main -- src/` and look at the line. For a DotMenu-composed testid,
grep the composing template (`-menu-button`, `-menuitem`) plus the `id`/`key` that feeds it.

Related: [[project_briefing]]

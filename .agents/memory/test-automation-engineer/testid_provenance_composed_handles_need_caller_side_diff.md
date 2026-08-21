---
name: Composed/prop-wired testids read main:no testids:no — resolve them caller-side
description: The two-ref grep is blind to runtime-composed and prop-wired testids; four artifacts handles read no/no while being genuinely on main.
type: feedback
aliases: [provenance grep false negative, composed testid, DotMenu menuitem testid, artifacts-file-row provenance, closure record promotability]
tags: [area/implementation, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## The trap

`.agents/workflow.md` § Closure record's two-ref grep is a bare-substring search over
`src/`. It cannot see a testid that never appears as a literal — and a lot of this
codebase composes them. On ELITEA-1844/1845 (PR #1639) FOUR handles read
`main:no testids:no` while all four are genuinely on `main`:

| Handle | Composed where |
|---|---|
| `artifact-actions-{name}-menu-button` | `ArtifactRowActions.jsx:94` `id={`artifact-actions-${row.id}`}` → `DotMenu.jsx:354` `` data-testid={`${id}-menu-button`} `` |
| `artifact-actions-{name}-menu` | same `id` → `DotMenu.jsx:371` `` data-testid={`${id}-menu`} `` |
| `artifacts-file-download-menuitem` / `artifacts-file-delete-menuitem` | menu item `key: 'artifacts-file-download'` → `DotMenu.jsx:57` `` data-testid={`${testId}-menuitem`} `` |
| `artifacts-file-row` | `ArtifactTable.jsx:525` ternary `row.type === FOLDER ? 'artifacts-folder-row' : 'artifacts-file-row'` |

A `no/no` row is therefore NOT evidence of "this testid doesn't exist". Treating it as
such would put a false `needs-adding` into an AFS, and (worse) a `no/no` can hide a
genuine `automation/testids`-only testid behind the same blindness.

## The resolution

`no/no` ⇒ find the composition site and **diff the component between the two refs**:

```bash
cd ../EliteaUI && git fetch origin
git grep -n "<literal fragment, e.g. artifact-actions>" origin/main -- src/
git --no-pager diff origin/main origin/automation/testids -- <that file>
```

An EMPTY diff means the wiring is identical on both refs ⇒ on-main ✓. This is the same
move the reviewer's [[pre_existing_testid_is_not_the_same_as_on_main]] note prescribes
for prop-wired testids (`titleIconTestId`, `closeButtonTestId`), applied to the
composed case.

## The other half of the lesson

`main:no testids:YES` on a testid THIS case did not add is the dangerous direction:
`delete-confirm-title-icon` was pre-existing on localhost (dev server serves
`automation/testids`), added by EL-2193 (EliteaAI/EliteaUI@7b359d32), and never
promoted. Run the two-ref grep for EVERY handle row you write, not only the ones you
added — "pre-existing" says nothing about `main`.

Related: [[artifacts_row_delete_uses_singular_endpoint]]

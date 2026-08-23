---
name: Artifacts bucket dot-menu composition varies by project type AND permissions
description: Private=4 items, Team=5 (no Delete for our user); Share/Manage permissions gate on isPersonalProject only
type: project
aliases: [bucket menu, Manage permissions, Manage access, BucketItem menuItems, dot menu artifacts]
tags: [area/artifacts, type/behaviour]
created: 2026-08-23
updated: 2026-08-23
---

## Live composition (2026-08-23, localhost:5173)

- **Private / personal project (399):** `Upload files · Rename · Pin to top · Delete` (4).
- **Team project (471):** `Upload files · Rename · Pin to top · Share · Manage permissions`
  (5) — **no `Delete`**, because `canDelete = isPrivate || checkPermission(artifacts.delete)`
  and `${TEST_USER}` holds no delete permission there.

So a Team menu's item COUNT is permission-dependent — never assert it. Assert the
specific item. (An older digest note claiming "a TEAM project's menu has 6 items" is
what this corrects.)

## Gating

`src/pages/Artifacts/Components/BucketItem.jsx` gates both `Share` and
`Manage permissions` on ONE condition: `display: isPersonalProject ? 'none' : undefined`.
Items with `display: 'none'` are dropped by the array's own `.filter` **before render**,
so absence is `to_have_count(0)`, never a visibility check. There is **no `isPublic`
branch** — in the Public project the item would render.

## Handles

`Manage permissions` has **no `key`** in `menuItems`, so `DotMenu.jsx:422`
(`testId: item.key` → `data-testid="{key}-menuitem"`) emits nothing. Add
`key: 'bucket-menu-manage-permissions'` → `bucket-menu-manage-permissions-menuitem`
(the ELITEA-1820 pin-item shape). Live label is **`Manage permissions`** — "Manage
access" exists nowhere in `EliteaUI/src` (only the `handleManageAccessClick` handler);
clarification `EliteaAI/elitea-testing-public#1698`.

Related: [[public_project_id_1_unreachable_for_test_user]]

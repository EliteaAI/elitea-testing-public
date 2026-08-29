---
name: Users batch delete leaves the page in a render loop
description: After a header batch-delete on Settings → Users the table never recovers — assert post-reload, never in place
type: project
aliases: [batch delete users, users header delete, 1974, DeleteUserButton render loop]
tags: [area/settings-users, type/product-defect]
created: 2026-08-29
updated: 2026-08-29
---

## What happens

Confirming a batch delete (row checkboxes → header trash → Delete) on
Settings → Users leaves the page in an unbounded React re-render loop —
`Maximum update depth exceeded` at `DeleteUserButton.jsx:30`, thousands of
console lines, table stuck at **0 rows** until a page reload. Tracked as
**#1974**; the singular-toast symptom of the same effect is **#1975**.

Cause is structural: the success `useEffect` calls `setSelectedUsers([])` while
`users` sits in its own dependency array, so a fresh array identity re-triggers
it forever. The PER-ROW delete escapes it only because its row unmounts when
the refetch removes it, which breaks the cycle.

## What it means for a spec

- No locator assertion after a batch-delete confirm can be trusted until a
  reload. Assert the in-place recovery `expect.soft()` + `# Known defect: #1974`
  (the visible red), then reload and assert the data truth hard.
- A console-error assertion on that flow is pure noise — thousands of errors
  from one defect. Omit it and say why in the docstring.
- Deterministic: byte-identical signature across invocations
  (`Locator expected to have count 'N' / Actual value: 0`), `reruns.json == {}`.

Related: [[settings_users_delete_flow_handles]]

---
name: Dynamic-testid promotability check needs a 3-hop trace, not 1
description: A bare literal grep for a DotMenu-composed testid (either half — trigger button or menu item) can false-negative even when the closure record's claim is true; trace the id/key prop fragment through the component before concluding "absent"
type: feedback
---

On #150/ELITEA-1892 (control-audit pass), a bare literal grep for
`agent-actions-menu-button` and `delete-agent-menuitem` came back false-negative
on **both** `origin/main` and `origin/automation/testids` in EliteaUI, even though
the closure record correctly claimed both were pre-existing and already promoted.

**Root cause:** EliteaUI's shared `DotMenu.jsx` composes testids two different
dynamic ways depending on which part of the component:

- The trigger button, via an `id` prop: `data-testid={id ? \`${id}-menu-button\` : undefined}`
- Each menu item, via a `testId` prop — itself sourced from the item's `key` field
  one file away (`testId: item.key` in the array-building hook) — composing to
  `${testId}-menuitem`

So verifying one of these testids requires a **3-hop trace**, not a 1-hop grep:

1. Find the LocatorDescriptor's literal testid string in the test repo
   (`agent-actions-menu-button`, `delete-agent-menuitem`).
2. Find the DotMenu call site (for the `-menu-button` suffix) or the menu-items
   hook (for the `-menuitem` suffix) in EliteaUI that supplies the **fragment**
   (`id="agent-actions"`, `key: 'delete-agent'`) — NOT the composed string, which
   never appears literally anywhere in source.
3. Grep **that fragment** against `main` / `automation/testids`.

This generalizes the existing `dynamic_testid_promotability_grep` memory entry
(which only documented the `${key}-menuitem` half, from a DotMenu menu-item case)
to also cover the trigger-button half (`${id}-menu-button`). Default move whenever
a promotability grep on a testid ending in a DotMenu-shaped suffix (`-menuitem`,
`-menu-button`) comes back empty on both branches: don't conclude "missing" —
grep the fragment, trace the one-hop composition, then re-grep the fragment.

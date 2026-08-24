---
name: DotMenu menu-item testids + unmount timing
description: Name a DotMenu item's testid by its `key` at the CALL SITE, and wait for detached before asserting the menu closed
type: feedback
aliases: [dot menu testid, controls-menu, three-dot menu, withClose, pin-toggle-toolkit, copy-link-toolkit]
tags: [area/ui, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## Giving a DotMenu item a testid

`DotMenu.jsx` wires `data-testid={testId ? `${testId}-menuitem` : undefined}` from
`testId: item.key`. So a menu item renders a testid **only if its item object carries a `key`**.

Two failure modes seen on the toolkit/MCP menu (`ToolkitsControls.jsx`):

- hook supplies **no** key (`useExportToolkitMenu`) -> no `data-testid` at all;
- hook defaults `key: key || label` (`useCopyLinkMenu`) -> the visible LABEL leaks into the
  testid, spaces included (`Copy link-menuitem`).

**The fix is at the call site, not in the shared hook** — spread the item and name the key in
the `items` array:

```jsx
{ ...copyLinkMenuItem, key: 'copy-link-toolkit' },
{ ...pinMenuItem, key: 'pin-toggle-toolkit' },
```

Precedent: `SkillControls.jsx` (`pin-toggle-skill`), `CredentialsControls.jsx`
(`pin-toggle-credential`). Smaller diff, scoped to one menu, zero impact on the hook's other
callers. Landed for ELITEA-1946/1959 as EliteaAI/EliteaUI@2c4107b4.

## The menu unmounts behind a transition

`withClose` fires on every item click, but `controls_menu.count()` read in the click's own tick
still returns `1`. Wait for `state="detached"` first
(`McpFormPage.wait_for_controls_menu_closed()`), then assert `count() == 0`. Same after Escape.
Cost one rerun on ELITEA-1959.

Related: [[mcp_create_type_picker_console_key_warning]]

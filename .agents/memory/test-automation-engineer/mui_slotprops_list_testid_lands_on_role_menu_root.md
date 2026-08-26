---
name: MUI slotProps.list testid lands on role=menu root
description: How to add a testid-compliant handle for an @mui/material Menu's own popup element (its role="menu" node), without a raw role selector.
type: feedback
---

## Problem

`@mui/material/Menu` renders its popup as a `MenuList` whose ROOT element
carries `role="menu"` — but that root is a MUI-internal render node with no
app testid by default. Case text / AFS sometimes wants the menu's own
visibility asserted as a distinct observable from its individual items
(e.g. ELITEA-2467: assert `aria-expanded` AND `role="menu"` visibility AND
the item list, as three separate checks). A raw `page.locator('[role="menu"]')`
is forbidden under the testid-only locator policy, and this is NOT a #579
"third-party subtree, testid genuinely can't be placed" exception — it CAN
be placed.

## Fix

`<Menu>` accepts `slotProps={{ list: {...} }}` and forwards those props
directly onto the underlying `MenuList` component, whose root is built as:

```js
// @mui/material/MenuList/MenuList.js
return jsx(List, { role: "menu", ref, className, onKeyDown, tabIndex, ...other, children: items });
```

`...other` is the destructured remainder of whatever `MenuList` receives —
i.e. whatever you pass via `slotProps.list` — spread onto the `role="menu"`
element itself. So:

```jsx
<Menu
  slotProps={{
    list: {
      'aria-labelledby': 'more-files-button',
      'data-testid': 'chat-attachment-overflow-menu',   // lands ON role="menu"
    },
  }}
>
```

Confirmed live (ELITEA-2467, `FileList.jsx`): the resulting
`[data-testid="chat-attachment-overflow-menu"]` element IS the `role="menu"`
node — `locator.get_attribute("role") == "menu"` passes directly on it, no
extra traversal needed.

## Why this generalizes

Any `@mui/material/Menu` in this codebase lacking a testid on its own popup
(as opposed to its `MenuItem` children, which usually already have per-item
testids) can get one the same way — check `Menu.js`'s
`externalForwardedProps.slotProps.list` merge order first if a project
also passes the deprecated `MenuListProps` prop (the later spread wins,
so `slotProps.list` fully replaces rather than merges with `MenuListProps`).
Same pattern already precedented for other MUI slot props in this repo:
`PlusChatButton.jsx`'s `slotProps: { input: { 'data-testid': ... } }` on a
`Switch`.

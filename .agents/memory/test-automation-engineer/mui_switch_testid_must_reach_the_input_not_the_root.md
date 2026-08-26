---
name: A testid on a MUI Switch must reach the input, not the root span
description: Spread lands the testid on the MUI root where checked state is unreadable; use slotProps.input
type: feedback
aliases: [switch testid, toggle checked assertion, to_be_checked fails, BaseSwitch testid, MUI v7 inputProps]
tags: [area/testids, area/mui, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## The trap

`Switch.BaseSwitch` (`src/[fsd]/shared/ui/switch/BaseSwitch.jsx`) spreads `...restProps`
onto MUI's `Switch`, and MUI puts unrecognised props on the **root `<span
class="MuiSwitch-root">`**. A testid passed that way therefore lands on a span, where
`expect(...).to_be_checked()` / `.is_checked()` cannot work — the `checked` property
lives on the hidden `<input type="checkbox">` underneath.

## The shape that works (MUI v7)

Thread it through `slotProps.input` from the FEATURE call site (never hardcode a
feature testid inside `shared/ui`):

```jsx
// EnableToggleCard.jsx — feature component, caller-supplied prop
<Switch.BaseSwitch
  checked={enabled}
  onChange={onToggle}
  slotProps={switchTestId ? { switch: { slotProps: { input: { 'data-testid': switchTestId } } } } : undefined}
/>
```

The extra `switch:` hop is `BaseSwitch`'s own `slotProps` API — it spreads
`{...slotProps?.switch}` onto MUI's `Switch`, so the inner `slotProps.input` reaches MUI
unmodified. Verified live 2026-08-26 (ELITEA-2267): the testid resolved to
`INPUT/checkbox/checked=true`. `inputProps` also works but is deprecated in MUI v7.

Related: [[vite_watcher_blind_on_onedrive_restart_dev_server]]

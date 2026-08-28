---
name: MUI v7 Switch — inputProps is dead, use slotProps.input
description: Adding a testid to a MUI Switch's hidden checkbox needs slotProps.input; inputProps is silently overridden
type: feedback
aliases: [switch testid, toggle input testid, inputProps ignored, BaseSwitch slotProps]
tags: [area/eliteaui, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## The trap

`<Switch.BaseSwitch inputProps={{ 'data-testid': 'x-input' }} />` renders the input
**without** the attribute — no error, no warning. MUI v7's `Switch.js` builds its own
`slotProps={{ input: mergeSlotProps(slotProps.input, { role: 'switch' }) }}` and passes it to
`SwitchBase`, whose `{ input: inputProps, ...slotProps }` merge lets the constructed object
win, so an `inputProps` arriving via `...other` never reaches the DOM.

## The compliant shape (EliteaUI)

`BaseSwitch` consumes its own `slotProps` and spreads only `slotProps.switch` onto the MUI
`Switch`, so the input slot is one level in:

```jsx
<Switch.BaseSwitch
  data-testid="sound-notifications-toggle"
  slotProps={{ switch: { slotProps: { input: { 'data-testid': 'sound-notifications-toggle-input' } } } }}
/>
```

`data-testid` still lands on the `SwitchBase` **span** (the click target); the input is the
only element `to_be_checked()` accepts. `Slider`'s `slotProps.input` / `slotProps.thumb` work
first try — only `Switch` has this trap.

Note the older project pattern (`UserProfileSettingsPage.is_context_management_enabled`) reads
the `Mui-checked` class off the span instead, because that testid was added before the input
one existed.

Related: [[vite_watcher_onedrive_stale_module]]

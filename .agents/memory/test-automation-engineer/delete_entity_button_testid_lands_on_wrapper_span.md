---
name: DeleteEntityButton testId lands on the wrapper span, not the button
description: A locator built on DeleteEntityButton's testId prop is a <span> — is_disabled() is always False; use the new buttonTestId prop instead.
type: reference
aliases: [DeleteEntityButton, delete entity button testid, buttonTestId, delete button disabled assertion]
tags: [area/ui-handles, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## The trap

`src/components/DeleteEntityButton.jsx` (EliteaUI) renders:

```jsx
<Tooltip title={title}><Box component="span" data-testid={testId}>
  <IconButton aria-label="delete entity" disabled={isLoading || disabled}> … </IconButton>
</Box></Tooltip>
```

The wrapper `<span>` exists because MUI `Tooltip` cannot wrap a **disabled** button.
Consequence: a `LocatorDescriptor(testid=<what you passed as testId>)` resolves to the
`<span>`, so `is_disabled()` / `expect(...).to_be_disabled()` on it is **always False /
always fails** — an enabled/disabled assertion silently reports "enabled" no matter the
real state. Presence and click still work through the span (the click bubbles), which is
why this stays invisible until you assert state.

## The fix (in place since 2026-08-26)

`EliteaAI/EliteaUI@30a15ac6` added an additive **`buttonTestId`** prop wired onto the
inner `IconButton` (`<part>TestId` naming per `.agents/testing.md` § Locator policy).
When a test needs the button's own state, pass **`buttonTestId` INSTEAD of `testId`** at
the call site — that way exactly one testid exists and it sits on the button. Every
pre-existing `testId` caller is untouched (`buttonTestId` defaults to `undefined`).

First use: `NotificationTableToolbar.jsx` → `notifications-delete-selected-button`
(ELITEA-2255). Cost when missed: one rerun.

## Generalisation

Any MUI `Tooltip`-wrapped control that can be disabled has this shape. Before asserting
`to_be_disabled()` on a testid you did not place yourself, check which NODE the testid
landed on — `document.querySelector('[data-testid=…]').tagName` in a live probe is a
two-second check. The notifications mark-toggle button
(`notification-mark-toggle-button`) has the same `Tooltip > span > BaseBtn` structure but
its testid is on the **button**, so it reports `disabled` correctly — the placement, not
the wrapper, is what matters.

Related: [[notification_center_surface_handles]]

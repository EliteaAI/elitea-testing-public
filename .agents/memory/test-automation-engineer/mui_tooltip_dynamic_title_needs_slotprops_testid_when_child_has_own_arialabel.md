---
name: MUI Tooltip dynamic title needs a slotProps testid when the child already has its own aria-label
description: If the wrapped child (button/icon) already carries a static aria-label, MUI's Tooltip does NOT clone the dynamic title onto it or a wrapper — read the popper via a testid added on Tooltip's slotProps.tooltip, not the child's own attribute
type: feedback
---

## The pattern

```jsx
// AttachmentButton.jsx (pipeline/agent embedded chat's bare attach button)
const processStatus = `Attach Files (${remainingAttachments} left)`;  // DYNAMIC

<Tooltip title={processStatus} placement="top">
  <Box component="span">
    <IconButton aria-label="attach files" data-testid={testId} ...>  {/* STATIC aria-label already set */}
      ...
    </IconButton>
  </Box>
</Tooltip>
```

Live-confirmed (`getAttribute('aria-label')` before/after hover, before/after
attaching a file): the button's `aria-label` stays the literal string
`"attach files"` the whole time. It never becomes `"Attach Files (10 left)"`
or `"Attach Files (9 left)"`. This is the SIBLING gotcha to
`mui_tooltip_aria_label_wrapper_differs_from_click_target_testid.md` (which
covers a STATIC title cloning onto a wrapping `<Box>` one level up) — here
the title is DYNAMIC and there is NO cloning at all, onto the button OR the
wrapper, because the child already declares its own `aria-label`. MUI only
clones `title` onto `aria-label` when the child has none of its own.

## Why this bites

The AFS/case text can say "accessible name via tooltip" as if reading
`aria-label` would surface the counter — it won't. The dynamic text exists
ONLY inside the Tooltip's portal-rendered popper content
(`document.querySelector('[role="tooltip"]')`), which only exists in the DOM
while hovering, and which is not a compliant testid-only handle by default
(no testid on it at all pre-add).

## The check (do this BEFORE assuming aria-label carries the dynamic text)

```js
// hover first (browser_hover / .hover()), then:
() => {
  const btn = document.querySelector('[data-testid="some-button-testid"]');
  const tooltip = document.querySelector('[role="tooltip"]');
  return { ariaLabel: btn.getAttribute('aria-label'), tooltipText: tooltip?.textContent };
}
```
If `ariaLabel` stays static while `tooltipText` carries the dynamic counter,
aria-label is a dead end for this assertion.

## The fix shape — MUI v7 `slotProps.tooltip`

```jsx
<Tooltip
  title={processStatus}
  placement="top"
  slotProps={{ tooltip: { 'data-testid': 'chat-attach-button-tooltip' } }}
>
```
Check first whether the `!showLabel`/Tooltip-wrapping branch is reachable
from more than one call site (grep the component's other render branches) —
if only one path renders the Tooltip, a hardcoded generic testid is
collision-safe (no `testId` prop threading needed). Read it via a NEW
page-object `LocatorDescriptor` + `.text_content()` after `.hover()` — never
a raw `[role="tooltip"]` selector in the page object (not a #579 exception;
it's our own MUI usage, not a third-party widget).

## Provenance

ELITEA-2059 (PR against `tests/batch-pipelines-remaining-w5`) — the AFS's
Concrete Handles table said "accessible name via tooltip" without flagging
that the button's OWN aria-label is static and the counter needs a fresh
testid. Caught via a live probe pipeline in implementer Phase 2, before
writing the assertion.

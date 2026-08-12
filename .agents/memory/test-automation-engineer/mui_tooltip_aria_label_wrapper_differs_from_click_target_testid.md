---
name: MUI Tooltip aria-label wrapper differs from the click-target's existing testid
description: When a case needs a MUI <Tooltip title="..."> element's text and the wrapped child already has a testid for CLICKING, that testid usually resolves to the inner button/element — the Tooltip clones its aria-label onto a separate wrapping <Box component="span"> one level up, which may have zero testid of its own
type: feedback
---

## The pattern

```jsx
<Tooltip title="Download files" placement="top">
  <Box component="span">                              {/* Tooltip clones aria-label HERE */}
    <Button.BaseBtn data-testid="artifacts-download-files-button" ...>  {/* testid is HERE */}
      <DownloadIcon />
    </Button.BaseBtn>
  </Box>
</Tooltip>
```

Reading `download_files_button.get_attribute("aria-label")` returns `None` —
the inner `<button>` carries only `class`/`tabindex`/`type`/`data-testid`,
no `aria-label`. The tooltip's static title text only lands on the
WRAPPING `<Box component="span">`, one DOM level up, which has no testid
unless someone adds one.

## Why this bites

An existing testid on a button is easy to assume covers "everything about
this control" — including its tooltip. It doesn't. The click-target and the
tooltip-anchor are frequently two different DOM nodes. This is invisible
until a case specifically requires reading tooltip TEXT (not just clicking
the button), at which point `element.getAttribute('aria-label')` silently
returns `null` and it's not obvious why without checking the parent.

Note the asymmetry with `DeleteEntityButton`-style shared components
(ELITEA-1847's `delete_files_button`): there, the caller-supplied `testId`
prop lands ON the SAME wrapping element MUI's Tooltip uses for aria-label —
so `get_delete_button_tooltip_text()` works with zero extra plumbing. Don't
assume this generalizes; always confirm live per-button.

## The check (do this BEFORE assuming a testid needs adding)

```js
// via Playwright MCP browser_evaluate or browser-verify evaluate
() => {
  const btn = document.querySelector('[data-testid="some-existing-button-testid"]');
  return {
    ownAriaLabel: btn.getAttribute('aria-label'),
    parentTag: btn.parentElement.tagName,
    parentAriaLabel: btn.parentElement.getAttribute('aria-label'),
  };
}
```

If `ownAriaLabel` is `null` and `parentAriaLabel` has the tooltip text, the
existing testid doesn't reach it — a new testid is needed on the parent
wrapper (or, per the shared-component testid ruling, a new caller-prop if
the wrapping component is shared across features).

## The fix shape

If the Tooltip's child wrapper (`<Box component="span">`) is JSX local to a
single-consumer, non-shared component (confirmed via
`grep -rl "<ComponentName>" src --include="*.jsx"`), hardcode the testid
directly — no prop threading needed:

```jsx
<Box component="span" data-testid="artifacts-download-files-tooltip">
```

Then read it via a NEW page-object locator distinct from the click-target's
existing one, and a NEW method (`get_download_button_tooltip_text()`) —
never chain `.locator("..")`/xpath parent-traversal off the existing
testid'd field (still a raw-selector chain per the page-objects rule, even
though it's structural rather than a CSS class).

## Provenance

ELITEA-1841 (PR #676) — AFS's own Concrete Handles table listed
`download_files_button` as "existing, reuse" with tooltip text "confirmed
via aria-label read on the wrapping `<span>`" (an analyst-exploration-time
fact), but didn't flag that automating that read compliantly (testid-only,
no raw parent traversal) needs its own testid. Caught in implementer Phase
2 before writing the assertion, not after a failed run — check live BEFORE
assuming an existing testid is sufficient whenever a case needs tooltip
TEXT, not just a click.

**Same pattern, 4 buttons at once (ELITEA-2614, 2026-08-12):**
`ToolMenu.jsx`'s Toolkit/MCP/Agent/Pipeline "+ X" add buttons each wrap a
testid'd `BaseBtn` in `<Tooltip><Box component="span">…</Box></Tooltip>`
with NO testid on the `Box`. Confirmed the mechanism by reading
`node_modules/@mui/material/Tooltip/Tooltip.js` directly (childrenProps
spread order: `{...nameOrDescProps, ...other, ...children.props}` — the
clone lands on Tooltip's immediate JSX child, and any `aria-label` already
set explicitly on that child via its own JSX props wins) rather than
guessing from behavior. Fix mirrored the pre-existing
`agent-add-skill-button-tooltip` precedent exactly: added
`agent-add-{toolkit,mcp,agent,pipeline}-button-tooltip` testids to the 4
wrapper `Box`es. Worth checking `Tooltip.js`'s childrenProps spread order
specifically when the WRAPPED element already sets its own static
`aria-label` prop (as `SkillCard.jsx`'s remove-button IconButton does,
`aria-label="remove skill"`) — in that shape the static prop wins over
Tooltip's generated one, so reading `aria-label` off the button reveals the
static label, not the tooltip's (conditional) title text; that's a
DIFFERENT node needing a DIFFERENT read, not just "one level up."

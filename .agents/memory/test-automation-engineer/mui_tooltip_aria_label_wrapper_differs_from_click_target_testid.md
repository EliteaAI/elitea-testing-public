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

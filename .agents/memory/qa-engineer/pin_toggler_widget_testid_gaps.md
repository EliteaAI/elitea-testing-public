---
name: Pin-toggler widget testid gaps
description: Shared pin/unpin widget (list icon button + detail-page three-dot menu item) reused across Credentials/Skills/Toolkits/Applications/MCPs has zero data-testid on both surfaces; root cause and fix location identified
type: reference
---

The pin/unpin feature lives in `EliteaUI/src/[fsd]/widgets/pin-toggler/` and
is consumed by every entity-list + entity-detail pair that supports
pinning (confirmed consumers: Credentials, Skills, Toolkits, Applications;
grep `usePinMenu`/`PinButton` to find more before starting a new pin-related
case on another entity type).

## Two testid gaps, both source-confirmed, both one-line fixes

1. **List-view icon button** (`pin-toggler/ui/PinButton.jsx`) — the
   `IconButton` rendering the pin icon in list/card rows
   (`DataTableRow.jsx` and card-view equivalents) has **zero
   `data-testid`**, only `aria-label` ("Pin to top" / "Unpin from top",
   flips with state). Fix: add a `data-testid` prop to `PinButton.jsx`
   itself (it's a shared component — fixing it once covers every consumer,
   same class of fix as the `DiscardButton`/`BaseModal` gap documented in
   ELITEA-1971's AFS).

2. **Detail-page pin-toggle menu item** — rendered via
   `pin-toggler/lib/hooks/usePinMenu.hooks.jsx` → passed into each entity's
   `*Controls.jsx` (e.g. `CredentialsControls.jsx`, `SkillControls.jsx`,
   `ToolkitsControls.jsx`, `ApplicationControls.jsx`) → rendered by the
   shared `DotMenu.jsx`'s `BasicMenuItem`, which DOES support
   `data-testid` — but only when the menu-item object carries a `key`
   (`DotMenu.jsx`: `testId: item.key`, then
   `data-testid={testId ? \`${testId}-menuitem\` : undefined}`). Every
   `*Controls.jsx`'s `pinMenuItem` object (spread from `usePinMenu`'s
   return) never sets `key` — while the sibling "Delete" menu item in the
   same array always does (e.g. `key: 'delete-credentials'`) and correctly
   gets a testid. Fix: add `key: 'pin-toggle-<entity>'` at each call site
   (or centralize it once inside `usePinMenu.hooks.jsx` if the entity name
   isn't needed for disambiguation — check whether multiple pin menu items
   can ever be open in the same DOM at once before centralizing).

## Not a defect: the `шnitialPinned` Cyrillic typo

`CredentialsControls.jsx`'s `usePin(...)` call spells the prop
`шnitialPinned` (Cyrillic С→ш homoglyph, not Latin "i"). Confirmed dead:
`usePin.hooks.js` derives `isPinned` from
`formikContext?.values?.is_pinned` whenever a `formikContext` is passed
(always true here, since the caller always calls `useFormikContext()`
first) — so the typo'd prop never reaches the branch that would use it.
Live-verified via ELITEA-1974 exploration: pin state displayed correctly
on page load and after pin/unpin round-trip despite the typo. Not filed —
purely a landmine for a future refactor that removes the
formik-vs-local-state branch, not a live bug. If `CredentialsControls.jsx`
is ever touched for another reason, worth a drive-by fix.

## API endpoints (for wait-strategy, not a client wrapper)

- Pin: `POST /api/v2/social/pin/prompt_lib/{project_id}/configuration/{id}` → 201
- Unpin: `DELETE /api/v2/social/pin/prompt_lib/{project_id}/configuration/{id}` → 204

Both fire synchronously with the UI state change (list reorder /
menu-label flip) — no separate loading-state UI observed, so
`page.wait_for_response` on these is sufficient, no polling needed.

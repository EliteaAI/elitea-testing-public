---
name: Pin-toggler widget testid gaps
description: Shared pin/unpin widget — list icon button testid now FIXED generically; detail-page three-dot menu item testid still gapped per-entity
type: reference
---

The pin/unpin feature lives in `EliteaUI/src/[fsd]/widgets/pin-toggler/` and
is consumed by every entity-list + entity-detail pair that supports
pinning (confirmed consumers: Credentials, Skills, Toolkits, Applications;
grep `usePinMenu`/`PinButton` to find more before starting a new pin-related
case on another entity type).

## Update (ELITEA-2435, Skills pin/unpin analysis): gap #1 is FIXED generically

`PinButton.jsx` now has `data-testid={entityId ? \`${getPinTestIdSlug(entityType)}-pin-toggle-button-${entityId}\` : undefined}`
built into the **shared** component (landed as part of `EliteaAI/EliteaUI#569`'s
credential fix, apparently generalized rather than credential-scoped).
`getPinTestIdSlug()` maps `isSkillCard→'skill'`, `isCredentialCard→'credential'`,
`isToolkitCard→'toolkit'`, `isMCPCard→'mcp'`, `isApplicationCard→'application'`.
**Confirmed live for Skills** (`skill-pin-toggle-button-{id}` resolved
correctly via Playwright MCP's own accessible-name click, ELITEA-2435 run) —
no `add-data-testid` round-trip needed for this element on ANY entity type
going forward; verify the other entity types' slug mapping holds if you hit
one, but the mechanism is generic now. Gap #2 below is still per-entity and
UNFIXED for Skills as of this run.

## Two testid gaps, one now fixed generically, one still per-entity

1. ~~List-view icon button has zero `data-testid`~~ — **FIXED, see Update
   above.** (Original text below kept for history/context.) Originally: the
   `IconButton` rendering the pin icon in list/card rows (`DataTableRow.jsx`
   and card-view equivalents) had zero `data-testid`, only `aria-label`
   ("Pin to top" / "Unpin from top", flips with state).

2. **Detail-page pin-toggle menu item** — STILL GAPPED for Skills
   (confirmed live, ELITEA-2435) — rendered via
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

## Skills use the clean local-state branch (no typo landmine)

`SkillControls.jsx` calls `usePin({entityId, entityType, initialPinned})`
with **no `formikContext`** — so `usePin.hooks.js` takes the local-state
branch (`useState(initialPinned)` + `setLocalIsPinned` on success), driven
correctly by `EditSkill.jsx`'s `initialPinned={data?.is_pinned}`. No
Cyrillic-typo-style landmine here; confirmed functionally correct live both
directions (ELITEA-2435).

## API endpoints (for wait-strategy, not a client wrapper)

- Credentials: `POST/DELETE /api/v2/social/pin/prompt_lib/{project_id}/configuration/{id}` → 201/204
- Skills: `POST/DELETE /api/v2/social/pin/prompt_lib/{project_id}/skill/{id}` → 201/204
  (confirmed live, ELITEA-2435 — path segment is the `PinEntityType` value,
  not always `configuration`; check the entity's `PinEntityType` constant
  for other entities rather than assuming the segment name)
- Pipelines: `POST/DELETE /api/v2/social/pin/prompt_lib/{project_id}/application/{id}` → 201/204
  (confirmed live, ELITEA-2025 — pipelines share the `application` path
  segment with agents, consistent with `PipelineAPI`'s own CRUD docstring)

Both fire synchronously with the UI state change (list reorder /
menu-label flip) — no separate loading-state UI observed, so
`page.wait_for_response` on these is sufficient, no polling needed.

## `getPinTestIdSlug()` has no `isPipelineCard` branch — leaks the raw ContentType (confirmed live, ELITEA-2025)

`PinButton.jsx`'s local `getPinTestIdSlug(entityType)` maps
`credential`/`skill`/`toolkit`/`mcp`/`application` explicitly but has NO
`isPipelineCard` case, so a pipeline card falls through to
`String(entityType).toLowerCase()`. On the main Pipelines dashboard
(`cardContentType={ContentType.PipelineAll}`) this resolves to
`pipelineall-pin-toggle-button-{id}` — a real, stable, working testid, just a
naming-convention leak (not `pipeline-pin-toggle-button-{id}` as the
`{section}-{element}-{type}` convention would predict). Not filed (cosmetic,
no collision risk within one view) — but **a different pipeline card view**
(Top/Latest/Trending/Draft/etc., none of which route through
`isPipelineCard` either) would produce a DIFFERENT testid for the SAME
pipeline (`pipelinetop-...`, `pipelinelatest-...`). Only `/pipelines/all`
(`ContentType.PipelineAll`) is confirmed; re-verify before reusing this
testid shape on another pipeline view.

## Gotcha: reorder timing is ASYMMETRIC between pin and unpin (confirmed live, ELITEA-2025, 3 cycles)

Pinning re-sorts the list/grid **instantly, client-side, no reload needed**.
Unpinning does **not** — the just-unpinned item stays in its pinned (top)
position, even though its own button/menu label flips back immediately,
until a fresh navigate/re-fetch happens. The merged
`test_credential_pin_unpin.py` already handles this correctly (Step 7b
re-navigates before asserting the reverted order) — this is now confirmed on
a second entity (Pipelines), so treat it as a platform-wide `usePin` hook
behavior. **Never assert order immediately after an unpin click** — always
re-navigate first, on any entity.

## Gotcha: pinning the already-topmost item shows no reordering

Pinning a skill/entity that's already the newest item (`sort_by=created_at&
sort_order=desc` default) produces only the icon/menu-label flip, no visible
position change (nothing above it to move past). To assert real reordering,
target a **bottom-ranked** item, or seed two records (older + newer) per
ELITEA-1974's two-credential / ELITEA-2435's two-skill pattern.

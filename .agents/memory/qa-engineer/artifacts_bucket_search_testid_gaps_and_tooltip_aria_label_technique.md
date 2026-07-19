---
name: Artifacts bucket-search testid gaps + tooltip aria-label technique
description: ELITEA-1809 — BucketsPanel.jsx's search input/clear button have no data-testid on main or automation/testids (SimpleSearchBar already supports one, call site just doesn't pass it); MUI Tooltip title= surfaces as a static aria-label on the trigger regardless of hover, so tooltip text is testid-compliant-verifiable without touching the ephemeral role="tooltip" popper.
type: feedback
---

## Context

ELITEA-1809 (duplicate bucket name validation) required verifying the
left-panel bucket-search feature (`artifacts/Components/BucketsPanel.jsx`,
`BucketSearch.jsx`, shared `SimpleSearchBar.jsx`).

## Finding 1 — bucket-search input/clear-button testid gap

`BucketsPanel.jsx:126-131`'s `<SimpleSearchBar searchQuery=... placeholder="Search
buckets..." />` call site passes **no `data-testid` prop**, even though the shared
`SimpleSearchBar.jsx:59` component already supports one conditionally
(`inputProps={props['data-testid'] ? {...} : undefined}`). The fix is a one-line
prop addition at the call site (`data-testid="artifacts-bucket-search-input"`),
not new plumbing in the shared component. The adjacent clear/X `IconButton`
(`BucketsPanel.jsx:132-138`, `onClick={handleSearchClear}`) has no testid at all.

Confirmed **absent on BOTH `origin/main` and `origin/automation/testids`** via
fresh `git fetch origin` + `git grep "data-testid" ... -- BucketsPanel.jsx` on
both refs (empty both times) — this is a genuine, currently-unfilled gap, not
something the UI team already added in parallel.

Per the current `role-overrides.md` Analyst-slot rule, specced as `testid
needed:` in the AFS for the **implementer** to add via `add-data-testid` — did
**not** self-fix live (unlike ELITEA-1808's earlier precedent, which predates
this rule's current phrasing and self-fixed three gaps directly).

## Finding 2 — MUI Tooltip title verification without the hover popper

`BucketSearch.jsx` wraps its `IconButton` in `<Tooltip title="Search buckets"
placement="top">` (from `@/ComponentsLib/Tooltip`, a thin MUI `Tooltip` wrapper).
Confirmed live: MUI sets a **static `aria-label="Search buckets"`** on the
IconButton itself, independent of hover state — `page.locator('[role="tooltip"]')`
stayed at count 0 even after a real `.hover()` + 500ms wait (the floating popper
never actually needs to render for this to be readable).

**Reusable technique**: to verify a MUI `Tooltip`'s text under this project's
testid-only locator policy, read the `aria-label` attribute of the
already-testid'd trigger element (`element.get_attribute("aria-label")`) rather
than trying to locate/hover/read the ephemeral `role="tooltip"` popper. This
stays fully testid-compliant (the LOCATOR is still the testid; you're reading an
attribute of a testid-resolved element, not locating anything by role/label) and
avoids flaky hover-then-wait-then-read sequences entirely.

## Also confirmed this run

The generic `toast-message` testid (already a `LocatorDescriptor` on
`ArtifactsPage`, documented for the SUCCESS path by ELITEA-1826/1832) is the
SAME component MUI renders for error-severity toasts too
(`src/components/Toast.jsx`'s `<Alert severity={severity}>` — `severity="error"`
just changes the MUI `filled` variant's color to red). No new toast testid
needed for error-path cases; reuse `toast-message` and assert the text/color via
the existing handle.

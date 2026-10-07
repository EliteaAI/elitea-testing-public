---
name: Bucket-row DotMenu hover-reveal is flaky on first try — retry recovers it, no drift
description: Locator.hover() on an Artifacts bucket row intermittently fails to register :hover (not an element-growth/center-drift issue); a second hover (move away, re-hover) reliably recovers it. Confirmed live, isolated, 2026-10-07 (ELITEA-2494/#2403 triage).
type: feedback
---

## The symptom

`ArtifactsPage.open_manage_permissions()` (`automation/pages/artifacts_page.py:2676`)
does `bucket_row.hover()` → `page.wait_for_timeout(500)` → `menu_btn.wait_for(state="visible",
timeout=10000)`. CI (`UI Tests DEV` run 37592267621, ELITEA-2494) saw this time out
3/3 pytest-rerun attempts with `24 × locator resolved to hidden` on
`[data-testid="bucket-menu-permissionstest-menu-button"]` — the testid is correct and
exists; the element is just stuck `visibility: hidden`.

## Root cause (confirmed live against DEV, isolated repro — no sibling test involved)

`BucketItem.jsx` (EliteaUI `origin/main`) gates the DotMenu's reveal with **two
independent mechanisms that must both be true**:
1. CSS `'&:hover #Menu': { visibility: 'visible' }` on the row — pure browser `:hover`
   pseudo-class, recalculated by the compositor.
2. React state `isHovering` (set via `onMouseEnter`/`onMouseLeave` on the same row) →
   `display: isHovering || showMenu ? 'flex' : 'none'`.

Live instrumentation (`row.matches(':hover')` + computed style of the menu button) showed
cases where React's `isHovering` state WAS correctly set to `true` (`display: flex`) but the
browser's native `:hover` pseudo-class was simultaneously **not** matching the same element
(`visibility: hidden`) — i.e. the DOM mouseenter event fired and was handled, but the
synthetic hover from Playwright's `Locator.hover()` (headless Chromium via CDP) didn't
register as a persistent `:hover` match. Once stuck, it stays hidden for the full
remaining wait — this is not a transient scheduling delay, it never self-resolves within
10s.

**Measured flake rate (4 standalone trials, exact page-object gesture, back-to-back
against DEV, 2026-10-07):** 1 PASS / 3 FAIL. In a tighter loop forcing quick failure
detection (2.5s budget) then **retrying** the hover (`page.mouse.move(5,5)` away, wait
200ms, `row.hover()` again, wait 300ms): **4/4 recovered** immediately. Retrying the
hover gesture is a reliable, cheap recovery — this is a genuine client-side hover-
registration race, not UI drift, not a missing/renamed handle, and (confirmed by running
in total isolation, no other test executed before it) **not test-interdependency with
any sibling test** sharing the same bucket.

## Reusable pattern

Any bucket-row (or similarly-styled: CSS-`:hover`-driven `visibility` + React-state-driven
`display`, two independent gates on the same reveal) `DotMenu`/hover-reveal timeout against
DEV in this app is a candidate for this exact race before concluding drift/defect: check
whether a **second** hover attempt (move the mouse away first, then re-hover) resolves it
within a couple seconds. If so, class **D** (timing/robustness) — the fix is a bounded
retry-the-hover loop in the page-object method, never a locator/assertion change. If a
`force=True` click bypasses visibility ever gets tried as an alternative fix: untested here,
plausible since JS click dispatch doesn't require `:hover` to be true, but not verified live
by this session.

## Side observation (not confirmed as the cause, flagging only)

`BucketItem.jsx` renders `<Box id="Menu">` per row with **no uniqueness** — with 107 buckets
in the Team project used for this repro, that's 107 DOM elements sharing `id="Menu"`
(invalid HTML). CSS descendant-selector scoping still worked correctly in every trial where
hover DID register, so this is NOT demonstrated to cause the flake — but it's a real
code-quality defect worth a product-team look if it recurs with a different signature
(e.g. `document.getElementById` based logic resolving to the wrong row).

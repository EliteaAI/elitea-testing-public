---
name: Playwright accessibility "[active]" marker is DOM focus, not app selection
description: never assert selection/pressed state from a11y snapshot [active] — it tracks focus
type: feedback
---

Discovered on ELITEA-2352 (Agent Hub category filter-rail chip, `CategoryRail.jsx`).

When a Playwright accessibility snapshot shows an element as `[active]`
(e.g. `button "Business Analyst" [active]`), this does **NOT** mean the
element is the app's "selected"/"pressed" state — it reflects **DOM focus**.

Confirmed live: clicking a second sibling chip moved `[active]` to the new
one even though the FIRST click's category remained the actually-filtered
one in app state (multi-select accumulates); clicking an unrelated element
(a search input) made `[active]` disappear from a still-selected chip
entirely, while the real filter state was unaffected.

If the element has no `aria-selected`/`aria-pressed`/`data-*` state attribute
(MUI `Chip` with only a conditional `sx` style is the recurring shape), that
is a real accessibility/testid gap — add a `data-selected="true"/"false"`
(or similarly named) attribute driven by the SAME boolean expression already
used for the conditional style, per `.agents/testing.md` § Locator policy
("state via data-* attributes"). Never assert on `[active]`/focus as a proxy
for selection — it will flake based on click order and subsequent focus
moves, not the thing the test actually cares about.

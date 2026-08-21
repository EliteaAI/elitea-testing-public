---
name: Asserting a visual/CSS state without evaluate()
description: Use to_have_css / not_to_have_css on a testid-anchored locator, and assert default-vs-not-default instead of a theme-dependent colour literal
type: feedback
aliases: [to_have_css, hover highlight, background-color assertion, computed style]
tags: [area/ui, type/technique]
created: 2026-08-21
updated: 2026-08-21
---

## The pattern

A case that says "the row background changes to indicate highlight" does NOT
need `evaluate("getComputedStyle(...)")` — Playwright's web-first
`expect(locator).to_have_css("background-color", value)` and its negative
`not_to_have_css(...)` read the computed style, retry until it settles, and keep
the diff clean of the reviewer's `\.evaluate\(` fidelity grep
(`.agents/role-overrides.md` § Reviewer slot). The locator stays a page-object
accessor (`ArtifactsPage.bucket_row(name)`), so the testid-only policy holds.

## Assert default-vs-not-default, never the highlight literal

Elitea themes both define the *neutral* value as literal `'transparent'`
(`darkPalette.js` / `lightPalette.js` → computed `rgba(0, 0, 0, 0)`), while the
*active* value differs per theme (`white6` dark = `rgba(255, 255, 255, 0.06)`,
`dark6` light). So:

- unhighlighted → `to_have_css("background-color", "rgba(0, 0, 0, 0)")`
- highlighted → `not_to_have_css("background-color", "rgba(0, 0, 0, 0)")`

Bi-directional and theme-independent. Pinning the hover literal makes the test
fail for the wrong reason the day someone runs it in the light theme.

## Selection styling can mask hover styling

`BucketItem.jsx`'s `getBackgroundColor()` returns the *selected* colour before
it looks at `isHovering`, so hovering a selected row changes nothing. Any
hover test must pick rows with `data-selected="false"`; `/artifacts` auto-selects
the first row on a param-less load, which makes "hover the first bucket" a trap
(ELITEA-1823, clarification `EliteaAI/elitea-testing-public#1623`).

Related: [[no_playwright_mcp_use_sync_playwright_script]]

---
name: First-visit tour prompt blocks the sidebar on any section route
description: The "New here?" interactive-tour prompt is per-section (not /onboarding-only) and its backdrop intercepts clicks on the sidebar — dismiss it before any sidebar interaction
type: feedback
aliases: [New here prompt, first visit prompt, interactive tour backdrop, intercepts pointer events sidebar]
tags: [area/ui, area/sidebar, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The gotcha

The interactive-tour **first-visit prompt** ("New here? … Skip / Start!") is documented in
`test-specs/onboarding/_surface.md` as an `/onboarding` after-effect. It is not: it is
**per-section**, keyed by `localStorage["interactive-tour:<section>:prompt-seen"]`, and it fires on
a plain landing on `/chat` (confirmed live 2026-08-24).

It is modal with `InteractiveTourBackdrop`, so the sidebar is **visible but not clickable**. A click
on any sidebar control fails Playwright actionability with
`<div class="MuiBox-root …"> intercepts pointer events` — which reads like a product bug and isn't.

## What to do

Dismiss it first: `components/interactive_tour.py` → `FirstVisitPromptCard.click_skip()`
(testids `interactive-tour-first-visit-prompt` / `interactive-tour-first-visit-skip-button`,
on `automation/testids`).

It also emits the known `#1753` console error (`MUI: The modal content node does not accept focus`)
— filter that one message rather than asserting a bare "no console errors".

Related: [[in_page_fetch_to_elitea_api_dies_on_oidc_cors]]

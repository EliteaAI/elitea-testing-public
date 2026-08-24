---
name: Playwright to_be_visible() ignores opacity — hover-reveal controls need to_have_css
description: A control at opacity:0 passes to_be_visible(); a case step saying "button is visible" is only honestly asserted by to_have_css("opacity", "1") after a hover
type: feedback
aliases: [hover reveal opacity, opacity 0 visible, pin toggle visibility, to_have_css opacity]
tags: [area/ui, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

Playwright's visibility definition = non-empty bounding box + `visibility != hidden`.
It says **nothing about `opacity`**. So a hover-reveal control rendered at
`opacity: 0` (the Elitea entity-card pattern: pin toggle, three-dot menu) is
reported **visible** and `to_be_visible()` passes on something no human can see.
Clicking it also works, because `pointer-events` stays `auto`.

## Consequence for review

When a TMS case step says "<control> is **visible** on the card", a bare
`to_be_visible()` is a **vacuous** assertion — it would pass on a fully
transparent control. The honest shape is: hover the control first, then
`expect(locator).to_have_css("opacity", "1")`.

Seen done correctly in `automation/tests/ui/toolkits/test_mcp_pin_unpin.py`
(ELITEA-1945, step 2) with `McpListPage.hover_pin_toggle()`.

Distinct from [[visibility_hidden_blocks_real_hit_testing_unreachable_case_step]]:
`visibility: hidden` removes hit-testing entirely (click impossible);
`opacity: 0` leaves the element fully clickable, only invisible.

Related: [[hover_reveal_menu_breaks_on_expanded_accordion_container]]

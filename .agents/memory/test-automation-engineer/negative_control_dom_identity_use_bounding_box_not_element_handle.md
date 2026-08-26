---
name: negative_control_dom_identity_use_bounding_box_not_element_handle
description: Proving two Playwright locators resolve to different DOM elements — use bounding_box(), not element_handle() equality
type: feedback
---

When an AFS asks for a negative control proving two visually-identical
locators (e.g. two menu items both labelled "Share") resolve to two
DIFFERENT DOM elements — not the same node matched twice by an
under-scoped selector — do NOT compare `locator.element_handle()` results
with `!=`. Two separate Python calls to `element_handle()` return two
separate `JSHandle` **Python objects**, which always compare unequal by
object identity regardless of whether they wrap the same underlying DOM
node. The assertion `handle_a != handle_b` is vacuously true even when
both locators secretly resolve to the same element — it proves nothing.

Correct approach (established repo pattern, e.g.
`test_agent_management.py`'s tag-chip identity check): compare
`locator.bounding_box()` results. Two different DOM elements — even ones
with identical text/label — almost always render at different screen
positions, so `box_a != box_b` is a real, meaningful signal. Used this way
in `test_pipeline_three_dot_menu_actions.py` (ELITEA-2049) to prove
`share_version_menuitem` (VERSION-group) and `share_agent_menuitem`
(PIPELINE-group) are genuinely separate menu items, not the same node
matched twice.

If you need certainty beyond position (rare — bounding boxes could
coincide for stacked/overlapping elements), the robust alternative is a
`page.evaluate()` call comparing both locators' resolved nodes for
strict `===` equality inside the browser context, not a Python-side handle
comparison.

---
name: page.viewport_size is None in this suite's headed mode
description: conftest uses no_viewport=True when HEADLESS=false, so any assertion comparing a bounding box to the viewport must degrade, not crash.
type: project
aliases: [no_viewport, viewport_size None, headed viewport, bounding box vs viewport]
tags: [area/framework, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## Fact

`automation/conftest.py` (~line 288-315): headless runs pin
`viewport={"width": 1366, "height": 768}`; **headed runs (the suite default —
`config.py: headless=False`) use `no_viewport=True`**, and Playwright then
reports `page.viewport_size is None`.

## Consequence

An AFS row saying "assert the element's `bounding_box()` equals
`page.viewport_size` (±2 px)" is unevaluatable in the default local mode.
Write the geometry assertion so the unconditional part still fails on a real
regression, e.g. for a fullscreen dialog:

- anchored at the viewport origin (`x`, `y` <= 2 px);
- covers at least the app shell container's own box;
- strictly larger than the element it expanded from (measured before the click);
- **plus** the exact viewport equality, only `if page.viewport_size is not None`.

Verified 2026-08-24 on ELITEA-2236 (`test_onboarding_tips_fullscreen.py`).

Related: [[mui_dialog_testid_paper_vs_root]]

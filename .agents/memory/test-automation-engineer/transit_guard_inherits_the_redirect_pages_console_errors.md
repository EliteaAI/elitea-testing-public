---
name: A transit guard that re-navigates through a product page inherits that page's console errors
description: Re-navigating past a bad redirect fixes the precondition wait but not a spec-wide console-error axis — the landing page's errors are already in the collector
type: feedback
aliases: [2305 guard console errors, redirect guard console axis, open_list console noise]
tags: [area/social-folders, type/flake-handling, status/open]
created: 2026-09-15
updated: 2026-09-15
---

## The trap

`collect_console_errors(page)` is armed at test start and asserted at the end ("Axis 2 — no
unexpected console errors"). A bounded re-navigation guard (`EntityTypeBinding.open_list`, #2305)
converts a Step-0 `Locator.wait_for` timeout into a clean list mount — but the page the product
redirected to (`/toolkits/create`, `ToolkitTypeSelector.jsx`) has ALREADY logged its own errors:
the #1971 project-id-less `GET /toolkits/prompt_lib/` 404 and a React `key` warning. So the
failure MOVES (Step 0 `broken` → Axis 2 `failed`) and the rerun count does not change.

Measured 2026-09-15 (localhost, `automation/testids`@480f00d6): 3 of 5 `toolkits_and_indexes`
draws hit #2305; the guard mounted the list on re-navigation 1 every time; Axis 2 failed every
time on the same two messages.

## What to do

Do not filter around it inside the guard (window-scoped or text-keyed drops are masking shapes
the canon has no pattern for). It is an observable decision for the lead: opt-in
`exclude_known_defect_urls` for the #1971 URL is the sanctioned half; the React `key` warning on
the create picker needs its own bug and a ruling. Check the console axis BEFORE claiming a
re-navigation guard closes a flake — read the allure attempt, not the pytest tail.

Related: [[a_retry_must_not_collapse_its_outcomes]] · [[absence_guards_must_watch_the_real_mechanism]]

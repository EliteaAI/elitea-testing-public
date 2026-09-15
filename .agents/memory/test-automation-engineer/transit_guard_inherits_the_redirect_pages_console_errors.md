---
name: A transit guard that re-navigates through a product page inherits that page's console errors
description: Re-navigating past a bad redirect fixes the precondition wait but not a spec-wide console-error axis — the landing page's errors are already in the collector
type: feedback
aliases: [2305 guard console errors, redirect guard console axis, open_list console noise]
tags: [area/social-folders, type/flake-handling, status/resolved]
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

## What to do — the lead's ruling (fix round 2, PR #2306)

Do not filter around it inside the guard (window-scoped or text-keyed drops are masking shapes
the canon has no pattern for). It is an observable decision for the lead, and the ruling was:

1. **Opt in to `exclude_known_defect_urls(errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)`**
   with `# Known defect: #1971` — the same idiom every migrated settings spec uses. URL-keyed,
   never a status code.
2. **Arm the collector AFTER the transit** — `collect_console_errors(page)` is just `page.on`, so
   it can be called late with no API change. Call it the moment `binding.open_list()` returns,
   before the baseline reads, so every case step is covered and nothing is dropped once armed.
   Declared in each spec's docstring as an improvisation (canon gap: "an ADDED console axis is
   scoped to the case's own steps; a transit precondition must not decide its verdict") — the
   lead files the `question` card. The React `key` warning on the create picker stays #656.

Result: 4 consecutive clean invocations of the 3-spec set (toolkits ×2, credentials, unpinned),
`reruns.json == {}` each. Check the console axis BEFORE claiming a re-navigation guard closes a
flake — read the allure attempt, not the pytest tail.

Related: [[a_retry_must_not_collapse_its_outcomes]] · [[absence_guards_must_watch_the_real_mechanism]]

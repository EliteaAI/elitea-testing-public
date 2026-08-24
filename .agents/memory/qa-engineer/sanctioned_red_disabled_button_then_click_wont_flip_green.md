---
name: Sanctioned-RED on a disabled-button assertion followed by a click on that button
description: A soft "to_be_disabled" tied to an open defect does NOT flip green when the defect is fixed if a later step clicks that same button — it flips to a click-actionability timeout.
type: feedback
aliases: [sanctioned red soft assert button, expect.soft to_be_disabled click timeout, known defect flips to timeout]
tags: [area/review, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

`.agents/testing.md` § Merge gate justifies a sanctioned-RED soft assertion on the
promise that it **flips green when the product fix ships**. That promise silently
fails when the soft assertion is `expect.soft(button).to_be_disabled()` and a LATER
step in the same test clicks that same button.

Today (defect open) the button is enabled, the soft assert fails, and the click
works — one clean, deterministic failure. The day the defect is fixed, the button
really becomes disabled: step 5 goes green, and the later `button.click()` blocks on
Playwright's actionability wait and dies as a `TimeoutError` that reads like flake,
not like "this case now needs rework".

Worked example: `automation/tests/ui/toolkits/test_mcp_create_validation.py`
(ELITEA-1924 row, `# Known defect: #633`) — step 5 soft-asserts Save is disabled,
step 6 clicks Save. Reviewed 2026-08-24; accepted as non-blocking because the
present-day signature is deterministic and single-cause, but the test carries a
rework obligation the fix will trigger.

## What to ask at review

When you see `expect.soft(<locator>).to_be_disabled()` (or `to_be_hidden`) tied to a
known defect, scan the rest of the test for an interaction with that same locator.
If there is one, require a comment naming what breaks when the defect closes, so the
next person reads "rework me", not "flaky click".

Related: [[absence_of_request_assertion_registration_window]]

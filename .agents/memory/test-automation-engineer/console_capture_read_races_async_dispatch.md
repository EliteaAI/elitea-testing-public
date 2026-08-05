---
name: Console-capture list read races an async Redux dispatch
description: A capture_console_errors() list read immediately after an expect_response()-wrapped click can miss a console.error that fires inside the click's .then() continuation — the CDP event hasn't been pumped into the Python-side list yet.
type: feedback
---

## What happened (ELITEA-2354, PR #1216)

`AgentHubPage.click_like_button()` clicks the like button inside
`self.page.expect_response(...)` (waits for the `/social/like/...` network
response). The click's success handler (`handleLikeSuccess` →
`updateApplicationInState` → `dispatch(...)`) fires a known, filed Redux
`console.error` (#1215) SYNCHRONOUSLY inside that dispatch, and the SAME
dispatch synchronously updates the Redux store (which the button's rendered
count/`data-liked` reflects).

Checking `console_errors` (a `CapturedConsoleMessages` list from
`capture_console_errors()`) **immediately** after `click_like_button()`
returned produced an EMPTY list — the known defect appeared to not
reproduce at all — even though a manual Playwright-MCP click on the exact
same button, same session, DID show the console error via
`browser_console_messages`. Root cause: Playwright's Python sync API only
pumps pending CDP events (including `Runtime.consoleAPICalled`, which is
how `page.on("console", ...)` fires) when a blocking call is made — a bare
Python-side list read triggers no pump.

## Fix

Defer the console-list read (and the `pytest.fail()`/`soft_failures`
decision built on it) until AFTER a subsequent Playwright wait that DOES
block — e.g. the same DOM-state assertions the case already needs
(`is_agent_liked()`'s `wait_for(state="visible")`, or a
`wait_for_like_count()` `expect(...).to_have_text(...)`). By the time those
resolve, the pending console event has been delivered. Reordered the test:
click → DOM-state waits (steps 4-5) → THEN a "side-channel check" step reads
`console_errors`. Same fix applied to the mandatory unlike-cleanup block —
read the retrying `wait_for_like_count(..., 0, ...)` FIRST, then inspect
`unlike_console_errors`.

## Generalization

Any `capture_console_errors()`/`capture_requests_matching()` list read that
happens right after an action returns (not after an intervening wait) is
suspect for the SAME reason described in
`never_assume_a_transition_settled.md` rule 3 (state reads must be a
polling `expect(...)`, never a synchronous read) — this is the console/
event-listener-buffer variant of that same race, not a new class per se,
but concrete enough to be worth its own note since the failure mode looks
like "the defect doesn't repro" rather than a timeout.

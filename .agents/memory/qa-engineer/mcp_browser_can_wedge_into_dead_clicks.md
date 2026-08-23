---
name: The shared MCP browser can wedge into dead clicks — and it mimics a product bug
description: After heavy MCP driving, clicks stopped producing React updates while typing still worked; cost two retracted issue filings. page.goto() in the same context is NOT a pristine repro.
type: feedback
aliases: [wedged browser context, clicks do nothing, retracted bug, false defect, pristine repro gate]
tags: [area/tooling, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## What happened (2026-08-23, credentials-w02, ELITEA-1981/1982)

After ~40 MCP interactions across several SPA navigations, the shared Playwright-MCP
browser reached a state where **every click on a `BaseCheckbox`-backed control**
(credential auth radios, the Auto Refresh Token checkbox) stopped producing a React
state update, and the Test-connection / Login handler stopped firing — **while text
inputs, `fill()`, and the Save button kept working normally.**

That partial liveness is the trap. A fully dead page is obvious; a page where
*typing works but radios don't* reads as a precise, well-scoped product defect. I
filed two issues (#1709, #1710) with what looked like solid evidence: element
present, enabled, `pointer-events: auto`, `elementFromPoint` returning the input
itself, three activation shapes tried, no console error, a `window.fetch` spy
showing zero requests, and reproduction on a **second credential type**.

All of it was an artifact of the context. Both issues retracted within the hour.

## Why my "pristine repro" wasn't one

I re-tested after three full `page.goto()` page loads and treated that as pristine.
It isn't: `goto` reloads the **document**, keeping the **browser context**. Whatever
was wedged (input plumbing / event routing) survived it.

## The gate to actually run before filing an unresponsive-control bug

1. **Run the nearest merged spec** that touches the same control.
   `tests/ui/toolkits/test_credential_create.py` clicks an auth radio and asserts
   `is_checked()` — 15 s, and it passed, which blew the whole theory open.
2. **Re-run the scenario in a fresh `browser.new_context()`** — a ~20-line throwaway
   `sync_playwright` script under `/tmp`, driven with `../.venv/bin/python`. Every
   step passed there.

Both are cheaper than one issue filing, let alone a retraction.

## Smell list — suspect the context, not the product, when

- clicks are dead but typing works (or any *partial* liveness);
- the first interaction of the session worked and nothing since has;
- the failure spans **unrelated** surfaces/types (I "reproduced" it on Jira too —
  which I read as "app-wide regression, worse than I thought" when it should have
  read as "my browser, not their code");
- a handler produces **zero** network requests **and** zero console errors. Real
  product bail-outs usually leave a trace somewhere.

Related: [[mui_keepmounted_dialog_presence_is_not_open]] ·
[[shared_mcp_browser_carries_viewport_across_dispatches]] ·
[[network_capture_timing_can_manufacture_a_false_bug]]

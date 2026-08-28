---
name: base_page.capture_console_errors is the URL-less shape
description: Two console-capture helpers exist; the BasePage one drops the failing resource URL the project's noise ledger keeps asking for
type: feedback
aliases: [console capture helper, collect_console_errors, capture_console_errors, console error url]
tags: [area/console-errors, type/review-check]
created: 2026-08-28
updated: 2026-08-28
---

## The two helpers are not interchangeable

- `BasePage.capture_console_errors()` (`automation/pages/base_page.py:430`) — attaches
  `page.on("console")`, appends raw `ConsoleMessage` objects. Specs then print
  `[m.text for m in console_errors]`, which is **URL-less**: for
  `Failed to load resource: ... 500` the browser puts the resource URL in
  `msg.location`, never in `msg.text`.
- `utils/console_errors.collect_console_errors(page)` — same capture, renders each
  message as `"<type>: <text> @ <url>"`. This is the shape
  `.agents/testing.md` § Unconfirmed asks new/touched specs to migrate to, because
  only migrated specs can name the resource behind the recurring 400/404/500 noise
  class (the standing ask that is still unfulfilled).

## Reviewer check

An AFS that says "console errors via `utils/console_errors.collect_console_errors`"
and a spec that calls `analytics_page.capture_console_errors()` are NOT the same
thing — the assertion strength is identical, the diagnosability is not. It is
invisible to every mechanical grep (both are legal, neither is a locator or a
substitution) and easy to inherit from a neighbouring merged spec, so check it by
name whenever a new spec asserts `not console_errors`.

Seen 2026-08-28 on PR #1953 (settings-w06, ELITEA-2311/2322/2324/2325): four brand-new
specs, all four AFS specced the migrated helper, all four shipped the BasePage one.

Related: [[console_assertion_window_gap]] · [[console_noise_filters_518_554_are_stale_closed]]

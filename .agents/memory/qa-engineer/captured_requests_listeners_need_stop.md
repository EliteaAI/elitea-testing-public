---
name: capture_requests_matching() leaks listeners unless .stop() is called
description: BasePage.capture_requests_matching attaches page.on listeners that stay live for the page's lifetime; its own docstring warns unstopped captures can hang later tests
type: feedback
aliases: [capture_requests_matching, CapturedRequests, network capture leak, requests.stop()]
tags: [area/framework, type/gotcha]
created: 2026-08-21
updated: 2026-08-21
---

## The gotcha

`BasePage.capture_requests_matching(url_substring, method=None)`
(`automation/pages/base_page.py:366`) attaches BOTH a `page.on("request")` and a
`page.on("response")` listener and returns a live-updating `CapturedRequests`.
Its docstring is explicit: *"Call `.stop()` when done capturing to remove the
event listeners and prevent resource leaks. Failing to call `.stop()` can cause
test hangs in subsequent tests."*

The suite is **inconsistent** about this, so copy-paste propagates the leak:

- stops:  `test_artifacts_upload_path_cancel.py:242` (ELITEA-1825)
- does not stop: `test_artifacts_upload_duplicate_cancel.py` (ELITEA-1832, merged),
  `test_artifacts_upload_duplicate_replace.py` / `_close_x.py` (ELITEA-1830/1833)

Second-order effect specific to zero-request assertions: an earlier, still-attached
capture on the SAME substring keeps appending after its assertion ran, so reading
it later measures a different window than the reader expects. Harmless when each
capture is asserted once, immediately — which is exactly what makes the omission
easy to miss in review.

## Reviewer disposition

Important, not a solo blocker while the family precedent is split and the page is
per-test. Ask for `.stop()` after the capture's last assertion; flag it every time
so the merged half of the family converges instead of the unstopped half spreading.

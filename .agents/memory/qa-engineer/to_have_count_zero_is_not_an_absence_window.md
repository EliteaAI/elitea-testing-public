---
name: to_have_count(0) does not observe a time window
description: Playwright expect().to_have_count(0, timeout=N) passes on the FIRST poll when count is already 0 — it never watches N ms for something to appear
type: feedback
aliases: [toast absence assertion, no success notification, absence check, to_have_count zero]
tags: [area/assertions, type/gotcha]
created: 2026-08-21
updated: 2026-08-21
---

## The trap

`expect(locator).to_have_count(0, timeout=2000)` is the suite's standard
"no success notification is displayed" assertion (artifacts specs:
`test_artifacts_upload_duplicate_cancel.py:243`,
`test_artifacts_upload_path_cancel.py:247`). Playwright's web-first
assertions retry **until the condition holds** — with count already 0 at the
first poll the assertion returns immediately. The `timeout` is a *deadline*,
never a *dwell time*. A toast that renders 300 ms later is not caught.

Docstrings/comments in the suite describe this as asserting absence "over a
short POLLED window" — that description is wrong, and it is the reason the
weakness has propagated by copy.

## What actually proves absence

- The strong form used alongside it: capture network traffic across the
  action (`capture_requests_matching(...)`) and assert the list is empty —
  a toast can only follow a request that never fired.
- Re-read the observable after a state change that would have surfaced it
  (reload + re-navigate), so the server, not the un-refreshed client, is the
  oracle.
- If a real dwell is wanted, assert the POSITIVE precondition first (e.g.
  wait for the dialog to be hidden), then a `wait_for_selector(state=
  "attached", timeout=N)` that is expected to raise, or poll explicitly.

## Reviewer disposition

Not a solo blocker where redundant strong evidence exists (zero-requests +
post-reload re-read). Flag it as Important so the wrong claim in the comment
does not keep spreading.

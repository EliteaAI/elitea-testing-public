---
name: Verify Playwright error-string claims against the installed driver bundle
description: Error-message allowlists are folklore until greped in coreBundle.js — narrow AND too-narrow are both defects
type: feedback
---

When a fix classifies exceptions by **message content** (an allowlist of error
fragments), the review question is two-sided: *is it too wide* (blanket catch in
disguise) and *is it too narrow* (a real variant missing → the bug returns).

Both are answerable statically. The installed driver is the ground truth:

```
B=.venv/lib/python3.13/site-packages/playwright/driver/package/lib/coreBundle.js
grep -oiF "Execution context was destroyed" $B | wc -l
grep -rhoiE '"[^"]{0,40}(was destroyed|was detached|not available)[^"]{0,40}"' \
  .venv/lib/python3.13/site-packages/playwright/driver/package/lib | sort -u
```

The second form is the one that catches *too narrow* — it enumerates every
nearby phrase the bundle can emit, instead of only confirming the ones already
in the allowlist. Also grep `playwright/_impl/*.py`: some strings are raised
from the Python side, not the driver (e.g. `_frame.py` "Navigating frame").

Verified 2026-09-07 for Playwright **1.61.0** (PR #2025 / #2023): the
navigation-race class is exactly
`Execution context was destroyed[, most likely because of a navigation]` and
`Frame was detached` / `Navigating frame was detached!` (plus the
`"; maybe frame was detached?"` suffix appended to cancelled navigations, which
the same lowercase substring covers). `Cannot find context with specified id`
and `Execution context is not available` — both widely cited for this race —
have **0 hits** in 1.61.0 and are correctly excluded. `Target page, context or
browser has been closed` and `Session closed` exist but are genuine failures,
not races: they must propagate.

Also check the **type gate**: a message-only classifier that omits
`isinstance(error, PlaywrightError)` will swallow a `RuntimeError` carrying the
same text. And remember `TimeoutError` subclasses `Error` in Playwright, so
`except PlaywrightError` catches timeouts — the classifier must say no to them
explicitly.

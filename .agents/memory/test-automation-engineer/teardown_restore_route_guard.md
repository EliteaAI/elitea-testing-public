---
name: Teardown that reads a page element must be route-guarded and non-masking
description: A `finally` teardown reading a locator raises where the test died and replaces the real failure — guard on page.url, best-effort on the failure path
type: feedback
aliases: [teardown masking, finally block teardown, restore shared state, route guard teardown]
tags: [area/ui-tests, type/pattern]
created: 2026-08-29
updated: 2026-08-29
---

## The two failures of a bare `finally` teardown

Any spec that mutates shared `${TEST_USER}` state restores it in teardown. The
naive shape reads the current value first:

```python
finally:
    if original and page_object.get_value() != original:   # ← both bugs live here
        ...restore...
```

1. **It cannot run where the test most often dies.** `get_value()` resolves a
   locator and calls `inner_text()`, which auto-waits. If the body failed on a
   step that navigated elsewhere (`/settings/notifications` for ELITEA-2387),
   the element is absent, the read burns the full timeout and raises — so the
   restore never happens and shared state stays dirty.
2. **It masks the real failure.** An exception raised inside `finally` REPLACES
   the in-flight one (the original survives only as `__context__`), so a
   one-line assertion failure is reported as a 30s `TimeoutError` on an
   unrelated locator.

## The shipped shape

`try / except BaseException: <best-effort restore>; raise / else: <strict restore>`
— never `finally`. The restore helper guards on `page.url` and re-opens the
route it needs before touching any locator. Best-effort (swallow + `logger.warning`)
only on the already-failed path; strict on the success path, so a genuine
restore failure still fails the test instead of leaking shared state silently.

Unit-testable with a fake page object whose reads raise off-route — see
`automation/tests/unit/test_personalization_restore_route_guard.py`
(red-green verified: the pre-fix shape fails 2 of its 4 tests).

Origin: reviewer finding, PR #1961 (ELITEA-2387), fix round 1.

Related: [[project_briefing]]

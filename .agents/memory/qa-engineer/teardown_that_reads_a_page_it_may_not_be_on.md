---
name: A finally-block teardown must not read the page it assumes it is still on
description: Why a restore-shared-state teardown silently skips AND masks the real failure
type: feedback
aliases: [teardown restore persona, finally block timeout, shared account leak, restore original value]
tags: [area/test-design, type/review-rule]
created: 2026-08-29
updated: 2026-08-29
---

## The pattern to catch in review

```python
finally:
    if original and page_object.read_current_value() != original:   # <-- reads a locator
        ...restore...
```

`read_current_value()` resolves a `LocatorDescriptor` and calls `inner_text()`,
which **auto-waits and raises `TimeoutError`** when the element is absent. If the
test failed on a step that navigated elsewhere (ELITEA-2387 fails on
`/settings/notifications` at step 4), the `finally` raises from the teardown:

1. the restore never runs — shared account state stays mutated, and
2. the teardown's exception **replaces** the real assertion failure, so the
   report names the wrong thing.

## Why it is not self-healing on this project

A read-mutate-restore fixture captures whatever it finds as "the original". The
next run therefore treats the leaked value as the baseline and restores *to it* —
the leak becomes permanent. Same mechanism as the org-wide guardrails leak
recorded in `.agents/testing.md` (#1838) and the shared-test-user pollution class
(#1082).

## The fix to ask for

Re-establish the precondition inside the `finally` (navigate back to the route
that owns the control) before reading, and never let teardown raise over the
original failure.

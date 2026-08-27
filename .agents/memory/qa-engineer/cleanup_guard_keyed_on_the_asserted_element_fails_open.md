---
name: Cleanup guard keyed on the asserted element fails open
description: A finally-block that restores shared state only when the element under assertion is absent skips restoration on the test's own failure path
type: feedback
aliases: [finally guard, cleanup fails open, restore project finally, shared state pollution]
tags: [area/review, type/anti-pattern]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

A spec that asserts an element is ABSENT under some shared-state vantage
(a switched project, a switched user, a toggled org setting) often restores
that shared state in a `finally`. If the guard is written as

```python
finally:
    if not page_obj.thing_under_assertion.count():   # "am I still on the bad vantage?"
        restore_shared_state()
```

it **fails open exactly when the test fails for the reason it exists**: if the
element is wrongly PRESENT on the restricted vantage (the regression the test
hunts), `count()` is non-zero, the restore is skipped, and every later spec in
the invocation inherits the polluted shared state.

Seen live: ELITEA-2348 (`test_viewer_role_cannot_access_secrets.py`), where the
guard keyed on `settings-nav-item-secrets` — the very item asserted absent on
the viewer project — so a real viewer-permission regression would have parked
the whole suite on project 471.

## The rule

Restore shared state **unconditionally**, or key the guard on an INDEPENDENT
observable (the active project id in the selector, the logged-in identity), never
on the element the test asserts. Cleanup must not depend on the assertion
holding.

Related: [[.agents/testing.md § Suite-health pointer]] — the `#1082`
shared-test-user pollution class this compounds.

---
name: best_effort in finally downgrades the success path
description: A teardown restore wrapped in best_effort inside `finally` swallows failures on the GREEN path too — split except/else instead
type: feedback
aliases: [teardown finally best_effort, strict teardown, restore leaks shared state, finally runs on both paths]
tags: [area/test-teardown, type/anti-pattern]
created: 2026-08-29
updated: 2026-08-29
---

## The shape that looks right and isn't

`best_effort(...)` exists for ONE reason: on the failure path a teardown
exception **replaces** the in-flight failure in the report (the original
survives only as `__context__`), so a one-line assertion failure gets reported
as an unrelated 30s `TimeoutError`.

Putting it in `finally` therefore looks like the safe choice. It is not —
`finally` runs on the **success** path as well, where there is no failure to
protect, so the wrapper silently converts "the restore failed" into a logged
warning under a **PASS**. On a spec that mutates shared `${TEST_USER}` account
state (persona, instructions, a toggle) that is a silent leak onto every later
spec that reads it, with a green report saying nothing happened.

## The correct shape

```python
try:
    ...body...
except BaseException:
    best_effort(restore_a, "…")   # failure path only: never mask the real failure
    best_effort(restore_b, "…")
    raise                          # re-raise, always
else:
    restore_a()                    # success path: STRICT — allowed to fail the test
    restore_b()
```

## The carve-out worth keeping

Not every cleanup owes strictness. Cleanup whose failure **cannot corrupt what a
later spec reads** may stay best-effort on both paths — ELITEA-2384's
`conversation_api.delete_conversation()` only adds to the `#1082` shared-account
pollution class. The rule targets **state restores**, not "any cleanup".

## Pinned mechanically

`automation/tests/unit/test_teardown_restores_are_strict_on_success_path.py`
walks the family specs' AST: no `best_effort` inside a `finalbody`, and any
`try` whose handlers call `best_effort` must have a non-empty `orelse` plus a
`raise`. Static, so it costs no browser.

Origin: PR #1964 review (ELITEA-2384, settings-w08), 2026-08-29.

Related: [[teardown_restore_route_guard]]

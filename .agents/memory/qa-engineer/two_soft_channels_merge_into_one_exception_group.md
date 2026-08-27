---
name: expect.soft + a finally-drained pytest.fail merge into ONE ExceptionGroup
description: Verified in-venv — pytest-playwright wraps a hard failure and all soft errors into one BaseExceptionGroup, so "two soft channels" is still one aggregated report
type: feedback
aliases: [two soft channels, soft scope exception group, finally drain sanctioned red, closed-set identical mechanism]
tags: [area/review, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## The verified mechanism

`.venv/lib/python3.13/site-packages/pytest_playwright/pytest_playwright.py:99-118`
(`pytest_playwright` 0.8.0) wraps every test in `_soft_scope()` and, at the end of
`pytest_runtest_call`:

```python
if not errors:
    if hard_failure is not None: raise hard_failure
    return
if hard_failure is not None:
    raise _BaseExceptionGroup("Test and soft assertion failures", [hard_failure, *errors])
```

So a spec that uses **both** soft channels — `expect.soft(...)` for locator-backed
observables, and a `soft_failures` list drained by `pytest.fail()` from a `finally`
for observables with no locator — produces exactly **one** aggregated report:
one `BaseExceptionGroup` carrying the `pytest.fail` plus every soft error. Nothing
is lost, nothing is bucketed, and (because a `try/finally` with **no `except`**
catches nothing) an unknown failure cannot be silently reclassified as a known one:
Python chains it via `__context__` and it appears in the same group.

## Why a reviewer needs this

`.agents/testing.md` § Merge gate, closed-set variant says *"All terminal failures
must route through the identical mechanism (one `soft_failures`/`pytest.fail()`
aggregation, not separate ad-hoc catches)"*. Read literally, two channels look
non-compliant. Read against what the clause is FOR — no ad-hoc `except` deciding
which bucket a failure lands in — two channels are compliant, because the aggregation
happens once, in the plugin, below both of them.

Do not reinterpret the clause silently (see
[[sanctioned_red_requires_single_failure_signature]] round-2, which warns against exactly
that). Verify the reasoning, approve if sound, and recommend the canon amendment —
"one aggregated report" rather than "one mechanism" — as a `question` card, per
`.agents/role-overrides.md` § Declared-improvisation protocol.

## The masking trap this closes

A soft-failure list drained **in the test body** (not from `finally`) is silently lost
whenever a later step fails hard — the drain is never reached. Field-observed 3/3 on
ELITEA-2212 before the fix: the #1834 "file never deleted" finding vanished behind a
later hard failure. **The drain must be in `finally`.** Grep any sanctioned-RED spec
for its drain site before approving.

Related: [[sanctioned_red_requires_single_failure_signature]] · [[phase2_amendment_leaves_stale_doc_claims]]

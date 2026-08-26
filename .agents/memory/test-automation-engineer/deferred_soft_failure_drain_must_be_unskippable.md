---
name: Deferred soft-failure drain must be unskippable
description: A soft-failure list drained at the end of a test body is silently discarded by any later hard failure — drain from `finally`
type: feedback
aliases: [soft_failures, pytest.fail aggregation, sanctioned-RED drain, expect.soft, deferred assertion]
tags: [area/test-design, type/masking-hazard]
created: 2026-08-27
updated: 2026-08-27
---

## The hazard

The common sanctioned-RED shape — collect known-defect symptoms into a `soft_failures` list, then
`pytest.fail()` once at the end of the test body — **loses every collected finding** if any later
assertion fails hard first. Execution never reaches the drain, and the report shows only the hard
failure. There is no error, no warning, and nothing in the Allure step trail hints that a soft
finding was recorded and dropped.

Measured on ELITEA-2212 (2026-08-27, PR #1836): the #1834 "tool did not execute" finding was
recorded and then discarded on **3 of 3** runs, behind an unrelated hard failure two steps later.
It only surfaced after the drain moved into a `finally`.

## The rule

```python
try:
    ...steps that may record soft failures AND may fail hard...
finally:
    if soft_failures:
        pytest.fail(...)
```

Python chains the two exceptions, so neither finding is lost. `expect.soft()` does not need this —
pytest-playwright collects those in a hookwrapper and re-raises them (as a `BaseExceptionGroup`
alongside any hard failure) regardless of how the body exited. A hand-rolled aggregation has no
such safety net; it is only as reliable as its control flow.

## Corollary — reading the report

`expect.soft` failures do not raise, so Allure marks their step **passed** and the overall result
**broken** (`BaseExceptionGroup`, not `AssertionError`). pytest reports FAILED. Audit a
soft-asserted spec by its failure MESSAGE, never by Allure step colours.

Related: [[project_briefing]]

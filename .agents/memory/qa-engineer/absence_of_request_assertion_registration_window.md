---
name: An "no request fired" assertion must wrap the triggering action, not follow it
description: expect_response only sees traffic after __enter__ — clicking first and waiting after leaves a blind window that turns the guard into a false pass.
type: feedback
aliases: [no POST fired, absence of network request, expect_response race, negative network assertion, registration window]
tags: [area/review, type/heuristic]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

The in-repo idiom for "the product must NOT send request X" is
`page.expect_response(...)` with a short timeout, treating `PlaywrightTimeoutError`
as the PASS. It is only sound when the **triggering action happens INSIDE the
context manager**:

```python
try:
    with page.expect_response(pred, timeout=SHORT):
        button.click()          # <-- inside
except PlaywrightTimeoutError:
    return                      # nothing fired: PASS
raise AssertionError(...)
```

`expect_response` (waitForResponse) only matches events arriving **after** its
`__enter__`. Clicking first and entering afterwards —

```python
button.click()
_assert_no_request(page)        # <-- enters the CM here, after the click
```

— leaves a window in which the very request the guard exists to catch can resolve
unseen. The guard then times out and reports PASS on a genuine regression. Nothing
is red, nothing is skipped, no weakened `expect` — the standard masking greps miss
it entirely (sibling failure mode to
[[absence_assertion_needs_a_proven_detector]]: there the detector *cannot* fire,
here it is merely *not listening yet*).

## The check

When reviewing any negative network assertion, look at where the trigger sits
relative to the `with` block. If the trigger is outside, it is
`CHANGES_REQUESTED` — refactor the helper to take the action as a callable
(`_assert_no_create_request(page, project_id, action=form.save_button.click)`) so
the click is executed inside the window.

Merged precedent doing it right:
`tests/ui/artifacts/test_artifacts_create_bucket_56char_limit_warning_delete_cancel.py:325-332`.
Caught at: ELITEA-1923/1924 (`test_mcp_create_validation.py`), where the racy form
was the only assertion proving "no MCP was created".

Related: [[absence_assertion_needs_a_proven_detector]] · [[absence_assertions_scope_the_side_channel]]

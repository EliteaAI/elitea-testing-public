---
name: Absence-of-request assertions must wrap their trigger
description: expect_response only sees traffic after __enter__ — clicking before opening the waiter makes a "no POST fired" assertion pass vacuously
type: feedback
aliases: [expect_response ordering, no POST fired, absence assertion, vacuous pass, negative network assertion]
tags: [area/playwright, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

Asserting that a request does **not** fire is done with the in-repo idiom
`page.expect_response(pred, timeout=SHORT)` inside `try/except PlaywrightTimeoutError`,
treating the timeout as the PASS.

`expect_response` only matches traffic that arrives after its `__enter__`. So this
shape asserts nothing:

```python
form.save_button.click()          # POST may fire AND resolve right here
_assert_no_create_request(page)   # waiter opens too late — never sees it
```

It reports "no POST fired" on a run where the entity **was** created. Whether it
catches anything at all is a race against the click's own round-trip — which is why
it passes locally and rots silently.

## The shape that works

Pass the trigger in as a callable so the wrong order is unrepresentable:

```python
def _assert_trigger_fires_no_create_request(page, project_id, trigger):
    try:
        with page.expect_response(pred, timeout=NO_REQUEST_WINDOW):
            trigger()
    except PlaywrightTimeoutError:
        return
    raise AssertionError(...)
```

Mirror-image of `McpFormPage.save_and_wait_for_created`, which already wraps its own
click for the presence case — copy that shape, not the two-statement one.

## Verified

Red/green out-of-band, 2026-08-24 (ELITEA-1923/1924 fix round 1): with the response
forced to land before `__enter__`, click-then-wait reported "no POST seen" while
trigger-inside-waiter correctly detected the POST. Caught in review, not by a run —
no test failure can surface this, because the bug's symptom IS a pass.

Related: [[absence_guards_must_watch_the_real_mechanism]] · [[project_briefing]]

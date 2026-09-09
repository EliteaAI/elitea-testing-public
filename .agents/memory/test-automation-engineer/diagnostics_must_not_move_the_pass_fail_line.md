---
name: Diagnostics must not move the pass/fail line — record, don't re-match
description: Enrich a wait's failure message with a response listener; never loosen the wait predicate to get a better error.
type: feedback
aliases: [expect_response diagnostics, opaque timeout, waiting for event response, failure message endpoint status]
tags: [area/playwright, type/pattern]
created: 2026-09-09
updated: 2026-09-09
---

## The problem

`page.expect_response(lambda r: URL in r.url and r.status == 200, timeout=60_000)`
gives a useless failure when the endpoint answers 5xx: it waits the FULL budget and
dies with `waiting for event "response"` — naming neither the endpoint nor the status.
On a spec that navigates three times, that is ~3 minutes of opaque red.

## The tempting fix, and why it is wrong

Match on **URL only** and assert the status inside the block. It fails fast and names
the status — but it **latches the first response for that URL**. A redirect, an auth
retry, or any non-200 that legitimately precedes a healthy 200 now fails a run that
would otherwise pass. That is not a diagnostics change; it is a new failure mode.

## The shape that works

Keep the strict predicate. Add a listener that only *records*, and enrich the re-raise:

```python
observed: list[int] = []

def _record(response: Response) -> None:
    if FRAGMENT in response.url:
        observed.append(response.status)

self.page.on("response", _record)
try:
    with self.page.expect_response(lambda r: FRAGMENT in r.url and r.status == 200,
                                   timeout=BUDGET):
        super().navigate("/artifacts")
except PlaywrightTimeoutError as err:
    raise PlaywrightTimeoutError(
        f"No 200 from {FRAGMENT} within {BUDGET} ms. Statuses observed: {observed}."
    ) from err
finally:
    self.page.remove_listener("response", _record)
```

Three details that are load-bearing:

1. **`remove_listener` in a `finally`.** `page` is shared across tests in this suite;
   a leaked listener accumulates on every later test.
2. **Re-raise `PlaywrightTimeoutError`, not `AssertionError`.** Its constructor takes a
   message, so the class survives. Several `.agents/testing.md` triage entries tell you
   to grep `reports/allure-results/*-result.json` for `"status": "broken"` to find
   raw-error-at-a-precondition failures — `AssertionError` flips that to `failed` and
   makes this class invisible to its own triage recipe.
3. **Say "none — the request never completed"** when the list is empty. An empty list
   and a list of 503s are completely different diagnoses, and `[]` reads as neither.

## The general rule

Ask of any "better error message" change: **could this now fail on an input that used
to pass, or pass on one that used to fail?** If yes, it is a behaviour change wearing
diagnostics clothing, and it needs the review a behaviour change gets.

Origin: PR #2080 review finding 3, `ArtifactsPage.navigate_to_artifacts`, 2026-09-09.

Related: [[networkidle_1847_artifacts_landing_is_the_third_site]]

---
name: Hover-gated element as wait condition trap + capture_requests_matching status race
description: A display:none-until-hover element can never satisfy Locator.wait_for(state="visible") on a row nobody has hovered — wait on the row's own testid instead; and capture_requests_matching() can read status:None right after a click resolves for POSITIVE status assertions — use page.expect_response() instead (proven for negative/absence checks only)
type: feedback
---

## A hover-gated element cannot be the "did X appear" wait condition

`BucketItem.jsx`'s dot-menu trigger button is `display: isHovering || showMenu
? 'flex' : 'none'` — hidden until the row is hovered. The AFS (ELITEA-1808)
suggested waiting on this button's own testid becoming visible as proof "the
new bucket appeared in the list" after Save. Live result: `TimeoutError` —
`locator resolved to hidden <button>` (23 retries, still hidden), because
nobody had hovered the row yet.

**Fix:** wait on the ROW's own testid instead (added `artifacts-bucket-row-{name}`
on `BucketItem.jsx`'s outer `Box`, which is NOT hover-gated). General rule:
before using any element's visibility as a "did the thing render" condition,
check whether that specific element is itself gated behind a DIFFERENT
interaction (hover/focus/click) from the one you're actually waiting on — if
so, pick an ungated ancestor/sibling instead, or add a testid to one.

## `capture_requests_matching()` is proven for negative checks, NOT positive status assertions

ELITEA-1832 established `BasePage.capture_requests_matching()` (async
request/response listener pair, returns a live-populated list) — but only
ever used it for `assert not requests` (proving NO network call fired).
ELITEA-1808 was the first case to assert a POSITIVE `status == 200` from it,
and hit a live race: `status: None` read immediately after the triggering
click resolved and the file/bucket row was already visible in the DOM
(client optimistic UI outran the Python-side response listener). Adding
`wait_for_network()` (networkidle) before the check did NOT reliably fix it.

**Fix:** use `page.expect_response(lambda r: ...)` instead — already an
established idiom elsewhere in this codebase (`CredentialDetailPage`'s
pin-toggle response wait). It BLOCKS until the matching response actually
lands, no polling/race. Pattern for a NEW page-object method (don't touch an
EXISTING shared click method just to add response-wrapping — see the
additive-sibling note below):

```python
def click_x_and_capture_response(self, timeout=15000):
    with self.page.expect_response(
        lambda r: "url/substring" in r.url and r.request.method == "PUT",
        timeout=timeout,
    ) as response_info:
        self.click_x()  # delegate to the existing method, don't duplicate its body
    return response_info.value
```

## Additive-sibling method when you can't modify a shared click method

`click_upload_path_upload_button()` (ELITEA-1832) could NOT be changed to
wrap `expect_response`, because ELITEA-1832's own test relies on it firing
**zero** network requests on the duplicate-file path — wrapping a
response-wait there would time out on that legitimate no-request outcome.
Added `click_upload_path_upload_button_and_capture_response()` as a new,
additive sibling that internally calls the existing method inside its own
`with expect_response(...)` block, rather than duplicating the click logic
or touching the shared method's body. General shape for "I need response-
capture behavior on a click method other callers use differently."

(from ELITEA-1808, PR #643)

## Addendum — a second valid fix: defer the READ, not the capture mechanism

ELITEA-1826 (3 concurrent PUTs from one multi-file Upload click) hit the same
`capture_requests_matching()` status race, but `page.expect_response()`
doesn't scale as cleanly here — it would mean 3 nested context managers
keyed by filename around one click, more ceremony than the flow needs when
an independent completion signal already exists. Alternative fix that also
works: keep `capture_requests_matching()`, but don't read/assert on the
returned list immediately after the click — defer the read until AFTER a
separate, reliable completion condition has already resolved (here: the
file-table's `get_total_file_count_from_pagination() == 3` /
`get_file_names()` check, itself required by the case). Since the UI-visible
completion state is only reachable once the server has actually returned
each PUT's response, by the time that condition holds, every entry in the
captured list is guaranteed to have a resolved (non-`None`) status — no
polling, no `page.expect_response()` nesting, zero race. Rule of thumb:
`page.expect_response()` when there's no other completion signal to piggy-back
on (or the count is small/fixed); defer-the-read on the existing capture
list when the test already condition-waits on something the network calls
must have finished before (from ELITEA-1826, PR pending).

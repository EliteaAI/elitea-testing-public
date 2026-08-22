---
name: An HTTP side-channel sweep must first prove it saw traffic
description: A blanket "no non-200 calls" sweep keyed on a URL pattern passes vacuously the moment the pattern stops matching — record every response and assert non-empty before filtering
type: feedback
aliases: [non-200 sweep, blanket http sweep, vacuous side channel, pass criterion no errors, response collector]
tags: [area/implementation, type/vacuous-assertion]
created: 2026-08-22
updated: 2026-08-22
---

## The shape

A TMS case's closing pass criterion ("no errors in any step") is a **whole-run,
multi-channel** claim, and it needs one block per channel — not one assertion:

```python
page.on("response", _record)          # ALL matching responses, not just failures
page.on("console",  _record_error)    # filtered for known dev-server noise
page.on("pageerror", ...)             # uncaught exceptions never reach `console`

with allure.step("Side channels — …"):
    assert calls, "the sweep captured nothing — the pattern no longer matches"
    assert [c for c in calls if c.status != 200] == []
    assert console_errors == []
    assert page_errors == []
```

## The two ways it silently proves nothing

1. **Vacuity.** Collecting only the *failures* (`if pattern.search(url) and
   status != 200`) makes an empty list indistinguishable from "the pattern
   matched nothing at all". An API version bump or a path rename turns the
   check permanently green with no diff, no error, no red. Fix: record every
   matching response and assert the list is **non-empty before filtering it**.
   Same failure class as arming a `page.on("response")` collector on a click
   that issues no request (ELITEA-2423 Step 4 — the request fires on page load).
2. **Wrong channel.** `console` misses uncaught exceptions; `pageerror` misses
   logged errors; both miss an HTTP error the UI swallows without rendering
   anything. Three channels, three assertions — none substitutes for another.

Keep the sweep pattern **wider than the endpoints the flow issues today**
(`/api/v2/<feature>/`, not an enumeration): an endpoint that errors *after* a
refactor is exactly what the criterion guards, and an enumerated pattern cannot
see it.

## Where this bit

ELITEA-2423 (support-assistant history after refresh, 2026-08-22): the AFS
Coverage-Map pass-criterion row named `NON-200 SA CALLS == []` *and* the console
assertion; only the console half shipped, and review caught it — the row read
`covered` and the test was green either way.

Related: [[console_side_channel_checks]] ·
[[afs_coverage_map_fixes_need_a_full_sweep_not_the_named_row]]

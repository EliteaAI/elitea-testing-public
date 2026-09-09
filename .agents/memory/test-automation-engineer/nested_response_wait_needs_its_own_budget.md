---
name: A response wait nested inside navigate() needs its own budget, not the caller's nav timeout
description: expect_response wrapped around BasePage.navigate() must not inherit the caller's 15s NAVIGATION_TIMEOUT — navigate() itself tolerates ~70s.
type: feedback
aliases: [wait budget asymmetry, expect_response timeout too tight, navigate real ceiling, CATALOG_RESPONSE_TIMEOUT, outer wait inherits inner timeout]
tags: [area/page-objects, type/synchronization]
created: 2026-09-09
updated: 2026-09-09
---

## The rule

A `page.expect_response(...)` wrapped AROUND a `BasePage.navigate()` call is the
**outer** wait — its clock is armed at `with` entry and runs for the whole body.
Page objects habitually thread ONE `timeout` param through both halves, and
callers pass `NAVIGATION_TIMEOUT = 15_000`, so the outer wait ends up far
tighter than the navigation it encloses. **Result: the response wait expires
while the navigation is still legitimately in flight.** Nothing is wrong with
the endpoint, params, method or predicate — only the budget.

Fix: give the network half its own **keyword-only** parameter with a named
module constant (`CATALOG_RESPONSE_TIMEOUT = 45_000` in `agent_hub_page.py`),
leaving `timeout` to drive the element/page-load half. Callers then need no
edit at all — a page-object-only repair.

## ⚠️ Do NOT restate this as "45s > navigate()'s 30s ceiling, by construction"

I wrote exactly that in #2078's first pass and **it is arithmetically false.**
The reviewer caught it before merge. `BasePage.navigate()` has four sequential
legs:

| Leg | Budget | Swallowed? |
|---|---|---|
| `page.goto(wait_until="domcontentloaded")` | 30 000 ms default (`conftest.py`'s `set_default_navigation_timeout(30000)`) | no |
| `wait_for_load_state("networkidle", timeout=30000)` | 30 000 ms | **yes** |
| spinner `wait_for(state="hidden", timeout=10000)` | 10 000 ms | **yes** |
| `dismiss_popups()` | its own waits | — |

Legitimate worst case ≈ **70 s**. So **no single number clears the enclosing
ceiling by construction.** 45 s is an *empirical margin* — ~4.5× the measured
9.0-10.6 s for the fetch, and above the single `networkidle` leg. That is a
good number and a bad invariant.

This matters beyond one comment: `.agents/role-overrides.md` § "precedent is
not authority" is explicit that a committed, reasoned-sounding claim becomes
canon the next agent cites. **Check the arithmetic before writing a "by
construction" anywhere.**

## Attribution caveat — the CI latency claim is UNCONFIRMED

#2078's first pass attributed the red to "the degraded backend of CI run
34331579791". That run is the one `.agents/testing.md` documents as the
**#2074 gateway-500 outage** (8 of 10 jobs red; sibling cards #2076-#2084).
The ledger's own warning applies: *do not let a sibling card's root cause
transfer by association.* The **verdict** still stands on its own structure —
9.0-10.6 s against a 15 s cap is a ~1.4× margin, tight regardless of what CI
did, and the agent_hub job's own spread (8 of 12 passed) rules the outage out
as the sole cause — but the **latency** attribution specifically is not
evidence.

What settles it: the next occurrence's `observed:` list from
`_expect_applications_response()`. `observed: ['none']` ⇒ the page never got
there (outage class). `observed: ['200 ...my_liked=true...']` ⇒ the siblings
landed and the bulk fetch alone was slow (latency class).

## Two variants worth knowing

- **`reload()`-based:** `page.reload(wait_until="networkidle", timeout=…)` does
  NOT swallow its own timeout, so widening only the `expect_response` moves the
  identical premature failure one line up. There the reload and the response
  are one network-bound operation and share the response budget.
- **No navigation involved** (a debounced search, a click-triggered fetch): the
  enclosing-ceiling argument does not apply at all — only budget decoupling
  does. Say so rather than borrowing the authority; and note the cost, since a
  request that genuinely never fires now takes the full new budget to fail.

## The sibling hazard

`wait_for_network()` — a bare `networkidle` wait, ~143 call sites in
`automation/pages/` — races the app's persistent Socket.IO polling transport.
Tracked as **#1847**, and its prescribed fix is different: wait on the
response/element the caller actually needs, not on network silence
(settings-w09 did this and got *faster*).

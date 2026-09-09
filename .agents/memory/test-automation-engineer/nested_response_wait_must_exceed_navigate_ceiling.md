---
name: A response wait nested inside navigate() must exceed navigate()'s own 30s ceiling
description: expect_response wrapped around BasePage.navigate() must not share the caller's 15s nav timeout — navigate() itself allows 30s.
type: feedback
aliases: [wait budget asymmetry, expect_response timeout too tight, navigate networkidle 30s ceiling, CATALOG_RESPONSE_TIMEOUT]
tags: [area/page-objects, type/synchronization]
created: 2026-09-09
updated: 2026-09-09
---

## The rule

`BasePage.navigate()` (`automation/pages/base_page.py`) does
`goto(wait_until="domcontentloaded")` and then allows the navigation up to a
**30 000 ms** `networkidle` wait, whose timeout it **swallows**. So any
`page.expect_response(...)` wrapped AROUND a `navigate()` call is the outer
wait but usually gets the tighter number, because page objects habitually
thread ONE `timeout` param through both halves and callers pass their
`NAVIGATION_TIMEOUT = 15_000`.

**Result: the response wait expires while the navigation it wraps is still
legitimately in flight.** Nothing is wrong with the endpoint, the params, the
method or the predicate — only the budget.

Give the network half its own keyword-only parameter with a named module
constant above 30 s (`CATALOG_RESPONSE_TIMEOUT = 45_000` in
`agent_hub_page.py`), and leave `timeout` driving the element/page-load half.
Callers' constants then need no edit at all — a page-object-only repair.

## How it presents

Green locally, red on a loaded/degraded backend, and the failure **names the
wrong subsystem** — the same trap as `#2074` and `#2076`. The Agent Hub case
(#2078) measured 9.0-10.6 s of a 15 s budget on a healthy backend for
`/public_applications/prompt_lib/?...&limit=1000&offset=0` (~2.5-3.0 s of raw
backend time vs ~0.35 s for the `limit=20` variants, and gated behind
`agent_categories` resolving first). Two thirds of the budget already spent on
a good day = deterministic red on a bad one.

**A `reload()`-based variant needs more care:** `page.reload(wait_until=
"networkidle", timeout=...)` does NOT swallow its own timeout, so capping the
reload at 15 s while widening only the `expect_response` just moves the same
premature failure one line up. There, the reload and the response are one
network-bound operation and share the response budget.

## Where the same shape still lives

`wait_for_network()` (a bare `networkidle` wait, ~143 call sites in
`automation/pages/`) is the sibling hazard, tracked as **#1847** — it races the
app's persistent Socket.IO polling transport. Its prescribed fix is different:
wait on the response/element the caller actually needs, not on network silence
(settings-w09 did this and got *faster*).

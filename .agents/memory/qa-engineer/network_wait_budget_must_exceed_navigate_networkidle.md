---
name: Network-response wait budgets must exceed the navigate() they wrap
description: Why expect_response helpers fail on DEV while every sibling test on the same page passes
type: feedback
aliases: [expect_response timeout, navigate_and_capture_applications, catalog bulk fetch, 15s response timeout]
tags: [area/ui-tests, type/robustness]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

`BasePage.navigate()` (`pages/base_page.py:358-365`) does
`goto(wait_until="domcontentloaded")` then `wait_for_load_state("networkidle", timeout=30000)`
and **swallows** the timeout. So any helper shaped like

```python
with self.page.expect_response(pred, timeout=15000):
    super().navigate(path)
```

gives the response a **15 s** ceiling while the navigation it wraps is allowed **30 s**.
Every ordinary test on the same page therefore tolerates a backend 2x slower than the
capture helper does — which is why a slow deployed env fails ONLY the capture call sites
and leaves ten sibling tests green. That asymmetry looks exactly like UI/API drift and
is not.

**Rule: a network-response budget inside `navigate()` must be >= 30 s (the networkidle
ceiling), and a network wait must never inherit a caller's UI_ELEMENT_TIMEOUT (10 s).**

## Measured, DEV, 2026-09-09 (ELITEA-2354/2363, FIX #2078)

| Call | Latency |
|---|---|
| `GET /public_applications/prompt_lib/?...&limit=1000` (catalog bulk) | 2.54-2.97 s |
| same endpoint, `limit=20` (Trending / My Liked) | 0.34-0.40 s |

Wall clock from `goto()` to the bulk response, warm client: **6.4-8.1 s** on DEV *and* on
localhost (the local vite dev server proxies the same DEV backend, so latency is identical
- localhost is NOT a faster control for anything backend-bound). The bulk call is the
slowest request the catalog makes, ~7-9x the small ones, and it is gated behind
`agent_categories` resolving first (`useAgentHubData.hooks.js` returns early while
`categoryNames.length === 0`).

## Triage tell

A CI failure of this class shows the timeout on the *first* step and names the wrong
subsystem. Read the per-attempt "Captured log call" blocks in the job log, not just the
final traceback: on #2078 one of the three attempts got past step 1 and died later in
`search()`'s own 10 s response wait — proof it was a latency band, not a broken locator
or a changed endpoint.

Related: [[[#1847]]] networkidle vs the persistent /socket.io/ poll (`.agents/testing.md`).

Related: [[base_page_navigate_real_ceiling_is_not_30s]] — the arithmetic correction:
30 s is only ONE of navigate()'s four legs; its real worst case is ~70 s.

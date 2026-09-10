---
name: networkidle is not a settle signal (and is not always unreachable either)
description: Why `wait_for_network()` fails BOTH ways — it can time out in CI and resolve in 0.00s locally while settling nothing
type: feedback
aliases: [networkidle, wait_for_network, "#1847", socket.io settle, search settle]
tags: [area/waits, type/flake]
created: 2026-09-10
updated: 2026-09-10
---

## The two-sided failure

`#1847` frames `networkidle` as *unreachable* because a persistent socket.io poll keeps the
connection count above zero. Measured on `dev.elitea.ai` (2026-09-10, #2166): **same-origin the
transport UPGRADES to a WebSocket** — 0 socket.io requests in a 6 s idle window — so
`wait_for_load_state("networkidle")` resolves in **0.00 s**. The `?EIO=4&transport=polling`
captures in `.agents/testing.md` are a **localhost** topology artifact (the app opens socket.io
cross-origin to dev.elitea.ai from `:5173`).

So a trailing `wait_for_network()` is the worst of both worlds:

- **In CI it can time out** (deterministic 3/3 on run #116) and name the wrong subsystem.
- **Locally it returns instantly and settles NOTHING** — which is the more dangerous half,
  because it hides an unprotected render window. On the Catalog search path that window is
  **802 ms** (`clearCache()` runs before the fetch, `setApplicationsData` only in the response's
  continuation, so `expect_response` resolves against an EMPTY grid).

## The fix shape

Wait on **what the caller needs**, and prefer a **union of the surface's mutually-exclusive
TERMINAL renders** so the wait covers the negative branch too and can never be satisfied by a
loading state:

```python
SEARCH_RESULTS_SETTLED = '[data-testid^="catalog-agent-card-"], [data-testid="catalog-no-results-title"]'
self.page.locator(self.SEARCH_RESULTS_SETTLED).first.wait_for(state="visible", timeout=timeout)
```

Check the loading render carries no testid first — if it does, the union is satisfied too early.

## Companion trap

`Locator.is_visible(timeout=…)` is **deprecated and IGNORED** by Playwright. A caller passing a
timeout there still performs a one-shot read, so it depends entirely on the page object's settle.
Grep for `is_visible(timeout=` when auditing a race.

Related: [[test_environment_scoped_sanctioned_red]]

---
name: A settle can be fragile AND vacuous — removing it is only half the fix
description: networkidle timed out in CI while measuring 0.00s locally; the caller's real need (the render commit) was never covered by anything
type: feedback
aliases: [networkidle useless, "#1847", search settle, clearCache before fetch, response is not the render, vacuous settle, stale state reachability, clear_search]
tags: [area/waits, type/lesson]
created: 2026-09-10
updated: 2026-09-10
---

## The shape

`AgentHubPage.search()` (#2166 / ELITEA-2354) awaited its debounced response correctly, then ran
`wait_for_network()` (`networkidle`). That wait was:

- **fragile** — the CI red, `Timeout 10000ms exceeded`, 3/3 attempts; and
- **vacuous** — measured **0.00 s** on DEV, where socket.io upgrades to a WebSocket. It settled
  nothing while still being able to time out. Worst of both.

The trap is stopping there. `useAgentHubData.searchAndCategorize()` calls `clearCache()` **before**
`await fetchApplications(...)` and dispatches `setApplicationsData` only in the response
continuation — so `expect_response` resolves while the grid is **EMPTY** (measured 802 ms on DEV).
The caller's one-shot `.is_visible()` on the next line had never been protected by anything.

**A response is not a render.** When a page object ends on a network wait, ask what the *caller*
reads on the very next line, and wait for that instead (#1847's own prescription).

## The shape that fixes it

A class-level union of the component's **terminal** renders, so the wait cannot resolve on the
loading state:

```python
SEARCH_RESULTS_SETTLED = (
    '[data-testid^="catalog-agent-card-"], [data-testid="catalog-no-results-title"]'
)
```

`CatalogBody.jsx` renders exactly one of three things; the loading branch is anonymous skeleton
`<Box>`es with **no testid at all** — verify that in source, it is what makes the union safe. Also
compliant testid-only locating (UPPER_CASE constant whose definition is a `[data-testid=` string).

Never raise the timeout instead — 10 s already covered the measured 0.802 s by >12x.

## Two adjacent traps

- **`Locator.is_visible(timeout=)` is deprecated and the argument is IGNORED.** A call site that
  *passes* a timeout is still a one-shot and still races. Convert to
  `expect(...).to_be_visible(timeout=…)` — same assertion, retry budget added.
- Union-settle has a **residual window**: on an already-populated grid a STALE card can satisfy it.
  Safe only because every current caller searches a freshly navigated/reloaded grid. Declare it.

## The residual window is now CONFIRMED and measured — and it makes the union WRONG for the inverse transition (#2168 / ELITEA-2363, 2026-09-10)

The last bullet above predicted it; `clear_search()` proved it. **A terminal-render union is
direction-specific.** For `search()` (unfiltered -> filtered) it is a real signal. For
`clear_search()` (filtered -> unfiltered) the SAME union is **vacuous**, because its
`catalog-agent-card-*` branch is already matched by the *pre-clear filtered* cards — nothing to
wait for. Measured on `dev.elitea.ai`, 27 baseline -> 6 filtered -> clear:

| Wait | Resolves after | Grid state at that instant |
|---|---|---|
| `SEARCH_RESULTS_SETTLED` | **4.72 ms** | 12 of 27 cards — mid-restore |
| the honest signal (`to_have_count(27)`) | **375.84 ms** | restored |

A count-CHANGE wait (`not_to_have_count(6)`) fails too: category sections commit progressively,
so the count leaves 6 within milliseconds while still far from 27.

**The generalisable rule: before reusing a settle, ask whether the state BEFORE the transition
already satisfies it.** If it does, it is vacuous no matter how well it worked for the sibling
method. And when the only terminal signal needs a value only the CALLER knows (here: the baseline
count), the right answer is **no settle at all** plus a documented contract — "returns on the
response; the grid re-renders ~376 ms later, callers MUST read it through an auto-retrying
assertion". A removed vacuous wait beats a clever one; do not invent a wait you cannot show is
both non-vacuous and unable to time out for a reason nobody needs.

Related: [[dev_page_goto_flake_is_a_precondition]] · [[sanctioned_red_can_be_dev_build_only]]

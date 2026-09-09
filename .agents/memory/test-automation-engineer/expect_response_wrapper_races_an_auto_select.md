---
name: expect_response wrapper races a product that auto-selects on open
description: A click wrapped in expect_response silently becomes a race once the product fires that same request itself on mount — replace with a rendered-state wait
type: feedback
aliases: [expect_response race, auto-select on open, run history row click fires no request]
tags: [area/ui-tests, type/flake]
created: 2026-09-09
updated: 2026-09-09
---

## What happened

`PipelineDetailPage.select_run_history_item()` wrapped the row click in
`page.expect_response("/elitea_core/conversation/prompt_lib/")`. `EliteaAI/EliteaUI@84025881`
(*fix: [EL-6391] select the latest run when Run History opens*, 2026-08-26) made the container
auto-select row 0 **on open** and fire that GET itself. Clicking row 0 afterwards fires **zero**
requests — so the wrapper passed only when the auto-select's own response happened to land inside
its expectation window. A latent, environment-timing-dependent false RED that no assertion owned.

## The rule

**`expect_response` proves a request happened inside a window — it does not prove the click caused
it.** Whenever the product may fire the same request on mount / auto-select / prefetch, wait on the
*rendered state the click produces* instead:

```python
row.click()
expect(row).to_have_attribute("data-selected", "true", timeout=timeout)
self.page.locator(self.CHAT_MESSAGE_ITEM_SELECTOR).first.wait_for(state="visible", timeout=timeout)
```

Fidelity is intact — both observables are still produced by the system; only the *signal we wait
on* changed. The corollary for the test: asserting `data-selected="true"` on an auto-selected row
after clicking it is **tautological** and must be dropped, not kept "for safety".

Related: [[run_history_is_a_route_not_a_panel_el6537]]

## Correction (review of PR #2068, fix round 1) — the rule is CONDITIONAL

Removing the response wait outright was wrong for rows the user actually switches to.
`data-selected` flips **synchronously** in `handleHistoryItemSelect`
(`RunHistoryContainer.jsx:156`) before the detail GET is issued, and the previous
conversation's `chat-message-item` nodes persist across the switch (`RunHistoryChat.jsx:51-65`
reads RTK-Query's retained `data`, not `currentData`; `ChatMessageList.jsx:240` maps it
unconditionally and its `Skeleton` is gated on `isLoadingMore`, not `isLoading`) — so BOTH
halves of a rendered-state wait are satisfiable by pre-click state. Live probe 2026-09-09:
immediately after clicking a non-selected row, `data-selected="true"` with **0** message items
rendered — the attribute is definitively not a load signal.

**Branch on whether the click actually causes the request:**
already-selected row (auto-selected row 0) → no request, use the state wait; not-yet-selected
row → keep `expect_response`, then the state wait. Reading the attribute before clicking is the
cheap discriminator.

---
name: Prove ordering determinism by repeating the request, before calling it a bug
description: Repeat the identical query N times; unstable order across runs vs a moved sort key are different verdicts
type: feedback
aliases: [unstable order, tie-break, sort_by likes, trending order, nondeterministic ordering]
tags: [area/agent-hub, type/triage-method]
created: 2026-09-10
updated: 2026-09-10
---

## The method

"The order looked unstable" is an observation, not a classification. Fire the **identical** request
5-6× back to back and compare orders before reaching a verdict — it costs one short script and it
separates two opposite dispositions:

- **Order differs across identical requests** → genuine backend nondeterminism (unspecified
  tie-break) → a product `bug`.
- **Order identical every time** → deterministic; any observed reorder means **the sort KEY moved**,
  i.e. the data changed under you → a test-data / shared-state problem, NOT a product bug.

Worked case: ELITEA-2363. Bulk catalog query **5/5 identical**; Trending query **6/6 identical**,
including inside every like-count tie group. So the CI reorder was a like landing mid-run re-ranking
the only likes-sorted section. Filing "unstable ordering" would have been wrong.

## Read the fetch params, not just the rendering

Confirm *what* sorts before blaming *where* it renders. In `useAgentHubData.hooks.js` the bulk fetch
sends **no** `sort_by` and the frontend never sorts; only `fetchTrendingApplications` sends
`sort_by: 'likes', sort_order: 'desc'` — and Trending renders first. One likes-sorted section was the
entire ordering exposure.

Corollary worth checking every time: a top-N sorted window (here Trending's first 6 of `limit=20`)
means a sort-key change can alter **membership**, not merely order.

Related: [[card_text_is_not_identity]]

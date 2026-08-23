---
name: browser_evaluate busy-poll starves the React render
description: A while-loop poll inside page.evaluate blocks the main thread, so the app can never render — reads a false "element never appears"
type: feedback
aliases: [busy poll evaluate, page.evaluate while loop, list never renders, 0 rows forever]
tags: [area/playwright, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## What happened

While analysing ELITEA-1810 I polled for the Artifacts bucket list from inside
`browser_evaluate`:

```js
while (Date.now()-t0 < 40000) { rows = document.querySelectorAll('...').length; if (rows) break; await new Promise(r=>setTimeout(r,500)); }
```

It returned `0 rows` after the full 40 s — twice — and the page showed the
"No buckets created yet" empty state, which looked like a product defect
(967 buckets exist). A plain single-shot probe **immediately after** returned 967 rows.

## Why

The `await setTimeout` yields the microtask queue but the loop keeps the JS thread hot
enough that React's render/commit for a large list never gets a slot — and, in the MCP
transport, the whole evaluate is one blocking call. The element genuinely was not in the
DOM *while I was asking*, precisely *because* I was asking.

## Rule

Never busy-poll inside `page.evaluate` / `browser_evaluate`. Use the framework's own
waits — `expect(locator).to_have_count(n)`, `locator.wait_for()`, `browser_wait_for` —
which release the thread. Reserve `evaluate` for a **single-shot** read.

Cost when I got this wrong: ~65 s of wall time and a near-miss false product-bug report.

Related: [[artifacts_bucket_list_slow_render]]

---
name: A fast, clean DEV gate is a normal outcome — the goto hazard is bursty, not a baseline
description: The same spec on the same machine spanned 3-of-3 and 0-of-3 goto flakes in one day; don't quote one session's rate as a trend, and don't distrust a 24s green
type: reference
aliases: [DEV gate fast, goto flake rate, bursty not rising, reruns empty]
tags: [area/merge-gate, area/environment]
created: 2026-09-10
updated: 2026-09-10
---

`#2139`'s DEV gate of `TestDeletePipeline` hit the `#2124`/`#2156` `Page.goto` hazard in
**all three** invocations (94.91 / 155.90 / 67.99 s). Re-gating the same repaired spec
hours later (#2171, single node-id, `-p devenv` harness) was **3/3 passed, `reruns.json == {}`
every run, 24.27 / 24.07 / 23.31 s, 5 allure steps each** — zero occurrences.

Two calibrations:

- **Budget by attempts, not wall clock.** The 4x wall-clock difference is almost entirely
  attempts the hazard ate, not work the spec does.
- **Green AND clean is achievable and unremarkable.** Verify it properly — `reruns.json == {}`,
  allure step count non-zero, and the INFO log's `Authenticating via API against
  https://dev.elitea.ai` line — then trust it. Re-running "because it seemed too fast" buys
  nothing.

Procedure lives in [[dev_gate_discipline_for_fix_cards]]; recorded in `.agents/testing.md`
under the #2124 entries.

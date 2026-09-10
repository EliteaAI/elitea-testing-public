---
name: A green DEV invocation is not a clean invocation — classify attempts, not exit codes
description: pytest prints "1 passed" while --reruns=2 silently absorbed two broken attempts; the evidence exists only in allure results, and skipping the check throws away the only free hazard datapoint you get
type: feedback
aliases: [reruns hide broken attempts, green but not clean, classify gate attempts, 1 passed 2 rerun]
tags: [area/gate, area/triage, type/process]
created: 2026-09-10
---

## What it looks like

Gate run 1 of my 3× DEV gate on #2193 (ELITEA-1901):

```
==================== 1 passed, 2 rerun in 74.08s (0:01:14) =====================
--- run 1 exit=0 ---
```

Exit 0. Junit records PASS. A gate table with three PASSED rows is *true*. And two attempts died.

## Why it matters even when the gate is legitimately green

`--reruns=2` absorbing a **precondition** failure is correct — a raw uncaught error upstream of
every assertion can never be a member of a sanctioned-RED closed set, so re-running is the
prescribed response, not a workaround. The gate stands.

But the absorbed attempts are the *only* evidence of a live infrastructure hazard, and they cost
nothing to read. On #2193 they were:

```
18:58:06 | broken | 0.0 s | TimeoutError: Page.goto: Timeout 15000ms exceeded.
                            navigating to "https://dev.elitea.ai/", waiting until "domcontentloaded"
```

`0.0 s` + **zero steps recorded** = death in session setup (`_browser_cookies`), before the test
body starts — which is what distinguishes it from a page object's `navigate()` and makes the
exposure session-wide rather than per-surface. None of that is derivable from `1 passed, 2 rerun`.

## The check, in full

```bash
cat reports/reruns.json          # cheapest tell that an invocation was impure — non-empty = look closer
```
then classify each attempt by cause, grepping by `fullName`:
```python
d['status'], (d['stop']-d['start'])/1000, d['statusDetails']['message']   # allure-results/*-result.json
```
Read `statusDetails.message`, **not** `status` alone — several specs now raise `AssertionError … from err`
so the old "grep for `broken`" habit misses them.

## The discipline in one line

**Count attempts by cause, never invocations by exit code.** Counting invocations reads a
7-of-9-hazard session as a clean pass and a 0-assertion-failure session as a red — both wrong, in
opposite directions.

Related: [[a_null_delta_card_still_owes_a_full_gate]] · [[dev_goto_lifecycle_waiter_never_resolves]]

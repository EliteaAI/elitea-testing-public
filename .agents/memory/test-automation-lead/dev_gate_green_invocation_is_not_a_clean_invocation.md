---
name: On DEV, "1 passed" is not a clean gate run — read reruns.json every time
description: The #2124 Page.goto hazard hides inside a green invocation; pytest's tail and junit both say PASS while 2 of 3 attempts died in session setup
type: insight
aliases: [dev gate reruns, page.goto timeout dev, broken vs failed, reruns.json, dev gate clean]
tags: [area/gate, area/dev-env, type/discipline]
created: 2026-09-10
updated: 2026-09-10
---

## The trap

A DEV gate on ELITEA-1866 (#2149) was **3/3 passed** — and the raw attempt tally was
**3 passed / 4 broken**. Runs 2 and 3 each burned both `--reruns=2` attempts before
passing. The pytest tail said `1 passed, 2 rerun`; junit recorded PASS.

All 4 lost attempts were byte-identical:

```
playwright._impl._errors.TimeoutError: Page.goto: Timeout 15000ms exceeded.
  - navigating to "https://dev.elitea.ai/", waiting until "domcontentloaded"
```

allure status **`broken`** (not `failed`), duration **0.0 s**, **zero steps** — session
setup, before the test body. That is the known #2124/#2156 DEV hazard: a **precondition**,
upstream of every assertion, so it can never be a member of a sanctioned-RED closed set.

## The discipline

- **`cat reports/reruns.json` after EVERY DEV invocation.** Non-empty means the invocation
  was not clean, however cheerful the tail. It is one command and it is the only cheap tell.
- **Classify by `statusDetails.message` in `reports/allure-results/*-result.json`**, grep by
  `fullName`. `broken` + 0 steps + 0.0 s ⇒ precondition hazard, re-run. `failed` with steps
  ⇒ the case's own signature, which is a real result.
- **Report the attempt tally, not just the invocation tally.** "3/3 green, 4 attempts lost to
  #2124, the case's own signature 0 times in 7 attempts" is the honest sentence.
- Never raise the timeout — `ERR_ABORTED`/hang means cancelled or wedged, not slow.

Rate datapoint: 4 of 7 attempts, on a **single-node-id** gate of a `tests/ui/toolkits/` spec.
Bursts are not a function of suite size. Ledger entry in `.agents/testing.md` (`d7e8710`).

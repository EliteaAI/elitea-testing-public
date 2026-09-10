---
name: DEV Page.goto flake is a precondition, never a signature
description: On dev.elitea.ai a goto timeout/ERR_ABORTED fires before any assertion — re-run, and read allure not junit
type: reference
aliases: [Page.goto timeout DEV, 2124, 2156, ERR_ABORTED, broken not failed, reruns.json]
tags: [area/automation, type/flake]
created: 2026-09-10
updated: 2026-09-10
---

## What it looks like

`playwright._impl._errors.TimeoutError: Page.goto: Timeout 15000ms exceeded`
(or `net::ERR_ABORTED`), allure status **`broken`**, duration often **0.0 s**
because it dies in session setup (`_browser_cookies`) rather than in a step.
Tracked as #2124 / #2137 / #2156.

## Why it matters to a verdict

It is a raw uncaught error at a **precondition**, upstream of every assertion the
spec makes — so it can never be a member of a sanctioned-RED closed set, and
`2-of-3` is never acceptable. **Re-run.** Raising the timeout is not a fix
(`ERR_ABORTED` means *cancelled*, not *slow*).

## The part that costs you if you forget it

`pytest.ini`'s `--reruns=2` absorbs it, so **junit records PASS and the pytest
tail shows a bare `1 passed`**. The occurrence exists only in
`reports/reruns.json` and `reports/allure-results/*-result.json` — grep by
`fullName`, read `statusDetails.message`. Always print `reruns.json` after a DEV
invocation; a green with a non-empty `reruns.json` is not the same evidence as a
green with `{}`.

## Rate

Bursty and high: measured 2 of 3 invocations on 2026-09-10 (ELITEA-1869), and the
ledger records 4-of-9 and 7-of-9 bursts the same week. **Budget 2-4x the nominal
wall clock for any DEV verification.**

Related: [[env_test_is_a_symlink_dev_swap_recipe]]

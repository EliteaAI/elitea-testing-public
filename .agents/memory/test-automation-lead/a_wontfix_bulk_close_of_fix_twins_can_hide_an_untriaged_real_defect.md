---
name: A wontfix bulk-close of [FIX] twins can hide an untriaged REAL defect — check the prior cards for a triage comment, not just their label
description: #2237/#2256 (ELITEA-1902) were closed wontfix with zero comments; the 3rd filing #2261 was real test-side work (one-shot input_value() hydration race), not a promotion-gap twin
type: feedback
aliases: [wontfix twins, bulk-closed fix cards, third filing real, one-shot input_value, hydration race, agents create non-render]
tags: [area/triage, type/lesson]
created: 2026-09-11
updated: 2026-09-11
---

## What happened
The human bulk-closed the previous two `[FIX][ELITEA-1902]` cards as `wontfix` (no comments,
no triage). My prior reads that "the human closed the twins ⇒ promotion-gap re-detection"
would have been wrong here: the spec was byte-identical on `main` and `automation/base`, no
repair existed anywhere, and the message-string grep was **absent on both refs** (the string
is split across two source lines — grep a distinctive fragment, not the whole sentence).

## The disposition that worked (~1 h session, PR #2268)
1. Board scan → #143 Ready, twins `wontfix` with **empty threads** ⇒ untriaged, not settled.
2. Message grep (fragment) → absent on BOTH refs ⇒ not a promotion gap.
3. Allure artifact for the shard (`allure-results-dev-stable-user5-127`; user number found by
   grepping each `test-results-*` junit for the node id) → failing step 1.4 s, screenshot
   shows the value the assertion wanted **present on screen** ⇒ test read too early.
4. Root cause: `confirm_import_complete()` = URL + `networkidle`; `verify_on_detail_page()` =
   URL only; `get_name()` = one-shot `input_value()`. Repair = additive
   `AgentFormPage.expect_name()` (`expect().to_have_value`), no weakening. Canon card #2275.

## New DEV precondition hazard flavour
First lead-gate attempt lost 3/3 attempts at Step 1 — `/app/agents/create` never rendered
`agent-name-input` within 15 s (allure `broken`, 18 s each), NOT a `Page.goto` timeout. Runs
2–3 clean; re-gate 3/3 clean. Same response: re-gate from scratch, never 2-of-3.

Related: [[fix_card_is_generated_from_ONE_attempt_diff_the_attempts_first]] ·
[[message_string_grep_is_the_cheapest_promotion_gap_proof]] ·
[[the_devenv_plugin_is_the_factory_safe_dev_gate]]

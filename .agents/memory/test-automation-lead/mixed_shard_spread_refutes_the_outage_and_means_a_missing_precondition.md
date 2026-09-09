---
name: A mixed shard spread REFUTES the sibling outage — and the usual per-test cause is an ambient-data precondition
description: 46-pass/6-fail is not an outage; check the job's own spread before inheriting a sibling's root cause, then suspect "nothing to render" over "not rendering"
type: feedback
aliases: [mixed spread, sibling fix card, no pipelines yet, empty project, ambient data, missing precondition, vacuous assertion, class D, outage refuted]
tags: [area/triage, type/lesson]
created: 2026-09-10
updated: 2026-09-10
---

## The finding

When one CI run files a batch of `[FIX]` cards at once, the outage explanation
is contagious — and it is right often enough to be dangerous. The cheap
discriminator is the **failing job's own pass/fail spread**, before any dispatch:

- **Contiguous failure block bounded by passes** → the outage story
  ([[env_outage_page_is_a_fix_card_root_cause]] has the shard-timeline proof).
- **Mixed spread** (e.g. `46 passed, 6 failed`) → **refuted.** The app was
  serving fine for 46 tests; this red is per-test and needs its own cause.

Worked case #2118 / ELITEA-2024: run 34331579791 produced siblings #2076–#2084
and a genuine gateway-500 signature elsewhere, but `pipelines_2` was 46/6. Its
allure screenshot showed **"No pipelines yet"** — the project held zero
pipelines. The card's headline ("card elements not rendering") named the wrong
subsystem; the view toggle worked perfectly.

## The per-test cause to suspect first: ambient data

A test that reads shared state it never established passes only where that
state happens to exist. It goes red on a CI matrix user whose project is empty,
and the failure surfaces at whatever assertion touches the data — never at the
precondition, so it always names the wrong subsystem.

The tell: the case text *declares* a precondition ("the dashboard contains at
least one pipeline") that the automation inherited instead of establishing.

## The part worth the whole triage: look for the SILENT twin

An empty list usually breaks one assertion loudly and makes its sibling pass
**vacuously**. In #2118, `CardList.jsx`'s `showEmptyOrError` short-circuits
*both* `showTable` and `showCards`, so "no cards render while in table view"
was satisfied by nothing having mounted at all — it passed in **0.00 s** having
proven nothing, and would have kept doing so forever.

So the repair is never just "make the red green":

1. **Establish** the precondition (an API-created fixture object is transit, not
   substitution — declare it).
2. Assert the fixture's **own** object, not "any object" — truthiness is the
   weakest possible check.
3. Put a **positive** assertion at the precondition step, so the next occurrence
   reports itself there with the right subsystem named.
4. Hunt the vacuous sibling and give it a discriminating handle (here
   `empty-state-title`, which separates "a table mounted" from "nothing mounted").

Ask of every absence assertion: **could this pass because the thing that should
contain the absent item never rendered either?**

## Cost

~10 minutes of orchestrator triage (job spread + one allure screenshot) replaced
a speculative product-bug hunt, and turned a one-line "make it green" into a
repair that closed a defect nobody had noticed.

Related: [[env_outage_page_is_a_fix_card_root_cause]] · [[gate_on_the_environment_the_repair_is_FOR]] · [[dev_only_red_check_the_screenshot_first]]

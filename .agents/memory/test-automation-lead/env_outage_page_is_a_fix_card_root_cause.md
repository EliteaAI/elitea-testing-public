---
name: A [FIX] card's real cause can be an ENVIRONMENT OUTAGE PAGE — bound the window on the shard timeline
description: Sort the whole shard's allure results by start time; a contiguous failure block bounded by passes plus a maintenance/5xx screenshot is a complete class-D proof in ~10 minutes, no dispatch
type: feedback
aliases: [maintenance page, under maintenance, 500 error page, environment outage, class D, shard timeline, dev outage, fix card triage]
tags: [area/triage, type/lesson]
created: 2026-09-09
updated: 2026-09-09
---

## The finding

A `Locator.wait_for` timeout on a deployed env is not necessarily a slow app.
The app may not have been served **at all**. Elitea renders two full-page
states that look like nothing to a locator: *"Elitea is under maintenance!"*
and a `500 Internal Server Error` page. Every spec that starts inside such a
window dies as an ordinary locator timeout, and the intake pipeline files a
`[FIX]` card per test.

Worked case, #2050 / ELITEA-1870 (GHA run 34244735426, shard `dev-stable-user3-110`):
all 3 attempts sat on the maintenance page. Sibling #2049 sat on the 500 page
70 seconds earlier. Neither test nor product was at fault.

## The decisive move — the shard timeline, not just the screenshot

The screenshot names the symptom. **Ordering the entire shard's results by
start time proves the cause**, and it is one script over the allure dir:

```python
rows = [(d['start'], d['stop'], d['status'], d['fullName']) for d in results]
rows.sort()   # then print, and look for a CONTIGUOUS failure block
```

What convicts an outage is the *shape*: passes right up to the block, a solid
run of failures across **different specs and different page objects**, then
passes resuming immediately. #2050's block was 15:31:02 → 15:33:21 — 2m19s,
two specs, six attempts — with five passing specs before and five after.

Read a screenshot from *before* and *after* the block too. #2042 failed at
15:27:19 in the same shard with a **fully rendered** app: same run, same
surface, genuinely different cause. That is the `sibling_fix_cards_can_have_
different_root_causes` rule getting a positive confirmation, cheaply.

## The one-command history check

`test-results-*` artifacts of the PREVIOUS nightly carry `junit.xml`. A
`<testcase>` with no `failure`/`error` child means the same test passed on the
same env a day earlier — that converts "chronically red" into "one-off" before
any dispatch. ELITEA-1870: `time=7.123`, clean, run #105.

## Then verify, don't just infer

Three separate `--reruns=0` invocations against DEV via the out-of-repo
`-p devenv` harness, with the target proven from the INFO log each run. 3/3
clean closes it. No PR, no code change — that is a legitimate terminal state.

## The systemic gap this exposes

The suite cannot distinguish "environment unavailable" from "locator drift",
so a 2-minute outage costs two triage sessions and files two bogus cards.
Filed as #2054. Blocked on the maintenance/5xx pages having no testid.

Related: [[dev_only_red_check_the_screenshot_first]] · [[sibling_fix_cards_can_have_different_root_causes]] · [[harvest_gha_allure_artifacts_before_dispatching]] · [[fix_card_body_can_carry_a_policy_violating_instruction]]

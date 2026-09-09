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

## Cross-shard confirmation — the strongest form of this proof (added 2026-09-09, #2053)

One shard's contiguous block is good. **Two shards agreeing on the same window is
decisive**, and it costs one extra run of the same timeline script. Run 34244735426
produced three `[FIX]` cards from one outage:

| Shard | Block | Specs x attempts | Card |
|---|---|---|---|
| `user3` | 15:31:02 -> 15:33:21 | 2 x 3 | #2050 (ELITEA-1870) |
| `user1` | 15:30:46 -> 15:33:18 | 2 x 3 | #2044 (ELITEA-1793) + #2053 (ELITEA-1795) |

Same window, different shards, different surfaces, same maintenance/5xx render.
A per-shard cause (a wedged browser, a polluted shard user, a slow runner) cannot
produce that; only the environment can.

**Check for a sibling's already-downloaded artifacts before re-harvesting** — #2053
needed zero downloads and zero dispatches because the #2050 session had pulled all
three shards to `/tmp/ar2050`.

## The card's prose is a paraphrase, not the signature

#2053's body: *"Timeout waiting for navigation after saving skill."* The actual
allure `statusDetails.message`: `waiting for get_by_test_id("skill-name-input")`,
in **Step 1 precondition setup** — a different step. The intake generator writes
plausible prose from a log tail. Read `statusDetails.message` and the per-step
statuses before forming any hypothesis from the card's own description; a wrong
step name sends triage at the wrong page object.

## Proving the 500 page is INFRA, not our ErrorBoundary — one grep (added 2026-09-09, #2074 / ELITEA-1740)

The screenshot shows a branded Elitea *"500 Internal Server Error / Something went wrong
on our end"* page with **"Go to Elitea" / "Go Back"** buttons. It looks like our app, so the
natural next thought is "an app error boundary caught a failed XHR" -- which would point
triage at a feature. It does not. One command settles it:

```bash
cd ../EliteaUI && git grep -n "Something went wrong on our end" origin/main -- src/   # 0 hits
```

No hit anywhere in `src/`, no `public/500.html` -> that markup is served by a layer **in front
of** the app (gateway/proxy/CDN) when the origin errors. So the whole platform was unreachable
for that request, not one endpoint. Positive proof in seconds, and it upgrades "probably an
outage" to a fact you can put in a closure record.

Two supporting reads on the same card, both cheap:
- **The 3 skills had been created successfully seconds earlier** -- the backend was provably
  healthy right up to the navigation, which kills every "the feature is broken" hypothesis.
- **8 of 10 suite jobs failed in that run** (sibling cards #2076-#2084, unrelated features).
  One card in isolation reads as a feature bug; the run-level view reads as an outage.

## An assertion-shaped CI red carries NO determinism signal

`automation/pytest.ini`'s `--only-rerun` list covers 5xx / connection / `TimeoutError` /
`WebSocket` / `Failed to load resource` -- **not `AssertionError`**. So an assertion failure
gets **zero** automatic reruns, and "it only failed once" says nothing at all about whether it
is deterministic. Check that list before reasoning about flakiness from a CI red's rerun count.

## When the outage is real but the message lied, the repair is DIAGNOSTICS

#2074's red said *"skill-a-... should be visible in the grid after creation"* -- the wrong
subsystem entirely -- because `BasePage.navigate()` discarded `page.goto()`'s `Response` and
`wait_for_page_load()` waited only on a URL regex + networkidle, so a top-level 500 sailed
through and surfaced ~64s later at an unrelated assertion. A transient-infra classification is
**not** automatically "no work": returning that `Response` and failing fast on a non-`None`,
non-OK status makes the same failure red *sooner and truthfully*. That passes the masking test
precisely because the 500 still turns the run red. Use a `Response.status` integer check, never
a text match on the error page -- that page is not our DOM, carries no testids, and matching its
text would be a locator-policy violation. Suite-wide rollout tracked as #2089.

Related: [[dev_only_red_check_the_screenshot_first]] · [[sibling_fix_cards_can_have_different_root_causes]] · [[harvest_gha_allure_artifacts_before_dispatching]] · [[fix_card_body_can_carry_a_policy_violating_instruction]]

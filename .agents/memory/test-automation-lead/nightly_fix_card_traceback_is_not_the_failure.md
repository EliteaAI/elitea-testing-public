---
name: A nightly FIX card's reported traceback is often NOT the failure you must fix
description: pytest reruns + accumulating caplog fuse three different attempts into one report — read the per-attempt allure results, not the FAILURES block
type: feedback
aliases: [caplog accumulation, rerun traceback misleading, FIX card triage, which attempt failed how, allure per-attempt]
tags: [area/triage, type/gotcha]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

`pytest.ini` runs `--reruns=2`, so a nightly failure is three attempts. The FAILURES
block shows only the **last** attempt's traceback — but `caplog` **accumulates across
reruns**, so the "Captured log call" section under it carries ERROR lines from *all
three*. The result reads like one coherent failure and is not one.

Worked case (#2077 / ELITEA-2063, run 34331579791):

| # | Failed at | Cause |
|---|---|---|
| 1 | Step 5 | the real defect — VERSION dropdown left open, backdrop intercepts the click |
| 2 | Step 1 | full-page gateway 500 |
| 3 | Step 1 | same (screenshots 2 and 3 byte-identical by md5) |

The report's traceback pointed at **Step 1** — a navigation timeout — while the single
backdrop ERROR line beneath it came from attempt 1. Triaging from the traceback sends you
after `wait_for_detail_page_load` and the wrong subsystem entirely.

## The tell, and the fix

**Tell that caplog is accumulating:** the same `Step failed: …` ERROR line repeated N times
in one report (the sibling `test_pipeline_delete_version` block in that same run carried
three identical lines for its three attempts). Once you see that anywhere in the report,
trust nothing about which error belongs to which attempt.

**Do this instead, in this order — it is cheap and it is decisive:**

1. `gh run download <run-id> --repo <repo> -D <dir>`, take the shard's `allure-results-*`
   artifact. Each attempt is its own `*-result.json` with its own `start`/`stop`, failing
   step and attachments.
2. **Open every attempt's screenshot.** `md5` them — identical screenshots across attempts
   means one environmental cause, not a per-attempt race. A branded full-page 500 or a
   maintenance page ends the analysis (see [[env_outage_page_is_a_fix_card_root_cause]]).
3. Only then read the traceback, knowing which attempt it belongs to.

A pytest **rerun that passes makes junit record PASS**, so this whole class is invisible in
the junit trail — the allure result JSON is the only place it exists.

Related: [[env_outage_page_is_a_fix_card_root_cause]]

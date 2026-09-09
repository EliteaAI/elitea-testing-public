---
name: caplog/allure log attachments accumulate across pytest reruns
description: The reported traceback and the reported error text can come from DIFFERENT rerun attempts — read per-attempt allure results, never the aggregated log
type: feedback
aliases: [rerun triage, caplog accumulation, which attempt failed, allure per-attempt]
tags: [area/triage, type/gotcha]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

With `pytest-rerunfailures`, the captured-log attachment carries the *previous* attempts' ERROR
lines too. So a CI report can show a traceback from attempt N and an error message from attempt 1
side by side, and reasoning from that pair produces a fiction.

Worked case: ELITEA-2002 / `#2077`, nightly run 34331579791. The reported traceback was a Step-1
navigation timeout; the reported error text was a Step-5 MUI-backdrop click interception. Neither
described "the" failure — attempt 1 failed at Step 5 (the real defect), attempts 2-3 failed at
Step 1 on an unrelated platform outage.

## What to do instead

Download the shard's `allure-results-*` artifact and read one `*-result.json` **per attempt**
(`grep -l "<test name>" au*/**-result.json` gives one file per attempt). Each carries its own
`steps[]` with per-step `status`, duration, `statusDetails.message` and its own screenshot
attachment. That is the only per-attempt ground truth.

- `test-results-*` artifacts hold only `report.html` / `junit.xml` / `reruns.json` — **no
  screenshots**. `reruns.json` gives the rerun COUNT but may list fewer messages than attempts.
- Screenshots live in `allure-results-*` under uuid names; find them via each result JSON's
  nested step `attachments[].source`, not by filename.
- `md5` the per-attempt screenshots: identical hashes across attempts is itself a finding.

Related: [[gateway_500_full_page_is_not_the_feature_failing]]

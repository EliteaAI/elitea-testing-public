---
name: A [FIX] card is generated from ONE attempt of a multi-attempt run — diff the attempts BEFORE triaging
description: Two API calls separate "the whole suite is broken" from "one attempt hit an outage"; on run #116 this cut an 11-case card to 1 real case, and named which failures were real
type: feedback
aliases: [run_attempt, re-run attempt, attempt 2, all tests failed, whole suite red, intake card wrong signature, fix card triage, agent_hub catalog timeout]
tags: [area/triage, type/lesson]
created: 2026-09-10
updated: 2026-09-10
---

## The finding

The test-failure intake pipeline generates a `[FIX]` card from **one attempt** of a
GHA run. A run that was re-run twice has three attempts, and the card may quote the
signature of the *worst* one. If that attempt caught an environment outage, the card
describes a failure that **does not exist in the other attempts** — and lists every
test in the shard as needing work.

Worked case: **#2179**, run `34436416962` (DEV Stable #116), `run_attempt: 3`.

| Attempt | agent_hub result |
|---|---|
| 1 (04:16Z) | 10 passed, **2 failed** |
| 2 (08:34Z) | **all 12 failed** — `catalog-page-heading` never visible ← **the card was generated from this one** |
| 3 (09:19Z) | 10 passed, **2 failed** — the same 2 as attempt 1 |

The card listed **11 cases**. Nine of them had nothing wrong. Of the two real
failures, one was a promotion gap already repaired on `automation/base`. **One case
of eleven was real work.**

## The move — two calls, before anything else

```bash
env -u GITHUB_TOKEN gh api repos/<owner>/<repo>/actions/runs/<id> --jq '.run_attempt'
# if > 1, list each attempt's jobs and compare the same job across them:
env -u GITHUB_TOKEN gh api "repos/<owner>/<repo>/actions/runs/<id>/attempts/<n>/jobs?per_page=100" \
  --jq '.jobs[] | "\(.id)\t\(.conclusion)\t\(.name)"'
env -u GITHUB_TOKEN gh run view <id> --repo <owner>/<repo> --log --job <job-id> \
  | sed -e 's/\x1b\[[0-9;]*m//g' | grep -E "PASSED|FAILED|RERUN|AssertionError"
```

Note the job ids in the card's body belong to whichever attempt generated it —
they will not match `runs/<id>/jobs`, which returns the **latest** attempt only.
That mismatch is itself the tell that more than one attempt exists.

## Why it beats the shard-timeline method

[[env_outage_page_is_a_fix_card_root_cause]] proves an outage from one shard's
allure timeline. Diffing attempts is **cheaper and strictly more informative**:
a whole suite passing in a different attempt of the *same run, same commit, same
environment* is proof no code is at fault, and — the part the timeline cannot give
you — the passing attempts **name exactly which failures are real**. Use the
timeline when there is only one attempt.

## The rule

**An entire suite failing on a page-level handle in one attempt, while another
attempt of the same run passes, is environment unavailability.** Do not
dispatch an analyst against it, and do not report those cases as needing work.
Triage the residual failures that survive across attempts — those are the card.

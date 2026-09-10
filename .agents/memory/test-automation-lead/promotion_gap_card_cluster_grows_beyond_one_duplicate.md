---
name: A promotion-gap [FIX] card is rarely alone — check the whole ELITEA-id cluster before delivering
description: One unpromoted repair regenerates a card on EVERY nightly; find the siblings and recommend bundling, instead of delivering each in isolation
type: feedback
aliases: [duplicate fix cards, promotion gap cluster, same ELITEA id multiple cards, bundle duplicates]
tags: [area/orchestration, type/triage]
created: 2026-09-10
updated: 2026-09-10
---

## What happened

#2171 (`[FIX][ELITEA-2022]`) was a textbook promotion gap: repair `09219bb8f` / PR #2161
merged to `automation/base` **35 min before the CI run that filed the card started**, and
`origin/main...origin/automation/base` read `0  450`. Delivery = verify + closure record, no code.

The part worth remembering is what the tracker search turned up: **the same spec and signature
had FOUR cards** — #2139 (the original, delivered), #2171 (mine), #2181, #2198 — all OPEN.
The nightly re-files on *every* run until a human promotes, so the cluster keeps growing while
the card sits in `Todo`.

## The move

One search, before writing the closure record:

```bash
env -u GITHUB_TOKEN gh issue list --repo <repo> --state all --limit 60 \
  --search "<CI-RUN-ID>" --json number,title,state
```

Group by `[ELITEA-<id>]`. Then **name the siblings explicitly in the closure record and
recommend bundling them at acceptance** — a human closing four cards in one sweep is seconds;
four separate agent sessions each re-deriving the same promotion gap is hours. Do **not** start
them (dispatch rule 7 — they are their own cards), and do **not** file a new "these are dupes"
card; log the occurrence on the standing intake question card (#2157) instead.

## Also worth pasting into the record

The gap is **not clearable by anything in this repo's automation pipeline**. Say that in those
words, name the human as owner, and name the mechanism (`batch-promote`, base N ahead / 0 behind).
Otherwise the record reads as "delivered" and the next nightly makes a liar of it.

Related: [[a_promotion_gap_fix_card_can_still_hide_real_work]] · [[fix_card_may_already_be_fixed_by_a_sibling_pr]] · [[ci_red_check_base_for_an_existing_fix_first]]

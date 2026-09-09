---
name: A timeout raise on a leak-fed list is headroom with a DECAYING balance — name the leak in the closure record
description: Sizing a wait against a measured band is right, but if a harness leak feeds the collection being waited on, the same red returns later and slower — the leak is the rate-limiter, not the budget
type: feedback
aliases: [timeout budget, decaying headroom, leaked buckets, unpaginated list, bucket leak, raise the timeout, budget defect]
tags: [area/triage, type/lesson]
created: 2026-09-09
updated: 2026-09-09
---

## The finding

`[FIX]` #2084 / ELITEA-1808: Step 7 waited 15 s for a newly created bucket's row
after a Save. The creation POST returned **200** and the bucket existed — the row
had not *rendered*. Cause: `invalidatesTags: [TAG_BUCKETS]` triggers a refetch of a
**single unpaginated** `GET /artifacts/s3/` returning **all 1221 buckets** (238 KB,
~10 s), then every row mounts (no windowing), ~1.2 s more. Measured on DEV:
POST-200 → row-visible = **10.75 / 11.29 / 10.83 s idle**, vs the same request at
**12.4–43.8 s under load**. A budget defect, not a signal defect — so the fix is the
number, and the signal (the rendered row testid) correctly stays put.

## The part that is easy to miss

**1176 of those 1221 buckets (96%) are our own leak.** `ArtifactAPI.delete_bucket()`
targets a route that does not exist (path-segment form → 404; the working form is
`{api_base}/artifacts/buckets/default/{pid}?name=<bucket>` → 200). So every artifacts
spec that creates a bucket adds one, permanently, to the very collection the new
timeout is sized against.

⇒ **The 60 s budget is headroom with a decaying balance.** It buys time, it does not
stop the clock. When the loaded request crosses ~58.8 s the identical red returns —
at 60 s instead of 15 s, burning 3× the CI time per occurrence, with the same
misleading message.

## What to do about it

- Ship the budget fix anyway — it is correct and it is sized against a measurement.
- **Name the leak, and the fact that it is the rate-limiter, in the closure record**,
  so nobody later reads a green as "solved". Ordering matters: fix the leak first,
  then the sibling budgets (#2127), because a purge removes the pressure entirely.
- Generalise the smell: *whenever a wait is on a collection that something appends to
  and nothing prunes, ask what feeds it before agreeing the budget is the fix.*

Related: [[hardcoded_count_drift_is_rarely_fixed_by_bumping_the_number]] · [[env_outage_page_is_a_fix_card_root_cause]] · [[identify_your_own_test_residue_by_set_difference_not_prefix]]

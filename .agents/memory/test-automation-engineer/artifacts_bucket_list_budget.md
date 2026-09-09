---
name: Artifacts bucket-list waits need a 60 s budget, not NAVIGATION_TIMEOUT
description: Any wait gated on the unpaginated GET /artifacts/s3/ refetch needs ~60 s, not 15 s
type: project
aliases: [bucket list timeout, wait_for_bucket_in_list, artifacts refetch budget, BUCKET_ROW_AFTER_REFETCH_TIMEOUT]
tags: [area/artifacts, type/timing]
created: 2026-09-09
updated: 2026-09-09
---

## The endpoint is unpaginated and the panel has no windowing

`GET /artifacts/s3/?project_id=399` returns **every** bucket in one 238 KB response
(1221 buckets in project 399 as of 2026-09-09, 96% of them leaked `autotest-*`),
and `SimpleBucketList.jsx` mounts a row for each one — no virtualisation.

Measured on DEV from an idle machine: request **9.5-11.6 s**, render **~1.2 s**,
so creation-POST-200 -> new row visible is **10.7-11.4 s**. Under load the same
request has been measured at **12.4-43.8 s** (#2066).

## Consequence

**Any** wait that is gated on that refetch must own a ~60 s budget — a 15 s
`NAVIGATION_TIMEOUT` sits *just above* the idle floor and far below the loaded
worst case, so it fails **deterministically under CI load**, not flakily. That is
what killed ELITEA-1808 Step 7 in CI run 34331579791 (#2084).

The fix is the budget, **not** the signal: the bucket row is what the caller
needs (#1847), and it appears only ~1.2 s after the refetch response, so waiting
on the response instead saves nothing and moves the observable off rendered state.

`ArtifactsPage.BUCKET_ROW_AFTER_REFETCH_TIMEOUT = 60_000` is now the default of
`wait_for_bucket_in_list()`. **13 sibling call sites still pass 15 s / 10 s** to
the same class of wait (`wait_for_bucket_removed_from_list` included) — tracked
as **#2127**, same latent defect.

## Gotcha when verifying locally

A local green proves nothing here — the unmodified spec also passes on DEV from an
idle box (49 s). Only a loaded run reproduces it. Say so explicitly rather than
claiming the fix is verified.

Related: [[../../..]] · `.agents/testing.md` § Known issues

---
name: Artifacts bucket list — ordering, pinning and the 8-10s refresh lag
description: The bucket panel is alphanumeric (by accident), pinned buckets lead the list, and the DOM lags the pin PATCH by ~10s
type: project
aliases: [bucket pin, pin to top, artifacts bucket order, sortBucketsByRecent]
tags: [area/artifacts]
created: 2026-08-21
updated: 2026-08-21
---

## Ordering
`SimpleBucketList.jsx` calls `sortBucketsByRecent`, but the buckets listing
payload carries no usable `updated_at`/`created_at`, so every comparison is
`NaN` and the sort is a **no-op** — the backend's **alphanumeric** order
survives. Live-verified 2026-08-21: 766 rendered names were exactly
`== sorted(names)` with nothing pinned. Assert the observable (alphanumeric),
never the mechanism — a payload change could make the recency intent real.

`BucketsPanel.jsx` splits `pinnedBuckets` / `unpinnedBuckets`, and
`BucketsListContent.jsx` renders the pinned list **above** the unpinned one, so
a pinned bucket appears **once** (the old "rendered twice" claim in
`ArtifactsPage.get_rendered_bucket_names()` was wrong and is now corrected).

## The lag
`PATCH /artifacts/buckets/default/{pid}?name={bucket}` (body `{"is_pinned":…}`)
returns 200 immediately, but the list re-renders **~8-10 s later** (10 s pin,
8 s unpin, measured by 2 s polling; no intervening buckets `GET` seen on the
wire). Use auto-retrying `expect(...)` with a ~45 s timeout. While the list is
stale the **dot-menu is stale too**: it still reads "Pin to top" for an
already-pinned bucket and clicking it re-sends `is_pinned: true`.

## Leaked pins are project-wide damage
A leaked *pinned* bucket sits at the top of every project member's list forever,
breaking any "first item" assertion. Always `ArtifactAPI.set_bucket_pinned(name,
False)` in teardown **before** deleting (deletion itself is unreliable, `#636`).

Related: [[artifact_bucket_fixture_delete_silently_fails_404]]

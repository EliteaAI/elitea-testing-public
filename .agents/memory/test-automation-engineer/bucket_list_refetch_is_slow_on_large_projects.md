---
name: Artifacts bucket-list refetch exceeds 15s on a ~970-bucket project
description: The 15s NAVIGATION_TIMEOUT the artifacts specs share is no longer enough for the post-save bucket-list refetch
type: project
aliases: [wait_for_bucket_in_list timeout, bucket never appeared after save, artifacts-bucket-row not visible]
tags: [area/artifacts, type/flake-source]
created: 2026-08-23
updated: 2026-08-23
---

## Fact

Project 399 held ~970 buckets on 2026-08-23. After a bucket create/edit save, the left
panel refetches the WHOLE list, and `wait_for_bucket_in_list()` at the shared
`NAVIGATION_TIMEOUT = 15_000` timed out on a bucket that a fresh
`navigate_to_artifacts()` then showed instantly — i.e. a false "the bucket was never
created", not a product defect.

ELITEA-1810's spec introduced a dedicated `BUCKET_LIST_TIMEOUT = 45_000` for every
bucket-list condition wait (post-create, post-edit, post-cancel, and the teardown's
removal wait) and went clean. It is still a condition wait on the row's own testid —
not a sleep.

## Expect this to spread

The sibling artifacts specs (ELITEA-1808 / 1817 / 1809 …) all use the 15s value and
will start flaking the same way as the project's bucket count grows. ELITEA-1817's test
is ALREADY marked `@pytest.mark.blocked` with "times out during retry — hangs during
bucket creation", which is very likely this same effect.

Related: [[mui_select_backdrop_blocks_second_combobox_click]]

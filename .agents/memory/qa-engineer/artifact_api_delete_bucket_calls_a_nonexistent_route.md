---
name: ArtifactAPI.delete_bucket 404s because it uses a path segment, not ?name=
description: "#636 is a harness bug, not a product one — DELETE .../buckets/default/{pid}?name={bucket} returns 200 Deleted"
type: project
aliases: [636, bucket cleanup 404, delete_bucket, bucket leak]
tags: [area/artifacts, type/harness-defect]
created: 2026-09-09
updated: 2026-09-09
---

## The fact (verified live on DEV, 2026-09-09)

`automation/api/client.py:1514` `ArtifactAPI.delete_bucket()` sends the bucket as a **path
segment** — `DELETE /api/v2/artifacts/buckets/default/{pid}/{bucket}` — and falls back to
`.../{pid}/p--{pid}.{bucket}`. Both return Flask's *"The requested URL was not found on the
server"* 404: **no such route**, not "no such bucket".

The product's own form works:

```
DELETE /api/v2/artifacts/buckets/default/399?name={bucket}  ->  200 {"message": "Deleted"}
```

(`set_bucket_pinned()` in the same class already uses `?name=` and even documents that the
path-segment form is wrong.)

So **#636 is a test-harness defect mislabelled as a product bug** for months, and it is the
engine of the bucket leak (1176 leaked `autotest-*` buckets in project 399) that made the
list slow enough to red ELITEA-1808 — see [[artifacts_bucket_list_is_unpaginated_and_slow]].

Every artifacts spec's teardown carries a "known defect #636" caveat that should be removed
once the client is fixed.

Related: [[artifacts_bucket_list_is_unpaginated_and_slow]]

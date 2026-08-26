---
name: Artifacts REST calls carry project_id as a query param, not a path segment
description: The bucket page's live reads are /artifacts/s3/[bucket]?project_id=N — ArtifactAPI's /artifacts/buckets/default/{id} shape is NOT what the UI issues
type: reference
aliases: [artifacts s3 project_id, bucket page network scope, artifacts REST url shape]
tags: [area/artifacts, type/handle]
created: 2026-08-26
updated: 2026-08-26
---

## The fact

When the Artifacts bucket page renders, the UI issues (measured live 2026-08-26,
localhost:5173, ELITEA-2263 fix round 1):

```
GET http://localhost:5173/artifacts/s3/?project_id=399&format=json          # bucket list
GET http://localhost:5173/artifacts/s3/<bucket>?project_id=399&format=json  # bucket contents
```

The project is a **query param**. Do NOT derive it from a path segment: the test-side
`ArtifactAPI._buckets_url()` uses `/artifacts/buckets/default/{project_id}` — that is the
API client's own shape and the UI does not use it. A regex written against the client's
shape matches nothing and the assertion fails with an empty set.

## The other trap in the same listener

A `"/artifacts/" in resp.url` response listener also catches **Vite dev-server module
fetches** (`/src/[fsd]/features/artifacts/...`) — ~35 of them per bucket-page load on
localhost. Filter with `"/src/" not in url` before reporting URLs in an assertion message,
or the failure text is unreadable.

## Why it matters

Proving "the new tab opened the notification's OWN project's bucket" cannot be done from the
landing URL: the `/{project_id}` prefix survives only when a project switch is required, so
the bare `/artifacts` form names no project at all. The network reads are the only
non-hardcoded proof — there is no project-name API client in `automation/api/`, and the
sidebar project selector renders a label, not an id.

Related: [[console_noise_filters_must_pair_status_with_url]]

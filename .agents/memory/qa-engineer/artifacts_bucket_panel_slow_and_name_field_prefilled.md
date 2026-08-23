---
name: Artifacts bucket panel is slow and its name field is prefilled
description: 976-bucket project renders the panel in >13s; the New Bucket name input is prefilled 'new-bucket' so press_sequentially prepends
type: project
aliases: [bucket list slow, new-bucket prefill, mangled bucket name, artifacts panel timeout]
tags: [area/artifacts, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## Panel render latency

Project `Private` (399) held **976 buckets** on 2026-08-23. After navigating to `/artifacts`,
polling `[data-testid^="artifacts-bucket-row-"]` returned **0 for over 13 seconds**, with
`artifacts-buckets-footer-count` still reading `Buckets: 0`, before the list rendered. A short wait
plus an empty-list read is a **false negative**, not evidence. Budget >=20s for first render, and
always search rather than scan.

Stronger oracle: `GET /artifacts/s3/?project_id=399&format=json` (cookie auth, callable from page
context). `/api/v2/...` endpoints are NOT callable from page-context `fetch` — they need Bearer and
fail with "Failed to fetch".

## Name-field prefill

`EliteaUI/src/pages/Artifacts/CreateBucket.jsx:91` prefills the bucket-name input with the literal
`'new-bucket'`. A bare `click()` + `press_sequentially()` places the caret at position 0 and
**prepends**, silently creating a mangled bucket. Live proof in project 399:
`dup-bucket-1867new-bucket` (mine) and `new-bucketautotest-buck1-800755` (an earlier session's).
**Clear the field first**, or use `ArtifactsPage`'s own bucket-creation helper.

Related: [[artifact_toolkit_existing_bucket_succeeds]]

---
name: Artifact toolkit creation with an existing bucket succeeds (no error)
description: Toolkit-save path never calls the bucket-create API, so "bucket already exists" errors cannot occur there
type: project
aliases: [artifact toolkit duplicate bucket, bucket already exists toolkit, ELITEA-1867]
tags: [area/artifacts, area/toolkits, type/product-behaviour]
created: 2026-08-23
updated: 2026-08-23
---

## The fact

Creating an **Artifact toolkit** whose `Bucket` field names an **already-existing** bucket
**succeeds**: `POST /api/v2/elitea_core/toolkits/prompt_lib/{project}` → 200, wizard navigates to
`/toolkits/all/{id}`, no error notification, no duplicate bucket. Verified live twice, 2026-08-23,
localhost:5173 → DEV backend.

## Why (source-level, decisive)

`createBucket` (`EliteaUI/src/api/artifacts.js:46`, `POST /artifacts/buckets/default/{projectId}`)
has **exactly one caller in the whole UI**: `src/pages/Artifacts/CreateBucket.jsx:119` — the
Artifacts "New Bucket" form. The toolkit wizard never calls it, and no `/artifacts/buckets/…`
request fires during toolkit Save. So the error string `Bucket with name X already exists` is
**architecturally impossible** on the toolkit path; it belongs to ELITEA-1809's surface only.

Consequence: TMS case **ELITEA-1867** is case-text drift (a mis-transposition of ELITEA-1809's
expectation onto Toolkits), not a product defect. Filed as
[#1685](https://github.com/EliteaAI/elitea-testing-public/issues/1685); AFS `blocked`.

## Bonus

`CreateBucket.jsx:91` — the New Bucket form's name field **defaults to the literal `new-bucket`**.
That is where ELITEA-1867's test-data value came from.

Related: [[artifacts_bucket_panel_slow_and_name_field_prefilled]]

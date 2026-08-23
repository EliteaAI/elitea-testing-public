---
name: "'new-bucket' is shared test data, not a safe absence oracle"
description: The New Bucket form's default name is also CREATED by a merged toolkit spec, so absolute count(0) assertions on it are environment-coupled
type: reference
aliases: [new-bucket, artifacts-bucket-row-new-bucket, bucket default name, absence assertion]
tags: [area/artifacts, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## The trap

`new-bucket` is the Artifacts New-Bucket form's pre-filled default
(`CreateBucket.jsx` `initialValues.name`), so it reads like a name nobody would
ever really own — and specs reach for
`expect(bucket_row("new-bucket")).to_have_count(0)` as "nothing was created".

It is not free. `automation/tests/ui/toolkits/test_toolkit_creation_create_bucket_verify_list_files.py`
creates a REAL bucket named exactly `new-bucket` (`BUCKET_NAME = "new-bucket"`,
line 112) and deletes it with **best-effort** pre/post cleanup that logs a
warning and continues on failure. Project 399 already carries ~968 leaked
buckets (#636), so one failed teardown leaves `new-bucket` on the list
permanently — and every absolute `count(0)` assertion on it turns into a
standing FALSE RED, reported as "Cancel created a bucket" when nothing of the
kind happened.

## What to do instead

- Assert a **delta**, not an absolute: read the row's presence (or the whole
  `all_bucket_rows()` count) at step 1 and assert it unchanged at the end.
- Or assert the name's absence **up front** as an explicit precondition, so a
  leftover fails early with a precondition message instead of a misleading
  end-state one (ELITEA-1815's spec does exactly this for its own name).
- The honest primary oracle for "no bucket was created" on this surface is the
  network: `capture_requests_matching("artifacts/buckets")` catches ONLY
  mutations — the bucket LIST query is `/artifacts/s3/?…`
  (`EliteaUI/src/api/artifacts.js`), so a refetch never pollutes the capture and
  `== []` is a clean, non-flaky assertion.

Seen while reviewing PR #1681 (ELITEA-1813 / ELITEA-1815).

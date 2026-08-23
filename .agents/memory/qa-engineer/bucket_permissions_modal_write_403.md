---
name: Bucket permissions modal — writes 403 for the automation user, and a failed save looks successful
description: Manage Permissions writes are 403 for ${TEST_USER}; the UI still shows the exception row (optimistic rollback never runs)
type: project
aliases: [manage permissions, bucket access, exceptions table, add exception, optimistic row]
tags: [area/artifacts, type/blocker]
created: 2026-08-23
updated: 2026-08-23
---

## The access wall
`${TEST_USER}` can READ bucket permissions (`GET bucket_permissions/default/<id>` → 200) but every
WRITE is `403`: `POST s3_credentials/default/471` and `PUT bucket_permissions/default/406`. Project
400 has no buckets; 399 is personal (no menu item). So any case whose steps ADD/EDIT a bucket
exception is `blocked` until a human grants admin rights or provisions an admin identity —
`elitea-testing-public#1701`. Display-only halves are fine.

Knock-on: merged `tests/ui/artifacts/test_bucket_permissions_api.py` (ELITEA-2493/2494) uses this
write path as setup AND needs `TEST_USER_B_EMAIL`, which is empty in this machine's `.env.test`.

## The trap that makes it look like it worked
On the 403 the UI **still** replaces the empty state, increments `Exceptions – N` and lists the user
with the chosen permission — an optimistic row that is never rolled back, because
`BucketAccessTable.handleAccessChange` catches the error and only toasts (no re-throw), so
`Promise.allSettled` in `handleAddConfirm` never reports a rejection. A `Failed to update access`
toast does fire. **Re-open the modal to see the truth** (`Exceptions – 0`). Filed as
`elitea-testing-public#1700`. Never treat `Exceptions – N` as proof a write landed.

Related: [[[test-specs/artifacts/_surface.md]]] § Manage Permissions modal.

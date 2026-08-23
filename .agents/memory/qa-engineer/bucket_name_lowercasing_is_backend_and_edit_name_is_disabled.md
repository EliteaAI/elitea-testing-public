---
name: Bucket name lowercasing is backend-side; Edit-mode name field is disabled not readOnly
description: Where Elitea lowercases a bucket name, and how to assert the Edit form's non-editable Name field honestly
type: reference
aliases: [bucket lowercase, bucket name case, edit bucket read-only, artifacts-bucket-name-input disabled]
tags: [area/artifacts, type/handle]
created: 2026-08-23
updated: 2026-08-23
---

## Lowercasing happens in the BACKEND, not the form

`src/pages/Artifacts/CreateBucket.jsx` has **no `toLowerCase()`**; its yup schema
`^[a-zA-Z][a-zA-Z0-9-]*$` explicitly permits uppercase, and the form posts
`values.name.trim()` verbatim to `POST /api/v2/artifacts/buckets/default/{pid}`.
The **response body** comes back lowercased:
`{"message":"Created","id":"p--399.autotest-1812-182449","name":"autotest-1812-182449"}`.

Consequence for any "stored and displayed in lowercase" case: the DOM proves only
*displayed*. The POST response's `name` is the only honest oracle for *stored*. Assert both,
plus the negative (`artifacts-bucket-row-{TYPED_UPPERCASE}` count 0) — the row testid is
derived from the stored name (`BucketItem.jsx:243`), so its presence *is* a name assertion.

## Edit mode: `disabled`, never `readOnly`

`CreateBucket.jsx:238` → `disabled={!!currentBucket}` on the Name TextField.
Live readings in Edit mode: `get_attribute("disabled") == ""`, `get_attribute("readonly")
is None`, `is_disabled() True`, `is_editable() False`.

Two traps when automating "verify the field is read-only and no input is accepted":

1. `Locator.click()` **raises `TimeoutError`** (actionability: not enabled) — automate it as
   an expected timeout with a SHORT (2–3 s) timeout inside `pytest.raises`, not as a plain
   click that hangs for the default.
2. The deprecated `Locator.type()` does **NOT** raise on the disabled input — it silently
   no-ops. So `type()` succeeding proves nothing; the assertion that actually proves "no
   input accepted" is **`input_value()` unchanged afterwards**.

Also assert the field is **enabled in Create mode** as a control — without it,
`is_disabled() is True` in Edit mode passes equally well for a field that is always disabled.

Related: [[artifact_bucket_fixture_delete_silently_fails_404]]

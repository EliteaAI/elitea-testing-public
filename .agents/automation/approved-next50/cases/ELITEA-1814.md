---
id: ELITEA-1814
title: "Bucket Name Rejects Non-Alphanumeric Characters (Except Hyphen)"
priority: medium
type: functional
module: artifacts
status: draft
execution_type: automated
tags: [automated:UI:regression, feat:artifacts]
requirements: []
---

# ELITEA-1814: Bucket Name Rejects Non-Alphanumeric Characters (Except Hyphen)

**Module:** artifacts · **Priority:** medium · **Type:** functional

**Objective:** Verify that bucket names containing special characters ($, _, space) are rejected with the correct inline validation error and no bucket is created for any of these invalid inputs.

---

## Preconditions

- User is logged in to the Elitea platform.

---

## Test Data

| Field | Value |
|-------|-------|
| Invalid name 1 | new-bucket$ |
| Invalid name 2 | bucket_one |
| Invalid name 3 | bucket one |
| Validation error | Name should start with a letter and contain only letters, numbers, and hyphen |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to the Artifacts section | Artifacts page loads |
| 2 | Click the folder/create icon located above the bucket list | "New Bucket" form opens |
| 3 | Enter bucket name with a special character: "new-bucket$" | Name field accepts the input |
| 4 | Verify an inline validation error is displayed: "Name should start with a letter and contain only letters, numbers, and hyphen" | Inline error is shown |
| 5 | Verify the "Save" button remains active but the bucket is not created upon clicking Save | Clicking Save does not create the bucket |
| 6 | Verify "new-bucket$" does not appear in the bucket list | No bucket with that name appears |
| 7 | Repeat steps 1-4 with input "bucket_one" (underscore) | Form opens and "bucket_one" is entered |
| 8 | Click to "Artifacts" | Navigation to Artifacts root occurs |
| 9 | Verify the same error message is shown and the bucket is not created | Error message displayed; "bucket_one" not in list |
| 10 | Repeat steps 1-4 with input "bucket one" (space) | Form opens and "bucket one" is entered |
| 11 | Click to "Artifacts" | Navigation to Artifacts root occurs |
| 12 | Verify the same error message is shown and the bucket is not created | Error message displayed; "bucket one" not in list |

---

## Expected Final State

None of the invalid bucket names ($, _, space) result in bucket creation. The inline validation error is consistently shown for all invalid characters.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Validation error is shown for all invalid inputs and no bucket is created.

**Fail:**
- Any step produces an error or unexpected result.
- A bucket is created with invalid characters, or validation error is missing for any input.

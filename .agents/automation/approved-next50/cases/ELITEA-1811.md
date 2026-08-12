---
id: ELITEA-1811
title: "Bucket Name Cannot Start with a Number"
priority: medium
type: functional
module: artifacts
status: draft
execution_type: automated
tags: [automated:UI:regression, feat:artifacts]
requirements: []
---

# ELITEA-1811: Bucket Name Cannot Start with a Number

**Module:** artifacts · **Priority:** medium · **Type:** functional

**Objective:** Verify that a bucket name starting with a number is rejected with an inline validation error and that no bucket is created.

---

## Preconditions

- User is logged in to the Elitea platform.

---

## Test Data

| Field | Value |
|-------|-------|
| Invalid bucket name | 1bucket |
| Validation error message | Name should start with a letter and contain only letters, numbers, and hyphen |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to the Artifacts section in the left sidebar | Artifacts page loads |
| 2 | Click the folder/create icon located above the bucket list | "New Bucket" form opens |
| 3 | Enter bucket name: "1bucket" | Name field displays "1bucket" |
| 4 | Click "Save" | Save is attempted |
| 5 | Verify an inline validation error is displayed: "Name should start with a letter and contain only letters, numbers, and hyphen" | Inline validation error with correct message is shown |
| 6 | Click "Artifacts" | Navigation to Artifacts root occurs |
| 7 | Verify the bucket is not created and does not appear in the bucket list | "1bucket" is not in the bucket list |

---

## Expected Final State

No bucket named "1bucket" is created. The validation error is displayed inline on the form when an invalid name starting with a number is submitted.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Inline validation error is shown and no bucket is created.

**Fail:**
- Any step produces an error or unexpected result.
- Bucket is created with an invalid name, or validation error is not displayed.

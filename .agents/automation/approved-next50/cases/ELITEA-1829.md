---
id: ELITEA-1829
title: "Upload Flow – Duplicate Handling: Skip Skips Duplicate and Saves Non-Duplicate Files"
priority: medium
type: functional
module: artifacts
status: draft
execution_type: automated
tags: [automated:UI:regression, feat:artifacts]
requirements: []
---

# ELITEA-1829: Upload Flow – Duplicate Handling: Skip Skips Duplicate and Saves Non-Duplicate Files

**Module:** artifacts · **Priority:** medium · **Type:** functional

**Objective:** Verify that clicking "Skip" in the "Resolve duplicates" modal skips the duplicate file, uploads the non-duplicate file, and leaves the original duplicate unchanged.

---

## Preconditions

- User is logged in to the Elitea platform.
- Bucket "bucket-1" contains "sample.txt" but does NOT contain "sample.png".
- Local files "sample.txt" (duplicate) and "sample.png" (new) are available for upload.

---

## Test Data

| Field | Value |
|-------|-------|
| Bucket name | bucket-1 |
| Duplicate file | sample.txt |
| New file | sample.png |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to the Artifacts section in the left sidebar | Artifacts page loads |
| 2 | Click on "bucket-1" in the bucket list that already contains "sample.txt" but does NOT contain "sample.png" | Bucket is selected |
| 3 | Click the upload icon in the top-right corner of the main panel | System file explorer opens |
| 4 | Verify the system file explorer opens immediately | File explorer is open |
| 5 | Select both "sample.txt" (duplicate) and "sample.png" (new file) and click "Open" | Both files are selected |
| 6 | Verify the "Upload files to ..." modal opens with the Path field pre-filled with "bucket-1" | Modal is open |
| 7 | Click "Upload" | Duplicate detection is triggered |
| 8 | Verify the "Resolve duplicates" modal opens listing "sample.txt" as the duplicate file | Modal shows "sample.txt" as duplicate |
| 9 | Click "Skip" | Skip action completes |
| 10 | Verify a success notification is displayed: "Your file(s) have been successfully uploaded!" | Success notification appears |
| 11 | Verify "sample.png" is listed in the file table as a newly uploaded file | "sample.png" appears in the file table |
| 12 | Verify only one "sample.txt" entry exists in the file table (the original, not replaced) | Exactly one "sample.txt" row is present |
| 13 | Verify the "Last update" timestamp for "sample.txt" has NOT changed | Original timestamp is preserved |

---

## Expected Final State

"sample.png" is uploaded successfully. "sample.txt" is skipped (original unchanged, timestamp preserved). Only one entry of "sample.txt" exists.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Non-duplicate file is uploaded; duplicate is skipped with original timestamp unchanged.

**Fail:**
- Any step produces an error or unexpected result.
- Duplicate file is overwritten or "sample.png" is not uploaded after Skip.

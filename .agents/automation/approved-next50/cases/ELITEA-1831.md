---
id: ELITEA-1831
title: "Upload Flow – Duplicate Handling: Keep Both Saves Both Files with copy Suffix"
priority: medium
type: functional
module: artifacts
status: draft
execution_type: automated
tags: [automated:UI:regression, feat:artifacts]
requirements: []
---

# ELITEA-1831: Upload Flow – Duplicate Handling: Keep Both Saves Both Files with copy Suffix

**Module:** artifacts · **Priority:** medium · **Type:** functional

**Objective:** Verify that clicking "Keep both" in the "Resolve duplicates" modal results in both the original and the new file being saved, with the new file having a "copy" suffix in its name.

---

## Preconditions

- User is logged in to the Elitea platform.
- Bucket "bucket-1" already contains "sample.txt".
- A local file named "sample.txt" is available for upload.

---

## Test Data

| Field | Value |
|-------|-------|
| Bucket name | bucket-1 |
| Duplicate file | sample.txt |
| Expected copy name | sample-copy.txt (or similar with "copy" in name) |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to the Artifacts section in the left sidebar | Artifacts page loads |
| 2 | Click on "bucket-1" in the bucket list that already contains "sample.txt" | Bucket is selected |
| 3 | Click the upload icon in the top-right corner of the main panel | System file explorer opens |
| 4 | Verify the system file explorer opens immediately | File explorer is open |
| 5 | Select "sample.txt" (same name as the existing file) and click "Open" | "Upload files to ..." modal opens |
| 6 | Verify the "Upload files to ..." modal opens with the Path field pre-filled with "bucket-1" | Modal is open |
| 7 | Click "Upload" | Duplicate detection is triggered |
| 8 | Verify the "Resolve duplicates" modal opens listing "sample.txt" as the duplicate file | Modal shows "sample.txt" as duplicate |
| 9 | Click "Keep both" | Keep both action completes |
| 10 | Verify a success notification is displayed: "Your file(s) have been successfully uploaded!" | Success notification appears |
| 11 | Verify the file table contains two entries: the original "sample.txt" and a new entry with "copy" added to the name (e.g. "sample-copy.txt") | Two entries are present: original and copy |
| 12 | Verify both files have their own distinct "Last update" timestamps | Each file has a different timestamp |

---

## Expected Final State

Both the original "sample.txt" and a renamed copy (e.g. "sample-copy.txt") exist in the file table, each with distinct "Last update" timestamps.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Two entries exist with distinct timestamps; copy file has "copy" in its name.

**Fail:**
- Any step produces an error or unexpected result.
- Only one entry exists, copy suffix is missing, or timestamps are identical.

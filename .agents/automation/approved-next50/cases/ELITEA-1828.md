---
id: ELITEA-1828
title: "Upload Flow – Duplicate File Detected and Resolve Duplicates Modal Appears"
priority: medium
type: functional
module: artifacts
status: draft
execution_type: automated
tags: [automated:UI:regression, feat:artifacts]
requirements: []
---

# ELITEA-1828: Upload Flow – Duplicate File Detected and Resolve Duplicates Modal Appears

**Module:** artifacts · **Priority:** medium · **Type:** functional

**Objective:** Verify that when uploading a file with the same name as an existing file, the "Resolve duplicates" modal appears with the correct message, file name, and action buttons.

---

## Preconditions

- User is logged in to the Elitea platform.
- Bucket "bucket-1" already contains a file named "sample.md".
- A local file named "sample.md" is available for upload.

---

## Test Data

| Field | Value |
|-------|-------|
| Bucket name | bucket-1 |
| Duplicate file | sample.md |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to the Artifacts section in the left sidebar | Artifacts page loads |
| 2 | Click on "bucket-1" in the bucket list that already contains "sample.md" | Bucket is selected and "sample.md" is visible |
| 3 | Click the upload icon in the top-right corner of the main panel | System file explorer opens |
| 4 | Verify the system file explorer/Open dialog window opens immediately | File explorer is open |
| 5 | Select a file named "sample.md" (same name as the existing file) and click "Open" | "Upload files to ..." modal opens |
| 6 | Verify the "Upload files to ..." modal opens with the Path field pre-filled with "bucket-1" | Modal is open with correct path |
| 7 | Click "Upload" | Duplicate detection is triggered |
| 8 | Verify the "Resolve duplicates" modal opens with the message: "This file already exists in this bucket. Choose how to handle duplicates." | "Resolve duplicates" modal appears with correct message |
| 9 | Verify the duplicate file name "sample.md" is listed in the modal | "sample.md" is shown as the duplicate |
| 10 | Verify the modal contains four buttons: "Cancel", "Skip", "Replace", "Keep both" | All four action buttons are present |

---

## Expected Final State

The "Resolve duplicates" modal is displayed with the correct message, duplicate file name, and all four action buttons (Cancel, Skip, Replace, Keep both) when uploading a file that already exists in the bucket.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- "Resolve duplicates" modal appears with correct message and all four buttons.

**Fail:**
- Any step produces an error or unexpected result.
- Duplicate detection modal does not appear, or modal shows incorrect content.

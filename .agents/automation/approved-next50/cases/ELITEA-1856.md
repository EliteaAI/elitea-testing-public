---
id: ELITEA-1856
title: "File Preview/Edit – Actions Dropdown in Editor Contains Copy Content, Download, Delete"
priority: medium
type: functional
module: artifacts
status: draft
execution_type: automated
tags: [automated:UI:regression, feat:artifacts]
requirements: []
---

# ELITEA-1856: File Preview/Edit – Actions Dropdown in Editor Contains Copy Content, Download, Delete

**Module:** artifacts · **Priority:** medium · **Type:** functional

**Objective:** Verify that the 3-dot actions menu in the editor panel contains "Copy Content", "Download", and "Delete", and that each action works correctly.

---

## Preconditions

- User is logged in to the Elitea platform.
- Bucket "bucket-1" contains "machine_learning.py".

---

## Test Data

| Field | Value |
|-------|-------|
| Bucket name | bucket-1 |
| File name | machine_learning.py |
| Delete confirmation message | Are you sure to delete machine_learning.py? It can't be restored. |
| Delete success notification | The artifacts have been deleted successfully |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to the Artifacts section and open "machine_learning.py" in "bucket-1" via the "View/Edit file" icon | Editor opens |
| 2 | Verify the editor panel is open | Editor is visible |
| 3 | Click the 3-dot (ellipsis) actions menu icon in the top-right of the editor panel | Dropdown opens |
| 4 | Verify a dropdown opens with three options: "Copy Content", "Download", "Delete" | All three options are present |
| 5 | Click "Copy Content" | File content is copied to clipboard |
| 6 | Verify the file content is copied to the clipboard (paste into a text editor to confirm the full content is present) | Pasted content matches file content |
| 7 | Click the 3-dot menu again and click "Download" | File download initiates |
| 8 | Verify the file "machine_learning.py" starts downloading to the local machine | Download starts |
| 9 | Verify the downloaded file is not corrupted and matches the file name | File is accessible and named correctly |
| 10 | Click the 3-dot menu again and click "Delete" | Delete confirmation modal opens |
| 11 | Verify a "Delete confirmation" modal opens with message: "Are you sure to delete machine_learning.py? It can't be restored." | Modal shows correct message |
| 12 | Click "Delete" in the modal | Deletion completes |
| 13 | Verify a success notification is displayed: "The artifacts have been deleted successfully" | Success notification appears |
| 14 | Verify the editor closes and "machine_learning.py" is no longer listed in the "bucket-1" file table | Editor closes; file is removed from table |

---

## Expected Final State

All three editor actions (Copy Content, Download, Delete) work correctly. After Delete, the file is removed from the bucket.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- All three actions work; file is deleted and removed from the table.

**Fail:**
- Any step produces an error or unexpected result.
- Any action fails, or file is not removed after delete.

---
id: ELITEA-1851
title: "File Preview/Edit – Open Supported Text File via View/Edit Icon and Verify Editor UI"
priority: high
type: functional
module: artifacts
status: draft
execution_type: automated
tags: [automated:UI:regression, feat:artifacts]
requirements: []
---

# ELITEA-1851: File Preview/Edit – Open Supported Text File via View/Edit Icon and Verify Editor UI

**Module:** artifacts · **Priority:** high · **Type:** functional

**Objective:** Verify that clicking the "View/Edit file" icon on a supported text file opens it in the editor panel with all expected UI elements: file path header, language label, line numbers, Save/Discard buttons, 3-dot menu, close icon, and updated URL.

---

## Preconditions

- User is logged in to the Elitea platform.
- Bucket "bucket-1" contains "machine_learning.py" (Python, 18.5 KB).

---

## Test Data

| Field | Value |
|-------|-------|
| Bucket name | bucket-1 |
| File name | machine_learning.py |
| Language label | Python (detected) |
| File size | 18.5 KB |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to the Artifacts section in the left sidebar | Artifacts page loads |
| 2 | Click on "bucket-1" in the bucket list | Bucket is selected |
| 3 | Verify the file table displays "machine_learning.py" (Python, 18.5 KB) | File is visible |
| 4 | Hover over the "machine_learning.py" file row | "View/Edit file" icon appears on the right side of the row |
| 5 | Verify a "View/Edit file" (loop/magnifier) icon appears on hover | Icon is visible |
| 6 | Click the "View/Edit file" icon | Editor panel opens in main area |
| 7 | Verify the file opens in the editor panel | Editor is visible |
| 8 | Verify the panel header displays the full file path: "bucket-1/machine_learning.py" | Header shows correct path |
| 9 | Verify a language label is shown: "Python (detected)" with a dropdown arrow | Language label is present |
| 10 | Verify the file content is displayed with line numbers on the left | Line numbers are visible |
| 11 | Verify "Save" (active/highlighted blue) and "Discard" buttons are present in the top-right | Both buttons are visible and Save is active |
| 12 | Verify a 3-dot (ellipsis) actions menu icon is present next to the Discard button and is active and clickable | 3-dot menu is present and clickable |
| 13 | Verify an X (close) icon is present to close the editor panel | Close icon is visible |
| 14 | Verify the URL updates to reflect the open file path (e.g. "...?bucket=bucket-1&file=machine_learning.py") | URL includes file parameter |

---

## Expected Final State

The file editor is open with all required UI elements: file path header, language label, line numbers, active Save/Discard buttons, 3-dot menu, close icon, and correct URL.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- All editor UI elements are present and in the correct state.

**Fail:**
- Any step produces an error or unexpected result.
- Any editor UI element is missing, incorrectly labelled, or in the wrong state.

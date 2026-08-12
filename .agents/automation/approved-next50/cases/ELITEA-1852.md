---
id: ELITEA-1852
title: "File Preview/Edit – Edit File Content and Save Changes Successfully"
priority: high
type: functional
module: artifacts
status: draft
execution_type: automated
tags: [automated:UI:regression, feat:artifacts]
requirements: []
---

# ELITEA-1852: File Preview/Edit – Edit File Content and Save Changes Successfully

**Module:** artifacts · **Priority:** high · **Type:** functional

**Objective:** Verify that editing file content in the editor and clicking Save persists the changes, updates the "Last update" timestamp, and that the saved change is visible when the file is reopened.

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
| Edit line | 17 |
| Added text | # edited line |
| Success notification | File saved successfully |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to the Artifacts section and open "machine_learning.py" in "bucket-1" via the "View/Edit file" icon | Editor opens for the file |
| 2 | Verify the file opens in edit mode with line numbers and file content visible and content is scrollable up and down | Editor is fully functional and scrollable |
| 3 | Click into the file content area at an existing line (e.g. line 17) | Text cursor appears at line 17 |
| 4 | Add new text: "# edited line" on that line | Text "# edited line" appears in the editor |
| 5 | Verify the edited text appears in the editor immediately | Change is visible in real time |
| 6 | Click the "Save" button in the top-right | Save operation completes |
| 7 | Verify a green success notification is displayed: "File saved successfully" | Success notification appears |
| 8 | Verify the editor closes and the main panel returns to the "bucket-1" file table | Editor closes; file table is shown |
| 9 | Verify the "Last update" timestamp for "machine_learning.py" has been updated to the current date and time | Timestamp is updated |
| 10 | Reopen "machine_learning.py" and verify the saved change "# edited line" is present | "# edited line" is visible at line 17 |

---

## Expected Final State

The edit "# edited line" is persisted in "machine_learning.py". The "Last update" timestamp reflects the time of the save operation.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Edit is saved; success notification shown; timestamp updated; change visible on reopen.

**Fail:**
- Any step produces an error or unexpected result.
- Edit is not saved, timestamp not updated, or change not present on reopen.

---
id: ELITEA-1858
title: "File Preview/Edit – Markdown File Raw Tab Enables Editing with Save and Discard Active"
priority: medium
type: functional
module: artifacts
status: draft
execution_type: automated
tags: [automated:UI:regression, feat:artifacts]
requirements: []
---

# ELITEA-1858: File Preview/Edit – Markdown File Raw Tab Enables Editing with Save and Discard Active

**Module:** artifacts · **Priority:** medium · **Type:** functional

**Objective:** Verify that switching to the "Raw" tab for a Markdown file enables editing with line numbers, activates Save/Discard buttons, and that saved changes are visible in Preview tab on reopen.

---

## Preconditions

- User is logged in to the Elitea platform.
- Bucket "bucket-1" contains "project-background.md" with heading "# Project Overview" on line 1.

---

## Test Data

| Field | Value |
|-------|-------|
| Bucket name | bucket-1 |
| File name | project-background.md |
| Original heading | # Project Overview |
| Updated heading | # Project Overview Updated |
| Success notification | File saved successfully |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to the Artifacts section and open "project-background.md" in "bucket-1" via the "View/Edit file" icon | Editor opens in Preview mode |
| 2 | Verify the file opens in "Preview" tab by default with rendered Markdown | Preview tab is active and Markdown is rendered |
| 3 | Click the "Raw" tab | Raw tab becomes active |
| 4 | Verify the "Raw" tab becomes active/highlighted and "Preview" tab becomes inactive | Raw tab is highlighted; Preview is inactive |
| 5 | Verify the file content is now displayed as raw Markdown text with line numbers | Raw content with line numbers is visible |
| 6 | Verify the "Save" and "Discard" buttons in the top-right become ACTIVE/enabled | Both buttons are enabled |
| 7 | Click into the content area on line 1 and modify the heading (e.g. change "# Project Overview" to "# Project Overview Updated") | Heading is changed |
| 8 | Verify the change is visible in the Raw editor | Updated text is shown |
| 9 | Click "Save" | Save operation completes |
| 10 | Verify a success notification is displayed: "File saved successfully" | Success notification appears |
| 11 | Reopen "project-background.md" and click the "Preview" tab | File is reopened in Preview mode |
| 12 | Verify the updated heading "# Project Overview Updated" is rendered in the Preview | Updated heading is shown in rendered view |

---

## Expected Final State

The Raw tab enables editing; the change is saved; the updated heading is visible in the Preview tab when the file is reopened.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Raw tab enables editing; change persists; updated heading visible in Preview.

**Fail:**
- Any step produces an error or unexpected result.
- Raw tab does not enable editing, or saved change not visible in Preview.

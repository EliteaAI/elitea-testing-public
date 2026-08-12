---
id: ELITEA-1857
title: "File Preview/Edit – Markdown File Opens in Preview Mode by Default with Save/Discard Inactive"
priority: medium
type: functional
module: artifacts
status: draft
execution_type: automated
tags: [automated:UI:regression, feat:artifacts]
requirements: []
---

# ELITEA-1857: File Preview/Edit – Markdown File Opens in Preview Mode by Default with Save/Discard Inactive

**Module:** artifacts · **Priority:** medium · **Type:** functional

**Objective:** Verify that a Markdown file opens in the editor with the "Preview" tab active by default, displaying rendered Markdown, and that Save/Discard buttons are inactive and editing is not possible in Preview mode.

---

## Preconditions

- User is logged in to the Elitea platform.
- Bucket "bucket-1" contains "project-background.md" with formatted Markdown content.

---

## Test Data

| Field | Value |
|-------|-------|
| Bucket name | bucket-1 |
| File name | project-background.md |
| Expected rendered headings | Project Overview, Scope, Architecture, Key Components |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to the Artifacts section and click on "bucket-1" | Bucket is selected |
| 2 | Hover over "project-background.md" in the file table and click the "View/Edit file" icon | Editor panel opens |
| 3 | Verify the editor panel opens with the header displaying: "bucket-1/project-background.md" | Header shows correct path |
| 4 | Verify a language label is shown: "Markdown (detected)" with a dropdown arrow | Language label is present |
| 5 | Verify two tabs are present: "Preview" (active/selected by default) and "Raw" | Both tabs are visible; "Preview" is active |
| 6 | Verify the "Preview" tab is highlighted/active | Preview tab is highlighted |
| 7 | Verify the file content is rendered as formatted Markdown (headings, bullet points, bold text etc.) | Rendered Markdown is displayed |
| 8 | Verify the "Save" and "Discard" buttons in the top-right are INACTIVE/greyed out in Preview mode | Both buttons are disabled/greyed out |
| 9 | Attempt to click anywhere in the rendered preview content area and type text | No text cursor appears; no input is accepted |
| 10 | Verify no text cursor appears and no edits can be made in Preview mode | Editing is blocked in Preview mode |
| 11 | Verify the 3-dot (ellipsis) actions menu is still present and accessible | Actions menu is accessible |

---

## Expected Final State

"project-background.md" opens with the Preview tab active, showing rendered Markdown. Save and Discard buttons are inactive. Editing is not possible in Preview mode.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Preview tab active by default; Markdown rendered; Save/Discard inactive; editing blocked.

**Fail:**
- Any step produces an error or unexpected result.
- Raw tab active by default, or editing possible in Preview mode, or buttons are active.

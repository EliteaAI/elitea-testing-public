---
id: ELITEA-1862
title: "File Preview/Edit – Image File Opens Directly as Image Preview with Inactive Edit Controls"
priority: medium
type: functional
module: artifacts
status: draft
execution_type: automated
tags: [automated:UI:regression, feat:artifacts]
requirements: []
---

# ELITEA-1862: File Preview/Edit – Image File Opens Directly as Image Preview with Inactive Edit Controls

**Module:** artifacts · **Priority:** medium · **Type:** functional

**Objective:** Verify that an image file opens directly as a visual image preview in the editor panel, with Save/Discard buttons inactive, no text editor, no Preview/Raw tabs, and an actions menu limited to Download and Delete.

---

## Preconditions

- User is logged in to the Elitea platform.
- Bucket "bucket-1" contains "diagram (2).png".

---

## Test Data

| Field | Value |
|-------|-------|
| Bucket name | bucket-1 |
| File name | diagram (2).png |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to the Artifacts section and click on bucket "bucket-1" | Bucket is selected |
| 2 | Hover over file "diagram (2).png" in the left panel tree or file table | "View/Edit file" icon appears on hover |
| 3 | Verify a "View/Edit file" icon appears on hover | Icon is visible |
| 4 | Click on file "diagram (2).png" or its "View/Edit file" icon | Image preview opens in main panel |
| 5 | Verify the file opens in the main panel displaying the image directly | Image is displayed in the panel |
| 6 | Verify the panel header displays the full path: "bucket-1/diagram (2).png" | Header shows correct path |
| 7 | Verify the "Save" and "Discard" buttons in the top-right are INACTIVE/greyed out | Both buttons are disabled |
| 8 | Verify no "Preview" / "Raw" tabs are shown | No tabs are visible |
| 9 | Verify no text editor or content editing area is present — only the image is displayed | Only image is shown; no text editor |
| 10 | Verify the 3-dot (ellipsis) actions menu is present | Actions menu is accessible |
| 11 | Click the 3-dot menu — verify the dropdown contains only "Download" and "Delete" (no "Copy Content" option) | Only Download and Delete are shown |

---

## Expected Final State

Image file opens as a visual preview. Save/Discard are inactive. No tabs or text editor shown. Actions menu contains only Download and Delete.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Image preview shown; Save/Discard inactive; no tabs; no text editor; actions limited to Download and Delete.

**Fail:**
- Any step produces an error or unexpected result.
- Text editor shown, tabs present, buttons active, or "Copy Content" in actions menu.

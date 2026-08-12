---
id: ELITEA-2055
title: "Pipeline — Editor Notes"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2055: Pipeline — Editor Notes

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that editor notes can be entered in the EDITOR NOTES section and that the text persists correctly after save and reload.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline is open for editing.

---

## Test Data

| Field | Value |
|-------|-------|
| Editor notes text | This pipeline is under development. Do not publish. |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline | Pipeline is loaded in the editor |
| 2 | Expand "EDITOR NOTES" section in left panel | EDITOR NOTES section is visible |
| 3 | Locate "Notes" textbox (with info tooltip icon) | Notes textbox is visible |
| 4 | Enter text: "This pipeline is under development. Do not publish." | Notes textbox is populated with the entered text |
| 5 | Save pipeline | Pipeline saves without errors |
| 6 | Reload page | Page reloads |
| 7 | Verify notes text persists: "This pipeline is under development. Do not publish." | Notes text is correctly restored after reload |

---

## Expected Final State

The editor notes text "This pipeline is under development. Do not publish." persists correctly after save and page reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Notes text is present and unchanged after save and reload.

**Fail:**
- Any step produces an error or unexpected result.
- Notes text is lost or modified after reload.

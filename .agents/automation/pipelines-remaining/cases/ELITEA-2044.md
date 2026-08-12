---
id: ELITEA-2044
title: "Pipeline — State Panel Delete Custom Variable"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2044: Pipeline — State Panel Delete Custom Variable

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that a custom state variable can be deleted from the State panel, that default variables (input, messages) cannot be deleted, and that the deletion persists in the YAML after saving.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with at least one custom state variable (e.g., "custom_output") exists.

---

## Test Data

| Field | Value |
|-------|-------|
| Custom variable to delete | custom_output |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline with a custom state variable (e.g., "custom_output") | Pipeline is open with "custom_output" in state |
| 2 | Click "State" button | STATE panel opens |
| 3 | Locate the trash icon (delete) button next to "custom_output" | Trash icon is visible next to "custom_output" |
| 4 | Click trash icon — verify variable is removed from panel | "custom_output" is removed from the State panel |
| 5 | Verify default "input" and "messages" do NOT have delete buttons (immutable) | "input" and "messages" have no trash/delete buttons |
| 6 | Save pipeline — verify removal persists in YAML | YAML state section does not include "custom_output" after save |

---

## Expected Final State

The custom variable "custom_output" is permanently deleted from the State panel and YAML. Default variables "input" and "messages" remain and have no delete option.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- "custom_output" is deleted from panel and YAML; default variables have no delete buttons.

**Fail:**
- Any step produces an error or unexpected result.
- Custom variable is not deleted, or default variables show delete buttons.

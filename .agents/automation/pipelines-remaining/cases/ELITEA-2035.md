---
id: ELITEA-2035
title: "Pipeline — State Modifier Node Configuration"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2035: Pipeline — State Modifier Node Configuration

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that a State modifier node can be configured with a Jinja template, input, and output variables, and that all configuration persists after save and reload.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with state variables exists.

---

## Test Data

| Field | Value |
|-------|-------|
| Jinja Template | ## GitHub Issue\n\n{{ issue_details }} |
| Input variable | issue_details |
| Output variable | normalized_issue |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline and add a State modifier node via "Add node" → "State modifier" | State modifier node appears on canvas |
| 2 | Verify State modifier node panel shows: Jinja Template (text area), "Variables to clean" (expandable section), Input combobox, Output combobox | All listed sections are present |
| 3 | In "Jinja Template" field enter: "## GitHub Issue\n\n{{ issue_details }}" | Jinja template field accepts the value |
| 4 | Expand "Variables to clean" section (if applicable) | Section expands as expected |
| 5 | Set Input combobox — add variable "issue_details" | "issue_details" is added to Input |
| 6 | Set Output combobox — add variable "normalized_issue" | "normalized_issue" is added to Output |
| 7 | Save pipeline | Pipeline saves without errors |
| 8 | Reload — verify Jinja Template text, Input, and Output persist | All State modifier fields are correctly restored after reload |

---

## Expected Final State

The State modifier node is fully configured with Jinja template, Input "issue_details", and Output "normalized_issue", all persisting after save and reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Jinja Template, Input, and Output persist correctly after reload.

**Fail:**
- Any step produces an error or unexpected result.
- Any field is lost after saving.

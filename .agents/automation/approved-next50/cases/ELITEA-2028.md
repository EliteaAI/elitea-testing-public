---
id: ELITEA-2028
title: "Pipeline — YAML to Flow Sync"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2028: Pipeline — YAML to Flow Sync

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that changes made in the YAML editor are immediately reflected in the Flow (visual) view, and that the Save button is enabled after a YAML edit.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with at least two nodes exists.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline and switch to "Yaml" view | YAML editor is displayed with the pipeline definition |
| 2 | Modify YAML by changing a node's transition target (e.g., change "END" to a different existing node) | YAML content is edited with the new transition value |
| 3 | Switch back to "Flow" view | Flow (visual) view is displayed |
| 4 | Verify the canvas reflects the updated edge (the edge now points to the new target node) | Canvas shows the modified edge connecting to the new target node |
| 5 | Verify "Save" button becomes enabled (indicating unsaved changes detected) | Save button is active/enabled |

---

## Expected Final State

A YAML edit to a node's transition is immediately reflected in the Flow view as an updated edge on the canvas, and the Save button is enabled indicating the change is pending save.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- YAML edit is reflected in Flow view with the correct updated edge, and Save button is enabled.

**Fail:**
- Any step produces an error or unexpected result.
- Canvas does not update after YAML edit, or Save button remains disabled.

---
id: ELITEA-2067
title: "Pipeline — YAML Editor Edit and Save"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2067: Pipeline — YAML Editor Edit and Save

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that edits made directly in the YAML editor are reflected in the Flow view, that the Save button activates, and that the edit persists after save and reload.

---

## Preconditions

- User is logged in to the Elitea platform.
- An existing pipeline is open.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline and switch to "Yaml" view | YAML editor is displayed |
| 2 | Click into the YAML editor area | Cursor is placed in the editor |
| 3 | Make a valid edit (e.g., change a node's output variable name) | YAML content is modified |
| 4 | Switch to "Flow" view — verify the change is reflected in node configuration | Flow view shows the modified configuration |
| 5 | Verify "Save" button is enabled | Save button is active |
| 6 | Click "Save" | Pipeline saves without errors |
| 7 | Reload page — switch to Yaml view — verify the edit persisted | YAML shows the modification after reload |

---

## Expected Final State

A YAML edit is reflected in the Flow view, the Save button activates, and the edit persists after save and reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- YAML edit is reflected in Flow view; save completes; edit persists after reload.

**Fail:**
- Any step produces an error or unexpected result.
- YAML edit is not reflected in Flow view, save fails, or edit is lost after reload.

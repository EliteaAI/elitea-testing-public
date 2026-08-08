---
id: ELITEA-2054
title: "Pipeline — Advanced Settings (Step Limit)"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2054: Pipeline — Advanced Settings (Step Limit)

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the Step limit field in Advanced settings can be modified and that the new value persists after save and page reload.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline is open for editing.

---

## Test Data

| Field | Value |
|-------|-------|
| Step limit | 10 |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline | Pipeline is loaded in the editor |
| 2 | Expand "Advanced" section in left panel | Advanced section is visible |
| 3 | Locate "Step limit" field (textbox with info tooltip icon) | Step limit field is visible |
| 4 | Change value from default (e.g., "25") to "10" | Step limit field shows "10" |
| 5 | Save pipeline | Pipeline saves without errors |
| 6 | Reload page | Page reloads |
| 7 | Verify Step limit field shows "10" | Step limit is persisted as "10" after reload |

---

## Expected Final State

The Step limit value is changed to "10" and persists correctly after save and page reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Step limit "10" is shown after save and reload.

**Fail:**
- Any step produces an error or unexpected result.
- Step limit reverts to default or shows incorrect value after reload.

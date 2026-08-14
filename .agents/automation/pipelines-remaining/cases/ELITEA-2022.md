---
id: ELITEA-2022
title: "Delete Pipeline"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2022: Delete Pipeline

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that a pipeline can be permanently deleted via the three-dot menu and that the user is redirected to the Pipelines dashboard with the deleted pipeline no longer visible.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline named "ToDelete_Pipeline" exists and is saved.

---

## Test Data

| Field | Value |
|-------|-------|
| Pipeline name | ToDelete_Pipeline |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline named "ToDelete_Pipeline" | Pipeline is created |
| 2 | Save it | Pipeline is saved successfully |
| 3 | Open the three-dot menu (next to version controls) | Three-dot menu opens |
| 4 | Click "Delete" option from the menu | Delete confirmation dialog opens |
| 5 | Confirm deletion in the confirmation dialog | Deletion is submitted |
| 6 | Verify redirect to Pipelines dashboard (URL: /app/pipelines/all) | Browser navigates to the Pipelines dashboard |
| 7 | Verify "ToDelete_Pipeline" no longer appears in the pipeline list | The deleted pipeline is not visible in the dashboard list |

---

## Expected Final State

The pipeline "ToDelete_Pipeline" is permanently deleted. The user is redirected to the Pipelines dashboard and the pipeline no longer appears in the list.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Pipeline is deleted, user is redirected to dashboard, and pipeline is absent from the list.

**Fail:**
- Any step produces an error or unexpected result.
- Pipeline is not deleted, redirect does not occur, or pipeline still appears in the list.

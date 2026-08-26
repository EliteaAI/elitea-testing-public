---
id: ELITEA-2024
title: "Pipeline Dashboard — View Toggle (Card vs Table)"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2024: Pipeline Dashboard — View Toggle (Card vs Table)

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the Pipelines dashboard supports toggling between Card list view and Table view, and that each view correctly changes the layout format.

---

## Preconditions

- User is logged in to the Elitea platform.
- The Pipelines dashboard contains at least one pipeline.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to Pipelines dashboard | Dashboard loads with pipelines visible |
| 2 | Locate the "Small View Toggler" group with "Table view" and "Card list view" buttons | Both view toggle buttons are visible |
| 3 | Verify default view is Card list view (button is pressed/active) | Card list view button is shown as active/pressed |
| 4 | Click "Table view" button | Table view is activated |
| 5 | Verify layout changes to table format (rows with columns instead of cards) | Pipelines are displayed in a table/row format |
| 6 | Click "Card list view" button | Card list view is activated |
| 7 | Verify layout returns to card grid format | Pipelines are displayed as cards in a grid |

---

## Expected Final State

The view toggle works correctly: Table view displays pipelines in row/column format, Card list view displays them as cards. The default is Card list view.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Both view modes work correctly and the default is Card list view.

**Fail:**
- Any step produces an error or unexpected result.
- View does not switch, or layout does not change as expected.

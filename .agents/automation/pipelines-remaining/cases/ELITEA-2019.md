---
id: ELITEA-2019
title: "Pipeline Canvas — Zoom and Pan"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2019: Pipeline Canvas — Zoom and Pan

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the pipeline canvas zoom and pan controls function correctly, allowing users to zoom in/out and pan, with Fit View restoring all-nodes-visible state.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with multiple nodes exists.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline with multiple nodes on canvas | Pipeline canvas loads with nodes visible |
| 2 | Use Fit View button — verify all nodes are visible | Canvas adjusts so all nodes are visible within the viewport |
| 3 | Zoom in using zoom controls or scroll | Canvas zoom level increases; nodes appear larger |
| 4 | Verify zoom level changes (nodes appear larger) | Nodes are visibly larger compared to default zoom |
| 5 | Pan the canvas by dragging | Canvas viewport position changes |
| 6 | Verify viewport position changes | Canvas has scrolled/panned to new position |
| 7 | Click Fit View again — verify returns to all-nodes-visible state | All nodes are visible again within the viewport |

---

## Expected Final State

The canvas zoom and pan controls work as expected: zoom in enlarges nodes, dragging pans the viewport, and Fit View restores the all-nodes-visible state.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Zoom, pan, and Fit View controls all work as described.

**Fail:**
- Any step produces an error or unexpected result.
- Zoom/pan controls are non-functional or Fit View does not restore all-nodes-visible state.

---
id: ELITEA-2060
title: "Pipeline — Node Deletion via Node Menu"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2060: Pipeline — Node Deletion via Node Menu

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that a node can be deleted using the trash icon on the node's action buttons, and that the node and all connected edges are removed with the Save button becoming enabled.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with multiple connected nodes exists.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline with multiple nodes | Pipeline canvas is displayed with multiple nodes |
| 2 | Hover over or select a non-entry-point node on the canvas | Node is highlighted or selected |
| 3 | Locate the node's action buttons (two small buttons on the node header) | Action buttons are visible on the node |
| 4 | Click the delete button (trash icon) on the node | Node deletion is triggered |
| 5 | Verify node is removed from canvas | Node no longer appears on the canvas |
| 6 | Verify edges to/from that node are removed | All edges connected to the deleted node are gone |
| 7 | Verify "Save" button becomes enabled | Save button is active indicating unsaved changes |

---

## Expected Final State

The node and all its connected edges are removed from the canvas via the node's trash icon button. The Save button becomes enabled to reflect the unsaved change.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Node and edges are removed; Save button becomes enabled.

**Fail:**
- Any step produces an error or unexpected result.
- Node is not deleted, edges remain, or Save button does not become enabled.

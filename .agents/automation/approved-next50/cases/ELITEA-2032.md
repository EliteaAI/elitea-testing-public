---
id: ELITEA-2032
title: "Pipeline — Edge Deletion"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2032: Pipeline — Edge Deletion

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that an edge on the pipeline canvas can be deleted, that the source node's transition field is cleared, and that the deletion persists after save.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with edges connecting nodes exists.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline with edges connecting nodes | Pipeline canvas is displayed with connected nodes and visible edges |
| 2 | Click on an edge on the canvas (edges are clickable groups) | Edge is selected/highlighted |
| 3 | Delete the edge (via delete key or context action) | Edge deletion is triggered |
| 4 | Verify the edge is removed from canvas | Edge line is no longer visible on the canvas |
| 5 | Verify the node's transition field is cleared | The source node's transition/routes field is empty or set to no target |
| 6 | Save — verify edge removal persists | No edge between those nodes after page reload |

---

## Expected Final State

The deleted edge is permanently removed from the canvas, the source node's transition field is cleared, and the deletion persists after save.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Edge is removed from canvas, transition field is cleared, and deletion persists after save.

**Fail:**
- Any step produces an error or unexpected result.
- Edge is not removed, transition field retains old value, or deletion is not saved.

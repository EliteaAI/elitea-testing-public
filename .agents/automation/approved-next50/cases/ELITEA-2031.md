---
id: ELITEA-2031
title: "Pipeline — Edge Creation Between Nodes"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2031: Pipeline — Edge Creation Between Nodes

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that an edge can be created between two pipeline nodes by setting the transition field, and that the edge appears on the canvas and persists after save and reload.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with at least 2 nodes (e.g., LLM + Printer) exists.

---

## Test Data

| Field | Value |
|-------|-------|
| Source node | LLM node |
| Target node | Printer node |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline with at least 2 nodes (e.g., LLM + Printer) | Pipeline canvas is displayed with both nodes |
| 2 | In the node configuration panel, locate the transition/routes field | Transition/routes field is visible in the LLM node panel |
| 3 | Set the transition of the LLM node to point to the Printer node | Transition field is updated to target the Printer node |
| 4 | Verify an edge line appears on canvas connecting LLM Output to Printer Input | Edge is drawn on the canvas between the two nodes |
| 5 | Save and reload — verify edge persists | Edge is present after page reload |

---

## Expected Final State

An edge connecting the LLM node to the Printer node is visible on the canvas and persists after save and reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Edge appears on canvas after setting the transition and persists after save/reload.

**Fail:**
- Any step produces an error or unexpected result.
- Edge does not appear, or is lost after reload.

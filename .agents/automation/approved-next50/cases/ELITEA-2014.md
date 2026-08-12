---
id: ELITEA-2014
title: "Pipeline HITL Node — Configuration and Router Mapping"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2014: Pipeline HITL Node — Configuration and Router Mapping

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that a Human-in-the-loop (HITL) node can be added and fully configured with USER MESSAGE, ROUTER MAPPING (Approve/Edit/Reject routes), and EDIT STATE KEY, and that all configuration persists after save and reload.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline exists with additional nodes to serve as HITL route targets.

---

## Test Data

| Field | Value |
|-------|-------|
| USER MESSAGE Type | Fixed or F-String |
| APPROVE route | target node for approval flow |
| REJECT route | END or rejection node |
| EDIT STATE KEY | state variable name for user feedback |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline and add a Human-in-the-loop node via "Add node" → "Human-in-the-loop" | HITL node appears on the canvas |
| 2 | Click HITL node — verify panel shows: Input, USER MESSAGE (Type+Value), ROUTER MAPPING (APPROVE/EDIT/REJECT routes), EDIT STATE KEY | All listed sections are present in the panel |
| 3 | Set Input combobox with relevant state variables | Input variables are configured |
| 4 | In USER MESSAGE section: set Type (Fixed or F-String) and enter a message value | USER MESSAGE is configured with type and value |
| 5 | In ROUTER MAPPING: APPROVE → select target node; EDIT → select target node; REJECT → select "END" or another node | All three ROUTER MAPPING routes are configured |
| 6 | Set EDIT STATE KEY Value: a state variable name where user-provided feedback text will be stored | EDIT STATE KEY is set |
| 7 | Save pipeline | Pipeline saves without errors |
| 8 | Reload — verify USER MESSAGE, all three ROUTER MAPPING routes, and EDIT STATE KEY persist | All HITL configuration fields are correctly restored after reload |

---

## Expected Final State

The HITL node is fully configured with USER MESSAGE, all three router mapping routes (APPROVE/EDIT/REJECT), and EDIT STATE KEY, all persisting after save and reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- All HITL configuration fields persist correctly after save and reload.

**Fail:**
- Any step produces an error or unexpected result.
- Any HITL configuration field is lost after saving.

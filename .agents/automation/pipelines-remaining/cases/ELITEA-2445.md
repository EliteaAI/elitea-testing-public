---
id: ELITEA-2445
title: "Subgraph Execution — Verify State Flow in Run Details"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2445: Subgraph Execution — Verify State Flow in Run Details

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that Subgraph Execution — Verify State Flow in Run Details. Success is confirmed when verify "completed" badge appears on the run header.

---

## Preconditions

- User is logged in to the Elitea platform.


---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a parent pipeline with 3 nodes: Node_A (Code/LLM) → Agent_Node (calls child pipeline) → Node_C (Code/LLM) → END | Operation completes successfully; state updates and confirmation is shown. |
| 2 | Parent and child share a common state variable (e.g., shared_data: String) | Action completes without error and produces the expected UI state. |
| 3 | Node_A writes to shared_data, child pipeline modifies shared_data, Node_C reads shared_data | Action completes without error and produces the expected UI state. |
| 4 | Execute the parent pipeline | Action completes without error and produces the expected UI state. |
| 5 | Open Run Details — verify timeline shows all three nodes with timestamps in execution order | Target page/section loads successfully. |
| 6 | Click Node_A step — verify shared_data Before is empty/initial, After has Node_A's output | Control responds; expected next state is shown. |
| 7 | Click Agent_Node step — verify shared_data Before shows Node_A's output, After shows child pipeline's modification | Control responds; expected next state is shown. |
| 8 | Click Node_C step — verify shared_data Before shows the child-modified value | Control responds; expected next state is shown. |
| 9 | Verify "Completed" badge appears on the run header | Condition holds as described. |

---

## Expected Final State

Verify "Completed" badge appears on the run header.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Subgraph Execution — Verify State Flow in Run Details.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.

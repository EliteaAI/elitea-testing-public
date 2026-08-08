---
id: ELITEA-2444
title: "Subgraph State Sharing — Non-Common State Isolation"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2444: Subgraph State Sharing — Non-Common State Isolation

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that Subgraph State Sharing — Non-Common State Isolation. Success is confirmed when verify state_3 (child-only, not in parent) does not appear in parent's run details state panel.

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
| 1 | Create a child pipeline with state variables: state_1 (String), state_3 (String) — child modifies both | Operation completes successfully; state updates and confirmation is shown. |
| 2 | Create a parent pipeline with state variables: state_1 (String), state_2 (String) | Operation completes successfully; state updates and confirmation is shown. |
| 3 | In parent, add a node that sets state_1 and state_2, then an Agent node calling the child pipeline | Action completes without error and produces the expected UI state. |
| 4 | Execute the parent pipeline | Action completes without error and produces the expected UI state. |
| 5 | Open Run Details after execution completes | Target page/section loads successfully. |
| 6 | Verify state_1 (common) is updated by child execution — After value differs from Before | Condition holds as described. |
| 7 | Verify state_2 (parent-only, not in child) remains unchanged through the Agent node step | Condition holds as described. |
| 8 | Verify state_3 (child-only, not in parent) does NOT appear in parent's Run Details state panel | Condition holds as described. |

---

## Expected Final State

Verify state_3 (child-only, not in parent) does NOT appear in parent's Run Details state panel.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Subgraph State Sharing — Non-Common State Isolation.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.

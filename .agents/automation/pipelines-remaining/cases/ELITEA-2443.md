---
id: ELITEA-2443
title: "Subgraph State Sharing — Common State Variables"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2443: Subgraph State Sharing — Common State Variables

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that Subgraph State Sharing — Common State Variables. Success is confirmed when verify state after shows state_1 and state_2 updated by child pipeline execution.

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
| 1 | Create a child pipeline with state variables: state_1 (String), state_2 (Number) and a Code/LLM node that modifies both | Operation completes successfully; state updates and confirmation is shown. |
| 2 | Create a parent pipeline with state variables: state_1 (String), state_2 (Number) | Operation completes successfully; state updates and confirmation is shown. |
| 3 | In parent, add a Code/LLM node that sets state_1 to some value, then add an Agent node calling the child pipeline, then connect to END | Action completes without error and produces the expected UI state. |
| 4 | Execute the parent pipeline with input | Action completes without error and produces the expected UI state. |
| 5 | Open Run Details after execution completes | Target page/section loads successfully. |
| 6 | Click on the Agent node step in the timeline | Control responds; expected next state is shown. |
| 7 | Verify state Before shows state_1 with value set by the preceding parent node | Condition holds as described. |
| 8 | Verify state After shows state_1 and state_2 updated by child pipeline execution | Condition holds as described. |
| 9 | Confirm common-named variables (state_1, state_2) shared data between parent and child | Operation completes successfully; state updates and confirmation is shown. |

---

## Expected Final State

Confirm common-named variables (state_1, state_2) shared data between parent and child.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Subgraph State Sharing — Common State Variables.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.

---
id: ELITEA-2451
title: "Run Details — Timeline Steps Display"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2451: Run Details — Timeline Steps Display

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that Run Details — Timeline Steps Display. Success is confirmed when verify total timeline entries match the number of nodes that executed.

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
| 1 | Execute a pipeline with 3+ nodes | Action completes without error and produces the expected UI state. |
| 2 | Open Run Details | Target page/section loads successfully. |
| 3 | Verify each executed node appears as a timeline entry with: | Condition holds as described. |
| 4 | Green dot indicator (successful execution) | Action completes without error and produces the expected UI state. |
| 5 | Node name(on hover) matching the node id from the pipeline | Action completes without error and produces the expected UI state. |
| 6 | Timestamp in HH:MM:SS format | Action completes without error and produces the expected UI state. |
| 7 | Verify nodes appear in execution order (top to bottom = first to last) | Condition holds as described. |
| 8 | Verify total timeline entries match the number of nodes that executed | Condition holds as described. |

---

## Expected Final State

Verify total timeline entries match the number of nodes that executed.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Run Details — Timeline Steps Display.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.

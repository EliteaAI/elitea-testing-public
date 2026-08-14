---
id: ELITEA-2447
title: "Code Node — Return Dict to Modify Multiple State Variables"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2447: Code Node — Return Dict to Modify Multiple State Variables

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that Code Node — Return Dict to Modify Multiple State Variables. Success is confirmed when verify after state shows: summary updated with appended text, count updated with number, tags updated with list value.

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
| 1 | Create a pipeline with state variables: summary (String), count (Number), tags (List) | Operation completes successfully; state updates and confirmation is shown. |
| 2 | Add a Code node with Input including summary | Operation completes successfully; state updates and confirmation is shown. |
| 3 | In Code node script, return a dict updating multiple state vars: data = elitea_state.get('summary', '') {'summary': data + ' [processed]', 'count': len(data.split()), 'tags': ['processed', 'automated']} | Action completes without error and produces the expected UI state. |
| 4 | Set Code node Output combobox to map returned keys to state variables and enable structured output | Action completes without error and produces the expected UI state. |
| 5 | Execute the pipeline | Action completes without error and produces the expected UI state. |
| 6 | Open Run Details, click Code node step | Target page/section loads successfully. |
| 7 | Verify After state shows: summary updated with appended text, count updated with number, tags updated with list value | Condition holds as described. |
| 8 | Confirm multiple state variables updated in single Code node execution | Operation completes successfully; state updates and confirmation is shown. |

---

## Expected Final State

Confirm multiple state variables updated in single Code node execution.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Code Node — Return Dict to Modify Multiple State Variables.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.

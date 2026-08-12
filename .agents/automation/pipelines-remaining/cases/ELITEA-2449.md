---
id: ELITEA-2449
title: "Code Node — Input Filtering (Selective State Access)"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2449: Code Node — Input Filtering (Selective State Access)

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that Code Node — Input Filtering (Selective State Access). Success is confirmed when verify var_c was not accessible (has_var_c = false).

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
| 1 | Create a pipeline with state variables: var_a (String), var_b (String), var_c (String) | Operation completes successfully; state updates and confirmation is shown. |
| 2 | Add nodes that set all three variables before the Code node | Operation completes successfully; state updates and confirmation is shown. |
| 3 | In Code node, set Input combobox to include ONLY var_a and var_b (exclude var_c) | Action completes without error and produces the expected UI state. |
| 4 | In Code node script: available_keys = list(elitea_state.keys()) has_var_c = 'var_c' in elitea_state result = f"Keys: {available_keys}, has_var_c: {has_var_c}" result | Action completes without error and produces the expected UI state. |
| 5 | Open YAML editor — verify Code node shows input: [var_a, var_b] (var_c not listed) | Target page/section loads successfully. |
| 6 | Execute the pipeline | Action completes without error and produces the expected UI state. |
| 7 | Open Run Details, check Code node output | Target page/section loads successfully. |
| 8 | Verify output confirms only var_a and var_b were accessible in elitea_state | Condition holds as described. |
| 9 | Verify var_c was NOT accessible (has_var_c = False) | Condition holds as described. |

---

## Expected Final State

Verify var_c was NOT accessible (has_var_c = False).

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Code Node — Input Filtering (Selective State Access).

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.

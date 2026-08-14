---
id: ELITEA-2448
title: "Code Node — elitea_client Access"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2448: Code Node — elitea_client Access

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that Code Node — elitea_client Access. Success is confirmed when verify code node output state variable contains the user information.

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
| 1 | Create a pipeline with a Code node | Operation completes successfully; state updates and confirmation is shown. |
| 2 | In Code node script, use elitea_client to read user information: user_info = elitea_client.get_user_data() user_info | Action completes without error and produces the expected UI state. |
| 3 | Set Output to a state variable and enable structured output | Action completes without error and produces the expected UI state. |
| 4 | Execute the pipeline | Action completes without error and produces the expected UI state. |
| 5 | Verify Code node executes without errors in Run Details | Condition holds as described. |
| 6 | Verify Code node output state variable contains the user information | Condition holds as described. |

---

## Expected Final State

Verify Code node output state variable contains the user information.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Code Node — elitea_client Access.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.

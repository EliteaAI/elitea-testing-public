---
id: ELITEA-2430
title: "Skill creation — mandatory fields validation (Name and Description)"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-2430: Skill creation — mandatory fields validation (Name and Description)

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that Skill creation — mandatory fields validation (Name and Description). Success is confirmed when click save — verify the skill is created successfully and appears in the skills list.

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
| 1 | Navigate to the Create Skill page | Target page/section loads successfully. |
| 2 | Leave Name empty, fill in Description and Instructions | Action completes without error and produces the expected UI state. |
| 3 | Verify the Save button is inactive/disabled | Condition holds as described. |
| 4 | Fill in Name, clear Description, keep Instructions filled | Field accepts the input and displays the entered value. |
| 5 | Verify the Save button is inactive/disabled | Condition holds as described. |
| 6 | Leave both Name and Description empty | Action completes without error and produces the expected UI state. |
| 7 | Verify the Save button is inactive/disabled | Condition holds as described. |
| 8 | Fill in both Name and Description, keep Instructions filled | Field accepts the input and displays the entered value. |
| 9 | Verify the Save button becomes active/enabled | Condition holds as described. |
| 10 | Click Save — verify the Skill is created successfully and appears in the Skills list | Control responds; expected next state is shown. |

---

## Expected Final State

Click Save — verify the Skill is created successfully and appears in the Skills list.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Skill creation — mandatory fields validation (Name and Description).

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.

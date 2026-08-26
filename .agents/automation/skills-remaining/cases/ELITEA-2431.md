---
id: ELITEA-2431
title: "Edit Skill name, description, and instructions"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-2431: Edit Skill name, description, and instructions

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that Edit Skill name, description, and instructions. Success is confirmed when verify all three updated values are persisted correctly.

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
| 1 | Open an existing Skill | Target page/section loads successfully. |
| 2 | Change the Name, Description, and Instructions to new values | Action completes without error and produces the expected UI state. |
| 3 | Click Save | Control responds; expected next state is shown. |
| 4 | Navigate back to the Skills list and re-open the Skill | Target page/section loads successfully. |
| 5 | Verify all three updated values are persisted correctly | Condition holds as described. |

---

## Expected Final State

Verify all three updated values are persisted correctly.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Edit Skill name, description, and instructions.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.

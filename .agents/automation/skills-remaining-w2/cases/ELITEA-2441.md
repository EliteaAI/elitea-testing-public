---
id: ELITEA-2441
title: "Test panel does not create a new Chat conversation"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-2441: Test panel does not create a new Chat conversation

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that Test panel does not create a new Chat conversation. Success is confirmed when verify no new conversation was created by the skill test execution.

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
| 1 | Note the current number of conversations in the Chat section | Action completes without error and produces the expected UI state. |
| 2 | Open a Skill and run a test via the test panel | Target page/section loads successfully. |
| 3 | Navigate to Chat | Target page/section loads successfully. |
| 4 | Verify no new conversation was created by the Skill test execution | Condition holds as described. |

---

## Expected Final State

Verify no new conversation was created by the Skill test execution.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Test panel does not create a new Chat conversation.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.

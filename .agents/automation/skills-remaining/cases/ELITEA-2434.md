---
id: ELITEA-2434
title: "Multiple tags can be saved on a Skill upon and after creation"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-2434: Multiple tags can be saved on a Skill upon and after creation

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that Multiple tags can be saved on a Skill upon and after creation. Success is confirmed when verify all four tags are persisted.

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
| 1 | Create a new Skill with tags "tag1", "tag2" added before first save (while creation a skill) | Operation completes successfully; state updates and confirmation is shown. |
| 2 | Save the Skill | Operation completes successfully; state updates and confirmation is shown. |
| 3 | Re-open the Skill | Action completes without error and produces the expected UI state. |
| 4 | Add new "tag3", "tag4" tags to the saved skill | Operation completes successfully; state updates and confirmation is shown. |
| 5 | Verify all four tags are persisted | Condition holds as described. |

---

## Expected Final State

Verify all four tags are persisted.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Multiple tags can be saved on a Skill upon and after creation.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.

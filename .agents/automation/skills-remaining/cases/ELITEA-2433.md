---
id: ELITEA-2433
title: "Add, save, and remove a tag on a Skill"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-2433: Add, save, and remove a tag on a Skill

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that Add, save, and remove a tag on a Skill. Success is confirmed when save — verify the tag no longer appears on the card.

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
| 1 | Open an existing Skill with no tags | Target page/section loads successfully. |
| 2 | Add tag "regression-v1" | Operation completes successfully; state updates and confirmation is shown. |
| 3 | Save — verify the tag appears on the Skill card in the list | Operation completes successfully; state updates and confirmation is shown. |
| 4 | Re-open the Skill and remove "regression-v1" | Action completes without error and produces the expected UI state. |
| 5 | Save — verify the tag no longer appears on the card | Operation completes successfully; state updates and confirmation is shown. |

---

## Expected Final State

Save — verify the tag no longer appears on the card.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Add, save, and remove a tag on a Skill.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.

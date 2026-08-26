---
id: ELITEA-1998
title: "Build with AI — Cancel from review step does not create a Skill"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-1998: Build with AI — Cancel from review step does not create a Skill

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that clicking "Cancel" from the Build with AI review/edit step closes the modal and does not create any Skill in the Skills list.

---

## Preconditions

- User is logged in to the Elitea platform with admin or editor role.
- A skill draft has been generated and the review/edit form is displayed.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Generate a skill draft and enter the review/edit form | The review/edit form is displayed with generated values |
| 2 | Click "Cancel" | The modal closes |
| 3 | Verify the modal closes | The modal is no longer visible |
| 4 | Navigate to the Skills list and verify no new Skill was created | No new Skill entry corresponding to the cancelled draft appears in the Skills list |

---

## Expected Final State

The modal is closed and no Skill has been created; the Skills list is unchanged.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Modal closes and no Skill is created in the Skills list.

**Fail:**
- Any step produces an error or unexpected result.
- A Skill is created in the Skills list after cancelling from the review step.

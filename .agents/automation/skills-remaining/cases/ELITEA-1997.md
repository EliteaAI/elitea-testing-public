---
id: ELITEA-1997
title: "Build with AI — Cancel closes the modal without creating a Skill"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-1997: Build with AI — Cancel closes the modal without creating a Skill

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that clicking "Cancel" on the Build with AI modal (from the prompt input step) closes the modal without creating a Skill, leaves the New Skill form empty, and does not add any skill to the Skills list.

---

## Preconditions

- User is logged in to the Elitea platform with admin or editor role.
- The Build with AI modal is open at the prompt input step.

---

## Test Data

| Field | Value |
|-------|-------|
| Natural-language description | Any valid prompt text |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open the Build with AI modal | The modal opens with the prompt input field |
| 2 | Enter a natural-language description | The input field accepts and displays the description |
| 3 | Click "Cancel" | The modal closes |
| 4 | Verify the modal closes | The modal is no longer visible |
| 5 | Verify the New Skill form is still shown with empty fields (no auto-population from the cancelled draft) | The New Skill creation form is displayed with empty fields |
| 6 | Navigate to the Skills list and verify no new Skill was created | No new Skill entry appears in the Skills list |

---

## Expected Final State

The modal is closed, the New Skill form is empty, and no Skill has been created in the project.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Modal closes, New Skill form remains empty, and no Skill is created.

**Fail:**
- Any step produces an error or unexpected result.
- The modal does not close, the form is auto-populated, or a Skill is created unexpectedly.

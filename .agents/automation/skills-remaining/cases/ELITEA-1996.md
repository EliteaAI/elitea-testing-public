---
id: ELITEA-1996
title: "Build with AI — Back to prompt returns to input step without losing the prompt"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-1996: Build with AI — Back to prompt returns to input step without losing the prompt

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that clicking "Back to prompt" from the review/edit step returns the user to the prompt input step, preserves the previously entered natural-language description, and does not leak any draft data into the prompt UI.

---

## Preconditions

- User is logged in to the Elitea platform with admin or editor role.
- A skill draft has been generated and the review/edit form is displayed.

---

## Test Data

| Field | Value |
|-------|-------|
| Natural-language description | The previously entered prompt text |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Generate a skill draft and enter the review/edit form | The review/edit form is displayed with generated values |
| 2 | Click "Back to prompt" | The modal returns to the prompt input step |
| 3 | Verify the modal returns to the prompt input state | The prompt input field and Generate button are visible |
| 4 | Verify the previously entered natural-language description is still present in the input field | The original prompt text is preserved in the input field |
| 5 | Verify no partial draft data leaks into the prompt step UI | No generated Name, Description, or Instructions data is shown in the prompt step |

---

## Expected Final State

The modal is at the prompt input step, the original description is intact in the input field, and no draft data is present in the prompt UI.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The user returns to the prompt step with the original description preserved and no draft data leaked.

**Fail:**
- Any step produces an error or unexpected result.
- The prompt is cleared on return, or draft data (Name, Description, Instructions) leaks into the prompt step.

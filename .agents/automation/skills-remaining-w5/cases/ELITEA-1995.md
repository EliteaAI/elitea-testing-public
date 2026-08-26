---
id: ELITEA-1995
title: "Build with AI — instructions character limit is enforced"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-1995: Build with AI — instructions character limit is enforced

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that the Instructions field in the Build with AI review form enforces a 2500-character limit, showing a validation error and disabling "Create Skill" when exceeded, and clearing the error when trimmed to the allowed length.

---

## Preconditions

- User is logged in to the Elitea platform with admin or editor role.
- A skill draft has been generated and the review/edit form is displayed.

---

## Test Data

| Field | Value |
|-------|-------|
| Over-limit instructions | A string exceeding 2500 characters |
| Exact-limit instructions | A string of exactly 2500 characters |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Generate a skill draft and enter the review form | The review/edit form is displayed |
| 2 | Clear the Instructions field and paste a string exceeding 2500 characters | The text is entered in the Instructions field |
| 3 | Verify a validation message is shown for the Instructions field | A validation error message is displayed for the Instructions field |
| 4 | Verify the "Create Skill" button is inactive/disabled | The "Create Skill" button is disabled or inactive |
| 5 | Trim the instructions to exactly 2500 characters | The Instructions field contains exactly 2500 characters |
| 6 | Verify the validation error clears and "Create Skill" becomes active | The validation error disappears and the "Create Skill" button becomes active |

---

## Expected Final State

The Instructions field enforces the 2500-character limit: validation error shown when exceeded, cleared when trimmed to the limit, and "Create Skill" enabled only when valid.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Validation error appears for over-limit input and clears when trimmed to exactly 2500 characters.

**Fail:**
- Any step produces an error or unexpected result.
- The form accepts instructions exceeding 2500 characters or incorrectly blocks valid instructions.

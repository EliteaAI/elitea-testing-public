---
id: ELITEA-1994
title: "Build with AI — description character limit is enforced"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-1994: Build with AI — description character limit is enforced

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that the Description field in the Build with AI review form enforces a 2304-character limit, showing a validation error and disabling "Create Skill" when exceeded, and clearing the error when trimmed to the allowed length.

---

## Preconditions

- User is logged in to the Elitea platform with admin or editor role.
- A skill draft has been generated and the review/edit form is displayed.

---

## Test Data

| Field | Value |
|-------|-------|
| Over-limit description | A string exceeding 2304 characters |
| Exact-limit description | A string of exactly 2304 characters |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Generate a skill draft and enter the review form | The review/edit form is displayed |
| 2 | Clear the Description field and paste a string exceeding 2304 characters | The text is entered in the Description field |
| 3 | Verify a validation message is shown for the Description field | A validation error message is displayed for the Description field |
| 4 | Verify the "Create Skill" button is inactive/disabled | The "Create Skill" button is disabled or inactive |
| 5 | Trim the description to exactly 2304 characters | The Description field contains exactly 2304 characters |
| 6 | Verify the validation error clears and "Create Skill" becomes active | The validation error disappears and the "Create Skill" button becomes active |

---

## Expected Final State

The Description field enforces the 2304-character limit: validation error shown when exceeded, cleared when trimmed to the limit, and "Create Skill" enabled only when valid.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Validation error appears for over-limit input and clears when trimmed to exactly 2304 characters.

**Fail:**
- Any step produces an error or unexpected result.
- The form accepts a description exceeding 2304 characters or incorrectly blocks a valid description.

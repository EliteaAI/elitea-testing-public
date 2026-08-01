---
id: ELITEA-1993
title: "Build with AI — name field validation on invalid manual edits"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-1993: Build with AI — name field validation on invalid manual edits

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that the Name field in the Build with AI review form enforces naming rules when the user manually edits it, disabling "Create Skill" or showing a validation error for each invalid input.

---

## Preconditions

- User is logged in to the Elitea platform with admin or editor role.
- A skill draft has been generated and the review/edit form is displayed.

---

## Test Data

| Field | Value |
|-------|-------|
| Invalid name (uppercase) | "MySkill" |
| Invalid name (spaces) | "my skill" |
| Invalid name (leading hyphen) | "-my-skill" |
| Invalid name (trailing hyphen) | "my-skill-" |
| Invalid name (exceeds 64 chars) | A string of 65 or more characters |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Generate a skill draft and enter the review form | The review/edit form is displayed |
| 2 | Edit the Name field to a name with uppercase letters (e.g., "MySkill") | The "Create Skill" button is disabled or a validation error is shown |
| 3 | Edit the Name field to a name with spaces (e.g., "my skill") | The "Create Skill" button is disabled or a validation error is shown |
| 4 | Edit the Name field to a name starting with a hyphen (e.g., "-my-skill") | The "Create Skill" button is disabled or a validation error is shown |
| 5 | Edit the Name field to a name ending with a hyphen (e.g., "my-skill-") | The "Create Skill" button is disabled or a validation error is shown |
| 6 | Edit the Name field to a name exceeding 64 characters | The "Create Skill" button is disabled or a validation error is shown |
| 7 | Verify the user cannot create a Skill with any of the above invalid names | Attempting to submit with each invalid name is blocked by validation |

---

## Expected Final State

For every invalid name variant, the form prevents skill creation via a disabled button or a visible validation error, and no Skill is created.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Each invalid name variant triggers a validation error or disables the "Create Skill" button.

**Fail:**
- Any step produces an error or unexpected result.
- The form allows creating a Skill with any of the listed invalid name values.

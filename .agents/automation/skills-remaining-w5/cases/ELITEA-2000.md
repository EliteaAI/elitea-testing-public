---
id: ELITEA-2000
title: "Build with AI — Skill creation failure stays on review step for correction"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-2000: Build with AI — Skill creation failure stays on review step for correction

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that when the Skill creation API fails after clicking "Create Skill" in the Build with AI review form, the user remains on the review/edit step with draft data intact, error messages are displayed, and the user can retry successfully after correcting the issue.

---

## Preconditions

- User is logged in to the Elitea platform with admin or editor role.
- A skill draft has been generated and the review/edit form is displayed.
- A method to simulate or trigger a creation API failure is available (e.g., network throttling, test environment condition).

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Generate a skill draft, review it, and click "Create Skill" | Skill creation is initiated |
| 2 | Simulate or trigger a creation API failure | The API call fails |
| 3 | Verify form-level error messages are displayed using the standard Skill creation error handling | Error messages are visible on the review/edit form |
| 4 | Verify the user remains on the review/edit step (not redirected or kicked back to prompt) | The review/edit form is still displayed |
| 5 | Verify the draft data (Name, Description, Instructions) is still present and editable | All draft fields retain their values and are editable |
| 6 | Correct the issue and click "Create Skill" again — verify the Skill is created successfully | The Skill is created and the user is redirected to the Skill details page |

---

## Expected Final State

After a creation failure, the user stays on the review/edit step with draft data intact. After correcting the issue and retrying, the Skill is created successfully.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Error is shown, user stays on review step, draft is preserved, and retry creates the Skill.

**Fail:**
- Any step produces an error or unexpected result.
- User is redirected away from the review step on failure, or draft data is lost after a creation error.

---
id: ELITEA-2439
title: "Copy Link copies a valid URL pointing to the correct Skill and version"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-2439: Copy Link copies a valid URL pointing to the correct Skill and version

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that Copy Link copies a valid URL pointing to the correct Skill and version. Success is confirmed when verify the skill opens at the correct version without a "not found" error.

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
| 1 | Open a Skill and navigate to a specific version (e.g., "v1") | Target page/section loads successfully. |
| 2 | Click the Share / Copy Link button (in header or overflow menu) | Control responds; expected next state is shown. |
| 3 | Verify a success notification confirms the link was copied | Condition holds as described. |
| 4 | Paste the link into a new browser tab | Field accepts the input and displays the entered value. |
| 5 | Verify the Skill opens at the correct version without a "not found" error | Condition holds as described. |

---

## Expected Final State

Verify the Skill opens at the correct version without a "not found" error.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Copy Link copies a valid URL pointing to the correct Skill and version.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.

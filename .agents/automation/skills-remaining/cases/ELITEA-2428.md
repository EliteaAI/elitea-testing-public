---
id: ELITEA-2428
title: "Skills listing — card view shows correct fields"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-2428: Skills listing — card view shows correct fields

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that Skills listing — card view shows correct fields. Success is confirmed when verify each card shows: skill icon, skill name, description (upon hover), and any assigned tags.

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
| 1 | Create at least one Skill with a name, description, and tags | Operation completes successfully; state updates and confirmation is shown. |
| 2 | Navigate to the Skills list page — confirm Card view is active by default | Target page/section loads successfully. |
| 3 | Verify each card shows: Skill icon, Skill name, description (upon hover), and any assigned tags | Condition holds as described. |

---

## Expected Final State

Verify each card shows: Skill icon, Skill name, description (upon hover), and any assigned tags.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Skills listing — card view shows correct fields.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.

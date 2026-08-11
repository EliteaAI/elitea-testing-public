---
id: ELITEA-1987
title: "Build with AI button is NOT visible for viewer role"
priority: high
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-1987: Build with AI button is NOT visible for viewer role

**Module:** skills · **Priority:** high · **Type:** functional

**Objective:** Verify that the "Build with AI" (Magic Wand) button is not displayed on the New Skill creation screen for users with a viewer role, ensuring that viewers cannot trigger the AI Skill Creator flow.

---

## Preconditions

- User is logged in to the Elitea platform.
- A user account with viewer role exists.
- The Skills page is accessible (or creation is restricted — verify behavior).

---

## Test Data

| Field | Value |
|-------|-------|
| Viewer role user | A valid user account with viewer role |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Log in as a user with viewer role | Login is successful and the user is redirected to the platform home |
| 2 | Navigate to the Skills page and click "+ Skill" (if accessible) | The New Skill creation screen opens (or access is restricted) |
| 3 | Verify the "Build with AI" / Magic Wand button is NOT displayed on the New Skill creation screen | The "Build with AI" / Magic Wand button is absent from the creation screen |
| 4 | Verify there is no way for a viewer to trigger the AI Skill Creator flow | No UI element enables the viewer to access the AI Skill Creator |

---

## Expected Final State

A viewer role user cannot see or interact with the "Build with AI" button, and has no available path to trigger the AI Skill Creator flow.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The "Build with AI" button is not visible and no alternative trigger exists for the viewer role.

**Fail:**
- Any step produces an error or unexpected result.
- The "Build with AI" button is visible or accessible to the viewer role.

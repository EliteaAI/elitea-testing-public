---
id: ELITEA-1986
title: "Build with AI button is visible for admin and editor roles"
priority: high
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-1986: Build with AI button is visible for admin and editor roles

**Module:** skills · **Priority:** high · **Type:** functional

**Objective:** Verify that the "Build with AI" (Magic Wand) button is visible on the New Skill creation screen for both admin and editor roles, ensuring role-based access to the AI Skill Creator feature is correctly granted.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least two user accounts exist: one with admin role and one with editor role.
- The Skills page is accessible.

---

## Test Data

| Field | Value |
|-------|-------|
| Admin role user | A valid user account with admin role |
| Editor role user | A valid user account with editor role |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Log in as a user with admin role | Login is successful and the user is redirected to the platform home |
| 2 | Navigate to the Skills page and click "+ Skill" | The New Skill creation screen opens |
| 3 | Verify the "Build with AI" / Magic Wand button is visible on the New Skill creation screen | The "Build with AI" / Magic Wand button is displayed on the creation screen |
| 4 | Log out and log in as a user with editor role | Login is successful and the user is redirected to the platform home |
| 5 | Navigate to the Skills page and click "+ Skill" | The New Skill creation screen opens |
| 6 | Verify the "Build with AI" / Magic Wand button is visible for the editor role as well | The "Build with AI" / Magic Wand button is displayed for the editor role |

---

## Expected Final State

Both admin and editor role users can see the "Build with AI" / Magic Wand button on the New Skill creation screen, confirming role-based access is correctly configured for these roles.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The "Build with AI" button is visible for both admin and editor roles on the New Skill creation screen.

**Fail:**
- Any step produces an error or unexpected result.
- The "Build with AI" button is not visible for admin or editor role on the New Skill creation screen.

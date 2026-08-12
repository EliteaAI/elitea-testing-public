---
id: ELITEA-2597
title: "Skill Publishing — Token Invalidation and TTL Expiration"
priority: high
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:publishing, feat:security]
requirements: []
---

# ELITEA-2597: Skill Publishing — Token Invalidation and TTL Expiration

**Module:** skills · **Priority:** high · **Type:** functional

**Objective:** Verify that the publishing validation token is invalidated when the skill is modified after validation, and that the token expires after 5 minutes (TTL).

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- A project exists and is accessible.
- The Skills section is available in the project.
- User has publishing permissions.
- Two browser tabs/windows available for testing.

---

## Test Data

| Field | Value |
|-------|-------|
| Skill Name | `token-test-skill` |
| Skill Description | Valid description with sufficient content (100+ characters) for passing validation |
| Skill Instructions | Valid instructions with sufficient content (100+ characters) for passing validation |
| Modified Instructions | Updated instructions text that differs from original |
| Token TTL | 5 minutes |

---

## Steps

### Part A: Token Invalidation on Modification

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a skill with valid content that will pass validation | Skill is created and saved successfully |
| 2 | Open the publish wizard and proceed to Validation step | Validation passes successfully |
| 3 | Keep the wizard open, open the same skill in a new browser tab | Skill editor opens in second tab |
| 4 | In the second tab, modify the skill instructions and save | Skill is updated successfully |
| 5 | Return to the first tab with the publish wizard open | Wizard is still on the post-validation step |
| 6 | Attempt to proceed with publishing (click Next/Publish) | Error message indicates token is invalid due to skill modification |
| 7 | Verify user must restart the validation process | User is prompted to re-validate or wizard resets to validation step |

### Part B: Token TTL Expiration

| # | Action | Expected Result |
|---|--------|-----------------|
| 8 | Create another skill with valid content (or use existing) | Skill is ready for publishing |
| 9 | Open the publish wizard and proceed to Validation step | Validation passes successfully |
| 10 | Note the current time and wait for more than 5 minutes | Timer exceeds 5-minute TTL |
| 11 | Attempt to proceed with publishing after 5+ minutes | Error message indicates validation token has expired |
| 12 | Verify user must re-validate the skill | User is prompted to re-validate or wizard resets |

---

## Expected Final State

The publishing security mechanism correctly prevents publishing when:
1. The skill content has been modified after validation (token invalidation)
2. The validation token has expired after 5 minutes (TTL)

In both cases, the user must re-run validation before publishing.

---

## Pass/Fail Criteria

**Pass:**
- Token invalidation triggers when skill is modified after validation.
- Token expiration triggers after 5 minutes.
- Clear error messages are shown in both scenarios.
- User is required to re-validate before publishing.

**Fail:**
- Publishing succeeds despite skill modification after validation.
- Publishing succeeds after token TTL expires.
- Error messages are missing or unclear.
- User can bypass the re-validation requirement.

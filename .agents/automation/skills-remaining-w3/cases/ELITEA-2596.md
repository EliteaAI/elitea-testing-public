---
id: ELITEA-2596
title: "Skill Publishing — AI Validation Blockers"
priority: high
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:publishing, feat:validation]
requirements: []
---

# ELITEA-2596: Skill Publishing — AI Validation Blockers

**Module:** skills · **Priority:** high · **Type:** functional

**Objective:** Verify that AI validation correctly blocks publishing for skills with short content, placeholder text, and hardcoded secrets/API keys. Each validation issue should result in a FAIL status that prevents publishing.

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- A project exists and is accessible.
- The Skills section is available in the project.
- User has publishing permissions.

---

## Test Data

| Field | Value |
|-------|-------|
| Short Content Skill | Name: `short-skill`, Description: "Short", Instructions: "Do it" |
| Placeholder Skill | Name: `placeholder-skill`, Description: "[replace this with actual description]", Instructions: "TODO: add instructions" |
| Secrets Skill | Name: `secrets-skill`, Description: "Valid description text here", Instructions: "Use API key: sk-1234567890abcdef and password: MySecretPass123" |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a skill with short content (description and instructions under 100 chars each) | Skill is created successfully |
| 2 | Attempt to publish the short content skill — proceed through wizard to Validation step | Validation runs and returns FAIL status |
| 3 | Verify the validation error message indicates content is too short | Error message references minimum content length requirement |
| 4 | Verify the "Next" or "Publish" button is disabled | User cannot proceed past validation step |
| 5 | Create a second skill with placeholder text (`[replace this]`, `TODO`) in description or instructions | Skill is created successfully |
| 6 | Attempt to publish the placeholder skill — proceed through wizard to Validation step | Validation runs and returns FAIL status |
| 7 | Verify the validation error message indicates placeholder text detected | Error message references placeholder patterns found |
| 8 | Verify the "Next" or "Publish" button is disabled | User cannot proceed past validation step |
| 9 | Create a third skill with hardcoded secrets/API keys in instructions | Skill is created successfully |
| 10 | Attempt to publish the secrets skill — proceed through wizard to Validation step | Validation runs and returns FAIL status |
| 11 | Verify the validation error message indicates secrets/credentials detected | Error message references sensitive data found |
| 12 | Verify the "Next" or "Publish" button is disabled | User cannot proceed past validation step |

---

## Expected Final State

All three validation scenarios result in FAIL status that blocks publishing. The user receives clear error messages explaining why each skill cannot be published.

---

## Pass/Fail Criteria

**Pass:**
- All validation checks correctly identify the issues.
- FAIL status is shown for each problematic skill.
- Publishing is blocked in all three cases.
- Error messages are clear and actionable.

**Fail:**
- Any validation check passes when it should fail.
- User is able to proceed to publish despite validation failures.
- Error messages are missing, unclear, or incorrect.

---
id: ELITEA-2598
title: "Skill Publishing — WARN Status Allows Publishing with Warnings"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:publishing, feat:validation]
requirements: []
---

# ELITEA-2598: Skill Publishing — WARN Status Allows Publishing with Warnings

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that skills with non-critical issues (generic names, missing custom icon) receive WARN status during validation but can still be published. Users should see warnings but not be blocked from proceeding.

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
| Generic Name Skill | Name: `skill`, Description: Valid 100+ char description, Instructions: Valid 100+ char instructions |
| No Icon Skill | Name: `detailed-task-helper`, Description: Valid content, Instructions: Valid content, Icon: None (default) |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a skill with a generic/non-descriptive name (e.g., "skill", "test", "helper") but valid description and instructions | Skill is created successfully |
| 2 | Ensure the skill does NOT have a custom icon (uses default icon) | Skill shows default icon |
| 3 | Open the publish wizard and proceed to Validation step | Validation runs and completes |
| 4 | Verify validation returns WARN status (not FAIL) | Status shows as WARNING, not FAIL |
| 5 | Verify warning message mentions generic/non-descriptive name | Warning text references the name being too generic |
| 6 | Verify warning message mentions missing custom icon | Warning text references no custom icon uploaded |
| 7 | Verify the "Next" or "Publish" button is still ENABLED | User can proceed despite warnings |
| 8 | Proceed to the Publishing step | User advances to final publishing step |
| 9 | Complete the publishing process | Skill is published successfully despite warnings |
| 10 | Verify the skill appears in the Catalog | Published skill is visible in Skills Studio/Catalog |

---

## Expected Final State

Skills with WARN-level issues can be published successfully. Users are informed of potential improvements (better name, custom icon) but are not blocked from publishing.

---

## Pass/Fail Criteria

**Pass:**
- Validation correctly identifies generic name and missing icon as warnings.
- WARN status is shown (not FAIL).
- User can proceed and complete publishing.
- Warning messages are clear and informative.

**Fail:**
- WARN issues incorrectly block publishing (treated as FAIL).
- Warning messages are missing or unclear.
- User cannot proceed despite meeting minimum requirements.

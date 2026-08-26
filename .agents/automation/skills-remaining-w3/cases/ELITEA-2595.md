---
id: ELITEA-2595
title: "Skill Publishing Wizard — Happy Path"
priority: high
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:publishing]
requirements: []
---

# ELITEA-2595: Skill Publishing Wizard — Happy Path

**Module:** skills · **Priority:** high · **Type:** functional

**Objective:** Verify that a skill with valid content can be successfully published through the 3-step publish wizard (Preparation → Validation → Publishing) and appears in the Skills Studio/Catalog.

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
| Skill Name | `test-publish-skill` |
| Skill Description | A detailed description for testing the publishing workflow (min 100 characters to pass validation) |
| Skill Instructions | Comprehensive instructions that explain the skill behavior clearly (min 100 characters) |
| Version Name | `v1.0` |
| Category | Any valid category from dropdown |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to Skills section and create a new skill with valid name, description (100+ chars), and instructions (100+ chars) | Skill is created and saved successfully |
| 2 | Open the skill and click the "Publish" button | Publish wizard modal opens showing Step 1: Preparation |
| 3 | Enter a valid version name and select a category from the dropdown | Fields accept input, no validation errors shown |
| 4 | Accept the Publishing Terms checkbox | Checkbox is checked, Next button becomes enabled |
| 5 | Click "Next" to proceed to Step 2: Validation | Validation step loads, AI validation runs automatically |
| 6 | Wait for validation to complete | Validation passes with no FAIL blockers (may show warnings) |
| 7 | Click "Next" to proceed to Step 3: Publishing | Publishing confirmation step is displayed |
| 8 | Click "Publish" to complete the process | Publishing completes successfully, success message shown |
| 9 | Navigate to Skills Studio/Catalog | Published skill appears in the catalog with correct version |
| 10 | Verify the published skill details | Name, description, version, and category match the input values |

---

## Expected Final State

The skill is successfully published and visible in the Skills Studio/Catalog. The published version is accessible to other users according to the visibility settings.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The 3-step wizard completes successfully.
- The skill appears in the Catalog with correct metadata.

**Fail:**
- Any step produces an error or unexpected result.
- Validation fails despite valid content.
- The skill does not appear in the Catalog after publishing.

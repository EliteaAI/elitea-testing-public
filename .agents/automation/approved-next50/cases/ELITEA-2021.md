---
id: ELITEA-2021
title: "Create Pipeline — Full Details"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2021: Create Pipeline — Full Details

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that a pipeline can be created with all available fields populated (name, description, tags, toolkit, welcome message, chat starter, step limit, editor notes) and that all fields persist correctly after saving and reloading.

---

## Preconditions

- User is logged in to the Elitea platform.
- An existing toolkit is available in the project.

---

## Test Data

| Field | Value |
|-------|-------|
| Pipeline name | FullDetailsPipe |
| Description | Pipeline with all fields populated |
| Tag | automation |
| Welcome message | Welcome to the pipeline |
| Chat starter | Run analysis |
| Step limit | 50 |
| Editor notes | Test pipeline for automation |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to Pipelines section via sidebar | Pipelines section loads |
| 2 | Click "+" button to create a new pipeline | New pipeline tab opens |
| 3 | Fill Name: "FullDetailsPipe" | Name field is populated |
| 4 | Fill Description: "Pipeline with all fields populated" | Description field is populated |
| 5 | Add tag "automation" in the Tags combobox | "automation" tag is added |
| 6 | In the Tools section, click "+ Toolkit" button and attach an existing toolkit | Toolkit appears in the Tools section |
| 7 | Fill Welcome message: "Welcome to the pipeline" | Welcome message field is populated |
| 8 | Add a Chat starter with text: "Run analysis" | Chat starter "Run analysis" is added |
| 9 | Set Step limit to "50" in Advanced section | Step limit field shows "50" |
| 10 | Add Editor Notes: "Test pipeline for automation" | Editor notes field is populated |
| 11 | Click "Save" | Pipeline saves without errors |
| 12 | Reload page and verify all fields persist: Name, Description, Tag "automation", attached toolkit, welcome message, chat starter "Run analysis", step limit "50", editor notes | All fields are correctly restored after reload |

---

## Expected Final State

All pipeline fields persist correctly after save and reload: Name, Description, Tag "automation", attached toolkit, welcome message "Welcome to the pipeline", chat starter "Run analysis", step limit "50", and editor notes.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- All specified fields persist correctly after save and reload.

**Fail:**
- Any step produces an error or unexpected result.
- Any field is missing or has incorrect value after reload.

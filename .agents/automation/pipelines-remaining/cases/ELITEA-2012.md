---
id: ELITEA-2012
title: "Pipeline Import via File"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2012: Pipeline Import via File

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that a pipeline exported as a file can be re-imported to create a new pipeline with a unique ID while preserving all original configuration including name, description, chat starters, and node structure.

---

## Preconditions

- User is logged in to the Elitea platform.
- A project exists with access to the Pipelines feature.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline with name, description, chat starters and configure a LLM node | Pipeline is created with all specified fields |
| 2 | Export the pipeline via three-dot menu → Export | JSON file downloads to local machine |
| 3 | Delete the original pipeline | Pipeline is deleted and no longer appears in the list |
| 4 | Navigate to Pipelines dashboard → Import | Import option is available on the dashboard |
| 5 | Upload the exported file | File is uploaded successfully |
| 6 | Verify imported pipeline has a new unique ID | Pipeline ID is different from the original |
| 7 | Verify name, description, chat starters, and node structure are preserved | All fields match the original pipeline's configuration |
| 8 | Verify pipeline can be executed after import | Pipeline executes without errors |

---

## Expected Final State

The imported pipeline is created with a new unique ID and all original configuration (name, description, chat starters, node structure) preserved. The pipeline is functional and can be executed.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Imported pipeline has a new unique ID, preserves all original configuration, and is executable.

**Fail:**
- Any step produces an error or unexpected result.
- Import fails, configuration is lost, or the pipeline cannot be executed after import.

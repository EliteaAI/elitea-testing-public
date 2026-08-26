---
id: ELITEA-2011
title: "Pipeline Run History — View Executions"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2011: Pipeline Run History — View Executions

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that the pipeline run history panel correctly displays past execution entries and allows drilling into individual execution details.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with an LLM node connected to END exists and has been executed at least 2-3 times.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline with LLM node connected to END | Pipeline is created and ready for execution |
| 2 | Execute the pipeline 2-3 times with different messages | Pipeline executions complete successfully |
| 3 | Click the "view run history" icon button | Run history panel opens |
| 4 | Verify run history panel opens | Panel is visible with execution entries |
| 5 | Verify at least 2-3 execution entries are listed | Multiple execution entries are displayed |
| 6 | Click on one entry — verify it shows the message and response details | Execution details (input message and response) are displayed for the selected entry |

---

## Expected Final State

The run history panel is accessible and shows all past executions. Clicking on an individual entry displays the full message and response details for that execution.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Run history panel opens, shows 2-3+ execution entries, and clicking an entry reveals its details.

**Fail:**
- Any step produces an error or unexpected result.
- Run history panel does not open, shows no entries, or execution details are missing.

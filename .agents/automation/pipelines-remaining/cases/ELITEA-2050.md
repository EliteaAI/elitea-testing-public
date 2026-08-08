---
id: ELITEA-2050
title: "Pipeline — Export"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2050: Pipeline — Export

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that a pipeline with nodes can be exported as a JSON file containing the full pipeline structure including name, nodes, and state.

---

## Preconditions

- User is logged in to the Elitea platform.
- An existing pipeline with nodes is open.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open an existing pipeline with nodes | Pipeline is loaded in the editor |
| 2 | Click three-dot menu → "Export" | Export action is triggered |
| 3 | Verify a JSON file download starts | Browser initiates a file download |
| 4 | Verify downloaded file contains pipeline structure (name, nodes, state, etc.) | JSON file content includes pipeline definition fields |

---

## Expected Final State

The pipeline is exported as a downloadable JSON file containing the complete pipeline structure (name, nodes, state, and other configuration fields).

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- A JSON file is downloaded and contains the pipeline structure.

**Fail:**
- Any step produces an error or unexpected result.
- No file is downloaded, or the file does not contain valid pipeline structure.

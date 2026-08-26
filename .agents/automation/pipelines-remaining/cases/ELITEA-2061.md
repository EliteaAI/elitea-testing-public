---
id: ELITEA-2061
title: "Pipeline — Node Duplicate via Node Menu"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2061: Pipeline — Node Duplicate via Node Menu

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that nodes of the same type are named with incrementing numbers (e.g., "LLM 1", "LLM 2") when added to the pipeline, confirming the auto-naming behavior for multiple nodes of the same type.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline is open in Flow view.

---

## Test Data

| Field | Value |
|-------|-------|
| Node type | LLM (or any repeatable type) |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline with a configured node | Pipeline is open |
| 2 | Select a node on canvas of any type (e.g., LLM, Code, Printer) | Node is selected |
| 3 | Verify the added node name is "<NodeType> number" (e.g., "LLM 1", "Code 2") | Node name follows the incremental naming pattern |
| 4 | Select another node of the same type | Second node of the same type is added |
| 5 | Verify the node name increments (e.g., "LLM 2", "Code 3") | New node name is incremented from the previous |

---

## Expected Final State

Multiple nodes of the same type are named with incrementing numbers, confirming the auto-naming convention (e.g., "LLM 1", "LLM 2", "LLM 3").

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Nodes of the same type have incrementally numbered names.

**Fail:**
- Any step produces an error or unexpected result.
- Node names do not follow the incremental naming pattern.

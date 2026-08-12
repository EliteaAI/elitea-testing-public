---
id: ELITEA-2016
title: "Pipeline with Multiple Branches (Decision Node)"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2016: Pipeline with Multiple Branches (Decision Node)

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that a Decision node correctly routes execution to the appropriate branch node based on the input content, and that all edges and DECISION OUTPUTS persist after save and reload.

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
| 1 | Create a pipeline with a Decision node | Decision node appears on the canvas |
| 2 | Add three nodes (e.g., LLM or Code) to serve as branch targets | Three branch nodes are added to the canvas |
| 3 | In Decision node: set Description with classification prompt, add all three node names to DECISION OUTPUTS | Decision node is configured with classification prompt and all branch outputs |
| 4 | Connect Decision → each branch node → END (edges from Output and Default output handles) | Edges connect Decision to all branch nodes and each branch to END |
| 5 | Save and verify all edges and DECISION OUTPUTS persist after reload | All edges and DECISION OUTPUTS are present after page reload |
| 6 | Execute with input matching one category — verify correct branch responds | Execution routes to the correct branch node and returns the expected response |

---

## Expected Final State

The Decision node correctly classifies input and routes execution to the appropriate branch. All canvas edges and DECISION OUTPUTS configuration persist after save and reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Decision node routes to the correct branch, and all configuration persists after reload.

**Fail:**
- Any step produces an error or unexpected result.
- Wrong branch is selected, edges are lost after reload, or DECISION OUTPUTS are not persisted.

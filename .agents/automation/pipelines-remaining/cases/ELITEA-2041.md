---
id: ELITEA-2041
title: "Pipeline — Trigger Shown on Entry Point Node Only"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2041: Pipeline — Trigger Shown on Entry Point Node Only

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the Trigger dropdown is only visible in the configuration panel of the entry point node, and not on any other node in the pipeline.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with multiple nodes (e.g., LLM → Code → Printer) exists where the LLM node is the entry point.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline with multiple nodes (e.g., LLM → Code → Printer) | Pipeline canvas is displayed with all nodes |
| 2 | Click on the entry point node (first node, marked with "Input" badge at top) | Entry point node configuration panel opens |
| 3 | Verify "Trigger" dropdown is visible at the top of node config panel | Trigger dropdown is present |
| 4 | Click on a non-entry-point node (e.g., Code node) | Code node configuration panel opens |
| 5 | Verify "Trigger" dropdown is NOT shown for non-entry nodes | Trigger dropdown is absent from non-entry node panels |
| 6 | Verify Information section in left panel shows "Trigger: Chat Message" matching entry node's selection | Information section correctly displays the active trigger type |

---

## Expected Final State

The Trigger dropdown is exclusive to the entry point node's configuration panel. Non-entry nodes do not show a Trigger dropdown. The Information section reflects the current trigger type.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Trigger dropdown is only on the entry point node, absent on all others, and Information section matches.

**Fail:**
- Any step produces an error or unexpected result.
- Trigger dropdown appears on non-entry nodes, or is missing from the entry node.

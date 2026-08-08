---
id: ELITEA-2029
title: "Pipeline — Flow to YAML Sync"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2029: Pipeline — Flow to YAML Sync

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that nodes added in the Flow (visual) editor are immediately reflected in the YAML view, confirming bidirectional synchronization between the two editing modes.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with existing nodes exists.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline in "Flow" view | Pipeline canvas is displayed in Flow view |
| 2 | Add a new LLM node via "Add node" button | New LLM node appears on the canvas |
| 3 | Switch to "Yaml" view | YAML editor is displayed |
| 4 | Verify the new node appears in the YAML definition | YAML content includes the newly added LLM node |
| 5 | Switch back to "Flow" view — verify node is still present on canvas | LLM node remains on the canvas in Flow view |

---

## Expected Final State

A node added in Flow view is immediately reflected in the YAML definition, confirming that the Flow editor and YAML editor are synchronized.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The new LLM node added in Flow view appears in YAML definition and remains in Flow view.

**Fail:**
- Any step produces an error or unexpected result.
- New node does not appear in YAML, or is lost when switching back to Flow view.

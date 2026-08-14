---
id: ELITEA-2018
title: "Pipeline Canvas — Delete Node"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2018: Pipeline Canvas — Delete Node

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that a node can be deleted from the pipeline canvas, that its connected edges are automatically removed, and that the deletion persists after saving.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline exists with at least 3 nodes connected by edges (e.g., LLM → Code → END).

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline with LLM → Code → END (3 nodes + edges) | Pipeline is created with all three nodes and connecting edges |
| 2 | Select the Code node on canvas | Code node is selected/highlighted |
| 3 | Delete it (press Delete key or use node menu → Delete) | Delete action is triggered |
| 4 | Verify Code node is removed from canvas | Code node no longer appears on the canvas |
| 5 | Verify edges connected to Code node are also removed | All edges connecting to or from Code node are gone |
| 6 | Verify LLM and END nodes remain | LLM and END nodes are still present on canvas |
| 7 | Save — verify deletion persists after reload | Canvas shows LLM and END nodes only after reload; Code node is gone |

---

## Expected Final State

The Code node and all its connected edges are permanently removed from the pipeline. LLM and END nodes remain. The deletion persists after save and reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Code node and its edges are removed; LLM and END remain; deletion persists after reload.

**Fail:**
- Any step produces an error or unexpected result.
- Node is not deleted, edges remain after deletion, or the change is not saved.

---
id: ELITEA-2064
title: "Pipeline — Attach Pipeline as Tool"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2064: Pipeline — Attach Pipeline as Tool

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that another pipeline can be attached as a tool to a pipeline, and that the attachment persists after save and reload.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least two pipelines (Pipeline A and Pipeline B) exist in the project.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline (Pipeline A) | Pipeline A is loaded in the editor |
| 2 | In the left panel Tools section, click "+ Pipeline" button | Pipeline picker opens |
| 3 | From the pipeline picker, select another pipeline (Pipeline B) | Pipeline B is selected |
| 4 | Verify Pipeline B appears in the Tools list under Pipeline sub-tab | Pipeline B is listed under the Pipeline sub-tab in Tools |
| 5 | Save Pipeline A | Pipeline A saves without errors |
| 6 | Reload — verify Pipeline B is still attached as a tool | Pipeline B remains in the Tools list after reload |

---

## Expected Final State

Pipeline B is successfully attached as a tool to Pipeline A and the attachment persists after save and reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Pipeline B is attached and persists in the Tools list after reload.

**Fail:**
- Any step produces an error or unexpected result.
- Pipeline B is not attached, or the attachment is lost after reload.

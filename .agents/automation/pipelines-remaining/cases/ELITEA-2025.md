---
id: ELITEA-2025
title: "Pipeline Dashboard — Pin to Top"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2025: Pipeline Dashboard — Pin to Top

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that a pipeline can be pinned to the top of the Pipelines dashboard list and unpinned to return to its original position.

---

## Preconditions

- User is logged in to the Elitea platform.
- The Pipelines dashboard is in card view with multiple pipelines, including one not currently pinned.

---

## Test Data

| Field | Value |
|-------|-------|
| Pipeline name | ImageAnalyzer (or any unpinned pipeline) |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to Pipelines dashboard in card view | Dashboard loads with pipelines in card view |
| 2 | Find a pipeline card that is NOT pinned (e.g., "ImageAnalyzer") | An unpinned pipeline card is identified |
| 3 | Click the "Pin to top" button on that card | Pipeline is pinned to the top of the list |
| 4 | Verify the pinned pipeline moves to the top of the list | The pipeline card now appears first in the dashboard |
| 5 | Click "Pin to top" again (unpin) | Pipeline is unpinned |
| 6 | Verify pipeline returns to its original position (or is no longer at top) | The pipeline is no longer at the top of the list |

---

## Expected Final State

The Pin to Top feature correctly moves a pipeline to the top of the dashboard list when pinned, and removes it from the top when unpinned.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Pipeline moves to top when pinned and leaves the top position when unpinned.

**Fail:**
- Any step produces an error or unexpected result.
- Pipeline does not move to top when pinned, or does not return when unpinned.

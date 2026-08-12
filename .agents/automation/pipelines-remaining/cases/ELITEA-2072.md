---
id: ELITEA-2072
title: "Pipeline — Collapse Left Panel"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2072: Pipeline — Collapse Left Panel

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the left configuration panel can be collapsed to give more space to the canvas/chat area, and can be expanded again to restore all configuration sections.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline is open in editor view with the left configuration panel visible.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline in editor view | Pipeline loads with left configuration panel fully visible |
| 2 | Locate the collapse button at top of left configuration panel | Collapse button is visible |
| 3 | Click the collapse button | Left panel collapses |
| 4 | Verify left panel collapses (configuration sections hidden) | Left panel is minimized/hidden; configuration sections are no longer visible |
| 5 | Verify canvas/chat area expands to fill available space | Canvas or chat area takes up more horizontal space |
| 6 | Click expand button to restore left panel | Left panel expands |
| 7 | Verify configuration sections are visible again | All configuration sections (Tools, Advanced, etc.) are restored |

---

## Expected Final State

The left panel collapse/expand toggle works correctly: collapsing hides configuration sections and expands the workspace, while expanding restores all configuration sections.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Collapse hides left panel and expands workspace; expand restores configuration sections.

**Fail:**
- Any step produces an error or unexpected result.
- Collapse/expand button is missing or does not change the panel state.

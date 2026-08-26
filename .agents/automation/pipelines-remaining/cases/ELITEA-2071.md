---
id: ELITEA-2071
title: "Pipeline — Fullscreen Chat Mode"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2071: Pipeline — Fullscreen Chat Mode

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the chat panel can be expanded to fullscreen mode, that pipeline execution works in fullscreen, and that the split view is restored when exiting fullscreen.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline is open with both the configuration panel and chat panel visible.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline | Pipeline loads with left configuration panel and right chat/canvas visible |
| 2 | In the chat panel header (right side), locate a fullscreen/expand button | Fullscreen button is visible |
| 3 | Click the fullscreen button | Chat panel expands |
| 4 | Verify chat panel expands to full screen (left configuration panel hides) | Left panel is hidden; chat fills the available space |
| 5 | Verify pipeline execution still works in fullscreen mode | Pipeline can be executed and responds in fullscreen chat |
| 6 | Click exit fullscreen button | Fullscreen mode exits |
| 7 | Verify returns to split view (left panel + right chat/canvas) | Left configuration panel is restored alongside the chat panel |

---

## Expected Final State

The fullscreen chat mode expands the chat to full width (hiding the left panel), allows pipeline execution, and correctly returns to split view when exited.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Fullscreen mode expands chat, execution works in fullscreen, and split view is restored on exit.

**Fail:**
- Any step produces an error or unexpected result.
- Fullscreen mode does not work, execution fails in fullscreen, or split view is not restored.

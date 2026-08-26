---
id: ELITEA-2057
title: "Pipeline — Canvas Control Panel"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2057: Pipeline — Canvas Control Panel

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that all canvas control panel buttons (Zoom In, Zoom Out, Fit View, Toggle Interactivity, Toggle cards size, Auto-arrange) function correctly.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with multiple nodes is open in Flow view.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline with nodes in Flow view | Pipeline canvas is displayed |
| 2 | Locate the Control Panel at bottom-right of canvas with buttons: Zoom In, Zoom Out, Fit View, Toggle Interactivity, Toggle cards size, Auto-arrange | All control panel buttons are visible |
| 3 | Click "Zoom In" — verify canvas zooms in | Canvas zoom level increases |
| 4 | Click "Zoom Out" — verify canvas zooms out | Canvas zoom level decreases |
| 5 | Click "Fit View" — verify all nodes fit within viewport | All nodes are visible within the canvas viewport |
| 6 | Click "Toggle Interactivity" — verify nodes become non-draggable (or re-enable) | Node dragging behavior toggles |
| 7 | Click "Toggle cards size" — verify node cards change between compact/expanded view | Node card size changes |
| 8 | Click "Auto-arrange" — verify nodes reposition to an auto-arranged layout | Nodes are repositioned in an organized layout |

---

## Expected Final State

All canvas control panel buttons function correctly: Zoom In/Out adjust zoom level, Fit View shows all nodes, Toggle Interactivity locks/unlocks dragging, Toggle cards size changes node card appearance, Auto-arrange repositions nodes.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Each control panel button produces the expected visual change on the canvas.

**Fail:**
- Any step produces an error or unexpected result.
- Any control panel button is missing or non-functional.

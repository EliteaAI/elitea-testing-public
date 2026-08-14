---
id: ELITEA-2049
title: "Pipeline — Three-dot Menu Actions"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2049: Pipeline — Three-dot Menu Actions

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the pipeline three-dot menu opens and displays all expected action options, and that the Copy link action successfully copies the pipeline link to clipboard.

---

## Preconditions

- User is logged in to the Elitea platform.
- An existing pipeline is open.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open an existing pipeline | Pipeline is loaded in the editor |
| 2 | Click the three-dot menu button (next to Save/Discard area) | Three-dot menu opens |
| 3 | Verify menu opens with options including: Export, Fork (may be disabled for own pipelines), Copy link, Pin to top, Delete, Delete version (when on non-base version) | All listed options are visible in the menu |
| 4 | Click "Copy link" | Copy link action is triggered |
| 5 | Verify link is copied to clipboard (toast notification or clipboard content) | Toast notification appears or clipboard contains the pipeline URL |
| 6 | Close menu | Menu closes |

---

## Expected Final State

The three-dot menu displays all expected actions. The Copy link function successfully copies the pipeline URL to clipboard with user feedback.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Menu shows all expected options; Copy link copies to clipboard with feedback.

**Fail:**
- Any step produces an error or unexpected result.
- Menu options are missing, or Copy link does not work.

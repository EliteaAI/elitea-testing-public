---
id: ELITEA-2066
title: "Pipeline — Modules Section"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2066: Pipeline — Modules Section

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the Modules section contains the Attachments toggle and that toggling it enables/disables the Attach Files button in the chat panel.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline is open for editing.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline | Pipeline is loaded in the editor |
| 2 | In Tools section, scroll to "MODULES" area | MODULES section is visible |
| 3 | Verify "Attachments" module is listed with an on/off switch | Attachments toggle is visible |
| 4 | Toggle "Attachments" switch to enabled | Attachments is enabled |
| 5 | Save pipeline | Pipeline saves without errors |
| 6 | Verify in chat panel that "Attach Files" button becomes active (no longer disabled) | Attach Files button is enabled in the chat panel |
| 7 | Toggle "Attachments" switch to disabled | Attachments is disabled |
| 8 | Save — verify "Attach Files" button returns to disabled state | Attach Files button is disabled in the chat panel |

---

## Expected Final State

The Attachments module toggle correctly enables and disables the Attach Files button in the chat panel. The state persists after save.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Enabling Attachments activates the Attach Files button; disabling it deactivates the button.

**Fail:**
- Any step produces an error or unexpected result.
- Attachments toggle does not affect the Attach Files button state.

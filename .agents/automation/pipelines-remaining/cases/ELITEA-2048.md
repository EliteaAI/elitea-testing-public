---
id: ELITEA-2048
title: "Pipeline — Unsaved Changes and Discard"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2048: Pipeline — Unsaved Changes and Discard

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that modifying a pipeline enables the Save and Discard buttons, and that clicking Discard reverts all unsaved changes and returns both buttons to the disabled state.

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
| 2 | Verify "Save" and "Discard" buttons are initially disabled | Both buttons are disabled/inactive |
| 3 | Modify the pipeline name (e.g., append " modified") | Name field shows the modified value |
| 4 | Verify "Save" button becomes enabled | Save button is active/enabled |
| 5 | Verify "Discard" button becomes enabled | Discard button is active/enabled |
| 6 | Click "Discard" button | Discard action is triggered |
| 7 | Verify pipeline name reverts to original value | Name field shows the original pipeline name |
| 8 | Verify "Save" and "Discard" return to disabled state | Both buttons are disabled again |

---

## Expected Final State

After discarding, all unsaved changes are reverted and the pipeline returns to its last saved state. Save and Discard buttons return to the disabled state.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Modifications enable Save/Discard; Discard reverts changes and disables both buttons.

**Fail:**
- Any step produces an error or unexpected result.
- Buttons don't enable on modification, Discard doesn't revert changes, or buttons remain enabled after discard.

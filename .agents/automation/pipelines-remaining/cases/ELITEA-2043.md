---
id: ELITEA-2043
title: "Pipeline — State Panel with Attachments Module"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2043: Pipeline — State Panel with Attachments Module

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that enabling the Attachments module automatically adds the "input_attachments" immutable variable to the State panel, and that disabling it removes the variable.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline is open in Flow view.

---

## Test Data

| Field | Value |
|-------|-------|
| Auto-added variable | input_attachments (list) |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline and enable "Attachments" toggle in MODULES section (left panel) | Attachments module is enabled |
| 2 | Click "State" button on canvas | STATE panel opens |
| 3 | Verify STATE panel shows three immutable variables: "input" (str), "messages" (list), "input_attachments" (list) | All three immutable variables are present |
| 4 | Verify "input_attachments" was auto-added when Attachments was enabled | "input_attachments" has no delete button (immutable) |
| 5 | Disable "Attachments" toggle in MODULES | Attachments module is disabled |
| 6 | Verify "input_attachments" is removed from STATE panel | "input_attachments" no longer appears in the panel |
| 7 | Verify in Yaml view that state section reflects the change | YAML state section does not include "input_attachments" |

---

## Expected Final State

Enabling the Attachments module adds "input_attachments" to the State panel automatically. Disabling it removes "input_attachments" from both the State panel and the YAML state section.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- "input_attachments" is added when Attachments is enabled and removed when it is disabled.

**Fail:**
- Any step produces an error or unexpected result.
- "input_attachments" does not appear or is not removed based on the Attachments toggle state.

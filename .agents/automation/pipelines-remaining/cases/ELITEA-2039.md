---
id: ELITEA-2039
title: "Pipeline — Printer Node Configuration"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2039: Pipeline — Printer Node Configuration

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that a Printer node can be added and configured with PRINTER type/value and Final Message, and that all configuration persists after save and reload.

---

## Preconditions

- User is logged in to the Elitea platform.
- A project exists with access to the Pipelines feature.

---

## Test Data

| Field | Value |
|-------|-------|
| PRINTER Type | F-String |
| PRINTER Value | ## GitHub Issue Triage Complete\n\n{triage_summary} |
| Final Message | Type 'ok' to end |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline and add a Printer node via "Add node" → "Printer" | Printer node appears on canvas |
| 2 | Verify Printer node panel shows: PRINTER section (Type + Value), Final Message field, Output handle at bottom | All listed sections are present |
| 3 | In PRINTER section: set Type dropdown to "F-String" | Type is set to F-String |
| 4 | Set Value field: "## GitHub Issue Triage Complete\n\n{triage_summary}" | Value field accepts the f-string |
| 5 | Set "Final Message" field: "Type 'ok' to end" | Final Message field is populated |
| 6 | Save pipeline | Pipeline saves without errors |
| 7 | Reload — verify PRINTER Type "F-String", Value text, and Final Message persist | All Printer node fields are correctly restored after reload |
| 8 | Note: Printer node has only Output handle (no Input combobox visible in panel) | Output handle is present; no Input combobox is shown |

---

## Expected Final State

The Printer node is fully configured with PRINTER Type "F-String", Value, and Final Message, all persisting after save and reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- PRINTER Type, Value, and Final Message persist correctly after reload.

**Fail:**
- Any step produces an error or unexpected result.
- Any Printer node field is lost after saving.

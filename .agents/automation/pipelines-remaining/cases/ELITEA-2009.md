---
id: ELITEA-2009
title: "Configure Code Node"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2009: Configure Code Node

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that a Code node can be added to a pipeline and fully configured with CODE type/value, Input, and Output fields, and that all configuration persists after saving and reloading.

---

## Preconditions

- User is logged in to the Elitea platform.
- A project exists with access to the Pipelines feature.

---

## Test Data

| Field | Value |
|-------|-------|
| CODE Type | Fixed |
| CODE Value | import json\nresult = input.upper() |
| Input variable | input |
| Output variable | result |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline and add a Code node via "Add node" → "Code" | Code node appears on the canvas |
| 2 | Click on Code node to open configuration panel | Configuration panel opens |
| 3 | Verify panel shows: CODE section (Type + Value), Input, Output, Interrupt before/after, Structured output | All listed sections are present in the panel |
| 4 | In CODE section: set Type to "Fixed", enter Value with Python code (e.g., "import json\nresult = input.upper()") | CODE section accepts the value |
| 5 | Set Input combobox — add variable "input" | "input" is added to the Input combobox |
| 6 | Set Output combobox — add variable "result" | "result" is added to the Output combobox |
| 7 | Save pipeline | Pipeline saves without errors |
| 8 | Reload — verify CODE Type "Fixed", Value, Input, and Output persist | All Code node configuration fields are correctly restored after reload |

---

## Expected Final State

The Code node is fully configured with CODE Type "Fixed", the Python code value, Input "input", and Output "result", all persisting correctly after save and reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- CODE Type, Value, Input, and Output all persist correctly after saving and reloading.

**Fail:**
- Any step produces an error or unexpected result.
- Any configuration field is lost after saving.

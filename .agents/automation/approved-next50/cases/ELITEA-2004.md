---
id: ELITEA-2004
title: "Configure LLM Node — System, Task, Chat History"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2004: Configure LLM Node — System, Task, Chat History

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that an LLM node can be fully configured with SYSTEM, TASK, and CHAT HISTORY sections using various input types, and that all values persist correctly after saving and reloading the pipeline.

---

## Preconditions

- User is logged in to the Elitea platform.
- A project exists with access to the Pipelines feature.

---

## Test Data

| Field | Value |
|-------|-------|
| SYSTEM Type | Fixed |
| SYSTEM Value | You are a helpful assistant |
| TASK Type | F-String |
| TASK Value | User Input: {input} |
| CHAT HISTORY Type | Fixed |
| CHAT HISTORY Value | [] |
| Input variable | input |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline and add an LLM node via "Add node" → "LLM" | LLM node appears on the canvas |
| 2 | Click on the LLM node to open its configuration panel | Configuration panel opens on the right |
| 3 | Verify panel shows sections: Trigger, SYSTEM, TASK, CHAT HISTORY, Input, Output, Toolkits, Interrupt before/after, Structured output | All listed sections are present in the panel |
| 4 | In SYSTEM section: set Type to "Fixed", enter Value: "You are a helpful assistant" | SYSTEM section accepts the value |
| 5 | In TASK section: set Type to "F-String", enter Value: "User Input: {input}" | TASK section accepts the f-string value |
| 6 | In CHAT HISTORY section: set Type to "Fixed", enter Value: "[]" | CHAT HISTORY section accepts the value |
| 7 | Set Input combobox to include "input" | "input" variable is added to Input |
| 8 | Set Output combobox to include desired output variables | Output variables are set |
| 9 | Save pipeline | Pipeline saves without errors |
| 10 | Reload page — verify SYSTEM, TASK, CHAT HISTORY types and values persisted | All values and types are correctly restored after reload |

---

## Expected Final State

The LLM node configuration is fully saved: SYSTEM (Fixed/"You are a helpful assistant"), TASK (F-String/"User Input: {input}"), CHAT HISTORY (Fixed/"[]"), Input, and Output persist after page reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- All LLM node configuration fields (SYSTEM, TASK, CHAT HISTORY, Input, Output) persist correctly after reload.

**Fail:**
- Any step produces an error or unexpected result.
- Any configured field does not persist after saving and reloading.

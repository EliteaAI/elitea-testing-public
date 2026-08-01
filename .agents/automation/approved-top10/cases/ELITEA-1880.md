---
id: ELITEA-1880
title: "LLM selector — change model, verify settings dialog, save and persist"
priority: medium
type: functional
module: agents
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:agents]
requirements: []
---

# ELITEA-1880: LLM selector — change model, verify settings dialog, save and persist

**Module:** agents · **Priority:** medium · **Type:** functional

**Objective:** Verify that the LLM selector allows changing models, that the settings dialog shows appropriate fields for the selected model, and that the model selection persists after save and reload.

---

## Preconditions

- User is logged in to the Elitea platform.
- An existing agent with an LLM selector is available.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to an agent detail page | The agent detail page loads |
| 2 | Note the currently selected model | The current model name is recorded |
| 3 | Click the model selector and choose a different model | The new model name is shown in the selector |
| 4 | Verify the new model name is shown in the selector | The selector displays the newly chosen model |
| 5 | Click the Settings (⚙️) icon | The settings dialog opens |
| 6 | Verify the settings dialog opens with fields appropriate to the model type: Reasoning slider (Low, Medium, High) + Max Completion Tokens (Auto/Custom) for standard models | The settings dialog shows the expected fields for the selected model |
| 7 | Close the settings dialog and click Save | Save completes successfully |
| 8 | Reload the page | The page reloads |
| 9 | Verify the model selector still shows the model chosen in step 3 | The model selector displays the saved model |

---

## Expected Final State

After reload, the model selector displays the model chosen during editing, confirming the selection was persisted.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The selected model persists after save and reload; the settings dialog shows correct fields.

**Fail:**
- Any step produces an error or unexpected result.
- The model reverts to the previous selection after reload, or the settings dialog shows incorrect fields.

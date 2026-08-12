---
id: ELITEA-2058
title: "Pipeline — LLM Model Selection in Chat Panel"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2058: Pipeline — LLM Model Selection in Chat Panel

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the model selector in the chat panel allows switching to a different LLM model and that the selected model is used for pipeline execution.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline is open with a chat panel visible.
- At least two models are available for selection.

---

## Test Data

| Field | Value |
|-------|-------|
| Default model | Anthropic Claude 4.6 Sonnet (or current default) |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline | Pipeline is loaded with chat panel visible |
| 2 | In the chat panel (right side), locate the "Model Selector Menu" group | Model selector button is visible in the chat panel |
| 3 | Verify current model is displayed (e.g., "Anthropic Claude 4.6 Sonnet") | Current model name is shown in the selector |
| 4 | Click the model button to open model selector | Model selection dropdown/list opens |
| 5 | Select a different model from the list | Different model is selected |
| 6 | Verify the model button label updates to the newly selected model | Model selector shows the newly selected model name |
| 7 | Execute pipeline — verify response uses the selected model | Pipeline execution uses the selected model |

---

## Expected Final State

The model selector in the chat panel allows changing the active model. The selected model is reflected in the button label and used for subsequent pipeline execution.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Model selector opens, allows selection, updates the label, and the selected model is used for execution.

**Fail:**
- Any step produces an error or unexpected result.
- Model selector does not open, selection does not update label, or wrong model is used.

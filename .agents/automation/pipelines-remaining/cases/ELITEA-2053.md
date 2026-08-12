---
id: ELITEA-2053
title: "Pipeline — Chat Starters"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2053: Pipeline — Chat Starters

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that chat starters can be added in pipeline settings, that they appear as clickable prompts in the chat panel, and that clicking a starter populates the chat input.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline is open for editing.

---

## Test Data

| Field | Value |
|-------|-------|
| Chat starter text | Analyze this data |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline | Pipeline is loaded in the editor |
| 2 | Expand "Chat starters" section in left panel | Chat starters section is visible |
| 3 | Verify existing starter (if any) shows with text and a "delete starter" button | Existing starters are shown with delete buttons |
| 4 | Click "+ Starter" button (button with text "Starter" and "+" icon) | A new starter input field appears |
| 5 | Enter text in the new starter textbox: "Analyze this data" | Starter text field is populated |
| 6 | Save pipeline | Pipeline saves without errors |
| 7 | In the chat panel (right side), verify "Analyze this data" appears as clickable starter | "Analyze this data" starter is visible in the chat panel |
| 8 | Click the starter — verify it populates the chat input and/or sends the message | Clicking the starter fills the chat input or sends the message |

---

## Expected Final State

The chat starter "Analyze this data" is visible in the chat panel as a clickable prompt and clicking it correctly populates the chat input with the starter text.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Chat starter appears in the chat panel and clicking it populates the input.

**Fail:**
- Any step produces an error or unexpected result.
- Chat starter does not appear, or clicking it does not populate the input.

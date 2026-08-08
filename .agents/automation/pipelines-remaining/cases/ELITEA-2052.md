---
id: ELITEA-2052
title: "Pipeline — Welcome Message"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2052: Pipeline — Welcome Message

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that a welcome message configured in the pipeline settings is automatically displayed at the start of a new chat session before any user input.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline is open for editing.

---

## Test Data

| Field | Value |
|-------|-------|
| Welcome message | Hello! How can I help you today? |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline | Pipeline is loaded in the editor |
| 2 | Expand "Welcome message" section in left panel | Welcome message section is visible |
| 3 | Fill textbox "Input your welcome message" with: "Hello! How can I help you today?" | Welcome message field is populated |
| 4 | Save pipeline | Pipeline saves without errors |
| 5 | Open a new chat session with this pipeline | New chat session starts |
| 6 | Verify welcome message "Hello! How can I help you today?" appears automatically before any user input | Welcome message is displayed at the top of the chat |

---

## Expected Final State

The configured welcome message "Hello! How can I help you today?" is automatically shown at the start of every new chat session with this pipeline, before any user interaction.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Welcome message appears automatically when a new chat session is opened.

**Fail:**
- Any step produces an error or unexpected result.
- Welcome message does not appear, or shows incorrect text.

---
id: ELITEA-2181
title: "Chat – Streaming Response Displayed While LLM Generates Output"
priority: high
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2181: Chat – Streaming Response Displayed While LLM Generates Output

**Module:** chat-interface · **Priority:** high · **Type:** functional

**Objective:** Verify that the LLM response streams progressively while generating, with loading indicators, pause scroll button, and the input field is restored after completion.

---

## Preconditions

- User is logged in to the Elitea platform.
- User has an open conversation.

---

## Test Data

| Field | Value |
|-------|-------|
| Message | Write a long poem about the city |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Type 'Write a long poem about the city' and click Send | User message appears; input cleared |
| 2 | Verify LLM response bubble appears with model name and spinning loading circle | Loading indicator visible |
| 3 | Verify response text streams progressively word by word or chunk by chunk | Streaming behavior visible |
| 4 | Verify 'Pause scroll' button appears at bottom right during streaming | Pause scroll button visible |
| 5 | Click 'Pause scroll' and verify auto-scroll stops | Auto-scroll stops |
| 6 | Verify Send button not visible during streaming | Send button hidden |
| 7 | Wait for streaming to complete | Spinning circle disappears; 'Pause scroll' button gone |
| 8 | Verify Regenerate button and action icons (speaker, copy, regenerate, delete) appear | Post-streaming actions visible |
| 9 | Verify input field becomes active again | Input field active |

---

## Expected Final State

Streaming response works correctly with all indicators; input restored after completion.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Streaming works; all indicators correct; input restored.

**Fail:**
- Any step produces an error or unexpected result.
- Response not streamed or indicators missing.

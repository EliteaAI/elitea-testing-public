---
id: ELITEA-2218
title: "Context Management – Global Setting Enabled, Auto-Summarization Enabled – Verify Automatic Summarization Occurs When Max Token Count Reached"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2218: Context Management – Global Setting Enabled, Auto-Summarization Enabled – Verify Automatic Summarization Occurs When Max Token Count Reached

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that with both context management and auto-summarization enabled, summarization occurs automatically when token count reaches the max.

---

## Preconditions

- User is logged in to the Elitea platform.
- Context management ON, auto-summarization ON in Settings.

---

## Test Data

| Field | Value |
|-------|-------|
| Max tokens | 64000 | Target summary tokens | 3000 | Preserve recent | 51 |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Enable context management and auto-summarization in Settings | Settings configured |
| 2 | Create a new conversation | Context Budget shows '0 / 64000', Messages: 0, Summaries: 0 |
| 3 | Send 10-15 detailed messages to increase token usage toward 64000 | Token count increases progressively |
| 4 | Continue sending messages until token count reaches ~64000 | Warning icon shown; bar turns yellow/orange |
| 5 | Send one more message to trigger summarization | 'Summarizing the chat history' indicator appears |
| 6 | After summarization, verify Summaries count incremented to 1 | Summaries: 1 |
| 7 | Verify token count reduced/managed after summarization | Token usage managed |
| 8 | Continue sending messages to trigger second summarization | Second summarization occurs; Summaries: 1 (increments) |

---

## Expected Final State

Automatic summarization triggers at max token count and Summaries count increments.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Auto-summarization triggers; Summaries count increments.

**Fail:**
- Any step produces an error or unexpected result.
- No summarization at max tokens.

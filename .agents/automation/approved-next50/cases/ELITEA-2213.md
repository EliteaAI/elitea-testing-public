---
id: ELITEA-2213
title: "Chat – HITL Authorization – Click Block Button and Verify Toolkit Tool Does Not Execute"
priority: high
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2213: Chat – HITL Authorization – Click Block Button and Verify Toolkit Tool Does Not Execute

**Module:** chat-interface · **Priority:** high · **Type:** functional

**Objective:** Verify that clicking Block prevents the sensitive toolkit action from executing.

---

## Preconditions

- User is logged in to the Elitea platform.
- HITL authorization card is showing for a sensitive toolkit action.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Verify HITL authorization card showing with three buttons | Buttons visible |
| 2 | Click 'Block' (red with X) | Card closes/updates showing action blocked |
| 3 | Verify toolkit tool does NOT execute | No execution |
| 4 | Verify LLM response indicates action was blocked | Response mentions block |
| 5 | Verify no tool execution chips for the blocked tool | No chips shown for blocked tool |

---

## Expected Final State

Toolkit action blocked; LLM responds indicating block.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Block prevents toolkit execution.

**Fail:**
- Any step produces an error or unexpected result.
- Toolkit executes despite blocking.

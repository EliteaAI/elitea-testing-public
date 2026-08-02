---
id: ELITEA-2203
title: "Chat – Slash Commands – Verify Typing / Displays Only Added Toolkit and MCP Participants"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2203: Chat – Slash Commands – Verify Typing / Displays Only Added Toolkit and MCP Participants

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that '/' only shows the specifically added toolkit and MCP in the dropdown.

---

## Preconditions

- User is logged in to the Elitea platform.
- User has a conversation with one toolkit and one MCP added.

---

## Test Data

| Field | Value |
|-------|-------|
| Toolkit name | banana | MCP name | delete |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Add toolkit 'banana' via + > Toolkits; add MCP 'delete' via + > MCPs | Both in PARTICIPANTS panel |
| 2 | Type '/' in message input | 'MENTION TOOLKIT OR MCP' dropdown shows exactly 'banana' (Toolkit) and 'delete' (MCP) |
| 3 | Verify 'banana' labeled 'Toolkit' with toolkit icon | Toolkit label and icon correct |
| 4 | Verify 'delete' labeled 'MCP' with MCP icon | MCP label and icon correct |
| 5 | Verify no other toolkits or MCPs appear | Only the two added items shown |

---

## Expected Final State

'/' shows only the added toolkit and MCP.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Only added toolkit and MCP shown in '/' dropdown.

**Fail:**
- Any step produces an error or unexpected result.
- Other items shown or added items missing.

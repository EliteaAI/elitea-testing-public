---
id: ELITEA-2140
title: "Chat – Conversation Moved from Older Back to List Appears in Today"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2140: Chat – Conversation Moved from Older Back to List Appears in Today

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that a conversation previously in the Older group that was moved to a folder, when moved back to the list, appears in the Today section.

---

## Preconditions

- User is logged in to the Elitea platform.
- A conversation that was originally in Older is now inside a folder.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and expand a folder containing a conversation from Older | Conversation visible in folder |
| 2 | Hover over the conversation, click three-dot icon, hover over Move to, click 'Back to the list' | Conversation removed from folder |
| 3 | Verify the conversation now appears in the Today section | Conversation appears in Today |
| 4 | Verify the timestamp reflects it as recently modified | Conversation listed under Today |

---

## Expected Final State

Conversation moved from folder appears in Today (not Older).

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Conversation appears in Today after moving back.

**Fail:**
- Any step produces an error or unexpected result.
- Conversation appears in Older or is missing.

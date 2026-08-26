---
id: ELITEA-2145
title: "Chat – Drag and Drop Conversation Back to the General List"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2145: Chat – Drag and Drop Conversation Back to the General List

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that dragging a conversation from a folder and dropping it into the general list area moves it back to the Today date group.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one conversation is inside a folder.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and expand a folder with a conversation | Conversation visible |
| 2 | Click and hold the conversation and drag toward Today/This Week/Older area | Date group area highlighted or accepts drop |
| 3 | Drop the conversation into the general list area | Conversation removed from folder |
| 4 | Verify the conversation appears in the Today section as recently modified | Conversation in Today |
| 5 | Verify the folder still exists and is empty or has remaining conversations | Folder remains |

---

## Expected Final State

Conversation moved from folder to Today via drag and drop.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Conversation moved back to Today via drag.

**Fail:**
- Any step produces an error or unexpected result.
- Drag and drop back to list does not work.
